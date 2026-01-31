"""Type definitions for meta-orchestrator toolset."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class LinkType(str, Enum):
    """Types of links between toolset outputs."""

    REFINES = "refines"
    EXPLORES = "explores"
    SYNTHESIZES = "synthesizes"
    REFERENCES = "references"


@dataclass
class CrossToolsetLink:
    """A link between outputs from different toolsets.

    Attributes:
        link_id: Unique identifier for this link
        source_toolset_id: ID of the source toolset
        source_item_id: ID of the item in the source toolset
        target_toolset_id: ID of the target toolset
        target_item_id: ID of the item in the target toolset
        link_type: Type of relationship (refines, explores, synthesizes, references)
        created_at: Timestamp when link was created
    """

    link_id: str
    source_toolset_id: str
    source_item_id: str
    target_toolset_id: str
    target_item_id: str
    link_type: LinkType
    created_at: float | None = None


@dataclass
class ToolsetTransition:
    """Suggests when to switch from one toolset to another.

    Attributes:
        from_toolset_id: ID of the current toolset
        to_toolset_id: ID of the recommended next toolset
        reason: Explanation for why this transition is recommended
        confidence: Confidence score (0.0 to 1.0)
        conditions_met: List of conditions that triggered this transition
    """

    from_toolset_id: str
    to_toolset_id: str
    reason: str
    confidence: float = 1.0
    conditions_met: list[str] | None = None


@dataclass
class Stage:
    """Represents a stage in a workflow template.

    Attributes:
        name: Human-readable name for this stage
        toolset_id: ID of the toolset to use in this stage
        transition_condition: Condition that must be met to transition to next stage
        description: Optional description of what happens in this stage
    """

    name: str
    toolset_id: str
    transition_condition: str
    description: str | None = None


@dataclass
class WorkflowTemplate:
    """A predefined workflow pattern combining multiple toolsets.

    Attributes:
        name: Unique identifier for this template
        toolsets: List of toolset IDs in order
        stages: List of stages with transition conditions
        handoff_instructions: Mapping of stage transitions to instructions
        description: Optional description of when to use this template
    """

    name: str
    toolsets: list[str]
    stages: list[Stage]
    handoff_instructions: dict[str, str]
    description: str | None = None


@dataclass
class WorkflowState:
    """Tracks the state of an active workflow.

    Attributes:
        workflow_id: Unique identifier for this workflow instance
        template_name: Name of the workflow template being used
        current_stage: Index of the current stage
        active_toolsets: List of toolset IDs currently active
        completed_stages: List of stage names that have been completed
        transitions: List of transitions that have occurred
        links: List of cross-toolset links created
        started_at: Timestamp when workflow started
        updated_at: Timestamp when workflow was last updated
    """

    workflow_id: str
    template_name: str
    current_stage: int = 0
    active_toolsets: list[str] = None
    completed_stages: list[str] = None
    transitions: list[ToolsetTransition] = None
    links: list[CrossToolsetLink] = None
    started_at: float | None = None
    updated_at: float | None = None

    def __post_init__(self):
        """Initialize default values for mutable fields."""
        if self.active_toolsets is None:
            self.active_toolsets = []
        if self.completed_stages is None:
            self.completed_stages = []
        if self.transitions is None:
            self.transitions = []
        if self.links is None:
            self.links = []


# Input models for toolset tools

class StartWorkflowItem(BaseModel):
    """Input model for starting a workflow."""

    template_name: str = Field(
        ...,
        description="Name of the workflow template to start (e.g., 'research_assistant', 'creative_problem_solver')",
    )
    initial_context: dict[str, Any] | None = Field(
        default=None,
        description="Optional initial context to pass to the workflow",
    )


class SuggestTransitionItem(BaseModel):
    """Input model for suggesting a toolset transition."""

    current_toolset_id: str | None = Field(
        default=None,
        description="ID of the current toolset. If not provided, will infer from workflow state.",
    )
    current_state_summary: str | None = Field(
        default=None,
        description="Optional summary of current state to help with transition decision",
    )


class LinkToolsetOutputsItem(BaseModel):
    """Input model for creating a cross-toolset link."""

    source_toolset_id: str = Field(
        ...,
        description="ID of the source toolset",
    )
    source_item_id: str = Field(
        ...,
        description="ID of the item in the source toolset to link from",
    )
    target_toolset_id: str = Field(
        ...,
        description="ID of the target toolset",
    )
    target_item_id: str = Field(
        ...,
        description="ID of the item in the target toolset to link to",
    )
    link_type: LinkType = Field(
        ...,
        description="Type of link: 'refines', 'explores', 'synthesizes', or 'references'",
    )


class GetWorkflowStatusItem(BaseModel):
    """Input model for getting workflow status."""

    workflow_id: str | None = Field(
        default=None,
        description="ID of the workflow. If not provided, returns status of active workflow.",
    )
