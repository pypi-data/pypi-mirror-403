Quick Start Guide
==================

This guide will get you up and running with GuardianLayer in under 5 minutes.

Installation
------------

Install GuardianLayer from PyPI:

.. code-block:: console

   pip install GuardianLayer

Your First Guardian
-------------------

Let's create a simple guardian to protect an AI agent's tool calls:

.. code-block:: python

   from GuardianLayer import GuardianLayer, AdviceStyle
   
   # Initialize with default settings
   guardian = GuardianLayer(
       db_path="my_agent_experience.db",
       max_repeats=2,
       advice_style=AdviceStyle.CONCISE
   )
   
   print("🛡️ GuardianLayer initialized!")

Registering Tools
-----------------

GuardianLayer works with MCP (Model Context Protocol) compatible tool schemas:

.. code-block:: python

   # Define your tools in MCP format
   mcp_tools = [
       {
           "name": "web_search",
           "description": "Search the web for information",
           "inputSchema": {
               "type": "object",
               "properties": {
                   "query": {"type": "string"},
                   "max_results": {"type": "integer"}
               },
               "required": ["query"]
           }
       },
       {
           "name": "calculator",
           "description": "Perform mathematical calculations",
           "inputSchema": {
               "type": "object",
               "properties": {
                   "expression": {"type": "string"}
               },
               "required": ["expression"]
           }
       }
   ]
   
   # Register tools with GuardianLayer
   count = guardian.ingest_tools(mcp_tools)
   print(f"✅ Registered {count} tools")

Validating Tool Calls
----------------------

Before executing any tool call, check it through GuardianLayer:

.. code-block:: python

   # A proposed tool call from your AI agent
   tool_call = {
       "tool": "web_search",
       "arguments": {
           "query": "Python tutorials",
           "max_results": 5
       }
   }
   
   # Check if the call should be allowed
   result = guardian.check(tool_call)
   
   if result["allowed"]:
       print("✅ Tool call allowed")
       # Execute your tool here
       response = execute_tool(tool_call)
       
       # Report the result for learning
       guardian.report_result(tool_call, success=True)
   else:
       print(f"❌ Tool call blocked!")
       print(f"Reason: {result['reason']}")
       print(f"Suggestion: {result['suggestion']}")

Loop Detection in Action
-------------------------

GuardianLayer automatically detects when your AI is stuck in a loop:

.. code-block:: python

   # Simulate an AI repeating the same call
   bad_call = {"tool": "web_search", "arguments": {"query": "impossible query"}}
   
   for i in range(4):
       result = guardian.check(bad_call)
       print(f"Attempt {i+1}: Allowed={result['allowed']}")
       
       if result['allowed']:
           # Simulate failure
           guardian.report_result(bad_call, success=False, error="No results")
   
   # Output:
   # Attempt 1: Allowed=True
   # Attempt 2: Allowed=True
   # Attempt 3: Allowed=False  ← Loop detected!

Circuit Breaker Protection
---------------------------

The circuit breaker prevents hammering failing tools:

.. code-block:: python

   failing_call = {"tool": "broken_api", "arguments": {"data": "test"}}
   
   # Simulate multiple failures
   for i in range(7):
       result = guardian.check(failing_call)
       
       if result['allowed']:
           guardian.report_result(
               failing_call,
               success=False,
               error="Connection timeout"
           )
           print(f"Attempt {i+1}: Failed")
       else:
           print(f"Attempt {i+1}: BLOCKED ({result['reason']})")
   
   # After 5 failures, the circuit opens and blocks further calls

Self-Awareness Injection
-------------------------

Inject awareness context into your LLM prompts:

.. code-block:: python

   # Get current awareness state
   awareness = guardian.get_awareness_context()
   
   # Inject into your prompt
   system_prompt = f"""
   You are a helpful AI assistant with access to tools.
   
   {awareness}
   
   Use your tools wisely based on the information above.
   """
   
   # Example output:
   # [SELF-AWARENESS]
   # 'broken_api' is temporarily disabled (circuit open).
   # 'web_search' has low health (45%).

