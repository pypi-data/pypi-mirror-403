Configuration Reference
========================

This page documents all configuration options for GuardianLayer and its components.

Environment Variables
---------------------

GuardianLayer respects the following environment variables:

.. code-block:: bash

   # Database configuration
   export GUARDIAN_DB_PATH="./experience.db"
   
   # Loop detection
   export GUARDIAN_MAX_HISTORY=10
   export GUARDIAN_MAX_REPEATS=2
   
   # Circuit breaker
   export GUARDIAN_FAILURE_THRESHOLD=5
   export GUARDIAN_BASE_COOLDOWN=60
   
   # Advice generation
   export GUARDIAN_ADVICE_STYLE="concise"  # concise | expert | friendly
   
   # Metrics estimation (for ROI calculations)
   export GUARDIAN_EST_TOKENS_PER_CALL=100
   export GUARDIAN_EST_LATENCY_MS=50

GuardianLayer Constructor
--------------------------

.. code-block:: python

   GuardianLayer(
       db_path: Optional[str] = None,
       max_history: Optional[int] = None,
       max_repeats: Optional[int] = None,
       advice_style: Optional[AdviceStyle] = None,
       failure_threshold: Optional[int] = None,
       base_cooldown: Optional[int] = None,
       est_tokens_per_call: Optional[int] = None,
       est_latency_ms: Optional[int] = None,
       storage_provider: Optional[StorageProvider] = None,
       cache_provider: Optional[CacheProvider] = None
   )

**Parameters**:

``db_path`` : str, optional
    Path to SQLite database file for persistent storage. Defaults to ``guardian_experience.db`` in current directory.
    Set to ``":memory:"`` for in-memory database (useful for testing).

``max_history`` : int, optional (default: 10)
    Number of recent tool calls to track for loop detection. Higher values detect longer cycles but use more memory.

``max_repeats`` : int, optional (default: 2)
    Maximum allowed repetitions of identical tool calls before flagging as a loop.

``advice_style`` : AdviceStyle, optional (default: CONCISE)
    Style for advice generation. Options:
    
    - ``AdviceStyle.CONCISE``: Short, direct messages (best for small models)
    - ``AdviceStyle.EXPERT``: Technical, detailed analysis (best for large models)
    - ``AdviceStyle.FRIENDLY``: Conversational tone (best for user-facing agents)

``failure_threshold`` : int, optional (default: 5)
    Number of consecutive system failures before opening the circuit breaker.

``base_cooldown`` : int, optional (default: 60)
    Initial cooldown duration in seconds when circuit opens. Doubles on repeated opens (exponential backoff).

``est_tokens_per_call`` : int, optional (default: 100)
    Estimated tokens saved per prevented tool call (for ROI metrics).

``est_latency_ms`` : int, optional (default: 50)
    Estimated latency in milliseconds saved per cache hit (for ROI metrics).

``storage_provider`` : StorageProvider, optional
    Custom storage backend. If None, uses ``SQLiteStorageProvider`` with ``db_path``.

``cache_provider`` : CacheProvider, optional
    Custom cache backend. If None, uses ``InMemoryCacheProvider`` with default settings.

**Examples**:

.. code-block:: python

   # Minimal configuration (all defaults)
   guardian = GuardianLayer()
   
   # Custom database path
   guardian = GuardianLayer(db_path="/var/lib/guardian/prod.db")
   
   # In-memory for testing
   guardian = GuardianLayer(db_path=":memory:")
   
   # Aggressive loop detection
   guardian = GuardianLayer(max_repeats=1, max_history=20)
   
   # Tolerant circuit breaker
   guardian = GuardianLayer(failure_threshold=10, base_cooldown=30)
   
   # Expert advice for GPT-4
   from GuardianLayer import AdviceStyle
   guardian = GuardianLayer(advice_style=AdviceStyle.EXPERT)

LoopDetector Configuration
---------------------------

