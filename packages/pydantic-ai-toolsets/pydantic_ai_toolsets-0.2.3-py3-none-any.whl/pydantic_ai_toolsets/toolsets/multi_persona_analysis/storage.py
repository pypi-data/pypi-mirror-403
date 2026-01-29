"""Storage abstraction for persona sessions."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from .types import Persona, PersonaResponse, PersonaSession

if TYPE_CHECKING:
    from .._shared.metrics import UsageMetrics


@runtime_checkable
class PersonaStorageProtocol(Protocol):
    """Protocol for persona storage implementations.

    Any class that has `session`, `personas`, and `responses` properties can be used
    as storage for the persona toolset.

    Example:
        ```python
        class MyCustomStorage:
            def __init__(self):
                self._session: PersonaSession | None = None
                self._personas: dict[str, Persona] = {}
                self._responses: dict[str, PersonaResponse] = {}

            @property
            def session(self) -> PersonaSession | None:
                return self._session

            @session.setter
            def session(self, value: PersonaSession) -> None:
                self._session = value

            @property
            def personas(self) -> dict[str, Persona]:
                return self._personas

            @personas.setter
            def personas(self, value: Persona) -> None:
                self._personas[value.persona_id] = value

            @property
            def responses(self) -> dict[str, PersonaResponse]:
                return self._responses

            @responses.setter
            def responses(self, value: PersonaResponse) -> None:
                self._responses[value.response_id] = value
        ```
    """

    @property
    def session(self) -> PersonaSession | None:
        """Get the current persona session."""
        ...

    @session.setter
    def session(self, value: PersonaSession) -> None:
        """Set the persona session."""
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
    def responses(self) -> dict[str, PersonaResponse]:
        """Get all responses (response_id -> PersonaResponse)."""
        ...

    @responses.setter
    def responses(self, value: PersonaResponse) -> None:
        """Add or update a response in the dictionary."""
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
            item_id: ID of the item (persona_id, response_id, or session_id)
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
class PersonaStorage:
    """Default in-memory persona storage.

    Simple implementation that stores persona sessions, personas, and responses in memory.
    Use this for standalone agents or testing.

    Example:
        ```python
        from pydantic_ai_toolsets import create_persona_toolset, PersonaStorage

        storage = PersonaStorage()
        toolset = create_persona_toolset(storage=storage)

        # After agent runs, access persona state directly
        print(storage.session)
        print(storage.personas)
        print(storage.responses)

        # With metrics tracking
        storage = PersonaStorage(track_usage=True)
        toolset = create_persona_toolset(storage=storage)
        print(storage.metrics.total_tokens())
        ```
    """

    _session: PersonaSession | None = None
    _personas: dict[str, Persona] = field(default_factory=lambda: {})
    _responses: dict[str, PersonaResponse] = field(default_factory=lambda: {})
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
        self._responses = {}
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
    def session(self) -> PersonaSession | None:
        """Get the current persona session."""
        return self._session

    @session.setter
    def session(self, value: PersonaSession) -> None:
        """Set the persona session."""
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
    def responses(self) -> dict[str, PersonaResponse]:
        """Get all responses (response_id -> PersonaResponse)."""
        return self._responses

    @responses.setter
    def responses(self, value: PersonaResponse) -> None:
        """Add or update a response in the dictionary."""
        self._responses[value.response_id] = value

    @property
    def metrics(self) -> UsageMetrics | None:
        """Get usage metrics if tracking is enabled."""
        return self._metrics

    def get_statistics(self) -> dict[str, int | float]:
        """Get summary statistics about persona operations.

        Returns:
            Dictionary with persona and response counts.
        """
        total_personas = len(self._personas)
        total_responses = len(self._responses)
        current_round = self._session.current_round if self._session else 0
        max_round = self._session.max_rounds if self._session else 0

        return {
            "has_session": 1 if self._session else 0,
            "total_personas": total_personas,
            "total_responses": total_responses,
            "current_round": current_round,
            "max_rounds": max_round,
        }

    def summary(self) -> dict[str, Any]:
        """Get comprehensive JSON summary of storage state and metrics.

        Returns:
            Dictionary containing storage state, statistics, and usage metrics.
        """
        summary_dict: dict[str, Any] = {
            "toolset": "multi_persona_analysis",
            "statistics": self.get_statistics(),
        }

        # Add storage-specific data
        summary_dict["storage"] = {
            "session": (
                {
                    "session_id": self._session.session_id,
                    "problem": self._session.problem,
                    "process_type": self._session.process_type,
                    "status": self._session.status,
                    "current_round": self._session.current_round,
                    "max_rounds": self._session.max_rounds,
                    "synthesis": self._session.synthesis,
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
                    "expertise_areas": persona.expertise_areas,
                }
                for persona_id, persona in self._personas.items()
            },
            "responses": {
                response_id: {
                    "response_id": response.response_id,
                    "persona_id": response.persona_id,
                    "content": response.content,
                    "references": response.references,
                    "round_number": response.round_number,
                }
                for response_id, response in self._responses.items()
            },
        }

        # Add metrics if available
        if self._metrics:
            summary_dict["usage_metrics"] = self._metrics.to_dict()

        return summary_dict

    def clear(self) -> None:
        """Clear all persona data and reset metrics."""
        self._session = None
        self._personas.clear()
        self._responses.clear()
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
            item_id: ID of the item (persona_id, response_id, or session_id)
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
            Formatted string summary of personas, responses, and session.
        """
        stats = self.get_statistics()
        lines: list[str] = []
        lines.append(f"Multi-Persona Analysis: {stats['total_personas']} personas, {stats['total_responses']} responses")
        if self._session:
            lines.append(f"  - Session: {self._session.status}, round {stats['current_round']}/{stats['max_rounds']}")
        if self._personas:
            lines.append(f"  Personas: {', '.join(p.name for p in list(self._personas.values())[:3])}")
            if len(self._personas) > 3:
                lines.append(f"    ... and {len(self._personas) - 3} more")
        return "\n".join(lines)

    def get_outputs_for_linking(self) -> list[dict[str, str]]:
        """Get list of linkable items with their IDs and descriptions.

        Returns:
            List of dictionaries with 'id' and 'description' keys for personas, responses, and session.
        """
        linkable_items: list[dict[str, str]] = []
        # Add session
        if self._session:
            description = f"Session {self._session.session_id}: {self._session.problem[:100]}..." if len(self._session.problem) > 100 else f"Session {self._session.session_id}: {self._session.problem}"
            linkable_items.append({"id": self._session.session_id, "description": description})
        # Add personas
        for persona_id, persona in self._personas.items():
            description = f"Persona {persona.name} ({persona.persona_type}): {persona.description[:100]}..." if len(persona.description) > 100 else f"Persona {persona.name} ({persona.persona_type}): {persona.description}"
            linkable_items.append({"id": persona_id, "description": description})
        # Add responses
        for response_id, response in self._responses.items():
            description = f"Response from {response.persona_id} (round {response.round_number}): {response.content[:100]}..." if len(response.content) > 100 else f"Response from {response.persona_id} (round {response.round_number}): {response.content}"
            linkable_items.append({"id": response_id, "description": description})
        return linkable_items

