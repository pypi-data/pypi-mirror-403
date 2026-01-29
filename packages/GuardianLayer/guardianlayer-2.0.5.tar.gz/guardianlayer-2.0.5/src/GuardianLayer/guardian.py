"""
GuardianLayer v2.0 - Meta-Cognition Shield for AI Agents
Enhanced with smart Circuit Breaker, Error Classification, and metrics.
"""

import logging
import asyncio
import time
from typing import Any, Callable, Dict, List, Optional

from .advice_generator import AdviceContext, AdviceGenerator, AdviceStyle
from .config import Config
from .experience_layer import ExperienceLayer
from .health_monitor import HealthMonitor
from .interfaces import CacheProvider, StorageProvider
from .LoopDetector import LoopDetector
from .mcp_facade import MCPFacade
from .metrics import MetricsCollector

logger = logging.getLogger(__name__)


class GuardianLayer:
    """
    The main orchestrator combining all protection layers.

    v2.0 Features:
    - L0: Smart Circuit Breaker (CLOSED/OPEN/HALF_OPEN with auto-recovery)
    - L1: Hash-based loop detection (O(1) performance)
    - L2: Schema validation (MCP compatible)
    - L3: Experience learning (SQLite + Memory)
    - L4: Advice injection (customizable prompts)
    - Error classification (system vs user vs business)
    - Health scoring (0-100 per tool)
    """

    def __init__(
        self,
        db_path: Optional[str] = None,
        max_history: Optional[int] = None,
        max_repeats: Optional[int] = None,
        advice_style: Optional[AdviceStyle] = None,
        failure_threshold: Optional[int] = None,
        base_cooldown: Optional[int] = None,
        est_tokens_per_call: Optional[int] = None,
        est_latency_ms: Optional[int] = None,
        storage_provider: Optional[StorageProvider] = None,
        cache_provider: Optional[CacheProvider] = None,
    ):
        """
        Initialize the GuardianLayer shield.

        Args:
            db_path: Path to SQLite database for persistence (None = uses Config)
            max_history: Number of tool calls to keep in loop detection history
            max_repeats: Max allowed repetitions before flagging a loop
            advice_style: Default style for advice generation
            failure_threshold: Consecutive system failures before opening circuit
            base_cooldown: Initial cooldown duration in seconds when circuit opens
            est_tokens_per_call: Estimated tokens saved per prevented call (for ROI)
            est_latency_ms: Estimated latency saved per cache hit (for ROI)
            storage_provider: Custom storage provider (None = uses default)
            cache_provider: Custom cache provider (None = uses default)

        Note:
            All parameters default to Config values if not specified.
            Environment variables can override defaults.
        """
        # Use Config defaults when parameters not specified
        db_path = db_path or Config.get_db_path()
        max_history = max_history or Config.MAX_HISTORY
        max_repeats = max_repeats or Config.MAX_REPEATS

        # Convert advice_style string to enum if needed
        if advice_style is None:
            advice_style = getattr(AdviceStyle, Config.ADVICE_STYLE, AdviceStyle.CONCISE)

        failure_threshold = failure_threshold or Config.FAILURE_THRESHOLD
        base_cooldown = base_cooldown or Config.BASE_COOLDOWN
        est_tokens_per_call = est_tokens_per_call or Config.EST_TOKENS_PER_CALL
        est_latency_ms = est_latency_ms or Config.EST_LATENCY_MS

        # Core components
        self.loop_detector = LoopDetector(max_history=max_history, max_repeats=max_repeats)
        self.mcp_facade = MCPFacade(cache_provider=cache_provider)
        self.experience = ExperienceLayer(db_path=db_path, storage_provider=storage_provider)
        self.advice_generator = AdviceGenerator(
            style=advice_style or AdviceStyle.CONCISE, cache_provider=cache_provider
        )

        # v2.0: Smart Health Monitor (replaces old binary circuit breaker)
        self.health_monitor = HealthMonitor(
            failure_threshold=failure_threshold, base_cooldown=base_cooldown
        )

        # v2.0: Centralized Metrics Collector
        self.metrics = MetricsCollector(
            est_tokens_per_call=est_tokens_per_call, est_latency_ms=est_latency_ms
        )
        self._register_metrics()

        # State
        self._last_error: Optional[str] = None

        logger.info("🛡️ GuardianLayer v2.0 initialized")

    def _register_metrics(self):
        """Register component metrics with the collector"""
        self.metrics.register_source("loop_detection", self.loop_detector.get_metrics)
        self.metrics.register_source("tool_health", self.health_monitor.get_all_health)
        self.metrics.register_source("session", self.experience.get_session_stats)

        # Add cache sources if available
        if hasattr(self.mcp_facade, "get_cache_stats"):
            self.metrics.register_source("val_cache", self.mcp_facade.get_cache_stats)
        if hasattr(self.advice_generator, "get_cache_stats"):
            self.metrics.register_source("advice_cache", self.advice_generator.get_cache_stats)

    # =====================
    # MCP Tool Management
    # =====================

    def ingest_tools(self, mcp_tools: List[Dict[str, Any]]) -> int:
        """
        Register tools from an MCP server's list_tools response.

        Args:
            mcp_tools: List of tool definitions from MCP

        Returns:
            Number of tools registered
        """
        return self.mcp_facade.ingest_mcp_tools(mcp_tools)

    def register_mcp_tools(self, mcp_tools: List[Dict[str, Any]]) -> int:
        """
        Alias for ingest_tools() for backward compatibility.

        Args:
            mcp_tools: List of tool definitions from MCP

        Returns:
            Number of tools registered
        """
        return self.ingest_tools(mcp_tools)

    def register_hook(self, tool_name: str, hook: Callable[[Dict], Optional[str]]):
        """Register a custom validation hook for a specific tool"""
        self.mcp_facade.register_hook(tool_name, hook)

    # =====================
    # Core Shield Methods
    # =====================

    def check(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main validation method. Checks a tool call through all layers.

        Args:
            tool_call: The proposed tool call from the LLM

        Returns:
            {
                "allowed": bool,
                "reason": str (if blocked),
                "suggestion": str (if blocked),
                "advice": str (always, may be empty),
                "health_score": int (0-100),
                "is_probe": bool (if this is a recovery test call)
            }
        """
        tool_name = tool_call.get("tool") or tool_call.get("name", "unknown")
        result = {
            "allowed": True,
            "reason": None,
            "suggestion": None,
            "advice": "",
            "health_score": 100,
            "is_probe": False,
        }

        # Track total checks
        self.metrics.track_check()

        # Layer 0: Smart Circuit Breaker (with auto-recovery)
        health_status = self.health_monitor.check_tool(tool_name)
        result["health_score"] = health_status.get("health_score", 100)
        result["is_probe"] = health_status.get("is_probe", False)

        if not health_status.get("allowed", True):
            self.metrics.track_circuit_break()
            result["allowed"] = False
            result["reason"] = health_status.get("advice", "Tool temporarily disabled")
            result["suggestion"] = (
                f"Retry in {health_status.get('retry_after', 60):.0f} seconds or try alternative."
            )
            return result

        # If there's health advice, include it
        if health_status.get("advice"):
            result["advice"] = health_status["advice"]

        # Layer 1: Loop Detection
        is_loop, loop_reason = self.loop_detector.check(tool_call)
        if is_loop:
            self.metrics.track_loop_prevented()
            result["allowed"] = False
            result["reason"] = f"Loop detected: {loop_reason}"
            result["suggestion"] = "You're repeating yourself. Try a different approach."
            return result

        # Layer 2: Schema Validation (if tools are registered)
        if self.mcp_facade.list_tools():
            validation = self.mcp_facade.validate_call(tool_call)
            if not validation.get("valid"):
                self.metrics.track_validation_failure()
                result["allowed"] = False
                result["reason"] = validation.get("reason", "Validation failed")
                result["suggestion"] = validation.get("suggestion", "Check parameters")
                return result

        # Layer 3: Generate Advice (always, for context injection)
        advice_context = AdviceContext(
            tool_name=tool_name,
            failure_count=self.experience.get_failure_count(tool_call),
            last_error=self._last_error,
            similar_success=self.experience.find_similar_success(tool_name),
            tool_reliability=self.experience.get_tool_reliability(tool_name),
        )
        generated_advice = self.advice_generator.generate(advice_context)
        if generated_advice:
            # Combine with health advice if present
            if result["advice"]:
                result["advice"] += "\n" + generated_advice
            else:
                result["advice"] = generated_advice

        return result

    async def check_async(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """
        True async version of the main validation method.
        All I/O operations are non-blocking.

        Args:
            tool_call: The proposed tool call from the LLM

        Returns:
            {
                "allowed": bool,
                "reason": str (if blocked),
                "suggestion": str (if blocked),
                "advice": str (always, may be empty),
                "health_score": int (0-100),
                "is_probe": bool (if this is a recovery test call)
            }
        """
        tool_name = tool_call.get("tool") or tool_call.get("name", "unknown")
        result = {
            "allowed": True,
            "reason": None,
            "suggestion": None,
            "advice": "",
            "health_score": 100,
            "is_probe": False,
        }

        # Track total checks
        self.metrics.track_check()

        # Layer 0: Smart Circuit Breaker (async)
        health_status = await self.health_monitor.check_tool_async(tool_name)
        result["health_score"] = health_status.get("health_score", 100)
        result["is_probe"] = health_status.get("is_probe", False)

        if not health_status.get("allowed", True):
            result["allowed"] = False
            result["reason"] = "Circuit breaker active"
            result["suggestion"] = health_status.get("advice", "Tool temporarily unavailable")
            self.metrics.track_circuit_break()
            return result

        # Layer 1: Hash-based Loop Detection (async)
        is_loop, loop_reason = await self.loop_detector.check_async(tool_call)
        if is_loop:
            result["allowed"] = False
            result["reason"] = f"Loop detected: {loop_reason}"
            result["suggestion"] = "Try a different tool or approach"
            self.metrics.track_loop_prevented()
            return result

        # Layer 2: Schema Validation (async)
        if self.mcp_facade.list_tools():
            validation = await self.mcp_facade.validate_call_async(tool_call)
            if not validation.get("valid", True):
                self.metrics.track_validation_failure()
                result["allowed"] = False
                result["reason"] = validation.get("reason", "Invalid tool call")
                result["suggestion"] = validation.get("suggestion", "Check tool parameters")
                return result

        # Layer 3+4: Experience Learning + Advice Generation (Async)

        # Async DB lookups for advice context
        similar_success = await self.experience.find_similar_success_async(tool_name)
        tool_reliability = await self.experience.get_tool_reliability_async(tool_name)

        advice_context = AdviceContext(
            tool_name=tool_name,
            failure_count=self.experience.get_failure_count(
                tool_call
            ),  # Process memory, sync is safe
            last_error=self._last_error,
            similar_success=similar_success,
            tool_reliability=tool_reliability,
        )
        # v2.0: True async advice generation
        generated_advice = await self.advice_generator.generate_async(advice_context)
        if generated_advice:
            result["advice"] = generated_advice

        return result

    def report_result(
        self,
        tool_call: Dict[str, Any],
        success: bool,
        error: Optional[str] = None,
        context_hint: Optional[str] = None,
    ):
        """
        Report the result of a tool call for learning.

        Args:
            tool_call: The tool call that was executed
            success: Whether it succeeded
            error: Error message if failed
            context_hint: What was the user trying to achieve?
        """
        tool_name = tool_call.get("tool") or tool_call.get("name", "unknown")

        # Update experience layer
        self.experience.log_incident(tool_call, success, error, context_hint)

        # Update health monitor (with error classification)
        self.health_monitor.report_result(tool_name, success, error)

        if not success:
            self._last_error = error

    # =====================
    # Prompt Injection
    # =====================

    def get_awareness_context(self) -> str:
        """
        Get a formatted string of current awareness to inject into the LLM prompt.
        Call this before sending a message to the LLM.

        Returns:
            A string with self-awareness directives (may be empty)
        """
        parts = []

        # Get health status for all tracked tools
        for tool_name, health_info in self.health_monitor.get_all_health().items():
            if health_info["state"] == "open":
                parts.append(f" '{tool_name}' is temporarily disabled (circuit open).")
            elif health_info["state"] == "half_open":
                parts.append(f" '{tool_name}' is recovering. Use with caution.")
            elif health_info["score"] < 50:
                parts.append(f" '{tool_name}' has low health ({health_info['score']}%).")

        # Report unreliable tools from experience
        for tool_name in self.mcp_facade.list_tools():
            reliability = self.experience.get_tool_reliability(tool_name)
            if reliability is not None and reliability < 0.5:
                if not any(tool_name in p for p in parts):
                    parts.append(f" '{tool_name}' success rate: {reliability:.0%}")

        if parts:
            return "\n[SELF-AWARENESS]\n" + "\n".join(parts) + "\n"
        return ""

    # =====================
    # Utilities
    # =====================

    def reset(self):
        """Reset all state for a new conversation"""
        self.loop_detector.reset()
        self.metrics.reset()
        self._last_error = None
        # Start a new experience session
        session_id = self.experience.start_new_session()
        logger.info(f" GuardianLayer reset for new session: {session_id}")

    def reset_tool(self, tool_name: str):
        """Admin override: reset a specific tool's health"""
        self.health_monitor.reset_tool(tool_name)

    def set_advice_style(self, style: AdviceStyle):
        """Change the advice generation style"""
        self.advice_generator.set_style(style)

    def set_custom_advice_resolver(self, resolver: Callable[[AdviceContext], str]):
        """Set a custom function for generating advice"""
        self.advice_generator.set_custom_resolver(resolver)

    def get_metrics(self) -> Dict[str, Any]:
        """Get all metrics for ROI visibility"""
        return self.metrics.get_all_metrics()

    def close(self):
        """
        Close all resources safely.
        If using async providers, use close_async() instead.
        """
        if hasattr(self.experience, "_is_async") and self.experience._is_async:
            # Just warn effectively, cannot await here
            logger.warning(
                "Attempting to close Async provider synchronously. Use await guardian.close_async() instead."
            )
            # We can try to run it if an event loop is running, but safer to just warn.
        else:
            # Close experience layer async
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If loop is running, schedule it
                    loop.create_task(self.experience.close())
                else:
                    loop.run_until_complete(self.experience.close())
            except Exception:
                # Fallback if no loop
                try:
                    asyncio.run(self.experience.close())
                except Exception:
                    pass

    async def close_async(self):
        """Close resources asynchronously"""
        await self.experience.close()
        logger.info(" GuardianLayer closed")

    async def report_result_async(
        self,
        tool_call: Dict[str, Any],
        success: bool,
        error: Optional[str] = None,
        context_hint: Optional[str] = None,
    ):
        """
        Async version of report_result.

        Args:
            tool_call: The tool call that was executed
            success: Whether it succeeded
            error: Error message if failed
            context_hint: What was the user trying to achieve?
        """
        tool_name = tool_call.get("tool") or tool_call.get("name", "unknown")
        fingerprint = self.mcp_facade.get_fingerprint(tool_call)

        # Store last error for context
        if error:
            self._last_error = error

        import json

        # Async experience layer updates
        # Ensure call_data is a string (JSON) for SQL binding
        call_json = json.dumps(tool_call)

        await self.experience.log_incident_async(
            {
                "session_id": self.experience.session_id,
                "tool_name": tool_name,
                "fingerprint": fingerprint,
                "success": success,
                "timestamp": time.time(),
                "error": error,
                "context_hint": context_hint,
                "call_data": call_json,
            }
        )

        # Update collective intelligence
        await self.experience.update_best_practice_async(fingerprint, tool_name, success, call_json)

        # Report to health monitor (sync - in-memory)
        self.health_monitor.report_result(tool_name, success, error)

        # Track metrics (sync - in-memory)
        if success:
            self.metrics.track_cache_hit()
        else:
            self.metrics.track_validation_failure()
