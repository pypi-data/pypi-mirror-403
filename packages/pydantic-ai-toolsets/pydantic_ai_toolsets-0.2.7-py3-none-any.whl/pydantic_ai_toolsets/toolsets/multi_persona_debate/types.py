"""Type definitions for pydantic-ai-persona-debate."""

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


class PersonaPosition(BaseModel):
    """A position/argument made by a persona in a debate.

    Each position represents an argument made by a specific persona in a specific round.
    Positions can be critiqued, defended, and agreed with by other personas.

    Attributes:
        position_id: Unique identifier for this position.
        persona_id: ID of the persona making this position.
        round_number: The debate round in which this position was made.
        content: The actual argument content.
        evidence: List of evidence citations (for evidence-based debates).
        critiques_addressed: List of critique IDs that this position addresses.
        parent_position_id: ID of parent position if this is a defense/refinement.
    """

    position_id: str
    persona_id: str = Field(..., description="ID of the persona making this position")
    round_number: int = Field(ge=0, description="The debate round number")
    content: str = Field(..., description="The argument content")
    evidence: list[str] = Field(
        default_factory=list,
        description="List of evidence citations (for evidence-based debates)",
    )
    critiques_addressed: list[str] = Field(
        default_factory=list,
        description="List of critique IDs that this position addresses",
    )
    parent_position_id: str | None = Field(
        default=None,
        description="ID of parent position if this is a defense/refinement",
    )


class PersonaCritique(BaseModel):
    """A critique of a position made by a persona.

    Each critique identifies weaknesses or challenges to a specific position.
    Critiques guide the defense and refinement process.

    Attributes:
        critique_id: Unique identifier for this critique.
        target_position_id: ID of the position being critiqued.
        persona_id: ID of the persona making this critique.
        round_number: The debate round in which this critique was made.
        content: The critique content.
        specific_points: List of specific weaknesses or points raised.
    """

    critique_id: str
    target_position_id: str = Field(..., description="ID of the position being critiqued")
    persona_id: str = Field(..., description="ID of the persona making this critique")
    round_number: int = Field(ge=0, description="The debate round number")
    content: str = Field(..., description="The critique content")
    specific_points: list[str] = Field(
        default_factory=list,
        description="List of specific weaknesses or points raised",
    )


class PersonaAgreement(BaseModel):
    """An agreement by a persona with another persona's position.

    Personas can agree with positions made by other personas, providing reasoning
    for their agreement. This allows for coalition-building and consensus formation.

    Attributes:
        agreement_id: Unique identifier for this agreement.
        target_position_id: ID of the position being agreed with.
        persona_id: ID of the persona agreeing with the position.
        round_number: The debate round in which this agreement was made.
        content: The agreement content explaining why the persona agrees.
        reasoning: Specific reasons or points that led to the agreement.
    """

    agreement_id: str
    target_position_id: str = Field(..., description="ID of the position being agreed with")
    persona_id: str = Field(..., description="ID of the persona agreeing with the position")
    round_number: int = Field(ge=0, description="The debate round number")
    content: str = Field(..., description="The agreement content explaining why the persona agrees")
    reasoning: list[str] = Field(
        default_factory=list,
        description="List of specific reasons or points that led to the agreement",
    )


class PersonaDebateSession(BaseModel):
    """Complete persona debate session.

    Tracks the overall state of a debate between personas, including topic,
    personas, rounds, positions, critiques, agreements, and resolution.

    Attributes:
        debate_id: Unique identifier for this debate session.
        topic: The debate topic/question.
        max_rounds: Maximum number of debate rounds.
        current_round: Current round number (0-indexed).
        status: Current status of the debate (active, completed, resolved).
        resolution: Final resolution text (if resolved).
        winner_persona_id: ID of winning persona (if resolved with winner).
        resolution_type: Type of resolution (synthesis, winner, consensus).
    """

    debate_id: str
    topic: str = Field(..., description="The debate topic/question")
    max_rounds: int = Field(default=5, ge=1, description="Maximum number of debate rounds")
    current_round: int = Field(default=0, ge=0, description="Current round number")
    status: Literal["active", "completed", "resolved"] = Field(
        default="active", description="Current status of the debate"
    )
    resolution: str | None = Field(default=None, description="Final resolution text (if resolved)")
    winner_persona_id: str | None = Field(
        default=None,
        description="ID of winning persona (if resolved with winner)",
    )
    resolution_type: Literal["synthesis", "winner", "consensus"] | None = Field(
        default=None,
        description="Type of resolution (synthesis combines views, winner selects persona, consensus finds agreement)",
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


class ProposePositionItem(BaseModel):
    """Input model for the propose_position tool."""

    persona_id: str = Field(..., description="ID of the persona proposing this position")
    content: str = Field(..., description="The argument content")
    evidence: list[str] = Field(
        default_factory=list,
        description="List of evidence citations (for evidence-based debates)",
    )


class CritiquePositionItem(BaseModel):
    """Input model for the critique_position tool."""

    target_position_id: str = Field(..., description="ID of the position to critique")
    persona_id: str = Field(..., description="ID of the persona making this critique")
    content: str = Field(..., description="The critique content")
    specific_points: list[str] = Field(
        ...,
        min_length=1,
        description="List of specific weaknesses or points raised",
    )


class DefendPositionItem(BaseModel):
    """Input model for the defend_position tool."""

    position_id: str = Field(..., description="ID of the position to defend/strengthen")
    persona_id: str = Field(..., description="ID of the persona defending this position")
    content: str = Field(
        ...,
        description="The defense content addressing critiques and strengthening the position",
    )
    critiques_addressed: list[str] = Field(
        default_factory=list,
        description="List of critique IDs that this defense addresses. Can be empty if strengthening position without addressing specific critiques.",
    )
    evidence: list[str] = Field(
        default_factory=list,
        description="Additional evidence citations",
    )


class AgreeWithPositionItem(BaseModel):
    """Input model for the agree_with_position tool."""

    target_position_id: str = Field(..., description="ID of the position to agree with")
    persona_id: str = Field(..., description="ID of the persona agreeing with the position")
    content: str = Field(
        ...,
        description="The agreement content explaining why the persona agrees",
    )
    reasoning: list[str] = Field(
        default_factory=list,
        description="List of specific reasons or points that led to the agreement",
    )


class ResolveDebateItem(BaseModel):
    """Input model for the resolve_debate tool."""

    resolution_type: Literal["synthesis", "winner", "consensus"] = Field(
        ..., description="Type of resolution"
    )
    resolution_content: str = Field(..., description="The resolution text/explanation")
    winner_persona_id: str | None = Field(
        default=None,
        description="ID of winning persona (required for winner type, optional for others)",
    )
    synthesis_elements: list[str] = Field(
        default_factory=list,
        description="List of elements synthesized from different positions (for synthesis type)",
    )
    consensus_points: list[str] = Field(
        default_factory=list,
        description="List of points where personas reached consensus (for consensus type)",
    )


class InitiatePersonaDebateItem(BaseModel):
    """Input model for the initiate_persona_debate tool."""

    topic: str = Field(..., description="The debate topic/question")
    max_rounds: int = Field(default=5, ge=1, description="Maximum number of debate rounds")


class OrchestrateRoundItem(BaseModel):
    """Input model for the orchestrate_round tool."""

    round_number: int = Field(..., ge=1, description="Round number to orchestrate")