.. code-block:: python

   from GuardianLayer import LoopDetector
   
   detector = LoopDetector(
       max_history=10,  # Sliding window size
       max_repeats=2    # Max allowed repetitions
   )

**Tuning Guidelines**:

.. list-table::
   :header-rows: 1
   :widths: 20 40 40

   * - Use Case
     - ``max_history``
     - ``max_repeats``
   * - Strict (production)
     - 10
     - 1-2
   * - Balanced (default)
     - 10
     - 2
   * - Permissive (development)
     - 20
     - 3-5
   * - Research/exploration
     - 50
     - 10

HealthMonitor Configuration
----------------------------

.. code-block:: python

   from GuardianLayer import HealthMonitor
   
   monitor = HealthMonitor(
       failure_threshold=5,     # Failures before opening circuit
       base_cooldown=60,        # Initial cooldown (seconds)
       max_cooldown=3600,       # Max cooldown (seconds)
       probe_limit=3            # Probe attempts in HALF_OPEN
   )

**Parameters**:

``failure_threshold`` : int
    Number of consecutive system errors before circuit opens. User errors don't count.

``base_cooldown`` : int
    Initial cooldown duration. Doubles with each repeated circuit open (exponential backoff).

``max_cooldown`` : int
    Maximum cooldown duration to prevent indefinite blocking.

``probe_limit`` : int
    Number of successful probe calls needed to transition from HALF_OPEN to CLOSED.

**Error Classification**:

The health monitor classifies errors to determine circuit behavior:

.. code-block:: python

   # System errors (count toward circuit breaker)
   - "timeout", "connection", "network", "unavailable"
   - "500", "502", "503", "504"
   
   # User errors (don't count toward circuit breaker)
   - "invalid", "missing", "required", "forbidden"
   - "400", "401", "403", "404"
   
   # Business errors (don't count toward circuit breaker)
   - "insufficient", "quota", "rate limit"

**Custom Error Classification**:

.. code-block:: python

   from GuardianLayer import ErrorClassifier, ErrorType
   
   classifier = ErrorClassifier()
   
   # Override classification
   def custom_classify(error_msg: str) -> ErrorType:
       if "CUSTOM_ERROR" in error_msg:
           return ErrorType.BUSINESS
       return classifier.classify(error_msg)
   
   # Note: GuardianLayer doesn't expose this API yet
   # Use custom storage provider to implement

MCPFacade Configuration
-----------------------

The MCP facade automatically configures based on ingested tools:

.. code-block:: python

   from GuardianLayer import MCPFacade, InMemoryCacheProvider
   
   # With custom cache
   cache = InMemoryCacheProvider(max_size=500, default_ttl=3600)
   facade = MCPFacade(cache_provider=cache)
   
   # Register tools
   facade.ingest_mcp_tools(mcp_tools)
   
   # Register custom validation hook
   def validate_api_key(tool_call):
       api_key = tool_call["arguments"].get("api_key", "")
       if not api_key.startswith("sk-"):
           return "Invalid API key format"
       return None
   
   facade.register_hook("openai_call", validate_api_key)

ExperienceLayer Configuration
------------------------------

.. code-block:: python

   from GuardianLayer import ExperienceLayer
   from GuardianLayer.providers import SQLiteStorageProvider
   
   # With default SQLite storage
   experience = ExperienceLayer(db_path="experience.db")
   
   # With custom storage provider
   storage = PostgreSQLStorageProvider("postgresql://...")
   experience = ExperienceLayer(storage_provider=storage)
   
   # Start a new session
   session_id = experience.start_new_session()

Storage Provider Configuration
-------------------------------

**SQLiteStorageProvider**:

.. code-block:: python

   from GuardianLayer.providers import SQLiteStorageProvider
   
   storage = SQLiteStorageProvider(
       db_path="experience.db"
   )

**AsyncSQLiteStorageProvider**:

