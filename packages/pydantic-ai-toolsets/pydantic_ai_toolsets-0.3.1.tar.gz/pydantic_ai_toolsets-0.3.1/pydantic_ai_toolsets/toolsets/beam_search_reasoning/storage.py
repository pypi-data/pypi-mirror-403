"""Storage abstraction for beam search."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from .types import BeamCandidate, BeamStep

if TYPE_CHECKING:
    from .._shared.metrics import UsageMetrics


@runtime_checkable
class BeamStorageProtocol(Protocol):
    """Protocol for beam search storage implementations.

    Any class that has `candidates` and `steps` properties can be used
    as storage for the beam search toolset.

    Example:
        ```python
        class MyCustomStorage:
            def __init__(self):
                self._candidates: dict[str, BeamCandidate] = {}
                self._steps: list[BeamStep] = []

            @property
            def candidates(self) -> dict[str, BeamCandidate]:
                return self._candidates

            @candidates.setter
            def candidates(self, value: BeamCandidate) -> None:
                self._candidates[value.candidate_id] = value

            @property
            def steps(self) -> list[BeamStep]:
                return self._steps

            @steps.setter
            def steps(self, value: BeamStep) -> None:
                # Update or append step
                ...
        ```
    """

    @property
    def candidates(self) -> dict[str, BeamCandidate]:
        """Get the current dictionary of candidates (candidate_id -> BeamCandidate)."""
        ...

    @candidates.setter
    def candidates(self, value: BeamCandidate) -> None:
        """Add or update a candidate in the dictionary."""
        ...

    @property
    def steps(self) -> list[BeamStep]:
        """Get the current list of beam steps."""
        ...

    @steps.setter
    def steps(self, value: BeamStep) -> None:
        """Add or update a step in the list."""
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
            item_id: ID of the item (candidate_id or step_id)
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
class BeamStorage:
    """Default in-memory beam search storage.

    Simple implementation that stores candidates and steps in memory.
    Use this for standalone agents or testing.

    Example:
        ```python
        from pydantic_ai_toolsets import create_beam_toolset, BeamStorage

        storage = BeamStorage()
        toolset = create_beam_toolset(storage=storage)

        # After agent runs, access candidates and steps directly
        print(storage.candidates)
        print(storage.steps)

        # With metrics tracking
        storage = BeamStorage(track_usage=True)
        toolset = create_beam_toolset(storage=storage)
        print(storage.metrics.total_tokens())
        ```
    """

    _candidates: dict[str, BeamCandidate] = field(default_factory=dict)
    _steps: list[BeamStep] = field(default_factory=list)
    _metrics: UsageMetrics | None = field(default=None)
    _links: dict[str, list[str]] = field(default_factory=dict)  # item_id -> list of link IDs
    _linked_from: list[str] = field(default_factory=list)  # list of link IDs where this storage is target

    def __init__(self, *, track_usage: bool = False) -> None:
        """Initialize storage with optional metrics tracking.

        Args:
            track_usage: If True, enables usage metrics collection.
        """
        self._candidates = {}
        self._steps = []
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
    def candidates(self) -> dict[str, BeamCandidate]:
        """Get the current dictionary of candidates."""
        return self._candidates

    @candidates.setter
    def candidates(self, value: BeamCandidate) -> None:
        """Add or update a candidate in the dictionary."""
        self._candidates[value.candidate_id] = value

    @property
    def steps(self) -> list[BeamStep]:
        """Get the current list of beam steps."""
        return self._steps

    @steps.setter
    def steps(self, value: BeamStep) -> None:
        """Add or update a step in the list."""
        for i, step in enumerate(self._steps):
            if step.step_index == value.step_index:
                self._steps[i] = value
                return
        self._steps.append(value)
        self._steps.sort(key=lambda s: s.step_index)

    @property
    def metrics(self) -> UsageMetrics | None:
        """Get usage metrics if tracking is enabled."""
        return self._metrics

    def get_statistics(self) -> dict[str, int | float]:
        """Get summary statistics about the beam search.

        Returns:
            Dictionary with candidate counts and beam metrics.
        """
        total = len(self._candidates)
        scored = sum(1 for c in self._candidates.values() if c.score is not None)
        terminal = sum(1 for c in self._candidates.values() if c.is_terminal)
        max_depth = max((c.depth for c in self._candidates.values()), default=0)
        avg_beam_width = (
            sum(s.beam_width for s in self._steps) / len(self._steps) if self._steps else 0
        )

        return {
            "total_candidates": total,
            "scored_candidates": scored,
            "terminal_candidates": terminal,
            "max_depth": max_depth,
            "total_steps": len(self._steps),
            "avg_beam_width": avg_beam_width,
        }

    def beam_width_history(self) -> list[tuple[int, int]]:
        """Get beam width at each step.

        Returns:
            List of (step_index, beam_width) tuples.
        """
        return [(s.step_index, s.beam_width) for s in sorted(self._steps, key=lambda s: s.step_index)]

    def summary(self) -> dict[str, Any]:
        """Get comprehensive JSON summary of storage state and metrics.

        Returns:
            Dictionary containing storage state, statistics, and usage metrics.
        """
        summary_dict: dict[str, Any] = {
            "toolset": "beam_search_reasoning",
            "statistics": self.get_statistics(),
        }

        # Add storage-specific data
        summary_dict["storage"] = {
            "candidates": {
                candidate_id: {
                    "candidate_id": candidate.candidate_id,
                    "content": candidate.content,
                    "depth": candidate.depth,
                    "score": candidate.score,
                    "is_terminal": candidate.is_terminal,
                }
                for candidate_id, candidate in self._candidates.items()
            },
            "steps": [
                {
                    "step_index": step.step_index,
                    "beam_width": step.beam_width,
                    "candidate_ids": step.candidate_ids,
                }
                for step in self._steps
            ],
        }

        # Add metrics if available
        if self._metrics:
            summary_dict["usage_metrics"] = self._metrics.to_dict()

        return summary_dict

    def clear(self) -> None:
        """Clear all candidates, steps, and reset metrics."""
        self._candidates.clear()
        self._steps.clear()
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
            item_id: ID of the item (candidate_id or step index as string)
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
            Formatted string summary of candidates and steps.
        """
        stats = self.get_statistics()
        lines: list[str] = []
        lines.append(f"Beam Search: {stats['total_candidates']} candidates, {stats['total_steps']} steps")
        if stats.get("best_score", None) is not None:
            lines.append(f"  - Best score: {stats['best_score']}")
        if self._candidates:
            best_candidate = max(self._candidates.values(), key=lambda c: c.score if c.score is not None else float('-inf'))
            lines.append(f"  Best candidate: {best_candidate.content}")
        return "\n".join(lines)

    def get_outputs_for_linking(self) -> list[dict[str, str]]:
        """Get list of linkable items with their IDs and descriptions.

        Returns:
            List of dictionaries with 'id' and 'description' keys for candidates and steps.
        """
        linkable_items: list[dict[str, str]] = []
        # Add candidates
        for candidate_id, candidate in self._candidates.items():
            description = f"Candidate {candidate_id} (depth {candidate.depth}): {candidate.content}"
            if candidate.score is not None:
                description += f" [score={candidate.score}]"
            linkable_items.append({"id": candidate_id, "description": description})
        # Add steps
        for step in self._steps:
            step_id = str(step.step_index)
            description = f"Step {step.step_index}: beam_width={step.beam_width}, {len(step.candidate_ids)} candidates"
            linkable_items.append({"id": step_id, "description": description})
        return linkable_items
