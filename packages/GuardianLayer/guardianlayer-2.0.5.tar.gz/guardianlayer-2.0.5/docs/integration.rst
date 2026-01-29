Integration Guide
==================

This guide shows how to integrate GuardianLayer with popular AI agent frameworks and custom systems.

LangChain Integration
----------------------

**Basic Integration**:

.. code-block:: python

   from langchain.agents import AgentExecutor, create_openai_functions_agent
   from langchain_openai import ChatOpenAI
   from langchain.tools import Tool
   from GuardianLayer import GuardianLayer
   
   # Initialize Guardian
   guardian = GuardianLayer(db_path="langchain_experience.db")
   
   # Wrap your tools with GuardianLayer
   def create_guarded_tool(original_tool: Tool) -> Tool:
       def guarded_func(*args, **kwargs):
           # Convert to GuardianLayer format
           tool_call = {
               "tool": original_tool.name,
               "arguments": {"args": args, "kwargs": kwargs}
           }
           
           # Check with Guardian
           result = guardian.check(tool_call)
           
           if not result["allowed"]:
               return f"Tool blocked: {result['reason']}. {result['suggestion']}"
           
           # Execute original tool
           try:
               response = original_tool.func(*args, **kwargs)
               guardian.report_result(tool_call, success=True)
               return response
           except Exception as e:
               guardian.report_result(tool_call, success=False, error=str(e))
               raise
       
       return Tool(
           name=original_tool.name,
           description=original_tool.description,
           func=guarded_func
       )
   
   # Create guarded tools
   guarded_tools = [create_guarded_tool(tool) for tool in original_tools]
   
   # Create agent with guarded tools
   agent = create_openai_functions_agent(llm, guarded_tools, prompt)
   agent_executor = AgentExecutor(agent=agent, tools=guarded_tools)

**With Self-Awareness**:

.. code-block:: python

   from langchain.prompts import ChatPromptTemplate
   
   # Inject awareness into system prompt
   awareness = guardian.get_awareness_context()
   
   prompt = ChatPromptTemplate.from_messages([
       ("system", f"""You are a helpful AI assistant.
       
       {awareness}
       
       Use tools carefully based on the health information above."""),
       ("human", "{input}"),
       ("placeholder", "{agent_scratchpad}")
   ])

AutoGen Integration
-------------------

.. code-block:: python

   import autogen
   from GuardianLayer import GuardianLayer
   
   guardian = GuardianLayer(db_path="autogen_experience.db")
   
   # Create guarded function calling wrapper
   class GuardedAssistant(autogen.AssistantAgent):
       def __init__(self, *args, **kwargs):
           super().__init__(*args, **kwargs)
           self.guardian = guardian
       
       def generate_reply(self, messages, sender, config):
           # Check if this is a function call
           last_msg = messages[-1] if messages else {}
           
           if "function_call" in last_msg:
               func_call = last_msg["function_call"]
               tool_call = {
                   "tool": func_call["name"],
                   "arguments": func_call["arguments"]
               }
               
               # Check with Guardian
               result = self.guardian.check(tool_call)
               
               if not result["allowed"]:
                   return {
                       "role": "function",
                       "name": func_call["name"],
                       "content": f"Blocked: {result['reason']}"
                   }
           
           # Proceed with normal generation
           return super().generate_reply(messages, sender, config)
   
   # Use GuardedAssistant instead of AssistantAgent
   assistant = GuardedAssistant(
       name="assistant",
       llm_config={"config_list": config_list}
   )

CrewAI Integration
------------------

.. code-block:: python

   from crewai import Agent, Task, Crew
   from crewai.tools import BaseTool
   from GuardianLayer import GuardianLayer
   
   guardian = GuardianLayer(db_path="crewai_experience.db")
   
   # Wrap CrewAI tools
   class GuardedTool(BaseTool):
       def __init__(self, original_tool: BaseTool, guardian: GuardianLayer):
           super().__init__(
               name=original_tool.name,
               description=original_tool.description
           )
           self.original_tool = original_tool
           self.guardian = guardian
       
       def _run(self, *args, **kwargs):
           tool_call = {
               "tool": self.name,
               "arguments": {"args": args, "kwargs": kwargs}
           }
           
           result = self.guardian.check(tool_call)
           
           if not result["allowed"]:
               return f"Tool blocked: {result['reason']}"
           
           try:
               response = self.original_tool._run(*args, **kwargs)
               self.guardian.report_result(tool_call, success=True)
               return response
           except Exception as e:
               self.guardian.report_result(tool_call, success=False, error=str(e))
               raise
   
   # Create guarded tools
   guarded_tools = [GuardedTool(tool, guardian) for tool in original_tools]
   
   # Create agent with guarded tools
   agent = Agent(
       role='researcher',
       goal='Research information safely',
       tools=guarded_tools,
       verbose=True
   )

