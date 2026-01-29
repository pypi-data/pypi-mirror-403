---
name: 07_documentation
overview: Update README.md with comprehensive documentation for combining toolsets, workflow templates, and meta-orchestrator usage
todos:
  - id: readme-combination-section
    content: Add Combining Toolsets section to README.md with overview, function collisions, and workflow templates
    status: completed
  - id: readme-examples
    content: Add combination examples to README.md showing each workflow template in action
    status: completed
  - id: readme-meta-orchestrator
    content: Add meta-orchestrator documentation to README.md with usage guide
    status: completed
---

# Documentation Updates

This plan covers Phase 7: README Updates.

## Files to Update

### README.md

**File**: `README.md`

Add new section after "Utility Toolsets":

### 1. Combining Toolsets Section

- Overview of toolset combination
- Function name collision explanation
- Dynamic runtime aliasing solution
- System prompt combination explanation

### 2. Workflow Templates Documentation

Document each of the 4 templates:

- Research Assistant: Search → Self-Ask → Self-Refine → Todo
- Creative Problem Solver: Multi-Persona Analysis → Graph of Thoughts → Reflection
- Strategic Decision Maker: Multi-Persona Debate → MCTS → Reflection
- Code Architect: Self-Ask → Tree of Thoughts → Reflection → Todo

### 3. Combination Examples

Add code examples for each workflow template showing:

- How to initialize the workflow
- How toolsets transition
- How to access unified state
- How to create cross-toolset links

### 4. Meta-Orchestrator Documentation

Document the meta-orchestrator toolset:

- When to use it
- How to register toolsets
- How to track workflows
- How to create custom workflows

## Dependencies

- Requires understanding of `02_aliasing_and_combination.md`
- Requires understanding of `01_core_infrastructure.md`
- Requires understanding of `05_workflow_templates_implementation.md`

## Related Plans

- See `02_aliasing_and_combination.md` for aliasing details
- See `01_core_infrastructure.md` for meta-orchestrator details
- See `10_examples_and_testing.md` for example code