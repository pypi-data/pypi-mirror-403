"""
Loop Detector v2 - Hash-based O(1) detection with metrics
Optimized for performance: uses SHA-256 hashing instead of string comparison.
"""

import hashlib
import json
import logging
from collections import deque
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class LoopMetrics:
    """Metrics for visibility into loop detection effectiveness"""

    total_checks: int = 0
    loops_detected: int = 0
    immediate_repeats: int = 0
    short_cycles: int = 0
    long_cycles: int = 0
    excessive_repeats: int = 0

    @property
    def detection_rate(self) -> float:
        """Percentage of calls that were detected as loops"""
        return self.loops_detected / self.total_checks * 100 if self.total_checks > 0 else 0


class LoopDetector:
    """
    Detects loop patterns in AI tool calls using hash-based comparison.

    Performance:
    - O(1) hash lookup instead of O(n) string comparison
    - Hash cache to avoid recomputing for repeated calls
    - Memory efficient: stores 16-char hashes instead of full JSON

    Detection levels:
    1. Immediate repeat: A → A
    2. Short cycle: A → B → A
    3. Long cycle: A → B → C → A (up to history size)
    4. Excessive repetition: Same call more than max_repeats times total
    """

    def __init__(self, max_history: int = 10, max_repeats: int = 2):
        """
        Initialize the loop detector.

        Args:
            max_history: Number of recent calls to track for cycle detection
            max_repeats: Max allowed total repetitions of an identical call
        """
        self.max_history = max_history
        self.max_repeats = max_repeats

        # Hash-based history (O(1) lookup)
        self.history: deque = deque(maxlen=max_history)
        self.history_set: set = set()  # For O(1) cycle detection

        # Repeat tracking
        self.repeat_counts: Dict[str, int] = {}

        # Hash cache to avoid recomputation
        self._hash_cache: Dict[str, str] = {}
        self._cache_max_size = 500

        # Metrics
        self.metrics = LoopMetrics()

    def _compute_hash(self, tool_call: Dict[str, Any]) -> str:
        """
        Compute a deterministic hash for a tool call.
        Uses SHA-256 truncated to 16 chars for balance of speed and collision resistance.

        Returns:
            16-character hex hash string
        """
        # Normalize the call structure
        normalized = {
            "tool": tool_call.get("tool") or tool_call.get("name", ""),
            "args": tool_call.get("arguments", tool_call.get("params", {})),
        }

        # Serialize deterministically
        content = json.dumps(normalized, sort_keys=True)

        # Check cache first
        if content in self._hash_cache:
            return self._hash_cache[content]

        # Compute hash
        call_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

        # Cache it (with size limit)
        if len(self._hash_cache) >= self._cache_max_size:
            # Simple cache eviction: clear half when full
            keys_to_remove = list(self._hash_cache.keys())[: self._cache_max_size // 2]
            for key in keys_to_remove:
                del self._hash_cache[key]

        self._hash_cache[content] = call_hash
        return call_hash

    def check(self, tool_call: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Check if a tool call would create a loop.

        Args:
            tool_call: The proposed tool call

        Returns:
            Tuple of (is_loop: bool, reason: str or None)
        """
        self.metrics.total_checks += 1

        try:
            call_hash = self._compute_hash(tool_call)
            tool_name = tool_call.get("tool") or tool_call.get("name", "unknown")

            # Level 1: Immediate repetition (A → A)
            if self.history and self.history[-1] == call_hash:
                self.metrics.loops_detected += 1
                self.metrics.immediate_repeats += 1
                logger.warning(f" Immediate repetition blocked: {tool_name}")
                return (True, "IMMEDIATE_REPEAT")

            # Level 2: Short cycle (A → B → A)
            if len(self.history) >= 2 and self.history[-2] == call_hash:
                self.metrics.loops_detected += 1
                self.metrics.short_cycles += 1
                logger.warning(f" Short cycle (A-B-A) blocked: {tool_name}")
                return (True, "SHORT_CYCLE")

            # Level 3: Longer cycles - check if hash exists in recent history
            if call_hash in self.history_set:
                # Find where in history (for logging)
                history_list = list(self.history)
                if call_hash in history_list[:-2]:  # Exclude last 2 (covered above)
                    self.metrics.loops_detected += 1
                    self.metrics.long_cycles += 1
                    logger.warning(f" Cycle detected in history: {tool_name}")
                    return (True, "CYCLE_DETECTED")

            # Level 4: Excessive total repetition
            self.repeat_counts[call_hash] = self.repeat_counts.get(call_hash, 0) + 1

            if self.repeat_counts[call_hash] > self.max_repeats:
                count = self.repeat_counts[call_hash]
                self.metrics.loops_detected += 1
                self.metrics.excessive_repeats += 1
                logger.error(f" Excessive repetition ({count}x): {tool_name}")
                return (True, f"REPEATED_{count}_TIMES")

            # No loop detected - add to history
            self._add_to_history(call_hash)
            return (False, None)

        except Exception as e:
            logger.error(f"Loop detector error: {e}")
            return (False, None)

    def _add_to_history(self, call_hash: str):
        """Add a hash to history, maintaining the set for O(1) lookup"""
        # If we're at capacity, remove the oldest from the set
        if len(self.history) >= self.max_history:
            oldest = self.history[0]
            # Only remove from set if it's not elsewhere in history
            if list(self.history).count(oldest) == 1:
                self.history_set.discard(oldest)

        self.history.append(call_hash)
        self.history_set.add(call_hash)

    def reset(self):
        """Reset detector state for a new conversation"""
        self.history.clear()
        self.history_set.clear()
        self.repeat_counts.clear()
        # Don't reset hash cache (still valid)
        # Don't reset metrics (cumulative)
        logger.info(" Loop detector reset for new session")

    def get_metrics(self) -> Dict[str, Any]:
        """Get detection metrics for visibility/ROI"""
        return {
            "total_checks": self.metrics.total_checks,
            "loops_detected": self.metrics.loops_detected,
            "detection_rate": f"{self.metrics.detection_rate:.1f}%",
            "breakdown": {
                "immediate_repeats": self.metrics.immediate_repeats,
                "short_cycles": self.metrics.short_cycles,
                "long_cycles": self.metrics.long_cycles,
                "excessive_repeats": self.metrics.excessive_repeats,
            },
            "cache_size": len(self._hash_cache),
        }

    async def check_async(self, tool_call: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Async version of check method.

        Since LoopDetector is CPU-bound (hashing, set operations),
        this method just wraps the sync check to maintain API compatibility.

        Args:
            tool_call: The proposed tool call

        Returns:
            Tuple of (is_loop: bool, reason: str or None)
        """
        return self.check(tool_call)