OpenAI Assistants API Integration
----------------------------------

.. code-block:: python

   from openai import OpenAI
   from GuardianLayer import GuardianLayer
   
   client = OpenAI()
   guardian = GuardianLayer(db_path="openai_experience.db")
   
   # Implement function calling with GuardianLayer
   def run_with_guardian(thread_id: str, assistant_id: str):
       run = client.beta.threads.runs.create(
           thread_id=thread_id,
           assistant_id=assistant_id
       )
       
       while True:
           run = client.beta.threads.runs.retrieve(
               thread_id=thread_id,
               run_id=run.id
           )
           
           if run.status == "requires_action":
               tool_calls = run.required_action.submit_tool_outputs.tool_calls
               tool_outputs = []
               
               for tool_call in tool_calls:
                   # Check with Guardian
                   guardian_check = guardian.check({
                       "tool": tool_call.function.name,
                       "arguments": eval(tool_call.function.arguments)
                   })
                   
                   if not guardian_check["allowed"]:
                       output = f"Blocked: {guardian_check['reason']}"
                   else:
                       # Execute function
                       try:
                           output = execute_function(
                               tool_call.function.name,
                               tool_call.function.arguments
                           )
                           guardian.report_result(
                               {"tool": tool_call.function.name},
                               success=True
                           )
                       except Exception as e:
                           output = str(e)
                           guardian.report_result(
                               {"tool": tool_call.function.name},
                               success=False,
                               error=str(e)
                           )
                   
                   tool_outputs.append({
                       "tool_call_id": tool_call.id,
                       "output": output
                   })
               
               # Submit tool outputs
               client.beta.threads.runs.submit_tool_outputs(
                   thread_id=thread_id,
                   run_id=run.id,
                   tool_outputs=tool_outputs
               )
           
           elif run.status == "completed":
               break

FastAPI Integration (Async)
----------------------------

.. code-block:: python

   from fastapi import FastAPI, HTTPException
   from pydantic import BaseModel
   from GuardianLayer import GuardianLayer
   from GuardianLayer.providers import AsyncSQLiteStorageProvider
   
   app = FastAPI()
   
   # Use async storage for FastAPI
   storage = AsyncSQLiteStorageProvider("fastapi_experience.db")
   guardian = GuardianLayer(storage_provider=storage)
   
   class ToolCall(BaseModel):
       tool: str
       arguments: dict
   
   @app.on_event("startup")
   async def startup():
       await storage.init()
   
   @app.on_event("shutdown")
   async def shutdown():
       await guardian.close_async()
   
   @app.post("/check_tool")
   async def check_tool(tool_call: ToolCall):
       result = await guardian.check_async(tool_call.dict())
       
       if not result["allowed"]:
           raise HTTPException(
               status_code=403,
               detail={
                   "reason": result["reason"],
                   "suggestion": result["suggestion"]
               }
           )
       
       return {"allowed": True, "advice": result["advice"]}
   
   @app.post("/execute_tool")
   async def execute_tool(tool_call: ToolCall):
       # Check first
       result = await guardian.check_async(tool_call.dict())
       
       if not result["allowed"]:
           raise HTTPException(status_code=403, detail=result["reason"])
       
       # Execute
       try:
           response = await execute_tool_async(tool_call)
           await guardian.report_result_async(
               tool_call.dict(),
               success=True
           )
           return response
       except Exception as e:
           await guardian.report_result_async(
               tool_call.dict(),
               success=False,
               error=str(e)
           )
           raise HTTPException(status_code=500, detail=str(e))

