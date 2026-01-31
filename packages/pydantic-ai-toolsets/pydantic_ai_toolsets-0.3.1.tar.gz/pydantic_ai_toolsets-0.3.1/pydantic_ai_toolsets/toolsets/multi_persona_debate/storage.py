"""Storage abstraction for persona debate sessions."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from .types import (
    Persona,
    PersonaAgreement,
    PersonaCritique,
    PersonaDebateSession,
    PersonaPosition,
)

if TYPE_CHECKING:
    from .._shared.metrics import UsageMetrics


@runtime_checkable
class PersonaDebateStorageProtocol(Protocol):
    """Protocol for persona debate storage implementations.

    Any class that has `session`, `personas`, `positions`, `critiques`, and `agreements`
    properties can be used as storage for the persona debate toolset.

    Example:
        ```python
        class MyCustomStorage:
            def __init__(self):
                self._session: PersonaDebateSession | None = None
                self._personas: dict[str, Persona] = {}
                self._positions: dict[str, PersonaPosition] = {}
                self._critiques: dict[str, PersonaCritique] = {}
                self._agreements: dict[str, PersonaAgreement] = {}

            @property
            def session(self) -> PersonaDebateSession | None:
                return self._session

            @session.setter
            def session(self, value: PersonaDebateSession) -> None:
                self._session = value

            @property
            def personas(self) -> dict[str, Persona]:
                return self._personas

            @personas.setter
            def personas(self, value: Persona) -> None:
                self._personas[value.persona_id] = value

            @property
            def positions(self) -> dict[str, PersonaPosition]:
                return self._positions

            @positions.setter
            def positions(self, value: PersonaPosition) -> None:
                self._positions[value.position_id] = value

            @property
            def critiques(self) -> dict[str, PersonaCritique]:
                return self._critiques

            @critiques.setter
            def critiques(self, value: PersonaCritique) -> None:
                self._critiques[value.critique_id] = value

            @property
            def agreements(self) -> dict[str, PersonaAgreement]:
                return self._agreements

            @agreements.setter
            def agreements(self, value: PersonaAgreement) -> None:
                self._agreements[value.agreement_id] = value
        ```
    """

    @property
    def session(self) -> PersonaDebateSession | None:
        """Get the current persona debate session."""
        ...

    @session.setter
    def session(self, value: PersonaDebateSession) -> None:
        """Set the persona debate session."""
        ...

    @property
    def personas(self) -> dict[str, Persona]:
        """Get all personas (persona_id -> Persona)."""
        ...

    @personas.setter
    def personas(self, value: Persona) -> None:
        """Add or update a persona in the dictionary."""
        ...

    @property
    def positions(self) -> dict[str, PersonaPosition]:
        """Get all positions (position_id -> PersonaPosition)."""
        ...

    @positions.setter
    def positions(self, value: PersonaPosition) -> None:
        """Add or update a position in the dictionary."""
        ...

    @property
    def critiques(self) -> dict[str, PersonaCritique]:
        """Get all critiques (critique_id -> PersonaCritique)."""
        ...

    @critiques.setter
    def critiques(self, value: PersonaCritique) -> None:
        """Add or update a critique in the dictionary."""
        ...

    @property
    def agreements(self) -> dict[str, PersonaAgreement]:
        """Get all agreements (agreement_id -> PersonaAgreement)."""
        ...

    @agreements.setter
    def agreements(self, value: PersonaAgreement) -> None:
        """Add or update an agreement in the dictionary."""
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
            item_id: ID of the item (persona_id, position_id, critique_id, or agreement_id)
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
class PersonaDebateStorage:
    """Default in-memory persona debate storage.

    Simple implementation that stores persona debate sessions, personas, positions,
    critiques, and agreements in memory. Use this for standalone agents or testing.

    Example:
        ```python
        from pydantic_ai_toolsets import create_persona_debate_toolset, PersonaDebateStorage

        storage = PersonaDebateStorage()
        toolset = create_persona_debate_toolset(storage=storage)

        # After agent runs, access debate state directly
        print(storage.session)
        print(storage.personas)
        print(storage.positions)
        print(storage.critiques)
        print(storage.agreements)

        # With metrics tracking
        storage = PersonaDebateStorage(track_usage=True)
        toolset = create_persona_debate_toolset(storage=storage)
        print(storage.metrics.total_tokens())
        ```
    """

    _session: PersonaDebateSession | None = None
    _personas: dict[str, Persona] = field(default_factory=dict)
    _positions: dict[str, PersonaPosition] = field(default_factory=dict)
    _critiques: dict[str, PersonaCritique] = field(default_factory=dict)
    _agreements: dict[str, PersonaAgreement] = field(default_factory=dict)
    _metrics: UsageMetrics | None = field(default=None)
    _links: dict[str, list[str]] = field(default_factory=dict)  # item_id -> list of link IDs
    _linked_from: list[str] = field(default_factory=list)  # list of link IDs where this storage is target

    def __init__(self, *, track_usage: bool = False) -> None:
        """Initialize storage with optional metrics tracking.

        Args:
            track_usage: If True, enables usage metrics collection.
        """
        self._session = None
        self._personas = {}
        self._positions = {}
        self._critiques = {}
        self._agreements = {}
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
    def session(self) -> PersonaDebateSession | None:
        """Get the current persona debate session."""
        return self._session

    @session.setter
    def session(self, value: PersonaDebateSession) -> None:
        """Set the persona debate session."""
        self._session = value

    @property
    def personas(self) -> dict[str, Persona]:
        """Get all personas (persona_id -> Persona)."""
        return self._personas

    @personas.setter
    def personas(self, value: Persona) -> None:
        """Add or update a persona in the dictionary."""
        self._personas[value.persona_id] = value

    @property
    def positions(self) -> dict[str, PersonaPosition]:
        """Get all positions (position_id -> PersonaPosition)."""
        return self._positions

    @positions.setter
    def positions(self, value: PersonaPosition) -> None:
        """Add or update a position in the dictionary."""
        self._positions[value.position_id] = value

    @property
    def critiques(self) -> dict[str, PersonaCritique]:
        """Get all critiques (critique_id -> PersonaCritique)."""
        return self._critiques

    @critiques.setter
    def critiques(self, value: PersonaCritique) -> None:
        """Add or update a critique in the dictionary."""
        self._critiques[value.critique_id] = value

    @property
    def agreements(self) -> dict[str, PersonaAgreement]:
        """Get all agreements (agreement_id -> PersonaAgreement)."""
        return self._agreements

    @agreements.setter
    def agreements(self, value: PersonaAgreement) -> None:
        """Add or update an agreement in the dictionary."""
        self._agreements[value.agreement_id] = value

    @property
    def metrics(self) -> UsageMetrics | None:
        """Get usage metrics if tracking is enabled."""
        return self._metrics

    def get_statistics(self) -> dict[str, int | float]:
        """Get summary statistics about persona debate operations.

        Returns:
            Dictionary with debate counts and metrics.
        """
        total_personas = len(self._personas)
        total_positions = len(self._positions)
        total_critiques = len(self._critiques)
        total_agreements = len(self._agreements)
        current_round = self._session.current_round if self._session else 0
        max_round = self._session.max_rounds if self._session else 0

        return {
            "has_session": 1 if self._session else 0,
            "total_personas": total_personas,
            "total_positions": total_positions,
            "total_critiques": total_critiques,
            "total_agreements": total_agreements,
            "current_round": current_round,
            "max_rounds": max_round,
        }

    def summary(self) -> dict[str, Any]:
        """Get comprehensive JSON summary of storage state and metrics.

        Returns:
            Dictionary containing storage state, statistics, and usage metrics.
        """
        summary_dict: dict[str, Any] = {
            "toolset": "multi_persona_debate",
            "statistics": self.get_statistics(),
        }

        # Add storage-specific data
        summary_dict["storage"] = {
            "session": (
                {
                    "session_id": self._session.session_id,
                    "problem": self._session.problem,
                    "status": self._session.status,
                    "current_round": self._session.current_round,
                    "max_rounds": self._session.max_rounds,
                }
                if self._session
                else None
            ),
            "personas": {
                persona_id: {
                    "persona_id": persona.persona_id,
                    "name": persona.name,
                    "persona_type": persona.persona_type,
                    "description": persona.description,
                }
                for persona_id, persona in self._personas.items()
            },
            "positions": {
                position_id: {
                    "position_id": position.position_id,
                    "persona_id": position.persona_id,
                    "content": position.content,
                    "round_number": position.round_number,
                }
                for position_id, position in self._positions.items()
            },
            "critiques": {
                critique_id: {
                    "critique_id": critique.critique_id,
                    "persona_id": critique.persona_id,
                    "target_position_id": critique.target_position_id,
                    "content": critique.content,
                    "round_number": critique.round_number,
                }
                for critique_id, critique in self._critiques.items()
            },
            "agreements": {
                agreement_id: {
                    "agreement_id": agreement.agreement_id,
                    "persona_ids": agreement.persona_ids,
                    "content": agreement.content,
                    "round_number": agreement.round_number,
                }
                for agreement_id, agreement in self._agreements.items()
            },
        }

        # Add metrics if available
        if self._metrics:
            summary_dict["usage_metrics"] = self._metrics.to_dict()

        return summary_dict

    def clear(self) -> None:
        """Clear all debate data and reset metrics."""
        self._session = None
        self._personas.clear()
        self._positions.clear()
        self._critiques.clear()
        self._agreements.clear()
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
            item_id: ID of the item (persona_id, position_id, critique_id, agreement_id, or session_id)
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
            Formatted string summary of personas, positions, critiques, and agreements.
        """
        stats = self.get_statistics()
        lines: list[str] = []
        lines.append(f"Multi-Persona Debate: {stats['total_personas']} personas, {stats['total_positions']} positions, {stats['total_critiques']} critiques, {stats['total_agreements']} agreements")
        if self._session:
            lines.append(f"  - Session: {self._session.status}, round {stats['current_round']}/{stats['max_rounds']}")
        if self._personas:
            lines.append(f"  Personas: {', '.join(p.name for p in self._personas.values())}")
        return "\n".join(lines)

    def get_outputs_for_linking(self) -> list[dict[str, str]]:
        """Get list of linkable items with their IDs and descriptions.

        Returns:
            List of dictionaries with 'id' and 'description' keys for personas, positions, critiques, agreements, and session.
        """
        linkable_items: list[dict[str, str]] = []
        # Add session
        if self._session:
            description = f"Debate Session {self._session.session_id}: {self._session.problem}"
            linkable_items.append({"id": self._session.session_id, "description": description})
        # Add personas
        for persona_id, persona in self._personas.items():
            description = f"Persona {persona.name} ({persona.persona_type}): {persona.description}"
            linkable_items.append({"id": persona_id, "description": description})
        # Add positions
        for position_id, position in self._positions.items():
            description = f"Position from {position.persona_id} (round {position.round_number}): {position.content}"
            linkable_items.append({"id": position_id, "description": description})
        # Add critiques
        for critique_id, critique in self._critiques.items():
            description = f"Critique from {critique.persona_id} (round {critique.round_number}): {critique.content}"
            linkable_items.append({"id": critique_id, "description": description})
        # Add agreements
        for agreement_id, agreement in self._agreements.items():
            description = f"Agreement between {', '.join(agreement.persona_ids)} (round {agreement.round_number}): {agreement.content}"
            linkable_items.append({"id": agreement_id, "description": description})
        return linkable_items
