"""Integration tests for workflow templates.

These tests verify that all workflow templates work end-to-end with proper
toolset combination, workflow progression, and unified state reading.
"""

from __future__ import annotations

import pytest

from pydantic_ai_toolsets import (
    CODE_ARCHITECT,
    CREATIVE_PROBLEM_SOLVER,
    RESEARCH_ASSISTANT,
    STRATEGIC_DECISION_MAKER,
    BeamStorage,
    GoTStorage,
    MCTSStorage,
    MetaOrchestratorStorage,
    PersonaDebateStorage,
    PersonaStorage,
    ReflectionStorage,
    SearchStorage,
    SelfAskStorage,
    SelfRefineStorage,
    TodoStorage,
    create_beam_toolset,
    create_got_toolset,
    create_mcts_toolset,
    create_persona_debate_toolset,
    create_persona_toolset,
    create_reflection_toolset,
    create_search_toolset,
    create_self_ask_toolset,
    create_self_refine_toolset,
    create_todo_toolset,
)
from pydantic_ai_toolsets.toolsets.meta_orchestrator.helpers import create_workflow_agent
from pydantic_ai_toolsets.toolsets.meta_orchestrator.types import LinkType


@pytest.mark.asyncio
async def test_research_assistant_workflow():
    """Test Research Assistant workflow end-to-end."""
    # Create storages
    storages = {
        "search": SearchStorage(track_usage=True),
        "self_ask": SelfAskStorage(track_usage=True),
        "self_refine": SelfRefineStorage(track_usage=True),
        "todo": TodoStorage(track_usage=True),
    }

    # Create toolsets
    toolsets = [
        create_search_toolset(storages["search"], id="search"),
        create_self_ask_toolset(storages["self_ask"], id="self_ask"),
        create_self_refine_toolset(storages["self_refine"], id="self_refine"),
        create_todo_toolset(storages["todo"], id="todo"),
    ]

    # Create orchestrator storage
    orchestrator_storage = MetaOrchestratorStorage(track_usage=True)

    # Create agent with workflow template
    agent = create_workflow_agent(
        model="openai:gpt-4o-mini",  # Use a cheaper model for testing
        workflow_template=RESEARCH_ASSISTANT,
        toolsets=toolsets,
        storages=storages,
        orchestrator_storage=orchestrator_storage,
    )

    # Run a simple research task
    result = await agent.run("Research what Python is and explain it briefly")

    # Verify workflow was started
    workflow = orchestrator_storage.get_active_workflow()
    assert workflow is not None
    assert workflow.template_name == "research_assistant"
    assert len(workflow.active_toolsets) == 4

    # Verify unified state can be read
    state_result = await agent.run("Read the unified state")
    assert "Unified State" in state_result.data
    assert "search" in state_result.data.lower()
    assert "self_ask" in state_result.data.lower()

    # Verify storages have data
    assert len(storages["search"].search_results) > 0 or len(storages["self_ask"].questions) > 0


@pytest.mark.asyncio
async def test_creative_problem_solver_workflow():
    """Test Creative Problem Solver workflow end-to-end."""
    # Create storages
    storages = {
        "persona": PersonaStorage(track_usage=True),
        "got": GoTStorage(track_usage=True),
        "reflection": ReflectionStorage(track_usage=True),
    }

    # Create toolsets
    toolsets = [
        create_persona_toolset(storages["persona"], id="persona"),
        create_got_toolset(storages["got"], id="got"),
        create_reflection_toolset(storages["reflection"], id="reflection"),
    ]

    # Create orchestrator storage
    orchestrator_storage = MetaOrchestratorStorage(track_usage=True)

    # Create agent with workflow template
    agent = create_workflow_agent(
        model="openai:gpt-4o-mini",
        workflow_template=CREATIVE_PROBLEM_SOLVER,
        toolsets=toolsets,
        storages=storages,
        orchestrator_storage=orchestrator_storage,
    )

    # Run a creative problem solving task
    result = await agent.run("How can we reduce plastic waste in cities? Provide a brief solution.")

    # Verify workflow was started
    workflow = orchestrator_storage.get_active_workflow()
    assert workflow is not None
    assert workflow.template_name == "creative_problem_solver"
    assert len(workflow.active_toolsets) == 3

    # Verify unified state can be read
    state_result = await agent.run("Read the unified state")
    assert "Unified State" in state_result.data


@pytest.mark.asyncio
async def test_strategic_decision_maker_workflow():
    """Test Strategic Decision Maker workflow end-to-end."""
    # Create storages
    storages = {
        "persona_debate": PersonaDebateStorage(track_usage=True),
        "mcts": MCTSStorage(track_usage=True),
        "reflection": ReflectionStorage(track_usage=True),
    }

    # Create toolsets
    toolsets = [
        create_persona_debate_toolset(storages["persona_debate"], id="persona_debate"),
        create_mcts_toolset(storages["mcts"], id="mcts"),
        create_reflection_toolset(storages["reflection"], id="reflection"),
    ]

    # Create orchestrator storage
    orchestrator_storage = MetaOrchestratorStorage(track_usage=True)

    # Create agent with workflow template
    agent = create_workflow_agent(
        model="openai:gpt-4o-mini",
        workflow_template=STRATEGIC_DECISION_MAKER,
        toolsets=toolsets,
        storages=storages,
        orchestrator_storage=orchestrator_storage,
    )

    # Run a strategic decision task
    result = await agent.run("Should a small company adopt remote work? Provide a brief decision.")

    # Verify workflow was started
    workflow = orchestrator_storage.get_active_workflow()
    assert workflow is not None
    assert workflow.template_name == "strategic_decision_maker"
    assert len(workflow.active_toolsets) == 3

    # Verify unified state can be read
    state_result = await agent.run("Read the unified state")
    assert "Unified State" in state_result.data


