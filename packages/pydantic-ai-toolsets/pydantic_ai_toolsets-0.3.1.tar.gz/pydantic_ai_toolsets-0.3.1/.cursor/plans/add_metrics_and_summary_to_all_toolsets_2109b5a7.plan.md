---
name: Add Metrics and Summary to All Toolsets
overview: Add usage metrics tracking to all toolsets (especially multi_persona_analysis) and implement a summary() method on all storage classes that returns JSON of all workings of a run.
todos:
  - id: add-metrics-multi-persona-analysis
    content: Add metrics tracking to multi_persona_analysis toolset (toolset.py and storage.py)
    status: pending
  - id: add-summary-cot
    content: Add summary() method to CoTStorage and CoTStorageProtocol
    status: pending
  - id: add-summary-tot
    content: Add summary() method to ToTStorage and ToTStorageProtocol
    status: pending
  - id: add-summary-beam
    content: Add summary() method to BeamStorage and BeamStorageProtocol
    status: pending
  - id: add-summary-got
    content: Add summary() method to GoTStorage and GoTStorageProtocol
    status: pending
  - id: add-summary-mcts
    content: Add summary() method to MCTSStorage and MCTSStorageProtocol
    status: pending
  - id: add-summary-reflection
    content: Add summary() method to ReflectionStorage and ReflectionStorageProtocol
    status: pending
  - id: add-summary-self-ask
    content: Add summary() method to SelfAskStorage and SelfAskStorageProtocol
    status: pending
  - id: add-summary-self-refine
    content: Add summary() method to SelfRefineStorage and SelfRefineStorageProtocol
    status: pending
  - id: add-summary-todo
    content: Add summary() method to TodoStorage and TodoStorageProtocol
    status: pending
  - id: add-summary-search
    content: Add summary() method to SearchStorage and SearchStorageProtocol
    status: pending
  - id: add-summary-persona-debate
    content: Add summary() method to PersonaDebateStorage and PersonaDebateStorageProtocol
    status: pending
  - id: add-summary-persona-analysis
    content: Add summary() method to PersonaStorage and PersonaStorageProtocol
    status: pending
---

# Add Metrics and Summary to All Toolsets

## Current State Analysis

### Toolsets with Metrics Tracking (12/13):

- ✅ chain_of_thought_reasoning
- ✅ tree_of_thought_reasoning  
- ✅ beam_search_reasoning
- ✅ graph_of_thought_reasoning
- ✅ monte_carlo_reasoning
- ✅ reflection
- ✅ self_ask
- ✅ self_refine
- ✅ to_do
- ✅ search
- ✅ multi_persona_debate
- ❌ **multi_persona_analysis** - Missing metrics tracking

### Storage Classes Status:

- All 12 storage classes have `get_statistics()` method
- All 12 storage classes support `track_usage=True` parameter
- **None** have a `summary()` method that returns JSON

## Implementation Plan

### Phase 1: Add Metrics Tracking to multi_persona_analysis

**File**: `pydantic_ai_toolsets/toolsets/multi_persona_analysis/toolset.py`

1. Update `create_persona_toolset()` signature to accept `track_usage: bool = False` parameter
2. Initialize `_metrics` from storage if available (similar to other toolsets)
3. Add metrics tracking to all tool functions:

   - `read_personas()`
   - `initiate_persona_session()`
   - `create_persona()`
   - `add_persona_response()`
   - `synthesize()`

4. Use pattern: `_metrics.record_invocation(tool_name, input_text, result, duration_ms)` after each tool execution

**File**: `pydantic_ai_toolsets/toolsets/multi_persona_analysis/storage.py`

1. Add `_metrics: UsageMetrics | None` field
2. Update `__init__()` to accept `track_usage: bool = False` and initialize metrics if enabled
3. Add `metrics` property getter
4. Update `clear()` to reset metrics if present

### Phase 2: Add summary() Method to All Storage Classes

**Pattern**: Each storage class should have a `summary()` method that returns a JSON-serializable dict containing:

- Storage-specific state (todos, thoughts, nodes, etc.)
- Statistics from `get_statistics()`
- Usage metrics (if enabled) from `metrics.to_dict()`
- Toolset-specific metadata

**Files to Update** (12 storage classes):

1. **chain_of_thought_reasoning/storage.py** - `CoTStorage.summary()`

   - Include: thoughts list, statistics, metrics

2. **tree_of_thought_reasoning/storage.py** - `ToTStorage.summary()`

   - Include: nodes dict, evaluations dict, statistics, metrics

3. **beam_search_reasoning/storage.py** - `BeamStorage.summary()`

   - Include: candidates dict, steps list, statistics, metrics

4. **graph_of_thought_reasoning/storage.py** - `GoTStorage.summary()`

   - Include: nodes dict, edges dict, evaluations dict, statistics, metrics

5. **monte_carlo_reasoning/storage.py** - `MCTSStorage.summary()`

   - Include: nodes dict, iteration_count, statistics, metrics

6. **reflection/storage.py** - `ReflectionStorage.summary()`

   - Include: outputs dict, critiques dict, statistics, metrics

7. **self_ask/storage.py** - `SelfAskStorage.summary()`

   - Include: questions dict, answers dict, final_answers dict, statistics, metrics

8. **self_refine/storage.py** - `SelfRefineStorage.summary()`

   - Include: outputs dict, feedbacks dict, statistics, metrics

9. **to_do/storage.py** - `TodoStorage.summary()`

   - Include: todos list, statistics, metrics

10. **search/storage.py** - `SearchStorage.summary()`

    - Include: search_results dict, extracted_contents dict, statistics, metrics

11. **multi_persona_debate/storage.py** - `PersonaDebateStorage.summary()`

    - Include: session, personas dict, positions dict, critiques dict, agreements dict, statistics, metrics

12. **multi_persona_analysis/storage.py** - `PersonaStorage.summary()`

    - Include: session, personas dict, responses dict, statistics, metrics

**Implementation Pattern**:

```python
def summary(self) -> dict[str, Any]:
    """Get comprehensive JSON summary of storage state and metrics.
    
    Returns:
        Dictionary containing storage state, statistics, and usage metrics.
    """
    summary_dict: dict[str, Any] = {
        "toolset": "toolset_name",
        "statistics": self.get_statistics(),
    }
    
    # Add storage-specific data
    summary_dict["storage"] = {
        # toolset-specific fields
    }
    
    # Add metrics if available
    if self._metrics:
        summary_dict["usage_metrics"] = self._metrics.to_dict()
    
    return summary_dict
```

### Phase 3: Update Storage Protocols

Add `summary()` method to all Protocol classes:

- `CoTStorageProtocol`
- `ToTStorageProtocol`
- `BeamStorageProtocol`
- `GoTStorageProtocol`
- `MCTSStorageProtocol`
- `ReflectionStorageProtocol`
- `SelfAskStorageProtocol`
- `SelfRefineStorageProtocol`
- `TodoStorageProtocol`
- `SearchStorageProtocol`
- `PersonaDebateStorageProtocol`
- `PersonaStorageProtocol`

## Testing Strategy

1. Verify metrics tracking works for multi_persona_analysis
2. Test `summary()` returns valid JSON for all storage classes
3. Verify `summary()` includes all expected fields
4. Test with and without `track_usage=True`
5. Ensure backward compatibility (existing code still works)

## Files Modified

- `pydantic_ai_toolsets/toolsets/multi_persona_analysis/toolset.py`
- `pydantic_ai_toolsets/toolsets/multi_persona_analysis/storage.py`
- All 12 storage.py files (add summary method)
- All 12 storage.py Protocol classes (add summary to protocol)