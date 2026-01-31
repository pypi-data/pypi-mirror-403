"""Helper functions for combining toolsets and managing workflows."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.toolsets import AbstractToolset, CombinedToolset

from .._shared.aliasing import create_aliased_toolset, get_prefix_for_toolset
from .._shared.system_prompts import combine_system_prompts
from .types import WorkflowTemplate


def create_combined_toolset(
    toolsets: list[AbstractToolset[Any]],
    storages: dict[str, Any] | None = None,
    prefix_map: dict[str, str] | None = None,
    orchestrator: AbstractToolset[Any] | None = None,
    workflow_template: WorkflowTemplate | None = None,
    auto_prefix: bool = True,
) -> tuple[CombinedToolset[Any], str]:
    """Combine multiple toolsets with automatic collision resolution.

    Uses official pydantic-ai API:
    - AbstractToolset.prefixed() to create aliased toolsets
    - CombinedToolset to combine toolsets

    Strategy:
    1. If auto_prefix=True, apply prefixes to all toolsets based on prefix_map
       (prevents collisions proactively)
    2. If auto_prefix=False, rely on CombinedToolset to detect collisions
       (raises UserError if collisions exist - user must handle)
    3. Use CombinedToolset to combine all toolsets
    4. Add orchestrator tools if provided
    5. Combine system prompts from all toolsets

    Args:
        toolsets: List of toolsets to combine
        storages: Optional dictionary mapping toolset IDs to storage instances
        prefix_map: Optional dictionary mapping toolset IDs to prefixes.
                   If not provided, prefixes are inferred from toolset IDs.
        orchestrator: Optional meta-orchestrator toolset to add
        workflow_template: Optional workflow template for context
        auto_prefix: If True, automatically prefix all toolsets to prevent collisions

    Returns:
        Tuple of (CombinedToolset, combined_system_prompt)

    Example:
        ```python
        from pydantic_ai_toolsets import create_cot_toolset, create_tot_toolset
        from pydantic_ai_toolsets.toolsets.meta_orchestrator.helpers import create_combined_toolset

        cot_toolset = create_cot_toolset()
        tot_toolset = create_tot_toolset()

        prefix_map = {
            "cot": "cot_",
            "tot": "tot_",
        }

        combined_toolset, combined_prompt = create_combined_toolset(
            toolsets=[cot_toolset, tot_toolset],
            prefix_map=prefix_map,
        )
        ```
    """
    # 1. Apply prefixes if auto_prefix is enabled
    if auto_prefix:
        aliased_toolsets = []
        for toolset in toolsets:
            # Get toolset ID (from toolset.id or infer from prefix_map keys)
            toolset_id = toolset.id if hasattr(toolset, "id") and toolset.id else None

            # Get prefix from prefix_map or infer from toolset
            if prefix_map and toolset_id and toolset_id in prefix_map:
                prefix = prefix_map[toolset_id]
            elif toolset_id:
                prefix = get_prefix_for_toolset(toolset_id)
            else:
                # Try to infer from prefix_map keys (fallback)
                prefix = None
                if prefix_map:
                    # Find matching prefix by checking toolset type
                    for key, value in prefix_map.items():
                        if key.lower() in str(type(toolset)).lower():
                            prefix = value
                            break

            if prefix:
                # Use official prefixed() method!
                aliased_toolsets.append(create_aliased_toolset(toolset, prefix))
            else:
                # No prefix available, use original
                aliased_toolsets.append(toolset)
    else:
        # No auto-prefixing, use toolsets as-is
        # CombinedToolset will raise UserError on collisions
        aliased_toolsets = toolsets

    # 2. Add orchestrator tools if provided
    all_toolsets = aliased_toolsets.copy()
    if orchestrator:
        all_toolsets.append(orchestrator)

    # 3. Use official CombinedToolset to combine all toolsets
    # This will raise UserError if there are still collisions (when auto_prefix=False)
    combined_toolset = CombinedToolset(all_toolsets)

    # 4. Combine system prompts from all toolsets
    # Build toolset_id -> toolset mapping for prompt combination
    toolset_id_map: dict[str, AbstractToolset[Any]] = {}
    for i, toolset in enumerate(toolsets):
        toolset_id = toolset.id if hasattr(toolset, "id") and toolset.id else f"toolset_{i}"
        toolset_id_map[toolset_id] = toolset

    combined_prompt = combine_system_prompts(
        toolsets=toolsets,  # Use original toolsets (before prefixing) to get original prompts
        storages=storages,
        prefix_map=prefix_map,
        workflow_template=workflow_template,
    )

    return combined_toolset, combined_prompt


def register_toolsets_with_orchestrator(
    orchestrator_storage: Any,
    toolsets: list[AbstractToolset[Any]],
    storages: dict[str, Any] | None = None,
) -> None:
    """Register toolsets with the meta-orchestrator storage.

    Args:
        orchestrator_storage: MetaOrchestratorStorage instance
        toolsets: List of toolsets to register
        storages: Optional dictionary mapping toolset IDs to storage instances
    """
    for toolset in toolsets:
        toolset_id = toolset.id if hasattr(toolset, "id") and toolset.id else "unknown"
        toolset_info: dict[str, Any] = {
            "type": type(toolset).__name__,
            "label": toolset_id,
        }
        if storages and toolset_id in storages:
            toolset_info["storage"] = storages[toolset_id]
        orchestrator_storage.register_toolset(toolset_id, toolset_info)


def create_workflow_agent(
    model: str,
    workflow_template: WorkflowTemplate,
    toolsets: list[AbstractToolset[Any]],
    storages: dict[str, Any] | None = None,
    prefix_map: dict[str, str] | None = None,
    orchestrator_storage: Any | None = None,
    auto_prefix: bool = True,
    additional_system_prompt: str | None = None,
    output_type: type[BaseModel] | list[type[BaseModel]] | None = None,
) -> Agent[Any]:
    """Create an agent configured with a workflow template and combined toolsets.

    This is a convenience function that:
    1. Creates a meta-orchestrator toolset (if orchestrator_storage is provided)
    2. Registers all toolsets with the orchestrator
    3. Combines all toolsets with automatic prefixing
    4. Creates an agent with the combined toolset and workflow-aware system prompt

    Args:
        model: Model string for the agent (e.g., "openai:gpt-4")
        workflow_template: Workflow template to use
        toolsets: List of toolsets to combine
        storages: Optional dictionary mapping toolset IDs to storage instances
        prefix_map: Optional dictionary mapping toolset IDs to prefixes.
                   If not provided, prefixes are inferred from toolset IDs.
        orchestrator_storage: Optional MetaOrchestratorStorage instance.
                            If provided, creates and registers orchestrator toolset.
        auto_prefix: If True, automatically prefix all toolsets to prevent collisions
        additional_system_prompt: Optional additional system prompt that will be appended
                                 to the combined prompt. Use this to add custom instructions
                                 or context without overriding the workflow-specific prompts.
        output_type: Optional Pydantic BaseModel class or list of BaseModel classes
                    to use as the structured output type for the agent. If provided,
                    the agent will return structured outputs matching this schema.

    Returns:
        Configured Agent instance with combined toolsets and workflow template

    Example:
        ```python
        from pydantic_ai_toolsets import (
            RESEARCH_ASSISTANT,
            create_search_toolset,
            create_self_ask_toolset,
            create_self_refine_toolset,
            create_todo_toolset,
            SearchStorage,
            SelfAskStorage,
            SelfRefineStorage,
            TodoStorage,
            MetaOrchestratorStorage,
        )
        from pydantic_ai_toolsets.toolsets.meta_orchestrator.helpers import create_workflow_agent

        # Create storages
        storages = {
            "search": SearchStorage(),
            "self_ask": SelfAskStorage(),
            "self_refine": SelfRefineStorage(),
            "todo": TodoStorage(),
        }

        # Create toolsets
        toolsets = [
            create_search_toolset(storages["search"], id="search"),
            create_self_ask_toolset(storages["self_ask"], id="self_ask"),
            create_self_refine_toolset(storages["self_refine"], id="self_refine"),
            create_todo_toolset(storages["todo"], id="todo"),
        ]

        # Create orchestrator storage
        orchestrator_storage = MetaOrchestratorStorage()

        # Create agent with workflow template and additional instructions
        agent = create_workflow_agent(
            model="openai:gpt-4",
            workflow_template=RESEARCH_ASSISTANT,
            toolsets=toolsets,
            storages=storages,
            orchestrator_storage=orchestrator_storage,
            additional_system_prompt="Always cite sources and provide URLs when available.",
        )

        # Use the agent
        result = await agent.run("Research quantum computing breakthroughs")

        # Example with output type:
        from pydantic import BaseModel

        class ResearchResult(BaseModel):
            summary: str
            sources: list[str]
            key_findings: list[str]

        agent_with_output = create_workflow_agent(
            model="openai:gpt-4",
            workflow_template=RESEARCH_ASSISTANT,
            toolsets=toolsets,
            storages=storages,
            orchestrator_storage=orchestrator_storage,
            output_type=ResearchResult,
        )
        result = await agent_with_output.run("Research quantum computing breakthroughs")
        print(result.output.summary)  # Access structured output
        ```
    """
    # Import here to avoid circular imports
    from .toolset import create_meta_orchestrator_toolset

    # 1. Create orchestrator toolset if storage is provided
    orchestrator_toolset: AbstractToolset[Any] | None = None
    if orchestrator_storage:
        orchestrator_toolset = create_meta_orchestrator_toolset(orchestrator_storage, id="orchestrator")
        # Register toolsets with orchestrator
        register_toolsets_with_orchestrator(
            orchestrator_storage=orchestrator_storage,
            toolsets=toolsets,
            storages=storages,
        )

    # 2. Create combined toolset
    combined_toolset, combined_prompt = create_combined_toolset(
        toolsets=toolsets,
        storages=storages,
        prefix_map=prefix_map,
        orchestrator=orchestrator_toolset,
        workflow_template=workflow_template,
        auto_prefix=auto_prefix,
    )

    # 3. Combine system prompts: append additional prompt if provided
    if additional_system_prompt:
        system_prompt = f"{combined_prompt}\n\n{additional_system_prompt}"
    else:
        system_prompt = combined_prompt

    # 4. Create agent with combined toolset and prompt
    agent_kwargs: dict[str, Any] = {
        "system_prompt": system_prompt,
        "toolsets": [combined_toolset],
    }
    if output_type is not None:
        agent_kwargs["output_type"] = output_type

    agent = Agent(model, **agent_kwargs)

    return agent
