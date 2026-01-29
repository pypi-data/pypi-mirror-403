"""
Experience Layer v2 - Multi-Level Storage & Collective Intelligence
Handles incident logging, success patterns, and tiered learning (Session/Process/Global).
"""

import hashlib
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from .interfaces import AsyncStorageProvider, StorageProvider
from .providers import SQLiteStorageProvider

logger = logging.getLogger(__name__)


@dataclass
class Incident:
    """Represents a tool call incident (success or failure)"""

    tool_name: str
    fingerprint: str
    success: bool
    timestamp: float
    session_id: str
    error_reason: Optional[str] = None
    context_hint: Optional[str] = None


@dataclass
class SessionStats:
    """Statistics for the current session"""

    session_id: str
    start_time: float = field(default_factory=time.time)
    tool_counts: Dict[str, int] = field(default_factory=dict)
    failures: int = 0
    successes: int = 0

    @property
    def duration(self) -> float:
        return time.time() - self.start_time

    @property
    def total_calls(self) -> int:
        return self.successes + self.failures


class ExperienceLayer:
    """
    Tiered storage for AI agent experiences.

    Levels:
    1. Session: Ephemeral stats for the current conversation.
    2. Process: In-memory cache shared across sessions in this process.
    3. Global: Persistent storage via StorageProvider.
    """

    def __init__(
        self, db_path: Optional[str] = None, storage_provider: Optional[StorageProvider] = None
    ):
        # L1: Session Scope
        self.current_session: Optional[SessionStats] = None
        self.start_new_session()

        # L2: Process Scope (Hot Memory Cache)
        self._process_cache: Dict[str, Dict] = {}  # fingerprint -> best_practice
        self._process_failures: Dict[str, int] = {}  # fingerprint -> count

        # L3: Global Scope (Abstracted Storage)
        self.storage = storage_provider

        # Backwards compatibility: if db_path provided but no provider, use SQLite default
        if not self.storage and db_path:
            self.storage = SQLiteStorageProvider(db_path)

        self._is_async = isinstance(self.storage, AsyncStorageProvider) if self.storage else False

        if self.storage and not self._is_async:
            self.storage.init()
        # Note: If async, init() must be called await experienc_layer.init_async() or implicitly handled

    def start_new_session(self, session_id: Optional[str] = None):
        """Start a new tracking session"""
        sid = session_id or str(uuid.uuid4())
        self.current_session = SessionStats(session_id=sid)
        logger.info(f"🆕 New experience session started: {sid}")
        return sid

    @property
    def session_id(self) -> Optional[str]:
        return self.current_session.session_id if self.current_session else None

    def log_incident(
        self,
        tool_call: Dict[str, Any],
        success: bool,
        error_reason: Optional[str] = None,
        context_hint: Optional[str] = None,
    ):
        """
        Log a tool call result across all tiers (Session, Process, Global).
        """
        fingerprint = self._compute_fingerprint(tool_call)
        tool_name = tool_call.get("tool") or tool_call.get("name", "unknown")

        # 1. Update Session Stats
        if self.current_session:
            self.current_session.tool_counts[tool_name] = (
                self.current_session.tool_counts.get(tool_name, 0) + 1
            )
            if success:
                self.current_session.successes += 1
            else:
                self.current_session.failures += 1

        # 2. Update Process Cache
        if success:
            self._process_cache[fingerprint] = {
                "tool": tool_name,
                "call": tool_call,
                "success": True,
            }
            self._process_failures.pop(fingerprint, None)
        else:
            self._process_failures[fingerprint] = self._process_failures.get(fingerprint, 0) + 1

        # 3. Update Global Storage (Sync-compatible only)
        if self.storage and not self._is_async:
            try:
                # Log incident
                incident_data = {
                    "session_id": (
                        self.current_session.session_id if self.current_session else "unknown"
                    ),
                    "tool_name": tool_name,
                    "fingerprint": fingerprint,
                    "success": success,
                    "timestamp": time.time(),
                    "error_reason": error_reason,
                    "context_hint": context_hint,
                    "call_data": json.dumps(tool_call),
                }
                self.storage.log_incident(incident_data)

                # Update collective intelligence
                self.storage.update_best_practice(
                    fingerprint, tool_name, success, json.dumps(tool_call) if success else None
                )
            except Exception as e:
                logger.error(f"Storage provider error: {e}")

    def get_failure_count(self, tool_call: Dict[str, Any]) -> int:
        """Get failure count from Process memory (fastest)"""
        fingerprint = self._compute_fingerprint(tool_call)
        return self._process_failures.get(fingerprint, 0)

    def find_similar_success(self, tool_name: str) -> Optional[Dict]:
        """
        Find a successful call pattern.
        Checks Process cache first, then Global Storage.
        """
        # 1. Process Cache
        for fp, data in self._process_cache.items():
            if data.get("tool") == tool_name and data.get("success"):
                return data.get("call")

        # 2. Global Storage
        if self.storage:
            if self._is_async:
                logger.warning(
                    "Attempted to call sync find_similar_success with Async Provider. Skipping DB lookup."
                )
                return None

            try:
                result = self.storage.get_best_practice(tool_name)
                if result and result.get("last_success_data"):
                    return json.loads(result["last_success_data"])
            except Exception as e:
                logger.error(f"Storage lookup failed: {e}")

        return None

    def get_tool_reliability(self, tool_name: str) -> Optional[float]:
        """Calculate global reliability score for a tool"""
        if not self.storage:
            return None

        try:
            stats = self.storage.get_tool_stats(tool_name)
            successes = stats.get("successes", 0)
            failures = stats.get("failures", 0)
            total = successes + failures
            return successes / total if total > 0 else None
        except Exception:
            return None
        return None

    def get_session_stats(self) -> Dict[str, Any]:
        """Get current session statistics"""
        if not self.current_session:
            return {}
        return {
            "session_id": self.current_session.session_id,
            "duration": f"{self.current_session.duration:.2f}s",
            "total_calls": self.current_session.total_calls,
            "successes": self.current_session.successes,
            "failures": self.current_session.failures,
            "tool_usage": self.current_session.tool_counts,
        }

    def _compute_fingerprint(self, tool_call: Dict[str, Any]) -> str:
        """Generate unique hash for a tool call"""
        normalized = {
            "tool": tool_call.get("tool") or tool_call.get("name"),
            "args": json.dumps(
                tool_call.get("arguments", tool_call.get("params", {})), sort_keys=True
            ),
        }
        content = json.dumps(normalized, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:32]

    async def close(self):
        """Close storage provider"""
        if self.storage:
            if self._is_async:
                await self.storage.close()
            else:
                self.storage.close()
        logger.info("📦 Experience storage closed")

    # =================
    # Async Methods
    # =================

    async def log_incident_async(self, incident_data: Dict[str, Any]):
        """Async version of log_incident"""
        if self.storage:
            if self._is_async:
                await self.storage.log_incident(incident_data)
            else:
                # Sync provider
                self.storage.log_incident(incident_data)

    async def update_best_practice_async(
        self, fingerprint: str, tool_name: str, success: bool, call_data: str
    ):
        """Async version of update_best_practice"""
        if self.storage:
            if self._is_async:
                await self.storage.update_best_practice(fingerprint, tool_name, success, call_data)
            else:
                # Sync provider
                self.storage.update_best_practice(fingerprint, tool_name, success, call_data)

    async def find_similar_success_async(self, tool_name: str) -> Optional[Dict]:
        """Async version of find_similar_success"""
        # 1. Process Cache (Sync access is fine mainly, but should be careful if massive)
        for fp, data in self._process_cache.items():
            if data.get("tool") == tool_name and data.get("success"):
                return data.get("call")

        # 2. Global Storage
        if self.storage:
            if self._is_async:
                result = await self.storage.get_best_practice(tool_name)
            else:
                result = self.storage.get_best_practice(tool_name)

            if result and result.get("last_success_data"):
                return json.loads(result["last_success_data"])
        return None

    async def get_tool_reliability_async(self, tool_name: str) -> Optional[float]:
        """Async version of tool reliability check"""
        if not self.storage:
            return None

        try:
            if self._is_async:
                stats = await self.storage.get_tool_stats(tool_name)
            else:
                stats = self.storage.get_tool_stats(tool_name)

            successes = stats.get("successes", 0)
            failures = stats.get("failures", 0)
            total = successes + failures
            return successes / total if total > 0 else None
        except Exception:
            return None

    async def get_tool_stats_async(self, tool_name: str) -> Dict[str, int]:
        """Async version of get_tool_stats"""
        if self.storage:
            if self._is_async:
                return await self.storage.get_tool_stats(tool_name)
            else:
                return self.storage.get_tool_stats(tool_name)

        return {"successes": 0, "failures": 0}

    async def get_session_stats_async(self) -> Dict[str, Any]:
        """Async version of get_session_stats"""
        # Session stats are in-memory, can be returned directly
        return self.get_session_stats()
