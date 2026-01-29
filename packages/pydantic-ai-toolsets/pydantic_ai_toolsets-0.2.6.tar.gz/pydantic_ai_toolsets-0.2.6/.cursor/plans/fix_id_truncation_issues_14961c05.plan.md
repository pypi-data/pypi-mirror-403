---
name: Fix ID Truncation Issues
overview: Comprehensive plan to fix all instances where IDs are truncated in display/output, ensuring agents always receive full IDs when needed for tool calls, linking, and lookups. Addresses inconsistencies across all toolsets and storage implementations.
todos: []
---

# Fix ID Truncation Issues - Comprehensive Plan

## Problem Summary

IDs are being truncated to `[:8]` for display purposes throughout the codebase, but agents need full IDs for:

- Tool calls (e.g., `refine_output(output_id="...")`)
- Cross-toolset linking (`link_toolset_outputs`)
- Storage lookups
- Error recovery

This causes failures when agents use truncated IDs they see in prompts/outputs.

## Root Causes

1. **Display Truncation**: IDs truncated to `[:8]` for readability in output messages
2. **Agent Confusion**: Agents see truncated IDs and try to use them in tool calls
3. **Inconsistent ID Formats**: Todo storage uses index-based IDs (`str(i)`) vs UUIDs elsewhere
4. **Missing Validation**: No checks that IDs passed to tools are full/valid
5. **Prompt Contamination**: Dynamic state sections include truncated IDs

## Solution Strategy

**Simple approach: Show FULL IDs everywhere - no truncation**

**Pattern to implement:**

- All displays: Show full UUIDs directly (e.g., `[{candidate_id}]` instead of `[{candidate_id[:8]}...]`)
- Error messages: Show full IDs
- System prompts: Show full IDs
- All tool outputs: Show full IDs
- Examples: Show full IDs

**Rationale:** We don't have a readability problem with full UUIDs. Showing truncated IDs causes agent confusion and tool call failures. Full IDs are clear and unambiguous.

## Detailed Fix Locations

### Category 1: Toolset Tool Functions (Critical - Tool Output Messages)

These are messages returned to agents that may contain truncated IDs.

#### 1.1 Beam Search Reasoning (`toolsets/beam_search_reasoning/toolset.py`)

**Lines to fix:**

- **Line 208**: Hint message - `[{unscored[0].candidate_id[:8]}...]` → Include full ID
- **Line 213**: Hint message - `[{best.candidate_id[:8]}...]` → Include full ID  
- **Line 241**: Display in read_beam - `[{cid[:8]}]` → Show full ID or add full ID reference
- **Line 256**: Parent reference - `←[{c.parent_id[:8]}]` → Include full ID
- **Line 257**: Candidate display - `[{c.candidate_id[:8]}]` → Include full ID
- **Line 309**: Creation message - `Created [{candidate_id[:8]}]` → Include full ID
- **Line 326**: Error message - `'{expand.candidate_id[:8]}...'` → Show full ID in error
- **Line 327**: Available list - `[{available}]` where available uses `[:8]` → Show full IDs
- **Line 362**: Expansion message - `Expanded [{expand.candidate_id[:8]}]` → Include full ID
- **Line 377**: Error message - `'{score.candidate_id[:8]}...'` → Show full ID
- **Line 378**: Available list - Same issue as 327
- **Line 383**: Scoring message - `Scored [{score.candidate_id[:8]}]` → Include full ID
- **Line 473**: Prune display - `[{cid[:8]}]` → Include full ID
- **Line 520**: System prompt state - `[{c.candidate_id[:8]}]` → Include full ID

**Fix pattern:**

```python
# Before
f"Created [{candidate_id[:8]}] at step 0"

# After - Show full ID
f"Created [{candidate_id}] at step 0"
```

#### 1.2 Tree of Thought Reasoning (`toolsets/tree_of_thought_reasoning/toolset.py`)

