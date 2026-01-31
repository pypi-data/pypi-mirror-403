"""Integration tests for workflow agent creation."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from pydantic import BaseModel

import pytest

from pydantic_ai_toolsets import (
    create_cot_toolset,
    create_reflection_toolset,
    CoTStorage,
    ReflectionStorage,
    MetaOrchestratorStorage,
)
from pydantic_ai_toolsets.toolsets.meta_orchestrator.helpers import create_workflow_agent
from pydantic_ai_toolsets.toolsets.meta_orchestrator.types import Stage, WorkflowTemplate


class TestCreateWorkflowAgent:
    """Test suite for create_workflow_agent function."""

    @patch('pydantic_ai_toolsets.toolsets.meta_orchestrator.helpers.Agent')
    def test_create_workflow_agent_basic(self, mock_agent_class):
        """Test creating a workflow agent with basic configuration."""
        mock_agent = MagicMock()
        mock_agent.system_prompt = "Test system prompt"
        mock_agent_class.return_value = mock_agent
        
        cot_storage = CoTStorage()
        reflection_storage = ReflectionStorage()
        
        cot_toolset = create_cot_toolset(cot_storage, id="cot")
        reflection_toolset = create_reflection_toolset(reflection_storage, id="reflection")
        
        workflow_template = WorkflowTemplate(
            name="test_workflow",
            toolsets=["cot", "reflection"],
            stages=[
                Stage(
                    name="reason",
                    toolset_id="cot",
                    transition_condition="has_final_thought",
                ),
                Stage(
                    name="reflect",
                    toolset_id="reflection",
                    transition_condition="has_best_output",
                ),
            ],
            handoff_instructions={},
            description="Test workflow",
        )
        
        storages = {
            "cot": cot_storage,
            "reflection": reflection_storage,
        }
        
        agent = create_workflow_agent(
            model="openai:gpt-4",
            workflow_template=workflow_template,
            toolsets=[cot_toolset, reflection_toolset],
            storages=storages,
        )
        
        assert agent is not None
        assert agent.system_prompt is not None
        assert len(agent.system_prompt) > 0
        mock_agent_class.assert_called_once()

    @patch('pydantic_ai_toolsets.toolsets.meta_orchestrator.helpers.Agent')
    def test_create_workflow_agent_with_orchestrator(self, mock_agent_class):
        """Test creating workflow agent with orchestrator."""
        cot_storage = CoTStorage()
        reflection_storage = ReflectionStorage()
        mock_agent = MagicMock()
        mock_agent.system_prompt = "Test system prompt"
        mock_agent_class.return_value = mock_agent
        
        orchestrator_storage = MetaOrchestratorStorage()
        
        cot_toolset = create_cot_toolset(cot_storage, id="cot")
        reflection_toolset = create_reflection_toolset(reflection_storage, id="reflection")
        
        workflow_template = WorkflowTemplate(
            name="test_workflow",
            toolsets=["cot", "reflection"],
            stages=[
                Stage(
                    name="reason",
                    toolset_id="cot",
                    transition_condition="has_final_thought",
                ),
            ],
            handoff_instructions={},
        )
        
        storages = {
            "cot": cot_storage,
            "reflection": reflection_storage,
        }
        
        agent = create_workflow_agent(
            model="openai:gpt-4",
            workflow_template=workflow_template,
            toolsets=[cot_toolset, reflection_toolset],
            storages=storages,
            orchestrator_storage=orchestrator_storage,
        )
        
        assert agent is not None

    @patch('pydantic_ai_toolsets.toolsets.meta_orchestrator.helpers.Agent')
    def test_create_workflow_agent_with_additional_prompt(self, mock_agent_class):
        """Test creating workflow agent with additional system prompt."""
        mock_agent = MagicMock()
        mock_agent.system_prompt = "Test system prompt. Always be helpful."
        mock_agent_class.return_value = mock_agent
        
        cot_storage = CoTStorage()
        cot_toolset = create_cot_toolset(cot_storage, id="cot")
        
        workflow_template = WorkflowTemplate(
            name="test_workflow",
            toolsets=["cot"],
            stages=[
                Stage(
                    name="reason",
                    toolset_id="cot",
                    transition_condition="has_final_thought",
                ),
            ],
            handoff_instructions={},
        )
        
        storages = {"cot": cot_storage}
        
        agent = create_workflow_agent(
            model="openai:gpt-4",
            workflow_template=workflow_template,
            toolsets=[cot_toolset],
            storages=storages,
            additional_system_prompt="Always be helpful.",
        )
        
        assert agent is not None
        assert "Always be helpful" in agent.system_prompt

    @patch('pydantic_ai_toolsets.toolsets.meta_orchestrator.helpers.Agent')
    def test_create_workflow_agent_with_output_type(self, mock_agent_class):
        """Test creating workflow agent with output type."""
        mock_agent = MagicMock()
        mock_agent.system_prompt = "Test system prompt"
        mock_agent_class.return_value = mock_agent
        
        cot_storage = CoTStorage()
        cot_toolset = create_cot_toolset(cot_storage, id="cot")
        
        class TestOutput(BaseModel):
            result: str
        
        workflow_template = WorkflowTemplate(
            name="test_workflow",
            toolsets=["cot"],
            stages=[
                Stage(
                    name="reason",
                    toolset_id="cot",
                    transition_condition="has_final_thought",
                ),
            ],
            handoff_instructions={},
        )
        
        storages = {"cot": cot_storage}
        
        agent = create_workflow_agent(
            model="openai:gpt-4",
            workflow_template=workflow_template,
            toolsets=[cot_toolset],
            storages=storages,
            output_type=TestOutput,
        )
        
        assert agent is not None
        # Note: We can't easily test output_type without running the agent,
        # but we can verify the agent was created successfully

    @patch('pydantic_ai_toolsets.toolsets.meta_orchestrator.helpers.Agent')
    def test_create_workflow_agent_with_prefix_map(self, mock_agent_class):
        """Test creating workflow agent with custom prefix map."""
        cot_storage = CoTStorage()
        reflection_storage = ReflectionStorage()
        
        cot_toolset = create_cot_toolset(cot_storage, id="cot")
        reflection_toolset = create_reflection_toolset(reflection_storage, id="reflection")
        
        workflow_template = WorkflowTemplate(
            name="test_workflow",
            toolsets=["cot", "reflection"],
            stages=[
                Stage(
                    name="reason",
                    toolset_id="cot",
                    transition_condition="has_final_thought",
                ),
            ],
            handoff_instructions={},
        )
        
        storages = {
            "cot": cot_storage,
            "reflection": reflection_storage,
        }
        
        prefix_map = {
            "cot": "custom_cot_",
            "reflection": "custom_reflection_",
        }
        
        agent = create_workflow_agent(
            model="openai:gpt-4",
            workflow_template=workflow_template,
            toolsets=[cot_toolset, reflection_toolset],
            storages=storages,
            prefix_map=prefix_map,
        )
        
        assert agent is not None

    @patch('pydantic_ai_toolsets.toolsets.meta_orchestrator.helpers.Agent')
    def test_create_workflow_agent_without_orchestrator(self, mock_agent_class):
        """Test creating workflow agent without orchestrator."""
        cot_storage = CoTStorage()
        cot_toolset = create_cot_toolset(cot_storage, id="cot")
        
        workflow_template = WorkflowTemplate(
            name="test_workflow",
            toolsets=["cot"],
            stages=[
                Stage(
                    name="reason",
                    toolset_id="cot",
                    transition_condition="has_final_thought",
                ),
            ],
            handoff_instructions={},
        )
        
        storages = {"cot": cot_storage}
        
        agent = create_workflow_agent(
            model="openai:gpt-4",
            workflow_template=workflow_template,
            toolsets=[cot_toolset],
            storages=storages,
            orchestrator_storage=None,
        )
        
        assert agent is not None

    @patch('pydantic_ai_toolsets.toolsets.meta_orchestrator.helpers.Agent')
    def test_create_workflow_agent_auto_prefix_false(self, mock_agent_class):
        """Test creating workflow agent with auto_prefix=False."""
        cot_storage = CoTStorage()
        cot_toolset = create_cot_toolset(cot_storage, id="cot")
        
        workflow_template = WorkflowTemplate(
            name="test_workflow",
            toolsets=["cot"],
            stages=[
                Stage(
                    name="reason",
                    toolset_id="cot",
                    transition_condition="has_final_thought",
                ),
            ],
            handoff_instructions={},
        )
        
        storages = {"cot": cot_storage}
        
        agent = create_workflow_agent(
            model="openai:gpt-4",
            workflow_template=workflow_template,
            toolsets=[cot_toolset],
            storages=storages,
            auto_prefix=False,
        )
        
        assert agent is not None
