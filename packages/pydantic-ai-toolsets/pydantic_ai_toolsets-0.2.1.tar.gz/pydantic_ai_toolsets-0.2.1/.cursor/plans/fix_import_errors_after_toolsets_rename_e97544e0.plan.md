---
name: Fix Import Errors After Toolsets Rename
overview: Fix all import errors caused by renaming toolsets and moving from `poc.*` package structure to `toolsets.*` and `evals.*`. This includes fixing imports in evals files, toolsets files, and path references.
todos:
  - id: fix-evals-poc-imports
    content: Replace all 'poc.evals.*' imports with 'evals.*' across all evals files (94 occurrences in ~30 files)
    status: pending
  - id: fix-toolsets-internal-imports
    content: Replace all 'pydantic_ai_*' imports with relative imports (., .storage, .toolset, .types) in all 12 toolsets (36 files total)
    status: pending
  - id: fix-evals-toolset-imports
    content: Update eval files to import toolsets from 'toolsets.*' instead of 'pydantic_ai_*' packages (13 eval files)
    status: pending
    dependencies:
      - fix-toolsets-internal-imports
  - id: fix-path-references
    content: Fix path references in run_evals.py and run_reflection_self_ask.py that point to 'poc/toolsets'
    status: pending
  - id: verify-imports
    content: Run Python import checks to verify all imports resolve correctly
    status: pending
    dependencies:
      - fix-evals-poc-imports
      - fix-toolsets-internal-imports
      - fix-evals-toolset-imports
      - fix-path-references
---

# Fix Import Errors After Toolsets Rename

## Problem Summary

The project was copied from another project that used `poc.*` as the package prefix. After renaming toolsets folders, all imports are broken. There are three categories of import errors:

1. **`poc.evals.*` imports** - 94 occurrences across evals files that need to change to `evals.*`
2. **`pydantic_ai_*` imports in toolsets** - 116+ occurrences where toolsets import from old package names instead of relative/local imports
3. **Path references** - 2 files reference non-existent `poc/toolsets` directory
4. **External toolset imports in evals** - eval files import toolsets using old package names

## Import Mapping

### Toolsets Package Name Mapping:

- `pydantic_ai_cot` → `toolsets.chain_of_thought_reasoning`
- `pydantic_ai_reflection` → `toolsets.reflection`
- `pydantic_ai_self_ask` → `toolsets.self_ask`
- `pydantic_ai_self_refine` → `toolsets.self_refine`
- `pydantic_ai_tot` → `toolsets.tree_of_thought_reasoning`
- `pydantic_ai_todo` → `toolsets.to_do`
- `pydantic_ai_mcts` → `toolsets.monte_carlo_reasoning`
- `pydantic_ai_got` → `toolsets.graph_of_thought_reasoning`
- `pydantic_ai_beam` → `toolsets.beam_search_reasoning`
- `pydantic_ai_debate` → `toolsets.pre_configured_multi_agent_debate`
- `pydantic_ai_multi_personas` → `toolsets.multi_persona_debate`
- `pydantic_ai_persona_debate` → `toolsets.pre_configured_multi_persona_debate`
- `search` (bare import) → `toolsets.search`

## Files Requiring Changes

### Category 1: Fix `poc.evals.*` → `evals.*` (94 occurrences)

**evals/base.py** (1 occurrence)

- Line 14: `from poc.evals.config import EvaluationConfig, default_config`

**evals/config.py** - No changes needed (no imports)

**evals/pydantic_evals_wrapper.py** (2 occurrences)

- Line 11: `from poc.evals.base import AgentRunner, StorageInspector`
- Line 12: `from poc.evals.config import EvaluationConfig`
- Line 13-18: `from poc.evals.evaluators import ...`

**evals/run_evals.py** (6 occurrences)

- Line 16: Path reference `project_root / "poc" / "toolsets"` → `project_root / "toolsets"`
- Line 24: `from poc.evals.base import ResultCollector`
- Line 25: `from poc.evals.config import EvaluationConfig, default_config`
- Lines 26-36: Multiple `from poc.evals.categories.*` imports

**evals/run_reflection_self_ask.py** (3 occurrences)

