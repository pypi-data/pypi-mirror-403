Architecture Overview
======================

GuardianLayer implements a multi-layered protection system inspired by defense-in-depth security principles. Each layer provides a specific type of protection, and together they create a robust safety shield for AI agents.

Protection Layers
-----------------

GuardianLayer uses a **5-layer protection model** (L0-L4), where each layer addresses a specific failure mode:

.. mermaid::

   graph TD
       A[AI Agent Proposes Tool Call] --> B[L0: Circuit Breaker]
       B -->|Health Check| C[L1: Loop Detection]
       C -->|Hash Comparison| D[L2: Schema Validation]
       D -->|MCP Validation| E[L3: Experience Learning]
       E -->|Pattern Matching| F[L4: Advice Generation]
       F -->|Context Injection| G{Allowed?}
       G -->|Yes| H[Execute Tool]
       G -->|No| I[Block + Return Advice]
       H --> J[Report Result]
       J --> E
       I --> K[Agent Receives Feedback]

Layer 0: Smart Circuit Breaker
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Purpose**: Prevent hammering failing tools and enable graceful degradation.

**How it works**:

The circuit breaker implements a three-state pattern inspired by Michael Nygard's *Release It!* pattern:

1. **CLOSED** (Normal): Tool is healthy, all calls allowed
2. **OPEN** (Failed): Tool has failed too many times, all calls blocked
3. **HALF_OPEN** (Recovery): Testing if tool has recovered with probe calls

.. code-block:: none

   CLOSED ──[5 consecutive failures]──> OPEN
   OPEN ──[cooldown expires]──> HALF_OPEN
   HALF_OPEN ──[3 probe successes]──> CLOSED
   HALF_OPEN ──[probe failure]──> OPEN (extended cooldown)

**Features**:

- **Error Classification**: Distinguishes between system errors (network, timeout) and user errors (invalid input)
- **Adaptive Cooldown**: Exponential backoff for repeated circuit opens (60s → 120s → 240s → max 3600s)
- **Health Scoring**: 0-100 score based on recent success rate
- **Probe Mechanism**: Safely tests recovery without full traffic

**Configuration**:

.. code-block:: python

   guardian = GuardianLayer(
       failure_threshold=5,    # Failures before opening circuit
       base_cooldown=60,       # Initial cooldown in seconds
       max_cooldown=3600       # Maximum cooldown duration
   )

Layer 1: Loop Detection
^^^^^^^^^^^^^^^^^^^^^^^

**Purpose**: Detect and prevent infinite loops and repetitive behavior.

**How it works**:

Uses SHA-256 hashing for O(1) loop detection instead of expensive string comparisons:

1. Compute deterministic hash of tool call (tool name + sorted arguments)
2. Check if hash exists in recent history (sliding window)
3. Track repetition count per hash
4. Detect three types of loops:
   - **Immediate repeats**: Same call twice in a row
   - **Short cycles**: Pattern repeats within 3-5 calls
   - **Excessive repeats**: Total count exceeds threshold

**Performance**:

- O(1) hash lookup vs O(n) string comparison
- Hash cache to avoid recomputing for repeated calls
- Memory-efficient: Only stores last N hashes (default 10)

**Configuration**:

.. code-block:: python

   guardian = GuardianLayer(
       max_history=10,    # Sliding window size
       max_repeats=2      # Max allowed repetitions
   )

**Metrics tracked**:

- ``total_checks``: All tool calls checked
- ``loops_detected``: Number of loops prevented
- ``immediate_repeats``: Back-to-back identical calls
- ``short_cycles``: Patterns detected
- ``detection_rate``: Percentage of calls that were loops

Layer 2: Schema Validation
^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Purpose**: Ensure tool calls match expected schemas and custom business rules.

**How it works**:

1. Parse MCP tool schemas into internal format
2. Validate tool exists in registry
3. Check required parameters are present
4. Validate parameter types match schema
5. Run custom validation hooks (if registered)
6. Cache validation results for performance

**MCP Compatibility**:

GuardianLayer is fully compatible with the Model Context Protocol (MCP):

.. code-block:: python

   # Ingest tools from any MCP server
   from mcp import Client
   
   mcp_client = Client("mcp://tool-server")
   tools = mcp_client.list_tools()
   
   guardian.ingest_tools(tools)

**Custom Hooks**:

.. code-block:: python

   def validate_sql_injection(tool_call):
       sql = tool_call["arguments"].get("query", "")
       if "DROP TABLE" in sql.upper():
           return "SQL injection attempt detected"
       return None  # Valid
   
   guardian.register_hook("database_query", validate_sql_injection)

**Validation Cache**:

Identical tool calls are cached to avoid redundant validation:

- LRU eviction policy
- Configurable TTL (default 3600s)
- Stats: ``cache_hits``, ``cache_misses``, ``hit_rate``

Layer 3: Experience Learning
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Purpose**: Learn from past successes and failures to improve future decisions.

**How it works**:

Three-tiered storage architecture:

