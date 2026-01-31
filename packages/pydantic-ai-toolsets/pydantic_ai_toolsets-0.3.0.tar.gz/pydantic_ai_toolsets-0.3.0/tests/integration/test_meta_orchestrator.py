"""Integration tests for meta-orchestrator functionality."""

from __future__ import annotations

import pytest

from pydantic_ai_toolsets import (
    create_cot_toolset,
    create_reflection_toolset,
    CoTStorage,
    ReflectionStorage,
    MetaOrchestratorStorage,
    create_meta_orchestrator_toolset,
)
from pydantic_ai_toolsets.toolsets.meta_orchestrator.helpers import register_toolsets_with_orchestrator
from pydantic_ai_toolsets.toolsets.meta_orchestrator.types import Stage, WorkflowTemplate


class TestMetaOrchestrator:
    """Test suite for meta-orchestrator functionality."""

    def test_create_orchestrator_toolset(self):
        """Test creating orchestrator toolset."""
        storage = MetaOrchestratorStorage()
        toolset = create_meta_orchestrator_toolset(storage, id="orchestrator")
        
        assert toolset is not None
        assert toolset.id == "orchestrator"

    def test_register_toolsets_with_orchestrator(self):
        """Test registering toolsets with orchestrator."""
        orchestrator_storage = MetaOrchestratorStorage()
        cot_storage = CoTStorage()
        reflection_storage = ReflectionStorage()
        
        cot_toolset = create_cot_toolset(cot_storage, id="cot")
        reflection_toolset = create_reflection_toolset(reflection_storage, id="reflection")
        
        storages = {
            "cot": cot_storage,
            "reflection": reflection_storage,
        }
        
        register_toolsets_with_orchestrator(
            orchestrator_storage=orchestrator_storage,
            toolsets=[cot_toolset, reflection_toolset],
            storages=storages,
        )
        
        # Verify toolsets are registered
        # (Implementation depends on storage structure)

    def test_workflow_template_registration(self):
        """Test workflow template registration."""
        storage = MetaOrchestratorStorage()
        
        template = WorkflowTemplate(
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
        
        storage.workflow_registry.register(template)
        
        # Verify template is registered
        registered = storage.workflow_registry.get("test_workflow")
        assert registered is not None
        assert registered.name == "test_workflow"

    def test_orchestrator_storage_initialization(self):
        """Test orchestrator storage initialization."""
        storage = MetaOrchestratorStorage()
        
        assert storage is not None
        assert hasattr(storage, "workflow_registry")

    def test_register_toolsets_with_storages(self):
        """Test register_toolsets_with_orchestrator with storages."""
        from pydantic_ai_toolsets.toolsets.meta_orchestrator.helpers import register_toolsets_with_orchestrator
        orchestrator_storage = MetaOrchestratorStorage()
        cot_storage = CoTStorage()
        reflection_storage = ReflectionStorage()
        
        cot_toolset = create_cot_toolset(cot_storage, id="cot")
        reflection_toolset = create_reflection_toolset(reflection_storage, id="reflection")
        
        storages = {
            "cot": cot_storage,
            "reflection": reflection_storage,
        }
        
        register_toolsets_with_orchestrator(
            orchestrator_storage=orchestrator_storage,
            toolsets=[cot_toolset, reflection_toolset],
            storages=storages,
        )
        
        # Verify toolsets are registered with storage
        assert "cot" in orchestrator_storage.registered_toolsets
        assert "reflection" in orchestrator_storage.registered_toolsets
        assert orchestrator_storage.registered_toolsets["cot"]["storage"] == cot_storage
        assert orchestrator_storage.registered_toolsets["reflection"]["storage"] == reflection_storage

    def test_create_workflow_agent_basic(self):
        """Test create_workflow_agent basic functionality."""
        from unittest.mock import patch, MagicMock
        from pydantic_ai_toolsets.toolsets.meta_orchestrator.helpers import create_workflow_agent
        from pydantic_ai_toolsets.toolsets.meta_orchestrator.workflow_templates import RESEARCH_ASSISTANT
        
        cot_storage = CoTStorage()
        reflection_storage = ReflectionStorage()
        
        cot_toolset = create_cot_toolset(cot_storage, id="cot")
        reflection_toolset = create_reflection_toolset(reflection_storage, id="reflection")
        
        storages = {
            "cot": cot_storage,
            "reflection": reflection_storage,
        }
        
        orchestrator_storage = MetaOrchestratorStorage()
        
        with patch("pydantic_ai_toolsets.toolsets.meta_orchestrator.helpers.Agent") as mock_agent_class:
            mock_agent = MagicMock()
            mock_agent.model = "openai:gpt-4"
            mock_agent.toolsets = [MagicMock()]
            mock_agent_class.return_value = mock_agent
            
            agent = create_workflow_agent(
                model="openai:gpt-4",
                workflow_template=RESEARCH_ASSISTANT,
                toolsets=[cot_toolset, reflection_toolset],
                storages=storages,
                orchestrator_storage=orchestrator_storage,
            )
            
            assert agent is not None
            assert mock_agent_class.called

    def test_create_workflow_agent_with_output_type(self):
        """Test create_workflow_agent with output_type."""
        from unittest.mock import patch, MagicMock
        from pydantic import BaseModel
        from pydantic_ai_toolsets.toolsets.meta_orchestrator.helpers import create_workflow_agent
        from pydantic_ai_toolsets.toolsets.meta_orchestrator.workflow_templates import RESEARCH_ASSISTANT
        
        class TestOutput(BaseModel):
            result: str
        
        cot_storage = CoTStorage()
        cot_toolset = create_cot_toolset(cot_storage, id="cot")
        
        orchestrator_storage = MetaOrchestratorStorage()
        
        with patch("pydantic_ai_toolsets.toolsets.meta_orchestrator.helpers.Agent") as mock_agent_class:
            mock_agent = MagicMock()
            mock_agent.model = "openai:gpt-4"
            mock_agent.toolsets = [MagicMock()]
            mock_agent_class.return_value = mock_agent
            
            agent = create_workflow_agent(
                model="openai:gpt-4",
                workflow_template=RESEARCH_ASSISTANT,
                toolsets=[cot_toolset],
                orchestrator_storage=orchestrator_storage,
                output_type=TestOutput,
            )
            
            assert agent is not None
            call_kwargs = mock_agent_class.call_args[1]
            assert "output_type" in call_kwargs
            assert call_kwargs["output_type"] == TestOutput

    def test_create_workflow_agent_with_additional_prompt(self):
        """Test create_workflow_agent with additional_system_prompt."""
        from unittest.mock import patch, MagicMock
        from pydantic_ai_toolsets.toolsets.meta_orchestrator.helpers import create_workflow_agent
        from pydantic_ai_toolsets.toolsets.meta_orchestrator.workflow_templates import RESEARCH_ASSISTANT
        
        cot_storage = CoTStorage()
        cot_toolset = create_cot_toolset(cot_storage, id="cot")
        
        orchestrator_storage = MetaOrchestratorStorage()
        
        with patch("pydantic_ai_toolsets.toolsets.meta_orchestrator.helpers.Agent") as mock_agent_class:
            mock_agent = MagicMock()
            mock_agent.model = "openai:gpt-4"
            mock_agent.toolsets = [MagicMock()]
            mock_agent_class.return_value = mock_agent
            
            agent = create_workflow_agent(
                model="openai:gpt-4",
                workflow_template=RESEARCH_ASSISTANT,
                toolsets=[cot_toolset],
                orchestrator_storage=orchestrator_storage,
                additional_system_prompt="Custom instructions",
            )
            
            assert agent is not None
            call_kwargs = mock_agent_class.call_args[1]
            assert "system_prompt" in call_kwargs
            assert "Custom instructions" in call_kwargs["system_prompt"]