**Lines to fix:**

- **Line 229**: Node display - `[{node.node_id[:8]}]` → Include full ID
- **Line 294**: Available nodes - `[{n.node_id[:8]}]` → Show full IDs
- **Line 296**: Error message - `'{parent_id[:8]}...'` → Show full ID
- **Line 309**: Creation message - `Created [{node_id[:8]}]` → Include full ID
- **Line 311**: Parent reference - `under [{parent_id[:8]}]` → Include full ID
- **Line 429**: Merge message - `Merged [{node_id[:8]}]` → Include full ID

**Fix pattern:** Same as beam search

#### 1.3 Self-Ask (`toolsets/self_ask/toolset.py`)

**Lines to fix (extensive - 30+ instances):**

- **Line 308**: Hint - `[{can_ask_sub[0].question_id[:8]}...]` → Include full ID
- **Line 310**: Hint - `[{unanswered[0].question_id[:8]}...]` → Include full ID
- **Line 317**: Hint - `[{main_q.question_id[:8]}...]` → Include full ID
- **Lines 351-396**: All display in read_self_ask_state - Multiple `[:8]` truncations → Include full IDs
- **Line 407**: Main question display - `[{main_q.question_id[:8]}...]` → Include full ID
- **Line 421**: Child question display - `[{child.question_id[:8]}...]` → Include full ID
- **Line 466**: Error message - `[{main_q.question_id[:8]}...]` → Show full ID
- **Line 498**: Available list - `[{q.question_id[:8]}]` → Show full IDs
- **Line 500**: Error message - `'{item.parent_question_id[:8]}...'` → Show full ID
- **Line 509**: Error message - `[{item.parent_question_id[:8]}...]` → Show full ID
- **Line 531**: Creation message - `from parent [{item.parent_question_id[:8]}...]` → Include full ID
- **Line 547**: Available list - Same as 498
- **Line 549**: Error message - `'{item.question_id[:8]}...'` → Show full ID
- **Line 577-578**: Answer messages - Multiple `[:8]` → Include full IDs
- **Line 594**: Available list - Same pattern
- **Line 596**: Error message - `'{item.main_question_id[:8]}...'` → Show full ID
- **Line 603**: Error message - `[{item.main_question_id[:8]}...]` → Show full ID
- **Line 613**: Error message - `[{aid[:8] + '...'}]` → Show full IDs
- **Line 635**: Composition message - `[{item.main_question_id[:8]}...]` → Include full ID
- **Line 659**: Final answer reference - `[{final_answer.main_question_id[:8]}...]` → Include full ID
- **Line 662**: Final answer display - `[{final_answer.final_answer_id[:8]}...]` → Include full ID
- **Line 682, 685**: Answer references - `[{answer_id[:8]}...]` → Include full IDs

**Fix pattern:** Most critical - this toolset has the most instances

#### 1.4 Self-Refine (`toolsets/self_refine/toolset.py`)

**Lines to fix:**

- **Line 353**: Hint - `[{unfeedback[0].output_id[:8]}...]` → Include full ID
- **Line 358**: Hint - `[{unrefined[0][:8]}...]` → Include full ID
- **Line 560**: Available list - `[{o.output_id[:8]}]` → Show full IDs
- **Line 562**: Error message - `'{feedback.output_id[:8]}...'` → Show full ID
- **Line 618**: Available list - Same as 560
- **Line 620**: Error message - `'{refine.output_id[:8]}...'` → Show full ID

#### 1.5 Reflection (`toolsets/reflection/toolset.py`)

**Lines to fix:**

- **Line 312**: Hint - `[{uncritiqued[0].output_id[:8]}...]` → Include full ID
- **Line 318**: Hint - `[{unrefined[0][:8]}...]` → Include full ID
- **Line 470**: Available list - `[{o.output_id[:8]}]` → Show full IDs
- **Line 472**: Error message - `'{critique.output_id[:8]}...'` → Show full ID
- **Line 510**: Available list - Same as 470
- **Line 512**: Error message - `'{refine.output_id[:8]}...'` → Show full ID

