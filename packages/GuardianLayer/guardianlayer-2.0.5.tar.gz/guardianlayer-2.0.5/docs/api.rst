API Reference
=============

This document is the comprehensive API reference for the GuardianLayer package. It covers all public classes, methods, and interfaces.

.. note::
   All classes and methods use Sphinx autodoc for automatic documentation generation from Python docstrings.

Core Modules
------------

GuardianLayer (Main Class)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The main orchestrator combining all protection layers.

.. automodule:: GuardianLayer.guardian
   :members: GuardianLayer
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

**Key Methods**:

* ``check(tool_call)`` - Validate a tool call (synchronous)
* ``check_async(tool_call)`` - Validate a tool call (asynchronous)
* ``report_result(tool_call, success, error)`` - Report execution result
* ``report_result_async(...)`` - Report execution result (asynchronous)
* ``ingest_tools(mcp_tools)`` - Register MCP tools
* ``get_awareness_context()`` - Get self-awareness string for prompts
* ``get_metrics()`` - Get all metrics
* ``reset()`` - Reset for new session
* ``close() / close_async()`` - Close resources

Loop Detection
~~~~~~~~~~~~~~

Hash-based O(1) loop detection with metrics tracking.

.. automodule:: GuardianLayer.LoopDetector
   :members:
   :undoc-members:
   :show-inheritance:

**Performance**: O(1) hash lookup vs O(n) string comparison

**Metrics Available**:

* ``total_checks`` - All checks performed
* ``loops_detected`` - Total loops prevented
* ``immediate_repeats`` - Back-to-back identical calls
* ``short_cycles`` - Pattern cycles detected
* ``detection_rate`` - Percentage of calls that were loops

Health Monitoring
~~~~~~~~~~~~~~~~~

Smart circuit breaker with auto-recovery and error classification.

.. automodule:: GuardianLayer.health_monitor
   :members: HealthMonitor, CircuitState, ErrorType, ErrorClassifier, ToolHealth
   :undoc-members:
   :show-inheritance:

**Circuit States**:

* ``CLOSED`` - Normal operation
* ``OPEN`` - Tool disabled due to failures
* ``HALF_OPEN`` - Testing recovery

**Error Types**:

