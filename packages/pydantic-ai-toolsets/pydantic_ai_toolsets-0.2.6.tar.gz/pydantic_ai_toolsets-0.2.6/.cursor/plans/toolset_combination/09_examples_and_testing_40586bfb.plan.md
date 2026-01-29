---
name: 09_examples_and_testing
overview: Create example scripts and testing infrastructure for combination workflows
todos:
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
---

# Examples and Testing

This plan covers Phase 10: Testing & Examples.

## Files to Create

### 1. Example Scripts

**File**: `examples/combinations/`

Create example scripts for each workflow template:

- `research_assistant_example.py`
- `creative_problem_solver_example.py`
- `strategic_decision_maker_example.py`
- `code_architect_example.py`

Each example demonstrates:

- Workflow initialization
- Toolset transitions
- Cross-toolset linking
- Unified state reading

### 2. Testing Strategy

- Unit tests for each component
- Integration tests for workflow templates
- Example scripts as living documentation
- Eval tests for all combination workflows
- Validation that dynamic aliasing works correctly
- Validation that original toolsets remain unchanged
- Validation that system prompts are properly combined
- Validation that prefixed tool names in prompts match actual prefixed tool names

## Dependencies

- Requires all previous plans to be implemented
- Requires `01_core_infrastructure.md` (workflow templates)
- Requires `02_aliasing_and_combination.md` (combination logic)
- Requires `08_combination_evals.md` (eval infrastructure)

## Related Plans

- See `01_core_infrastructure.md` for workflow templates
- See `02_aliasing_and_combination.md` for combination examples
- See `08_combination_evals.md` for eval infrastructure