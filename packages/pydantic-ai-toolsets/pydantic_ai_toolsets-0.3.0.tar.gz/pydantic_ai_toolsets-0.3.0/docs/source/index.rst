Welcome to Pydantic AI Toolsets Documentation
==============================================

A comprehensive collection of reasoning, reflection, and multi-agent toolsets for pydantic-ai agents.

Overview
--------

This package provides a rich set of toolsets that can be used individually or combined to create powerful multi-stage workflows:

- **Reasoning Toolsets**: Chain of Thought, Tree of Thought, Graph of Thought, Beam Search, Monte Carlo Tree Search
- **Reflection Toolsets**: Reflection, Self-Refine, Self-Ask
- **Multi-Agent Toolsets**: Multi-Persona Analysis, Multi-Persona Debate
- **Utility Toolsets**: Search, Todo
- **Meta-Orchestrator**: Workflow coordination and multi-toolset management

Quick Start
-----------

.. code-block:: python

   from pydantic_ai import Agent
   from pydantic_ai_toolsets import create_cot_toolset, CoTStorage

   storage = CoTStorage()
   agent = Agent("openai:gpt-4", toolsets=[create_cot_toolset(storage)])
   result = await agent.run("Solve this problem step by step")

Contents
--------

.. toctree::
   :maxdepth: 2
   :caption: Documentation:

   readme
   api
