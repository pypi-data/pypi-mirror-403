"""Workflow templates for common toolset combination patterns."""

from __future__ import annotations

from .types import Stage, WorkflowTemplate

# =============================================================================
# RESEARCH ASSISTANT TEMPLATE
# =============================================================================

RESEARCH_ASSISTANT = WorkflowTemplate(
    name="research_assistant",
    toolsets=["search", "self_ask", "self_refine", "todo"],
    stages=[
        Stage(
            name="research",
            toolset_id="search",
            transition_condition="has_search_results",
            description="Gather information from the web using search tools",
        ),
        Stage(
            name="decompose",
            toolset_id="self_ask",
            transition_condition="has_final_answer",
            description="Decompose complex questions into sub-questions and compose final answer",
        ),
        Stage(
            name="refine",
            toolset_id="self_refine",
            transition_condition="has_best_output",
            description="Refine the output through iterative feedback cycles",
        ),
        Stage(
            name="track",
            toolset_id="todo",
            transition_condition="always",
            description="Track completed tasks and manage workflow",
        ),
    ],
    handoff_instructions={
        "search→self_ask": "Use search results to formulate main question for decomposition",
        "self_ask→self_refine": "Use final answer from self-ask as initial output for refinement",
        "self_refine→todo": "Track refined output as completed task",
    },
    description="Perfect for research tasks requiring information gathering, decomposition, and refinement",
)

# =============================================================================
# CREATIVE PROBLEM SOLVER TEMPLATE
# =============================================================================

CREATIVE_PROBLEM_SOLVER = WorkflowTemplate(
    name="creative_problem_solver",
    toolsets=["persona", "got", "reflection"],
    stages=[
        Stage(
            name="analyze",
            toolset_id="persona",
            transition_condition="has_synthesis",
            description="Gather diverse perspectives using multiple personas",
        ),
        Stage(
            name="explore",
            toolset_id="got",
            transition_condition="has_path_found",
            description="Explore multiple reasoning paths using graph structure",
        ),
        Stage(
            name="reflect",
            toolset_id="reflection",
            transition_condition="has_best_output",
            description="Reflect on and refine the solution through critique cycles",
        ),
    ],
    handoff_instructions={
        "persona→got": "Use synthesized persona perspectives to seed graph exploration",
        "got→reflection": "Use best path from graph exploration as initial output for reflection",
    },
    description="Perfect for complex problems needing diverse perspectives and synthesis",
)

# =============================================================================
# STRATEGIC DECISION MAKER TEMPLATE
# =============================================================================

STRATEGIC_DECISION_MAKER = WorkflowTemplate(
    name="strategic_decision_maker",
    toolsets=["persona_debate", "mcts", "reflection"],
    stages=[
        Stage(
            name="debate",
            toolset_id="persona_debate",
            transition_condition="has_resolution",
            description="Engage in structured debate between multiple expert personas",
        ),
        Stage(
            name="explore",
            toolset_id="mcts",
            transition_condition="has_best_action",
            description="Explore decision space using Monte Carlo Tree Search",
        ),
        Stage(
            name="reflect",
            toolset_id="reflection",
            transition_condition="has_best_output",
            description="Reflect on and refine the decision through critique cycles",
        ),
    ],
    handoff_instructions={
        "persona_debate→mcts": "Use debate positions to seed MCTS exploration",
        "mcts→reflection": "Use best action from MCTS as initial output for reflection",
    },
    description="Perfect for high-stakes decisions requiring expert debate and exploration",
)

# =============================================================================
# CODE ARCHITECT TEMPLATE
# =============================================================================

CODE_ARCHITECT = WorkflowTemplate(
    name="code_architect",
    toolsets=["self_ask", "tot", "reflection", "todo"],
    stages=[
        Stage(
            name="decompose",
            toolset_id="self_ask",
            transition_condition="has_final_answer",
            description="Decompose architecture problem into sub-questions",
        ),
        Stage(
            name="explore",
            toolset_id="tot",
            transition_condition="has_solution",
            description="Explore multiple architectural approaches using tree structure",
        ),
        Stage(
            name="reflect",
            toolset_id="reflection",
            transition_condition="has_best_output",
            description="Reflect on and refine the architecture through critique cycles",
        ),
        Stage(
            name="track",
            toolset_id="todo",
            transition_condition="always",
            description="Track architectural components and tasks",
        ),
    ],
    handoff_instructions={
        "self_ask→tot": "Use decomposed questions to seed tree exploration of architectural options",
        "tot→reflection": "Use best solution from tree as initial output for reflection",
        "reflection→todo": "Track refined architecture components as completed tasks",
    },
    description="Perfect for software architecture requiring decomposition, exploration, and task tracking",
)

# =============================================================================
# TEMPLATE REGISTRY
# =============================================================================

ALL_TEMPLATES = [
    RESEARCH_ASSISTANT,
    CREATIVE_PROBLEM_SOLVER,
    STRATEGIC_DECISION_MAKER,
    CODE_ARCHITECT,
]

TEMPLATE_BY_NAME = {template.name: template for template in ALL_TEMPLATES}


def get_template(name: str) -> WorkflowTemplate | None:
    """Get a workflow template by name.

    Args:
        name: Name of the template (e.g., 'research_assistant')

    Returns:
        WorkflowTemplate if found, None otherwise
    """
    return TEMPLATE_BY_NAME.get(name)


def list_templates() -> list[str]:
    """List all available workflow template names.

    Returns:
        List of template names
    """
    return list(TEMPLATE_BY_NAME.keys())
