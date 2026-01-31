---
name: Remove Unused Code from Evals Module
overview: Remove all unused code from the evals module, including pydantic_evals_wrapper.py, unused base evaluator classes, and ResultCollector import.
todos:
  - id: verify-evaluator-usage
    content: Verify if evaluator modules are used outside of base classes
    status: pending
  - id: delete-pydantic-evals-wrapper
    content: Delete pydantic_evals_wrapper.py
    status: pending
  - id: delete-base-evaluators
    content: Delete all base evaluator class files (base_multi_agent, base_reflection, base_thinking, base_self_ask)
    status: pending
  - id: remove-result-collector
    content: Remove ResultCollector class from base.py
    status: pending
  - id: remove-result-collector-import
    content: Remove ResultCollector import from run_evals.py
    status: pending
  - id: clean-init-files
    content: Clean up __init__.py files to remove deleted module exports
    status: pending
  - id: delete-evaluators-if-unused
    content: Delete evaluators/ directory if not used elsewhere
    status: pending
---

# Remove Unused Code from Evals Module

## Unused Code Identified

### 1. pydantic_evals_wrapper.py

- **Status**: Not imported or used anywhere
- **Location**: `pydantic_ai_toolsets/evals/pydantic_evals_wrapper.py`
- **Contains**: `ToolsetTaskWrapper`, `create_custom_evaluators()`, `create_dataset_from_cases()`
- **Reason**: Current implementation uses pydantic-evals Dataset API directly in individual eval files

### 2. ResultCollector from base.py

- **Status**: Imported in `run_evals.py` but never used
- **Location**: `pydantic_ai_toolsets/evals/base.py` (lines 369-431)
- **Reason**: Current implementation uses pydantic-evals `EvaluationReport` objects instead

### 3. Base Evaluator Classes (Legacy)

- **Status**: Not imported or used anywhere
- **Files**:
- `pydantic_ai_toolsets/evals/categories/multi_agent/base_multi_agent.py`
- `pydantic_ai_toolsets/evals/categories/reflection/base_reflection.py`
- `pydantic_ai_toolsets/evals/categories/thinking_cognition/base_thinking.py`
- `pydantic_ai_toolsets/evals/categories/reflection/base_self_ask.py`
- **Reason**: Legacy code from older evaluation approach using `ToolsetEvaluator` base class. Current implementation uses pydantic-evals Dataset API directly.

### 4. Evaluator Modules (Potentially Unused)

- **Status**: Only used by unused base evaluator classes
- **Location**: `pydantic_ai_toolsets/evals/evaluators/`
- **Files**:
- `output_quality.py`
- `tool_usage.py`
- `storage_state.py`
- `efficiency.py`
- **Action**: Verify if used elsewhere before removal

## Removal Plan

### Phase 1: Remove Unused Files

1. **Delete** `pydantic_ai_toolsets/evals/pydantic_evals_wrapper.py`

- Complete file removal

2. **Delete** base evaluator classes:

- `pydantic_ai_toolsets/evals/categories/multi_agent/base_multi_agent.py`
- `pydantic_ai_toolsets/evals/categories/reflection/base_reflection.py`
- `pydantic_ai_toolsets/evals/categories/thinking_cognition/base_thinking.py`
- `pydantic_ai_toolsets/evals/categories/reflection/base_self_ask.py`

### Phase 2: Clean Up base.py

**File**: `pydantic_ai_toolsets/evals/base.py`

1. Remove `ResultCollector` class (lines 369-431)

- Keep `AgentRunner`, `StorageInspector`, `EvaluationResult`, `AgentRunResult`, `ToolsetEvaluator` (these are used)

### Phase 3: Clean Up run_evals.py

**File**: `pydantic_ai_toolsets/evals/run_evals.py`

1. Remove unused import:

- Line 19: `from pydantic_ai_toolsets.evals.base import ResultCollector`

### Phase 4: Verify Evaluator Modules

**Files**: `pydantic_ai_toolsets/evals/evaluators/*.py`

1. Search codebase for imports/usage of:

- `OutputQualityEvaluator`
- `ToolUsageEvaluator`
- `StorageStateEvaluator`
- `EfficiencyEvaluator`

2. If only used in deleted base classes:

- Delete entire `evaluators/` directory
- Remove `evaluators/__init__.py` exports

3. If used elsewhere:

- Keep evaluator modules

### Phase 5: Update **init**.py Files

1. **evals/init.py**: Remove any exports related to deleted modules
2. **categories/multi_agent/init.py**: Remove `base_multi_agent` exports if present
3. **categories/reflection/init.py**: Remove `base_reflection`, `base_self_ask` exports if present
4. **categories/thinking_cognition/init.py**: Remove `base_thinking` exports if present

## Verification Steps

1. Run `grep` to ensure no remaining imports of deleted modules
2. Run evals to ensure everything still works: `python -m pydantic_ai_toolsets.evals.run_evals`
3. Check for any broken imports in the codebase
4. Verify all eval files still function correctly

## Files to Delete

- `pydantic_ai_toolsets/evals/pydantic_evals_wrapper.py`
- `pydantic_ai_toolsets/evals/categories/multi_agent/base_multi_agent.py`
- `pydantic_ai_toolsets/evals/categories/reflection/base_reflection.py`
- `pydantic_ai_toolsets/evals/categories/thinking_cognition/base_thinking.py`
- `pydantic_ai_toolsets/evals/categories/reflection/base_self_ask.py`
- Potentially: `pydantic_ai_toolsets/evals/evaluators/` directory (if unused)

## Files to Modify

- `pydantic_ai_toolsets/evals/base.py` - Remove ResultCollector class
- `pydantic_ai_toolsets/evals/run_evals.py` - Remove ResultCollector import
- `pydantic_ai_toolsets/evals/__init__.py` - Clean up exports
- Category `__init__.py` files - Remove base class exports