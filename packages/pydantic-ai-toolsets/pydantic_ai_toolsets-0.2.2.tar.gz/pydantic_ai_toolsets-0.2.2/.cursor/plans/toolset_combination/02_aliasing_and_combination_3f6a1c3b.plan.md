---
name: 02_aliasing_and_combination
overview: Implement dynamic toolset aliasing using official pydantic-ai API and system prompt combination for multi-toolset workflows
todos:
  - id: implement-aliased-toolset-api
    content: Implement create_aliased_toolset() using official AbstractToolset.prefixed() API method
    status: pending
  - id: implement-prefix-mapping
    content: Implement get_prefix_for_toolset() helper to map toolsets to prefixes based on id/label
    status: pending
  - id: implement-combined-toolset-api
    content: Implement create_combined_toolset() using official CombinedToolset API to combine toolsets
    status: pending
  - id: implement-system-prompt-combination
    content: Implement combine_system_prompts() to collect and combine system prompts from all toolsets
    status: pending
  - id: implement-prompt-tool-name-update
    content: Implement update_prompt_tool_names() to update tool names in prompts when aliasing is applied
    status: pending
  - id: implement-toolset-type-identification
    content: Implement identify_toolset_type() to map toolsets to their system prompt getter functions
    status: pending
  - id: implement-combination-prompt-generators
    content: Implement generate_*_combination_prompt() functions for each toolset type (12 functions total)
    status: pending
  - id: implement-workflow-instructions-generator
    content: Implement generate_workflow_instructions() to add workflow-specific guidance when workflow_template is provided
    status: pending
---

# Dynamic Toolset Aliasing and Combination

This plan covers Phase 3: Dynamic Toolset Aliasing and System Prompt Combination.

## Critical Principle

All aliasing happens at runtime using the official pydantic-ai API (`prefixed()` method and `CombinedToolset`). ZERO modifications to existing toolset source code.

## Files to Create

### 1. Aliasing System

**File**: `pydantic_ai_toolsets/toolsets/_shared/aliasing.py`

- `create_aliased_toolset()` - uses `AbstractToolset.prefixed()` API
- `get_prefix_for_toolset()` - maps toolsets to prefixes based on id/label
- Prefix mapping for all 12 toolsets

### 2. Combination Helpers

**File**: `pydantic_ai_toolsets/toolsets/meta_orchestrator/helpers.py`

- `create_combined_toolset()` - combines toolsets with automatic prefixing
- Returns `tuple[CombinedToolset[Any], str]` (toolset + combined prompt)
- Uses `prefix_map` for proactive collision prevention

### 3. System Prompt Combination

**File**: `pydantic_ai_toolsets/toolsets/_shared/system_prompts.py`

**Key Feature**: Combination-specific prompts (different from standalone prompts)

Functions:

- `combine_system_prompts()` - combines prompts from all toolsets
- `generate_combination_prompt_for_toolset()` - generates combination-specific prompt
- `update_prompt_tool_names()` - updates tool names in prompts when aliasing applied
- `identify_toolset_type()` - maps toolsets to their types
- `build_tool_name_mapping()` - extracts tool names from prompts

**Combination Prompt Generators** (12 functions, one per toolset):

- `generate_search_combination_prompt()`
- `generate_self_ask_combination_prompt()`
- `generate_self_refine_combination_prompt()`
- `generate_todo_combination_prompt()`
- `generate_reflection_combination_prompt()`
- `generate_tot_combination_prompt()`
- `generate_got_combination_prompt()`
- `generate_mcts_combination_prompt()`
- `generate_beam_combination_prompt()`
- `generate_cot_combination_prompt()`
- `generate_persona_combination_prompt()`
- `generate_persona_debate_combination_prompt()`

Each generator:

- Acknowledges other toolsets in combination
- Explains toolset's role in workflow (e.g., "Stage 1 of 4")
- Describes integration with previous/next toolsets
- Updates tool names with prefixes

## Dependencies

- Requires official pydantic-ai API (`AbstractToolset.prefixed()`, `CombinedToolset`)
- Requires access to toolset system prompt getters (`get_*_system_prompt()`)

## Related Plans

- See `01_core_infrastructure.md` for workflow templates
- See `03_cross_toolset_linking.md` for linking infrastructure