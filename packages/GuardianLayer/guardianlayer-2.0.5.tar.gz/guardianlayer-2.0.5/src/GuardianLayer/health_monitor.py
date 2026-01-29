"""
Health Monitor - Smart Circuit Breaker with Auto-Recovery
Replaces the binary circuit breaker with a 3-state pattern (CLOSED/OPEN/HALF_OPEN)
and distinguishes between error types.
"""

import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""

    CLOSED = "closed"  # Normal operation, all calls allowed
    OPEN = "open"  # Blocked, waiting for cooldown
    HALF_OPEN = "half_open"  # Testing recovery with probe calls


class ErrorType(Enum):
    """Classification of errors for intelligent handling"""

    SYSTEM = "system_error"  # Server down, timeout, network - penalizes health
    USER = "user_error"  # Missing param, invalid format - doesn't penalize health
    BUSINESS = "business_error"  # Not found, unauthorized - mild penalty
    UNKNOWN = "unknown"


@dataclass
class ToolHealth:
    """Health state for a single tool"""

    name: str
    score: int = 100  # 0-100 health score
    state: CircuitState = CircuitState.CLOSED
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    last_error_type: Optional[ErrorType] = None
    last_error_message: Optional[str] = None
    opened_at: float = 0  # Timestamp when circuit opened
    cooldown_duration: int = 60  # Seconds before trying recovery
    test_attempts: int = 0  # Probe attempts in HALF_OPEN
    total_calls: int = 0
    total_successes: int = 0
    total_failures: int = 0


class ErrorClassifier:
    """
    Classifies error messages into categories.
    This determines how errors affect tool health.
    """

    PATTERNS: Dict[ErrorType, List[str]] = {
        ErrorType.SYSTEM: [
            "timeout",
            "connection",
            "502",
            "503",
            "504",
            "network",
            "unavailable",
            "rate limit",
            "refused",
            "reset",
            "closed",
            "dns",
            "ssl",
            "tls",
        ],
        ErrorType.USER: [
            "missing",
            "required",
            "invalid",
            "parameter",
            "validation",
            "format",
            "type error",
            "schema",
            "expected",
            "must be",
            "cannot be empty",
        ],
        ErrorType.BUSINESS: [
            "not found",
            "unauthorized",
            "forbidden",
            "403",
            "401",
            "insufficient",
            "quota exceeded",
            "limit reached",
            "permission denied",
            "access denied",
        ],
    }

    def classify(self, error_message: str) -> ErrorType:
        """
        Classify an error message into a category.

        Args:
            error_message: The error string from the tool

        Returns:
            ErrorType indicating the category
        """
        if not error_message:
            return ErrorType.UNKNOWN

        error_lower = error_message.lower()

        for error_type, patterns in self.PATTERNS.items():
            if any(pattern in error_lower for pattern in patterns):
                return error_type

        return ErrorType.UNKNOWN