Monitoring Tool Health
----------------------

Check the health status of your tools:

.. code-block:: python

   # Get health metrics
   health = guardian.health_monitor.get_all_health()
   
   for tool_name, status in health.items():
       print(f"{tool_name}:")
       print(f"  Health Score: {status['score']}/100")
       print(f"  State: {status['state']}")
       print(f"  Success Rate: {status['success_rate']:.1%}")

Viewing Metrics
---------------

Get insights into GuardianLayer's effectiveness:

.. code-block:: python

   metrics = guardian.get_metrics()
   
   print(f"Total checks: {metrics['total_checks']}")
   print(f"Loops prevented: {metrics['loops_prevented']}")
   print(f"Circuit breaks: {metrics['circuit_breaks']}")
   print(f"Validation failures: {metrics['validation_failures']}")
   print(f"Estimated tokens saved: {metrics['tokens_saved']}")

Async Usage
-----------

For async applications (FastAPI, asyncio, etc.):

.. code-block:: python

   import asyncio
   from GuardianLayer import GuardianLayer
   
   async def main():
       guardian = GuardianLayer(db_path="async_experience.db")
       
       tool_call = {"tool": "web_search", "arguments": {"query": "async Python"}}
       
       # Use async methods
       result = await guardian.check_async(tool_call)
       
       if result["allowed"]:
           response = await execute_tool_async(tool_call)
           await guardian.report_result_async(tool_call, success=True)
       
       # Clean up
       await guardian.close_async()
   
   asyncio.run(main())

Cleanup
-------

Always close the guardian when done (especially in async mode):

.. code-block:: python

   # Synchronous
   guardian.close()
   
   # Asynchronous
   await guardian.close_async()

Next Steps
----------

Now that you've mastered the basics, explore:

- :doc:`architecture` - Understand the 5-layer protection system
- :doc:`configuration` - Configure GuardianLayer for your needs
- :doc:`integration` - Integrate with LangChain, AutoGen, and other frameworks
- :doc:`api/guardianlayer` - Complete API reference for GuardianLayer class
- **examples/** - Real-world usage examples

Common Patterns
---------------

**Pattern 1: Integration with LangChain**

.. code-block:: python

   from langchain.agents import AgentExecutor
   from GuardianLayer import GuardianLayer
   
   guardian = GuardianLayer()
   
   def guarded_tool_wrapper(tool_func):
       def wrapper(tool_call):
           result = guardian.check(tool_call)
           if not result["allowed"]:
               return {"error": result["reason"]}
           
           try:
               response = tool_func(tool_call)
               guardian.report_result(tool_call, success=True)
               return response
           except Exception as e:
               guardian.report_result(tool_call, success=False, error=str(e))
               raise
       return wrapper

**Pattern 2: Custom Storage Provider**

.. code-block:: python

   from GuardianLayer import GuardianLayer
   from GuardianLayer.providers import AsyncSQLiteStorageProvider
   
   # Use async storage for better performance
   storage = AsyncSQLiteStorageProvider("experience.db")
   guardian = GuardianLayer(storage_provider=storage)

**Pattern 3: Custom Advice Style**

.. code-block:: python

   from GuardianLayer import AdviceContext
   
   def snarky_advice(context: AdviceContext) -> str:
       if context.failure_count > 3:
           return f"Seriously? '{context.tool_name}' failed {context.failure_count} times. Try something else!"
       return ""
   
   guardian.set_custom_advice_resolver(snarky_advice)

Troubleshooting
---------------

**Issue: Database locked errors**

Solution: Use async providers or increase connection pool size.

**Issue: Too many false positives in loop detection**

Solution: Increase ``max_repeats`` parameter:

.. code-block:: python

   guardian = GuardianLayer(max_repeats=5)  # Default is 2

**Issue: Circuit breaker too aggressive**

Solution: Increase ``failure_threshold``:

.. code-block:: python

   guardian = GuardianLayer(failure_threshold=10)  # Default is 5

For more troubleshooting, see :doc:`troubleshooting`.
