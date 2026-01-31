---
name: Implement Toolset Combination System
overview: Implement a comprehensive system for combining multiple toolsets together, including a meta-orchestrator toolset, workflow templates, cross-toolset linking, unified state management, and comprehensive README documentation.
todos:
  - id: meta-orchestrator-types
    content: Create meta-orchestrator types.py with WorkflowState, ToolsetTransition, WorkflowTemplate, CrossToolsetLink
    status: pending
  - id: meta-orchestrator-storage
    content: Create meta-orchestrator storage.py with MetaOrchestratorStorage and WorkflowRegistry
    status: pending
  - id: meta-orchestrator-toolset
    content: Create meta-orchestrator toolset.py with read_unified_state, suggest_toolset_transition, start_workflow, link_toolset_outputs
    status: pending
  - id: workflow-templates
    content: Create workflow_templates.py with 4 predefined templates (Research Assistant, Creative Problem Solver, Strategic Decision Maker, Code Architect)
    status: pending
  - id: linking-infrastructure
    content: Create _shared/linking.py with LinkManager for cross-toolset references
    status: pending
  - id: update-storage-classes
    content: Add link tracking to existing storage classes (optional links and linked_from fields)
    status: pending
  - id: update-cot-toolset-names
    content: Update chain_of_thought_reasoning/toolset.py to use cot_ prefix for all function names
    status: pending
  - id: update-tot-toolset-names
    content: Update tree_of_thought_reasoning/toolset.py to use tot_ prefix for all function names
    status: pending
  - id: update-got-toolset-names
    content: Update graph_of_thought_reasoning/toolset.py to use got_ prefix for all function names
    status: pending
  - id: update-mcts-toolset-names
    content: Update monte_carlo_reasoning/toolset.py to use mcts_ prefix for all function names
    status: pending
  - id: update-beam-toolset-names
    content: Update beam_search_reasoning/toolset.py to use beam_ prefix for all function names
    status: pending
  - id: update-reflection-toolset-names
    content: Update reflection/toolset.py to use reflection_ prefix for all function names
    status: pending
  - id: update-self-refine-toolset-names
    content: Update self_refine/toolset.py to use self_refine_ prefix for all function names
    status: pending
  - id: update-self-ask-toolset-names
    content: Update self_ask/toolset.py to use self_ask_ prefix for all function names
    status: pending
  - id: update-persona-toolset-names
    content: Update multi_persona_analysis/toolset.py to use persona_ prefix for all function names
    status: pending
  - id: update-persona-debate-toolset-names
    content: Update multi_persona_debate/toolset.py to use persona_debate_ prefix for all function names
    status: pending
  - id: update-search-toolset-names
    content: Update search/toolset.py to use search_ prefix for all function names
    status: pending
  - id: update-todo-toolset-names
    content: Update to_do/toolset.py to use todo_ prefix for all function names
    status: pending
  - id: update-all-system-prompts
    content: Update all system prompts in toolset.py files to reference prefixed function names
    status: pending
  - id: update-all-tool-descriptions
    content: Update all tool descriptions to use prefixed names in examples
    status: pending
  - id: update-all-eval-files
    content: Update all *_eval.py files to expect and use prefixed function names
    status: pending
  - id: update-compare-functions
    content: Update compare_*.py files to handle prefixed names correctly
    status: pending
  - id: combination-helpers
    content: Create meta_orchestrator/helpers.py with create_combined_toolset and register_toolsets_with_orchestrator
    status: pending
  - id: update-init-exports
    content: Update __init__.py to export meta-orchestrator components and workflow templates
    status: pending
  - id: readme-combination-section
    content: Add Combining Toolsets section to README.md with overview, function collisions, and workflow templates
    status: pending
  - id: readme-examples
    content: Add combination examples to README.md showing each workflow template in action
    status: pending
  - id: readme-meta-orchestrator
    content: Add meta-orchestrator documentation to README.md with usage guide
    status: pending
  - id: example-research-assistant
    content: Create examples/combinations/research_assistant_example.py
    status: pending
  - id: example-creative-solver
    content: Create examples/combinations/creative_problem_solver_example.py
    status: pending
  - id: example-strategic-decision
    content: Create examples/combinations/strategic_decision_maker_example.py
    status: pending
  - id: example-code-architect
    content: Create examples/combinations/code_architect_example.py
    status: pending
  - id: create-combination-eval-infrastructure
    content: Create evals/categories/combinations/ directory with __init__.py and compare_combinations.py
    status: pending
  - id: create-research-assistant-eval
    content: Create evals/categories/combinations/research_assistant_eval.py with task function and dataset creation
    status: pending
  - id: create-creative-solver-eval
    content: Create evals/categories/combinations/creative_problem_solver_eval.py with task function and dataset creation
    status: pending
  - id: create-strategic-decision-eval
    content: Create evals/categories/combinations/strategic_decision_maker_eval.py with task function and dataset creation
    status: pending
  - id: create-code-architect-eval
    content: Create evals/categories/combinations/code_architect_eval.py with task function and dataset creation
    status: pending
  - id: create-combination-test-dataset
    content: Create evals/datasets/combination_cases.py with test cases for all 4 workflow templates (20-28 total cases)
    status: pending
  - id: update-run-evals-combinations
    content: Update run_evals.py to add run_combinations function and add combinations to category choices
    status: pending
  - id: update-datasets-init
    content: Update evals/datasets/__init__.py to export COMBINATION_CASES
    status: pending
---

# Implement Toolset Combination System

This plan implements a comprehensive system for combining multiple toolsets together, addressing function name collisions, workflow orchestration, and cross-toolset integration.

## Architecture Overview

The implementation will add:

1. **Meta-Orchestrator Toolset** - Suggests toolset transitions and tracks workflows
2. **Workflow Templates** - Predefined combinations for common patterns
3. **Cross-Toolset Linking** - Link outputs between toolsets
4. **Unified State Management** - Single read function across all toolsets
5. **Dynamic Toolset Aliasing** - Runtime-only aliasing when combining toolsets (zero source code changes, preserves backward compatibility)
6. **README Updates** - Comprehensive combination documentation

## Implementation Steps

### Phase 1: Core Infrastructure

#### 1.1 Create Meta-Orchestrator Toolset

**File**: `pydantic_ai_toolsets/toolsets/meta_orchestrator/`

