"""Type definitions for pydantic-ai-tot."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ThoughtNode(BaseModel):
    """A node in a tree of thoughts execution.

    Each node represents a reasoning state. Nodes form a tree structure
    where multiple branches can be explored simultaneously.

    Attributes:
        node_id: Unique identifier for this node.
        content: The reasoning content at this node.
        parent_id: ID of the parent node (None for root nodes).
        depth: Depth level in the tree (0 for root).
        branch_id: Identifier for the branch this node belongs to.
        status: Current status of this node/branch.
        evaluation_score: Optional score evaluating this path (0-100).
        is_solution: Whether this node represents a solution.
        merged_from: List of node IDs whose insights were merged into this node.
    """

    node_id: str
    content: str
    parent_id: str | None = None
    depth: int = 0
    branch_id: str | None = None
    status: Literal["active", "pruned", "merged", "completed"] = "active"
    evaluation_score: float | None = None
    is_solution: bool = False
    merged_from: list[str] = Field(default_factory=list)


class BranchEvaluation(BaseModel):
    """Evaluation of a branch/path in the tree.

    Used to assess the promise of different reasoning paths.

    Attributes:
        branch_id: Identifier for the branch being evaluated.
        score: Evaluation score (0-100, higher is better).
        reasoning: Explanation of why this score was assigned.
        recommendation: Recommended action for this branch.
    """

    branch_id: str
    score: float = Field(..., ge=0, le=100, description="Evaluation score from 0-100")
    reasoning: str = Field(..., description="Explanation of why this score was assigned")
    recommendation: Literal["continue", "prune", "merge", "explore_deeper"] = Field(
        ...,
        description="Recommended action: continue exploring, prune as dead end, "
        "merge with another branch, or explore deeper",
    )


class NodeItem(BaseModel):
    """Input model for the create_node tool.

    This is the model that agents use when calling create_node.
    It has the same fields as ThoughtNode but with Field descriptions for LLM guidance.
    """

    content: str = Field(
        ...,
        description=(
            "The reasoning content at this node. Should represent a specific "
            "reasoning state or approach to the problem."
        ),
    )
    parent_id: str | None = Field(
        default=None,
        description=(
            "ID of the parent node. For root nodes, omit this field entirely or use null "
            "(not the string 'null'). Provide a parent_id string to extend an existing branch."
        ),
    )
    branch_id: str | None = Field(
        default=None,
        description=(
            "Identifier for the branch this node belongs to. Use to group related nodes. "
            "If creating a new branch from an existing node, use a new unique branch_id. "
            "Omit this field or use null (not the string 'null') if not needed."
        ),
    )
    is_solution: bool = Field(
        default=False,
        description="Whether this node represents a solution to the problem.",
    )


class BranchEvaluationItem(BaseModel):
    """Input model for the evaluate_branch tool."""

    branch_id: str = Field(..., description="Identifier for the branch to evaluate")
    score: float = Field(
        ...,
        ge=0,
        le=100,
        description="Evaluation score from 0-100 (higher is better)",
    )
    reasoning: str = Field(
        ...,
        description="Explanation of why this score was assigned. Be specific about "
        "what makes this branch promising or not.",
    )
    recommendation: Literal["continue", "prune", "merge", "explore_deeper"] = Field(
        ...,
        description=(
            "Recommended action: 'continue' to keep exploring, 'prune' if this is a dead end, "
            "'merge' if insights should be combined with another branch, "
            "'explore_deeper' if this path needs more depth before evaluation"
        ),
    )
