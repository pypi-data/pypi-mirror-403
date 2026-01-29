"""
Metrics Collector - Centralized Observability & ROI Tracking
Aggregates metrics from all layers and calculates high-level ROI (Tokens Saved, Time Saved).
"""

import logging
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict

logger = logging.getLogger(__name__)


@dataclass
class RoiMetrics:
    """Return on Investment metrics"""

    loops_prevented: int = 0
    cache_hits: int = 0
    validation_failures: int = 0
    circuit_breaks: int = 0
    total_checks: int = 0  # New metric for successful checks

    # Estimates
    tokens_saved: int = 0  # Est. tokens saved by preventing bad calls
    time_saved_ms: float = 0.0  # Est. latency saved by cache


class MetricsCollector:
    """
    Central hub for GuardianLayer observability.
    Collects real-time metrics and calculates ROI.
    """

    def __init__(self, est_tokens_per_call: int = 250, est_latency_ms: int = 1000):
        self._roi = RoiMetrics()
        self._sources: Dict[str, Callable[[], Dict]] = {}
        self._start_time = time.time()

        # Configurable ROI estimation
        self.est_tokens_per_call = est_tokens_per_call
        self.est_latency_ms = est_latency_ms

        # Thread safety
        import threading

        self._lock = threading.Lock()

    def register_source(self, name: str, callback: Callable[[], Dict]):
        """Register a component to pull metrics from"""
        self._sources[name] = callback

    # --- Event Tracking ---

    def track_check(self):
        """Record a standard check event"""
        with self._lock:
            self._roi.total_checks += 1

    def track_loop_prevented(self):
        """Record a prevented loop"""
        with self._lock:
            self._roi.loops_prevented += 1
            self._roi.tokens_saved += self.est_tokens_per_call

    def track_cache_hit(self):
        """Record a validation/advice cache hit"""
        with self._lock:
            self._roi.cache_hits += 1
            self._roi.time_saved_ms += (
                self.est_latency_ms * 0.1
            )  # Assume 10% of full call cost saved

    def track_circuit_break(self):
        """Record a circuit breaker activation"""
        with self._lock:
            self._roi.circuit_breaks += 1
            self._roi.tokens_saved += self.est_tokens_per_call

    def track_validation_failure(self):
        """Record a schema validation failure"""
        with self._lock:
            self._roi.validation_failures += 1
        # Validation failure saves execution time but not necessarily tokens (LLM already generated it)
        # But it prevents the *result* processing cost.

    # --- Reporting ---

    def get_roi_stats(self) -> Dict[str, Any]:
        """Get high-level ROI statistics"""
        return {
            "uptime_seconds": int(time.time() - self._start_time),
            "protection_events": {
                "loops_prevented": self._roi.loops_prevented,
                "circuit_breaks": self._roi.circuit_breaks,
                "validation_failures": self._roi.validation_failures,
                "cache_hits": self._roi.cache_hits,
                "total_checks": self._roi.total_checks,
            },
            "estimated_savings": {
                "tokens_saved": self._roi.tokens_saved,
                "time_saved_sec": self._roi.time_saved_ms / 1000,
            },
        }

    def get_all_metrics(self) -> Dict[str, Any]:
        """Aggregate all metrics (ROI + Component details)"""
        metrics = {"roi": self.get_roi_stats()}

        # Collect from registered components
        for name, source in self._sources.items():
            try:
                metrics[name] = source()
            except Exception as e:
                logger.warning(f"Failed to collect metrics from {name}: {e}")
                metrics[name] = {"error": str(e)}

        return metrics

    def reset(self):
        """Reset counters"""
        self._roi = RoiMetrics()
        self._start_time = time.time()