- **`types.py`**: Define types for workflow tracking, toolset registry, transition suggestions
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - `WorkflowState` - tracks active toolsets and their states
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - `ToolsetTransition` - suggests when to switch toolsets
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - `WorkflowTemplate` - predefined workflow patterns
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - `CrossToolsetLink` - links between toolset outputs

- **`storage.py`**: Unified storage for orchestrator state
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - `MetaOrchestratorStorage` - tracks active toolsets, workflows, links
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - `WorkflowRegistry` - stores workflow templates
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - Methods: `register_toolset()`, `track_transition()`, `create_link()`, `get_unified_state()`

- **`toolset.py`**: Main orchestrator toolset
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - `read_unified_state()` - shows state across all active toolsets
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - `suggest_toolset_transition()` - recommends next toolset based on current state
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - `start_workflow()` - initialize a workflow template
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - `link_toolset_outputs()` - create cross-toolset links
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - `get_workflow_status()` - show current workflow progress

#### 1.2 Create Workflow Templates Module

**File**: `pydantic_ai_toolsets/toolsets/meta_orchestrator/workflow_templates.py`

Define 4 workflow templates:

- **Research Assistant**: Search → Self-Ask → Self-Refine → Todo
- **Creative Problem Solver**: Multi-Persona Analysis → Graph of Thoughts → Reflection
- **Strategic Decision Maker**: Multi-Persona Debate → MCTS → Reflection
- **Code Architect**: Self-Ask → Tree of Thoughts → Reflection → Todo

Each template includes:

- Toolset sequence
- Transition conditions
- Expected outputs at each stage
- Handoff instructions

### Phase 2: Cross-Toolset Linking

#### 2.1 Create Linking Infrastructure

**File**: `pydantic_ai_toolsets/toolsets/_shared/linking.py`

- `LinkManager` class to manage cross-toolset references
- Methods:
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - `create_link(source_toolset, source_id, target_toolset, target_id, link_type)`
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - `get_links(toolset_id, item_id)` - get all links for an item
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - `resolve_link(link_id)` - get linked item content

- Link types: `refines`, `explores`, `synthesizes`, `references`

#### 2.2 Update Storage Classes

Add optional link tracking to existing storage classes:

- Add `links: dict[str, list[str]]` to track outgoing links
- Add `linked_from: list[str]` to track incoming links
- Update storage protocols to include link methods

### Phase 3: Dynamic Toolset Aliasing (Runtime-Only, Using Official API)

**Critical Principle**: This phase implements aliasing using the official pydantic-ai API (`prefixed()` method and `CombinedToolset`). It requires ZERO modifications to existing toolset source code, function names, system prompts, or tool descriptions. All existing evals continue to work unchanged.

**What This Phase Does**:
- Uses official `AbstractToolset.prefixed()` method to create prefixed toolsets
- Uses `CombinedToolset` to combine multiple toolsets
- Detects name collisions using `get_tools()` API method
- Applies prefixes only when collisions occur (minimal aliasing)
- Preserves all original toolsets completely unchanged

**What This Phase Does NOT Do**:
- ❌ Modify any existing toolset creation functions
- ❌ Change any function names in existing toolsets
- ❌ Update any system prompts or tool descriptions
- ❌ Require any changes to existing evals
- ❌ Break backward compatibility in any way
- ❌ Use Python introspection (uses official API instead)

#### 3.1 Create Dynamic Aliasing System Using Official API

**File**: `pydantic_ai_toolsets/toolsets/_shared/aliasing.py`

**Key Principle**: All aliasing happens at runtime using the official pydantic-ai API. NO changes to existing toolset source code.

**Official API Methods** (from pydantic-ai documentation):
- `AbstractToolset.prefixed(prefix: str) -> PrefixedToolset` - Returns a toolset with prefixed tool names
- `AbstractToolset.get_tools(ctx: RunContext) -> dict[str, ToolsetTool]` - Gets all tools from a toolset
- `CombinedToolset(toolsets: Sequence[AbstractToolset])` - Combines multiple toolsets

**Implementation**:

```python
from pydantic_ai.toolsets import AbstractToolset, CombinedToolset
from pydantic_ai import RunContext
from typing import Any

def create_aliased_toolset(
    base_toolset: AbstractToolset[Any],
    prefix: str
) -> AbstractToolset[Any]:
    """Create an aliased version of a toolset with prefixed tool names.
    
    Uses the official pydantic-ai API: AbstractToolset.prefixed()
    
    Args:
        base_toolset: The original toolset to alias (unchanged)
        prefix: Prefix to add to all tool names (e.g., "cot_", "tot_")
    
    Returns:
        PrefixedToolset with aliased tool names
    """
    # Use official API method - no introspection needed!
    return base_toolset.prefixed(prefix)
```

**Benefits of Using Official API**:
- No introspection needed - uses official `prefixed()` method
- Guaranteed compatibility with pydantic-ai updates
- Handles all edge cases (async/sync, metadata, etc.)
- Preserves all tool metadata automatically
- System prompts remain unchanged (handled by PrefixedToolset)

**Prefix Mapping** (used by combination helpers):
- Chain of Thought: `cot_`
- Tree of Thoughts: `tot_`
- Graph of Thoughts: `got_`
- Monte Carlo: `mcts_`
- Beam Search: `beam_`
- Reflection: `reflection_`
- Self-Refine: `self_refine_`
- Self-Ask: `self_ask_`
- Multi-Persona Analysis: `persona_`
- Multi-Persona Debate: `persona_debate_`
- Search: `search_`
- Todo: `todo_`

#### 3.2 Collision Detection and Smart Aliasing Using Official API

**File**: `pydantic_ai_toolsets/toolsets/meta_orchestrator/helpers.py`

**Function**: `create_combined_toolset()`

**Algorithm Using Official API**:

