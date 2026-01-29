"""Type definitions for pydantic-ai-beam."""

from __future__ import annotations

from pydantic import BaseModel, Field


class BeamCandidate(BaseModel):
    """A candidate in the beam search execution.

    Each candidate represents a reasoning state at a specific depth in the search.
    Candidates form a tree structure where each candidate can have multiple children
    (expansions) but only one parent.

    Attributes:
        candidate_id: Unique identifier for this candidate.
        content: The reasoning content at this candidate.
        score: Evaluation score for this candidate (0-100, higher is better).
        depth: Depth level in the search tree (0 for initial candidates).
        parent_id: ID of the parent candidate (None for root candidates).
        is_terminal: Whether this candidate represents a terminal/solution state.
        step_index: Which beam step this candidate belongs to.
    """

    candidate_id: str
    content: str
    score: float | None = None
    depth: int = Field(default=0, ge=0, description="Depth level in the search tree")
    parent_id: str | None = None
    is_terminal: bool = False
    step_index: int = Field(
        default=0, ge=0, description="Index of the beam step this candidate belongs to"
    )


class BeamStep(BaseModel):
    """A step in the beam search execution.

    Each step contains the top-k candidates (the "beam") at that depth level.
    Steps are ordered sequentially, with step 0 containing initial candidates.

    Attributes:
        step_index: Sequential index of this step (0-based).
        candidate_ids: List of candidate IDs in this step's beam (top-k).
        beam_width: The beam width (k) used for this step.
    """

    step_index: int = Field(ge=0, description="Sequential index of this step")
    candidate_ids: list[str] = Field(
        default_factory=list,
        description="List of candidate IDs in this step's beam (top-k)",
    )
    beam_width: int = Field(ge=1, description="The beam width (k) used for this step")


class CreateCandidateItem(BaseModel):
    """Input model for the create_candidate tool.

    This is the model that agents use when calling create_candidate.
    """

    content: str = Field(
        ...,
        description=(
            "The reasoning content for this candidate. Should represent a specific "
            "reasoning state or approach to the problem."
        ),
    )
    is_terminal: bool = Field(
        default=False,
        description="Whether this candidate represents a terminal/solution state.",
    )


class ExpandCandidateItem(BaseModel):
    """Input model for the expand_candidate tool."""

    candidate_id: str = Field(..., description="ID of the candidate to expand")
    expansions: list[str] = Field(
        ...,
        min_length=1,
        description=(
            "List of expansion contents. Each string represents a possible "
            "next step/continuation from this candidate."
        ),
    )
    is_terminal: list[bool] = Field(
        default_factory=lambda: [],
        description=(
            "Optional list indicating which expansions are terminal states. "
            "If provided, must match length of expansions."
        ),
    )


class ScoreCandidateItem(BaseModel):
    """Input model for the score_candidate tool."""

    candidate_id: str = Field(..., description="Identifier for the candidate to score")
    score: float = Field(
        ...,
        ge=0,
        le=100,
        description="Evaluation score from 0-100 (higher is better)",
    )
    reasoning: str = Field(
        ...,
        description=(
            "Explanation of why this score was assigned. Be specific about "
            "what makes this candidate valuable or not."
        ),
    )


class PruneBeamItem(BaseModel):
    """Input model for the prune_beam tool."""

    step_index: int = Field(
        ...,
        ge=0,
        description="Index of the step to prune (keep only top-k candidates)",
    )
    beam_width: int = Field(
        ...,
        ge=1,
        description="Beam width (k) - how many top candidates to keep",
    )
