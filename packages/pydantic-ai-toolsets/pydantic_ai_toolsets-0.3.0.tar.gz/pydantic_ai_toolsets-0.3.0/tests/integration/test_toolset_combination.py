"""Integration tests for toolset combination."""

from __future__ import annotations

import pytest

from pydantic_ai_toolsets import (
    create_cot_toolset,
    create_reflection_toolset,
    create_todo_toolset,
    CoTStorage,
    ReflectionStorage,
    TodoStorage,
)
from pydantic_ai_toolsets.toolsets.meta_orchestrator.helpers import create_combined_toolset
from tests.fixtures.mock_agents import MockToolset


class TestCreateCombinedToolset:
    """Test suite for create_combined_toolset function."""

    def test_combine_two_toolsets(self):
        """Test combining two toolsets."""
        cot_storage = CoTStorage()
        reflection_storage = ReflectionStorage()
        
        cot_toolset = create_cot_toolset(cot_storage, id="cot")
        reflection_toolset = create_reflection_toolset(reflection_storage, id="reflection")
        
        prefix_map = {
            "cot": "cot_",
            "reflection": "reflection_",
        }
        
        storages = {
            "cot": cot_storage,
            "reflection": reflection_storage,
        }
        
        combined_toolset, combined_prompt = create_combined_toolset(
            toolsets=[cot_toolset, reflection_toolset],
            storages=storages,
            prefix_map=prefix_map,
        )
        
        assert combined_toolset is not None
        assert isinstance(combined_prompt, str)
        assert len(combined_prompt) > 0

    def test_combine_three_toolsets(self):
        """Test combining three toolsets."""
        cot_storage = CoTStorage()
        reflection_storage = ReflectionStorage()
        todo_storage = TodoStorage()
        
        cot_toolset = create_cot_toolset(cot_storage, id="cot")
        reflection_toolset = create_reflection_toolset(reflection_storage, id="reflection")
        todo_toolset = create_todo_toolset(todo_storage, id="todo")
        
        prefix_map = {
            "cot": "cot_",
            "reflection": "reflection_",
            "todo": "todo_",
        }
        
        storages = {
            "cot": cot_storage,
            "reflection": reflection_storage,
            "todo": todo_storage,
        }
        
        combined_toolset, combined_prompt = create_combined_toolset(
            toolsets=[cot_toolset, reflection_toolset, todo_toolset],
            storages=storages,
            prefix_map=prefix_map,
        )
        
        assert combined_toolset is not None
        assert len(combined_prompt) > 0

    def test_combine_without_prefix_map(self):
        """Test combining toolsets without explicit prefix_map."""
        cot_storage = CoTStorage()
        reflection_storage = ReflectionStorage()
        
        cot_toolset = create_cot_toolset(cot_storage, id="cot")
        reflection_toolset = create_reflection_toolset(reflection_storage, id="reflection")
        
        combined_toolset, combined_prompt = create_combined_toolset(
            toolsets=[cot_toolset, reflection_toolset],
            auto_prefix=True,
        )
        
        assert combined_toolset is not None
        assert len(combined_prompt) > 0

    def test_combine_without_storages(self):
        """Test combining toolsets without storages."""
        cot_toolset = create_cot_toolset(id="cot")
        reflection_toolset = create_reflection_toolset(id="reflection")
        
        prefix_map = {
            "cot": "cot_",
            "reflection": "reflection_",
        }
        
        combined_toolset, combined_prompt = create_combined_toolset(
            toolsets=[cot_toolset, reflection_toolset],
            prefix_map=prefix_map,
        )
        
        assert combined_toolset is not None
        assert len(combined_prompt) > 0

    def test_combine_with_auto_prefix_false(self):
        """Test combining toolsets with auto_prefix=False."""
        cot_toolset = create_cot_toolset(id="cot")
        reflection_toolset = create_reflection_toolset(id="reflection")
        
        # With auto_prefix=False, toolsets are used as-is
        # This may raise UserError if there are collisions
        combined_toolset, combined_prompt = create_combined_toolset(
            toolsets=[cot_toolset, reflection_toolset],
            auto_prefix=False,
        )
        
        assert combined_toolset is not None

    def test_combine_with_orchestrator(self):
        """Test combining toolsets with orchestrator."""
        from pydantic_ai_toolsets import MetaOrchestratorStorage, create_meta_orchestrator_toolset
        
        cot_storage = CoTStorage()
        cot_toolset = create_cot_toolset(cot_storage, id="cot")
        
        orchestrator_storage = MetaOrchestratorStorage()
        orchestrator_toolset = create_meta_orchestrator_toolset(orchestrator_storage, id="orchestrator")
        
        prefix_map = {"cot": "cot_"}
        
        combined_toolset, combined_prompt = create_combined_toolset(
            toolsets=[cot_toolset],
            prefix_map=prefix_map,
            orchestrator=orchestrator_toolset,
        )
        
        assert combined_toolset is not None
        assert len(combined_prompt) > 0

    def test_combine_system_prompt_contains_all_toolsets(self):
        """Test that combined system prompt contains instructions from all toolsets."""
        cot_storage = CoTStorage()
        reflection_storage = ReflectionStorage()
        
        cot_toolset = create_cot_toolset(cot_storage, id="cot")
        reflection_toolset = create_reflection_toolset(reflection_storage, id="reflection")
        
        prefix_map = {
            "cot": "cot_",
            "reflection": "reflection_",
        }
        
        storages = {
            "cot": cot_storage,
            "reflection": reflection_storage,
        }
        
        combined_toolset, combined_prompt = create_combined_toolset(
            toolsets=[cot_toolset, reflection_toolset],
            storages=storages,
            prefix_map=prefix_map,
        )
        
        # Check that prompt contains references to both toolsets
        assert "Chain of Thought" in combined_prompt or "chain of thought" in combined_prompt.lower()
        assert "Reflection" in combined_prompt or "reflection" in combined_prompt.lower()

    def test_combine_with_workflow_template(self):
        """Test combining toolsets with workflow template."""
        from pydantic_ai_toolsets.toolsets.meta_orchestrator.types import Stage, WorkflowTemplate
        
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
        
        prefix_map = {
            "cot": "cot_",
            "reflection": "reflection_",
        }
        
        storages = {
            "cot": cot_storage,
            "reflection": reflection_storage,
        }
        
        combined_toolset, combined_prompt = create_combined_toolset(
            toolsets=[cot_toolset, reflection_toolset],
            storages=storages,
            prefix_map=prefix_map,
            workflow_template=workflow_template,
        )
        
        assert combined_toolset is not None
        assert "test_workflow" in combined_prompt.lower() or "workflow" in combined_prompt.lower()

    def test_combine_empty_toolsets_list(self):
        """Test combining empty toolsets list."""
        combined_toolset, combined_prompt = create_combined_toolset(
            toolsets=[],
        )
        
        assert combined_toolset is not None
        assert isinstance(combined_prompt, str)

    def test_combine_single_toolset(self):
        """Test combining single toolset."""
        cot_storage = CoTStorage()
        cot_toolset = create_cot_toolset(cot_storage, id="cot")
        
        prefix_map = {"cot": "cot_"}
        storages = {"cot": cot_storage}
        
        combined_toolset, combined_prompt = create_combined_toolset(
            toolsets=[cot_toolset],
            storages=storages,
            prefix_map=prefix_map,
        )
        
        assert combined_toolset is not None
        assert len(combined_prompt) > 0