MCP Server Integration
-----------------------

GuardianLayer works seamlessly with MCP (Model Context Protocol) servers:

.. code-block:: python

   import mcp
   from GuardianLayer import GuardianLayer
   
   # Connect to MCP server
   client = mcp.Client("mcp://localhost:3000")
   
   # Initialize Guardian
   guardian = GuardianLayer()
   
   # Ingest available tools from MCP server
   mcp_tools = client.list_tools()
   count = guardian.ingest_tools(mcp_tools)
   print(f"Registered {count} tools from MCP server")
   
   # Use tools with Guardian protection
   tool_call = {"tool": "web_search", "arguments": {"query": "test"}}
   result = guardian.check(tool_call)
   
   if result["allowed"]:
       response = client.call_tool(
           tool_call["tool"],
           tool_call["arguments"]
       )

**Creating a Guarded MCP Server**:

.. code-block:: python

   from mcp.server import Server, Tool
   from GuardianLayer import GuardianLayer
   
   app = Server("guarded-tools")
   guardian = GuardianLayer()
   
   @app.tool()
   async def web_search(query: str, max_results: int = 5):
       \"\"\"Search the web\"\"\"
       tool_call = {
           "tool": "web_search",
           "arguments": {"query": query, "max_results": max_results}
       }
       
       result = await guardian.check_async(tool_call)
       
       if not result["allowed"]:
           return {"error": result["reason"], "suggestion": result["suggestion"]}
       
       # Execute search
       try:
           results = await perform_search(query, max_results)
           await guardian.report_result_async(tool_call, success=True)
           return results
       except Exception as e:
           await guardian.report_result_async(tool_call, success=False, error=str(e))
           raise

Redis for Distributed Systems
------------------------------

For multi-process or multi-server deployments:

.. code-block:: python

   from GuardianLayer import GuardianLayer
   from GuardianLayer.interfaces import CacheProvider
   import redis
   import pickle
   
   class RedisCacheProvider(CacheProvider):
       def __init__(self, redis_url: str):
           self.client = redis.from_url(redis_url)
       
       def get(self, key: str):
           value = self.client.get(key)
           return pickle.loads(value) if value else None
       
       def set(self, key: str, value, ttl=None):
           self.client.set(key, pickle.dumps(value), ex=ttl)
       
       def delete(self, key: str):
           self.client.delete(key)
       
       def get_stats(self):
           info = self.client.info("stats")
           return {
               "hits": info.get("keyspace_hits", 0),
               "misses": info.get("keyspace_misses", 0)
           }
   
   # Use Redis cache across processes
   cache = RedisCacheProvider("redis://localhost:6379/0")
   guardian = GuardianLayer(cache_provider=cache)

PostgreSQL for Production
--------------------------

For production deployments with PostgreSQL:

.. code-block:: python

   from GuardianLayer.interfaces import AsyncStorageProvider
   import asyncpg
   
   class PostgreSQLStorageProvider(AsyncStorageProvider):
       def __init__(self, dsn: str):
           self.dsn = dsn
           self.pool = None
       
       async def init(self):
           self.pool = await asyncpg.create_pool(self.dsn)
           
           # Create tables
           async with self.pool.acquire() as conn:
               await conn.execute("""
                   CREATE TABLE IF NOT EXISTS incidents (
                       id SERIAL PRIMARY KEY,
                       session_id TEXT,
                       tool_name TEXT,
                       fingerprint TEXT,
                       success BOOLEAN,
                       timestamp DOUBLE PRECISION,
                       error_reason TEXT,
                       context_hint TEXT,
                       call_data JSONB
                   )
               """)
               
               await conn.execute("""
                   CREATE TABLE IF NOT EXISTS best_practices (
                       fingerprint TEXT PRIMARY KEY,
                       tool_name TEXT,
                       success_count INTEGER,
                       failure_count INTEGER,
                       last_success_data JSONB
                   )
               """)
       
       async def log_incident(self, incident_data):
           async with self.pool.acquire() as conn:
               await conn.execute("""
                   INSERT INTO incidents
                   (session_id, tool_name, fingerprint, success, timestamp, error_reason, call_data)
                   VALUES ($1, $2, $3, $4, $5, $6, $7)
               """, ...)
       
       # Implement other methods...
   
   # Usage
   storage = PostgreSQLStorageProvider(
       "postgresql://user:pass@localhost/guardian"
   )
   guardian = GuardianLayer(storage_provider=storage)

