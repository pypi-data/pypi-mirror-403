"""
MCP Facade - Universal Middleware for any MCP Server
Handles tool schema ingestion and provides a standard validation interface.
Now with validation caching for performance.
"""

import hashlib
import json
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from .interfaces import CacheProvider
from .providers import InMemoryCacheProvider

logger = logging.getLogger(__name__)


@dataclass
class ToolSchema:
    """Represents a validated MCP tool schema"""

    name: str
    description: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    required_params: List[str] = field(default_factory=list)

    @property
    def fingerprint(self) -> str:
        """Generate a unique hash for this tool's structure"""
        content = json.dumps(
            {"name": self.name, "params": sorted(self.parameters.keys())}, sort_keys=True
        )
        return hashlib.sha256(content.encode()).hexdigest()[:16]


class MCPFacade:
    """
    Universal adapter for MCP tool schemas.
    Acts as a registry and validator for any MCP-compliant tool server.

    v2.0: Now with validation caching for performance.
    """

    def __init__(self, cache_provider: Optional[CacheProvider] = None):
        self._tools: Dict[str, ToolSchema] = {}
        self._hooks: Dict[str, List[Callable]] = {}  # Tool-specific validation hooks

        # v2.0: Validation cache (injected or default)
        self._validation_cache = (
            cache_provider
            if cache_provider
            else InMemoryCacheProvider(max_size=2000, default_ttl=1800)
        )

    def ingest_mcp_tools(self, mcp_response: List[Dict[str, Any]]) -> int:
        """
        Ingest tool definitions from an MCP server's list_tools response.

        Args:
            mcp_response: The JSON response from MCP's list_tools()

        Returns:
            Number of tools successfully registered
        """
        count = 0
        for tool_def in mcp_response:
            try:
                schema = self._parse_tool_definition(tool_def)
                self._tools[schema.name] = schema
                count += 1
                logger.info(f" Registered tool: {schema.name} ({schema.fingerprint})")
            except Exception as e:
                logger.warning(f" Failed to parse tool: {tool_def.get('name', 'unknown')} - {e}")
        return count

    def _parse_tool_definition(self, tool_def: Dict[str, Any]) -> ToolSchema:
        """Parse a single MCP tool definition into our internal format"""
        name = tool_def.get("name", "")
        if not name:
            raise ValueError("Tool definition missing 'name'")

        description = tool_def.get("description", "")

        # Handle JSON Schema style parameters (MCP standard)
        input_schema = tool_def.get("inputSchema", tool_def.get("parameters", {}))
        properties = input_schema.get("properties", {})
        required = input_schema.get("required", [])

        return ToolSchema(
            name=name, description=description, parameters=properties, required_params=required
        )

    def get_tool(self, name: str) -> Optional[ToolSchema]:
        """Retrieve a registered tool schema by name"""
        return self._tools.get(name)

    def list_tools(self) -> List[str]:
        """List all registered tool names"""
        return list(self._tools.keys())

    def register_hook(self, tool_name: str, hook: Callable[[Dict], Optional[str]]):
        """
        Register a custom validation hook for a specific tool.

        Args:
            tool_name: Name of the tool to attach the hook to
            hook: A function that takes a tool_call dict and returns:
                  - None if valid
                  - An error message string if invalid
        """
        if tool_name not in self._hooks:
            self._hooks[tool_name] = []
        self._hooks[tool_name].append(hook)
        logger.info(f"🔗 Hook registered for tool: {tool_name}")

    def validate_call(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a tool call against the registered schema and hooks.
        Uses cache for repeated identical calls.

        Args:
            tool_call: The proposed tool call from the LLM

        Returns:
            {"valid": True} or {"valid": False, "reason": "...", "suggestion": "..."}
        """
        # Compute fingerprint for caching
        fingerprint = self.get_fingerprint(tool_call)

        # Check cache first (v2.0)
        if self._validation_cache:
            cached = self._validation_cache.get(fingerprint)
            if cached is not None:
                return cached

        # Perform validation
        result = self._do_validate(tool_call)

        # Cache valid results (v2.0)
        if self._validation_cache and result.get("valid"):
            self._validation_cache.set(fingerprint, result)

        return result

    def _do_validate(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """Internal validation logic"""
        tool_name = tool_call.get("tool") or tool_call.get("name")

        if not tool_name:
            return {
                "valid": False,
                "reason": "Missing tool name in call",
                "suggestion": "Provide a 'tool' or 'name' field",
            }

        schema = self._tools.get(tool_name)
        if not schema:
            return {
                "valid": False,
                "reason": f"Unknown tool: {tool_name}",
                "suggestion": f"Available tools: {', '.join(self.list_tools())}",
            }

        # Check required parameters
        args = tool_call.get("arguments", tool_call.get("params", tool_call))
        for param in schema.required_params:
            if param not in args or args[param] is None or args[param] == "":
                return {
                    "valid": False,
                    "reason": f"Missing required parameter: {param}",
                    "suggestion": f"Add '{param}' to the {tool_name} call",
                }

        # Run custom hooks
        for hook in self._hooks.get(tool_name, []):
            try:
                error = hook(tool_call)
                if error:
                    return {
                        "valid": False,
                        "reason": error,
                        "suggestion": "Check the tool's specific requirements",
                    }
            except Exception as e:
                logger.error(f"Hook error on {tool_name}: {e}")

        return {"valid": True}

    def get_cache_stats(self) -> Optional[Dict]:
        """Get validation cache statistics"""
        return self._validation_cache.get_stats()

    def get_fingerprint(self, tool_call: Dict[str, Any]) -> str:
        """
        Generate a unique fingerprint for a tool call (for loop detection).
        Uses SHA-256 for speed and collision resistance.
        """
        # Normalize the call for consistent hashing
        normalized = {
            "tool": tool_call.get("tool") or tool_call.get("name"),
            "args": json.dumps(
                tool_call.get("arguments", tool_call.get("params", {})), sort_keys=True
            ),
        }
        content = json.dumps(normalized, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()

    async def validate_call_async(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """
        Async version of validate_call.

        Args:
            tool_call: The proposed tool call from the LLM

        Returns:
            {"valid": True} or {"valid": False, "reason": "...", "suggestion": "..."}
        """
        # Compute fingerprint for caching
        fingerprint = self.get_fingerprint(tool_call)

        # Check cache first (async)
        if self._validation_cache:
            try:
                # Try to get from cache asynchronously if provider supports it
                if hasattr(self._validation_cache, "get"):
                    cached = self._validation_cache.get(fingerprint)
                    if cached is not None:
                        return cached
            except Exception:
                # Fallback to sync if async fails
                pass

        # Perform validation (sync is fine for validation logic)
        result = self._do_validate(tool_call)

        # Cache valid results (async if possible)
        if self._validation_cache and result.get("valid"):
            try:
                self._validation_cache.set(fingerprint, result)
            except Exception:
                # Ignore cache errors
                pass

        return result