#### 1.6 Graph of Thought Reasoning (`toolsets/graph_of_thought_reasoning/toolset.py`)

**Lines to fix:**

- **Line 231**: Hint - `[{unevaluated[0].node_id[:8]}...]` → Include full ID
- **Line 235**: Hint - `[{low_score[0].node_id[:8]}...]` → Include full ID
- **Line 266**: Node display - `[{node.node_id[:8]}]` → Include full ID
- **Line 276**: Edge display - `[{edge.source_id[:8]}]` and `[{edge.target_id[:8]}]` → Include full IDs
- **Line 284**: Evaluation display - `[{ev.node_id[:8]}]` → Include full ID
- **Line 323**: Creation message - `Created [{node_id[:8]}]` → Include full ID
- **Line 340**: Available list - `[{n.node_id[:8]}]` → Show full IDs
- **Line 341**: Error message - `'{edge.source_id[:8]}...'` → Show full ID
- **Line 344**: Error message - `'{edge.target_id[:8]}...'` → Show full ID
- **Line 413**: Error message - `'{refine.node_id[:8]}...'` → Show full ID
- **Line 455**: Error message - `'{evaluation.node_id[:8]}...'` → Show full ID
- **Line 484**: Error message - `'{node_id[:8]}...'` → Show full ID
- **Line 505**: Error message - `'{source_id[:8]}...'` → Show full ID
- **Line 508**: Error message - `'{target_id[:8]}...'` → Show full ID

#### 1.7 Monte Carlo Reasoning (`toolsets/monte_carlo_reasoning/toolset.py`)

**Lines to fix:**

- **Line 263**: Node display in read_mcts - `[{node.node_id[:8]}]` → Show full ID
- **Line 307**: Available list - `[{n.node_id[:8]}]` → Show full IDs
- **Line 308**: Error message - `'{select.node_id[:8]}...'` → Show full ID
- **Line 370**: Error message - `'{expand.node_id[:8]}...'` → Show full ID
- **Line 412**: Error message - `'{sim.node_id[:8]}...'` → Show full ID
- **Line 448**: Error message - `'{backprop.node_id[:8]}...'` → Show full ID

#### 1.8 Multi-Persona Debate (`toolsets/multi_persona_debate/toolset.py`)

**Lines to fix:**

- **Line 471**: Hint - `[{uncritiqued[0].position_id[:8]}...]` → Show full ID
- **Line 498**: Persona display - `[{persona.persona_id[:8]}...]` → Show full ID
- **Line 521**: Parent position reference - `[{position.parent_position_id[:8]}...]` → Show full ID
- **Line 532**: Position display - `[{position.position_id[:8]}...]` → Show full ID (note: line 531 shows full ID, but 532 truncates)
- **Line 537**: Critiques addressed - `[{c[:8] + '...'}]` → Show full IDs
- **Lines 558-594**: Multiple display truncations in critiques/agreements → Show full IDs
- **Line 815**: Position creation - `[{position_id[:8]}...]` → Show full ID
- **Line 898-899**: Critique creation - Multiple `[:8]` → Show full IDs
- **Line 977-978**: Agreement creation - Multiple `[:8]` → Show full IDs
- **Line 1081**: Position defense - `[{position_id[:8]}...]` → Show full ID
- **Lines 1169-1176**: Remove warnings about full IDs (no longer needed once we show full IDs everywhere)

#### 1.9 Multi-Persona Analysis (`toolsets/multi_persona_analysis/toolset.py`)

**Lines to fix:**

- **Line 293**: Hint - `[{missing[0][:8]}...]` → Show full ID (persona_id)

### Category 2: Storage `get_outputs_for_linking()` Methods