.. code-block:: python

   from GuardianLayer.providers import AsyncSQLiteStorageProvider
   
   storage = AsyncSQLiteStorageProvider(
       db_path="async_experience.db"
   )
   
   # Must initialize asynchronously
   await storage.init()

**Custom PostgreSQL Provider** (example):

.. code-block:: python

   from GuardianLayer.interfaces import AsyncStorageProvider
   import asyncpg
   
   class PostgreSQLStorageProvider(AsyncStorageProvider):
       def __init__(self, dsn: str, pool_size: int = 10):
           self.dsn = dsn
           self.pool_size = pool_size
           self.pool = None
       
       async def init(self):
           self.pool = await asyncpg.create_pool(
               self.dsn,
               min_size=2,
               max_size=self.pool_size
           )
       
       async def log_incident(self, incident_data):
           async with self.pool.acquire() as conn:
               await conn.execute("""
                   INSERT INTO incidents 
                   (session_id, tool_name, fingerprint, success, timestamp, error_reason)
                   VALUES ($1, $2, $3, $4, $5, $6)
               """, ...)
       
       # Implement other methods...
   
   # Usage
   storage = PostgreSQLStorageProvider(
       dsn="postgresql://user:pass@localhost/guardian",
       pool_size=20
   )
   guardian = GuardianLayer(storage_provider=storage)

Cache Provider Configuration
-----------------------------

**InMemoryCacheProvider**:

.. code-block:: python

   from GuardianLayer.providers import InMemoryCacheProvider
   
   cache = InMemoryCacheProvider(
       max_size=1000,    # Max entries
       default_ttl=3600  # Time-to-live in seconds
   )

**Custom Redis Provider** (example):

.. code-block:: python

   from GuardianLayer.interfaces import CacheProvider
   import redis
   
   class RedisCacheProvider(CacheProvider):
       def __init__(self, host="localhost", port=6379, db=0):
           self.client = redis.Redis(host=host, port=port, db=db)
       
       def get(self, key: str):
           value = self.client.get(key)
           if value:
               import pickle
               return pickle.loads(value)
           return None
       
       def set(self, key: str, value, ttl=None):
           import pickle
           self.client.set(key, pickle.dumps(value), ex=ttl)
       
       def delete(self, key: str):
           self.client.delete(key)
       
       def get_stats(self):
           info = self.client.info("stats")
           return {
               "keyspace_hits": info.get("keyspace_hits", 0),
               "keyspace_misses": info.get("keyspace_misses", 0)
           }
   
   # Usage
   cache = RedisCacheProvider(host="redis.example.com")
   guardian = GuardianLayer(cache_provider=cache)

AdviceGenerator Configuration
------------------------------

.. code-block:: python

   from GuardianLayer import AdviceGenerator, AdviceStyle, AdviceContext
   
   # With predefined style
   advice_gen = AdviceGenerator(style=AdviceStyle.EXPERT)
   
   # Change style at runtime
   advice_gen.set_style(AdviceStyle.FRIENDLY)
   
   # Custom resolver
   def my_advice(context: AdviceContext) -> str:
       if context.failure_count > 10:
           return "🚨 CRITICAL: Excessive failures detected!"
       elif context.tool_reliability and context.tool_reliability < 0.2:
           return f"⚠️ {context.tool_name} has <20% success rate. Consider alternatives."
       return ""
   
   advice_gen.set_custom_resolver(my_advice)

MetricsCollector Configuration
-------------------------------

Metrics are configured via GuardianLayer constructor:

.. code-block:: python

   guardian = GuardianLayer(
       est_tokens_per_call=150,  # Your model's average tokens
       est_latency_ms=75         # Your API's average latency
   )
   
   # Get metrics
   metrics = guardian.get_metrics()
   print(f"Estimated ROI: ${metrics['tokens_saved'] * 0.0001:.2f}")

Production Configuration Examples
----------------------------------

**High-Availability Setup**:

