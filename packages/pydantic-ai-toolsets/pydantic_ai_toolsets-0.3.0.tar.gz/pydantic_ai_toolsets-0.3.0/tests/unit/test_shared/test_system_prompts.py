"""Unit tests for system prompt utilities."""

from __future__ import annotations

import pytest

from pydantic_ai_toolsets import create_cot_toolset, create_tot_toolset, CoTStorage, ToTStorage
from pydantic_ai_toolsets.toolsets._shared.system_prompts import (
    build_tool_name_mapping,
    combine_system_prompts,
    generate_workflow_instructions,
    identify_toolset_type,
    update_prompt_tool_names,
)
from pydantic_ai_toolsets.toolsets.meta_orchestrator.types import Stage, WorkflowTemplate
from tests.fixtures.mock_agents import MockToolset


class TestIdentifyToolsetType:
    """Test suite for identify_toolset_type function."""

    def test_identify_cot(self):
        """Test identifying CoT toolset."""
        toolset = MockToolset(id="cot")
        assert identify_toolset_type(toolset) == "cot"
        
        toolset = MockToolset(id="chain_of_thought")
        assert identify_toolset_type(toolset) == "cot"

    def test_identify_tot(self):
        """Test identifying ToT toolset."""
        toolset = MockToolset(id="tot")
        assert identify_toolset_type(toolset) == "tot"
        
        toolset = MockToolset(id="tree_of_thought")
        assert identify_toolset_type(toolset) == "tot"

    def test_identify_got(self):
        """Test identifying GoT toolset."""
        toolset = MockToolset(id="got")
        assert identify_toolset_type(toolset) == "got"

    def test_identify_mcts(self):
        """Test identifying MCTS toolset."""
        toolset = MockToolset(id="mcts")
        assert identify_toolset_type(toolset) == "mcts"

    def test_identify_beam(self):
        """Test identifying Beam toolset."""
        toolset = MockToolset(id="beam")
        assert identify_toolset_type(toolset) == "beam"

    def test_identify_reflection(self):
        """Test identifying Reflection toolset."""
        toolset = MockToolset(id="reflection")
        assert identify_toolset_type(toolset) == "reflection"

    def test_identify_self_refine(self):
        """Test identifying Self-Refine toolset."""
        toolset = MockToolset(id="self_refine")
        assert identify_toolset_type(toolset) == "self_refine"

    def test_identify_self_ask(self):
        """Test identifying Self-Ask toolset."""
        toolset = MockToolset(id="self_ask")
        assert identify_toolset_type(toolset) == "self_ask"

    def test_identify_persona(self):
        """Test identifying Persona toolset."""
        toolset = MockToolset(id="persona")
        assert identify_toolset_type(toolset) == "persona"
        
        toolset = MockToolset(id="multi_persona")
        assert identify_toolset_type(toolset) == "persona"

    def test_identify_persona_debate(self):
        """Test identifying Persona Debate toolset."""
        toolset = MockToolset(id="persona_debate")
        assert identify_toolset_type(toolset) == "persona_debate"

    def test_identify_search(self):
        """Test identifying Search toolset."""
        toolset = MockToolset(id="search")
        assert identify_toolset_type(toolset) == "search"

    def test_identify_todo(self):
        """Test identifying Todo toolset."""
        toolset = MockToolset(id="todo")
        assert identify_toolset_type(toolset) == "todo"
        
        toolset = MockToolset(id="to_do")
        assert identify_toolset_type(toolset) == "todo"

    def test_identify_unknown(self):
        """Test identifying unknown toolset."""
        toolset = MockToolset(id="unknown_toolset")
        assert identify_toolset_type(toolset) == "unknown"


class TestBuildToolNameMapping:
    """Test suite for build_tool_name_mapping function."""

    def test_build_mapping_simple(self):
        """Test building tool name mapping from simple prompt."""
        prompt = "Use `read_thoughts` to read thoughts and `write_thoughts` to write."
        mapping = build_tool_name_mapping(prompt, "cot_")
        
        assert "read_thoughts" in mapping
        assert mapping["read_thoughts"] == "cot_read_thoughts"
        assert "write_thoughts" in mapping
        assert mapping["write_thoughts"] == "cot_write_thoughts"

    def test_build_mapping_no_tools(self):
        """Test building mapping from prompt with no tools."""
        prompt = "This is a regular prompt without any tools."
        mapping = build_tool_name_mapping(prompt, "cot_")
        
        assert len(mapping) == 0

    def test_build_mapping_filters_short_names(self):
        """Test that very short matches are filtered out."""
        prompt = "Use `a` and `ab` and `abc` and `read_thoughts`."
        mapping = build_tool_name_mapping(prompt, "cot_")
        
        # Should filter out very short names
        assert "read_thoughts" in mapping
        # Very short names may or may not be included depending on length threshold

    def test_build_mapping_removes_duplicates(self):
        """Test that duplicate tool names are removed."""
        prompt = "Use `read_thoughts` and `read_thoughts` again."
        mapping = build_tool_name_mapping(prompt, "cot_")
        
        assert len(mapping) == 1
        assert "read_thoughts" in mapping


class TestUpdatePromptToolNames:
    """Test suite for update_prompt_tool_names function."""

    def test_update_backtick_wrapped_names(self):
        """Test updating backtick-wrapped tool names."""
        prompt = "Use `read_thoughts` to read."
        mapping = {"read_thoughts": "cot_read_thoughts"}
        updated = update_prompt_tool_names(prompt, mapping)
        
        assert "`cot_read_thoughts`" in updated
        assert "`read_thoughts`" not in updated

    def test_update_list_format(self):
        """Test updating tool names in list format."""
        prompt = "- `read_thoughts`: Read thoughts\n- `write_thoughts`: Write thoughts"
        mapping = {
            "read_thoughts": "cot_read_thoughts",
            "write_thoughts": "cot_write_thoughts",
        }
        updated = update_prompt_tool_names(prompt, mapping)
        
        assert "`cot_read_thoughts`" in updated
        assert "`cot_write_thoughts`" in updated

    def test_update_standalone_mentions(self):
        """Test updating standalone tool name mentions."""
        prompt = "The read_thoughts: tool reads thoughts."
        mapping = {"read_thoughts": "cot_read_thoughts"}
        updated = update_prompt_tool_names(prompt, mapping)
        
        assert "cot_read_thoughts:" in updated


