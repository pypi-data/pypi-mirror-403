---
name: 04_unified_state_management
overview: Implement unified state management to provide a single view of state across all active toolsets
todos:
  - id: implement-unified-read
    content: Implement read_unified_state() in meta_orchestrator/toolset.py to aggregate state from all registered toolsets
    status: pending
---

# Unified State Management

This plan covers Phase 4: Unified State Management.

## Files to Update

### Meta-Orchestrator Toolset

**File**: `pydantic_ai_toolsets/toolsets/meta_orchestrator/toolset.py` (continued)

Implement `read_unified_state()`:

- Iterate through all registered toolsets
- Call their respective `read_*` functions
- Aggregate results into structured format
- Show cross-toolset links
- Display workflow progress

Format:

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

## Dependencies

- Requires `01_core_infrastructure.md` (meta-orchestrator)
- Requires `03_cross_toolset_linking.md` (links)
- Requires access to all toolset `read_*` functions

## Related Plans

- See `01_core_infrastructure.md` for meta-orchestrator structure
- See `03_cross_toolset_linking.md` for link infrastructure