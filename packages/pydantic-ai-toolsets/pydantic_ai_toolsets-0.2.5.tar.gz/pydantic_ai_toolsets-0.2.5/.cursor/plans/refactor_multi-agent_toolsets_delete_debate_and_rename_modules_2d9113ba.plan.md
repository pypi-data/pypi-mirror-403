---
name: "Refactor Multi-Agent Toolsets: Delete Debate and Rename Modules"
overview: Delete pre_configured_multi_agent_debate toolset and its eval, rename pre_configured_multi_persona_debate to multi_persona_debate, rename multi_persona_debate to multi_persona_analysis, and update all imports and README.
todos:
  - id: rename-multi-persona-debate-to-analysis
    content: "Rename directory: multi_persona_debate → multi_persona_analysis"
    status: completed
  - id: rename-pre-configured-to-multi-persona-debate
    content: "Rename directory: pre_configured_multi_persona_debate → multi_persona_debate"
    status: completed
  - id: update-init-imports
    content: "Update imports in pydantic_ai_toolsets/__init__.py: remove debate imports, update persona import paths"
    status: completed
  - id: update-init-exports
    content: Remove all debate-related exports from __init__.py __all__ list
    status: completed
  - id: update-compare-multi-agent
    content: Remove debate_eval import and entry from compare_multi_agent.py
    status: completed
  - id: update-persona-debate-eval
    content: Update import path in persona_debate_eval.py to use multi_persona_debate
    status: completed
  - id: update-multi-personas-eval
    content: Update import path in multi_personas_eval.py to use multi_persona_analysis
    status: completed
  - id: delete-debate-toolset
    content: Delete entire pre_configured_multi_agent_debate directory
    status: completed
  - id: delete-debate-eval
    content: Delete debate_eval.py file
    status: completed
  - id: update-readme-sections
    content: "Update README.md: remove Pre-configured Multi-Agent Debate section, update section names"
    status: completed
  - id: update-readme-comparison-table
    content: "Update README.md comparison table: remove debate column, update references"
    status: completed
---

# Refactor Multi-Agent Toolsets: Delete Debate and Rename Modules

## Overview

This plan covers:

1. Deleting `pre_configured_multi_agent_debate` toolset and its evaluation
2. Renaming `pre_configured_multi_persona_debate` → `multi_persona_debate`
3. Renaming `multi_persona_debate` → `multi_persona_analysis`
4. Updating all imports and references
5. Updating README.md

## Phase 1: Delete pre_configured_multi_agent_debate

### Files to Delete

- `pydantic_ai_toolsets/toolsets/pre_configured_multi_agent_debate/` (entire directory)
- `__init__.py`
- `toolset.py`
- `storage.py`
- `types.py`
- `py.typed`
- `pydantic_ai_toolsets/evals/categories/multi_agent/debate_eval.py`

### Import Updates Required

- `pydantic_ai_toolsets/__init__.py`: Remove import and all exports related to debate toolset
- `pydantic_ai_toolsets/evals/categories/multi_agent/compare_multi_agent.py`: Remove `debate_eval` import and `("debate", evaluate_debate_toolset)` entry

## Phase 2: Rename pre_configured_multi_persona_debate → multi_persona_debate

### Directory Rename

- `pydantic_ai_toolsets/toolsets/pre_configured_multi_persona_debate/` → `pydantic_ai_toolsets/toolsets/multi_persona_debate/`

### Import Path Updates

- `pydantic_ai_toolsets/__init__.py`: Change import from `pre_configured_multi_persona_debate` to `multi_persona_debate`
- `pydantic_ai_toolsets/evals/categories/multi_agent/persona_debate_eval.py`: Update import path

## Phase 3: Rename multi_persona_debate → multi_persona_analysis

### Directory Rename

- `pydantic_ai_toolsets/toolsets/multi_persona_debate/` → `pydantic_ai_toolsets/toolsets/multi_persona_analysis/`

### Import Path Updates

- `pydantic_ai_toolsets/__init__.py`: Change import from `multi_persona_debate` to `multi_persona_analysis`
- `pydantic_ai_toolsets/evals/categories/multi_agent/multi_personas_eval.py`: Update import path

## Phase 4: Update **init**.py Exports

### Remove Debate-Related Exports

Remove all exports related to `pre_configured_multi_agent_debate`:

- `create_debate_toolset`
- `get_debate_system_prompt`
- `DebateStorage`, `DebateStorageProtocol`
- `DebateSession`, `Position`, `Critique`
- All debate-related item types and descriptions
- All `DEBATE_*` constants

### Update Export Names (if needed)

- Keep `create_persona_debate_toolset` (now from `multi_persona_debate`)
- Keep `create_persona_toolset` (now from `multi_persona_analysis`)

## Phase 5: Update Evaluation Files

### compare_multi_agent.py

- Remove: `from pydantic_ai_toolsets.evals.categories.multi_agent.debate_eval import evaluate_debate_toolset`
- Remove: `("debate", evaluate_debate_toolset)` from evaluation_functions list
- Update remaining entries to reflect new names

### persona_debate_eval.py

- Change import from `pre_configured_multi_persona_debate` to `multi_persona_debate`

### multi_personas_eval.py

- Change import from `multi_persona_debate` to `multi_persona_analysis`
- Update error message if it references old name

## Phase 6: Update README.md

### Remove Sections

- Remove "Pre-configured Multi-Agent Debate" section entirely
- Remove it from comparison table

### Update Section Names

- "Pre-configured Multi-Persona Debate" → "Multi-Persona Debate"
- "Multi-Persona Analysis" section (already exists, verify it's correct)

### Update Comparison Table

- Remove `pre_configured_multi_agent_debate` column
- Update `pre_configured_multi_persona_debate` references to `multi_persona_debate`
- Ensure `multi_persona_analysis` is correctly described

### Update Code Examples

- Update any code examples that reference old import paths
- Ensure examples use `create_persona_debate_toolset` and `create_persona_toolset` correctly

## Execution Order

1. **First**: Rename directories (to avoid conflicts)

- `multi_persona_debate` → `multi_persona_analysis` (temporary: `multi_persona_analysis_temp`)
- `pre_configured_multi_persona_debate` → `multi_persona_debate`
- `multi_persona_analysis_temp` → `multi_persona_analysis`

2. **Second**: Update all import statements in code files

3. **Third**: Delete `pre_configured_multi_agent_debate` directory and `debate_eval.py`

4. **Fourth**: Update `__init__.py` exports

5. **Fifth**: Update README.md

6. **Finally**: Verify no broken imports remain

## Files to Modify

### Code Files

- `pydantic_ai_toolsets/__init__.py` - Remove debate imports/exports, update persona import paths
- `pydantic_ai_toolsets/evals/categories/multi_agent/compare_multi_agent.py` - Remove debate evaluation
- `pydantic_ai_toolsets/evals/categories/multi_agent/persona_debate_eval.py` - Update import path
- `pydantic_ai_toolsets/evals/categories/multi_agent/multi_personas_eval.py` - Update import path

### Documentation

- `README.md` - Update toolset descriptions and comparison tables

## Verification Steps

1. Check that all imports resolve correctly
2. Verify no references to `pre_configured_multi_agent_debate` remain
3. Verify no references to old `multi_persona_debate` path remain (should now point to analysis)
4. Verify `multi_persona_debate` now points to former `pre_configured_multi_persona_debate`
5. Run any existing tests to ensure nothing breaks
6. Check that README examples use correct import paths