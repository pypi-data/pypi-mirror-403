"""Type definitions for pydantic-ai-multi-personas."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class Persona(BaseModel):
    """A persona representing a distinct viewpoint or expertise.

    Personas can be expert personas (domain specialists), thinking style personas
    (cognitive approaches), or stakeholder personas (interested parties).

    Attributes:
        persona_id: Unique identifier for this persona.
        name: Display name of the persona (e.g., "Clinical Doctor", "Analytical Persona").
        persona_type: Type of persona - expert, thinking_style, or stakeholder.
        description: Detailed description of the persona's background, expertise, and perspective.
        expertise_areas: List of specific areas of expertise or focus.
    """

    persona_id: str
    name: str = Field(..., description="Display name of the persona")
    persona_type: Literal["expert", "thinking_style", "stakeholder"] = Field(
        ..., description="Type of persona"
    )
    description: str = Field(
        ...,
        description="Detailed description of the persona's background, expertise, and perspective",
    )
    expertise_areas: list[str] = Field(
        default_factory=list,
        description="List of specific areas of expertise or focus",
    )


class PersonaResponse(BaseModel):
    """A response from a persona to a problem or question.

    Each persona provides independent analysis from their unique perspective.
    Responses can reference other responses in interactive dialogue patterns.

    Attributes:
        response_id: Unique identifier for this response.
        persona_id: ID of the persona providing this response.
        content: The persona's analysis, insights, or perspective.
        references: List of response IDs that this response references or responds to.
        round_number: Round number in interactive dialogue (0 for initial responses).
    """

    response_id: str
    persona_id: str = Field(..., description="ID of the persona providing this response")
    content: str = Field(..., description="The persona's analysis, insights, or perspective")
    references: list[str] = Field(
        default_factory=list,
        description="List of response IDs that this response references or responds to",
    )
    round_number: int = Field(
        default=0, ge=0, description="Round number in interactive dialogue"
    )


class PersonaSession(BaseModel):
    """Complete persona session.

    Tracks the overall state of a multi-persona analysis session, including
    the problem/question, personas, responses, and synthesis.

    Attributes:
        session_id: Unique identifier for this session.
        problem: The problem or question being analyzed.
        process_type: Type of process - sequential, interactive, or devils_advocate.
        status: Current status of the session (active, completed, synthesized).
        synthesis: Final synthesis text (if synthesized).
        max_rounds: Maximum number of dialogue rounds (for interactive/devils_advocate).
        current_round: Current round number (0-indexed).
    """

    session_id: str
    problem: str = Field(..., description="The problem or question being analyzed")
    process_type: Literal["sequential", "interactive", "devils_advocate"] = Field(
        ..., description="Type of process"
    )
    status: Literal["active", "completed", "synthesized"] = Field(
        default="active", description="Current status of the session"
    )
    synthesis: str | None = Field(
        default=None, description="Final synthesis text (if synthesized)"
    )
    max_rounds: int = Field(
        default=3, ge=1, description="Maximum number of dialogue rounds"
    )
    current_round: int = Field(
        default=0, ge=0, description="Current round number"
    )


# Input models for tools


class CreatePersonaItem(BaseModel):
    """Input model for the create_persona tool."""

    name: str = Field(..., description="Display name of the persona")
    persona_type: Literal["expert", "thinking_style", "stakeholder"] = Field(
        ..., description="Type of persona"
    )
    description: str = Field(
        ...,
        description="Detailed description of the persona's background, expertise, and perspective",
    )
    expertise_areas: list[str] = Field(
        default_factory=list,
        description="List of specific areas of expertise or focus",
    )


class AddPersonaResponseItem(BaseModel):
    """Input model for the add_persona_response tool."""

    persona_id: str = Field(..., description="ID of the persona providing this response")
    content: str = Field(..., description="The persona's analysis, insights, or perspective")
    references: list[str] = Field(
        default_factory=list,
        description="List of response IDs that this response references or responds to",
    )


class SynthesizeItem(BaseModel):
    """Input model for the synthesize tool."""

    synthesis_content: str = Field(
        ...,
        description="The synthesis text combining insights from all personas",
    )
    key_insights: list[str] = Field(
        default_factory=list,
        description="List of key insights or elements synthesized",
    )
    conflicts_resolved: list[str] = Field(
        default_factory=list,
        description="List of conflicts or tensions that were resolved",
    )


class InitiatePersonaSessionItem(BaseModel):
    """Input model for the initiate_persona_session tool."""

    problem: str = Field(..., description="The problem or question to analyze")
    process_type: Literal["sequential", "interactive", "devils_advocate"] = Field(
        ..., description="Type of process"
    )
    max_rounds: int = Field(
        default=3, ge=1, description="Maximum number of dialogue rounds"
    )