class HealthMonitor:
    """
    Smart health monitoring for MCP tools.

    Features:
    - 3-state circuit breaker (CLOSED → OPEN → HALF_OPEN → CLOSED)
    - Health score (0-100) instead of binary state
    - Error classification (system vs user vs business)
    - Auto-recovery with exponential backoff
    - Probe calls for testing recovery
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        base_cooldown: int = 60,
        max_cooldown: int = 3600,
        probe_limit: int = 3,
    ):
        """
        Initialize the Health Monitor.

        Args:
            failure_threshold: Consecutive system failures before opening circuit
            base_cooldown: Initial cooldown duration in seconds
            max_cooldown: Maximum cooldown duration (cap for exponential backoff)
            probe_limit: Number of probe attempts in HALF_OPEN state
        """
        self.tools: Dict[str, ToolHealth] = {}
        self.error_classifier = ErrorClassifier()
        self.failure_threshold = failure_threshold
        self.base_cooldown = base_cooldown
        self.max_cooldown = max_cooldown
        self.probe_limit = probe_limit

        # Thread safety
        import threading

        self._lock = threading.RLock()

    def get_health(self, tool_name: str) -> ToolHealth:
        """Get or create health record for a tool"""
        with self._lock:
            if tool_name not in self.tools:
                self.tools[tool_name] = ToolHealth(
                    name=tool_name, cooldown_duration=self.base_cooldown
                )
            return self.tools[tool_name]

    def check_tool(self, tool_name: str) -> Dict:
        """
        Check if a tool is healthy enough to be called.

        Returns:
            {
                "allowed": bool,
                "advice": str,
                "health_score": int (0-100),
                "is_probe": bool (if this is a recovery test),
                "retry_after": float (seconds until retry, if blocked)
            }
        """
        health = self.get_health(tool_name)
        now = time.time()

        # State: CLOSED - Normal operation
        if health.state == CircuitState.CLOSED:
            advice = ""
            if health.score < 50:
                advice = f" Tool '{tool_name}' has low health ({health.score}%). Use with caution."
            elif health.score < 80:
                advice = f"ℹ Tool '{tool_name}' health: {health.score}%"

            return {
                "allowed": True,
                "advice": advice,
                "health_score": health.score,
                "is_probe": False,
            }

        # State: OPEN - Check if cooldown expired
        elif health.state == CircuitState.OPEN:
            elapsed = now - health.opened_at

            if elapsed >= health.cooldown_duration:
                # Cooldown expired, transition to HALF_OPEN
                health.state = CircuitState.HALF_OPEN
                health.test_attempts = 0
                logger.info(f" Circuit HALF_OPEN for '{tool_name}' - testing recovery")

                return {
                    "allowed": True,
                    "advice": f" Tool '{tool_name}' recovering. This is a test probe.",
                    "health_score": health.score,
                    "is_probe": True,
                }
            else:
                remaining = health.cooldown_duration - elapsed
                return {
                    "allowed": False,
                    "advice": f"🔌 Tool '{tool_name}' temporarily disabled. Retry in {remaining:.0f}s",
                    "health_score": health.score,
                    "retry_after": remaining,
                    "is_probe": False,
                }

        # State: HALF_OPEN - Allow limited probes
        elif health.state == CircuitState.HALF_OPEN:
            if health.test_attempts < self.probe_limit:
                health.test_attempts += 1
                return {
                    "allowed": True,
                    "advice": f" Tool '{tool_name}' in recovery mode ({health.test_attempts}/{self.probe_limit}). Use with caution.",
                    "health_score": health.score,
                    "is_probe": True,
                }
            else:
                # Too many probes without success, reopen circuit
                self._open_circuit(health, extend_cooldown=True)
                return {
                    "allowed": False,
                    "advice": f" Tool '{tool_name}' still failing. Extended cooldown to {health.cooldown_duration}s.",
                    "health_score": health.score,
                    "retry_after": health.cooldown_duration,
                    "is_probe": False,
                }

        # Fallback
        return {"allowed": True, "advice": "", "health_score": 100, "is_probe": False}

    async def check_tool_async(self, tool_name: str) -> Dict:
        """
        Async version of check_tool.

        Since HealthMonitor is mostly in-memory operations,
        this method wraps the sync check_tool to maintain API compatibility.

        Args:
            tool_name: Name of the tool to check

        Returns:
            {
                "allowed": bool,
                "advice": str,
                "health_score": int (0-100),
                "is_probe": bool (if this is a recovery test),
                "retry_after": float (seconds until retry, if blocked)
            }
        """
        return self.check_tool(tool_name)

    def report_result(self, tool_name: str, success: bool, error_message: Optional[str] = None):
        """
        Report the result of a tool call.
        Updates health score and circuit state based on error classification.

        Args:
            tool_name: Name of the tool
            success: Whether the call succeeded
            error_message: Error message if failed
        """
        health = self.get_health(tool_name)
        health.total_calls += 1

        if success:
            self._handle_success(health)
        else:
            error_type = self.error_classifier.classify(error_message or "")
            self._handle_failure(health, error_type, error_message)

    def _handle_success(self, health: ToolHealth):
        """Handle a successful call"""
        health.total_successes += 1
        health.consecutive_successes += 1
        health.consecutive_failures = 0

        # Improve health score (up to 100)
        recovery_amount = 5 if health.state == CircuitState.CLOSED else 10
        health.score = min(100, health.score + recovery_amount)

        # If in HALF_OPEN and successful, close the circuit
        if health.state == CircuitState.HALF_OPEN:
            health.state = CircuitState.CLOSED
            health.cooldown_duration = self.base_cooldown  # Reset cooldown
            logger.info(f"✅ Circuit CLOSED for '{health.name}' - recovered successfully")

    def _handle_failure(
        self, health: ToolHealth, error_type: ErrorType, error_message: Optional[str]
    ):
        """Handle a failed call based on error type"""
        health.total_failures += 1
        health.consecutive_successes = 0
        health.last_error_type = error_type
        health.last_error_message = error_message

        # Different penalties based on error type
        if error_type == ErrorType.SYSTEM:
            # System errors are serious - penalize heavily
            health.score = max(0, health.score - 15)
            health.consecutive_failures += 1

            # Check if we should open the circuit
            if health.consecutive_failures >= self.failure_threshold:
                if health.state != CircuitState.OPEN:
                    self._open_circuit(
                        health, extend_cooldown=health.state == CircuitState.HALF_OPEN
                    )

        elif error_type == ErrorType.USER:
            # User errors (bad params) - minimal penalty to tool health
            # The AI made a mistake, not the tool
            health.score = max(0, health.score - 2)
            # Don't increment consecutive_failures - this doesn't indicate tool problems

        elif error_type == ErrorType.BUSINESS:
            # Business errors - mild penalty
            health.score = max(0, health.score - 5)
            health.consecutive_failures += 1
            # Don't open circuit for business errors alone

        else:  # UNKNOWN
            health.score = max(0, health.score - 10)
            health.consecutive_failures += 1

    def _open_circuit(self, health: ToolHealth, extend_cooldown: bool = False):
        """Open the circuit breaker for a tool"""
        health.state = CircuitState.OPEN
        health.opened_at = time.time()

        if extend_cooldown:
            # Exponential backoff
            health.cooldown_duration = min(health.cooldown_duration * 2, self.max_cooldown)

        logger.warning(
            f"🔌 Circuit OPEN for '{health.name}' - "
            f"{health.consecutive_failures} failures, "
            f"cooldown: {health.cooldown_duration}s"
        )

    def reset_tool(self, tool_name: str):
        """Manually reset a tool's health (admin override)"""
        if tool_name in self.tools:
            self.tools[tool_name] = ToolHealth(name=tool_name, cooldown_duration=self.base_cooldown)
            logger.info(f"🔄 Health reset for '{tool_name}'")

    def get_all_health(self) -> Dict[str, Dict]:
        """Get health summary for all tracked tools"""
        return {
            name: {
                "score": health.score,
                "state": health.state.value,
                "success_rate": (
                    health.total_successes / health.total_calls * 100
                    if health.total_calls > 0
                    else 100
                ),
                "last_error": health.last_error_message,
            }
            for name, health in self.tools.items()
        }
