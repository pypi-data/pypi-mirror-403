Welcome to GuardianLayer's documentation!
========================================

**GuardianLayer** is a production-ready meta-cognition layer for AI agents that prevents infinite loops, learns from failures, and provides self-awareness capabilities for safer, more reliable AI systems.

.. note::
   GuardianLayer v2.0 introduces smart circuit breakers, error classification, and async support for high-performance applications.

What is GuardianLayer?
-----------------------

GuardianLayer acts as a safety shield between your AI agent and external tools, providing:

* **Loop Detection**: O(1) hash-based detection prevents infinite repetition
* **Circuit Breaking**: Smart health monitoring with automatic recovery
* **Schema Validation**: MCP-compatible tool call validation
* **Experience Learning**: Learn from past successes and failures
* **Self-Awareness**: Inject context into LLM prompts for better decision-making

Key Features
------------

🛡️ **5-Layer Protection System**
   Defense-in-depth approach with circuit breaker, loop detection, validation, learning, and advice generation

⚡ **High Performance**
   O(1) loop detection, smart caching, async/await support, sub-100ms latency

🔌 **Framework Agnostic**
   Works with LangChain, AutoGen, CrewAI, OpenAI Assistants, and any custom AI framework

📊 **Production Ready**
   Health scoring, metrics, observability, PostgreSQL/Redis support, multi-process deployment

🎯 **MCP Compatible**
   Full support for Model Context Protocol (MCP) tool schemas

Table of Contents
-----------------

.. toctree::
   :maxdepth: 2
   :caption: Getting Started

   quickstart
   architecture
   configuration

.. toctree::
   :maxdepth: 2
   :caption: Integration Guides

   integration
   troubleshooting

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   api

Quick links
-----------

* :ref:`installation`
* :ref:`quickstart`
* :doc:`architecture`
* :doc:`integration`
* :doc:`api`
* :doc:`troubleshooting`

Installation
------------

.. _installation:

Install from PyPI:

.. code-block:: console

   pip install GuardianLayer

Or install from source (development):

.. code-block:: console

   git clone https://github.com/Mk3Ang8l/GuardianLayer.git
   cd GuardianLayer
   pip install -e '.[dev]'

Quick Start
-----------

.. _quickstart:

A minimal example to get started:

.. code-block:: python

   from GuardianLayer import GuardianLayer
   
   # Initialize the guardian
   guardian = GuardianLayer(db_path="experience.db")
   
   # Register MCP tools
   mcp_tools = [{
       "name": "web_search",
       "description": "Search the web",
       "inputSchema": {
           "type": "object",
           "properties": {"query": {"type": "string"}},
           "required": ["query"]
       }
   }]
   guardian.ingest_tools(mcp_tools)
   
   # Check a tool call
   tool_call = {"tool": "web_search", "arguments": {"query": "Python tutorials"}}
   result = guardian.check(tool_call)
   
   if result["allowed"]:
       # Execute your tool
       response = execute_tool(tool_call)
       guardian.report_result(tool_call, success=True)
   else:
       print(f"Blocked: {result['reason']}")

For more complete examples, see :doc:`quickstart` and the ``examples/`` directory.

How It Works
------------

GuardianLayer implements a **5-layer protection model**:

**Layer 0: Circuit Breaker**
   Prevents hammering failing tools with 3-state pattern (CLOSED/OPEN/HALF_OPEN)

**Layer 1: Loop Detection**
   Hash-based O(1) detection of infinite loops and repetitive behavior

**Layer 2: Schema Validation**
   Validates tool calls against MCP schemas with custom hooks

**Layer 3: Experience Learning**
   Multi-tiered storage learns from past successes and failures

**Layer 4: Advice Generation**
   Context-aware prompt injection guides AI behavior

See :doc:`architecture` for detailed explanation.

Core Components
---------------

GuardianLayer
~~~~~~~~~~~~~

The main orchestrator combining all protection layers.

.. code-block:: python

   from GuardianLayer import GuardianLayer, AdviceStyle
   
   guardian = GuardianLayer(
       db_path="experience.db",
       max_repeats=2,
       failure_threshold=5,
       advice_style=AdviceStyle.EXPERT
   )

LoopDetector
~~~~~~~~~~~~

Hash-based loop detection with O(1) performance.

.. code-block:: python

   from GuardianLayer import LoopDetector
   
   detector = LoopDetector(max_history=10, max_repeats=2)
   is_loop, reason = detector.check(tool_call)

HealthMonitor
~~~~~~~~~~~~~

