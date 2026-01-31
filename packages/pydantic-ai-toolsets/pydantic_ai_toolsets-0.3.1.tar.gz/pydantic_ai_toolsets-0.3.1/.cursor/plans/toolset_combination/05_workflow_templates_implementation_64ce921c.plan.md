---
name: 05_workflow_templates_implementation
overview: Implement the 4 workflow templates (Research Assistant, Creative Problem Solver, Strategic Decision Maker, Code Architect) with detailed stage definitions
todos:
  - id: implement-research-assistant-template
    content: Implement RESEARCH_ASSISTANT workflow template with stages and handoff instructions
    status: pending
  - id: implement-creative-solver-template
    content: Implement CREATIVE_PROBLEM_SOLVER workflow template
    status: pending
  - id: implement-strategic-decision-template
    content: Implement STRATEGIC_DECISION_MAKER workflow template
    status: pending
  - id: implement-code-architect-template
    content: Implement CODE_ARCHITECT workflow template
    status: pending
---

# Workflow Template Implementation

This plan covers Phase 5: Workflow Template Implementation.

## Files to Update

### Workflow Templates

**File**: `pydantic_ai_toolsets/toolsets/meta_orchestrator/workflow_templates.py`

Implement detailed templates:

### 1. Research Assistant Template

```python
RESEARCH_ASSISTANT = WorkflowTemplate(
    name="research_assistant",
    toolsets=["search", "self_ask", "self_refine", "todo"],
    stages=[
        Stage("research", "search", transition_condition="has_search_results"),
        Stage("decompose", "self_ask", transition_condition="has_final_answer"),
        Stage("refine", "self_refine", transition_condition="has_best_output"),
        Stage("track", "todo", transition_condition="always"),
    ],
    handoff_instructions={
        "search→self_ask": "Use search results to formulate main question",
        "self_ask→self_refine": "Use final answer as initial output for refinement",
        "self_refine→todo": "Track refined output as completed task",
    }
)
```

### 2. Creative Problem Solver Template

- Multi-Persona Analysis → Graph of Thoughts → Reflection
- Similar structure with appropriate stages and transitions

### 3. Strategic Decision Maker Template

- Multi-Persona Debate → MCTS → Reflection
- Similar structure with appropriate stages and transitions

### 4. Code Architect Template

- Self-Ask → Tree of Thoughts → Reflection → Todo
- Similar structure with appropriate stages and transitions

## Dependencies

- Requires `01_core_infrastructure.md` (WorkflowTemplate type definition)
- Requires `02_aliasing_and_combination.md` (for combining toolsets)

## Related Plans

- See `01_core_infrastructure.md` for WorkflowTemplate type
- See `02_aliasing_and_combination.md` for combination helpers