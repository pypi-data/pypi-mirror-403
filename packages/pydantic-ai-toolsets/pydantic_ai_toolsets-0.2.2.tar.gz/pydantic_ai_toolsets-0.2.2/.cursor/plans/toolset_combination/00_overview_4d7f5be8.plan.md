---
name: 00_overview
overview: Overview and architecture of the toolset combination system - master plan that references all sub-plans
todos:
  - id: review-all-plans
    content: Review all sub-plans to ensure consistency and completeness
    status: pending
---

# Toolset Combination System - Overview

This is the master plan that provides an overview of the entire toolset combination system. Implementation is broken down into focused sub-plans.

## Architecture Overview

The implementation adds:

1. **Meta-Orchestrator Toolset** - Suggests toolset transitions and tracks workflows
2. **Workflow Templates** - Predefined combinations for common patterns
3. **Cross-Toolset Linking** - Link outputs between toolsets
4. **Unified State Management** - Single read function across all toolsets
5. **Dynamic Toolset Aliasing** - Runtime-only aliasing when combining toolsets (zero source code changes)
6. **Combination-Specific System Prompts** - Prompts adapted for multi-toolset workflows
7. **Documentation** - Comprehensive combination documentation
8. **Evaluation System** - Evals for combination workflows

## Implementation Plans

The work is broken down into focused plans:

1. **`01_core_infrastructure.md`** - Meta-orchestrator toolset, workflow templates, core types
2. **`02_aliasing_and_combination.md`** - Dynamic aliasing using official API, system prompt combination
3. **`03_cross_toolset_linking.md`** - Cross-toolset linking infrastructure
4. **`04_unified_state_management.md`** - Unified state read function
5. **`05_workflow_templates_implementation.md`** - Detailed implementation of 4 workflow templates
6. **`06_integration_and_helpers.md`** - Integration hooks, helper functions, package exports
7. **`07_documentation.md`** - README updates and documentation
8. **`08_combination_evals.md`** - Evaluation system for combination workflows
9. **`09_examples_and_testing.md`** - Example scripts and testing

## Key Design Decisions

1. **Zero Breaking Changes**: All aliasing happens at runtime using official pydantic-ai API. Original toolsets remain unchanged.

2. **Combination-Specific Prompts**: Each toolset has two prompt variants:

   - Standalone prompt (for single-toolset usage)
   - Combination prompt (for multi-toolset workflows)

3. **Minimal Aliasing**: Only alias when collisions exist. Tools without collisions keep original names.

4. **Modularity**: Each component can be used independently.

5. **Extensibility**: Easy to add new workflow templates.

## File Structure

```
pydantic_ai_toolsets/
├── toolsets/
│   ├── meta_orchestrator/
│   │   ├── __init__.py
│   │   ├── types.py
│   │   ├── storage.py
│   │   ├── toolset.py
│   │   ├── workflow_templates.py
│   │   └── helpers.py
│   └── _shared/
│       ├── linking.py
│       ├── aliasing.py
│       └── system_prompts.py
├── evals/
│   ├── categories/
│   │   └── combinations/
│   │       ├── __init__.py
│   │       ├── compare_combinations.py
│   │       ├── research_assistant_eval.py
│   │       ├── creative_problem_solver_eval.py
│   │       ├── strategic_decision_maker_eval.py
│   │       └── code_architect_eval.py
│   └── datasets/
│       └── combination_cases.py
├── examples/
│   └── combinations/
│       ├── research_assistant_example.py
│       ├── creative_problem_solver_example.py
│       ├── strategic_decision_maker_example.py
│       └── code_architect_example.py
└── README.md
```

## Implementation Order

1. **Week 1**: Core infrastructure (01, 03)
2. **Week 2**: Aliasing and combination (02)
3. **Week 3**: Unified state and workflow templates (04, 05)
4. **Week 4**: Integration and helpers (06)
5. **Week 5**: Documentation and examples (07, 09)
6. **Week 6**: Evaluation system (08)

## Dependencies Between Plans

- 01 (Core Infrastructure) → Foundation for everything
- 02 (Aliasing) → Required by 05, 06, 08
- 03 (Linking) → Used by 01, 04, 08
- 04 (Unified State) → Requires 01, 03
- 05 (Templates) → Requires 01, 02
- 06 (Integration) → Requires 01, 02, 03
- 07 (Documentation) → Requires understanding of all
- 08 (Evals) → Requires 01, 02, 03, 04, 05
- 09 (Examples) → Requires all previous plans