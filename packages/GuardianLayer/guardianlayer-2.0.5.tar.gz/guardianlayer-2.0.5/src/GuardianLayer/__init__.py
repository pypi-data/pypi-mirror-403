"""AI Loop Guardian v2.0 - Meta-Cognition Layer for AI Agents"""

__version__ = "2.0.5"

from .advice_generator import AdviceContext, AdviceGenerator, AdviceStyle
from .cache import AdviceCache, CacheStats, HashCache, LRUCache, ValidationCache
from .experience_layer import ExperienceLayer
from .guardian import GuardianLayer
from .health_monitor import CircuitState, ErrorClassifier, ErrorType, HealthMonitor
from .interfaces import CacheProvider, StorageProvider
from .LoopDetector import LoopDetector, LoopMetrics
from .mcp_facade import MCPFacade, ToolSchema
from .metrics import MetricsCollector
from .providers import InMemoryCacheProvider, AsyncInMemoryCacheProvider, SQLiteStorageProvider

__all__ = [
    # Core
    "GuardianLayer",
    "LoopDetector",
    "LoopMetrics",
    # Validation
    "MCPFacade",
    "ToolSchema",
    # Health
    "HealthMonitor",
    "CircuitState",
    "ErrorType",
    "ErrorClassifier",
    # Experience & Storage
    "ExperienceLayer",
    "StorageProvider",
    "SQLiteStorageProvider",
    # Advice
    "AdviceGenerator",
    "AdviceStyle",
    "AdviceContext",
    # Caching
    "CacheProvider",
    "InMemoryCacheProvider",
    "AsyncInMemoryCacheProvider",
    "LRUCache",
    "AdviceCache",
    "ValidationCache",
    "HashCache",
    "CacheStats",
    # Metrics
    "MetricsCollector",
]
