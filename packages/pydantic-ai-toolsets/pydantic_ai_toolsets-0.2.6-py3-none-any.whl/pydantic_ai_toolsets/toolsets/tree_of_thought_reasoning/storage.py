"""Storage abstraction for tree of thoughts."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from .types import BranchEvaluation, ThoughtNode

if TYPE_CHECKING:
    from .._shared.metrics import UsageMetrics


@runtime_checkable
class ToTStorageProtocol(Protocol):
    """Protocol for tree of thoughts storage implementations.

    Any class that has `nodes` and `evaluations` properties can be used
    as storage for the ToT toolset.

    Example:
        ```python
        class MyCustomStorage:
            def __init__(self):
                self._nodes: dict[str, ThoughtNode] = {}
                self._evaluations: dict[str, BranchEvaluation] = {}

            @property
            def nodes(self) -> dict[str, ThoughtNode]:
                return self._nodes

            @nodes.setter
            def nodes(self, value: ThoughtNode) -> None:
                self._nodes[value.node_id] = value

            @property
            def evaluations(self) -> dict[str, BranchEvaluation]:
                return self._evaluations

            @evaluations.setter
            def evaluations(self, value: BranchEvaluation) -> None:
                self._evaluations[value.branch_id] = value
        ```
    """

    @property
    def nodes(self) -> dict[str, ThoughtNode]:
        """Get the current dictionary of nodes (node_id -> ThoughtNode)."""
        ...

    @nodes.setter
    def nodes(self, value: ThoughtNode) -> None:
        """Add or update a node in the dictionary."""
        ...

    @property
    def evaluations(self) -> dict[str, BranchEvaluation]:
        """Get the current dictionary of branch evaluations (branch_id -> BranchEvaluation)."""
        ...

    @evaluations.setter
    def evaluations(self, value: BranchEvaluation) -> None:
        """Add or update a branch evaluation in the dictionary."""
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
            item_id: ID of the item (node_id or evaluation_id)
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
class ToTStorage:
    """Default in-memory tree of thoughts storage.

    Simple implementation that stores nodes and evaluations in memory.
    Use this for standalone agents or testing.

    Example:
        ```python
        from pydantic_ai_toolsets import create_tot_toolset, ToTStorage

        storage = ToTStorage()
        toolset = create_tot_toolset(storage=storage)

        # After agent runs, access nodes and evaluations directly
        print(storage.nodes)
        print(storage.evaluations)

        # With metrics tracking
        storage = ToTStorage(track_usage=True)
        toolset = create_tot_toolset(storage=storage)
        print(storage.metrics.total_tokens())
        ```
    """

    _nodes: dict[str, ThoughtNode] = field(default_factory=dict)
    _evaluations: dict[str, BranchEvaluation] = field(default_factory=dict)
    _metrics: UsageMetrics | None = field(default=None)
    _links: dict[str, list[str]] = field(default_factory=dict)  # item_id -> list of link IDs
    _linked_from: list[str] = field(default_factory=list)  # list of link IDs where this storage is target

    def __init__(self, *, track_usage: bool = False) -> None:
        """Initialize storage with optional metrics tracking.

        Args:
            track_usage: If True, enables usage metrics collection.
        """
        self._nodes = {}
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
    def nodes(self) -> dict[str, ThoughtNode]:
        """Get the current dictionary of nodes."""
        return self._nodes

    @nodes.setter
    def nodes(self, value: ThoughtNode) -> None:
        """Add or update a node in the dictionary."""
        self._nodes[value.node_id] = value

    @property
    def evaluations(self) -> dict[str, BranchEvaluation]:
        """Get the current dictionary of branch evaluations."""
        return self._evaluations

    @evaluations.setter
    def evaluations(self, value: BranchEvaluation) -> None:
        """Add or update a branch evaluation in the dictionary."""
        self._evaluations[value.branch_id] = value

    @property
    def metrics(self) -> UsageMetrics | None:
        """Get usage metrics if tracking is enabled."""
        return self._metrics

    def get_statistics(self) -> dict[str, int | float]:
        """Get summary statistics about the tree.

        Returns:
            Dictionary with node counts and tree metrics.
        """
        total_nodes = len(self._nodes)
        active = sum(1 for n in self._nodes.values() if n.status == "active")
        pruned = sum(1 for n in self._nodes.values() if n.status == "pruned")
        merged = sum(1 for n in self._nodes.values() if n.status == "merged")
        solutions = sum(1 for n in self._nodes.values() if n.is_solution)
        branches = len(set(n.branch_id for n in self._nodes.values() if n.branch_id))
        max_depth = max((n.depth for n in self._nodes.values()), default=0)

        return {
            "total_nodes": total_nodes,
            "active_nodes": active,
            "pruned_nodes": pruned,
            "merged_nodes": merged,
            "solution_nodes": solutions,
            "branches": branches,
            "max_depth": max_depth,
            "evaluations": len(self._evaluations),
        }

    def depth_statistics(self) -> dict[int, int]:
        """Get node count at each depth level.

        Returns:
            Dictionary mapping depth to node count.
        """
        stats: dict[int, int] = {}
        for node in self._nodes.values():
            stats[node.depth] = stats.get(node.depth, 0) + 1
        return dict(sorted(stats.items()))

    def summary(self) -> dict[str, Any]:
        """Get comprehensive JSON summary of storage state and metrics.

        Returns:
            Dictionary containing storage state, statistics, and usage metrics.
        """
        summary_dict: dict[str, Any] = {
            "toolset": "tree_of_thought_reasoning",
            "statistics": self.get_statistics(),
        }

        # Add storage-specific data
        summary_dict["storage"] = {
            "nodes": {
                node_id: {
                    "node_id": node.node_id,
                    "content": node.content,
                    "depth": node.depth,
                    "parent_id": node.parent_id,
                    "branch_id": node.branch_id,
                    "status": node.status,
                    "is_solution": node.is_solution,
                }
                for node_id, node in self._nodes.items()
            },
            "evaluations": {
                branch_id: {
                    "branch_id": eval.branch_id,
                    "node_id": eval.node_id,
                    "score": eval.score,
                    "reasoning": eval.reasoning,
                }
                for branch_id, eval in self._evaluations.items()
            },
        }

        # Add metrics if available
        if self._metrics:
            summary_dict["usage_metrics"] = self._metrics.to_dict()

        return summary_dict

    def clear(self) -> None:
        """Clear all nodes, evaluations, and reset metrics."""
        self._nodes.clear()
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
            item_id: ID of the item (node_id or evaluation_id)
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
            Formatted string summary of nodes and evaluations.
        """
        stats = self.get_statistics()
        lines: list[str] = []
        lines.append(f"Tree of Thought: {stats['total_nodes']} nodes, {stats['total_evaluations']} evaluations")
        if stats.get("solution_nodes", 0) > 0:
            lines.append(f"  - {stats['solution_nodes']} solution nodes")
        if stats.get("max_depth", 0) > 0:
            lines.append(f"  - Max depth: {stats['max_depth']}")
        if self._nodes:
            latest_node = list(self._nodes.values())[-1]
            lines.append(f"  Latest node: {latest_node.content}")
        return "\n".join(lines)

    def get_outputs_for_linking(self) -> list[dict[str, str]]:
        """Get list of linkable items with their IDs and descriptions.

        Returns:
            List of dictionaries with 'id' and 'description' keys for nodes and evaluations.
        """
        linkable_items: list[dict[str, str]] = []
        # Add nodes
        for node_id, node in self._nodes.items():
            description = f"Node {node_id}: {node.content}"
            if node.is_solution:
                description += " [SOLUTION]"
            linkable_items.append({"id": node_id, "description": description})
        # Add evaluations
        for branch_id, evaluation in self._evaluations.items():
            description = f"Evaluation for branch {branch_id}: score={evaluation.score}"
            linkable_items.append({"id": branch_id, "description": description})
        return linkable_items
