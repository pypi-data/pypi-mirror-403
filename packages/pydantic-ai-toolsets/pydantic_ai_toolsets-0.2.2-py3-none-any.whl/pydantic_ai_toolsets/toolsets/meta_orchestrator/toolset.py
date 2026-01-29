"""Meta-orchestrator toolset for pydantic-ai agents."""

from __future__ import annotations

import sys
import time
import uuid
from typing import Any

from pydantic_ai import Agent
from pydantic_ai.toolsets import FunctionToolset

from .storage import MetaOrchestratorStorage, MetaOrchestratorStorageProtocol
from .types import (
    CrossToolsetLink,
    GetWorkflowStatusItem,
    LinkToolsetOutputsItem,
    LinkType,
    StartWorkflowItem,
    SuggestTransitionItem,
    ToolsetTransition,
    WorkflowState,
)
from .workflow_templates import ALL_TEMPLATES

# =============================================================================
# SYSTEM PROMPT - Contains "when and why" to use the toolset
# =============================================================================

META_ORCHESTRATOR_SYSTEM_PROMPT = """
## Meta-Orchestrator

You have access to tools for orchestrating multi-toolset workflows:
- `read_unified_state`: View state across all active toolsets
- `suggest_toolset_transition`: Get recommendations for transitioning between toolsets
- `start_workflow`: Initialize a workflow template
- `link_toolset_outputs`: Create links between outputs from different toolsets
- `get_workflow_status`: Check the current status of an active workflow

### When to Use Meta-Orchestrator

Use these tools in these scenarios:
1. Coordinating multiple toolsets in a complex workflow
2. Managing transitions between different reasoning stages
3. Creating explicit links between toolset outputs
4. Tracking workflow progress across multiple stages
5. Understanding the overall state of a multi-toolset system

### Workflow Management

1. **Start Workflow**: Use `start_workflow` to initialize a predefined workflow template
2. **Monitor State**: Use `read_unified_state` to see the current state across all toolsets
3. **Transition Guidance**: Use `suggest_toolset_transition` when unsure which toolset to use next
4. **Create Links**: Use `link_toolset_outputs` to explicitly connect outputs between toolsets
5. **Check Status**: Use `get_workflow_status` to see workflow progress

### Key Principles

- **Workflow Templates**: Use predefined templates for common patterns (research_assistant, creative_problem_solver, etc.)
- **Explicit Transitions**: Create clear transitions between toolsets to guide the agent
- **Cross-Toolset Links**: Link related outputs to maintain context across toolsets
- **State Awareness**: Regularly check unified state to understand the full picture
"""

# =============================================================================
# TOOL DESCRIPTIONS - Contains "how" to use each specific tool
# =============================================================================

READ_UNIFIED_STATE_DESCRIPTION = """Read the unified state across all active toolsets.

Returns a comprehensive view of:
- All registered toolsets and their states
- Active workflows and their progress
- Cross-toolset links
- Recent transitions

Use this to understand the overall state of the multi-toolset system.
"""

SUGGEST_TRANSITION_DESCRIPTION = """Suggest when to transition from one toolset to another.

Parameters:
- current_toolset_id: Optional ID of current toolset (will infer if not provided)
- current_state_summary: Optional summary of current state

Returns a recommendation for the next toolset to use, including:
- Recommended next toolset
- Reason for the recommendation
- Confidence score
- Conditions that triggered the suggestion

Use this when you're unsure which toolset to use next in a workflow.
"""

START_WORKFLOW_DESCRIPTION = """Start a new workflow using a predefined template.

Parameters:
- template_name: Name of the workflow template (e.g., 'research_assistant', 'creative_problem_solver')
- initial_context: Optional initial context to pass to the workflow

Returns confirmation with workflow ID and initial stage information.

Available templates:
- research_assistant: Search → Self-Ask → Self-Refine → Todo
- creative_problem_solver: Multi-Persona Analysis → Graph of Thoughts → Reflection
- strategic_decision_maker: Multi-Persona Debate → MCTS → Reflection
- code_architect: Self-Ask → Tree of Thoughts → Reflection → Todo
"""

