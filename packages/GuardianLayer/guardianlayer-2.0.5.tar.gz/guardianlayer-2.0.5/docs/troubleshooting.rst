Troubleshooting Guide
======================

This guide helps you diagnose and resolve common issues with GuardianLayer.

Common Issues
-------------

Database Locked Errors
^^^^^^^^^^^^^^^^^^^^^^^

**Symptom**:

.. code-block:: none

   sqlite3.OperationalError: database is locked

**Cause**:

SQLite doesn't handle high concurrency well. Multiple threads/processes trying to write simultaneously.

**Solutions**:

**Option 1: Use Async Storage**

.. code-block:: python

   from GuardianLayer import GuardianLayer
   from GuardianLayer.providers import AsyncSQLiteStorageProvider
   
   storage = AsyncSQLiteStorageProvider("experience.db")
   guardian = GuardianLayer(storage_provider=storage)
   
   # Use async methods
   result = await guardian.check_async(tool_call)
   await guardian.report_result_async(tool_call, success=True)

**Option 2: Use PostgreSQL for Production**

.. code-block:: python

   # See integration.rst for PostgreSQL provider implementation
   storage = PostgreSQLStorageProvider("postgresql://...")
   guardian = GuardianLayer(storage_provider=storage)

**Option 3: Increase SQLite Timeout**

.. code-block:: python

   # Custom timeout
   import sqlite3
   conn = sqlite3.connect("experience.db", timeout=30.0)

False Positive Loop Detections
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Symptom**:

Guardian blocks legitimate repeated calls (e.g., pagination, retries).

**Solution 1: Increase Repetition Threshold**

.. code-block:: python

   # Allow more repetitions
   guardian = GuardianLayer(max_repeats=5)  # Default is 2

**Solution 2: Make Tool Calls More Unique**

.. code-block:: python

   # Add unique identifiers to arguments
   tool_call = {
       "tool": "fetch_page",
       "arguments": {
           "url": "https://example.com",
           "page": page_num,      # Different per call
           "request_id": uuid4()  # Unique ID
       }
   }

**Solution 3: Reset Between Logical Boundaries**

.. code-block:: python

   # Reset between user sessions
   guardian.reset()  # Clears history
   
   # Or start new session
   guardian.experience.start_new_session()

Circuit Breaker Too Aggressive
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Symptom**:

Circuit opens after first few failures, blocking tools unnecessarily.

**Solution: Increase Failure Threshold**

.. code-block:: python

   # Require more failures before opening
   guardian = GuardianLayer(
       failure_threshold=10,  # Default is 5
       base_cooldown=30       # Shorter cooldown
   )

**Manually Reset Circuit**:

.. code-block:: python

   # Admin override for specific tool
   guardian.reset_tool("problematic_tool")
   
   # Or reset entire guardian
   guardian.reset()

Mixing Async and Sync Methods
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Symptom**:

.. code-block:: none

   RuntimeWarning: coroutine 'check_async' was never awaited

**Cause**:

Calling async method without ``await``, or calling sync method in async context.

**Solution: Choose One Mode**

.. code-block:: python

   # ✅ Sync mode
   guardian = GuardianLayer()
   result = guardian.check(tool_call)
   guardian.report_result(tool_call, success=True)
   guardian.close()
   
   # ✅ Async mode
   guardian = GuardianLayer()
   result = await guardian.check_async(tool_call)
   await guardian.report_result_async(tool_call, success=True)
   await guardian.close_async()
   
   # ❌ DON'T MIX
   result = await guardian.check_async(tool_call)
   guardian.report_result(tool_call, success=True)  # Wrong!

Memory Usage Growing
^^^^^^^^^^^^^^^^^^^^

**Symptom**:

Guardian's memory usage increases over time.

**Causes**:

1. Large history window
2. Large cache sizes
3. Process memory accumulation

**Solutions**:

**Reduce History Window**:

.. code-block:: python

   guardian = GuardianLayer(max_history=5)  # Default is 10

**Limit Cache Size**:

.. code-block:: python

   from GuardianLayer.providers import InMemoryCacheProvider
   
   cache = InMemoryCacheProvider(max_size=100)  # Default is 1000
   guardian = GuardianLayer(cache_provider=cache)

**Reset Periodically**:

.. code-block:: python

   # Reset process memory between sessions
   guardian.reset()

Validation Always Failing
^^^^^^^^^^^^^^^^^^^^^^^^^^

**Symptom**:

All tool calls fail validation even when they look correct.

**Debug Steps**:

**1. Check Tool Registration**:

.. code-block:: python

   # Verify tools are registered
   tools = guardian.mcp_facade.list_tools()
   print(f"Registered tools: {tools}")
   
   # Check specific tool schema
   schema = guardian.mcp_facade.get_tool("web_search")
   print(f"Schema: {schema}")