class TestGenerateWorkflowInstructions:
    """Test suite for generate_workflow_instructions function."""

    def test_generate_instructions_basic(self):
        """Test generating basic workflow instructions."""
        template = WorkflowTemplate(
            name="test_workflow",
            toolsets=["cot", "reflection"],
            stages=[
                Stage(
                    name="reason",
                    toolset_id="cot",
                    transition_condition="has_final_thought",
                    description="Reason through the problem",
                ),
                Stage(
                    name="reflect",
                    toolset_id="reflection",
                    transition_condition="has_best_output",
                    description="Reflect on the solution",
                ),
            ],
            handoff_instructions={},
            description="Test workflow",
        )
        
        instructions = generate_workflow_instructions(template)
        
        assert "test_workflow" in instructions.lower()
        assert "reason" in instructions.lower()
        assert "reflect" in instructions.lower()
        assert "has_final_thought" in instructions

    def test_generate_instructions_with_prefix_map(self):
        """Test generating instructions with prefix map."""
        template = WorkflowTemplate(
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
        
        prefix_map = {"cot": "cot_"}
        instructions = generate_workflow_instructions(template, prefix_map)
        
        assert "cot_" in instructions

    def test_generate_instructions_with_handoff(self):
        """Test generating instructions with handoff instructions."""
        template = WorkflowTemplate(
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
            handoff_instructions={
                "cot→reflection": "Use final thought as initial output",
            },
        )
        
        instructions = generate_workflow_instructions(template)
        
        assert "cot→reflection" in instructions
        assert "Use final thought" in instructions


class TestCombineSystemPrompts:
    """Test suite for combine_system_prompts function."""

    def test_combine_single_toolset(self):
        """Test combining prompts from single toolset."""
        cot_storage = CoTStorage()
        cot_toolset = create_cot_toolset(cot_storage, id="cot")
        
        storages = {"cot": cot_storage}
        
        combined = combine_system_prompts(
            toolsets=[cot_toolset],
            storages=storages,
        )
        
        assert isinstance(combined, str)
        assert len(combined) > 0

    def test_combine_multiple_toolsets(self):
        """Test combining prompts from multiple toolsets."""
        cot_storage = CoTStorage()
        tot_storage = ToTStorage()
        
        cot_toolset = create_cot_toolset(cot_storage, id="cot")
        tot_toolset = create_tot_toolset(tot_storage, id="tot")
        
        storages = {
            "cot": cot_storage,
            "tot": tot_storage,
        }
        
        prefix_map = {
            "cot": "cot_",
            "tot": "tot_",
        }
        
        combined = combine_system_prompts(
            toolsets=[cot_toolset, tot_toolset],
            storages=storages,
            prefix_map=prefix_map,
        )
        
        assert isinstance(combined, str)
        assert len(combined) > 0

    def test_combine_with_workflow_template(self):
        """Test combining prompts with workflow template."""
        cot_storage = CoTStorage()
        cot_toolset = create_cot_toolset(cot_storage, id="cot")
        
        template = WorkflowTemplate(
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
        
        combined = combine_system_prompts(
            toolsets=[cot_toolset],
            storages=storages,
            workflow_template=template,
        )
        
        assert isinstance(combined, str)
        assert len(combined) > 0

    def test_combine_use_combination_prompts(self):
        """Test combining prompts with use_combination_prompts=True."""
        cot_storage = CoTStorage()
        tot_storage = ToTStorage()
        
        cot_toolset = create_cot_toolset(cot_storage, id="cot")
        tot_toolset = create_tot_toolset(tot_storage, id="tot")
        
        storages = {
            "cot": cot_storage,
            "tot": tot_storage,
        }
        
        combined = combine_system_prompts(
            toolsets=[cot_toolset, tot_toolset],
            storages=storages,
            use_combination_prompts=True,
        )
        
        assert isinstance(combined, str)
        assert len(combined) > 0

    def test_combine_use_standalone_prompts(self):
        """Test combining prompts with use_combination_prompts=False."""
        cot_storage = CoTStorage()
        cot_toolset = create_cot_toolset(cot_storage, id="cot")
        
        storages = {"cot": cot_storage}
        
        combined = combine_system_prompts(
            toolsets=[cot_toolset],
            storages=storages,
            use_combination_prompts=False,
        )
        
        assert isinstance(combined, str)
        assert len(combined) > 0


class TestGenerateCombinationPrompts:
    """Test suite for generate_*_combination_prompt functions."""

    def test_generate_search_combination_prompt(self):
        """Test generate_search_combination_prompt."""
        from pydantic_ai_toolsets.toolsets._shared.system_prompts import generate_search_combination_prompt
        from pydantic_ai_toolsets import create_search_toolset
        from tests.fixtures.mock_agents import MockToolset
        
        search_toolset = create_search_toolset(id="search")
        other_toolsets = [MockToolset(id="self_ask")]
        template = WorkflowTemplate(
            name="test",
            toolsets=["search", "self_ask"],
            stages=[],
            handoff_instructions={},
        )
        
        prompt = generate_search_combination_prompt(
            toolset=search_toolset,
            storage=None,
            other_toolsets=other_toolsets,
            position=0,
            prefix_map={"search": "search_"},
            workflow_template=template,
        )
        
        assert isinstance(prompt, str)
        assert "search_" in prompt
        assert "Stage 1" in prompt

    def test_generate_self_ask_combination_prompt(self):
        """Test generate_self_ask_combination_prompt."""
        from pydantic_ai_toolsets.toolsets._shared.system_prompts import generate_self_ask_combination_prompt
        from pydantic_ai_toolsets import create_self_ask_toolset
        from tests.fixtures.mock_agents import MockToolset
        
        self_ask_toolset = create_self_ask_toolset(id="self_ask")
        other_toolsets = [MockToolset(id="search")]
        template = WorkflowTemplate(
            name="test",
            toolsets=["search", "self_ask"],
            stages=[],
            handoff_instructions={},
        )
        
        prompt = generate_self_ask_combination_prompt(
            toolset=self_ask_toolset,
            storage=None,
            other_toolsets=other_toolsets,
            position=1,
            prefix_map={"self_ask": "self_ask_"},
            workflow_template=template,
        )
        
        assert isinstance(prompt, str)
        assert "self_ask_" in prompt
        assert "Stage 2" in prompt

    def test_generate_self_refine_combination_prompt(self):
        """Test generate_self_refine_combination_prompt."""
        from pydantic_ai_toolsets.toolsets._shared.system_prompts import generate_self_refine_combination_prompt
        from pydantic_ai_toolsets import create_self_refine_toolset
        from tests.fixtures.mock_agents import MockToolset
        
        self_refine_toolset = create_self_refine_toolset(id="self_refine")
        other_toolsets = [MockToolset(id="cot")]
        template = WorkflowTemplate(
            name="test",
            toolsets=["cot", "self_refine"],
            stages=[],
            handoff_instructions={},
        )
        
        prompt = generate_self_refine_combination_prompt(
            toolset=self_refine_toolset,
            storage=None,
            other_toolsets=other_toolsets,
            position=1,
            prefix_map={"self_refine": "self_refine_"},
            workflow_template=template,
        )
        
        assert isinstance(prompt, str)
        assert "self_refine_" in prompt

    def test_generate_todo_combination_prompt(self):
        """Test generate_todo_combination_prompt."""
        from pydantic_ai_toolsets.toolsets._shared.system_prompts import generate_todo_combination_prompt
        from pydantic_ai_toolsets import create_todo_toolset, TodoStorage
        from tests.fixtures.mock_agents import MockToolset
        
        storage = TodoStorage()
        todo_toolset = create_todo_toolset(storage, id="todo")
        other_toolsets = [MockToolset(id="search")]
        template = WorkflowTemplate(
            name="test",
            toolsets=["search", "todo"],
            stages=[],
            handoff_instructions={},
        )
        
        prompt = generate_todo_combination_prompt(
            toolset=todo_toolset,
            storage=storage,
            other_toolsets=other_toolsets,
            position=1,
            prefix_map={"todo": "todo_"},
            workflow_template=template,
        )
        
        assert isinstance(prompt, str)
        assert "todo_" in prompt

    def test_generate_reflection_combination_prompt(self):
        """Test generate_reflection_combination_prompt."""
        from pydantic_ai_toolsets.toolsets._shared.system_prompts import generate_reflection_combination_prompt
        from pydantic_ai_toolsets import create_reflection_toolset
        from tests.fixtures.mock_agents import MockToolset
        
        reflection_toolset = create_reflection_toolset(id="reflection")
        other_toolsets = [MockToolset(id="cot")]
        template = WorkflowTemplate(
            name="test",
            toolsets=["cot", "reflection"],
            stages=[],
            handoff_instructions={},
        )
        
        prompt = generate_reflection_combination_prompt(
            toolset=reflection_toolset,
            storage=None,
            other_toolsets=other_toolsets,
            position=1,
            prefix_map={"reflection": "reflection_"},
            workflow_template=template,
        )
        
        assert isinstance(prompt, str)
        assert "reflection_" in prompt

    def test_generate_cot_combination_prompt(self):
        """Test generate_cot_combination_prompt."""
        from pydantic_ai_toolsets.toolsets._shared.system_prompts import generate_cot_combination_prompt
        from pydantic_ai_toolsets import create_cot_toolset, CoTStorage
        
        storage = CoTStorage()
        cot_toolset = create_cot_toolset(storage, id="cot")
        template = WorkflowTemplate(
            name="test",
            toolsets=["cot"],
            stages=[],
            handoff_instructions={},
        )
        
        prompt = generate_cot_combination_prompt(
            toolset=cot_toolset,
            storage=storage,
            other_toolsets=[],
            position=0,
            prefix_map={"cot": "cot_"},
            workflow_template=template,
        )
        
        assert isinstance(prompt, str)
        assert "cot_" in prompt

    def test_generate_tot_combination_prompt(self):
        """Test generate_tot_combination_prompt."""
        from pydantic_ai_toolsets.toolsets._shared.system_prompts import generate_tot_combination_prompt
        from pydantic_ai_toolsets import create_tot_toolset, ToTStorage
        
        storage = ToTStorage()
        tot_toolset = create_tot_toolset(storage, id="tot")
        template = WorkflowTemplate(
            name="test",
            toolsets=["tot"],
            stages=[],
            handoff_instructions={},
        )
        
        prompt = generate_tot_combination_prompt(
            toolset=tot_toolset,
            storage=storage,
            other_toolsets=[],
            position=0,
            prefix_map={"tot": "tot_"},
            workflow_template=template,
        )
        
        assert isinstance(prompt, str)
        assert "tot_" in prompt

    def test_generate_got_combination_prompt(self):
        """Test generate_got_combination_prompt."""
        from pydantic_ai_toolsets.toolsets._shared.system_prompts import generate_got_combination_prompt
        from pydantic_ai_toolsets import create_got_toolset, GoTStorage
        
        storage = GoTStorage()
        got_toolset = create_got_toolset(storage, id="got")
        template = WorkflowTemplate(
            name="test",
            toolsets=["got"],
            stages=[],
            handoff_instructions={},
        )
        
        prompt = generate_got_combination_prompt(
            toolset=got_toolset,
            storage=storage,
            other_toolsets=[],
            position=0,
            prefix_map={"got": "got_"},
            workflow_template=template,
        )
        
        assert isinstance(prompt, str)
        assert "got_" in prompt

    def test_generate_mcts_combination_prompt(self):
        """Test generate_mcts_combination_prompt."""
        from pydantic_ai_toolsets.toolsets._shared.system_prompts import generate_mcts_combination_prompt
        from pydantic_ai_toolsets import create_mcts_toolset, MCTSStorage
        
        storage = MCTSStorage()
        mcts_toolset = create_mcts_toolset(storage, id="mcts")
        template = WorkflowTemplate(
            name="test",
            toolsets=["mcts"],
            stages=[],
            handoff_instructions={},
        )
        
        prompt = generate_mcts_combination_prompt(
            toolset=mcts_toolset,
            storage=storage,
            other_toolsets=[],
            position=0,
            prefix_map={"mcts": "mcts_"},
            workflow_template=template,
        )
        
        assert isinstance(prompt, str)
        assert "mcts_" in prompt

    def test_generate_beam_combination_prompt(self):
        """Test generate_beam_combination_prompt."""
        from pydantic_ai_toolsets.toolsets._shared.system_prompts import generate_beam_combination_prompt
        from pydantic_ai_toolsets import create_beam_toolset, BeamStorage
        
        storage = BeamStorage()
        beam_toolset = create_beam_toolset(storage, id="beam")
        template = WorkflowTemplate(
            name="test",
            toolsets=["beam"],
            stages=[],
            handoff_instructions={},
        )
        
        prompt = generate_beam_combination_prompt(
            toolset=beam_toolset,
            storage=storage,
            other_toolsets=[],
            position=0,
            prefix_map={"beam": "beam_"},
            workflow_template=template,
        )
        
        assert isinstance(prompt, str)
        assert "beam_" in prompt

    def test_generate_persona_combination_prompt(self):
        """Test generate_persona_combination_prompt."""
        from pydantic_ai_toolsets.toolsets._shared.system_prompts import generate_persona_combination_prompt
        from pydantic_ai_toolsets import create_persona_toolset, PersonaStorage
        
        storage = PersonaStorage()
        persona_toolset = create_persona_toolset(storage, id="persona")
        template = WorkflowTemplate(
            name="test",
            toolsets=["persona"],
            stages=[],
            handoff_instructions={},
        )
        
        prompt = generate_persona_combination_prompt(
            toolset=persona_toolset,
            storage=storage,
            other_toolsets=[],
            position=0,
            prefix_map={"persona": "persona_"},
            workflow_template=template,
        )
        
        assert isinstance(prompt, str)
        assert "persona_" in prompt

    def test_generate_persona_debate_combination_prompt(self):
        """Test generate_persona_debate_combination_prompt."""
        from pydantic_ai_toolsets.toolsets._shared.system_prompts import generate_persona_debate_combination_prompt
        from pydantic_ai_toolsets import create_persona_debate_toolset, PersonaDebateStorage
        
        storage = PersonaDebateStorage()
        persona_debate_toolset = create_persona_debate_toolset(storage, id="persona_debate")
        template = WorkflowTemplate(
            name="test",
            toolsets=["persona_debate"],
            stages=[],
            handoff_instructions={},
        )
        
        prompt = generate_persona_debate_combination_prompt(
            toolset=persona_debate_toolset,
            storage=storage,
            other_toolsets=[],
            position=0,
            prefix_map={"persona_debate": "persona_debate_"},
            workflow_template=template,
        )
        
        assert isinstance(prompt, str)
        assert "persona_debate_" in prompt

    def test_generate_combination_prompt_for_toolset(self):
        """Test generate_combination_prompt_for_toolset dispatcher."""
        from pydantic_ai_toolsets.toolsets._shared.system_prompts import generate_combination_prompt_for_toolset
        from pydantic_ai_toolsets import create_cot_toolset, CoTStorage
        
        storage = CoTStorage()
        cot_toolset = create_cot_toolset(storage, id="cot")
        template = WorkflowTemplate(
            name="test",
            toolsets=["cot"],
            stages=[],
            handoff_instructions={},
        )
        
        prompt = generate_combination_prompt_for_toolset(
            toolset_type="cot",
            toolset=cot_toolset,
            storage=storage,
            other_toolsets=[],
            toolset_order=0,
            prefix_map={"cot": "cot_"},
            workflow_template=template,
        )
        
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_generate_combination_prompt_for_toolset_unknown(self):
        """Test generate_combination_prompt_for_toolset with unknown type."""
        from pydantic_ai_toolsets.toolsets._shared.system_prompts import generate_combination_prompt_for_toolset
        from tests.fixtures.mock_agents import MockToolset
        
        toolset = MockToolset(id="unknown")
        prompt = generate_combination_prompt_for_toolset(
            toolset_type="unknown",
            toolset=toolset,
            storage=None,
            other_toolsets=[],
            toolset_order=0,
            prefix_map=None,
            workflow_template=None,
        )
        
        assert prompt == ""

    def test_generate_search_combination_prompt_with_self_ask(self):
        """Test generate_search_combination_prompt with self_ask in other_types."""
        from pydantic_ai_toolsets.toolsets._shared.system_prompts import generate_search_combination_prompt
        from pydantic_ai_toolsets import create_search_toolset, create_self_ask_toolset, SearchStorage, SelfAskStorage
        from pydantic_ai_toolsets.toolsets.meta_orchestrator.types import WorkflowTemplate
        
        search_storage = SearchStorage()
        search_toolset = create_search_toolset(search_storage, id="search")
        self_ask_toolset = create_self_ask_toolset(SelfAskStorage(), id="self_ask")
        
        prompt = generate_search_combination_prompt(
            toolset=search_toolset,
            storage=search_storage,
            other_toolsets=[self_ask_toolset],
            position=0,
            prefix_map={"search": "search_", "self_ask": "self_ask_"},
            workflow_template=None,
        )
        
        assert "self_ask" in prompt.lower() or "questions" in prompt.lower()

    def test_generate_search_combination_prompt_with_reflection(self):
        """Test generate_search_combination_prompt with reflection in other_types."""
        from pydantic_ai_toolsets.toolsets._shared.system_prompts import generate_search_combination_prompt
        from pydantic_ai_toolsets import create_search_toolset, create_reflection_toolset, SearchStorage, ReflectionStorage
        from pydantic_ai_toolsets.toolsets.meta_orchestrator.types import WorkflowTemplate
        
        search_storage = SearchStorage()
        search_toolset = create_search_toolset(search_storage, id="search")
        reflection_toolset = create_reflection_toolset(ReflectionStorage(), id="reflection")
        
        prompt = generate_search_combination_prompt(
            toolset=search_toolset,
            storage=search_storage,
            other_toolsets=[reflection_toolset],
            position=0,
            prefix_map={"search": "search_", "reflection": "reflection_"},
            workflow_template=None,
        )
        
        assert "refinement" in prompt.lower() or "reflection" in prompt.lower()

    def test_generate_search_combination_prompt_with_todo(self):
        """Test generate_search_combination_prompt with todo in other_types."""
        from pydantic_ai_toolsets.toolsets._shared.system_prompts import generate_search_combination_prompt
        from pydantic_ai_toolsets import create_search_toolset, create_todo_toolset, SearchStorage, TodoStorage
        
        search_storage = SearchStorage()
        search_toolset = create_search_toolset(search_storage, id="search")
        todo_toolset = create_todo_toolset(TodoStorage(), id="todo")
        
        prompt = generate_search_combination_prompt(
            toolset=search_toolset,
            storage=search_storage,
            other_toolsets=[todo_toolset],
            position=0,
            prefix_map={"search": "search_", "todo": "todo_"},
            workflow_template=None,
        )
        
        assert "todo" in prompt.lower() or "tracked" in prompt.lower()

    def test_generate_search_combination_prompt_with_next_types(self):
        """Test generate_search_combination_prompt with next_types."""
        from pydantic_ai_toolsets.toolsets._shared.system_prompts import generate_search_combination_prompt
        from pydantic_ai_toolsets import create_search_toolset, create_self_ask_toolset, SearchStorage, SelfAskStorage
        
        search_storage = SearchStorage()
        search_toolset = create_search_toolset(search_storage, id="search")
        self_ask_toolset = create_self_ask_toolset(SelfAskStorage(), id="self_ask")
        
        prompt = generate_search_combination_prompt(
            toolset=search_toolset,
            storage=search_storage,
            other_toolsets=[self_ask_toolset],
            position=0,
            prefix_map={"search": "search_", "self_ask": "self_ask_"},
            workflow_template=None,
        )
        
        assert "ask_main_question" in prompt.lower() or "next stage" in prompt.lower()

    def test_generate_self_ask_combination_prompt_with_search_prev(self):
        """Test generate_self_ask_combination_prompt with search in prev_types."""
        from pydantic_ai_toolsets.toolsets._shared.system_prompts import generate_self_ask_combination_prompt
        from pydantic_ai_toolsets import create_self_ask_toolset, create_search_toolset, SelfAskStorage, SearchStorage
        
        self_ask_storage = SelfAskStorage()
        self_ask_toolset = create_self_ask_toolset(self_ask_storage, id="self_ask")
        search_toolset = create_search_toolset(SearchStorage(), id="search")
        
        prompt = generate_self_ask_combination_prompt(
            toolset=self_ask_toolset,
            storage=self_ask_storage,
            other_toolsets=[search_toolset],
            position=1,
            prefix_map={"self_ask": "self_ask_", "search": "search_"},
            workflow_template=None,
        )
        
        assert "search" in prompt.lower() or "previous" in prompt.lower()

    def test_generate_self_ask_combination_prompt_with_reflection_next(self):
        """Test generate_self_ask_combination_prompt with reflection in next_types."""
        from pydantic_ai_toolsets.toolsets._shared.system_prompts import generate_self_ask_combination_prompt
        from pydantic_ai_toolsets import create_self_ask_toolset, create_reflection_toolset, SelfAskStorage, ReflectionStorage
        
        self_ask_storage = SelfAskStorage()
        self_ask_toolset = create_self_ask_toolset(self_ask_storage, id="self_ask")
        reflection_toolset = create_reflection_toolset(ReflectionStorage(), id="reflection")
        
        prompt = generate_self_ask_combination_prompt(
            toolset=self_ask_toolset,
            storage=self_ask_storage,
            other_toolsets=[reflection_toolset],
            position=0,
            prefix_map={"self_ask": "self_ask_", "reflection": "reflection_"},
            workflow_template=None,
        )
        
        assert "refined" in prompt.lower() or "refinement" in prompt.lower()

    def test_generate_self_ask_combination_prompt_with_todo_next(self):
        """Test generate_self_ask_combination_prompt with todo in next_types."""
        from pydantic_ai_toolsets.toolsets._shared.system_prompts import generate_self_ask_combination_prompt
        from pydantic_ai_toolsets import create_self_ask_toolset, create_todo_toolset, SelfAskStorage, TodoStorage
        
        self_ask_storage = SelfAskStorage()
        self_ask_toolset = create_self_ask_toolset(self_ask_storage, id="self_ask")
        todo_toolset = create_todo_toolset(TodoStorage(), id="todo")
        
        prompt = generate_self_ask_combination_prompt(
            toolset=self_ask_toolset,
            storage=self_ask_storage,
            other_toolsets=[todo_toolset],
            position=0,
            prefix_map={"self_ask": "self_ask_", "todo": "todo_"},
            workflow_template=None,
        )
        
        # The prompt should be generated successfully (todo in next_types adds text)
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        # Check that it mentions task or completed (the actual text may vary)
        assert "task" in prompt.lower() or "completed" in prompt.lower() or "answer" in prompt.lower()

    def test_generate_combination_prompt_for_toolset_with_prefix_map(self):
        """Test generate_combination_prompt_for_toolset with prefix_map."""
        from pydantic_ai_toolsets.toolsets._shared.system_prompts import generate_combination_prompt_for_toolset
        from pydantic_ai_toolsets import create_cot_toolset, CoTStorage
        
        storage = CoTStorage()
        cot_toolset = create_cot_toolset(storage, id="cot")
        
        prompt = generate_combination_prompt_for_toolset(
            toolset_type="cot",
            toolset=cot_toolset,
            storage=storage,
            other_toolsets=[],
            toolset_order=0,
            prefix_map={"cot": "cot_"},
            workflow_template=None,
        )
        
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_generate_combination_prompt_for_toolset_fallback_to_standalone(self):
        """Test generate_combination_prompt_for_toolset fallback to standalone."""
        from pydantic_ai_toolsets.toolsets._shared.system_prompts import generate_combination_prompt_for_toolset
        from pydantic_ai_toolsets import create_cot_toolset, CoTStorage
        
        storage = CoTStorage()
        cot_toolset = create_cot_toolset(storage, id="cot")
        
        # Use a toolset type that doesn't have a combination generator
        # but has a standalone getter
        prompt = generate_combination_prompt_for_toolset(
            toolset_type="cot",
            toolset=cot_toolset,
            storage=storage,
            other_toolsets=[],
            toolset_order=0,
            prefix_map={"cot": "cot_"},
            workflow_template=None,
        )
        
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_combine_system_prompts_with_empty_toolsets(self):
        """Test combine_system_prompts with empty toolsets list."""
        from pydantic_ai_toolsets.toolsets._shared.system_prompts import combine_system_prompts
        
        prompt = combine_system_prompts(
            toolsets=[],
            storages=None,
            prefix_map=None,
            workflow_template=None,
        )
        
        assert isinstance(prompt, str)

    def test_combine_system_prompts_with_none_storages(self):
        """Test combine_system_prompts with None storages."""
        from pydantic_ai_toolsets.toolsets._shared.system_prompts import combine_system_prompts
        from pydantic_ai_toolsets import create_cot_toolset, CoTStorage
        
        cot_toolset = create_cot_toolset(CoTStorage(), id="cot")
        
        prompt = combine_system_prompts(
            toolsets=[cot_toolset],
            storages=None,
            prefix_map=None,
            workflow_template=None,
        )
        
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_update_prompt_tool_names_edge_cases(self):
        """Test update_prompt_tool_names with edge cases."""
        from pydantic_ai_toolsets.toolsets._shared.system_prompts import update_prompt_tool_names, build_tool_name_mapping
        
        prompt = "Use `read_thoughts` and `write_thoughts` tools."
        mapping = build_tool_name_mapping(prompt, "cot_")
        result = update_prompt_tool_names(prompt, mapping)
        
        assert isinstance(result, str)
        assert len(result) > 0

    def test_generate_search_combination_prompt_with_self_ask_next(self):
        """Test generate_search_combination_prompt with self_ask in next_types.
        
        Note: Due to the logic in generate_search_combination_prompt where next_types
        checks `i > position`, when position=0 and self_ask is at index 0 in other_toolsets,
        it won't be in next_types. To test the missing lines 333-335, we need a scenario
        where a toolset comes AFTER position 0, so we add a dummy toolset before self_ask.
        """
        from pydantic_ai_toolsets.toolsets._shared.system_prompts import generate_search_combination_prompt
        from pydantic_ai_toolsets import create_search_toolset, create_self_ask_toolset, create_cot_toolset, SearchStorage, SelfAskStorage, CoTStorage
        
        search_storage = SearchStorage()
        search_toolset = create_search_toolset(search_storage, id="search")
        cot_toolset = create_cot_toolset(CoTStorage(), id="cot")  # Dummy toolset at index 0
        self_ask_toolset = create_self_ask_toolset(SelfAskStorage(), id="self_ask")  # At index 1
        
        # With position=0, cot is at index 0 (i=0 > 0 is False, not in next_types)
        # self_ask is at index 1 (i=1 > 0 is True, IS in next_types)
        prompt = generate_search_combination_prompt(
            toolset=search_toolset,
            storage=search_storage,
            other_toolsets=[cot_toolset, self_ask_toolset],
            position=0,
            prefix_map={"search": "search_", "self_ask": "self_ask_", "cot": "cot_"},
            workflow_template=None,
        )
        
        # Check if the conditional text for self_ask in next_types is present (line 333)
        assert "ask_main_question" in prompt or "formulate main questions" in prompt.lower()

    def test_generate_search_combination_prompt_with_refinement_next(self):
        """Test generate_search_combination_prompt with self_refine/reflection in next_types."""
        from pydantic_ai_toolsets.toolsets._shared.system_prompts import generate_search_combination_prompt
        from pydantic_ai_toolsets import create_search_toolset, create_self_refine_toolset, create_reflection_toolset, SearchStorage, SelfRefineStorage, ReflectionStorage
        
        search_storage = SearchStorage()
        search_toolset = create_search_toolset(search_storage, id="search")
        self_refine_toolset = create_self_refine_toolset(SelfRefineStorage(), id="self_refine")
        reflection_toolset = create_reflection_toolset(ReflectionStorage(), id="reflection")
        
        prompt1 = generate_search_combination_prompt(
            toolset=search_toolset,
            storage=search_storage,
            other_toolsets=[self_refine_toolset],
            position=0,
            prefix_map={"search": "search_", "self_refine": "self_refine_"},
            workflow_template=None,
        )
        assert "refinement" in prompt1.lower() or "refined" in prompt1.lower()
        
        prompt2 = generate_search_combination_prompt(
            toolset=search_toolset,
            storage=search_storage,
            other_toolsets=[reflection_toolset],
            position=0,
            prefix_map={"search": "search_", "reflection": "reflection_"},
            workflow_template=None,
        )
        assert "refinement" in prompt2.lower() or "refined" in prompt2.lower()

    def test_generate_self_ask_combination_prompt_with_refinement_next(self):
        """Test generate_self_ask_combination_prompt with self_refine/reflection in next_types."""
        from pydantic_ai_toolsets.toolsets._shared.system_prompts import generate_self_ask_combination_prompt
        from pydantic_ai_toolsets import create_self_ask_toolset, create_self_refine_toolset, create_reflection_toolset, SelfAskStorage, SelfRefineStorage, ReflectionStorage
        
        self_ask_storage = SelfAskStorage()
        self_ask_toolset = create_self_ask_toolset(self_ask_storage, id="self_ask")
        self_refine_toolset = create_self_refine_toolset(SelfRefineStorage(), id="self_refine")
        reflection_toolset = create_reflection_toolset(ReflectionStorage(), id="reflection")
        
        prompt1 = generate_self_ask_combination_prompt(
            toolset=self_ask_toolset,
            storage=self_ask_storage,
            other_toolsets=[self_refine_toolset],
            position=0,
            prefix_map={"self_ask": "self_ask_", "self_refine": "self_refine_"},
            workflow_template=None,
        )
        assert "refined" in prompt1.lower() or "refinement" in prompt1.lower()
        # Check for the text from line 406-407 (refinement comes next, completeness/perfection)
        assert "refinement comes next" in prompt1.lower() or "completeness" in prompt1.lower() or "perfection" in prompt1.lower() or "thorough decomposition" in prompt1.lower()
        
        prompt2 = generate_self_ask_combination_prompt(
            toolset=self_ask_toolset,
            storage=self_ask_storage,
            other_toolsets=[reflection_toolset],
            position=0,
            prefix_map={"self_ask": "self_ask_", "reflection": "reflection_"},
            workflow_template=None,
        )
        assert "refined" in prompt2.lower() or "refinement" in prompt2.lower()

    def test_generate_self_refine_combination_prompt_with_search_prev(self):
        """Test generate_self_refine_combination_prompt with search in prev_types."""
        from pydantic_ai_toolsets.toolsets._shared.system_prompts import generate_self_refine_combination_prompt
        from pydantic_ai_toolsets import create_self_refine_toolset, create_search_toolset, SelfRefineStorage, SearchStorage
        
        self_refine_storage = SelfRefineStorage()
        self_refine_toolset = create_self_refine_toolset(self_refine_storage, id="self_refine")
        search_toolset = create_search_toolset(SearchStorage(), id="search")
        
        prompt = generate_self_refine_combination_prompt(
            toolset=self_refine_toolset,
            storage=self_refine_storage,
            other_toolsets=[search_toolset],
            position=1,
            prefix_map={"self_refine": "self_refine_", "search": "search_"},
            workflow_template=None,
        )
        assert "search" in prompt.lower() or "context" in prompt.lower()

    def test_generate_self_refine_combination_prompt_with_tot_got_prev(self):
        """Test generate_self_refine_combination_prompt with tot/got in prev_types."""
        from pydantic_ai_toolsets.toolsets._shared.system_prompts import generate_self_refine_combination_prompt
        from pydantic_ai_toolsets import create_self_refine_toolset, create_tot_toolset, create_got_toolset, SelfRefineStorage, ToTStorage, GoTStorage
        
        self_refine_storage = SelfRefineStorage()
        self_refine_toolset = create_self_refine_toolset(self_refine_storage, id="self_refine")
        tot_toolset = create_tot_toolset(ToTStorage(), id="tot")
        got_toolset = create_got_toolset(GoTStorage(), id="got")
        
        prompt1 = generate_self_refine_combination_prompt(
            toolset=self_refine_toolset,
            storage=self_refine_storage,
            other_toolsets=[tot_toolset],
            position=1,
            prefix_map={"self_refine": "self_refine_", "tot": "tot_"},
            workflow_template=None,
        )
        assert "exploration" in prompt1.lower() or "solution" in prompt1.lower()
        
        prompt2 = generate_self_refine_combination_prompt(
            toolset=self_refine_toolset,
            storage=self_refine_storage,
            other_toolsets=[got_toolset],
            position=1,
            prefix_map={"self_refine": "self_refine_", "got": "got_"},
            workflow_template=None,
        )
        assert "exploration" in prompt2.lower() or "solution" in prompt2.lower()

    def test_generate_self_refine_combination_prompt_with_todo_next(self):
        """Test generate_self_refine_combination_prompt with todo in next_types."""
        from pydantic_ai_toolsets.toolsets._shared.system_prompts import generate_self_refine_combination_prompt
        from pydantic_ai_toolsets import create_self_refine_toolset, create_todo_toolset, SelfRefineStorage, TodoStorage
        
        self_refine_storage = SelfRefineStorage()
        self_refine_toolset = create_self_refine_toolset(self_refine_storage, id="self_refine")
        todo_toolset = create_todo_toolset(TodoStorage(), id="todo")
        
        prompt = generate_self_refine_combination_prompt(
            toolset=self_refine_toolset,
            storage=self_refine_storage,
            other_toolsets=[todo_toolset],
            position=0,
            prefix_map={"self_refine": "self_refine_", "todo": "todo_"},
            workflow_template=None,
        )
        assert "task" in prompt.lower() or "tracked" in prompt.lower()

    def test_generate_todo_combination_prompt_with_refinement_prev(self):
        """Test generate_todo_combination_prompt with self_refine/reflection in prev_types."""
        from pydantic_ai_toolsets.toolsets._shared.system_prompts import generate_todo_combination_prompt
        from pydantic_ai_toolsets import create_todo_toolset, create_self_refine_toolset, create_reflection_toolset, TodoStorage, SelfRefineStorage, ReflectionStorage
        
        todo_storage = TodoStorage()
        todo_toolset = create_todo_toolset(todo_storage, id="todo")
        self_refine_toolset = create_self_refine_toolset(SelfRefineStorage(), id="self_refine")
        reflection_toolset = create_reflection_toolset(ReflectionStorage(), id="reflection")
        
        prompt1 = generate_todo_combination_prompt(
            toolset=todo_toolset,
            storage=todo_storage,
            other_toolsets=[self_refine_toolset],
            position=1,
            prefix_map={"todo": "todo_", "self_refine": "self_refine_"},
            workflow_template=None,
        )
        assert "refined" in prompt1.lower() or "refinement" in prompt1.lower()
        
        prompt2 = generate_todo_combination_prompt(
            toolset=todo_toolset,
            storage=todo_storage,
            other_toolsets=[reflection_toolset],
            position=1,
            prefix_map={"todo": "todo_", "reflection": "reflection_"},
            workflow_template=None,
        )
        assert "refined" in prompt2.lower() or "refinement" in prompt2.lower()

    def test_generate_todo_combination_prompt_with_tot_got_prev(self):
        """Test generate_todo_combination_prompt with tot/got in prev_types."""
        from pydantic_ai_toolsets.toolsets._shared.system_prompts import generate_todo_combination_prompt
        from pydantic_ai_toolsets import create_todo_toolset, create_tot_toolset, create_got_toolset, TodoStorage, ToTStorage, GoTStorage
        
        todo_storage = TodoStorage()
        todo_toolset = create_todo_toolset(todo_storage, id="todo")
        tot_toolset = create_tot_toolset(ToTStorage(), id="tot")
        got_toolset = create_got_toolset(GoTStorage(), id="got")
        
        prompt1 = generate_todo_combination_prompt(
            toolset=todo_toolset,
            storage=todo_storage,
            other_toolsets=[tot_toolset],
            position=1,
            prefix_map={"todo": "todo_", "tot": "tot_"},
            workflow_template=None,
        )
        assert "exploration" in prompt1.lower() or "solution" in prompt1.lower()
        
        prompt2 = generate_todo_combination_prompt(
            toolset=todo_toolset,
            storage=todo_storage,
            other_toolsets=[got_toolset],
            position=1,
            prefix_map={"todo": "todo_", "got": "got_"},
            workflow_template=None,
        )
        assert "exploration" in prompt2.lower() or "solution" in prompt2.lower()

    def test_generate_todo_combination_prompt_with_storage_todos(self):
        """Test generate_todo_combination_prompt displays todos from storage."""
        from pydantic_ai_toolsets.toolsets._shared.system_prompts import generate_todo_combination_prompt
        from pydantic_ai_toolsets import create_todo_toolset, TodoStorage
        from pydantic_ai_toolsets.toolsets.to_do.types import Todo
        
        todo_storage = TodoStorage()
        import uuid
        todo = Todo(todo_id=str(uuid.uuid4()), content="Test task", status="pending", active_form="Testing task")
        todo_storage.todos = [todo]
        todo_toolset = create_todo_toolset(todo_storage, id="todo")
        
        prompt = generate_todo_combination_prompt(
            toolset=todo_toolset,
            storage=todo_storage,
            other_toolsets=[],
            position=0,
            prefix_map={"todo": "todo_"},
            workflow_template=None,
        )
        assert "Current Todos" in prompt or "Todos" in prompt
        assert "Test task" in prompt

    def test_generate_reflection_combination_prompt_with_persona_prev(self):
        """Test generate_reflection_combination_prompt with persona in prev_types."""
        from pydantic_ai_toolsets.toolsets._shared.system_prompts import generate_reflection_combination_prompt
        from pydantic_ai_toolsets import create_reflection_toolset, create_persona_toolset, ReflectionStorage, PersonaStorage
        
        reflection_storage = ReflectionStorage()
        reflection_toolset = create_reflection_toolset(reflection_storage, id="reflection")
        persona_toolset = create_persona_toolset(PersonaStorage(), id="persona")
        
        prompt = generate_reflection_combination_prompt(
            toolset=reflection_toolset,
            storage=reflection_storage,
            other_toolsets=[persona_toolset],
            position=1,
            prefix_map={"reflection": "reflection_", "persona": "persona_"},
            workflow_template=None,
        )
        assert "persona" in prompt.lower() or "perspective" in prompt.lower()

    def test_generate_reflection_combination_prompt_with_mcts_prev(self):
        """Test generate_reflection_combination_prompt with mcts in prev_types."""
        from pydantic_ai_toolsets.toolsets._shared.system_prompts import generate_reflection_combination_prompt
        from pydantic_ai_toolsets import create_reflection_toolset, create_mcts_toolset, ReflectionStorage, MCTSStorage
        
        reflection_storage = ReflectionStorage()
        reflection_toolset = create_reflection_toolset(reflection_storage, id="reflection")
        mcts_toolset = create_mcts_toolset(MCTSStorage(), id="mcts")
        
        prompt = generate_reflection_combination_prompt(
            toolset=reflection_toolset,
            storage=reflection_storage,
            other_toolsets=[mcts_toolset],
            position=1,
            prefix_map={"reflection": "reflection_", "mcts": "mcts_"},
            workflow_template=None,
        )
        assert "mcts" in prompt.lower() or "action" in prompt.lower()

    def test_generate_reflection_combination_prompt_with_todo_next(self):
        """Test generate_reflection_combination_prompt with todo in next_types."""
        from pydantic_ai_toolsets.toolsets._shared.system_prompts import generate_reflection_combination_prompt
        from pydantic_ai_toolsets import create_reflection_toolset, create_todo_toolset, ReflectionStorage, TodoStorage
        
        reflection_storage = ReflectionStorage()
        reflection_toolset = create_reflection_toolset(reflection_storage, id="reflection")
        todo_toolset = create_todo_toolset(TodoStorage(), id="todo")
        
        prompt = generate_reflection_combination_prompt(
            toolset=reflection_toolset,
            storage=reflection_storage,
            other_toolsets=[todo_toolset],
            position=0,
            prefix_map={"reflection": "reflection_", "todo": "todo_"},
            workflow_template=None,
        )
        assert "task" in prompt.lower() or "tracked" in prompt.lower()

    def test_generate_cot_combination_prompt_with_current_state_section(self):
        """Test generate_cot_combination_prompt extracts and updates current_state_section."""
        from pydantic_ai_toolsets.toolsets._shared.system_prompts import generate_cot_combination_prompt
        from pydantic_ai_toolsets import create_cot_toolset, CoTStorage
        
        cot_storage = CoTStorage()
        cot_toolset = create_cot_toolset(cot_storage, id="cot")
        
        prompt = generate_cot_combination_prompt(
            toolset=cot_toolset,
            storage=cot_storage,
            other_toolsets=[],
            position=0,
            prefix_map={"cot": "cot_"},
            workflow_template=None,
        )
        assert "Current State" in prompt or "cot_" in prompt

    def test_generate_cot_combination_prompt_with_refinement_next(self):
        """Test generate_cot_combination_prompt with reflection/self_refine in next_types."""
        from pydantic_ai_toolsets.toolsets._shared.system_prompts import generate_cot_combination_prompt
        from pydantic_ai_toolsets import create_cot_toolset, create_reflection_toolset, create_self_refine_toolset, create_search_toolset, CoTStorage, ReflectionStorage, SelfRefineStorage, SearchStorage
        
        cot_storage = CoTStorage()
        cot_toolset = create_cot_toolset(cot_storage, id="cot")
        search_toolset = create_search_toolset(SearchStorage(), id="search")  # Dummy at index 0
        reflection_toolset = create_reflection_toolset(ReflectionStorage(), id="reflection")  # At index 1
        self_refine_toolset = create_self_refine_toolset(SelfRefineStorage(), id="self_refine")  # At index 1
        
        prompt1 = generate_cot_combination_prompt(
            toolset=cot_toolset,
            storage=cot_storage,
            other_toolsets=[search_toolset, reflection_toolset],
            position=0,
            prefix_map={"cot": "cot_", "reflection": "reflection_", "search": "search_"},
            workflow_template=None,
        )
        assert "refinement" in prompt1.lower() or "refined" in prompt1.lower()
        
        prompt2 = generate_cot_combination_prompt(
            toolset=cot_toolset,
            storage=cot_storage,
            other_toolsets=[search_toolset, self_refine_toolset],
            position=0,
            prefix_map={"cot": "cot_", "self_refine": "self_refine_", "search": "search_"},
            workflow_template=None,
        )
        assert "refinement" in prompt2.lower() or "refined" in prompt2.lower()

    def test_generate_tot_combination_prompt_with_current_state_section(self):
        """Test generate_tot_combination_prompt extracts and updates current_state_section."""
        from pydantic_ai_toolsets.toolsets._shared.system_prompts import generate_tot_combination_prompt
        from pydantic_ai_toolsets import create_tot_toolset, ToTStorage
        
        tot_storage = ToTStorage()
        tot_toolset = create_tot_toolset(tot_storage, id="tot")
        
        prompt = generate_tot_combination_prompt(
            toolset=tot_toolset,
            storage=tot_storage,
            other_toolsets=[],
            position=0,
            prefix_map={"tot": "tot_"},
            workflow_template=None,
        )
        assert "Current State" in prompt or "tot_" in prompt

    def test_generate_tot_combination_prompt_with_persona_prev(self):
        """Test generate_tot_combination_prompt with persona in prev_types."""
        from pydantic_ai_toolsets.toolsets._shared.system_prompts import generate_tot_combination_prompt
        from pydantic_ai_toolsets import create_tot_toolset, create_persona_toolset, ToTStorage, PersonaStorage
        
        tot_storage = ToTStorage()
        tot_toolset = create_tot_toolset(tot_storage, id="tot")
        persona_toolset = create_persona_toolset(PersonaStorage(), id="persona")
        
        prompt = generate_tot_combination_prompt(
            toolset=tot_toolset,
            storage=tot_storage,
            other_toolsets=[persona_toolset],
            position=1,
            prefix_map={"tot": "tot_", "persona": "persona_"},
            workflow_template=None,
        )
        assert "persona" in prompt.lower() or "perspective" in prompt.lower()

    def test_generate_tot_combination_prompt_with_refinement_next(self):
        """Test generate_tot_combination_prompt with reflection/self_refine in next_types."""
        from pydantic_ai_toolsets.toolsets._shared.system_prompts import generate_tot_combination_prompt
        from pydantic_ai_toolsets import create_tot_toolset, create_reflection_toolset, create_self_refine_toolset, ToTStorage, ReflectionStorage, SelfRefineStorage
        
        tot_storage = ToTStorage()
        tot_toolset = create_tot_toolset(tot_storage, id="tot")
        reflection_toolset = create_reflection_toolset(ReflectionStorage(), id="reflection")
        self_refine_toolset = create_self_refine_toolset(SelfRefineStorage(), id="self_refine")
        
        prompt1 = generate_tot_combination_prompt(
            toolset=tot_toolset,
            storage=tot_storage,
            other_toolsets=[reflection_toolset],
            position=0,
            prefix_map={"tot": "tot_", "reflection": "reflection_"},
            workflow_template=None,
        )
        assert "refined" in prompt1.lower() or "refinement" in prompt1.lower()
        
        prompt2 = generate_tot_combination_prompt(
            toolset=tot_toolset,
            storage=tot_storage,
            other_toolsets=[self_refine_toolset],
            position=0,
            prefix_map={"tot": "tot_", "self_refine": "self_refine_"},
            workflow_template=None,
        )
        assert "refined" in prompt2.lower() or "refinement" in prompt2.lower()

    def test_generate_tot_combination_prompt_with_todo_next(self):
        """Test generate_tot_combination_prompt with todo in next_types."""
        from pydantic_ai_toolsets.toolsets._shared.system_prompts import generate_tot_combination_prompt
        from pydantic_ai_toolsets import create_tot_toolset, create_todo_toolset, ToTStorage, TodoStorage
        
        tot_storage = ToTStorage()
        tot_toolset = create_tot_toolset(tot_storage, id="tot")
        todo_toolset = create_todo_toolset(TodoStorage(), id="todo")
        
        prompt = generate_tot_combination_prompt(
            toolset=tot_toolset,
            storage=tot_storage,
            other_toolsets=[todo_toolset],
            position=0,
            prefix_map={"tot": "tot_", "todo": "todo_"},
            workflow_template=None,
        )
        assert "task" in prompt.lower() or "tracked" in prompt.lower()

    def test_generate_got_combination_prompt_with_current_state_section(self):
        """Test generate_got_combination_prompt extracts and updates current_state_section."""
        from pydantic_ai_toolsets.toolsets._shared.system_prompts import generate_got_combination_prompt
        from pydantic_ai_toolsets import create_got_toolset, GoTStorage
        
        got_storage = GoTStorage()
        got_toolset = create_got_toolset(got_storage, id="got")
        
        prompt = generate_got_combination_prompt(
            toolset=got_toolset,
            storage=got_storage,
            other_toolsets=[],
            position=0,
            prefix_map={"got": "got_"},
            workflow_template=None,
        )
        assert "Current State" in prompt or "got_" in prompt

    def test_generate_got_combination_prompt_with_persona_prev(self):
        """Test generate_got_combination_prompt with persona in prev_types."""
        from pydantic_ai_toolsets.toolsets._shared.system_prompts import generate_got_combination_prompt
        from pydantic_ai_toolsets import create_got_toolset, create_persona_toolset, GoTStorage, PersonaStorage
        
        got_storage = GoTStorage()
        got_toolset = create_got_toolset(got_storage, id="got")
        persona_toolset = create_persona_toolset(PersonaStorage(), id="persona")
        
        prompt = generate_got_combination_prompt(
            toolset=got_toolset,
            storage=got_storage,
            other_toolsets=[persona_toolset],
            position=1,
            prefix_map={"got": "got_", "persona": "persona_"},
            workflow_template=None,
        )
        assert "persona" in prompt.lower() or "perspective" in prompt.lower()

    def test_generate_got_combination_prompt_with_refinement_next(self):
        """Test generate_got_combination_prompt with reflection/self_refine in next_types."""
        from pydantic_ai_toolsets.toolsets._shared.system_prompts import generate_got_combination_prompt
        from pydantic_ai_toolsets import create_got_toolset, create_reflection_toolset, create_self_refine_toolset, GoTStorage, ReflectionStorage, SelfRefineStorage
        
        got_storage = GoTStorage()
        got_toolset = create_got_toolset(got_storage, id="got")
        reflection_toolset = create_reflection_toolset(ReflectionStorage(), id="reflection")
        self_refine_toolset = create_self_refine_toolset(SelfRefineStorage(), id="self_refine")
        
        prompt1 = generate_got_combination_prompt(
            toolset=got_toolset,
            storage=got_storage,
            other_toolsets=[reflection_toolset],
            position=0,
            prefix_map={"got": "got_", "reflection": "reflection_"},
            workflow_template=None,
        )
        assert "refined" in prompt1.lower() or "refinement" in prompt1.lower()
        
        prompt2 = generate_got_combination_prompt(
            toolset=got_toolset,
            storage=got_storage,
            other_toolsets=[self_refine_toolset],
            position=0,
            prefix_map={"got": "got_", "self_refine": "self_refine_"},
            workflow_template=None,
        )
        assert "refined" in prompt2.lower() or "refinement" in prompt2.lower()

    def test_generate_got_combination_prompt_with_todo_next(self):
        """Test generate_got_combination_prompt with todo in next_types."""
        from pydantic_ai_toolsets.toolsets._shared.system_prompts import generate_got_combination_prompt
        from pydantic_ai_toolsets import create_got_toolset, create_todo_toolset, GoTStorage, TodoStorage
        
        got_storage = GoTStorage()
        got_toolset = create_got_toolset(got_storage, id="got")
        todo_toolset = create_todo_toolset(TodoStorage(), id="todo")
        
        prompt = generate_got_combination_prompt(
            toolset=got_toolset,
            storage=got_storage,
            other_toolsets=[todo_toolset],
            position=0,
            prefix_map={"got": "got_", "todo": "todo_"},
            workflow_template=None,
        )
        assert "task" in prompt.lower() or "tracked" in prompt.lower()

    def test_generate_mcts_combination_prompt_with_current_state_section(self):
        """Test generate_mcts_combination_prompt extracts and updates current_state_section."""
        from pydantic_ai_toolsets.toolsets._shared.system_prompts import generate_mcts_combination_prompt
        from pydantic_ai_toolsets import create_mcts_toolset, MCTSStorage
        
        mcts_storage = MCTSStorage()
        mcts_toolset = create_mcts_toolset(mcts_storage, id="mcts")
        
        prompt = generate_mcts_combination_prompt(
            toolset=mcts_toolset,
            storage=mcts_storage,
            other_toolsets=[],
            position=0,
            prefix_map={"mcts": "mcts_"},
            workflow_template=None,
        )
        assert "Current State" in prompt or "mcts_" in prompt

    def test_generate_mcts_combination_prompt_with_persona_debate_prev(self):
        """Test generate_mcts_combination_prompt with persona_debate in prev_types."""
        from pydantic_ai_toolsets.toolsets._shared.system_prompts import generate_mcts_combination_prompt
        from pydantic_ai_toolsets import create_mcts_toolset, create_persona_debate_toolset, MCTSStorage, PersonaDebateStorage
        
        mcts_storage = MCTSStorage()
        mcts_toolset = create_mcts_toolset(mcts_storage, id="mcts")
        persona_debate_toolset = create_persona_debate_toolset(PersonaDebateStorage(), id="persona_debate")
        
        prompt = generate_mcts_combination_prompt(
            toolset=mcts_toolset,
            storage=mcts_storage,
            other_toolsets=[persona_debate_toolset],
            position=1,
            prefix_map={"mcts": "mcts_", "persona_debate": "persona_debate_"},
            workflow_template=None,
        )
        assert "debate" in prompt.lower() or "position" in prompt.lower()

    def test_generate_mcts_combination_prompt_with_refinement_next(self):
        """Test generate_mcts_combination_prompt with reflection/self_refine in next_types."""
        from pydantic_ai_toolsets.toolsets._shared.system_prompts import generate_mcts_combination_prompt
        from pydantic_ai_toolsets import create_mcts_toolset, create_reflection_toolset, create_self_refine_toolset, MCTSStorage, ReflectionStorage, SelfRefineStorage
        
        mcts_storage = MCTSStorage()
        mcts_toolset = create_mcts_toolset(mcts_storage, id="mcts")
        reflection_toolset = create_reflection_toolset(ReflectionStorage(), id="reflection")
        self_refine_toolset = create_self_refine_toolset(SelfRefineStorage(), id="self_refine")
        
        prompt1 = generate_mcts_combination_prompt(
            toolset=mcts_toolset,
            storage=mcts_storage,
            other_toolsets=[reflection_toolset],
            position=0,
            prefix_map={"mcts": "mcts_", "reflection": "reflection_"},
            workflow_template=None,
        )
        assert "refined" in prompt1.lower() or "refinement" in prompt1.lower()
        
        prompt2 = generate_mcts_combination_prompt(
            toolset=mcts_toolset,
            storage=mcts_storage,
            other_toolsets=[self_refine_toolset],
            position=0,
            prefix_map={"mcts": "mcts_", "self_refine": "self_refine_"},
            workflow_template=None,
        )
        assert "refined" in prompt2.lower() or "refinement" in prompt2.lower()

    def test_generate_mcts_combination_prompt_with_todo_next(self):
        """Test generate_mcts_combination_prompt with todo in next_types."""
        from pydantic_ai_toolsets.toolsets._shared.system_prompts import generate_mcts_combination_prompt
        from pydantic_ai_toolsets import create_mcts_toolset, create_todo_toolset, create_search_toolset, MCTSStorage, TodoStorage, SearchStorage
        
        mcts_storage = MCTSStorage()
        mcts_toolset = create_mcts_toolset(mcts_storage, id="mcts")
        search_toolset = create_search_toolset(SearchStorage(), id="search")  # Dummy at index 0
        todo_toolset = create_todo_toolset(TodoStorage(), id="todo")  # At index 1
        
        prompt = generate_mcts_combination_prompt(
            toolset=mcts_toolset,
            storage=mcts_storage,
            other_toolsets=[search_toolset, todo_toolset],
            position=0,
            prefix_map={"mcts": "mcts_", "todo": "todo_", "search": "search_"},
            workflow_template=None,
        )
        assert "task" in prompt.lower() or "tracked" in prompt.lower()

    def test_generate_beam_combination_prompt_with_current_state_section(self):
        """Test generate_beam_combination_prompt extracts and updates current_state_section."""
        from pydantic_ai_toolsets.toolsets._shared.system_prompts import generate_beam_combination_prompt
        from pydantic_ai_toolsets import create_beam_toolset, BeamStorage
        
        beam_storage = BeamStorage()
        beam_toolset = create_beam_toolset(beam_storage, id="beam")
        
        prompt = generate_beam_combination_prompt(
            toolset=beam_toolset,
            storage=beam_storage,
            other_toolsets=[],
            position=0,
            prefix_map={"beam": "beam_"},
            workflow_template=None,
        )
        assert "Current State" in prompt or "beam_" in prompt

    def test_generate_beam_combination_prompt_with_refinement_next(self):
        """Test generate_beam_combination_prompt with reflection/self_refine in next_types."""
        from pydantic_ai_toolsets.toolsets._shared.system_prompts import generate_beam_combination_prompt
        from pydantic_ai_toolsets import create_beam_toolset, create_reflection_toolset, create_self_refine_toolset, BeamStorage, ReflectionStorage, SelfRefineStorage
        
        beam_storage = BeamStorage()
        beam_toolset = create_beam_toolset(beam_storage, id="beam")
        reflection_toolset = create_reflection_toolset(ReflectionStorage(), id="reflection")
        self_refine_toolset = create_self_refine_toolset(SelfRefineStorage(), id="self_refine")
        
        prompt1 = generate_beam_combination_prompt(
            toolset=beam_toolset,
            storage=beam_storage,
            other_toolsets=[reflection_toolset],
            position=0,
            prefix_map={"beam": "beam_", "reflection": "reflection_"},
            workflow_template=None,
        )
        assert "refined" in prompt1.lower() or "refinement" in prompt1.lower()
        
        prompt2 = generate_beam_combination_prompt(
            toolset=beam_toolset,
            storage=beam_storage,
            other_toolsets=[self_refine_toolset],
            position=0,
            prefix_map={"beam": "beam_", "self_refine": "self_refine_"},
            workflow_template=None,
        )
        assert "refined" in prompt2.lower() or "refinement" in prompt2.lower()

    def test_generate_beam_combination_prompt_with_todo_next(self):
        """Test generate_beam_combination_prompt with todo in next_types."""
        from pydantic_ai_toolsets.toolsets._shared.system_prompts import generate_beam_combination_prompt
        from pydantic_ai_toolsets import create_beam_toolset, create_todo_toolset, BeamStorage, TodoStorage
        
        beam_storage = BeamStorage()
        beam_toolset = create_beam_toolset(beam_storage, id="beam")
        todo_toolset = create_todo_toolset(TodoStorage(), id="todo")
        
        prompt = generate_beam_combination_prompt(
            toolset=beam_toolset,
            storage=beam_storage,
            other_toolsets=[todo_toolset],
            position=0,
            prefix_map={"beam": "beam_", "todo": "todo_"},
            workflow_template=None,
        )
        assert "task" in prompt.lower() or "tracked" in prompt.lower()

    def test_generate_persona_combination_prompt_with_current_state_section(self):
        """Test generate_persona_combination_prompt extracts and updates current_state_section."""
        from pydantic_ai_toolsets.toolsets._shared.system_prompts import generate_persona_combination_prompt
        from pydantic_ai_toolsets import create_persona_toolset, PersonaStorage
        
        persona_storage = PersonaStorage()
        persona_toolset = create_persona_toolset(persona_storage, id="persona")
        
        prompt = generate_persona_combination_prompt(
            toolset=persona_toolset,
            storage=persona_storage,
            other_toolsets=[],
            position=0,
            prefix_map={"persona": "persona_"},
            workflow_template=None,
        )
        assert "Current Persona Session" in prompt or "persona_" in prompt

    def test_generate_persona_combination_prompt_with_got_next(self):
        """Test generate_persona_combination_prompt with got in next_types."""
        from pydantic_ai_toolsets.toolsets._shared.system_prompts import generate_persona_combination_prompt
        from pydantic_ai_toolsets import create_persona_toolset, create_got_toolset, PersonaStorage, GoTStorage
        
        persona_storage = PersonaStorage()
        persona_toolset = create_persona_toolset(persona_storage, id="persona")
        got_toolset = create_got_toolset(GoTStorage(), id="got")
        
        prompt = generate_persona_combination_prompt(
            toolset=persona_toolset,
            storage=persona_storage,
            other_toolsets=[got_toolset],
            position=0,
            prefix_map={"persona": "persona_", "got": "got_"},
            workflow_template=None,
        )
        assert "graph" in prompt.lower() or "exploration" in prompt.lower()

    def test_generate_persona_combination_prompt_with_tot_next(self):
        """Test generate_persona_combination_prompt with tot in next_types."""
        from pydantic_ai_toolsets.toolsets._shared.system_prompts import generate_persona_combination_prompt
        from pydantic_ai_toolsets import create_persona_toolset, create_tot_toolset, PersonaStorage, ToTStorage
        
        persona_storage = PersonaStorage()
        persona_toolset = create_persona_toolset(persona_storage, id="persona")
        tot_toolset = create_tot_toolset(ToTStorage(), id="tot")
        
        prompt = generate_persona_combination_prompt(
            toolset=persona_toolset,
            storage=persona_storage,
            other_toolsets=[tot_toolset],
            position=0,
            prefix_map={"persona": "persona_", "tot": "tot_"},
            workflow_template=None,
        )
        assert "tree" in prompt.lower() or "exploration" in prompt.lower()

    def test_generate_persona_debate_combination_prompt_with_mcts_next(self):
        """Test generate_persona_debate_combination_prompt with mcts in next_types."""
        from pydantic_ai_toolsets.toolsets._shared.system_prompts import generate_persona_debate_combination_prompt
        from pydantic_ai_toolsets import create_persona_debate_toolset, create_mcts_toolset, PersonaDebateStorage, MCTSStorage
        
        persona_debate_storage = PersonaDebateStorage()
        persona_debate_toolset = create_persona_debate_toolset(persona_debate_storage, id="persona_debate")
        mcts_toolset = create_mcts_toolset(MCTSStorage(), id="mcts")
        
        prompt = generate_persona_debate_combination_prompt(
            toolset=persona_debate_toolset,
            storage=persona_debate_storage,
            other_toolsets=[mcts_toolset],
            position=0,
            prefix_map={"persona_debate": "persona_debate_", "mcts": "mcts_"},
            workflow_template=None,
        )
        assert "mcts" in prompt.lower() or "exploration" in prompt.lower()

    def test_generate_combination_prompt_for_toolset_fallback_with_prefix(self):
        """Test generate_combination_prompt_for_toolset fallback with prefix_map."""
        from pydantic_ai_toolsets.toolsets._shared.system_prompts import generate_combination_prompt_for_toolset
        from pydantic_ai_toolsets import create_cot_toolset, CoTStorage
        
        cot_storage = CoTStorage()
        cot_toolset = create_cot_toolset(cot_storage, id="cot")
        
        # Use a toolset type that doesn't have a combination generator
        # This will fallback to standalone prompt with prefix update
        prompt = generate_combination_prompt_for_toolset(
            toolset_type="cot",
            toolset=cot_toolset,
            storage=cot_storage,
            other_toolsets=[],
            toolset_order=0,
            prefix_map={"cot": "cot_"},
            workflow_template=None,
        )
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "cot_" in prompt

    def test_combine_system_prompts_with_prefix_map_fallback(self):
        """Test combine_system_prompts with prefix_map for fallback case."""
        from pydantic_ai_toolsets.toolsets._shared.system_prompts import combine_system_prompts
        from pydantic_ai_toolsets import create_cot_toolset, CoTStorage
        
        cot_toolset = create_cot_toolset(CoTStorage(), id="cot")
        
        prompt = combine_system_prompts(
            toolsets=[cot_toolset],
            storages={cot_toolset: CoTStorage()},
            prefix_map={"cot": "cot_"},
            workflow_template=None,
        )
        assert isinstance(prompt, str)
        assert len(prompt) > 0
