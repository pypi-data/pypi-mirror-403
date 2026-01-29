"""
Structured logging configuration for GuardianLayer
Provides consistent, searchable logs with context
"""

import logging
import logging.handlers
import sys
from typing import Any, Dict, Optional

try:
    import structlog

    STRUCTLOG_AVAILABLE = True
except ImportError:
    STRUCTLOG_AVAILABLE = False

from .config import Config


class GuardianLogger:
    """
    Unified logger interface that falls back to standard logging
    if structlog is not available
    """

    def __init__(self, name: str):
        self.name = name
        self._setup_logging()

    def _setup_logging(self):
        """Configure logging based on configuration"""
        level = getattr(logging, Config.LOG_LEVEL.upper(), logging.INFO)

        # Configure root logger
        logging.basicConfig(
            level=level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.handlers.RotatingFileHandler(
                    "guardian.log", maxBytes=10485760, backupCount=5  # 10MB
                ),
            ],
        )

        if STRUCTLOG_AVAILABLE and Config.LOG_FORMAT == "structured":
            self._setup_structlog()
        else:
            self.logger = logging.getLogger(self.name)

    def _setup_structlog(self):
        """Configure structured logging with structlog"""
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer(),
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
        self.logger = structlog.get_logger(self.name)

    def info(self, event: str, **kwargs):
        """Log info event with optional context"""
        if STRUCTLOG_AVAILABLE and Config.LOG_FORMAT == "structured":
            self.logger.info(event, **kwargs)
        else:
            context_str = " | ".join(f"{k}={v}" for k, v in kwargs.items())
            message = f"{event}{' | ' + context_str if context_str else ''}"
            self.logger.info(message)

    def warning(self, event: str, **kwargs):
        """Log warning event with optional context"""
        if STRUCTLOG_AVAILABLE and Config.LOG_FORMAT == "structured":
            self.logger.warning(event, **kwargs)
        else:
            context_str = " | ".join(f"{k}={v}" for k, v in kwargs.items())
            message = f"{event}{' | ' + context_str if context_str else ''}"
            self.logger.warning(message)

    def error(self, event: str, **kwargs):
        """Log error event with optional context"""
        if STRUCTLOG_AVAILABLE and Config.LOG_FORMAT == "structured":
            self.logger.error(event, **kwargs)
        else:
            context_str = " | ".join(f"{k}={v}" for k, v in kwargs.items())
            message = f"{event}{' | ' + context_str if context_str else ''}"
            self.logger.error(message)

    def debug(self, event: str, **kwargs):
        """Log debug event with optional context"""
        if STRUCTLOG_AVAILABLE and Config.LOG_FORMAT == "structured":
            self.logger.debug(event, **kwargs)
        else:
            context_str = " | ".join(f"{k}={v}" for k, v in kwargs.items())
            message = f"{event}{' | ' + context_str if context_str else ''}"
            self.logger.debug(message)

    def critical(self, event: str, **kwargs):
        """Log critical event with optional context"""
        if STRUCTLOG_AVAILABLE and Config.LOG_FORMAT == "structured":
            self.logger.critical(event, **kwargs)
        else:
            context_str = " | ".join(f"{k}={v}" for k, v in kwargs.items())
            message = f"{event}{' | ' + context_str if context_str else ''}"
            self.logger.critical(message)


# Convenience function for getting a logger
def get_logger(name: str) -> GuardianLogger:
    """
    Get a configured GuardianLogger instance

    Args:
        name: Logger name (usually __name__)

    Returns:
        GuardianLogger instance
    """
    return GuardianLogger(name)


# Common log event templates
class LogEvents:
    """Pre-defined log event templates for consistency"""

    # Initialization
    GUARDIAN_INITIALIZED = "guardian_initialized"
    COMPONENT_INITIALIZED = "component_initialized"

    # Loop Detection
    LOOP_DETECTED = "loop_detected"
    IMMEDIATE_REPEAT = "immediate_repeat"
    SHORT_CYCLE = "short_cycle"
    LONG_CYCLE = "long_cycle"
    EXCESSIVE_REPETITION = "excessive_repetition"

    # Circuit Breaker
    CIRCUIT_OPENED = "circuit_opened"
    CIRCUIT_HALF_OPEN = "circuit_half_open"
    CIRCUIT_CLOSED = "circuit_closed"
    PROBE_FAILED = "probe_failed"

    # Validation
    TOOL_VALIDATION_FAILED = "tool_validation_failed"
    MISSING_REQUIRED_PARAM = "missing_required_param"
    UNKNOWN_TOOL = "unknown_tool"

    # Performance
    CACHE_HIT = "cache_hit"
    CACHE_MISS = "cache_miss"
    METRICS_COLLECTED = "metrics_collected"

    # Experience Learning
    INCIDENT_LOGGED = "incident_logged"
    BEST_PRACTICE_UPDATED = "best_practice_updated"
    SIMILAR_SUCCESS_FOUND = "similar_success_found"

    # Errors
    DATABASE_ERROR = "database_error"
    CONFIG_ERROR = "config_error"
    PROVIDER_ERROR = "provider_error"
    UNEXPECTED_ERROR = "unexpected_error"


# Context builders for common scenarios
class LogContext:
    """Builders for common log contexts"""

    @staticmethod
    def tool_context(tool_name: str, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """Build context for tool-related logs"""
        return {
            "tool_name": tool_name,
            "tool": tool_name,
            "call_args": list(tool_call.get("arguments", {}).keys()),
            "fingerprint": tool_call.get("fingerprint", "unknown"),
        }

    @staticmethod
    def performance_context(
        operation: str, duration_ms: Optional[float] = None, cache_hit: Optional[bool] = None
    ) -> Dict[str, Any]:
        """Build context for performance-related logs"""
        context = {"operation": operation}
        if duration_ms is not None:
            context["duration_ms"] = duration_ms
        if cache_hit is not None:
            context["cache_hit"] = cache_hit
        return context

    @staticmethod
    def error_context(
        error: Exception, operation: Optional[str] = None, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Build context for error logs"""
        error_context = {"error_type": type(error).__name__, "error_message": str(error)}
        if operation:
            error_context["operation"] = operation
        if context:
            error_context.update(context)
        return error_context

    @staticmethod
    def metrics_context(
        metrics_type: str, value: Any, metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Build context for metrics logs"""
        context = {"metrics_type": metrics_type, "value": value}
        if metadata:
            context.update(metadata)
        return context
