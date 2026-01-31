"""Storage abstraction for chain of thoughts."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from .types import Thought

if TYPE_CHECKING:
    from .._shared.metrics import UsageMetrics


@runtime_checkable
class CoTStorageProtocol(Protocol):
    """Protocol for chain of thoughts storage implementations.

    Any class that has a `thoughts` property (read returns list, write appends Thought)
    can be used as storage for the CoT toolset.

    Example:
        ```python
        class MyCustomStorage:
            def __init__(self):
                self._thoughts: list[Thought] = []

            @property
            def thoughts(self) -> list[Thought]:
                return self._thoughts

            @thoughts.setter
            def thoughts(self, value: Thought) -> None:
                self._thoughts.append(value)
        ```
    """

    @property
    def thoughts(self) -> list[Thought]:
        """Get the current list of thoughts."""
        ...

    @thoughts.setter
    def thoughts(self, value: Thought) -> None:
        """Append a single thought to the list."""
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
            item_id: ID of the item (e.g., thought number as string)
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
class CoTStorage:
    """Default in-memory chain of thoughts storage.

    Simple implementation that stores thoughts in memory.
    Use this for standalone agents or testing.

    Attributes:
        _thoughts: Internal list of recorded thoughts.
        _metrics: Optional usage metrics tracker (enabled via track_usage parameter).

    Example:
        ```python
        from pydantic_ai_toolsets import create_cot_toolset, CoTStorage

        storage = CoTStorage()
        toolset = create_cot_toolset(storage=storage)

        # After agent runs, access thoughts directly
        print(storage.thoughts)

        # With metrics tracking
        storage = CoTStorage(track_usage=True)
        toolset = create_cot_toolset(storage=storage)
        # After agent runs
        print(storage.metrics.total_tokens())
        ```
    """

    _thoughts: list[Thought] = field(default_factory=list)
    _metrics: UsageMetrics | None = field(default=None)
    _links: dict[str, list[str]] = field(default_factory=dict)  # item_id -> list of link IDs
    _linked_from: list[str] = field(default_factory=list)  # list of link IDs where this storage is target

    def __init__(self, *, track_usage: bool = False) -> None:
        """Initialize storage with optional metrics tracking.

        Args:
            track_usage: If True, enables usage metrics collection.
        """
        self._thoughts = []
        self._metrics = None
        self._links = {}
        self._linked_from = []
        if track_usage:
            # Import here to avoid circular imports and keep it optional
            # Add toolsets directory to path if needed
            import os

            from .._shared.metrics import UsageMetrics

            self._metrics = UsageMetrics()

    @property
    def thoughts(self) -> list[Thought]:
        """Get the current list of thoughts."""
        return self._thoughts

    @thoughts.setter
    def thoughts(self, value: Thought) -> None:
        """Append a single thought to the list."""
        self._thoughts.append(value)

    @property
    def metrics(self) -> UsageMetrics | None:
        """Get usage metrics if tracking is enabled.

        Returns:
            UsageMetrics instance if track_usage=True was set, otherwise None.
        """
        return self._metrics

    def get_statistics(self) -> dict[str, int | float]:
        """Get summary statistics about the chain of thoughts.

        Returns:
            Dictionary with thought counts and metadata.
        """
        total = len(self._thoughts)
        revisions = sum(1 for t in self._thoughts if t.is_revision)
        branches = len(set(t.branch_id for t in self._thoughts if t.branch_id))
        final = sum(1 for t in self._thoughts if not t.next_thought_needed)

        return {
            "total_thoughts": total,
            "revisions": revisions,
            "branches": branches,
            "final_thoughts": final,
        }

    def summary(self) -> dict[str, Any]:
        """Get comprehensive JSON summary of storage state and metrics.

        Returns:
            Dictionary containing storage state, statistics, and usage metrics.
        """
        summary_dict: dict[str, Any] = {
            "toolset": "chain_of_thought_reasoning",
            "statistics": self.get_statistics(),
        }

        # Add storage-specific data
        summary_dict["storage"] = {
            "thoughts": [
                {
                    "thought_number": thought.thought_number,
                    "thought": thought.thought,
                    "is_revision": thought.is_revision,
                    "revises_thought": thought.revises_thought,
                    "branch_id": thought.branch_id,
                    "branch_from_thought": thought.branch_from_thought,
                    "next_thought_needed": thought.next_thought_needed,
                }
                for thought in self._thoughts
            ],
        }

        # Add metrics if available
        if self._metrics:
            summary_dict["usage_metrics"] = self._metrics.to_dict()

        return summary_dict

    def clear(self) -> None:
        """Clear all thoughts and reset metrics."""
        self._thoughts.clear()
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
            item_id: ID of the item (e.g., thought number as string)
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
            Formatted string summary of thoughts and statistics.
        """
        stats = self.get_statistics()
        lines: list[str] = []
        lines.append(f"Chain of Thought: {stats['total_thoughts']} thoughts")
        if stats["revisions"] > 0:
            lines.append(f"  - {stats['revisions']} revisions")
        if stats["branches"] > 0:
            lines.append(f"  - {stats['branches']} branches")
        if stats["final_thoughts"] > 0:
            lines.append(f"  - {stats['final_thoughts']} final thoughts")
        if self._thoughts:
            lines.append(f"  Latest: {self._thoughts[-1].thought}")
        return "\n".join(lines)

    def get_outputs_for_linking(self) -> list[dict[str, str]]:
        """Get list of linkable items with their IDs and descriptions.

        Returns:
            List of dictionaries with 'id' and 'description' keys for each linkable thought.
        """
        linkable_items: list[dict[str, str]] = []
        for thought in self._thoughts:
            item_id = str(thought.thought_number)
            description = f"Thought #{thought.thought_number}: {thought.thought}"
            linkable_items.append({"id": item_id, "description": description})
        return linkable_items