```python
from pydantic_ai.toolsets import AbstractToolset, CombinedToolset
from pydantic_ai import RunContext
from typing import Any

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
    - CombinedToolset to combine toolsets (raises UserError on collisions)
    
    Strategy:
    1. If auto_prefix=True, apply prefixes to all toolsets based on prefix_map
       (prevents collisions proactively)
    2. If auto_prefix=False, rely on CombinedToolset to detect collisions
       (raises UserError if collisions exist - user must handle)
    3. Use CombinedToolset to combine all toolsets
    4. Add orchestrator tools if provided
    
    Note: get_tools() requires RunContext which isn't available at combination time.
    We use prefix_map to proactively prevent collisions, or let CombinedToolset
    raise errors for manual handling.
    
    Example (auto_prefix=True):
        - tot_toolset with prefix_map["tot"] = "tot_"
        - got_toolset with prefix_map["got"] = "got_"
        
        Result:
        - tot_create_node (prefixed)
        - tot_read_tree (prefixed)
        - got_create_node (prefixed)
        - got_read_graph (prefixed)
    
    Example (auto_prefix=False):
        - CombinedToolset will raise UserError if collisions exist
        - User must manually prefix conflicting toolsets
    """
    # 1. Apply prefixes if auto_prefix is enabled
    if auto_prefix:
        aliased_toolsets = []
        for toolset in toolsets:
            # Get prefix from prefix_map or infer from toolset
            prefix = get_prefix_for_toolset(toolset, prefix_map)
            if prefix:
                # Use official prefixed() method!
                aliased_toolsets.append(toolset.prefixed(prefix))
            else:
                # No prefix available, use original
                aliased_toolsets.append(toolset)
    else:
        # No auto-prefixing, use toolsets as-is
        # CombinedToolset will raise UserError on collisions
        aliased_toolsets = toolsets
    
    # 2. Add orchestrator tools if provided
    all_toolsets = aliased_toolsets
    if orchestrator:
        all_toolsets.append(orchestrator)
    
    # 3. Use official CombinedToolset to combine all toolsets
    # This will raise UserError if there are still collisions (when auto_prefix=False)
    combined_toolset = CombinedToolset(all_toolsets)
    
    # 4. Combine system prompts from all toolsets
    combined_prompt = combine_system_prompts(
        toolsets=toolsets,  # Use original toolsets (before prefixing) to get original prompts
        storages=storages,
        prefix_map=prefix_map,  # Pass prefix_map to update tool names in prompts
    )
    
    return combined_toolset, combined_prompt
```

**Key Features**:
- **Uses Official API**: `prefixed()`, `CombinedToolset`
- **Proactive Prefixing**: Uses prefix_map to prevent collisions (avoids need for RunContext)
- **Fallback**: Can disable auto_prefix and let CombinedToolset detect collisions (raises UserError)
- **No Source Changes**: All toolsets remain unchanged
- **System Prompts**: Must be manually combined (see Phase 3.4)
- **Backward Compatible**: Original toolsets work exactly as before
- **No Introspection**: Pure API usage
- **No RunContext Required**: Uses prefix_map instead of get_tools() for collision detection

#### 3.4 System Prompt Combination

**File**: `pydantic_ai_toolsets/toolsets/_shared/system_prompts.py`

**Critical Issue**: pydantic-ai's `CombinedToolset` and `PrefixedToolset` do NOT automatically combine system prompts. Each toolset has its own system prompt that describes when and how to use its tools. 

**Key Finding**: Current toolset prompts assume **standalone usage**:
- They say "You have access to tools for..." (implying these are THE tools)
- They provide complete workflows assuming only these tools exist
- They don't mention coordination with other toolsets
- They don't explain when to transition between toolsets

**Solution**: We need **combination-specific prompts** that:
1. Acknowledge other toolsets exist in the combination
2. Explain when THIS toolset fits in the overall workflow
3. Describe how to use outputs from previous toolsets as inputs
4. Provide transition guidance (when to move to next toolset)
5. Update tool names to reflect prefixes

**Implementation Strategy**:
- Each toolset should have TWO prompt variants:
  - **Standalone prompt**: Current prompt (for single-toolset usage)
  - **Combination prompt**: Modified prompt for multi-toolset workflows
- Combination prompts are generated dynamically based on:
  - Which toolsets are in the combination
  - The workflow template (if provided)
  - The order/sequence of toolsets
  - Prefixed tool names

**Implementation**:

```python
from typing import Any
from pydantic_ai.toolsets import AbstractToolset

# Mapping of toolset types to their system prompt getter functions
# These return STANDALONE prompts (for single-toolset usage)
TOOLSET_SYSTEM_PROMPT_GETTERS = {
    "cot": lambda storage: get_cot_system_prompt(storage),
    "tot": lambda storage: get_tot_system_prompt(storage),
    "got": lambda storage: get_got_system_prompt(storage),
    "mcts": lambda storage: get_mcts_system_prompt(storage),
    "beam": lambda storage: get_beam_system_prompt(storage),
    "reflection": lambda storage: get_reflection_system_prompt(),
    "self_refine": lambda storage: get_self_refine_system_prompt(),
    "self_ask": lambda storage: get_self_ask_system_prompt(),
    "persona": lambda storage: get_persona_system_prompt(storage),
    "persona_debate": lambda storage: get_persona_debate_system_prompt(),
    "search": lambda storage: get_search_system_prompt(),
    "todo": lambda storage: get_todo_system_prompt(storage),
}

# Mapping of toolset types to their COMBINATION prompt generators
# These generate prompts adapted for multi-toolset workflows
TOOLSET_COMBINATION_PROMPT_GENERATORS = {
    "cot": generate_cot_combination_prompt,
    "tot": generate_tot_combination_prompt,
    "got": generate_got_combination_prompt,
    "mcts": generate_mcts_combination_prompt,
    "beam": generate_beam_combination_prompt,
    "reflection": generate_reflection_combination_prompt,
    "self_refine": generate_self_refine_combination_prompt,
    "self_ask": generate_self_ask_combination_prompt,
    "persona": generate_persona_combination_prompt,
    "persona_debate": generate_persona_debate_combination_prompt,
    "search": generate_search_combination_prompt,
    "todo": generate_todo_combination_prompt,
}

def update_prompt_tool_names(
    prompt: str,
    tool_name_mapping: dict[str, str]
) -> str:
    """Update tool names in a system prompt to reflect aliased names.
    
    Args:
        prompt: Original system prompt
        tool_name_mapping: Mapping of original tool names to aliased names
                          e.g., {"read_thoughts": "cot_read_thoughts"}
    
    Returns:
        Updated prompt with aliased tool names
    """
    updated_prompt = prompt
    for original_name, aliased_name in tool_name_mapping.items():
        # Replace backtick-wrapped tool names (common in prompts)
        updated_prompt = updated_prompt.replace(f"`{original_name}`", f"`{aliased_name}`")
        # Replace tool names in lists/descriptions
        updated_prompt = updated_prompt.replace(f"- `{original_name}`", f"- `{aliased_name}`")
        # Replace standalone mentions
        updated_prompt = updated_prompt.replace(f" {original_name}:", f" {aliased_name}:")
    
    return updated_prompt

def generate_combination_prompt_for_toolset(
    toolset_type: str,
    toolset: AbstractToolset[Any],
    storage: Any | None,
    other_toolsets: list[AbstractToolset[Any]],
    toolset_order: list[int],
    prefix_map: dict[str, str] | None,
    workflow_template: WorkflowTemplate | None,
) -> str:
    """Generate a combination-specific prompt for a single toolset.
    
    Args:
        toolset_type: Type identifier (e.g., "search", "self_ask")
        toolset: The toolset to generate prompt for
        storage: Optional storage for dynamic prompts
        other_toolsets: Other toolsets in the combination
        toolset_order: Order of toolsets (index of this toolset)
        prefix_map: Mapping of toolset IDs to prefixes
        workflow_template: Optional workflow template
    
    Returns:
        Combination-specific prompt for this toolset
    """
    # Get the combination prompt generator
    if toolset_type in TOOLSET_COMBINATION_PROMPT_GENERATORS:
        generator = TOOLSET_COMBINATION_PROMPT_GENERATORS[toolset_type]
        return generator(
            toolset=toolset,
            storage=storage,
            other_toolsets=other_toolsets,
            position=toolset_order,
            prefix_map=prefix_map,
            workflow_template=workflow_template,
        )
    else:
        # Fallback to standalone prompt if no combination generator exists
        getter = TOOLSET_SYSTEM_PROMPT_GETTERS.get(toolset_type)
        if getter:
            prompt = getter(storage)
            # Update tool names if prefixing was applied
            if prefix_map and toolset.id in prefix_map:
                prefix = prefix_map[toolset.id]
                tool_name_mapping = build_tool_name_mapping(prompt, prefix)
                prompt = update_prompt_tool_names(prompt, tool_name_mapping)
            return prompt
        return ""

def combine_system_prompts(
    toolsets: list[AbstractToolset[Any]],
    storages: dict[str, Any] | None = None,
    prefix_map: dict[str, str] | None = None,
    workflow_template: WorkflowTemplate | None = None,
    use_combination_prompts: bool = True,
) -> str:
    """Combine system prompts from multiple toolsets.
    
    Args:
        toolsets: List of toolsets to combine prompts from
        storages: Optional mapping of toolset IDs to storage objects
                 (needed for dynamic prompts that read state)
        prefix_map: Optional mapping of toolset IDs to prefixes
                   (used to update tool names in prompts)
        workflow_template: Optional workflow template for context
        use_combination_prompts: If True, use combination-specific prompts
    
    Returns:
        Combined system prompt with all toolset instructions
    """
    if storages is None:
        storages = {}
    
    prompt_sections = []
    
    for idx, toolset in enumerate(toolsets):
        toolset_id = toolset.id or ""
        toolset_type = identify_toolset_type(toolset)
        storage = storages.get(toolset_id)
        
        if use_combination_prompts and len(toolsets) > 1:
            # Generate combination-specific prompt
            prompt = generate_combination_prompt_for_toolset(
                toolset_type=toolset_type,
                toolset=toolset,
                storage=storage,
                other_toolsets=[t for i, t in enumerate(toolsets) if i != idx],
                toolset_order=idx,
                prefix_map=prefix_map,
                workflow_template=workflow_template,
            )
        else:
            # Use standalone prompt
            if toolset_type in TOOLSET_SYSTEM_PROMPT_GETTERS:
                getter = TOOLSET_SYSTEM_PROMPT_GETTERS[toolset_type]
                prompt = getter(storage)
                
                # Update tool names if prefixing was applied
                if prefix_map and toolset_id in prefix_map:
                    prefix = prefix_map[toolset_id]
                    tool_name_mapping = build_tool_name_mapping(prompt, prefix)
                    prompt = update_prompt_tool_names(prompt, tool_name_mapping)
            else:
                prompt = ""
        
        if prompt:
            prompt_sections.append(prompt)
    
    # Combine prompts with separators
    combined = "\n\n".join(prompt_sections)
    
    # Add workflow-specific instructions if provided
    if workflow_template:
        workflow_instructions = generate_workflow_instructions(workflow_template, prefix_map)
        combined = f"{workflow_instructions}\n\n{combined}"
    
    return combined

def identify_toolset_type(toolset: AbstractToolset[Any]) -> str:
    """Identify toolset type from its ID or label.
    
    Returns toolset type string (e.g., "cot", "tot", "self_ask")
    """
    toolset_id = (toolset.id or "").lower()
    toolset_label = toolset.label.lower()
    
    # Check for known patterns
    if "cot" in toolset_id or "chain" in toolset_label:
        return "cot"
    elif "tot" in toolset_id or "tree" in toolset_label:
        return "tot"
    elif "got" in toolset_id or "graph" in toolset_label:
        return "got"
    elif "mcts" in toolset_id or "monte" in toolset_label:
        return "mcts"
    elif "beam" in toolset_id or toolset_label:
        return "beam"
    elif "reflection" in toolset_id or toolset_label:
        return "reflection"
    elif "self_refine" in toolset_id or "self-refine" in toolset_label:
        return "self_refine"
    elif "self_ask" in toolset_id or "self-ask" in toolset_label:
        return "self_ask"
    elif "persona" in toolset_id or toolset_label:
        if "debate" in toolset_id or toolset_label:
            return "persona_debate"
        return "persona"
    elif "search" in toolset_id or toolset_label:
        return "search"
    elif "todo" in toolset_id or toolset_label:
        return "todo"
    
    return "unknown"

def build_tool_name_mapping(prompt: str, prefix: str) -> dict[str, str]:
    """Build mapping of original tool names to prefixed names from prompt.
    
    Extracts tool names mentioned in backticks and creates mapping.
    """
    import re
    tool_names = re.findall(r'`([a-z_]+)`', prompt)
    return {name: f"{prefix}{name}" for name in tool_names}

# Example combination prompt generators (one per toolset type)

def generate_search_combination_prompt(
    toolset: AbstractToolset[Any],
    storage: Any | None,
    other_toolsets: list[AbstractToolset[Any]],
    position: int,
    prefix_map: dict[str, str] | None,
    workflow_template: WorkflowTemplate | None,
) -> str:
    """Generate combination-specific prompt for Search toolset.
    
    When Search is first in workflow (Research Assistant):
    - Emphasize gathering information for downstream toolsets
    - Explain that results will be used by self-ask for decomposition
    """
    prefix = prefix_map.get(toolset.id or "search", "search_") if prefix_map else ""
    
    # Get other toolset types
    other_types = [identify_toolset_type(t) for t in other_toolsets]
    
    prompt = f"""## Web Search (Stage {position + 1} of {len(other_toolsets) + 1})

You have access to tools for searching the web and extracting content:
- `{prefix}search_web`: Search the web for information using Firecrawl
- `{prefix}extract_web_content`: Extract main content from webpages using Trafilatura

### Your Role in This Workflow

You are the **information gathering** stage. Your search results will be used by other toolsets in this workflow:
"""
    
    if "self_ask" in other_types:
        prompt += "- Search results will be used to formulate questions for decomposition\n"
    if "self_refine" in other_types or "reflection" in other_types:
        prompt += "- Search results will inform the refinement process\n"
    if "todo" in other_types:
        prompt += "- Search results may be tracked as completed research tasks\n"
    
    prompt += f"""
### When to Use Web Search

Use these tools when:
1. You need current information from the web
2. Researching topics requiring up-to-date data
3. Gathering information that will feed into subsequent reasoning stages
4. Finding authoritative sources for the problem at hand

### Workflow Integration

1. **Search**: Use `{prefix}search_web` with specific queries
2. **Extract**: Use `{prefix}extract_web_content` for relevant URLs
3. **Transition**: After gathering sufficient information, proceed to the next stage
   - If self-ask is available: Use search results to formulate main questions
   - If self-refine/reflection is available: Use search results as context for refinement
"""
    
    return prompt

def generate_self_ask_combination_prompt(
    toolset: AbstractToolset[Any],
    storage: Any | None,
    other_toolsets: list[AbstractToolset[Any]],
    position: int,
    prefix_map: dict[str, str] | None,
    workflow_template: WorkflowTemplate | None,
) -> str:
    """Generate combination-specific prompt for Self-Ask toolset.
    
    When Self-Ask is in middle of workflow:
    - Explain how to use outputs from previous toolsets (e.g., search results)
    - Explain how outputs feed into next toolsets (e.g., self-refine)
    """
    prefix = prefix_map.get(toolset.id or "self_ask", "self_ask_") if prefix_map else ""
    
    other_types = [identify_toolset_type(t) for t in other_toolsets]
    prev_types = [identify_toolset_type(t) for i, t in enumerate(other_toolsets) if i < position]
    next_types = [identify_toolset_type(t) for i, t in enumerate(other_toolsets) if i > position]
    
    prompt = f"""## Self-Ask Question Decomposition (Stage {position + 1} of {len(other_toolsets) + 1})

You have access to tools for decomposing complex questions:
- `{prefix}read_self_ask_state`: Read current self-ask state
- `{prefix}ask_main_question`: Initialize main question (depth 0)
- `{prefix}ask_sub_question`: Generate sub-question from parent question
- `{prefix}answer_question`: Answer a question/sub-question
- `{prefix}compose_final_answer`: Compose final answer from sub-question answers
- `{prefix}get_final_answer`: Retrieve the final composed answer

### Your Role in This Workflow

You are the **question decomposition** stage. """
    
    if "search" in prev_types:
        prompt += "Use search results from the previous stage to formulate your main question.\n"
    if "self_refine" in next_types or "reflection" in next_types:
        prompt += "Your final answer will be refined by the next stage.\n"
    
    prompt += f"""
### Integration with Other Stages

**Input from Previous Stages:**
"""
    if "search" in prev_types:
        prompt += "- Use search results to inform your main question\n"
        prompt += "- Reference extracted content when answering sub-questions\n"
    
    prompt += f"""
**Output to Next Stages:**
"""
    if "self_refine" in next_types or "reflection" in next_types:
        prompt += "- Your final answer will be refined/improved by the next stage\n"
        prompt += "- Focus on completeness rather than perfection (refinement comes next)\n"
    if "todo" in next_types:
        prompt += "- Your final answer may be tracked as a completed task\n"
    
    prompt += f"""
### Self-Ask Process

1. **Main Question**: Initialize using `{prefix}ask_main_question`
   - Base it on information from previous stages if available
2. **Decompose**: Generate sub-questions using `{prefix}ask_sub_question`
3. **Answer**: Answer sub-questions using `{prefix}answer_question`
4. **Compose**: Synthesize final answer using `{prefix}compose_final_answer`
5. **Transition**: After composing final answer, proceed to next stage
"""
    
    return prompt

# Similar generators needed for: self_refine, todo, reflection, tot, got, mcts, beam, persona, persona_debate, cot
```