**2. Enable Debug Logging**:

.. code-block:: python

   import logging
   logging.basicConfig(level=logging.DEBUG)
   
   result = guardian.check(tool_call)
   # Will show detailed validation steps

**3. Check Parameter Names**:

.. code-block:: python

   # Tool call format must match
   tool_call = {
       "tool": "web_search",      # Must match registered name
       "arguments": {              # Use "arguments" not "params"
           "query": "test"          # Must match schema
       }
   }

Import Errors
^^^^^^^^^^^^^

**Symptom**:

.. code-block:: none

   ImportError: cannot import name 'GuardianLayer'

**Solution**: Ensure correct import path:

.. code-block:: python

   # ✅ Correct
   from GuardianLayer import GuardianLayer
   
   # ❌ Wrong
   from guardian import GuardianLayer
   from guardianlayer import GuardianLayer

Performance Issues
------------------

Slow Check Operations
^^^^^^^^^^^^^^^^^^^^^

**Symptom**:

``guardian.check()`` takes > 100ms.

**Diagnosis**:

.. code-block:: python

   import time
   
   start = time.time()
   result = guardian.check(tool_call)
   elapsed = (time.time() - start) * 1000
   print(f"Check took {elapsed:.2f}ms")

**Solutions**:

**Use Async Mode**:

.. code-block:: python

   # Non-blocking DB I/O
   result = await guardian.check_async(tool_call)

**Enable Caching**:

.. code-block:: python

   # Cache is enabled by default, but verify:
   cache = guardian.mcp_facade.get_cache_stats()
   print(f"Hit rate: {cache['hit_rate']:.1%}")

**Reduce DB Queries**:

.. code-block:: python

   # Use in-memory mode for testing
   guardian = GuardianLayer(db_path=":memory:")

High Database Size
^^^^^^^^^^^^^^^^^^

**Symptom**:

``experience.db`` grows to GB size.

**Solution: Implement Retention Policy**:

.. code-block:: python

   from datetime import datetime, timedelta
   
   def cleanup_old_incidents(guardian, days=30):
       cutoff = (datetime.now() - timedelta(days=days)).timestamp()
       
       # Access storage directly
       with guardian.experience._storage._session() as session:
           session.execute(
               "DELETE FROM incidents WHERE timestamp < :cutoff",
               {"cutoff": cutoff}
           )
           session.commit()
   
   # Run as cron job
   cleanup_old_incidents(guardian, days=30)

Debugging
---------

Enable Detailed Logging
^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   import logging
   
   # Enable all GuardianLayer logs
   logging.basicConfig(
       level=logging.DEBUG,
       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
   )
   
   # Or just GuardianLayer
   logger = logging.getLogger("GuardianLayer")
   logger.setLevel(logging.DEBUG)

Inspect Internal State
^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   # Check loop detector state
   print("History:", guardian.loop_detector._history)
   print("Repeat counts:", guardian.loop_detector._repeat_counts)
   
   # Check health monitor
   health = guardian.health_monitor.get_all_health()
   for tool, status in health.items():
       print(f"{tool}: {status}")
   
   # Check experience layer
   stats = guardian.experience.get_session_stats()
   print(f"Session stats: {stats}")
   
   # Check metrics
   metrics = guardian.get_metrics()
   print(f"Metrics: {metrics}")

Test in Isolation
^^^^^^^^^^^^^^^^^

.. code-block:: python

   # Test each layer independently
   from GuardianLayer import LoopDetector, HealthMonitor, MCPFacade
   
   # Test loop detector
   detector = LoopDetector()
   call = {"tool": "test", "arguments": {}}
   is_loop, reason = detector.check(call)
   print(f"Loop: {is_loop}, Reason: {reason}")
   
   # Test health monitor
   monitor = HealthMonitor()
   status = monitor.check_tool("test")
   print(f"Health status: {status}")

Common Error Messages
---------------------

"Tool not registered"
^^^^^^^^^^^^^^^^^^^^^

**Cause**: Tool not ingested into MCP facade.

**Solution**:

.. code-block:: python

   # Ingest tools first
   mcp_tools = [...]
   guardian.ingest_tools(mcp_tools)

"Missing required parameter"
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Cause**: Tool call missing required argument.

**Solution**:

.. code-block:: python

   # Check schema
   schema = guardian.mcp_facade.get_tool("tool_name")
   print(f"Required params: {schema.required_params}")
   
   # Ensure all required params present
   tool_call = {
       "tool": "tool_name",
       "arguments": {
           "param1": "value1",  # Required
           "param2": "value2"   # Required
       }
   }

"Circuit breaker active"
^^^^^^^^^^^^^^^^^^^^^^^^

