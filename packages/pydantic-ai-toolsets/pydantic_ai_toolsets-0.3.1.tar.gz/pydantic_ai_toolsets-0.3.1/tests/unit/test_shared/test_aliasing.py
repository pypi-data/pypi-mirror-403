"""Unit tests for aliasing utilities."""

from __future__ import annotations

import pytest

from pydantic_ai_toolsets.toolsets._shared.aliasing import (
    create_aliased_toolset,
    get_prefix_for_toolset,
)
from tests.fixtures.mock_agents import MockToolset


class TestGetPrefixForToolset:
    """Test suite for get_prefix_for_toolset function."""

    def test_cot_prefixes(self):
        """Test CoT prefix mappings."""
        assert get_prefix_for_toolset("cot") == "cot_"
        assert get_prefix_for_toolset("chain_of_thought") == "cot_"
        assert get_prefix_for_toolset("chain_of_thought_reasoning") == "cot_"

    def test_tot_prefixes(self):
        """Test ToT prefix mappings."""
        assert get_prefix_for_toolset("tot") == "tot_"
        assert get_prefix_for_toolset("tree_of_thought") == "tot_"
        assert get_prefix_for_toolset("tree_of_thought_reasoning") == "tot_"

    def test_got_prefixes(self):
        """Test GoT prefix mappings."""
        assert get_prefix_for_toolset("got") == "got_"
        assert get_prefix_for_toolset("graph_of_thought") == "got_"
        assert get_prefix_for_toolset("graph_of_thought_reasoning") == "got_"

    def test_mcts_prefixes(self):
        """Test MCTS prefix mappings."""
        assert get_prefix_for_toolset("mcts") == "mcts_"
        assert get_prefix_for_toolset("monte_carlo") == "mcts_"
        assert get_prefix_for_toolset("monte_carlo_reasoning") == "mcts_"

    def test_beam_prefixes(self):
        """Test Beam prefix mappings."""
        assert get_prefix_for_toolset("beam") == "beam_"
        assert get_prefix_for_toolset("beam_search") == "beam_"
        assert get_prefix_for_toolset("beam_search_reasoning") == "beam_"

    def test_reflection_prefixes(self):
        """Test Reflection prefix mappings."""
        assert get_prefix_for_toolset("reflection") == "reflection_"

    def test_self_refine_prefixes(self):
        """Test Self-Refine prefix mappings."""
        assert get_prefix_for_toolset("self_refine") == "self_refine_"

    def test_self_ask_prefixes(self):
        """Test Self-Ask prefix mappings."""
        assert get_prefix_for_toolset("self_ask") == "self_ask_"

    def test_persona_prefixes(self):
        """Test Persona prefix mappings."""
        assert get_prefix_for_toolset("persona") == "persona_"
        assert get_prefix_for_toolset("multi_persona") == "persona_"
        assert get_prefix_for_toolset("multi_persona_analysis") == "persona_"

    def test_persona_debate_prefixes(self):
        """Test Persona Debate prefix mappings."""
        assert get_prefix_for_toolset("persona_debate") == "persona_debate_"
        assert get_prefix_for_toolset("multi_persona_debate") == "persona_debate_"

    def test_search_prefixes(self):
        """Test Search prefix mappings."""
        assert get_prefix_for_toolset("search") == "search_"

    def test_todo_prefixes(self):
        """Test Todo prefix mappings."""
        assert get_prefix_for_toolset("todo") == "todo_"
        assert get_prefix_for_toolset("to_do") == "todo_"

    def test_unknown_prefix(self):
        """Test unknown toolset ID returns default prefix."""
        assert get_prefix_for_toolset("unknown_toolset") == "unknown_toolset_"

    def test_empty_string(self):
        """Test empty string returns empty prefix."""
        assert get_prefix_for_toolset("") == ""
        assert get_prefix_for_toolset(None) == ""

    def test_none_values(self):
        """Test None values."""
        assert get_prefix_for_toolset(None) == ""
        assert get_prefix_for_toolset(None, None) == ""

    def test_label_parameter(self):
        """Test toolset_label parameter."""
        assert get_prefix_for_toolset(None, "cot") == "cot_"
        assert get_prefix_for_toolset(None, "tot") == "tot_"

    def test_case_insensitive(self):
        """Test case insensitivity."""
        assert get_prefix_for_toolset("COT") == "cot_"
        assert get_prefix_for_toolset("ToT") == "tot_"
        assert get_prefix_for_toolset("SELF_ASK") == "self_ask_"

    def test_whitespace_stripping(self):
        """Test whitespace stripping."""
        assert get_prefix_for_toolset("  cot  ") == "cot_"
        assert get_prefix_for_toolset(" tot ") == "tot_"


class TestCreateAliasedToolset:
    """Test suite for create_aliased_toolset function."""

    def test_create_aliased_toolset_with_prefix(self):
        """Test creating aliased toolset with prefix."""
        base_toolset = MockToolset(id="cot")
        aliased = create_aliased_toolset(base_toolset, "cot_")
        
        assert aliased is not base_toolset
        assert hasattr(aliased, "prefixed")

    def test_create_aliased_toolset_empty_prefix(self):
        """Test creating aliased toolset with empty prefix returns original."""
        base_toolset = MockToolset(id="cot")
        aliased = create_aliased_toolset(base_toolset, "")
        
        assert aliased is base_toolset

    def test_create_aliased_toolset_calls_prefixed(self):
        """Test that create_aliased_toolset calls prefixed method."""
        base_toolset = MockToolset(id="cot")
        prefixed_called = False
        
        def mock_prefixed(prefix: str):
            nonlocal prefixed_called
            prefixed_called = True
            return MockToolset(id=f"{prefix}cot")
        
        base_toolset.prefixed = mock_prefixed
        result = create_aliased_toolset(base_toolset, "cot_")
        
        assert prefixed_called
        assert result is not None