**Usage in Combination Helpers**:

```python
def create_combined_toolset(
    toolsets: list[AbstractToolset[Any]],
    storages: dict[str, Any] | None = None,
    prefix_map: dict[str, str] | None = None,
    ...
) -> tuple[CombinedToolset[Any], str]:
    """Combine toolsets and return combined toolset + combined system prompt.
    
    Returns:
        Tuple of (combined_toolset, combined_system_prompt)
    """
    # ... existing toolset combination logic ...
    
    # Combine system prompts
    combined_prompt = combine_system_prompts(
        toolsets=toolsets,
        storages=storages,
        prefix_map=prefix_map,
    )
    
    return combined_toolset, combined_prompt
```

**Integration with Agent Creation**:

When creating an agent with combined toolsets:

```python
combined_toolset, combined_prompt = create_combined_toolset(
    toolsets=[search_toolset, self_ask_toolset, self_refine_toolset],
    storages={"search": search_storage, "self_ask": self_ask_storage, ...},
    prefix_map={"search": "search_", "self_ask": "self_ask_", ...},
)

agent = Agent(
    model,
    system_prompt=combined_prompt,  # Use combined prompt
    toolsets=[combined_toolset]
)
```

#### 3.3 Helper Functions

**File**: `pydantic_ai_toolsets/toolsets/_shared/aliasing.py`

Helper functions using official API:

```python
def get_prefix_for_toolset(
    toolset: AbstractToolset[Any],
    prefix_map: dict[str, str] | None = None
) -> str:
    """Get prefix for a toolset from prefix_map or infer from toolset id.
    
    Args:
        toolset: The toolset to get prefix for
        prefix_map: Optional mapping of toolset IDs to prefixes
    
    Returns:
        Prefix string (e.g., "cot_", "tot_")
    """
    # Check prefix_map first
    if prefix_map and toolset.id in prefix_map:
        return prefix_map[toolset.id]
    
    # Infer from toolset id or label
    # Default prefixes based on toolset type
    toolset_id = toolset.id or ""
    toolset_label = toolset.label.lower()
    
    # Map common toolset patterns to prefixes
    if "cot" in toolset_id or "chain" in toolset_label:
        return "cot_"
    elif "tot" in toolset_id or "tree" in toolset_label:
        return "tot_"
    elif "got" in toolset_id or "graph" in toolset_label:
        return "got_"
    elif "mcts" in toolset_id or "monte" in toolset_label:
        return "mcts_"
    elif "beam" in toolset_id or toolset_label:
        return "beam_"
    elif "reflection" in toolset_id or toolset_label:
        return "reflection_"
    elif "self_refine" in toolset_id or "self-refine" in toolset_label:
        return "self_refine_"
    elif "self_ask" in toolset_id or "self-ask" in toolset_label:
        return "self_ask_"
    elif "persona" in toolset_id or toolset_label:
        if "debate" in toolset_id or toolset_label:
            return "persona_debate_"
        return "persona_"
    elif "search" in toolset_id or toolset_label:
        return "search_"
    elif "todo" in toolset_id or toolset_label:
        return "todo_"
    
    # Default: use toolset id as prefix
    return f"{toolset_id}_" if toolset_id else "toolset_"
```

**Note**: The `create_combined_toolset()` function needs a `RunContext` to call `get_tools()`. In practice, this context will be provided by the agent runtime when tools are actually needed. For collision detection during combination setup, we may need to create a minimal context or defer collision detection until runtime (when CombinedToolset will raise errors for conflicts).

### Phase 4: Unified State Management

#### 4.1 Implement Unified Read Function

**File**: `pydantic_ai_toolsets/toolsets/meta_orchestrator/toolset.py` (continued)

- `read_unified_state()` implementation:
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - Iterate through all registered toolsets
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - Call their respective `read_*` functions
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - Aggregate results into structured format
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - Show cross-toolset links
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - Display workflow progress

- Format:
  ```
  Unified State:
  ==============
  
  Active Toolsets: [list]
  
  [Toolset 1 State]
  [Toolset 2 State]
  ...
  
  Cross-Toolset Links:
 - [source] → [target] (type)
  
  Workflow Progress: [current stage]
  ```


### Phase 5: Workflow Template Implementation

#### 5.1 Research Assistant Template

**File**: `pydantic_ai_toolsets/toolsets/meta_orchestrator/workflow_templates.py`

```python
RESEARCH_ASSISTANT = WorkflowTemplate(
    name="research_assistant",
    toolsets=["search", "self_ask", "self_refine", "todo"],
    stages=[
        Stage("research", "search", transition_condition="has_search_results"),
        Stage("decompose", "self_ask", transition_condition="has_final_answer"),
        Stage("refine", "self_refine", transition_condition="has_best_output"),
        Stage("track", "todo", transition_condition="always"),
    ],
    handoff_instructions={
        "search→self_ask": "Use search results to formulate main question",
        "self_ask→self_refine": "Use final answer as initial output for refinement",
        "self_refine→todo": "Track refined output as completed task",
    }
)
```

#### 5.2 Other Templates

Implement similar structures for:

- Creative Problem Solver
- Strategic Decision Maker  
- Code Architect

### Phase 6: Integration Points

#### 6.1 Update Existing Toolsets

Add optional integration hooks to existing toolsets:

- Add `get_state_summary()` method to each storage class
- Add `get_outputs_for_linking()` method to return linkable items
- Update toolset creation to register with orchestrator if available

#### 6.2 Create Combination Helper Functions

**File**: `pydantic_ai_toolsets/toolsets/meta_orchestrator/helpers.py`

- `create_combined_toolset(toolsets, workflow_template=None)` - creates combined toolset
- `register_toolsets_with_orchestrator(toolsets, orchestrator)` - auto-registration
- `create_workflow_agent(template_name, model)` - convenience function

### Phase 7: README Updates

#### 7.1 Add Combination Section

**File**: `README.md`

Add new section after "Utility Toolsets":

```markdown
## Combining Toolsets

### Overview

Toolsets can be combined to create powerful multi-stage reasoning workflows. This section covers:
- How to combine multiple toolsets
- Workflow templates for common patterns
- Cross-toolset linking
- Unified state management

### Function Name Collisions

When combining toolsets, some functions may have similar names (e.g., `create_node` in Tree, Graph, and MCTS). 

**Solution: Dynamic Runtime Aliasing Using Official API**
- When toolsets are combined via `create_combined_toolset()`, prefixes are applied proactively using `prefix_map`
- Toolsets get aliased using `AbstractToolset.prefixed()` method based on prefix_map
- Function names get prefixed: `create_node` → `tot_create_node`, `got_create_node` (when prefixes provided)
- Original toolsets remain completely unchanged (zero source code modifications)
- All aliasing uses official pydantic-ai API (`prefixed()`, `CombinedToolset`) - no introspection needed
- **System Prompts**: Must be manually combined using `combine_system_prompts()` function
  - Collects prompts from all toolsets using their `get_*_system_prompt()` functions
  - Updates tool names in prompts to reflect prefixes (e.g., `read_thoughts` → `cot_read_thoughts`)
  - Combines prompts with clear separators
- You can also manually create aliased toolsets using `toolset.prefixed(prefix)` or `create_aliased_toolset(base_toolset, prefix)`

### Workflow Templates

#### Research Assistant
Search → Self-Ask → Self-Refine → Todo

Perfect for: Research tasks requiring information gathering, decomposition, and refinement

#### Creative Problem Solver  
Multi-Persona Analysis → Graph of Thoughts → Reflection

Perfect for: Complex problems needing diverse perspectives and synthesis

#### Strategic Decision Maker
Multi-Persona Debate → MCTS → Reflection

Perfect for: High-stakes decisions requiring expert debate and exploration

#### Code Architect
Self-Ask → Tree of Thoughts → Reflection → Todo

Perfect for: Software architecture requiring decomposition, exploration, and task tracking
```

