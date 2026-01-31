"""Storage abstraction for meta-orchestrator."""

from __future__ import annotations

import sys
import time
from dataclasses import asdict, dataclass, field
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from .types import CrossToolsetLink, LinkType, ToolsetTransition, WorkflowState, WorkflowTemplate

if TYPE_CHECKING:
    from .._shared.metrics import UsageMetrics


@runtime_checkable
class MetaOrchestratorStorageProtocol(Protocol):
    """Protocol for meta-orchestrator storage implementations.

    Any class that implements these methods can be used as storage for the meta-orchestrator toolset.
    """

    def register_toolset(self, toolset_id: str, toolset_info: dict[str, Any]) -> None:
        """Register a toolset with the orchestrator."""
        ...

    def track_transition(self, transition: ToolsetTransition) -> None:
        """Track a toolset transition."""
        ...

    def create_link(self, link: CrossToolsetLink) -> None:
        """Create a cross-toolset link."""
        ...

    def get_unified_state(self) -> dict[str, Any]:
        """Get unified state across all registered toolsets."""
        ...

    def start_workflow(self, workflow: WorkflowState) -> None:
        """Start a new workflow."""
        ...

    def get_active_workflow(self) -> WorkflowState | None:
        """Get the currently active workflow."""
        ...

    def update_workflow(self, workflow_id: str, updates: dict[str, Any]) -> None:
        """Update a workflow's state."""
        ...


@dataclass
class WorkflowRegistry:
    """Registry for workflow templates."""

    templates: dict[str, WorkflowTemplate] = field(default_factory=dict)

    def register(self, template: WorkflowTemplate) -> None:
        """Register a workflow template."""
        self.templates[template.name] = template

    def get(self, name: str) -> WorkflowTemplate | None:
        """Get a workflow template by name."""
        return self.templates.get(name)

    def list_all(self) -> list[str]:
        """List all registered template names."""
        return list(self.templates.keys())


