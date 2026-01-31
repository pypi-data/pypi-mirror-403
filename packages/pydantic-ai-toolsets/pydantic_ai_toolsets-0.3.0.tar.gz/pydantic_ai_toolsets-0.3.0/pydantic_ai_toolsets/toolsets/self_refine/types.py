"""Type definitions for pydantic-ai-self-refine."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class FeedbackType(str, Enum):
    """Types of feedback that can be provided."""

    ADDITIVE = "additive"  # Missing information, should include X
    SUBTRACTIVE = "subtractive"  # Remove redundant section Y
    TRANSFORMATIVE = "transformative"  # Restructure argument to lead with conclusion
    CORRECTIVE = "corrective"  # Fix factual error in paragraph Z


class FeedbackDimension(str, Enum):
    """Dimensions for evaluating feedback quality."""

    FACTUALITY = "factuality"  # Accuracy and correctness
    COHERENCE = "coherence"  # Logical flow and consistency
    COMPLETENESS = "completeness"  # All necessary information included
    STYLE = "style"  # Writing style and clarity


class RefinementOutput(BaseModel):
    """An output that can be refined through feedback loops.

    Each output represents a version of the solution at a specific refinement iteration.
    Outputs form a chain where each output can receive feedback and be refined into a new output.

    Attributes:
        output_id: Unique identifier for this output.
        content: The actual output content (solution, answer, etc.).
        iteration: The refinement iteration number (0 for initial output).
        parent_id: ID of the parent output that was refined to create this one (None for initial).
        is_final: Whether this output is marked as final/satisfactory.
        quality_score: Optional quality score (0-100, higher is better).
        quality_threshold: Optional quality threshold that must be met (0-100).
        iteration_limit: Optional maximum number of iterations allowed.
    """

    output_id: str
    content: str
    iteration: int = Field(
        default=0, ge=0, description="Refinement iteration number (0 for initial)"
    )
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
    quality_threshold: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Optional quality threshold that must be met (0-100)",
    )
    iteration_limit: int | None = Field(
        default=None,
        ge=1,
        description="Optional maximum number of iterations allowed",
    )


class Feedback(BaseModel):
    """Feedback analyzing an output and providing actionable suggestions.

    Each feedback examines a specific output and provides structured feedback with
    specific types (additive, subtractive, transformative, corrective) and dimensions.

    Attributes:
        feedback_id: Unique identifier for this feedback.
        output_id: ID of the output being analyzed.
        feedback_type: Type of feedback (additive, subtractive, transformative, corrective).
        dimension: Dimension being evaluated (factuality, coherence, completeness, style).
        description: Detailed description of the feedback.
        suggestion: Specific, actionable suggestion for improvement.
        priority: Priority weight (0-1, higher is more important). Used for weighted feedback.
        is_actionable: Whether this feedback provides actionable guidance.
    """

    feedback_id: str
    output_id: str
    feedback_type: FeedbackType = Field(..., description="Type of feedback")
    dimension: FeedbackDimension = Field(..., description="Dimension being evaluated")
    description: str = Field(..., description="Detailed description of the feedback")
    suggestion: str = Field(..., description="Specific, actionable suggestion for improvement")
    priority: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Priority weight (0-1, higher is more important) for weighted feedback",
    )
    is_actionable: bool = Field(
        default=True, description="Whether this feedback provides actionable guidance"
    )


class GenerateOutputItem(BaseModel):
    """Input model for the generate_output tool.

    This is the model that agents use when calling generate_output.
    """

    content: str = Field(
        ...,
        description=(
            "The initial output content. This should be your first attempt at solving "
            "the problem or answering the question."
        ),
    )
    quality_threshold: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description=(
            "Optional quality threshold (0-100). Refinement will continue until "
            "this threshold is met or iteration limit is reached."
        ),
    )
    iteration_limit: int | None = Field(
        default=None,
        ge=1,
        description=(
            "Optional maximum number of refinement iterations allowed. "
            "Default is unlimited, but typically 2-3 iterations are sufficient."
        ),
    )


class ProvideFeedbackItem(BaseModel):
    """Input model for the provide_feedback tool."""

    output_id: str = Field(..., description="ID of the output to provide feedback on")
    feedback_items: list[FeedbackItem] = Field(
        ...,
        min_length=1,
        description=(
            "List of feedback items. Each item should be specific and actionable, "
            "with a clear type (additive, subtractive, transformative, corrective) "
            "and dimension (factuality, coherence, completeness, style)."
        ),
    )
    overall_assessment: str = Field(
        ...,
        description=(
            "Overall assessment of the output quality. "
            "Provide a clear evaluation of how well the output addresses the problem, "
            "and whether further refinement is needed."
        ),
    )
    should_continue_refining: bool = Field(
        default=True,
        description=(
            "Whether refinement should continue. Set to false if the output "
            "meets quality standards and no further improvement is needed."
        ),
    )


class FeedbackItem(BaseModel):
    """A single feedback item within ProvideFeedbackItem."""

    feedback_type: FeedbackType = Field(..., description="Type of feedback")
    dimension: FeedbackDimension = Field(..., description="Dimension being evaluated")
    description: str = Field(..., description="Detailed description of the feedback")
    suggestion: str = Field(..., description="Specific, actionable suggestion for improvement")
    priority: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Priority weight (0-1, higher is more important) for weighted feedback",
    )


class RefineOutputItem(BaseModel):
    """Input model for the refine_output tool."""

    output_id: str = Field(
        ...,
        description=(
            "ID of the output to refine. This should be an output that has received feedback. "
            "The refined version will address the feedback provided."
        ),
    )
    refined_content: str = Field(
        ...,
        description=(
            "The improved version of the output. This should address the feedback "
            "provided, incorporating all suggestions, especially high-priority ones."
        ),
    )
    is_final: bool = Field(
        default=False,
        description=(
            "Whether this refined output is final/satisfactory. "
            "Set to true if you believe no further refinement is needed or "
            "quality threshold has been met."
        ),
    )
    quality_score: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description=(
            "Optional quality score for this refined output (0-100, higher is better). "
            "Use this to track improvement across refinement iterations. "
            "Compare against quality_threshold to determine if refinement should continue."
        ),
    )