These return IDs for cross-toolset linking - MUST be full IDs.

#### 2.1 Todo Storage (`toolsets/to_do/storage.py`)

**Line 249**: Uses `item_id = str(i)` - **CRITICAL ISSUE**

**Problem:** Index-based IDs are not stable/persistent. If todos are reordered or deleted, IDs change.

**Fix:** Change to UUID-based IDs:

1. Add `todo_id: str` field to `Todo` type (if not exists)
2. Generate UUID when todo is created
3. Update `get_outputs_for_linking()` to return `todo.todo_id` instead of `str(i)`
4. Update all references to use `todo_id` instead of index

**Lines to check:**

- `toolsets/to_do/types.py` - Verify Todo model has `todo_id`
- `toolsets/to_do/toolset.py` - Ensure todos are created with UUIDs
- `toolsets/to_do/storage.py` line 249 - Fix get_outputs_for_linking

#### 2.2 Chain of Thought Storage (`toolsets/chain_of_thought_reasoning/storage.py`)

**Line 263**: Uses `item_id = str(thought.thought_number)` - **POTENTIAL ISSUE**

**Problem:** Thought numbers are sequential and may not be unique across sessions.

**Fix:**

- Option A: Use thought_number (acceptable if thoughts are never deleted/reordered)
- Option B: Add `thought_id: str` UUID field to Thought type
- **Recommendation:** Keep thought_number for now but document it's stable within a session

#### 2.3 All Other Storages

**Verify:** All other `get_outputs_for_linking()` methods return full UUIDs (not truncated):

- Search storage: ✅ Returns full `result_id` and `content_id`
- Self-ask storage: ✅ Returns full UUIDs
- Self-refine storage: ✅ Returns full UUIDs
- Reflection storage: ✅ Returns full UUIDs
- Tree of Thought storage: ✅ Returns full UUIDs
- Graph of Thought storage: ✅ Returns full UUIDs
- Beam Search storage: ✅ Returns full UUIDs
- Monte Carlo storage: ✅ Returns full UUIDs
- Persona Analysis storage: ✅ Returns full UUIDs
- Persona Debate storage: ✅ Returns full UUIDs

### Category 3: System Prompt Dynamic Sections

These appear in prompts and may contain truncated IDs.

#### 3.1 Beam Search System Prompt (`toolsets/beam_search_reasoning/toolset.py`)

**Line 520**: `get_beam_system_prompt()` shows `[{c.candidate_id[:8]}]` in "Current State" section

**Fix:** Include full IDs in system prompt state sections

#### 3.2 Tree of Thought System Prompt (`toolsets/tree_of_thought_reasoning/toolset.py`)

**Check:** `get_tot_system_prompt()` - verify if it includes truncated IDs

#### 3.3 Graph of Thought System Prompt (`toolsets/graph_of_thought_reasoning/toolset.py`)

**Check:** `get_got_system_prompt()` - verify if it includes truncated IDs

#### 3.4 Self-Ask System Prompt (`toolsets/self_ask/toolset.py`)

**Check:** `get_self_ask_system_prompt()` - verify if it includes truncated IDs

### Category 4: Error Messages

Error messages showing truncated IDs in "Available" lists cause agents to use wrong IDs.

**Pattern to fix:**

```python
# Before
available = ", ".join([c.candidate_id[:8] for c in list(_storage.candidates.values())[:5]])
return f"Error: Candidate '{expand.candidate_id[:8]}...' not found. Available: [{available}]. Call read_beam."

# After - Show full IDs
available = ", ".join([c.candidate_id for c in list(_storage.candidates.values())[:5]])
return f"Error: Candidate '{expand.candidate_id}' not found. Available: [{available}]. Call read_beam."
```

**Files with error messages to fix:**

