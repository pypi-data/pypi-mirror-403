"""Storage abstraction for todo items."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from .types import Todo

if TYPE_CHECKING:
    from .._shared.metrics import UsageMetrics


@runtime_checkable
class TodoStorageProtocol(Protocol):
    """Protocol for todo storage implementations.

    Any class that has a `todos` property (read/write) implementing
    `list[Todo]` can be used as storage for the todo toolset.

    Example:
        ```python
        class MyCustomStorage:
            def __init__(self):
                self._todos: list[Todo] = []

            @property
            def todos(self) -> list[Todo]:
                return self._todos

            @todos.setter
            def todos(self, value: list[Todo]) -> None:
                self._todos = value
        ```
    """

    @property
    def todos(self) -> list[Todo]:
        """Get the current list of todos."""
        ...

    @todos.setter
    def todos(self, value: list[Todo]) -> None:
        """Set the list of todos."""
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
            item_id: ID of the item (todo_id)
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
class TodoStorage:
    """Default in-memory todo storage.

    Simple implementation that stores todos in memory.
    Use this for standalone agents or testing.

    Example:
        ```python
        from pydantic_ai_toolsets import create_todo_toolset, TodoStorage

        storage = TodoStorage()
        toolset = create_todo_toolset(storage=storage)

        # After agent runs, access todos directly
        print(storage.todos)

        # With metrics tracking
        storage = TodoStorage(track_usage=True)
        toolset = create_todo_toolset(storage=storage)
        print(storage.metrics.total_tokens())
        ```
    """

    _todos: list[Todo] = field(default_factory=list)
    _metrics: UsageMetrics | None = field(default=None)
    _links: dict[str, list[str]] = field(default_factory=dict)  # item_id -> list of link IDs
    _linked_from: list[str] = field(default_factory=list)  # list of link IDs where this storage is target

    def __init__(self, *, track_usage: bool = False) -> None:
        """Initialize storage with optional metrics tracking.

        Args:
            track_usage: If True, enables usage metrics collection.
        """
        self._todos = []
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
    def todos(self) -> list[Todo]:
        """Get the current list of todos."""
        return self._todos

    @todos.setter
    def todos(self, value: list[Todo]) -> None:
        """Set the list of todos."""
        self._todos = value

    @property
    def metrics(self) -> UsageMetrics | None:
        """Get usage metrics if tracking is enabled."""
        return self._metrics

    def get_statistics(self) -> dict[str, int | float]:
        """Get summary statistics about todos.

        Returns:
            Dictionary with todo counts and completion metrics.
        """
        total = len(self._todos)
        pending = sum(1 for t in self._todos if t.status == "pending")
        in_progress = sum(1 for t in self._todos if t.status == "in_progress")
        completed = sum(1 for t in self._todos if t.status == "completed")
        completion_rate = completed / total if total > 0 else 0.0

        return {
            "total_todos": total,
            "pending": pending,
            "in_progress": in_progress,
            "completed": completed,
            "completion_rate": completion_rate,
        }

    def summary(self) -> dict[str, Any]:
        """Get comprehensive JSON summary of storage state and metrics.

        Returns:
            Dictionary containing storage state, statistics, and usage metrics.
        """
        summary_dict: dict[str, Any] = {
            "toolset": "to_do",
            "statistics": self.get_statistics(),
        }

        # Add storage-specific data
        summary_dict["storage"] = {
            "todos": [
                {
                    "content": todo.content,
                    "status": todo.status,
                }
                for todo in self._todos
            ],
        }

        # Add metrics if available
        if self._metrics:
            summary_dict["usage_metrics"] = self._metrics.to_dict()

        return summary_dict

    def clear(self) -> None:
        """Clear all todos and reset metrics."""
        self._todos.clear()
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
            item_id: ID of the todo item
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
            Formatted string summary of todos.
        """
        stats = self.get_statistics()
        lines: list[str] = []
        lines.append(f"Todo: {stats['total_todos']} tasks ({stats['pending']} pending, {stats['in_progress']} in progress, {stats['completed']} completed)")
        if stats["completion_rate"] > 0:
            lines.append(f"  - Completion rate: {stats['completion_rate']:.1%}")
        if self._todos:
            latest_todo = self._todos[-1]
            lines.append(f"  Latest: {latest_todo.content} [{latest_todo.status}]")
        return "\n".join(lines)

    def get_outputs_for_linking(self) -> list[dict[str, str]]:
        """Get list of linkable items with their IDs and descriptions.

        Returns:
            List of dictionaries with 'id' and 'description' keys for todos.
        """
        linkable_items: list[dict[str, str]] = []
        for i, todo in enumerate(self._todos):
            item_id = todo.todo_id
            description = f"Todo #{i+1} [{todo.status}]: {todo.content}"
            linkable_items.append({"id": item_id, "description": description})
        return linkable_items