.. code-block:: python

   from GuardianLayer import GuardianLayer, AdviceStyle
   from custom_providers import PostgreSQLStorage, RedisCache
   
   guardian = GuardianLayer(
       # Use PostgreSQL for multi-server deployment
       storage_provider=PostgreSQLStorage(
           dsn="postgresql://guardian:pwd@db.prod:5432/guardian",
           pool_size=20
       ),
       # Use Redis for shared cache
       cache_provider=RedisCache(
           host="redis.prod",
           port=6379,
           db=0
       ),
       # Strict protection
       max_repeats=1,
       failure_threshold=3,
       base_cooldown=120,
       # Expert advice for production LLMs
       advice_style=AdviceStyle.EXPERT
   )

**Development Setup**:

.. code-block:: python

   guardian = GuardianLayer(
       db_path=":memory:",        # No persistence needed
       max_repeats=5,             # Permissive loop detection
       failure_threshold=10,      # Tolerant circuit breaker
       advice_style=AdviceStyle.FRIENDLY
   )

**Testing Setup**:

.. code-block:: python

   import pytest
   from GuardianLayer import GuardianLayer
   
   @pytest.fixture
   def guardian():
       g = GuardianLayer(db_path=":memory:")
       yield g
       g.close()

Performance Tuning
------------------

**Optimize for Latency**:

.. code-block:: python

   # Use async mode
   guardian = GuardianLayer()
   result = await guardian.check_async(tool_call)  # Non-blocking DB I/O
   
   # Increase cache sizes
   cache = InMemoryCacheProvider(max_size=5000, default_ttl=7200)
   guardian = GuardianLayer(cache_provider=cache)

**Optimize for Memory**:

.. code-block:: python

   # Reduce history window
   guardian = GuardianLayer(max_history=5)
   
   # Smaller cache
   cache = InMemoryCacheProvider(max_size=100, default_ttl=1800)
   guardian = GuardianLayer(cache_provider=cache)

**Optimize for Throughput**:

.. code-block:: python

   # Use connection pooling
   from GuardianLayer.providers import AsyncSQLiteStorageProvider
   
   storage = AsyncSQLiteStorageProvider("experience.db")
   guardian = GuardianLayer(storage_provider=storage)
   
   # Process calls concurrently
   results = await asyncio.gather(*[
       guardian.check_async(call) for call in batch_calls
   ])

Logging Configuration
---------------------

GuardianLayer uses Python's standard logging module:

.. code-block:: python

   import logging
   
   # Enable debug logging
   logging.basicConfig(level=logging.DEBUG)
   
   # Or configure specific logger
   logger = logging.getLogger("GuardianLayer")
   logger.setLevel(logging.INFO)
   
   # Custom format
   handler = logging.StreamHandler()
   handler.setFormatter(logging.Formatter(
       '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
   ))
   logger.addHandler(handler)

**Log Levels**:

- ``DEBUG``: All operations (hash computations, cache hits/misses, etc.)
- ``INFO``: Important events (circuit opens, loops detected, etc.)
- ``WARNING``: Unexpected conditions (async sync mixing, etc.)
- ``ERROR``: Errors in GuardianLayer itself (not tool errors)

Troubleshooting
---------------

**Issue: Database locked errors**

.. code-block:: python

   # Solution 1: Use async provider
   storage = AsyncSQLiteStorageProvider("experience.db")
   
   # Solution 2: Increase timeout
   import sqlite3
   sqlite3.connect("experience.db", timeout=30)

**Issue: Memory usage growing**

.. code-block:: python

   # Reduce history window
   guardian = GuardianLayer(max_history=5)
   
   # Limit cache size
   cache = InMemoryCacheProvider(max_size=500)

**Issue: Too many false positives**

.. code-block:: python

   # Increase thresholds
   guardian = GuardianLayer(
       max_repeats=5,
       failure_threshold=10
   )

See :doc:`troubleshooting` for more details.