- `beam_search_reasoning/toolset.py`: Lines 326-327, 377-378
- `tree_of_thought_reasoning/toolset.py`: Lines 294-296
- `self_ask/toolset.py`: Lines 498-500, 547-549, 594-596, 613
- `self_refine/toolset.py`: Lines 560-562, 618-620
- `reflection/toolset.py`: Lines 470-472, 510-512
- `graph_of_thought_reasoning/toolset.py`: Lines 340-344, 413, 455, 484, 505, 508
- `monte_carlo_reasoning/toolset.py`: Lines 308, 370, 412, 448

### Category 5: Search Toolset (Reference Implementation)

**Current state:** Search toolset shows FULL IDs (good example):

- Line 251: `[{result_id}]` - Full UUID
- Line 352: `[{result_id}]` - Full UUID  
- Line 446: `[{result_id}]` - Full UUID
- Line 491: `[{content.content_id}]` - Full UUID
- Line 540: `[{content_id}]` - Full UUID

**Action:** Use search toolset as the pattern for other toolsets

### Category 6: Examples and Documentation

**Files to update:**

- `examples/combinations/research_assistant_example.py`: Line 181 - Shows truncated IDs (`{link.source_item_id[:8]}...`)
- `examples/combinations/strategic_decision_maker_example.py`: Line 168 - Shows truncated IDs (`{link.source_item_id[:8]}...`)
- `examples/combinations/creative_problem_solver_example.py`: Line 170 - Shows truncated IDs (`{link.source_item_id[:8]}...`)
- `examples/combinations/code_architect_example.py`: Line 174 - Shows truncated IDs (`{link.source_item_id[:8]}...`)

**Fix:** Update examples to show full IDs:

```python
# Before
print(f"  {link.source_toolset_id}:{link.source_item_id[:8]}... → {link.target_toolset_id}:{link.target_item_id[:8]}... ({link.link_type.value})")

# After
print(f"  {link.source_toolset_id}:{link.source_item_id} → {link.target_toolset_id}:{link.target_item_id} ({link.link_type.value})")
```

### Category 7: Evaluation Code (`evals/base.py`)

**CRITICAL:** Evaluation code truncates IDs in state inspection, which may affect test results.

**Lines to fix:**

- **Line 341**: `"question_id": q.question_id[:8] + "..."` → Show full ID
- **Line 352**: `"answer_id": a.answer_id[:8] + "..."` → Show full ID
- **Line 353**: `"question_id": a.question_id[:8] + "..."` → Show full ID
- **Line 363**: `"final_answer_id": fa.final_answer_id[:8] + "..."` → Show full ID
- **Line 364**: `"main_question_id": fa.main_question_id[:8] + "..."` → Show full ID

**Fix pattern:**

```python
# Before
"question_id": q.question_id[:8] + "..."

# After
"question_id": q.question_id
```

**Note:** Line 452 truncates prompt text (not an ID) - this is acceptable for display purposes.

### Category 8: Meta-Orchestrator Linking

**File:** `toolsets/meta_orchestrator/toolset.py`

**Line 358**: Shows full IDs in unified state (good)

**Line 519**: Shows full IDs in link creation message (good)

**Verify:** Ensure `read_unified_state` always shows full IDs for linking purposes

## Implementation Strategy

### Phase 1: Critical Fixes (Tool Output Messages)

1. Fix all tool output messages - replace all `[:8]` truncations with full IDs
2. Update error messages to show full IDs
3. Update hint messages to show full IDs

### Phase 2: Storage Consistency

1. Fix Todo storage to use UUID-based IDs
2. Verify Chain of Thought storage ID strategy
3. Audit all `get_outputs_for_linking()` methods

### Phase 3: System Prompts

1. Update dynamic state sections in system prompts
2. Ensure full IDs are always available when needed

### Phase 4: Examples and Documentation

1. Update example files to show full IDs
2. Update evaluation code to show full IDs

### Phase 5: Verification

1. Search entire codebase for any remaining `[:8]` or `[:N]` patterns on ID fields
2. Verify no ID truncation remains anywhere

