"""Storage abstraction for graph of thoughts."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from .types import GraphEdge, GraphNode, NodeEvaluation

if TYPE_CHECKING:
    from .._shared.metrics import UsageMetrics


@runtime_checkable
class GoTStorageProtocol(Protocol):
    """Protocol for graph of thoughts storage implementations.

    Any class that has `nodes`, `edges`, and `evaluations` properties can be used
    as storage for the GoT toolset.

    Example:
        ```python
        class MyCustomStorage:
            def __init__(self):
                self._nodes: dict[str, GraphNode] = {}
                self._edges: dict[str, GraphEdge] = {}
                self._evaluations: dict[str, NodeEvaluation] = {}

            @property
            def nodes(self) -> dict[str, GraphNode]:
                return self._nodes

            @nodes.setter
            def nodes(self, value: GraphNode) -> None:
                self._nodes[value.node_id] = value

            @property
            def edges(self) -> dict[str, GraphEdge]:
                return self._edges

            @edges.setter
            def edges(self, value: GraphEdge) -> None:
                self._edges[value.edge_id] = value

            @property
            def evaluations(self) -> dict[str, NodeEvaluation]:
                return self._evaluations

            @evaluations.setter
            def evaluations(self, value: NodeEvaluation) -> None:
                self._evaluations[value.node_id] = value
        ```
    """

    @property
    def nodes(self) -> dict[str, GraphNode]:
        """Get the current dictionary of nodes (node_id -> GraphNode)."""
        ...

    @nodes.setter
    def nodes(self, value: GraphNode) -> None:
        """Add or update a node in the dictionary."""
        ...

    @property
    def edges(self) -> dict[str, GraphEdge]:
        """Get the current dictionary of edges (edge_id -> GraphEdge)."""
        ...

    @edges.setter
    def edges(self, value: GraphEdge) -> None:
        """Add or update an edge in the dictionary."""
        ...

    @property
    def evaluations(self) -> dict[str, NodeEvaluation]:
        """Get the current dictionary of node evaluations (node_id -> NodeEvaluation)."""
        ...

    @evaluations.setter
    def evaluations(self, value: NodeEvaluation) -> None:
        """Add or update a node evaluation in the dictionary."""
        ...

    def summary(self) -> dict[str, Any]:
        """Get comprehensive JSON summary of storage state and metrics.
        
        Returns:
            Dictionary containing storage state, statistics, and usage metrics.
        """
        ...

    def add_link(self, item_id: str, link_id: str) -> None:
        """Add an outgoing link for an item.
        
        Args:
            item_id: ID of the item (node_id, edge_id, or evaluation_id)
            link_id: ID of the link
        """
        ...

    def add_linked_from(self, link_id: str) -> None:
        """Add an incoming link.
        
        Args:
            link_id: ID of the link
        """
        ...


@dataclass
class GoTStorage:
    """Default in-memory graph of thoughts storage.

    Simple implementation that stores nodes, edges, and evaluations in memory.
    Use this for standalone agents or testing.

    Example:
        ```python
        from pydantic_ai_toolsets import create_got_toolset, GoTStorage

        storage = GoTStorage()
        toolset = create_got_toolset(storage=storage)

        # After agent runs, access nodes, edges, and evaluations directly
        print(storage.nodes)
        print(storage.edges)
        print(storage.evaluations)

        # With metrics tracking
        storage = GoTStorage(track_usage=True)
        toolset = create_got_toolset(storage=storage)
        print(storage.metrics.total_tokens())
        ```
    """

    _nodes: dict[str, GraphNode] = field(default_factory=dict)
    _edges: dict[str, GraphEdge] = field(default_factory=dict)
    _evaluations: dict[str, NodeEvaluation] = field(default_factory=dict)
    _metrics: UsageMetrics | None = field(default=None)
    _links: dict[str, list[str]] = field(default_factory=dict)  # item_id -> list of link IDs
    _linked_from: list[str] = field(default_factory=list)  # list of link IDs where this storage is target

    def __init__(self, *, track_usage: bool = False) -> None:
        """Initialize storage with optional metrics tracking.

        Args:
            track_usage: If True, enables usage metrics collection.
        """
        self._nodes = {}
        self._edges = {}
        self._evaluations = {}
        self._metrics = None
        self._links = {}
        self._linked_from = []
        if track_usage:
            import os

            toolsets_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if toolsets_dir not in sys.path:
                sys.path.insert(0, toolsets_dir)
            from .._shared.metrics import UsageMetrics

            self._metrics = UsageMetrics()

    @property
    def nodes(self) -> dict[str, GraphNode]:
        """Get the current dictionary of nodes."""
        return self._nodes

    @nodes.setter
    def nodes(self, value: GraphNode) -> None:
        """Add or update a node in the dictionary."""
        self._nodes[value.node_id] = value

    @property
    def edges(self) -> dict[str, GraphEdge]:
        """Get the current dictionary of edges."""
        return self._edges

    @edges.setter
    def edges(self, value: GraphEdge) -> None:
        """Add or update an edge in the dictionary."""
        self._edges[value.edge_id] = value

    @property
    def evaluations(self) -> dict[str, NodeEvaluation]:
        """Get the current dictionary of node evaluations."""
        return self._evaluations

    @evaluations.setter
    def evaluations(self, value: NodeEvaluation) -> None:
        """Add or update a node evaluation in the dictionary."""
        self._evaluations[value.node_id] = value

    @property
    def metrics(self) -> UsageMetrics | None:
        """Get usage metrics if tracking is enabled."""
        return self._metrics

    def get_statistics(self) -> dict[str, int | float]:
        """Get summary statistics about the graph.

        Returns:
            Dictionary with node, edge, and evaluation counts.
        """
        total_nodes = len(self._nodes)
        active = sum(1 for n in self._nodes.values() if n.status == "active")
        pruned = sum(1 for n in self._nodes.values() if n.status == "pruned")
        solutions = sum(1 for n in self._nodes.values() if n.is_solution)
        aggregated = sum(1 for n in self._nodes.values() if n.aggregated_from)
        refined = sum(1 for n in self._nodes.values() if n.refinement_count > 0)

        # Edge statistics
        edges_by_type: dict[str, int] = {}
        for e in self._edges.values():
            edges_by_type[e.edge_type] = edges_by_type.get(e.edge_type, 0) + 1

        return {
            "total_nodes": total_nodes,
            "active_nodes": active,
            "pruned_nodes": pruned,
            "solution_nodes": solutions,
            "aggregated_nodes": aggregated,
            "refined_nodes": refined,
            "total_edges": len(self._edges),
            "edges_by_type": edges_by_type,
            "evaluations": len(self._evaluations),
        }

    def graph_complexity(self) -> dict[str, float]:
        """Calculate graph complexity metrics.

        Returns:
            Dictionary with complexity metrics (density, avg degree).
        """
        n_nodes = len(self._nodes)
        n_edges = len(self._edges)

        if n_nodes <= 1:
            return {"density": 0.0, "avg_degree": 0.0}

        # Density: actual edges / possible edges
        max_edges = n_nodes * (n_nodes - 1)
        density = n_edges / max_edges if max_edges > 0 else 0.0

        # Average degree
        avg_degree = (2 * n_edges) / n_nodes if n_nodes > 0 else 0.0

        return {"density": density, "avg_degree": avg_degree}

    def summary(self) -> dict[str, Any]:
        """Get comprehensive JSON summary of storage state and metrics.

        Returns:
            Dictionary containing storage state, statistics, and usage metrics.
        """
        summary_dict: dict[str, Any] = {
            "toolset": "graph_of_thought_reasoning",
            "statistics": self.get_statistics(),
        }

        # Add storage-specific data
        summary_dict["storage"] = {
            "nodes": {
                node_id: {
                    "node_id": node.node_id,
                    "content": node.content,
                    "status": node.status,
                    "is_solution": node.is_solution,
                    "aggregated_from": node.aggregated_from,
                    "refinement_count": node.refinement_count,
                }
                for node_id, node in self._nodes.items()
            },
            "edges": {
                edge_id: {
                    "edge_id": edge.edge_id,
                    "source_id": edge.source_id,
                    "target_id": edge.target_id,
                    "edge_type": edge.edge_type,
                }
                for edge_id, edge in self._edges.items()
            },
            "evaluations": {
                node_id: {
                    "node_id": eval.node_id,
                    "score": eval.score,
                    "reasoning": eval.reasoning,
                }
                for node_id, eval in self._evaluations.items()
            },
        }

        # Add metrics if available
        if self._metrics:
            summary_dict["usage_metrics"] = self._metrics.to_dict()

        return summary_dict

    def clear(self) -> None:
        """Clear all nodes, edges, evaluations, and reset metrics."""
        self._nodes.clear()
        self._edges.clear()
        self._evaluations.clear()
        self._links.clear()
        self._linked_from.clear()
        if self._metrics:
            self._metrics.clear()

    @property
    def links(self) -> dict[str, list[str]]:
        """Get outgoing links dictionary (item_id -> list of link IDs)."""
        return self._links

    @property
    def linked_from(self) -> list[str]:
        """Get incoming links list (link IDs where this storage is target)."""
        return self._linked_from

    def add_link(self, item_id: str, link_id: str) -> None:
        """Add an outgoing link for an item.

        Args:
            item_id: ID of the item (node_id, edge_id, or evaluation_id)
            link_id: ID of the link
        """
        if item_id not in self._links:
            self._links[item_id] = []
        if link_id not in self._links[item_id]:
            self._links[item_id].append(link_id)

    def add_linked_from(self, link_id: str) -> None:
        """Add an incoming link.

        Args:
            link_id: ID of the link
        """
        if link_id not in self._linked_from:
            self._linked_from.append(link_id)

    def get_state_summary(self) -> str:
        """Get a human-readable summary of the storage state.

        Returns:
            Formatted string summary of nodes, edges, and evaluations.
        """
        stats = self.get_statistics()
        lines: list[str] = []
        lines.append(f"Graph of Thought: {stats['total_nodes']} nodes, {stats['total_edges']} edges, {stats['evaluations']} evaluations")
        if stats.get("solution_nodes", 0) > 0:
            lines.append(f"  - {stats['solution_nodes']} solution nodes")
        if stats.get("active_nodes", 0) > 0:
            lines.append(f"  - {stats['active_nodes']} active nodes")
        if self._nodes:
            latest_node = list(self._nodes.values())[-1]
            lines.append(f"  Latest node: {latest_node.content}")
        return "\n".join(lines)

    def get_outputs_for_linking(self) -> list[dict[str, str]]:
        """Get list of linkable items with their IDs and descriptions.

        Returns:
            List of dictionaries with 'id' and 'description' keys for nodes, edges, and evaluations.
        """
        linkable_items: list[dict[str, str]] = []
        # Add nodes
        for node_id, node in self._nodes.items():
            description = f"Node {node_id}: {node.content}"
            if node.is_solution:
                description += " [SOLUTION]"
            linkable_items.append({"id": node_id, "description": description})
        # Add edges
        for edge_id, edge in self._edges.items():
            description = f"Edge {edge_id}: {edge.source_id} → {edge.target_id} ({edge.edge_type})"
            linkable_items.append({"id": edge_id, "description": description})
        # Add evaluations
        for node_id, evaluation in self._evaluations.items():
            description = f"Evaluation for node {node_id}: score={evaluation.score}"
            linkable_items.append({"id": node_id, "description": description})
        return linkable_items
