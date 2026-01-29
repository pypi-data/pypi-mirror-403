"""Storage abstraction for Monte Carlo Tree Search."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from .types import MCTSNode

if TYPE_CHECKING:
    from .._shared.metrics import UsageMetrics


@runtime_checkable
class MCTSStorageProtocol(Protocol):
    """Protocol for MCTS storage implementations.

    Any class that has a `nodes` property can be used
    as storage for the MCTS toolset.

    Example:
        ```python
        class MyCustomStorage:
            def __init__(self):
                self._nodes: dict[str, MCTSNode] = {}

            @property
            def nodes(self) -> dict[str, MCTSNode]:
                return self._nodes

            @nodes.setter
            def nodes(self, value: MCTSNode) -> None:
                self._nodes[value.node_id] = value
        ```
    """

    @property
    def nodes(self) -> dict[str, MCTSNode]:
        """Get the current dictionary of nodes (node_id -> MCTSNode)."""
        ...

    @nodes.setter
    def nodes(self, value: MCTSNode) -> None:
        """Add or update a node in the dictionary."""
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
            item_id: ID of the item (node_id)
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
class MCTSStorage:
    """Default in-memory MCTS storage.

    Simple implementation that stores nodes in memory.
    Use this for standalone agents or testing.

    Example:
        ```python
        from pydantic_ai_toolsets import create_mcts_toolset, MCTSStorage

        storage = MCTSStorage()
        toolset = create_mcts_toolset(storage=storage)

        # After agent runs, access nodes directly
        print(storage.nodes)

        # With metrics tracking
        storage = MCTSStorage(track_usage=True)
        toolset = create_mcts_toolset(storage=storage)
        print(storage.metrics.total_tokens())
        ```
    """

    _nodes: dict[str, MCTSNode] = field(default_factory=dict)
    _metrics: UsageMetrics | None = field(default=None)
    _iteration_count: int = field(default=0)
    _links: dict[str, list[str]] = field(default_factory=dict)  # item_id -> list of link IDs
    _linked_from: list[str] = field(default_factory=list)  # list of link IDs where this storage is target

    def __init__(self, *, track_usage: bool = False) -> None:
        """Initialize storage with optional metrics tracking.

        Args:
            track_usage: If True, enables usage metrics collection.
        """
        self._nodes = {}
        self._metrics = None
        self._iteration_count = 0
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
    def nodes(self) -> dict[str, MCTSNode]:
        """Get the current dictionary of nodes."""
        return self._nodes

    @nodes.setter
    def nodes(self, value: MCTSNode) -> None:
        """Add or update a node in the dictionary."""
        self._nodes[value.node_id] = value

    @property
    def metrics(self) -> UsageMetrics | None:
        """Get usage metrics if tracking is enabled."""
        return self._metrics

    @property
    def iteration_count(self) -> int:
        """Get the number of MCTS iterations performed."""
        return self._iteration_count

    def increment_iteration(self) -> None:
        """Increment the iteration counter."""
        self._iteration_count += 1

    def get_statistics(self) -> dict[str, int | float]:
        """Get summary statistics about the MCTS tree.

        Returns:
            Dictionary with node counts and tree metrics.
        """
        total = len(self._nodes)
        expanded = sum(1 for n in self._nodes.values() if n.is_expanded)
        terminal = sum(1 for n in self._nodes.values() if n.is_terminal)
        max_depth = max((n.depth for n in self._nodes.values()), default=0)
        total_visits = sum(n.visits for n in self._nodes.values())
        total_wins = sum(n.wins for n in self._nodes.values())

        return {
            "total_nodes": total,
            "expanded_nodes": expanded,
            "terminal_nodes": terminal,
            "max_depth": max_depth,
            "total_visits": total_visits,
            "total_wins": total_wins,
            "iterations": self._iteration_count,
        }

    def get_ucb1_stats(self) -> list[tuple[str, float, int, float]]:
        """Get UCB1 statistics for all nodes.

        Returns:
            List of (node_id, win_rate, visits, ucb1_value) tuples.
            UCB1 calculated with c=sqrt(2).
        """
        import math

        results: list[tuple[str, float, int, float]] = []
        root = next((n for n in self._nodes.values() if n.parent_id is None), None)
        if not root or root.visits == 0:
            return results

        c = math.sqrt(2)
        for node in self._nodes.values():
            if node.visits == 0:
                continue
            win_rate = node.wins / node.visits
            exploration = c * math.sqrt(math.log(root.visits) / node.visits)
            ucb1 = win_rate + exploration
            results.append((node.node_id, win_rate, node.visits, ucb1))

        results.sort(key=lambda x: x[3], reverse=True)
        return results

    def summary(self) -> dict[str, Any]:
        """Get comprehensive JSON summary of storage state and metrics.

        Returns:
            Dictionary containing storage state, statistics, and usage metrics.
        """
        summary_dict: dict[str, Any] = {
            "toolset": "monte_carlo_reasoning",
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
                    "is_expanded": node.is_expanded,
                    "is_terminal": node.is_terminal,
                    "visits": node.visits,
                    "wins": node.wins,
                }
                for node_id, node in self._nodes.items()
            },
            "iteration_count": self._iteration_count,
        }

        # Add metrics if available
        if self._metrics:
            summary_dict["usage_metrics"] = self._metrics.to_dict()

        return summary_dict

    def clear(self) -> None:
        """Clear all nodes and reset metrics."""
        self._nodes.clear()
        self._iteration_count = 0
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
            item_id: ID of the item (node_id)
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
            Formatted string summary of nodes and iterations.
        """
        stats = self.get_statistics()
        lines: list[str] = []
        lines.append(f"MCTS: {stats['total_nodes']} nodes, {stats['total_iterations']} iterations")
        if stats.get("best_node_id"):
            lines.append(f"  - Best node: {stats['best_node_id']}")
        if stats.get("max_depth", 0) > 0:
            lines.append(f"  - Max depth: {stats['max_depth']}")
        if self._nodes:
            root_node = self._nodes.get("root")
            if root_node:
                lines.append(f"  Root node visits: {root_node.visits}, wins: {root_node.wins}")
        return "\n".join(lines)

    def get_outputs_for_linking(self) -> list[dict[str, str]]:
        """Get list of linkable items with their IDs and descriptions.

        Returns:
            List of dictionaries with 'id' and 'description' keys for nodes.
        """
        linkable_items: list[dict[str, str]] = []
        for node_id, node in self._nodes.items():
            description = f"Node {node_id}: visits={node.visits}, wins={node.wins}"
            if node.action:
                description += f", action={node.action}"
            if node.is_terminal:
                description += " [TERMINAL]"
            linkable_items.append({"id": node_id, "description": description})
        return linkable_items