Smart circuit breaker with error classification and auto-recovery.

.. code-block:: python

   from GuardianLayer import HealthMonitor
   
   monitor = HealthMonitor(failure_threshold=5, base_cooldown=60)
   status = monitor.check_tool("tool_name")

MCPFacade
~~~~~~~~~

MCP-compatible tool schema validation.

.. code-block:: python

   from GuardianLayer import MCPFacade
   
   facade = MCPFacade()
   facade.ingest_mcp_tools(mcp_tools)
   result = facade.validate_call(tool_call)

ExperienceLayer
~~~~~~~~~~~~~~~

Multi-tiered learning from past interactions.

.. code-block:: python

   from GuardianLayer import ExperienceLayer
   
   experience = ExperienceLayer(db_path="experience.db")
   reliability = experience.get_tool_reliability("tool_name")

AdviceGenerator
~~~~~~~~~~~~~~~

Context-aware advice for prompt injection.

.. code-block:: python

   from GuardianLayer import AdviceGenerator, AdviceStyle
   
   advice_gen = AdviceGenerator(style=AdviceStyle.EXPERT)
   advice = advice_gen.generate(context)

Usage Patterns
--------------

**Basic Pattern**:

.. code-block:: python

   result = guardian.check(tool_call)
   if result["allowed"]:
       response = execute_tool(tool_call)
       guardian.report_result(tool_call, success=True)

**Async Pattern**:

.. code-block:: python

   result = await guardian.check_async(tool_call)
   if result["allowed"]:
       response = await execute_tool_async(tool_call)
       await guardian.report_result_async(tool_call, success=True)

**With Self-Awareness**:

.. code-block:: python

   awareness = guardian.get_awareness_context()
   prompt = f"System: {awareness}\n\nUser: {message}"

**Custom Validation**:

.. code-block:: python

   def validate_sql(tool_call):
       if "DROP TABLE" in tool_call["arguments"].get("sql", ""):
           return "Destructive SQL not allowed"
       return None
   
   guardian.register_hook("database_query", validate_sql)

Framework Integration
---------------------

GuardianLayer integrates seamlessly with popular AI frameworks:

* **LangChain**: Wrap tools with GuardianLayer checks
* **AutoGen**: Integrate into AssistantAgent
* **CrewAI**: Wrap CrewAI tools
* **OpenAI Assistants**: Validate function calls
* **FastAPI**: Use async mode for high performance
* **MCP Servers**: Native MCP protocol support

See :doc:`integration` for detailed examples.

Examples and Testing
--------------------

See the ``examples/`` and ``tests/`` directories for real usage patterns and test coverage.

**Run examples**:

.. code-block:: console

   python examples/demo.py
   python examples/demo_v2.py
   python examples/demo_cache_perf.py

**Run tests**:

.. code-block:: console

   pytest tests/ -v --cov=src

Configuration
-------------

GuardianLayer can be configured via constructor parameters or environment variables:

.. code-block:: bash

   export GUARDIAN_DB_PATH="./experience.db"
   export GUARDIAN_MAX_REPEATS=2
   export GUARDIAN_FAILURE_THRESHOLD=5
   export GUARDIAN_ADVICE_STYLE="expert"

See :doc:`configuration` for complete reference.

Contributing
------------

We welcome contributions! Please follow these guidelines:

1. Create an issue to discuss major changes
2. Fork the repository and create a pull request
3. Add tests for any new functionality
4. Ensure linters and tests pass locally

See ``CONTRIBUTING.md`` for detailed guidelines.

License
-------

GuardianLayer is licensed under the MIT License. See ``LICENSE`` for details.

Changelog
---------

See ``CHANGELOG.md`` for a history of notable changes and releases.

Support and Community
---------------------

* **Documentation**: This site
* **GitHub Issues**: `Report bugs or request features <https://github.com/Mk3Ang8l/GuardianLayer/issues>`_

* **Examples**: Browse the ``examples/`` directory

Performance Tips
----------------

* Use ``check_async()`` for non-blocking DB operations
* Enable caching (enabled by default)
* Use PostgreSQL for multi-server deployments
* Use Redis for distributed caching
* Tune ``max_history`` and cache sizes for your workload

See :doc:`troubleshooting` for optimization strategies.

Building the Docs Locally
--------------------------

1. Install requirements:

   .. code-block:: console

      pip install -r docs/requirements.txt

2. Build HTML documentation:

   .. code-block:: console

      cd docs
      sphinx-build -b html . _build/html

3. Open ``docs/_build/html/index.html`` in your browser

Indices and Tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

