"""Type definitions for pydantic-ai-mcts."""

from __future__ import annotations

from pydantic import BaseModel, Field


class MCTSNode(BaseModel):
    """A node in a Monte Carlo Tree Search execution.

    Each node represents a state in the search tree. Nodes track visit counts,
    win/reward totals, and maintain parent-child relationships for the tree structure.

    Attributes:
        node_id: Unique identifier for this node.
        content: The reasoning/state content at this node.
        visits: Number of times this node has been visited.
        wins: Total reward/wins accumulated from simulations passing through this node.
        parent_id: ID of the parent node (None for root node).
        children_ids: List of child node IDs.
        is_terminal: Whether this node represents a terminal/solution state.
        is_expanded: Whether this node has been expanded (has children).
        depth: Depth level in the tree (0 for root).
    """

    node_id: str
    content: str
    visits: int = Field(default=0, ge=0, description="Number of times this node has been visited")
    wins: float = Field(
        default=0.0, ge=0.0, description="Total reward/wins accumulated from simulations"
    )
    parent_id: str | None = None
    children_ids: list[str] = Field(default_factory=list, description="List of child node IDs")
    is_terminal: bool = False
    is_expanded: bool = False
    depth: int = Field(default=0, ge=0, description="Depth level in the search tree")


class SelectNodeItem(BaseModel):
    """Input model for the select_node tool.

    Allows manual selection of a node, or automatic selection using UCB1.
    """

    node_id: str | None = Field(
        default=None,
        description=(
            "Optional node ID to select. If None, selects using UCB1 from root. "
            "If provided, selects that specific node."
        ),
    )
    exploration_constant: float = Field(
        default=1.414,  # sqrt(2)
        ge=0.0,
        description=(
            "Exploration constant (c) for UCB1 formula. "
            "Higher values favor exploration. Default is sqrt(2) ≈ 1.414."
        ),
    )


class ExpandNodeItem(BaseModel):
    """Input model for the expand_node tool."""

    node_id: str = Field(..., description="ID of the node to expand")
    children: list[str] = Field(
        ...,
        min_length=1,
        description=(
            "List of child node contents. Each string represents a possible "
            "next state/action from this node."
        ),
    )
    is_terminal: list[bool] = Field(
        default_factory=lambda: [],
        description=(
            "Optional list indicating which children are terminal states. "
            "If provided, must match length of children."
        ),
    )


class SimulateItem(BaseModel):
    """Input model for the simulate tool."""

    node_id: str = Field(..., description="ID of the node to start simulation from")
    simulation_result: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description=(
            "Result of the simulation (reward/win value). "
            "Should be between 0.0 (loss) and 1.0 (win). "
            "Can represent partial rewards for intermediate states."
        ),
    )
    simulation_path: list[str] = Field(
        default_factory=list,
        description=(
            "Optional list of node IDs representing the simulation path. "
            "If provided, backpropagation will update statistics for all nodes in the path."
        ),
    )


class BackpropagateItem(BaseModel):
    """Input model for the backpropagate tool."""

    node_id: str = Field(
        ..., description="ID of the node where simulation ended (terminal or leaf)"
    )
    reward: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description=(
            "Reward/win value from the simulation (0.0 to 1.0). "
            "Higher values indicate better outcomes."
        ),
    )
