---
name: 01_core_infrastructure
overview: Create meta-orchestrator toolset, workflow templates, and core infrastructure for toolset combination system
todos:
  - id: meta-orchestrator-types
    content: Create meta_orchestrator/types.py with WorkflowState, ToolsetTransition, WorkflowTemplate, CrossToolsetLink, Stage
    status: pending
  - id: meta-orchestrator-storage
    content: Create meta_orchestrator/storage.py with MetaOrchestratorStorage and WorkflowRegistry
    status: pending
  - id: meta-orchestrator-toolset
    content: Create meta_orchestrator/toolset.py with read_unified_state, suggest_toolset_transition, start_workflow, link_toolset_outputs, get_workflow_status
    status: pending
  - id: workflow-templates
    content: Create workflow_templates.py with 4 predefined templates (Research Assistant, Creative Problem Solver, Strategic Decision Maker, Code Architect)
    status: pending
---

# Core Infrastructure for Toolset Combination

This plan covers Phase 1: Core Infrastructure including meta-orchestrator toolset and workflow templates.

## Files to Create

### 1. Meta-Orchestrator Types

**File**: `pydantic_ai_toolsets/toolsets/meta_orchestrator/types.py`

Define core types:

- `WorkflowState` - tracks active toolsets and their states
- `ToolsetTransition` - suggests when to switch toolsets
- `WorkflowTemplate` - predefined workflow patterns
- `CrossToolsetLink` - links between toolset outputs
- `Stage` - represents a stage in a workflow template

### 2. Meta-Orchestrator Storage

**File**: `pydantic_ai_toolsets/toolsets/meta_orchestrator/storage.py`

- `MetaOrchestratorStorage` - tracks active toolsets, workflows, links
- `WorkflowRegistry` - stores workflow templates
- Methods: `register_toolset()`, `track_transition()`, `create_link()`, `get_unified_state()`

### 3. Meta-Orchestrator Toolset

**File**: `pydantic_ai_toolsets/toolsets/meta_orchestrator/toolset.py`

Main orchestrator toolset with tools:

- `read_unified_state()` - shows state across all active toolsets
- `suggest_toolset_transition()` - recommends next toolset based on current state
- `start_workflow()` - initialize a workflow template
- `link_toolset_outputs()` - create cross-toolset links
- `get_workflow_status()` - show current workflow progress

### 4. Workflow Templates

**File**: `pydantic_ai_toolsets/toolsets/meta_orchestrator/workflow_templates.py`

Define 4 workflow templates:

- **Research Assistant**: Search → Self-Ask → Self-Refine → Todo
- **Creative Problem Solver**: Multi-Persona Analysis → Graph of Thoughts → Reflection
- **Strategic Decision Maker**: Multi-Persona Debate → MCTS → Reflection
- **Code Architect**: Self-Ask → Tree of Thoughts → Reflection → Todo

Each template includes:

- Toolset sequence
- Transition conditions
- Expected outputs at each stage
- Handoff instructions

## Dependencies

- None (foundational infrastructure)

## Related Plans

- See `02_aliasing_and_combination.md` for aliasing system
- See `03_cross_toolset_linking.md` for linking infrastructure
- See `04_unified_state.md` for unified state management