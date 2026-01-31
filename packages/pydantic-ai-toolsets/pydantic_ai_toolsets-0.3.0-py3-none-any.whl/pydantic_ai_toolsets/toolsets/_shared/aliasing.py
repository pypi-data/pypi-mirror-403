"""Dynamic toolset aliasing using official pydantic-ai API."""

from __future__ import annotations

from typing import Any

from pydantic_ai.toolsets import AbstractToolset


def get_prefix_for_toolset(toolset_id: str | None, toolset_label: str | None = None) -> str:
    """Get the prefix for a toolset based on its ID or label.

    Args:
        toolset_id: Optional toolset ID (e.g., "cot", "tot", "self_ask")
        toolset_label: Optional toolset label/name

    Returns:
        Prefix string (e.g., "cot_", "tot_", "self_ask_")

    Example:
        ```python
        prefix = get_prefix_for_toolset("cot")  # Returns "cot_"
        prefix = get_prefix_for_toolset("self_ask")  # Returns "self_ask_"
        ```
    """
    # Normalize toolset identifier
    identifier = toolset_id or toolset_label or ""
    identifier = identifier.lower().strip()

    # Prefix mapping for all toolsets
    prefix_map: dict[str, str] = {
        # Reasoning toolsets
        "cot": "cot_",
        "chain_of_thought": "cot_",
        "chain_of_thought_reasoning": "cot_",
        "tot": "tot_",
        "tree_of_thought": "tot_",
        "tree_of_thought_reasoning": "tot_",
        "got": "got_",
        "graph_of_thought": "got_",
        "graph_of_thought_reasoning": "got_",
        "mcts": "mcts_",
        "monte_carlo": "mcts_",
        "monte_carlo_reasoning": "mcts_",
        "beam": "beam_",
        "beam_search": "beam_",
        "beam_search_reasoning": "beam_",
        # Reflection/refinement toolsets
        "reflection": "reflection_",
        "self_refine": "self_refine_",
        "self_ask": "self_ask_",
        # Multi-agent toolsets
        "persona": "persona_",
        "multi_persona": "persona_",
        "multi_persona_analysis": "persona_",
        "persona_debate": "persona_debate_",
        "multi_persona_debate": "persona_debate_",
        # Utility toolsets
        "search": "search_",
        "todo": "todo_",
        "to_do": "todo_",
    }

    # Return mapped prefix or default to identifier + "_"
    return prefix_map.get(identifier, f"{identifier}_" if identifier else "")


def create_aliased_toolset(
    base_toolset: AbstractToolset[Any],
    prefix: str,
) -> AbstractToolset[Any]:
    """Create an aliased version of a toolset with prefixed tool names.

    Uses the official pydantic-ai API: AbstractToolset.prefixed()

    This function wraps a toolset and prefixes all its tool names to avoid
    collisions when combining multiple toolsets.

    Args:
        base_toolset: The original toolset to alias (unchanged)
        prefix: Prefix to add to all tool names (e.g., "cot_", "tot_")

    Returns:
        PrefixedToolset with aliased tool names

    Example:
        ```python
        from pydantic_ai_toolsets import create_cot_toolset

        cot_toolset = create_cot_toolset()
        aliased_cot = create_aliased_toolset(cot_toolset, "cot_")
        # Tools are now: cot_read_thoughts, cot_write_thoughts
        ```

    Note:
        - The original toolset is NOT modified
        - All tool names are prefixed (even if no collision exists)
        - System prompts remain unchanged (handled separately)
    """
    if not prefix:
        return base_toolset

    # Use official API method - no introspection needed!
    return base_toolset.prefixed(prefix)
