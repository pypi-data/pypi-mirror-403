---
name: 06_integration_and_helpers
overview: Create integration points and helper functions for combining toolsets and creating workflow agents
todos:
  - id: add-storage-integration-hooks
    content: Add get_state_summary() and get_outputs_for_linking() methods to all storage classes
    status: completed
  - id: combination-helpers
    content: Create meta_orchestrator/helpers.py with create_combined_toolset and register_toolsets_with_orchestrator
    status: completed
  - id: create-workflow-agent-helper
    content: Implement create_workflow_agent() convenience function
    status: completed
  - id: update-init-exports
    content: Update __init__.py to export meta-orchestrator components and workflow templates
    status: completed
---

# Integration Points and Helper Functions

This plan covers Phase 6: Integration Points.

## Files to Create/Update

### 1. Update Existing Toolsets

**Files**: All `toolset.py` files in each toolset directory

Add optional integration hooks:

- Add `get_state_summary()` method to each storage class
- Add `get_outputs_for_linking()` method to return linkable items
- Update toolset creation to register with orchestrator if available

### 2. Combination Helper Functions

**File**: `pydantic_ai_toolsets/toolsets/meta_orchestrator/helpers.py`

- `create_combined_toolset()` - creates combined toolset (see `02_aliasing_and_combination.md`)
- `register_toolsets_with_orchestrator()` - auto-registration
- `create_workflow_agent()` - convenience function to create agent with workflow template

### 3. Update Package Exports

**File**: `pydantic_ai_toolsets/__init__.py`

Add exports for:

- Meta-orchestrator components
- Workflow templates
- Combination helpers
- Link manager

## Dependencies

- Requires `01_core_infrastructure.md` (meta-orchestrator)
- Requires `02_aliasing_and_combination.md` (combination helpers)
- Requires `03_cross_toolset_linking.md` (linking)

## Related Plans

- See `01_core_infrastructure.md` for meta-orchestrator
- See `02_aliasing_and_combination.md` for combination logic