* ``SYSTEM`` - Network, timeout, server errors (count toward circuit breaker)
* ``USER`` - Invalid input, missing parameters (don't count)
* ``BUSINESS`` - Rate limits, quotas (don't count)

MCP Facade (Tool Validation)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Universal adapter for MCP (Model Context Protocol) tool schemas.

.. automodule:: GuardianLayer.mcp_facade
   :members: MCPFacade, ToolSchema
   :undoc-members:
   :show-inheritance:

**Features**:

* MCP-compatible schema parsing
* Parameter validation with type checking
* Custom validation hooks
* Validation result caching

Experience Layer
~~~~~~~~~~~~~~~~

Multi-tiered storage for learning from past interactions.

.. automodule:: GuardianLayer.experience_layer
   :members: ExperienceLayer, Incident, SessionStats
   :undoc-members:
   :show-inheritance:

**Storage Tiers**:

1. **Session Memory** - Ephemeral stats for current conversation
2. **Process Memory** - LRU cache shared across sessions
3. **Global Storage** - Persistent SQLite/PostgreSQL database

Advice Generation
~~~~~~~~~~~~~~~~~

Context-aware advice for prompt injection and self-awareness.

.. automodule:: GuardianLayer.advice_generator
   :members: AdviceGenerator, AdviceStyle, AdviceContext
   :undoc-members:
   :show-inheritance:

**Advice Styles**:

* ``CONCISE`` - Short, direct (for small models)
* ``EXPERT`` - Technical, detailed (for large models)
* ``FRIENDLY`` - Conversational (for user-facing agents)

Providers & Interfaces
----------------------

Storage Providers
~~~~~~~~~~~~~~~~~

Abstract interfaces for persistent storage backends.

.. automodule:: GuardianLayer.interfaces
   :members: StorageProvider, AsyncStorageProvider
   :undoc-members:
   :show-inheritance:

**Built-in Implementations**:

.. automodule:: GuardianLayer.providers
   :members: SQLiteStorageProvider, AsyncSQLiteStorageProvider
   :undoc-members:
   :show-inheritance:

**Methods**:

* ``init()`` - Initialize database and tables
* ``log_incident(incident_data)`` - Log a tool call result
* ``update_best_practice(...)`` - Update collective intelligence
* ``get_best_practice(tool_name)`` - Retrieve successful patterns
* ``get_tool_stats(tool_name)`` - Get success/failure counts
* ``close()`` - Close database connection

Cache Providers
~~~~~~~~~~~~~~~

Abstract interfaces for caching backends.

.. automodule:: GuardianLayer.interfaces
   :members: CacheProvider, AsyncCacheProvider
   :undoc-members:
   :show-inheritance:

**Built-in Implementations**:

.. automodule:: GuardianLayer.providers
   :members: InMemoryCacheProvider
   :undoc-members:
   :show-inheritance:

**Methods**:

* ``get(key)`` - Retrieve cached value
* ``set(key, value, ttl)`` - Store value with TTL
* ``delete(key)`` - Remove value
* ``get_stats()`` - Get cache statistics

Cache Implementations
~~~~~~~~~~~~~~~~~~~~~

Specialized cache implementations for different use cases.

.. automodule:: GuardianLayer.cache
   :members: LRUCache, AdviceCache, ValidationCache, HashCache, CacheStats
   :undoc-members:
   :show-inheritance:

**Cache Types**:

* ``LRUCache`` - General-purpose LRU eviction
* ``AdviceCache`` - Optimized for advice generation
* ``ValidationCache`` - Optimized for validation results
* ``HashCache`` - Optimized for fingerprint storage

Metrics & Utilities
-------------------

Metrics Collector
~~~~~~~~~~~~~~~~~

Centralized metrics collection for ROI visibility.

.. automodule:: GuardianLayer.metrics
   :members: MetricsCollector
   :undoc-members:
   :show-inheritance:

**Collected Metrics**:

* ``total_checks`` - All tool calls checked
* ``loops_prevented`` - Loops blocked
* ``circuit_breaks`` - Circuit breaker activations
* ``validation_failures`` - Schema validation failures
* ``tokens_saved`` - Estimated tokens saved
* ``latency_saved_ms`` - Estimated latency saved

Configuration
~~~~~~~~~~~~~

Configuration management with environment variable support.

.. automodule:: GuardianLayer.config
   :members: Config
   :undoc-members:
   :show-inheritance:

**Environment Variables**:

* ``GUARDIAN_DB_PATH`` - Database file path
* ``GUARDIAN_MAX_HISTORY`` - Loop detection history size
* ``GUARDIAN_MAX_REPEATS`` - Max allowed repetitions
* ``GUARDIAN_FAILURE_THRESHOLD`` - Circuit breaker threshold
* ``GUARDIAN_BASE_COOLDOWN`` - Circuit breaker cooldown
* ``GUARDIAN_ADVICE_STYLE`` - Advice generation style

See :doc:`configuration` for complete reference.

Type Definitions
----------------

**Tool Call Format**:

.. code-block:: python

   tool_call = {
       "tool": str,           # Tool name
       "arguments": dict      # Tool arguments
   }

**Check Result Format**:

.. code-block:: python

   result = {
       "allowed": bool,              # Whether call is allowed
       "reason": Optional[str],      # Block reason if not allowed
       "suggestion": Optional[str],  # Suggestion if blocked
       "advice": str,                # Context-aware advice
       "health_score": int,          # 0-100 health score
       "is_probe": bool              # Whether this is a recovery probe
   }

**MCP Tool Schema Format**:

.. code-block:: python

   mcp_tool = {
       "name": str,
       "description": str,
       "inputSchema": {
           "type": "object",
           "properties": dict,
           "required": List[str]
       }
   }

Usage Examples
--------------

**Basic Initialize and Check**:

.. code-block:: python

   from GuardianLayer import GuardianLayer
   
   guardian = GuardianLayer(db_path="experience.db")
   result = guardian.check({"tool": "search", "arguments": {"q": "test"}})
   
   if result["allowed"]:
       # Execute tool
       guardian.report_result(tool_call, success=True)

**Async Usage**:

.. code-block:: python

   result = await guardian.check_async(tool_call)
   if result["allowed"]:
       await guardian.report_result_async(tool_call, success=True)

**Custom Storage Provider**:

.. code-block:: python

   from GuardianLayer.interfaces import StorageProvider
   
   class CustomStorage(StorageProvider):
       def init(self): pass
       def log_incident(self, data): pass
       # Implement other methods...
   
   guardian = GuardianLayer(storage_provider=CustomStorage())

**Custom Cache Provider**:

.. code-block:: python

   from GuardianLayer.interfaces import CacheProvider
   
   class RedisCache(CacheProvider):
       def get(self, key): pass
       def set(self, key, value, ttl): pass
       # Implement other methods...
   
   guardian = GuardianLayer(cache_provider=RedisCache())

See Also
--------

* :doc:`quickstart` - Get started quickly
* :doc:`architecture` - Understand the design
* :doc:`configuration` - Configure GuardianLayer
* :doc:`integration` - Framework integration examples
* :doc:`troubleshooting` - Common issues and solutions

