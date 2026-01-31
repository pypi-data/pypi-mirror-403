"""Storage abstraction for reflection."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from .types import Critique, ReflectionOutput

if TYPE_CHECKING:
    from .._shared.metrics import UsageMetrics


@runtime_checkable
class ReflectionStorageProtocol(Protocol):
    """Protocol for reflection storage implementations.

    Any class that has `outputs` and `critiques` properties can be used
    as storage for the reflection toolset.

    Example:
        ```python
        class MyCustomStorage:
            def __init__(self):
                self._outputs: dict[str, ReflectionOutput] = {}
                self._critiques: dict[str, Critique] = {}

            @property
            def outputs(self) -> dict[str, ReflectionOutput]:
                return self._outputs

            @outputs.setter
            def outputs(self, value: ReflectionOutput) -> None:
                self._outputs[value.output_id] = value

            @property
            def critiques(self) -> dict[str, Critique]:
                return self._critiques

            @critiques.setter
            def critiques(self, value: Critique) -> None:
                self._critiques[value.critique_id] = value
        ```
    """

    @property
    def outputs(self) -> dict[str, ReflectionOutput]:
        """Get the current dictionary of outputs (output_id -> ReflectionOutput)."""
        ...

    @outputs.setter
    def outputs(self, value: ReflectionOutput) -> None:
        """Add or update an output in the dictionary."""
        ...

    @property
    def critiques(self) -> dict[str, Critique]:
        """Get the current dictionary of critiques (critique_id -> Critique)."""
        ...

    @critiques.setter
    def critiques(self, value: Critique) -> None:
        """Add or update a critique in the dictionary."""
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
            item_id: ID of the item (output_id or critique_id)
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
class ReflectionStorage:
    """Default in-memory reflection storage.

    Simple implementation that stores outputs and critiques in memory.
    Use this for standalone agents or testing.

    Example:
        ```python
        from pydantic_ai_toolsets import create_reflection_toolset, ReflectionStorage

        storage = ReflectionStorage()
        toolset = create_reflection_toolset(storage=storage)

        # After agent runs, access outputs and critiques directly
        print(storage.outputs)
        print(storage.critiques)

        # With metrics tracking
        storage = ReflectionStorage(track_usage=True)
        toolset = create_reflection_toolset(storage=storage)
        print(storage.metrics.total_tokens())
        ```
    """

    _outputs: dict[str, ReflectionOutput] = field(default_factory=dict)
    _critiques: dict[str, Critique] = field(default_factory=dict)
    _metrics: UsageMetrics | None = field(default=None)
    _links: dict[str, list[str]] = field(default_factory=dict)  # item_id -> list of link IDs
    _linked_from: list[str] = field(default_factory=list)  # list of link IDs where this storage is target

    def __init__(self, *, track_usage: bool = False) -> None:
        """Initialize storage with optional metrics tracking.

        Args:
            track_usage: If True, enables usage metrics collection.
        """
        self._outputs = {}
        self._critiques = {}
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
    def outputs(self) -> dict[str, ReflectionOutput]:
        """Get the current dictionary of outputs."""
        return self._outputs

    @outputs.setter
    def outputs(self, value: ReflectionOutput) -> None:
        """Add or update an output in the dictionary."""
        self._outputs[value.output_id] = value

    @property
    def critiques(self) -> dict[str, Critique]:
        """Get the current dictionary of critiques."""
        return self._critiques

    @critiques.setter
    def critiques(self, value: Critique) -> None:
        """Add or update a critique in the dictionary."""
        self._critiques[value.critique_id] = value

    @property
    def metrics(self) -> UsageMetrics | None:
        """Get usage metrics if tracking is enabled."""
        return self._metrics

    def get_statistics(self) -> dict[str, int | float]:
        """Get summary statistics about reflection operations.

        Returns:
            Dictionary with output and critique counts.
        """
        total_outputs = len(self._outputs)
        final_outputs = sum(1 for o in self._outputs.values() if o.is_final)
        max_cycle = max((o.cycle for o in self._outputs.values()), default=0)
        avg_quality = None
        quality_scores = [o.quality_score for o in self._outputs.values() if o.quality_score is not None]
        if quality_scores:
            avg_quality = sum(quality_scores) / len(quality_scores)

        stats: dict[str, int | float] = {
            "total_outputs": total_outputs,
            "final_outputs": final_outputs,
            "max_cycle": max_cycle,
            "total_critiques": len(self._critiques),
        }
        if avg_quality is not None:
            stats["avg_quality_score"] = avg_quality

        return stats

    def summary(self) -> dict[str, Any]:
        """Get comprehensive JSON summary of storage state and metrics.

        Returns:
            Dictionary containing storage state, statistics, and usage metrics.
        """
        summary_dict: dict[str, Any] = {
            "toolset": "reflection",
            "statistics": self.get_statistics(),
        }

        # Add storage-specific data
        summary_dict["storage"] = {
            "outputs": {
                output_id: {
                    "output_id": output.output_id,
                    "content": output.content,
                    "cycle": output.cycle,
                    "is_final": output.is_final,
                    "quality_score": output.quality_score,
                }
                for output_id, output in self._outputs.items()
            },
            "critiques": {
                critique_id: {
                    "critique_id": critique.critique_id,
                    "output_id": critique.output_id,
                    "content": critique.content,
                    "aspects": critique.aspects,
                }
                for critique_id, critique in self._critiques.items()
            },
        }

        # Add metrics if available
        if self._metrics:
            summary_dict["usage_metrics"] = self._metrics.to_dict()

        return summary_dict

    def clear(self) -> None:
        """Clear all outputs, critiques, and reset metrics."""
        self._outputs.clear()
        self._critiques.clear()
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
            item_id: ID of the item (output_id or critique_id)
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
            Formatted string summary of outputs and critiques.
        """
        stats = self.get_statistics()
        lines: list[str] = []
        lines.append(f"Reflection: {stats['total_outputs']} outputs, {stats['total_critiques']} critiques")
        if stats["final_outputs"] > 0:
            lines.append(f"  - {stats['final_outputs']} final outputs")
        if stats["max_cycle"] > 0:
            lines.append(f"  - Max cycle: {stats['max_cycle']}")
        if self._outputs:
            latest_output = list(self._outputs.values())[-1]
            lines.append(f"  Latest output: {latest_output.content}")
        return "\n".join(lines)

    def get_outputs_for_linking(self) -> list[dict[str, str]]:
        """Get list of linkable items with their IDs and descriptions.

        Returns:
            List of dictionaries with 'id' and 'description' keys for outputs and critiques.
        """
        linkable_items: list[dict[str, str]] = []
        # Add outputs
        for output_id, output in self._outputs.items():
            description = f"Output {output_id} (cycle {output.cycle}): {output.content}"
            if output.is_final:
                description += " [FINAL]"
            linkable_items.append({"id": output_id, "description": description})
        # Add critiques
        for critique_id, critique in self._critiques.items():
            description = f"Critique {critique_id} for output {critique.output_id}: {critique.overall_assessment}"
            linkable_items.append({"id": critique_id, "description": description})
        return linkable_items