## Testing Strategy

1. **Unit Tests**: Verify full IDs are returned in all tool outputs
2. **Integration Tests**: Test cross-toolset linking with full IDs
3. **Agent Tests**: Run agents and verify they can use IDs from tool outputs
4. **Error Recovery Tests**: Verify agents can recover from errors using full IDs

## Code Pattern to Implement

**Simple replacement pattern:**

```python
# Find all instances of:
id[:8] or id[:N] where id is an ID field (question_id, answer_id, candidate_id, node_id, output_id, position_id, persona_id, content_id, result_id, etc.)

# Replace with:
id (full ID)

# Examples:
# Before: f"[{candidate_id[:8]}]"
# After:  f"[{candidate_id}]"

# Before: f"Error: '{expand.candidate_id[:8]}...' not found"
# After:  f"Error: '{expand.candidate_id}' not found"

# Before: ", ".join([c.candidate_id[:8] for c in candidates])
# After:  ", ".join([c.candidate_id for c in candidates])
```

**Note:** Only truncate non-ID content (like descriptions, content text) - never truncate IDs.

## Priority Order

1. **HIGHEST**: Tool output messages (Category 1) - Agents see these directly
2. **HIGHEST**: Evaluation code (Category 7) - Affects test accuracy and debugging
3. **HIGH**: Error messages (Category 4) - Critical for error recovery
4. **HIGH**: Todo storage fix (Category 2.1) - Breaks linking
5. **MEDIUM**: System prompt sections (Category 3) - Affects agent understanding
6. **MEDIUM**: Examples (Category 6) - Documentation and examples
7. **LOW**: Meta-orchestrator (Category 8) - Already mostly correct

## Notes

- **Search toolset is the reference implementation** - shows full IDs correctly (lines 251, 352, 446, 491, 540)
- Persona debate toolset has warnings about full IDs (lines 1170-1171) - these can be removed once we show full IDs everywhere
- Evaluation code truncates IDs in state inspection - this may affect debugging and test result accuracy
- Monte Carlo toolset truncates node IDs in display (line 263) - needs full IDs
- Multi-persona debate truncates critique IDs in position display (line 537) - needs full IDs
- All storage `get_outputs_for_linking()` methods should return full IDs (already mostly correct except Todo)

## Complete File List

Files requiring fixes (183+ instances total):

### Toolset Tool Files (Primary)

1. `toolsets/beam_search_reasoning/toolset.py` - 13 instances
2. `toolsets/tree_of_thought_reasoning/toolset.py` - 6 instances
3. `toolsets/self_ask/toolset.py` - 30+ instances (most critical)
4. `toolsets/self_refine/toolset.py` - 6 instances
5. `toolsets/reflection/toolset.py` - 6 instances
6. `toolsets/graph_of_thought_reasoning/toolset.py` - 15 instances
7. `toolsets/monte_carlo_reasoning/toolset.py` - 7 instances
8. `toolsets/multi_persona_debate/toolset.py` - 12+ instances
9. `toolsets/multi_persona_analysis/toolset.py` - 1 instance

### Storage Files

10. `toolsets/to_do/storage.py` - Index-based IDs (needs UUID conversion)
11. `toolsets/chain_of_thought_reasoning/storage.py` - Verify ID strategy

### Evaluation Files

12. `evals/base.py` - 5 instances (CRITICAL for test accuracy)

### Example Files

13. `examples/combinations/research_assistant_example.py` - 1 instance
14. `examples/combinations/strategic_decision_maker_example.py` - 1 instance
15. `examples/combinations/creative_problem_solver_example.py` - 1 instance
16. `examples/combinations/code_architect_example.py` - 1 instance

### System Prompt Files

17. `toolsets/beam_search_reasoning/toolset.py` - `get_beam_system_prompt()` function
18. Other toolset system prompt getters - verify for truncated IDs