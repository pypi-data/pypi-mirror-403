"""Storage abstraction for self-refinement."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from .types import Feedback, RefinementOutput

if TYPE_CHECKING:
    from .._shared.metrics import UsageMetrics


@runtime_checkable
class SelfRefineStorageProtocol(Protocol):
    """Protocol for self-refinement storage implementations.

    Any class that has `outputs` and `feedbacks` properties can be used
    as storage for the self-refinement toolset.

    Example:
        ```python
        class MyCustomStorage:
            def __init__(self):
                self._outputs: dict[str, RefinementOutput] = {}
                self._feedbacks: dict[str, Feedback] = {}

            @property
            def outputs(self) -> dict[str, RefinementOutput]:
                return self._outputs

            @outputs.setter
            def outputs(self, value: RefinementOutput) -> None:
                self._outputs[value.output_id] = value

            @property
            def feedbacks(self) -> dict[str, Feedback]:
                return self._feedbacks

            @feedbacks.setter
            def feedbacks(self, value: Feedback) -> None:
                self._feedbacks[value.feedback_id] = value
        ```
    """

    @property
    def outputs(self) -> dict[str, RefinementOutput]:
        """Get the current dictionary of outputs (output_id -> RefinementOutput)."""
        ...

    @outputs.setter
    def outputs(self, value: RefinementOutput) -> None:
        """Add or update an output in the dictionary."""
        ...

    @property
    def feedbacks(self) -> dict[str, Feedback]:
        """Get the current dictionary of feedbacks (feedback_id -> Feedback)."""
        ...

    @feedbacks.setter
    def feedbacks(self, value: Feedback) -> None:
        """Add or update a feedback in the dictionary."""
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
            item_id: ID of the item (output_id or feedback_id)
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
class SelfRefineStorage:
    """Default in-memory self-refinement storage.

    Simple implementation that stores outputs and feedbacks in memory.
    Use this for standalone agents or testing.

    Example:
        ```python
        from pydantic_ai_toolsets import create_self_refine_toolset, SelfRefineStorage

        storage = SelfRefineStorage()
        toolset = create_self_refine_toolset(storage=storage)

        # After agent runs, access outputs and feedbacks directly
        print(storage.outputs)
        print(storage.feedbacks)

        # With metrics tracking
        storage = SelfRefineStorage(track_usage=True)
        toolset = create_self_refine_toolset(storage=storage)
        print(storage.metrics.total_tokens())
        ```
    """

    _outputs: dict[str, RefinementOutput] = field(default_factory=dict)
    _feedbacks: dict[str, Feedback] = field(default_factory=dict)
    _metrics: UsageMetrics | None = field(default=None)
    _links: dict[str, list[str]] = field(default_factory=dict)  # item_id -> list of link IDs
    _linked_from: list[str] = field(default_factory=list)  # list of link IDs where this storage is target

    def __init__(self, *, track_usage: bool = False) -> None:
        """Initialize storage with optional metrics tracking.

        Args:
            track_usage: If True, enables usage metrics collection.
        """
        self._outputs = {}
        self._feedbacks = {}
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
    def outputs(self) -> dict[str, RefinementOutput]:
        """Get the current dictionary of outputs."""
        return self._outputs

    @outputs.setter
    def outputs(self, value: RefinementOutput) -> None:
        """Add or update an output in the dictionary."""
        self._outputs[value.output_id] = value

    @property
    def feedbacks(self) -> dict[str, Feedback]:
        """Get the current dictionary of feedbacks."""
        return self._feedbacks

    @feedbacks.setter
    def feedbacks(self, value: Feedback) -> None:
        """Add or update a feedback in the dictionary."""
        self._feedbacks[value.feedback_id] = value

    @property
    def metrics(self) -> UsageMetrics | None:
        """Get usage metrics if tracking is enabled."""
        return self._metrics

    def get_statistics(self) -> dict[str, int | float]:
        """Get summary statistics about self-refinement operations.

        Returns:
            Dictionary with output and feedback counts.
        """
        total_outputs = len(self._outputs)
        final_outputs = sum(1 for o in self._outputs.values() if o.is_final)
        max_iteration = max((o.iteration for o in self._outputs.values()), default=0)
        avg_quality = None
        quality_scores = [o.quality_score for o in self._outputs.values() if o.quality_score is not None]
        if quality_scores:
            avg_quality = sum(quality_scores) / len(quality_scores)

        stats: dict[str, int | float] = {
            "total_outputs": total_outputs,
            "final_outputs": final_outputs,
            "max_iteration": max_iteration,
            "total_feedbacks": len(self._feedbacks),
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
            "toolset": "self_refine",
            "statistics": self.get_statistics(),
        }

        # Add storage-specific data
        summary_dict["storage"] = {
            "outputs": {
                output_id: {
                    "output_id": output.output_id,
                    "content": output.content,
                    "iteration": output.iteration,
                    "is_final": output.is_final,
                    "quality_score": output.quality_score,
                }
                for output_id, output in self._outputs.items()
            },
            "feedbacks": {
                feedback_id: {
                    "feedback_id": feedback.feedback_id,
                    "output_id": feedback.output_id,
                    "content": feedback.content,
                    "aspects": feedback.aspects,
                }
                for feedback_id, feedback in self._feedbacks.items()
            },
        }

        # Add metrics if available
        if self._metrics:
            summary_dict["usage_metrics"] = self._metrics.to_dict()

        return summary_dict

    def clear(self) -> None:
        """Clear all outputs, feedbacks, and reset metrics."""
        self._outputs.clear()
        self._feedbacks.clear()
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
            item_id: ID of the item (output_id or feedback_id)
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
            Formatted string summary of outputs and feedbacks.
        """
        stats = self.get_statistics()
        lines: list[str] = []
        lines.append(f"Self-Refine: {stats['total_outputs']} outputs, {stats['total_feedbacks']} feedbacks")
        if stats["final_outputs"] > 0:
            lines.append(f"  - {stats['final_outputs']} final outputs")
        if stats["max_iteration"] > 0:
            lines.append(f"  - Max iteration: {stats['max_iteration']}")
        if self._outputs:
            latest_output = list(self._outputs.values())[-1]
            lines.append(f"  Latest output: {latest_output.content}")
        return "\n".join(lines)

    def get_outputs_for_linking(self) -> list[dict[str, str]]:
        """Get list of linkable items with their IDs and descriptions.

        Returns:
            List of dictionaries with 'id' and 'description' keys for outputs and feedbacks.
        """
        linkable_items: list[dict[str, str]] = []
        # Add outputs
        for output_id, output in self._outputs.items():
            description = f"Output {output_id} (iteration {output.iteration}): {output.content}"
            if output.is_final:
                description += " [FINAL]"
            linkable_items.append({"id": output_id, "description": description})
        # Add feedbacks
        for feedback_id, feedback in self._feedbacks.items():
            description = f"Feedback {feedback_id} for output {feedback.output_id}: {feedback.description} - {feedback.suggestion}"
            linkable_items.append({"id": feedback_id, "description": description})
        return linkable_items