#### 7.2 Add Combination Examples

Add code examples for each workflow template showing:

- How to initialize the workflow
- How toolsets transition
- How to access unified state
- How to create cross-toolset links

#### 7.3 Add Meta-Orchestrator Documentation

Document the meta-orchestrator toolset:

- When to use it
- How to register toolsets
- How to track workflows
- How to create custom workflows

### Phase 8: Update Evals for Combinations

#### 8.1 Update Combination Evals to Use Aliasing

**Files**: All combination eval files in `pydantic_ai_toolsets/evals/categories/combinations/`

- Combination evals should use aliased toolsets (with prefixes) to avoid collisions
- Individual toolset evals continue using original function names (backward compatible)
- Update combination task functions to create aliased toolsets when combining

#### 8.2 Update Compare Functions

**Files**: `compare_*.py` files in eval categories

- Individual toolset comparisons continue using original names
- Only combination evals need to handle prefixed names

### Phase 9: Combination Evals

#### 9.1 Create Combination Eval Infrastructure

**File**: `pydantic_ai_toolsets/evals/categories/combinations/`

- **`__init__.py`**: Export combination eval functions
- **`compare_combinations.py`**: Compare different workflow templates
- **`research_assistant_eval.py`**: Eval for Research Assistant workflow
- **`creative_problem_solver_eval.py`**: Eval for Creative Problem Solver workflow
- **`strategic_decision_maker_eval.py`**: Eval for Strategic Decision Maker workflow
- **`code_architect_eval.py`**: Eval for Code Architect workflow

#### 9.2 Create Combination Test Datasets

**File**: `pydantic_ai_toolsets/evals/datasets/combination_cases.py`

Create test cases for each workflow template:

**Research Assistant Cases** (5-7 cases):

1. "Research the latest developments in quantum computing and create a comprehensive summary"

                                                - Expected toolsets: search, self_ask, self_refine, todo
                                                - Expected transitions: search → self_ask → self_refine → todo
                                                - Difficulty: medium

2. "Find information about renewable energy trends and break down the key factors affecting solar adoption"

                                                - Expected toolsets: search, self_ask, self_refine
                                                - Difficulty: medium

3. "Research the pros and cons of remote work and synthesize findings into actionable recommendations"

                                                - Expected toolsets: search, self_ask, self_refine, todo
                                                - Difficulty: complex

4. "Investigate recent AI safety research and create a detailed analysis"

                                                - Expected toolsets: search, self_ask, self_refine
                                                - Difficulty: medium

5. "Research sustainable packaging solutions and develop a comprehensive report"

                                                - Expected toolsets: search, self_ask, self_refine, todo
                                                - Difficulty: complex

**Creative Problem Solver Cases** (5-7 cases):

1. "Design a sustainable urban transportation system"

                                                - Expected toolsets: persona, got, reflection
                                                - Expected transitions: persona → got → reflection
                                                - Difficulty: complex

2. "Create a comprehensive strategy for reducing food waste in cities"

                                                - Expected toolsets: persona, got, reflection
                                                - Difficulty: medium

3. "Design an inclusive educational platform for diverse learners"

                                                - Expected toolsets: persona, got, reflection
                                                - Difficulty: complex

4. "Develop a plan for carbon-neutral manufacturing"

                                                - Expected toolsets: persona, got, reflection
                                                - Difficulty: medium

5. "Create a mental health support system for remote workers"

                                                - Expected toolsets: persona, got, reflection
                                                - Difficulty: complex

**Strategic Decision Maker Cases** (5-7 cases):

1. "Should a company migrate from monolith to microservices?"

                                                - Expected toolsets: persona_debate, mcts, reflection
                                                - Expected transitions: persona_debate → mcts → reflection
                                                - Difficulty: complex

2. "Should we invest in building an in-house AI team or partner with external vendors?"

                                                - Expected toolsets: persona_debate, mcts, reflection
                                                - Difficulty: medium

3. "Should we prioritize user acquisition or user retention?"

                                                - Expected toolsets: persona_debate, mcts, reflection
                                                - Difficulty: medium

4. "Should we expand to international markets now or wait?"

                                                - Expected toolsets: persona_debate, mcts, reflection
                                                - Difficulty: complex

5. "Should we adopt a fully remote work model permanently?"

                                                - Expected toolsets: persona_debate, mcts, reflection
                                                - Difficulty: complex

**Code Architect Cases** (5-7 cases):

1. "Design the architecture for a distributed task queue system"

                                                - Expected toolsets: self_ask, tot, reflection, todo
                                                - Expected transitions: self_ask → tot → reflection → todo
                                                - Difficulty: complex

2. "Design a scalable real-time chat application"

                                                - Expected toolsets: self_ask, tot, reflection, todo
                                                - Difficulty: medium

3. "Create the architecture for a multi-tenant SaaS platform"

                                                - Expected toolsets: self_ask, tot, reflection, todo
                                                - Difficulty: complex

4. "Design a microservices architecture for an e-commerce platform"

                                                - Expected toolsets: self_ask, tot, reflection, todo
                                                - Difficulty: complex

5. "Plan the architecture for a data pipeline processing system"

                                                - Expected toolsets: self_ask, tot, reflection, todo
                                                - Difficulty: medium

**Test Case Structure**:

```python
@dataclass
class CombinationTestCase:
    name: str
    prompt: str
    workflow_template: str  # "research_assistant", "creative_problem_solver", etc.
    expected_toolsets: list[str]  # ["search", "self_ask", "self_refine", "todo"]
    expected_transitions: list[tuple[str, str]]  # [("search", "self_ask"), ("self_ask", "self_refine")]
    expected_prefixed_tools: list[str] | None = None  # Optional: ["search_search_web", "self_ask_ask_main_question", etc.] if aliasing is used
    min_storage_items: int = 5
    difficulty: str = "medium"  # simple, medium, complex
    expected_cross_links: int = 0  # Minimum number of cross-toolset links expected
```

Total: 20-28 test cases across 4 workflow templates

#### 9.3 Update run_evals.py

**File**: `pydantic_ai_toolsets/evals/run_evals.py`

Add new function:

- `run_combinations(config)` - Run all combination workflow evals
- Add "combinations" to category choices in argparse
- Update `run_all()` to include combinations category

#### 9.4 Create Combination Task Functions

Each combination eval file needs a task function that:

**File**: `pydantic_ai_toolsets/evals/categories/combinations/research_assistant_eval.py`