- Line 13: Path reference `project_root / "poc" / "toolsets"` → `project_root / "toolsets"`
- Line 18: `from poc.evals.config import EvaluationConfig, default_config`
- Lines 19-21: `from poc.evals.categories.reflection.compare_reflection import ...`

**evals/datasets/init.py** (4 occurrences)

- Lines 3-6: All `from poc.evals.datasets.*` imports

**evals/evaluators/** (5 files, 5 occurrences)

- `efficiency.py` line 7: `from poc.evals.base import EvaluationResult`
- `output_quality.py` line 7: `from poc.evals.base import EvaluationResult`
- `storage_state.py` line 7: `from poc.evals.base import EvaluationResult`
- `tool_usage.py` line 7: `from poc.evals.base import EvaluationResult`
- `__init__.py` lines 3-6: All `from poc.evals.evaluators.*` imports

**evals/categories/** (23 files)

- All base_*.py files (3 files): `from poc.evals.base import ...`
- All *_eval.py files (10 files): `from poc.evals.base import ...` and `from poc.evals.config import ...`
- All compare_*.py files (3 files): `from poc.evals.categories.* `and `from poc.evals.config import ...`
- All datasets imports: `from poc.evals.datasets.*`

### Category 2: Fix `pydantic_ai_*` imports in toolsets (116+ occurrences)

Each toolset folder needs its internal imports changed from `pydantic_ai_*` to relative imports (`.storage`, `.toolset`, `.types`) or to `toolsets.<toolset_name>.*`.

**toolsets/chain_of_thought_reasoning/** (3 files)

- `__init__.py`: Change `from pydantic_ai_cot.*` to relative imports
- `toolset.py`: Change `from pydantic_ai_cot.*` to relative imports
- `storage.py`: Change `from pydantic_ai_cot.*` to relative imports

**toolsets/reflection/** (3 files)

- `__init__.py`: Change `from pydantic_ai_reflection.*` to relative imports
- `toolset.py`: Change `from pydantic_ai_reflection.*` to relative imports
- `storage.py`: Change `from pydantic_ai_reflection.*` to relative imports

**toolsets/self_ask/** (3 files)

- `__init__.py`: Change `from pydantic_ai_self_ask.*` to relative imports
- `toolset.py`: Change `from pydantic_ai_self_ask.*` to relative imports
- `storage.py`: Change `from pydantic_ai_self_ask.*` to relative imports

**toolsets/self_refine/** (3 files)

- `__init__.py`: Change `from pydantic_ai_self_refine.*` to relative imports
- `toolset.py`: Change `from pydantic_ai_self_refine.*` to relative imports
- `storage.py`: Change `from pydantic_ai_self_refine.*` to relative imports

**toolsets/tree_of_thought_reasoning/** (3 files)

- `__init__.py`: Change `from pydantic_ai_tot.*` to relative imports
- `toolset.py`: Change `from pydantic_ai_tot.*` to relative imports
- `storage.py`: Change `from pydantic_ai_tot.*` to relative imports

**toolsets/to_do/** (3 files)

- `__init__.py`: Change `from pydantic_ai_todo.*` to relative imports
- `toolset.py`: Change `from pydantic_ai_todo.*` to relative imports
- `storage.py`: Change `from pydantic_ai_todo.*` to relative imports

**toolsets/monte_carlo_reasoning/** (3 files)

- `__init__.py`: Change `from pydantic_ai_mcts.*` to relative imports
- `toolset.py`: Change `from pydantic_ai_mcts.*` to relative imports
- `storage.py`: Change `from pydantic_ai_mcts.*` to relative imports

**toolsets/graph_of_thought_reasoning/** (3 files)

- `__init__.py`: Change `from pydantic_ai_got.*` to relative imports
- `toolset.py`: Change `from pydantic_ai_got.*` to relative imports
- `storage.py`: Change `from pydantic_ai_got.*` to relative imports

**toolsets/beam_search_reasoning/** (3 files)

- `__init__.py`: Change `from pydantic_ai_beam.*` to relative imports
- `toolset.py`: Change `from pydantic_ai_beam.*` to relative imports
- `storage.py`: Change `from pydantic_ai_beam.*` to relative imports

**toolsets/pre_configured_multi_agent_debate/** (3 files)

- `__init__.py`: Change `from pydantic_ai_debate.*` to relative imports
- `toolset.py`: Change `from pydantic_ai_debate.*` to relative imports
- `storage.py`: Change `from pydantic_ai_debate.*` to relative imports

**toolsets/multi_persona_debate/** (3 files)

- `__init__.py`: Change `from pydantic_ai_multi_personas.*` to relative imports
- `toolset.py`: Change `from pydantic_ai_multi_personas.*` to relative imports
- `storage.py`: Change `from pydantic_ai_multi_personas.*` to relative imports

**toolsets/pre_configured_multi_persona_debate/** (3 files)

- `__init__.py`: Change `from pydantic_ai_persona_debate.*` to relative imports
- `toolset.py`: Change `from pydantic_ai_persona_debate.*` to relative imports
- `storage.py`: Change `from pydantic_ai_persona_debate.*` to relative imports

**toolsets/search/** - Already uses relative imports (`.storage`, `.toolset`, `.types`) - No changes needed

### Category 3: Fix toolset imports in evals files

**evals/categories/thinking_cognition/cot_eval.py**

- Line 13-14: `from pydantic_ai_cot import ...` → `from toolsets.chain_of_thought_reasoning import ...`

**evals/categories/thinking_cognition/beam_eval.py**

- Change `from pydantic_ai_beam import ...` → `from toolsets.beam_search_reasoning import ...`

**evals/categories/thinking_cognition/got_eval.py**

- Change `from pydantic_ai_got import ...` → `from toolsets.graph_of_thought_reasoning import ...`

**evals/categories/thinking_cognition/mcts_eval.py**

- Change `from pydantic_ai_mcts import ...` → `from toolsets.monte_carlo_reasoning import ...`

**evals/categories/thinking_cognition/tot_eval.py**

- Change `from pydantic_ai_tot import ...` → `from toolsets.tree_of_thought_reasoning import ...`

**evals/categories/reflection/reflection_eval.py**

- Change `from pydantic_ai_reflection import ...` → `from toolsets.reflection import ...`

**evals/categories/reflection/self_ask_eval.py**

- Change `from pydantic_ai_self_ask import ...` → `from toolsets.self_ask import ...`

**evals/categories/reflection/self_refine_eval.py**

- Change `from pydantic_ai_self_refine import ...` → `from toolsets.self_refine import ...`

**evals/categories/multi_agent/debate_eval.py**

- Change `from pydantic_ai_debate import ...` → `from toolsets.pre_configured_multi_agent_debate import ...`

**evals/categories/multi_agent/multi_personas_eval.py**

- Change `from pydantic_ai_multi_personas import ...` → `from toolsets.multi_persona_debate import ...`

**evals/categories/multi_agent/persona_debate_eval.py**

- Change `from pydantic_ai_persona_debate import ...` → `from toolsets.pre_configured_multi_persona_debate import ...`

**evals/categories/uniques/search_eval.py**

- Line 13-14: `from search import ...` → `from toolsets.search import ...`

**evals/categories/uniques/todo_eval.py**

- Change `from pydantic_ai_todo import ...` → `from toolsets.to_do import ...`

## Implementation Strategy

1. **Phase 1: Fix evals imports** - Replace all `poc.evals.*` with `evals.*`
2. **Phase 2: Fix toolsets internal imports** - Replace `pydantic_ai_*` with relative imports in each toolset
3. **Phase 3: Fix evals toolset imports** - Update eval files to import from `toolsets.*`
4. **Phase 4: Fix path references** - Update `run_evals.py` and `run_reflection_self_ask.py`
5. **Phase 5: Verify** - Run import checks to ensure no broken imports remain

## Notes

- The `search` toolset already uses relative imports correctly - use it as a reference pattern
- Some toolsets have example code in docstrings that reference old package names - these should be updated too
- After fixing imports, the package structure should allow imports like `from toolsets.chain_of_thought_reasoning import create_cot_toolset`