"""Type definitions for pydantic-ai-got."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class GraphNode(BaseModel):
    """A node in a graph of thoughts execution.

    Each node represents a reasoning state. Nodes form a directed graph structure
    where edges represent dependencies, logical connections, or information flow.

    Attributes:
        node_id: Unique identifier for this node.
        content: The reasoning content at this node.
        evaluation_score: Optional score evaluating this node (0-100).
        is_solution: Whether this node represents a solution.
        status: Current status of this node.
        aggregated_from: List of node IDs whose insights were aggregated into this node.
        refined_from: Node ID that this node refines (if any).
        refinement_count: Number of times this node has been refined.
    """

    node_id: str
    content: str
    evaluation_score: float | None = None
    is_solution: bool = False
    status: Literal["active", "completed", "pruned"] = "active"
    aggregated_from: list[str] = Field(default_factory=list)
    refined_from: str | None = None
    refinement_count: int = 0


class GraphEdge(BaseModel):
    """An edge in a graph of thoughts execution.

    Edges represent dependencies, logical connections, or information flow
    between nodes. They form a directed graph (DAG or with cycles).

    Attributes:
        edge_id: Unique identifier for this edge.
        source_id: ID of the source node.
        target_id: ID of the target node.
        edge_type: Type of connection (dependency, aggregation, refinement, etc.).
        weight: Optional weight indicating strength/importance of the connection.
    """

    edge_id: str
    source_id: str
    target_id: str
    edge_type: Literal["dependency", "aggregation", "refinement", "reference", "merge"] = (
        "dependency"
    )
    weight: float | None = None


class NodeEvaluation(BaseModel):
    """Evaluation of a node in the graph.

    Used to assess the quality and relevance of individual nodes.

    Attributes:
        node_id: Identifier for the node being evaluated.
        score: Evaluation score (0-100, higher is better).
        reasoning: Explanation of why this score was assigned.
        recommendation: Recommended action for this node.
    """

    node_id: str
    score: float = Field(..., ge=0, le=100, description="Evaluation score from 0-100")
    reasoning: str = Field(..., description="Explanation of why this score was assigned")
    recommendation: Literal["keep", "refine", "aggregate", "prune"] = Field(
        ...,
        description="Recommended action: keep as-is, refine for improvement, "
        "aggregate with others, or prune as not useful",
    )


class NodeItem(BaseModel):
    """Input model for the create_node tool.

    This is the model that agents use when calling create_node.
    """

    content: str = Field(
        ...,
        description=(
            "The reasoning content at this node. Should represent a specific "
            "reasoning state or approach to the problem."
        ),
    )
    is_solution: bool = Field(
        default=False,
        description="Whether this node represents a solution to the problem.",
    )


class EdgeItem(BaseModel):
    """Input model for the create_edge tool."""

    source_id: str = Field(..., description="ID of the source node")
    target_id: str = Field(..., description="ID of the target node")
    edge_type: Literal["dependency", "aggregation", "refinement", "reference", "merge"] = Field(
        default="dependency",
        description=(
            "Type of connection: 'dependency' (source depends on target), "
            "'aggregation' (target aggregates source), 'refinement' (target refines source), "
            "'reference' (source references target), 'merge' (nodes are merged)"
        ),
    )
    weight: float | None = Field(
        default=None,
        ge=0,
        le=1,
        description="Optional weight indicating strength/importance (0-1, higher is stronger)",
    )


class AggregateItem(BaseModel):
    """Input model for the aggregate_nodes tool."""

    source_node_ids: list[str] = Field(
        ...,
        description="List of node IDs whose insights should be aggregated",
    )
    aggregated_content: str = Field(
        ...,
        description="Content of the new aggregated node combining insights from source nodes",
    )
    is_solution: bool = Field(
        default=False,
        description="Whether the aggregated node represents a solution",
    )


class RefineItem(BaseModel):
    """Input model for the refine_node tool."""

    node_id: str = Field(..., description="ID of the node to refine")
    refined_content: str = Field(
        ...,
        description="Improved/refined content for the node",
    )
    is_solution: bool = Field(
        default=False,
        description="Whether the refined node represents a solution",
    )


class NodeEvaluationItem(BaseModel):
    """Input model for the evaluate_node tool."""

    node_id: str = Field(..., description="Identifier for the node to evaluate")
    score: float = Field(
        ...,
        ge=0,
        le=100,
        description="Evaluation score from 0-100 (higher is better)",
    )
    reasoning: str = Field(
        ...,
        description="Explanation of why this score was assigned. Be specific about "
        "what makes this node valuable or not.",
    )
    recommendation: Literal["keep", "refine", "aggregate", "prune"] = Field(
        ...,
        description=(
            "Recommended action: 'keep' to maintain as-is, 'refine' if it needs improvement, "
            "'aggregate' if it should be combined with others, 'prune' if it's not useful"
        ),
    )