1. **Session Memory** (Ephemeral): Current conversation stats
2. **Process Memory** (LRU Cache): Shared across sessions in same process
3. **Global Storage** (SQLite/PostgreSQL): Persistent across restarts

**Data Structures**:

.. code-block:: sql

   -- Incidents table
   CREATE TABLE incidents (
       id INTEGER PRIMARY KEY,
       session_id TEXT,
       tool_name TEXT,
       fingerprint TEXT,  -- Hash of tool call
       success BOOLEAN,
       timestamp REAL,
       error_reason TEXT,
       context_hint TEXT,
       call_data TEXT  -- Full JSON of call
   );
   
   -- Best practices table (collective intelligence)
   CREATE TABLE best_practices (
       fingerprint TEXT PRIMARY KEY,
       tool_name TEXT,
       success_count INTEGER,
       failure_count INTEGER,
       last_success_data TEXT  -- JSON of known-good call
   );

**Pattern Matching**:

When a tool call fails, GuardianLayer:

1. Searches for similar successful calls in the past
2. Compares parameters to identify what worked
3. Returns suggestions to the AI agent

**Reliability Scoring**:

.. code-block:: python

   reliability = successes / (successes + failures)
   
   # Result: 0.0 to 1.0 (0% to 100%)

Layer 4: Advice Generation
^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Purpose**: Provide context-aware guidance to the AI agent via prompt injection.

**How it works**:

1. Collect context from previous layers (failures, health, patterns)
2. Generate advice based on configured style
3. Cache advice to avoid redundant generation
4. Inject into LLM prompt for self-awareness

**Advice Styles**:

.. list-table::
   :header-rows: 1
   :widths: 20 40 40

   * - Style
     - Use Case
     - Example
   * - CONCISE
     - Small models (GPT-3.5)
     - "Tool 'search' failed 3x. Try different approach."
   * - EXPERT
     - Large models (GPT-4)
     - "[SELF-AWARENESS]\\n- Tool: search\\n- Failure count: 3\\n- Last error: timeout\\n- RECOMMENDATION: Use alternative"
   * - FRIENDLY
     - User-facing agents
     - "Hey, I noticed 'search' didn't work last time. Double-check parameters!"

**Context Injection**:

.. code-block:: python

   awareness = guardian.get_awareness_context()
   
   prompt = f"""
   You are an AI assistant.
   
   {awareness}
   
   User: {message}
   """

**Custom Resolvers**:

.. code-block:: python

   from GuardianLayer import AdviceContext
   
   def custom_advice(context: AdviceContext) -> str:
       if context.tool_reliability and context.tool_reliability < 0.3:
           return f"⚠️ Warning: {context.tool_name} has only {context.tool_reliability:.0%} reliability!"
       return ""
   
   guardian.set_custom_advice_resolver(custom_advice)

Component Interactions
----------------------

.. mermaid::

   classDiagram
       class GuardianLayer {
           +check() Dict
           +check_async() Dict
           +report_result()
           +get_awareness_context() str
       }
       
       class HealthMonitor {
           +check_tool() Dict
           +report_result()
           -_tools: Dict[ToolHealth]
       }
       
       class LoopDetector {
           +check() Tuple
           -_history: deque
           -_repeat_counts: Dict
       }
       
       class MCPFacade {
           +validate_call() Dict
           +ingest_mcp_tools()
           -_tools: Dict[ToolSchema]
       }
       
       class ExperienceLayer {
           +log_incident()
           +find_similar_success()
           +get_tool_reliability()
           -_storage: StorageProvider
       }
       
       class AdviceGenerator {
           +generate() str
           -_style: AdviceStyle
       }
       
       GuardianLayer --> HealthMonitor
       GuardianLayer --> LoopDetector
       GuardianLayer --> MCPFacade
       GuardianLayer --> ExperienceLayer
       GuardianLayer --> AdviceGenerator
       ExperienceLayer --> StorageProvider
       MCPFacade --> CacheProvider
       AdviceGenerator --> CacheProvider

Data Flow
---------

**Synchronous Flow** (``guardian.check()``):

.. code-block:: none

   1. AI proposes tool call
   2. GuardianLayer.check(tool_call)
      ├─> HealthMonitor.check_tool() [in-memory]
      ├─> LoopDetector.check()        [in-memory]
      ├─> MCPFacade.validate()        [cache + in-memory]
      ├─> ExperienceLayer queries     [cache + DB]
      └─> AdviceGenerator.generate()  [cache + CPU]
   3. Return: {allowed, reason, suggestion, advice, health_score}

**Asynchronous Flow** (``guardian.check_async()``):

.. code-block:: none

   1. AI proposes tool call
   2. await GuardianLayer.check_async(tool_call)
      ├─> await HealthMonitor.check_tool_async()       [non-blocking]
      ├─> await LoopDetector.check_async()             [non-blocking]
      ├─> await MCPFacade.validate_call_async()        [non-blocking]
      ├─> await ExperienceLayer.find_similar_success_async()  [async DB]
      └─> AdviceGenerator.generate()                   [sync, CPU-bound]
   3. Return: {allowed, reason, suggestion, advice, health_score}

Storage Architecture
--------------------

