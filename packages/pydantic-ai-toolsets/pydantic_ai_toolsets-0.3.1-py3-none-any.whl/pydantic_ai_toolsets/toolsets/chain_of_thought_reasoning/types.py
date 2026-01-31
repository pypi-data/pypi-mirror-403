"""Type definitions for pydantic-ai-cot."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Thought(BaseModel):
    """A thought in a chain of thoughts execution.

    Attributes:
        thought: The current thinking step content.
        thought_number: Current number in sequence (1-based).
        total_thoughts: Estimated total thoughts needed (can be adjusted).
        is_revision: Whether this thought revises previous thinking.
        revises_thought: Which thought number is being reconsidered (if is_revision).
        branch_from_thought: Branching point thought number (if branching).
        branch_id: Identifier for the current branch (if branching).
        next_thought_needed: Whether another thought step is needed.
    """

    thought: str
    thought_number: int
    total_thoughts: int
    is_revision: bool = False
    revises_thought: int | None = None
    branch_from_thought: int | None = None
    branch_id: str | None = None
    next_thought_needed: bool = True


class ThoughtItem(BaseModel):
    """Input model for the write_thoughts tool.

    This is the model that agents use when calling write_thoughts.
    It has the same fields as Thought but with Field descriptions for LLM guidance.
    """

    thought: str = Field(
        ...,
        description=(
            "Your current thinking step, which can include: regular analytical steps, "
            "revisions of previous thoughts, questions about previous decisions, "
            "realizations about needing more analysis, changes in approach, "
            "hypothesis generation, or hypothesis verification"
        ),
    )
    thought_number: int = Field(
        ...,
        description="Current thought number in sequence (1-based). Should increment sequentially.",
    )
    total_thoughts: int = Field(
        ...,
        description="Estimated total thoughts needed. Can be adjusted up or down as you progress.",
    )
    is_revision: bool = Field(
        default=False,
        description="Whether this thought revises previous thinking. Set to true if reconsidering "
        "or changing a previous thought.",
    )
    revises_thought: int | None = Field(
        default=None,
        description="Which thought number is being reconsidered (required if is_revision is true).",
    )
    branch_from_thought: int | None = Field(
        default=None,
        description="Branching point thought number if this thought branches into a new path.",
    )
    branch_id: str | None = Field(
        default=None,
        description=(
            "Identifier for the current branch (if branching). Use to group related thoughts."
        ),
    )
    next_thought_needed: bool = Field(
        default=True,
        description="Whether another thought step is needed. Set to false when you've reached "
        "a satisfactory conclusion or answer.",
    )
