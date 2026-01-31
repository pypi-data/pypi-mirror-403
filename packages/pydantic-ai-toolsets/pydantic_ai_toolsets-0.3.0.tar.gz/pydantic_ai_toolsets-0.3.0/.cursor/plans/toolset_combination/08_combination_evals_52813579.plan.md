---
name: 08_combination_evals
overview: Create evaluation system for combination workflows including test datasets and eval functions for all 4 workflow templates
todos:
  - id: create-combination-eval-infrastructure
    content: Create evals/categories/combinations/ directory with __init__.py and compare_combinations.py
    status: completed
  - id: create-research-assistant-eval
    content: Create research_assistant_eval.py with task function and dataset creation
    status: completed
  - id: create-creative-solver-eval
    content: Create creative_problem_solver_eval.py with task function and dataset creation
    status: completed
  - id: create-strategic-decision-eval
    content: Create strategic_decision_maker_eval.py with task function and dataset creation
    status: completed
  - id: create-code-architect-eval
    content: Create code_architect_eval.py with task function and dataset creation
    status: completed
  - id: create-combination-test-dataset
    content: Create evals/datasets/combination_cases.py with test cases for all 4 workflow templates (20-28 total cases)
    status: completed
  - id: update-run-evals-combinations
    content: Update run_evals.py to add run_combinations function and add combinations to category choices
    status: completed
  - id: update-datasets-init
    content: Update evals/datasets/__init__.py to export COMBINATION_CASES
    status: completed
---

# Combination Evaluation System

This plan covers Phases 8-9: Combination Evals.

## Files to Create

### 1. Combination Eval Infrastructure

**File**: `pydantic_ai_toolsets/evals/categories/combinations/`

- `__init__.py` - Export combination eval functions
- `compare_combinations.py` - Compare different workflow templates
- `research_assistant_eval.py` - Eval for Research Assistant workflow
- `creative_problem_solver_eval.py` - Eval for Creative Problem Solver workflow
- `strategic_decision_maker_eval.py` - Eval for Strategic Decision Maker workflow
- `code_architect_eval.py` - Eval for Code Architect workflow

### 2. Combination Test Dataset

**File**: `pydantic_ai_toolsets/evals/datasets/combination_cases.py`

Create test cases for each workflow template (20-28 total cases):

**Research Assistant Cases** (5-7 cases):

- "Research the latest developments in quantum computing..."
- "Find information about renewable energy trends..."
- "Research the pros and cons of remote work..."
- "Investigate recent AI safety research..."
- "Research sustainable packaging solutions..."

**Creative Problem Solver Cases** (5-7 cases):

- "Design a sustainable urban transportation system"
- "Create a comprehensive strategy for reducing food waste..."
- "Design an inclusive educational platform..."
- "Develop a plan for carbon-neutral manufacturing"
- "Create a mental health support system..."

**Strategic Decision Maker Cases** (5-7 cases):

- "Should a company migrate from monolith to microservices?"
- "Should we invest in building an in-house AI team..."
- "Should we prioritize user acquisition or user retention?"
- "Should we expand to international markets now or wait?"
- "Should we adopt a fully remote work model permanently?"

**Code Architect Cases** (5-7 cases):

- "Design the architecture for a distributed task queue system"
- "Design a scalable real-time chat application"
- "Create the architecture for a multi-tenant SaaS platform"
- "Design a microservices architecture for an e-commerce platform"
- "Plan the architecture for a data pipeline processing system"

**Test Case Structure**:

```python
@dataclass
class CombinationTestCase:
    name: str
    prompt: str
    workflow_template: str
    expected_toolsets: list[str]
    expected_transitions: list[tuple[str, str]]
    expected_prefixed_tools: list[str] | None = None
    min_storage_items: int = 5
    difficulty: str = "medium"
    expected_cross_links: int = 0
```

### 3. Update run_evals.py

**File**: `pydantic_ai_toolsets/evals/run_evals.py`

- Add `run_combinations(config)` function
- Add "combinations" to category choices in argparse
- Update `run_all()` to include combinations category

### 4. Task Functions

Each combination eval file needs a task function that:

- Creates combined toolset with meta-orchestrator
- Initializes workflow template
- Runs agent with combined toolsets
- Validates workflow progression
- Checks cross-toolset links exist
- Validates unified state is accessible

## Dependencies

- Requires `01_core_infrastructure.md` (workflow templates)
- Requires `02_aliasing_and_combination.md` (combination helpers)
- Requires `03_cross_toolset_linking.md` (for link validation)
- Requires `04_unified_state_management.md` (for unified state validation)

## Related Plans

- See `01_core_infrastructure.md` for workflow templates
- See `02_aliasing_and_combination.md` for combination logic