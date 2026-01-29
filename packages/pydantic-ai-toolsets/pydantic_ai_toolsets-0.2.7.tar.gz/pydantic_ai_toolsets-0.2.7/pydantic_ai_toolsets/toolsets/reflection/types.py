"""Type definitions for pydantic-ai-reflection."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ReflectionOutput(BaseModel):
    """An output that can be critiqued and refined.

    Each output represents a version of the solution at a specific refinement cycle.
    Outputs form a chain where each output can be critiqued and refined into a new output.

    Attributes:
        output_id: Unique identifier for this output.
        content: The actual output content (solution, answer, etc.).
        cycle: The refinement cycle number (0 for initial output).
        parent_id: ID of the parent output that was refined to create this one (None for initial).
        is_final: Whether this output is marked as final/satisfactory.
        quality_score: Optional quality score (0-100, higher is better).
    """

    output_id: str
    content: str
    cycle: int = Field(default=0, ge=0, description="Refinement cycle number (0 for initial)")
    parent_id: str | None = Field(
        default=None, description="ID of the parent output that was refined to create this one"
    )
    is_final: bool = Field(
        default=False, description="Whether this output is marked as final/satisfactory"
    )
    quality_score: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Optional quality score (0-100, higher is better)",
    )


class Critique(BaseModel):
    """A critique analyzing an output and identifying problems.

    Each critique examines a specific output and identifies areas for improvement.

    Attributes:
        critique_id: Unique identifier for this critique.
        output_id: ID of the output being critiqued.
        problems: List of specific problems identified (logical errors, missing info, etc.).
        strengths: List of strengths/positive aspects of the output.
        overall_assessment: Overall assessment of the output quality.
        improvement_suggestions: Specific suggestions for improvement.
    """

    critique_id: str
    output_id: str
    problems: list[str] = Field(
        default_factory=list,
        description="List of specific problems identified (logical errors, missing info, etc.)",
    )
    strengths: list[str] = Field(
        default_factory=list, description="List of strengths/positive aspects of the output"
    )
    overall_assessment: str = Field(..., description="Overall assessment of the output quality")
    improvement_suggestions: list[str] = Field(
        default_factory=list, description="Specific suggestions for improvement"
    )


class CreateOutputItem(BaseModel):
    """Input model for the create_output tool.

    This is the model that agents use when calling create_output.
    """

    content: str = Field(
        ...,
        description=(
            "The initial output content. This should be your first attempt at solving "
            "the problem or answering the question."
        ),
    )


class CritiqueOutputItem(BaseModel):
    """Input model for the critique_output tool."""

    output_id: str = Field(..., description="ID of the output to critique")
    problems: list[str] = Field(
        ...,
        min_length=1,
        description=(
            "List of specific problems identified in the output. "
            "Be specific about logical errors, missing information, poor structure, etc."
        ),
    )
    strengths: list[str] = Field(
        default_factory=list,
        description="List of strengths or positive aspects of the output (optional)",
    )
    overall_assessment: str = Field(
        ...,
        description=(
            "Overall assessment of the output quality. "
            "Provide a clear evaluation of how well the output addresses the problem."
        ),
    )
    improvement_suggestions: list[str] = Field(
        ...,
        min_length=1,
        description=(
            "Specific suggestions for how to improve the output. "
            "These should address the identified problems."
        ),
    )


class RefineOutputItem(BaseModel):
    """Input model for the refine_output tool."""

    output_id: str = Field(
        ...,
        description=(
            "ID of the output to refine. This should be an output that has been critiqued. "
            "The refined version will address the problems identified in the critique."
        ),
    )
    refined_content: str = Field(
        ...,
        description=(
            "The improved version of the output. This should address the problems "
            "identified in the critique and incorporate the improvement suggestions."
        ),
    )
    is_final: bool = Field(
        default=False,
        description=(
            "Whether this refined output is final/satisfactory. "
            "Set to true if you believe no further refinement is needed."
        ),
    )
    quality_score: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description=(
            "Optional quality score for this refined output (0-100, higher is better). "
            "Use this to track improvement across refinement cycles."
        ),
    )