@dataclass
class MetaOrchestratorStorage:
    """Default in-memory meta-orchestrator storage.

    Tracks active workflows, registered toolsets, transitions, and cross-toolset links.
    Use this for standalone agents or testing.

    Attributes:
        _registered_toolsets: Dictionary mapping toolset IDs to their metadata
        _active_workflows: Dictionary mapping workflow IDs to WorkflowState
        _links: List of all cross-toolset links
        _transitions: List of all toolset transitions
        _workflow_registry: Registry of workflow templates
        _metrics: Optional usage metrics tracker

    Example:
        ```python
        from pydantic_ai_toolsets import create_meta_orchestrator_toolset, MetaOrchestratorStorage

        storage = MetaOrchestratorStorage()
        toolset = create_meta_orchestrator_toolset(storage=storage)

        # After agent runs, access workflow state
        workflow = storage.get_active_workflow()
        print(workflow.current_stage)
        print(storage.links)

        # With metrics tracking
        storage = MetaOrchestratorStorage(track_usage=True)
        toolset = create_meta_orchestrator_toolset(storage=storage)
        print(storage.metrics.total_tokens())
        ```
    """

    _registered_toolsets: dict[str, dict[str, Any]] = field(default_factory=dict)
    _active_workflows: dict[str, WorkflowState] = field(default_factory=dict)
    _links: list[CrossToolsetLink] = field(default_factory=list)
    _transitions: list[ToolsetTransition] = field(default_factory=list)
    _workflow_registry: WorkflowRegistry = field(default_factory=WorkflowRegistry)
    _metrics: UsageMetrics | None = field(default=None)

    def __init__(self, *, track_usage: bool = False) -> None:
        """Initialize storage with optional metrics tracking.

        Args:
            track_usage: If True, enables usage metrics collection.
        """
        self._registered_toolsets = {}
        self._active_workflows = {}
        self._links = []
        self._transitions = []
        self._workflow_registry = WorkflowRegistry()
        self._metrics = None
        if track_usage:
            import os

            toolsets_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if toolsets_dir not in sys.path:
                sys.path.insert(0, toolsets_dir)
            from .._shared.metrics import UsageMetrics

            self._metrics = UsageMetrics()

    @property
    def registered_toolsets(self) -> dict[str, dict[str, Any]]:
        """Get dictionary of registered toolsets."""
        return self._registered_toolsets

    @property
    def active_workflows(self) -> dict[str, WorkflowState]:
        """Get dictionary of active workflows."""
        return self._active_workflows

    @property
    def links(self) -> list[CrossToolsetLink]:
        """Get list of all cross-toolset links."""
        return self._links

    @property
    def transitions(self) -> list[ToolsetTransition]:
        """Get list of all toolset transitions."""
        return self._transitions

    @property
    def workflow_registry(self) -> WorkflowRegistry:
        """Get the workflow registry."""
        return self._workflow_registry

    @property
    def metrics(self) -> UsageMetrics | None:
        """Get usage metrics if tracking is enabled."""
        return self._metrics

    def register_toolset(self, toolset_id: str, toolset_info: dict[str, Any]) -> None:
        """Register a toolset with the orchestrator.

        Args:
            toolset_id: Unique identifier for the toolset
            toolset_info: Dictionary with toolset metadata (e.g., type, label, tools)
        """
        self._registered_toolsets[toolset_id] = toolset_info

    def track_transition(self, transition: ToolsetTransition) -> None:
        """Track a toolset transition and automatically update workflow progression.

        Args:
            transition: The transition to track
        """
        self._transitions.append(transition)
        
        # Automatically update workflow stage progression if transition matches active workflow
        active_workflow = self.get_active_workflow()
        if active_workflow:
            # Check if transition matches the workflow's expected progression
            if transition.from_toolset_id in active_workflow.active_toolsets:
                from_index = active_workflow.active_toolsets.index(transition.from_toolset_id)
                if transition.to_toolset_id in active_workflow.active_toolsets:
                    to_index = active_workflow.active_toolsets.index(transition.to_toolset_id)
                    # If transitioning to next stage, update workflow
                    if to_index == from_index + 1 and from_index == active_workflow.current_stage:
                        # Mark current stage as completed
                        template = self.workflow_registry.get(active_workflow.template_name)
                        if template and from_index < len(template.stages):
                            stage_name = template.stages[from_index].name
                            if stage_name not in active_workflow.completed_stages:
                                active_workflow.completed_stages.append(stage_name)
                        
                        # Advance to next stage
                        active_workflow.current_stage = to_index
                        active_workflow.updated_at = time.time()
                        
                        # Add transition to workflow
                        active_workflow.transitions.append(transition)

    def create_link(self, link: CrossToolsetLink) -> None:
        """Create a cross-toolset link.

        Args:
            link: The link to create
        """
        if link.created_at is None:
            link.created_at = time.time()
        self._links.append(link)

    def get_links_for_item(self, toolset_id: str, item_id: str) -> list[CrossToolsetLink]:
        """Get all links for a specific item.

        Args:
            toolset_id: ID of the toolset
            item_id: ID of the item

        Returns:
            List of links where this item is source or target
        """
        return [
            link
            for link in self._links
            if (link.source_toolset_id == toolset_id and link.source_item_id == item_id)
            or (link.target_toolset_id == toolset_id and link.target_item_id == item_id)
        ]

    def start_workflow(self, workflow: WorkflowState) -> None:
        """Start a new workflow.

        Args:
            workflow: The workflow state to start
        """
        if workflow.started_at is None:
            workflow.started_at = time.time()
        workflow.updated_at = time.time()
        self._active_workflows[workflow.workflow_id] = workflow

    def get_active_workflow(self) -> WorkflowState | None:
        """Get the currently active workflow.

        Returns:
            The most recently updated workflow, or None if no workflows exist
        """
        if not self._active_workflows:
            return None
        # Return the most recently updated workflow
        return max(self._active_workflows.values(), key=lambda w: w.updated_at or 0)

    def update_workflow(self, workflow_id: str, updates: dict[str, Any]) -> None:
        """Update a workflow's state.

        Args:
            workflow_id: ID of the workflow to update
            updates: Dictionary of updates to apply
        """
        if workflow_id not in self._active_workflows:
            return
        workflow = self._active_workflows[workflow_id]
        for key, value in updates.items():
            if hasattr(workflow, key):
                setattr(workflow, key, value)
        workflow.updated_at = time.time()

    def get_unified_state(self) -> dict[str, Any]:
        """Get unified state across all registered toolsets.

        Returns:
            Dictionary containing:
            - active_toolsets: List of registered toolset IDs
            - active_workflows: List of active workflow IDs
            - total_links: Total number of cross-toolset links
            - total_transitions: Total number of transitions
            - current_workflow: Current workflow state if any
        """
        active_workflow = self.get_active_workflow()
        return {
            "active_toolsets": list(self._registered_toolsets.keys()),
            "active_workflows": list(self._active_workflows.keys()),
            "total_links": len(self._links),
            "total_transitions": len(self._transitions),
            "current_workflow": asdict(active_workflow) if active_workflow else None,
        }

    def summary(self) -> dict[str, Any]:
        """Get comprehensive JSON summary of storage state and metrics.

        Returns:
            Dictionary containing storage state, statistics, and usage metrics.
        """
        summary_dict: dict[str, Any] = {
            "registered_toolsets": len(self._registered_toolsets),
            "active_workflows": len(self._active_workflows),
            "total_links": len(self._links),
            "total_transitions": len(self._transitions),
            "workflow_templates": len(self._workflow_registry.templates),
        }

        if self._metrics:
            summary_dict["metrics"] = {
                "total_tokens": self._metrics.total_tokens(),
                "invocation_count": self._metrics.invocation_count(),
            }

        return summary_dict