```python
def create_research_assistant_task_function(config: EvaluationConfig) -> Callable:
    """Create task function for Research Assistant workflow evaluation."""
    async def task(case: Case) -> str:
        # Create storages for all toolsets
        search_storage = SearchStorage(track_usage=True)
        self_ask_storage = SelfAskStorage(track_usage=True)
        self_refine_storage = SelfRefineStorage(track_usage=True)
        todo_storage = TodoStorage(track_usage=True)
        orchestrator_storage = MetaOrchestratorStorage()
        
        # Create toolsets (original function names preserved - backward compatible)
        search_toolset = create_search_toolset(search_storage)
        self_ask_toolset = create_self_ask_toolset(self_ask_storage)
        self_refine_toolset = create_self_refine_toolset(self_refine_storage)
        todo_toolset = create_todo_toolset(todo_storage)
        orchestrator_toolset = create_meta_orchestrator_toolset(orchestrator_storage)
        
        # Create combined toolset (automatically applies aliasing to avoid collisions)
        # Function names become: search_search_web, self_ask_ask_main_question, 
        # self_refine_generate_output, todo_read_todos, etc.
        prefix_map = {
            search_toolset.id or "search": "search_",
            self_ask_toolset.id or "self_ask": "self_ask_",
            self_refine_toolset.id or "self_refine": "self_refine_",
            todo_toolset.id or "todo": "todo_",
        }
        storages_map = {
            search_toolset.id or "search": search_storage,
            self_ask_toolset.id or "self_ask": self_ask_storage,
            self_refine_toolset.id or "self_refine": self_refine_storage,
            todo_toolset.id or "todo": todo_storage,
        }
        
        combined_toolset, combined_prompt = create_combined_toolset(
            toolsets=[search_toolset, self_ask_toolset, self_refine_toolset, todo_toolset],
            storages=storages_map,
            prefix_map=prefix_map,
            orchestrator=orchestrator_toolset,
            workflow_template=RESEARCH_ASSISTANT_TEMPLATE
        )
        
        # Create agent with combined system prompt
        agent = Agent(
            config.get_model_string(),
            system_prompt=combined_prompt,  # Combined prompt from all toolsets
            toolsets=[combined_toolset]
        )
        
        # Run agent
        result = await agent.run(case.inputs["prompt"])
        
        # Validate workflow progression
        # Check that all expected toolsets were used
        # Check transitions occurred
        # Check cross-toolset links exist
        # Check unified state is accessible
        
        return result.data
    return task
```

Similar structure for other combination evals:

- `create_creative_problem_solver_task_function()`
- `create_strategic_decision_maker_task_function()`
- `create_code_architect_task_function()`

Each task function:

- Creates combined toolset with meta-orchestrator
- Initializes workflow template
- Runs agent with combined toolsets
- Validates workflow progression (checks transitions occurred)
- Checks cross-toolset links exist
- Validates unified state is accessible
- Returns output for evaluation

### Phase 10: Testing & Examples

#### 10.1 Create Example Scripts

**File**: `examples/combinations/`

- `research_assistant_example.py`
- `creative_problem_solver_example.py`
- `strategic_decision_maker_example.py`
- `code_architect_example.py`

Each example demonstrates:

- Workflow initialization
- Toolset transitions
- Cross-toolset linking
- Unified state reading

#### 10.2 Update Package Exports

**File**: `pydantic_ai_toolsets/__init__.py`

Add exports for:

- Meta-orchestrator components
- Workflow templates
- Combination helpers
- Link manager

## File Structure

```
pydantic_ai_toolsets/
├── toolsets/
│   ├── meta_orchestrator/
│   │   ├── __init__.py
│   │   ├── types.py          # Workflow types
│   │   ├── storage.py         # Orchestrator storage
│   │   ├── toolset.py         # Main orchestrator toolset
│   │   ├── workflow_templates.py  # Predefined workflows
│   │   └── helpers.py         # Combination helpers
│   └── _shared/
│       ├── linking.py          # Cross-toolset linking
│       ├── aliasing.py         # Toolset aliasing/namespacing
│       └── system_prompts.py   # System prompt combination utilities (standalone + combination prompts)
├── evals/
│   ├── categories/
│   │   └── combinations/
│   │       ├── __init__.py
│   │       ├── compare_combinations.py
│   │       ├── research_assistant_eval.py
│   │       ├── creative_problem_solver_eval.py
│   │       ├── strategic_decision_maker_eval.py
│   │       └── code_architect_eval.py
│   └── datasets/
│       └── combination_cases.py
├── examples/
│   └── combinations/
│       ├── research_assistant_example.py
│       ├── creative_problem_solver_example.py
│       ├── strategic_decision_maker_example.py
│       └── code_architect_example.py
└── README.md                   # Updated with combination docs
```

## Implementation Order

1. **Week 1**: Core infrastructure (meta-orchestrator, linking, aliasing system)
2. **Week 2**: Workflow templates and unified state
3. **Week 3**: Combination helpers and integration
4. **Week 4**: Combination evals and test datasets
5. **Week 5**: Documentation and examples
6. **Week 6**: Testing and refinement

## Key Design Decisions

1. **Zero Breaking Changes**: 
   - All aliasing happens at runtime using official pydantic-ai API (`prefixed()`, `CombinedToolset`)
   - Original toolsets remain completely unchanged (no source code modifications)
   - Function names in original toolsets stay the same
   - **System Prompts**: Must be manually combined using `combine_system_prompts()` helper function
     - Each toolset's system prompt is collected via its `get_*_system_prompt()` function
     - Tool names in prompts are updated to reflect prefixes when aliasing is applied
     - Prompts are combined with clear section separators
   - Existing evals continue to work without any changes
   - No updates needed to toolset creation functions
   - No updates needed to tool descriptions or prompts (except for prefix updates in combined prompts)
   - No introspection needed - uses official API methods

2. **Minimal Aliasing Strategy**: 
   - Only alias toolsets when name collisions are detected
   - Tools without collisions keep original names
   - Reduces cognitive load and maintains clarity

3. **Modularity**: Each component can be used independently

4. **Extensibility**: Easy to add new workflow templates

5. **Performance**: Lazy loading of toolset states in unified read

6. **Type Safety**: Full type hints for all new components

7. **Eval Coverage**: Comprehensive evals for both individual toolsets and combinations