LINK_TOOLSET_OUTPUTS_DESCRIPTION = """Create a link between outputs from different toolsets.

Parameters:
- source_toolset_id: ID of the source toolset
- source_item_id: ID of the item in the source toolset
- target_toolset_id: ID of the target toolset
- target_item_id: ID of the item in the target toolset
- link_type: Type of link ('refines', 'explores', 'synthesizes', or 'references')

Returns confirmation with link ID.

Link types:
- refines: Target output refines/improves source output
- explores: Target output explores/expands on source output
- synthesizes: Target output synthesizes multiple source outputs
- references: Target output references source output

Use this to create explicit relationships between outputs from different toolsets.
"""

GET_WORKFLOW_STATUS_DESCRIPTION = """Get the current status of an active workflow.

Parameters:
- workflow_id: Optional workflow ID (returns active workflow if not provided)

Returns workflow status including:
- Current stage
- Completed stages
- Active toolsets
- Recent transitions
- Cross-toolset links

Use this to check progress and understand where you are in a workflow.
"""


def create_meta_orchestrator_toolset(
    storage: MetaOrchestratorStorageProtocol | None = None,
    *,
    id: str | None = None,
    track_usage: bool = False,
) -> FunctionToolset[Any]:
    """Create a meta-orchestrator toolset for workflow management.

    This toolset provides tools for AI agents to orchestrate multi-toolset workflows,
    manage transitions between toolsets, and create cross-toolset links.

    Args:
        storage: Optional storage backend. Defaults to in-memory MetaOrchestratorStorage.
            You can provide a custom storage implementing MetaOrchestratorStorageProtocol
            for persistence or integration with other systems.
        id: Optional unique ID for the toolset.
        track_usage: If True, enables usage metrics collection in storage.

    Returns:
        FunctionToolset compatible with any pydantic-ai agent.

    Example (standalone):
        ```python
        from pydantic_ai import Agent
        from pydantic_ai_toolsets import create_meta_orchestrator_toolset

        agent = Agent("openai:gpt-4.1", toolsets=[create_meta_orchestrator_toolset()])
        result = await agent.run("Start a research assistant workflow")
        ```

    Example (with storage access):
        ```python
        from pydantic_ai_toolsets import create_meta_orchestrator_toolset, MetaOrchestratorStorage

        storage = MetaOrchestratorStorage()
        toolset = create_meta_orchestrator_toolset(storage=storage)

        # After agent runs, access workflow state directly
        workflow = storage.get_active_workflow()
        print(workflow.current_stage)
        print(storage.links)
        ```
    """
    if storage is not None:
        _storage = storage
    else:
        _storage = MetaOrchestratorStorage(track_usage=track_usage)

    toolset: FunctionToolset[Any] = FunctionToolset(id=id)
    _metrics = getattr(_storage, "metrics", None) if hasattr(_storage, "metrics") else None

    # Register all workflow templates
    for template in ALL_TEMPLATES:
        _storage.workflow_registry.register(template)

    def _get_status_summary() -> str:
        """Get one-line status summary."""
        active_workflow = _storage.get_active_workflow()
        if active_workflow:
            return f"Status: ● Active | Workflow: {active_workflow.template_name} | Stage: {active_workflow.current_stage + 1}/{len(active_workflow.active_toolsets)}"
        return f"Status: ○ No active workflow | Toolsets: {len(_storage.registered_toolsets)}"

    def _get_next_hint() -> str:
        """Get contextual hint for next action."""
        active_workflow = _storage.get_active_workflow()
        if not active_workflow:
            return "Use start_workflow to begin a workflow template."
        if active_workflow.current_stage < len(active_workflow.active_toolsets) - 1:
            next_toolset = active_workflow.active_toolsets[active_workflow.current_stage + 1]
            return f"Consider transitioning to {next_toolset} for the next stage."
        return "Workflow is in final stage. Complete current tasks and provide final output."

    def _get_toolset_state_summary(toolset_id: str, toolset_info: dict[str, Any]) -> str:
        """Get state summary for a single toolset from its storage.

        Args:
            toolset_id: ID of the toolset
            toolset_info: Toolset info dictionary (may contain storage)

        Returns:
            Formatted state summary string
        """
        storage = toolset_info.get("storage")
        if not storage:
            return f"  {toolset_id}: No storage available"

        lines: list[str] = [f"  {toolset_id}:"]

        # Chain of Thought
        if hasattr(storage, "thoughts") and storage.thoughts:
            total = len(storage.thoughts)
            revisions = sum(1 for t in storage.thoughts if t.is_revision)
            final = sum(1 for t in storage.thoughts if not t.next_thought_needed)
            lines.append(f"    Thoughts: {total} total, {revisions} revisions, {final} final")

        # Self-Ask
        if hasattr(storage, "questions") and storage.questions:
            if isinstance(storage.questions, dict):
                total_q = len(storage.questions)
                answered = sum(1 for q in storage.questions.values() if hasattr(q, "status") and str(q.status) == "answered")
                final_answers = len(storage.final_answers) if hasattr(storage, "final_answers") and storage.final_answers else 0
                lines.append(f"    Questions: {total_q} total, {answered} answered, {final_answers} final answers")

        # Self-Refine / Reflection
        if hasattr(storage, "outputs") and storage.outputs:
            if isinstance(storage.outputs, dict):
                total_outputs = len(storage.outputs)
                final_outputs = sum(1 for o in storage.outputs.values() if hasattr(o, "is_final") and o.is_final)
                lines.append(f"    Outputs: {total_outputs} total, {final_outputs} final")
            elif isinstance(storage.outputs, list):
                total_outputs = len(storage.outputs)
                final_outputs = sum(1 for o in storage.outputs if hasattr(o, "is_final") and o.is_final)
                lines.append(f"    Outputs: {total_outputs} total, {final_outputs} final")

        # Todo
        if hasattr(storage, "todos") and storage.todos:
            total = len(storage.todos)
            pending = sum(1 for t in storage.todos if t.status == "pending")
            in_progress = sum(1 for t in storage.todos if t.status == "in_progress")
            completed = sum(1 for t in storage.todos if t.status == "completed")
            lines.append(f"    Todos: {total} total ({pending} pending, {in_progress} in progress, {completed} completed)")

        # Tree of Thought
        if hasattr(storage, "nodes") and storage.nodes:
            if isinstance(storage.nodes, dict):
                total_nodes = len(storage.nodes)
                solution_nodes = sum(1 for n in storage.nodes.values() if hasattr(n, "is_solution") and n.is_solution)
                lines.append(f"    Nodes: {total_nodes} total, {solution_nodes} solutions")

        # Graph of Thought
        if hasattr(storage, "edges") and storage.edges:
            if isinstance(storage.edges, dict):
                total_edges = len(storage.edges)
                lines.append(f"    Edges: {total_edges} total")

        # MCTS
        if hasattr(storage, "_iteration_count"):
            iterations = storage._iteration_count
            nodes = len(storage.nodes) if hasattr(storage, "nodes") else 0
            lines.append(f"    MCTS: {iterations} iterations, {nodes} nodes")

        # Beam Search
        if hasattr(storage, "candidates") and storage.candidates:
            if isinstance(storage.candidates, dict):
                total_candidates = len(storage.candidates)
                lines.append(f"    Candidates: {total_candidates} total")

        # Multi-Persona Analysis
        if hasattr(storage, "personas") and storage.personas:
            if isinstance(storage.personas, dict):
                total_personas = len(storage.personas)
                total_responses = len(storage.responses) if hasattr(storage, "responses") and storage.responses else 0
                lines.append(f"    Personas: {total_personas} total, {total_responses} responses")

        # Multi-Persona Debate
        if hasattr(storage, "positions") and storage.positions:
            if isinstance(storage.positions, dict):
                total_positions = len(storage.positions)
                total_critiques = len(storage.critiques) if hasattr(storage, "critiques") and storage.critiques else 0
                lines.append(f"    Positions: {total_positions} total, {total_critiques} critiques")

        # Search
        if hasattr(storage, "search_results") and storage.search_results:
            if isinstance(storage.search_results, dict):
                total_results = len(storage.search_results)
                total_extracted = len(storage.extracted_contents) if hasattr(storage, "extracted_contents") and storage.extracted_contents else 0
                lines.append(f"    Search Results: {total_results} total, {total_extracted} extracted")

        # Statistics if available
        if hasattr(storage, "get_statistics"):
            try:
                stats = storage.get_statistics()
                if stats:
                    stats_str = ", ".join(f"{k}: {v}" for k, v in stats.items() if isinstance(v, (int, float)))
                    if stats_str:
                        lines.append(f"    Stats: {stats_str}")
            except Exception:
                pass  # Ignore errors in statistics

        if len(lines) == 1:  # Only header line
            lines.append("    No active state")

        return "\n".join(lines)

    @toolset.tool(description=READ_UNIFIED_STATE_DESCRIPTION)
    async def read_unified_state() -> str:
        """Read the unified state across all active toolsets."""
        start_time = time.perf_counter()

        unified_state = _storage.get_unified_state()
        active_workflow = _storage.get_active_workflow()

        lines: list[str] = [
            "Unified State:",
            "==============",
            "",
            f"Active Toolsets: {len(_storage.registered_toolsets)}",
        ]

        # Show state for each registered toolset
        if _storage.registered_toolsets:
            lines.append("")
            for toolset_id, info in _storage.registered_toolsets.items():
                state_summary = _get_toolset_state_summary(toolset_id, info)
                lines.append(state_summary)
                lines.append("")

        # Show cross-toolset links
        if _storage.links:
            lines.append("Cross-Toolset Links:")
            for link in _storage.links:
                lines.append(
                    f"  {link.source_toolset_id}:{link.source_item_id} → {link.target_toolset_id}:{link.target_item_id} ({link.link_type.value})"
                )
            lines.append("")

        # Show workflow progress
        if active_workflow:
            template = _storage.workflow_registry.get(active_workflow.template_name)
            total_stages = len(template.stages) if template else len(active_workflow.active_toolsets)
            current_stage_name = ""
            if template and active_workflow.current_stage < len(template.stages):
                current_stage = template.stages[active_workflow.current_stage]
                current_stage_name = f" ({current_stage.name})"

            lines.append("Workflow Progress:")
            lines.append(f"  Workflow: {active_workflow.template_name}")
            lines.append(f"  Current Stage: {active_workflow.current_stage + 1}/{total_stages}{current_stage_name}")
            lines.append(f"  Completed Stages: {len(active_workflow.completed_stages)}")
            if active_workflow.completed_stages:
                lines.append(f"    {', '.join(active_workflow.completed_stages)}")
            lines.append(f"  Active Toolsets: {', '.join(active_workflow.active_toolsets)}")
            lines.append("")
        else:
            lines.append("Workflow Progress: No active workflow")
            lines.append("")

        lines.append(_get_status_summary())
        lines.append("")
        lines.append(f"Next: {_get_next_hint()}")

        result = "\n".join(lines)

        if _metrics is not None:
            duration_ms = (time.perf_counter() - start_time) * 1000
            _metrics.record_invocation("read_unified_state", "", result, duration_ms)

        return result

    @toolset.tool(description=SUGGEST_TRANSITION_DESCRIPTION)
    async def suggest_toolset_transition(suggestion: SuggestTransitionItem) -> str:
        """Suggest when to transition from one toolset to another."""
        start_time = time.perf_counter()

        active_workflow = _storage.get_active_workflow()
        current_toolset_id = suggestion.current_toolset_id

        # If no current toolset provided, try to infer from workflow
        if not current_toolset_id and active_workflow:
            if active_workflow.current_stage < len(active_workflow.active_toolsets):
                current_toolset_id = active_workflow.active_toolsets[active_workflow.current_stage]

        if not active_workflow:
            result = "No active workflow. Use start_workflow to begin a workflow template."
        elif not current_toolset_id:
            result = "Cannot determine current toolset. Please provide current_toolset_id."
        else:
            # Determine next toolset from workflow
            current_index = active_workflow.active_toolsets.index(current_toolset_id) if current_toolset_id in active_workflow.active_toolsets else -1
            if current_index >= 0 and current_index < len(active_workflow.active_toolsets) - 1:
                next_toolset_id = active_workflow.active_toolsets[current_index + 1]
                template = _storage.workflow_registry.get(active_workflow.template_name)
                reason = "Next stage in workflow"
                if template and current_index < len(template.stages) - 1:
                    next_stage = template.stages[current_index + 1]
                    reason = f"Transition to {next_stage.name} stage: {next_stage.description or next_stage.transition_condition}"

                transition = ToolsetTransition(
                    from_toolset_id=current_toolset_id,
                    to_toolset_id=next_toolset_id,
                    reason=reason,
                    confidence=0.9,
                    conditions_met=[suggestion.current_state_summary] if suggestion.current_state_summary else None,
                )
                _storage.track_transition(transition)

                result = f"Recommended transition: {current_toolset_id} → {next_toolset_id}\nReason: {reason}\nConfidence: {transition.confidence}"
            else:
                result = f"Current toolset '{current_toolset_id}' is the final stage. Workflow is complete."

        if _metrics is not None:
            duration_ms = (time.perf_counter() - start_time) * 1000
            input_text = suggestion.model_dump_json() if hasattr(suggestion, "model_dump_json") else str(suggestion)
            _metrics.record_invocation("suggest_toolset_transition", input_text, result, duration_ms)

        return result

    @toolset.tool(description=START_WORKFLOW_DESCRIPTION)
    async def start_workflow(workflow: StartWorkflowItem) -> str:
        """Start a new workflow using a predefined template."""
        start_time = time.perf_counter()

        template = _storage.workflow_registry.get(workflow.template_name)
        if not template:
            result = f"Workflow template '{workflow.template_name}' not found. Available templates: {', '.join(_storage.workflow_registry.list_all())}"
        else:
            workflow_id = str(uuid.uuid4())
            new_workflow = WorkflowState(
                workflow_id=workflow_id,
                template_name=workflow.template_name,
                current_stage=0,
                active_toolsets=template.toolsets.copy(),
                started_at=time.time(),
                updated_at=time.time(),
            )
            _storage.start_workflow(new_workflow)

            # Register toolsets if not already registered
            for toolset_id in template.toolsets:
                if toolset_id not in _storage.registered_toolsets:
                    _storage.register_toolset(toolset_id, {"type": "unknown", "label": toolset_id})

            stage_info = ""
            if template.stages:
                current_stage = template.stages[0]
                stage_info = f"\nCurrent Stage: {current_stage.name} ({current_stage.toolset_id})"

            result = f"Started workflow '{workflow.template_name}' (ID: {workflow_id}){stage_info}\nToolsets: {', '.join(template.toolsets)}"

        if _metrics is not None:
            duration_ms = (time.perf_counter() - start_time) * 1000
            input_text = workflow.model_dump_json() if hasattr(workflow, "model_dump_json") else str(workflow)
            _metrics.record_invocation("start_workflow", input_text, result, duration_ms)

        return result

    @toolset.tool(description=LINK_TOOLSET_OUTPUTS_DESCRIPTION)
    async def link_toolset_outputs(link_item: LinkToolsetOutputsItem) -> str:
        """Create a link between outputs from different toolsets."""
        start_time = time.perf_counter()

        link_id = str(uuid.uuid4())
        link = CrossToolsetLink(
            link_id=link_id,
            source_toolset_id=link_item.source_toolset_id,
            source_item_id=link_item.source_item_id,
            target_toolset_id=link_item.target_toolset_id,
            target_item_id=link_item.target_item_id,
            link_type=link_item.link_type,
            created_at=time.time(),
        )
        _storage.create_link(link)

        # Update individual storage link fields if storages are registered
        source_toolset_info = _storage.registered_toolsets.get(link_item.source_toolset_id)
        target_toolset_info = _storage.registered_toolsets.get(link_item.target_toolset_id)
        
        if source_toolset_info and "storage" in source_toolset_info:
            source_storage = source_toolset_info["storage"]
            if hasattr(source_storage, "add_link"):
                source_storage.add_link(link_item.source_item_id, link_id)
        
        if target_toolset_info and "storage" in target_toolset_info:
            target_storage = target_toolset_info["storage"]
            if hasattr(target_storage, "add_linked_from"):
                target_storage.add_linked_from(link_id)

        # Update active workflow if exists
        active_workflow = _storage.get_active_workflow()
        if active_workflow:
            active_workflow.links.append(link)
            _storage.update_workflow(active_workflow.workflow_id, {"links": active_workflow.links})

        result = f"Created link {link_id}: {link_item.source_toolset_id}:{link_item.source_item_id} → {link_item.target_toolset_id}:{link_item.target_item_id} ({link_item.link_type.value})"

        if _metrics is not None:
            duration_ms = (time.perf_counter() - start_time) * 1000
            input_text = link_item.model_dump_json() if hasattr(link_item, "model_dump_json") else str(link_item)
            _metrics.record_invocation("link_toolset_outputs", input_text, result, duration_ms)

        return result

    @toolset.tool(description=GET_WORKFLOW_STATUS_DESCRIPTION)
    async def get_workflow_status(status_item: GetWorkflowStatusItem) -> str:
        """Get the current status of an active workflow."""
        start_time = time.perf_counter()

        workflow_id = status_item.workflow_id
        if workflow_id:
            workflow = _storage.active_workflows.get(workflow_id)
        else:
            workflow = _storage.get_active_workflow()

        if not workflow:
            result = "No active workflow found."
        else:
            template = _storage.workflow_registry.get(workflow.template_name)
            lines: list[str] = [
                f"Workflow Status: {workflow.template_name}",
                f"Workflow ID: {workflow.workflow_id}",
                f"Current Stage: {workflow.current_stage + 1}/{len(workflow.active_toolsets)}",
            ]

            if template and workflow.current_stage < len(template.stages):
                current_stage = template.stages[workflow.current_stage]
                lines.append(f"Current Stage Name: {current_stage.name}")
                lines.append(f"Current Toolset: {current_stage.toolset_id}")
                lines.append(f"Transition Condition: {current_stage.transition_condition}")

            lines.append(f"Completed Stages: {len(workflow.completed_stages)}")
            if workflow.completed_stages:
                lines.append(f"  {', '.join(workflow.completed_stages)}")

            lines.append(f"Active Toolsets: {', '.join(workflow.active_toolsets)}")
            lines.append(f"Total Transitions: {len(workflow.transitions)}")
            lines.append(f"Total Links: {len(workflow.links)}")

            if workflow.started_at:
                elapsed = time.time() - workflow.started_at
                lines.append(f"Elapsed Time: {elapsed:.1f}s")

            result = "\n".join(lines)

        if _metrics is not None:
            duration_ms = (time.perf_counter() - start_time) * 1000
            input_text = status_item.model_dump_json() if hasattr(status_item, "model_dump_json") else str(status_item)
            _metrics.record_invocation("get_workflow_status", input_text, result, duration_ms)

        return result

    return toolset


def get_meta_orchestrator_system_prompt() -> str:
    """Get the system prompt for the meta-orchestrator toolset.

    Returns:
        System prompt string describing when and how to use the meta-orchestrator tools.
    """
    return META_ORCHESTRATOR_SYSTEM_PROMPT