@pytest.mark.asyncio
async def test_code_architect_workflow():
    """Test Code Architect workflow end-to-end."""
    # Create storages
    storages = {
        "self_ask": SelfAskStorage(track_usage=True),
        "tot": GoTStorage(track_usage=True),  # Using GoTStorage as ToTStorage equivalent
        "reflection": ReflectionStorage(track_usage=True),
        "todo": TodoStorage(track_usage=True),
    }

    # Create toolsets
    toolsets = [
        create_self_ask_toolset(storages["self_ask"], id="self_ask"),
        create_got_toolset(storages["tot"], id="tot"),  # Using GoT as ToT equivalent
        create_reflection_toolset(storages["reflection"], id="reflection"),
        create_todo_toolset(storages["todo"], id="todo"),
    ]

    # Create orchestrator storage
    orchestrator_storage = MetaOrchestratorStorage(track_usage=True)

    # Create agent with workflow template
    agent = create_workflow_agent(
        model="openai:gpt-4o-mini",
        workflow_template=CODE_ARCHITECT,
        toolsets=toolsets,
        storages=storages,
        orchestrator_storage=orchestrator_storage,
    )

    # Run a code architecture task
    result = await agent.run("Design a simple REST API architecture. Provide a brief overview.")

    # Verify workflow was started
    workflow = orchestrator_storage.get_active_workflow()
    assert workflow is not None
    assert workflow.template_name == "code_architect"
    assert len(workflow.active_toolsets) == 4

    # Verify unified state can be read
    state_result = await agent.run("Read the unified state")
    assert "Unified State" in state_result.data


@pytest.mark.asyncio
async def test_cross_toolset_linking():
    """Test cross-toolset link creation and retrieval."""
    # Create storages
    storages = {
        "search": SearchStorage(track_usage=True),
        "self_ask": SelfAskStorage(track_usage=True),
    }

    # Create toolsets
    toolsets = [
        create_search_toolset(storages["search"], id="search"),
        create_self_ask_toolset(storages["self_ask"], id="self_ask"),
    ]

    # Create orchestrator storage
    orchestrator_storage = MetaOrchestratorStorage(track_usage=True)

    # Create agent
    agent = create_workflow_agent(
        model="openai:gpt-4o-mini",
        workflow_template=RESEARCH_ASSISTANT,
        toolsets=toolsets,
        storages=storages,
        orchestrator_storage=orchestrator_storage,
    )

    # Create a link manually using the tool
    from pydantic_ai_toolsets.toolsets.meta_orchestrator.types import LinkToolsetOutputsItem

    link_item = LinkToolsetOutputsItem(
        source_toolset_id="search",
        source_item_id="test_result_1",
        target_toolset_id="self_ask",
        target_item_id="test_question_1",
        link_type=LinkType.REFERENCES,
    )

    result = await agent.run(f"Create a link: search:test_result_1 → self_ask:test_question_1")

    # Verify link was created in orchestrator storage
    assert len(orchestrator_storage.links) > 0

    # Verify link was added to individual storages
    assert "test_result_1" in storages["search"].links
    assert len(storages["search"].links["test_result_1"]) > 0
    assert len(storages["self_ask"].linked_from) > 0


@pytest.mark.asyncio
async def test_workflow_progression():
    """Test that workflow stages are automatically tracked."""
    # Create storages
    storages = {
        "search": SearchStorage(track_usage=True),
        "self_ask": SelfAskStorage(track_usage=True),
    }

    # Create toolsets
    toolsets = [
        create_search_toolset(storages["search"], id="search"),
        create_self_ask_toolset(storages["self_ask"], id="self_ask"),
    ]

    # Create orchestrator storage
    orchestrator_storage = MetaOrchestratorStorage(track_usage=True)

    # Create agent
    agent = create_workflow_agent(
        model="openai:gpt-4o-mini",
        workflow_template=RESEARCH_ASSISTANT,
        toolsets=toolsets,
        storages=storages,
        orchestrator_storage=orchestrator_storage,
    )

    # Start workflow
    await agent.run("Start the research assistant workflow")

    # Get initial workflow state
    workflow = orchestrator_storage.get_active_workflow()
    assert workflow is not None
    initial_stage = workflow.current_stage
    assert initial_stage == 0

    # Suggest a transition (this should automatically update workflow stage)
    transition_result = await agent.run("Suggest transitioning from search to self_ask")

    # Verify transition was tracked
    assert len(orchestrator_storage.transitions) > 0

    # Verify workflow stage was updated (if transition was accepted)
    workflow = orchestrator_storage.get_active_workflow()
    assert workflow is not None
    # Stage may have advanced if transition was processed
    assert workflow.current_stage >= initial_stage