Custom Tool Validation
----------------------

Add domain-specific validation rules:

.. code-block:: python

   from GuardianLayer import GuardianLayer
   
   guardian = GuardianLayer()
   
   # Register validation hooks
   def validate_sql_query(tool_call):
       sql = tool_call["arguments"].get("query", "")
       
       # Prevent destructive operations
       dangerous = ["DROP", "DELETE", "TRUNCATE", "ALTER"]
       if any(keyword in sql.upper() for keyword in dangerous):
           return "Destructive SQL operations not allowed"
       
       return None  # Valid
   
   def validate_file_path(tool_call):
       path = tool_call["arguments"].get("path", "")
       
       # Prevent path traversal
       if ".." in path or path.startswith("/"):
           return "Invalid file path"
       
       return None
   
   guardian.register_hook("database_query", validate_sql_query)
   guardian.register_hook("read_file", validate_file_path)

Monitoring and Observability
-----------------------------

**Prometheus Metrics**:

.. code-block:: python

   from prometheus_client import Counter, Histogram, Gauge
   from GuardianLayer import GuardianLayer
   
   # Define metrics
   tool_calls_total = Counter(
       'guardian_tool_calls_total',
       'Total tool calls checked',
       ['tool_name', 'allowed']
   )
   
   loops_prevented = Counter(
       'guardian_loops_prevented_total',
       'Total loops prevented'
   )
   
   circuit_state = Gauge(
       'guardian_circuit_state',
       'Circuit breaker state (0=closed, 1=open, 2=half_open)',
       ['tool_name']
   )
   
   # Instrument GuardianLayer
   guardian = GuardianLayer()
   
   def check_with_metrics(tool_call):
       result = guardian.check(tool_call)
       
       tool_calls_total.labels(
           tool_name=tool_call["tool"],
           allowed=str(result["allowed"])
       ).inc()
       
       if not result["allowed"] and "loop" in result.get("reason", "").lower():
           loops_prevented.inc()
       
       return result

**Datadog Integration**:

.. code-block:: python

   from datadog import statsd
   from GuardianLayer import GuardianLayer
   
   guardian = GuardianLayer()
   
   def check_with_datadog(tool_call):
       result = guardian.check(tool_call)
       
       # Track metrics
       statsd.increment('guardian.checks.total')
       if result["allowed"]:
           statsd.increment('guardian.checks.allowed')
       else:
           statsd.increment('guardian.checks.blocked')
       
       statsd.histogram('guardian.health_score', result.get("health_score", 100))
       
       return result

Testing Your Integration
-------------------------

**Unit Tests**:

.. code-block:: python

   import pytest
   from GuardianLayer import GuardianLayer
   
   @pytest.fixture
   def guardian():
       g = GuardianLayer(db_path=":memory:")
       yield g
       g.close()
   
   def test_loop_detection(guardian):
       tool_call = {"tool": "test", "arguments": {"query": "test"}}
       
       # First 2 calls allowed
       assert guardian.check(tool_call)["allowed"]
       assert guardian.check(tool_call)["allowed"]
       
       # Third repetition blocked
       result = guardian.check(tool_call)
       assert not result["allowed"]
       assert "loop" in result["reason"].lower()

**Integration Tests**:

.. code-block:: python

   import pytest
   from your_agent import YourAgent
   from GuardianLayer import GuardianLayer
   
   @pytest.mark.asyncio
   async def test_agent_with_guardian():
       guardian = GuardianLayer(db_path=":memory:")
       agent = YourAgent(guardian=guardian)
       
       # Test that agent respects Guardian blocks
       response = await agent.run("Repeat this task 100 times")
       
       metrics = guardian.get_metrics()
       assert metrics["loops_prevented"] > 0

Next Steps
----------

- :doc:`configuration` - Configure GuardianLayer for your use case
- :doc:`api/guardianlayer` - Complete API reference
- :doc:`architecture` - Understanding the protection layers
- **examples/** - More integration examples