**Provider Pattern**:

GuardianLayer uses the Provider pattern for dependency injection:

.. code-block:: python

   # Sync providers
   class StorageProvider(ABC):
       def log_incident(incident_data: Dict): pass
       def get_best_practice(tool_name: str): pass
   
   class CacheProvider(ABC):
       def get(key: str): pass
       def set(key: str, value: Any, ttl: int): pass
   
   # Async providers
   class AsyncStorageProvider(ABC):
       async def log_incident(incident_data: Dict): pass
       async def get_best_practice(tool_name: str): pass

**Built-in Implementations**:

- ``SQLiteStorageProvider``: Thread-safe SQLite with SQLAlchemy
- ``AsyncSQLiteStorageProvider``: Async SQLite with aiosqlite
- ``InMemoryCacheProvider``: LRU cache with TTL support

**Custom Implementations**:

.. code-block:: python

   from GuardianLayer.interfaces import StorageProvider
   import psycopg2
   
   class PostgreSQLStorageProvider(StorageProvider):
       def __init__(self, connection_string):
           self.conn = psycopg2.connect(connection_string)
       
       def log_incident(self, incident_data):
           # Implement PostgreSQL logging
           pass
   
   guardian = GuardianLayer(
       storage_provider=PostgreSQLStorageProvider("postgresql://...")
   )

Performance Characteristics
---------------------------

.. list-table::
   :header-rows: 1
   :widths: 25 25 25 25

   * - Layer
     - Time Complexity
     - Space Complexity
     - Latency
   * - Circuit Breaker
     - O(1)
     - O(n tools)
     - < 1ms
   * - Loop Detection
     - O(1)
     - O(history size)
     - < 1ms
   * - Schema Validation
     - O(1) cached, O(m params) uncached
     - O(n tools × m params)
     - 1-5ms
   * - Experience Learning
     - O(log n) DB query
     - O(database size)
     - 5-50ms (DB I/O)
   * - Advice Generation
     - O(1) cached, O(k) uncached
     - O(cache size)
     - < 1ms cached, 1-5ms uncached

**Total latency**: Typically 10-60ms per check (mostly DB I/O).

**Optimization strategies**:

1. **Caching**: All layers use caching to minimize redundant work
2. **Async mode**: Use ``check_async()`` for non-blocking DB operations
3. **Connection pooling**: SQLite uses thread-local connections
4. **Batch operations**: Log multiple incidents in one transaction

Scalability Considerations
---------------------------

**Horizontal Scaling**:

- **Process Memory**: Not shared across processes (by design)
- **Global Storage**: Shared via database (SQLite for single-server, PostgreSQL for multi-server)
- **Recommendation**: Use PostgreSQL/Redis for multi-process deployments

**Multi-Tenant Scenarios**:

.. code-block:: python

   # Option 1: Separate guardians per tenant
   guardians = {
       tenant_id: GuardianLayer(db_path=f"tenant_{tenant_id}.db")
       for tenant_id in tenants
   }
   
   # Option 2: Single guardian with session isolation
   guardian = GuardianLayer()
   guardian.experience.start_new_session(session_id=f"tenant_{tenant_id}")

**Database Growth**:

The ``incidents`` table grows over time. Mitigation strategies:

1. **Retention policy**: Delete incidents older than N days
2. **Archival**: Move old data to cold storage
3. **Partitioning**: Use database partitioning by date

.. code-block:: python

   # Example cleanup job
   from datetime import datetime, timedelta
   
   cutoff = (datetime.now() - timedelta(days=30)).timestamp()
   guardian.experience._storage.execute(
       "DELETE FROM incidents WHERE timestamp < ?",
       (cutoff,)
   )

Security Considerations
-----------------------

**SQL Injection**:

GuardianLayer uses parameterized queries throughout:

.. code-block:: python

   # Safe: Uses parameter binding
   cursor.execute("SELECT * FROM incidents WHERE tool_name = ?", (tool_name,))
   
   # NOT used: String interpolation
   # cursor.execute(f"SELECT * FROM incidents WHERE tool_name = '{tool_name}'")

**Data Privacy**:

- Tool call arguments are stored in ``call_data`` as JSON
- Sensitive data (API keys, passwords) may be logged
- **Recommendation**: Sanitize sensitive fields before reporting:

.. code-block:: python

   def sanitize_call(tool_call):
       sanitized = tool_call.copy()
       if "api_key" in sanitized.get("arguments", {}):
           sanitized["arguments"]["api_key"] = "***REDACTED***"
       return sanitized
   
   result = guardian.check(tool_call)
   if result["allowed"]:
       guardian.report_result(sanitize_call(tool_call), success=True)

**Database Security**:

- SQLite files have no built-in encryption
- **Recommendation**: Use SQLCipher for encrypted databases, or PostgreSQL with TLS

Next Steps
----------

- :doc:`configuration` - Configure each layer for your needs
- :doc:`integration` - Integrate with your AI framework
- :doc:`api/guardianlayer` - Complete API reference
- :doc:`troubleshooting` - Performance tuning and debugging