**Cause**: Too many consecutive failures.

**Solutions**:

.. code-block:: python

   # Wait for cooldown to expire
   import time
   time.sleep(60)
   
   # Or manually reset
   guardian.reset_tool("tool_name")

Production Deployment Issues
-----------------------------

Multi-Process Deployment
^^^^^^^^^^^^^^^^^^^^^^^^

**Issue**: Process memory not shared.

**Solution**: Use shared storage/cache:

.. code-block:: python

   # Use PostgreSQL + Redis
   storage = PostgreSQLStorageProvider("postgresql://...")
   cache = RedisCacheProvider("redis://...")
   guardian = GuardianLayer(
       storage_provider=storage,
       cache_provider=cache
   )

Database Connection Pool Exhaustion
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Issue**: Too many concurrent connections.

**Solution**: Increase pool size:

.. code-block:: python

   # For custom PostgreSQL provider
   storage = PostgreSQLStorageProvider(
       dsn="postgresql://...",
       pool_size=50  # Increase from default
   )

Docker Container Issues
^^^^^^^^^^^^^^^^^^^^^^^

**Issue**: Database file permissions or path issues.

**Solution**:

.. code-block:: dockerfile

   # Dockerfile
   FROM python:3.11
   
   # Create data directory
   RUN mkdir -p /app/data
   VOLUME /app/data
   
   # Set working directory
   WORKDIR /app
   
   # Install GuardianLayer
   RUN pip install GuardianLayer
   
   # Use volume for database
   ENV GUARDIAN_DB_PATH=/app/data/experience.db

Testing Strategies
------------------

Unit Testing
^^^^^^^^^^^^

.. code-block:: python

   import pytest
   from GuardianLayer import GuardianLayer
   
   @pytest.fixture
   def guardian():
       # Use in-memory DB for tests
       g = GuardianLayer(db_path=":memory:")
       yield g
       g.close()
   
   def test_loop_detection(guardian):
       call = {"tool": "test", "arguments": {"q": "test"}}
       
       assert guardian.check(call)["allowed"]
       assert guardian.check(call)["allowed"]
       assert not guardian.check(call)["allowed"]  # 3rd blocked

Integration Testing
^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   @pytest.mark.asyncio
   async def test_async_operations():
       guardian = GuardianLayer(db_path=":memory:")
       
       call = {"tool": "test", "arguments": {}}
       result = await guardian.check_async(call)
       assert result["allowed"]
       
       await guardian.report_result_async(call, success=True)
       await guardian.close_async()

Load Testing
^^^^^^^^^^^^

.. code-block:: python

   import asyncio
   from GuardianLayer import GuardianLayer
   
   async def load_test(num_calls=1000):
       guardian = GuardianLayer(db_path=":memory:")
       
       calls = [
           {"tool": f"tool_{i%10}", "arguments": {"id": i}}
           for i in range(num_calls)
       ]
       
       start = time.time()
       results = await asyncio.gather(*[
           guardian.check_async(call) for call in calls
       ])
       elapsed = time.time() - start
       
       print(f"{num_calls} checks in {elapsed:.2f}s")
       print(f"Throughput: {num_calls/elapsed:.0f} checks/sec")
       
       await guardian.close_async()
   
   asyncio.run(load_test())

Getting Help
------------

If you're still experiencing issues:

1. **Check GitHub Issues**: `https://github.com/Mk3Ang8l/GuardianLayer/issues <https://github.com/Mk3Ang8l/GuardianLayer/issues>`_
2. **Enable Debug Logging**: Capture detailed logs and include in issue report
3. **Provide Minimal Reproduction**: Create a minimal example that reproduces the issue  
4. **Check Documentation**: Review :doc:`architecture`, :doc:`configuration`, and :doc:`integration`
5. **Community Support**: Ask in GitHub Discussions

Bug Report Template
^^^^^^^^^^^^^^^^^^^

.. code-block:: markdown

   **GuardianLayer Version**: (e.g., 2.0.0)
   **Python Version**: (e.g., 3.11.0)
   **Operating System**: (e.g., Ubuntu 22.04)
   
   **Description**:
   Brief description of the issue
   
   **Reproduction Steps**:
   1. Step 1
   2. Step 2
   3. Step 3
   
   **Expected Behavior**:
   What you expected to happen
   
   **Actual Behavior**:
   What actually happened
   
   **Code Sample**:
   ```python
   Minimal code to reproduce
   ```
   
   **Logs**:
   ```
   Relevant log output
   ```

Next Steps
----------

- :doc:`configuration` - Fine-tune your configuration
- :doc:`architecture` - Understand how GuardianLayer works
- :doc:`integration` - See integration examples
- **GitHub Issues**: Report bugs or request features
