"""Self-refinement toolset for pydantic-ai agents."""

from __future__ import annotations

import sys
import time
import uuid
from typing import Any

from pydantic_ai import Agent
from pydantic_ai.toolsets import FunctionToolset

from .storage import SelfRefineStorage, SelfRefineStorageProtocol
from .types import (
    Feedback,
    GenerateOutputItem,
    ProvideFeedbackItem,
    RefinementOutput,
    RefineOutputItem,
)

# =============================================================================
# SYSTEM PROMPT - Contains "when and why" to use the toolset
# =============================================================================

SELF_REFINE_SYSTEM_PROMPT = """
## Self-Refinement

You have access to tools for improving outputs through iterative self-refinement:
- `read_refinement_state`: Read current refinement state
- `generate_output`: Create initial output (iteration 0)
- `provide_feedback`: Provide structured, actionable feedback
- `refine_output`: Generate improved version based on feedback
- `get_best_output`: Find the best refined output

### When to Use Self-Refinement

Use these tools in these scenarios:
1. Tasks requiring high-quality, polished outputs
2. Problems where initial solutions may have flaws
3. Situations where iterative improvement is valuable
4. Tasks where structured feedback helps identify issues
5. Problems where multiple refinement cycles improve results
6. When you need to meet specific quality thresholds

### Self-Refinement Process

1. **Generate**: Create initial output (iteration 0)
   - Set quality_threshold if you have a target quality level
   - Set iteration_limit if you want to cap refinement cycles (typically 2-3)
2. **Feedback**: Provide detailed, actionable feedback on the output
   - Use structured feedback types: additive, subtractive, transformative, corrective
   - Evaluate multiple dimensions: factuality, coherence, completeness, style
   - Prioritize feedback (higher priority = more important)
   - Indicate if refinement should continue
3. **Refine**: Generate improved version incorporating the feedback
   - Address all feedback, especially high-priority items
   - Provide quality score to track improvement
   - Mark as final if quality threshold is met or no further improvement needed
4. **Repeat**: Continue feedback-refine cycle until:
   - Quality threshold is met (quality_score >= quality_threshold)
   - Iteration limit is reached (iteration >= iteration_limit)
   - Feedback indicates no further improvements needed
5. **Select**: Choose the best refined output

### Feedback Types

- **Additive**: Missing information about X, should include Y
- **Subtractive**: Remove redundant section Z
- **Transformative**: Restructure argument to lead with conclusion
- **Corrective**: Fix factual error in paragraph 3

### Feedback Dimensions

- **Factuality**: Accuracy and correctness of information
- **Coherence**: Logical flow and consistency
- **Completeness**: All necessary information included
- **Style**: Writing style and clarity

### Key Principles

- **Structured Feedback**: Use feedback types and dimensions systematically
- **Actionable Suggestions**: Feedback should be specific enough to guide improvement
- **Weighted Feedback**: Prioritize certain aspects (e.g., correctness > style)
- **Iterative Convergence**: Quality typically improves most in first 2-3 iterations
- **Quality Tracking**: Use quality scores to track improvement and compare against thresholds

### Workflow

1. Call `read_refinement_state` to see current state
2. Generate initial output using `generate_output` (if none exists)
3. Provide feedback using `provide_feedback`
4. Refine using `refine_output` based on feedback
5. Repeat steps 3-4 until satisfied or limits reached
6. Use `get_best_output` for final result

**IMPORTANT**: Always call `read_refinement_state` before generating, providing feedback, or refining.
"""

# =============================================================================
# TOOL DESCRIPTIONS - Contains "how" to use each specific tool
# =============================================================================

READ_REFINEMENT_STATE_DESCRIPTION = """Read the current self-refinement state.

Returns all outputs organized by iteration with feedbacks and refinement chains.

Precondition: Call before every generate_output, provide_feedback, or refine_output.
"""

GENERATE_OUTPUT_DESCRIPTION = """Generate an initial output (iteration 0).

Parameters:
- content: Initial output content
- quality_threshold: Optional target quality (0-100)
- iteration_limit: Optional max iterations (typically 2-3)

Returns output ID and iteration info.

Precondition: Call read_refinement_state first.
"""

PROVIDE_FEEDBACK_DESCRIPTION = """Provide structured, actionable feedback on an output.

Parameters:
- output_id: Output to provide feedback on
- feedback_type: additive, subtractive, transformative, or corrective
- dimension: factuality, coherence, completeness, or style
- feedback_text: Specific, actionable feedback
- priority: Priority level (higher = more important)
- should_continue_refining: Whether to continue refinement

Returns feedback ID and summary.

Precondition: Call read_refinement_state first.
"""

REFINE_OUTPUT_DESCRIPTION = """Generate improved version based on feedback.

Parameters:
- output_id: Output to refine (must have feedback)
- refined_content: Improved content addressing feedback
- quality_score: Quality score (0-100) to track improvement
- is_final: True if quality threshold met or no further improvement needed

Returns refined output ID at iteration+1.

Precondition: Call read_refinement_state first.
"""

GET_BEST_OUTPUT_DESCRIPTION = """Find the best refined output.

Returns highest-quality output (prefers final, then highest score/iteration).

Precondition: Call read_refinement_state first.
"""

# Legacy constant for backward compatibility
SELF_REFINE_TOOL_DESCRIPTION = GENERATE_OUTPUT_DESCRIPTION

READ_REFINEMENT_STATE_DESCRIPTION = """
Read the current self-refinement state.

**CRITICAL**: Call this BEFORE every generate_output, provide_feedback, or refine_output call to:
- Review the current refinement state
- See which outputs exist and their refinement iterations
- Understand feedback and identified areas for improvement
- Track quality scores and thresholds
- Know iteration limits and current iteration counts
- Make informed decisions about next steps

Returns:
- All outputs with their content, iterations, and quality scores
- All feedback with types, dimensions, and suggestions
- Output refinement chain (parent-child relationships)
- Summary statistics (total outputs, iterations, final outputs, quality tracking)
"""

GENERATE_OUTPUT_DESCRIPTION = """
Generate an initial output (iteration 0).

Use this tool to create your first attempt at solving the problem or answering the question.
This initial output will be the starting point for feedback and refinement.

**CRITICAL**: Call read_refinement_state first to see existing outputs.

When generating outputs:
- This should be your initial attempt (iteration 0)
- Don't worry about perfection - you'll refine it later
- Focus on generating a complete response
- Optionally set quality_threshold if you have a target quality level
- Optionally set iteration_limit if you want to cap refinement cycles (typically 2-3)
- The output will receive feedback and be refined in subsequent steps
"""

PROVIDE_FEEDBACK_DESCRIPTION = """
Provide structured, actionable feedback on an output.

Use this tool to analyze an output systematically and provide detailed feedback
with specific types and dimensions to guide refinement.

**CRITICAL**: Call read_refinement_state first to see which outputs exist.

When providing feedback:
- Use structured feedback types:
  - **Additive**: Missing information about X, should include Y
  - **Subtractive**: Remove redundant section Z
  - **Transformative**: Restructure argument to lead with conclusion
  - **Corrective**: Fix factual error in paragraph 3
- Evaluate multiple dimensions:
  - **Factuality**: Accuracy and correctness
  - **Coherence**: Logical flow and consistency
  - **Completeness**: All necessary information included
  - **Style**: Writing style and clarity
- Prioritize feedback (higher priority = more important)
  - Typically prioritize: correctness > completeness > coherence > style
- Be specific and actionable in suggestions
- Provide overall assessment
- Indicate if refinement should continue

The feedback will guide the refinement process, with high-priority items addressed first.
"""

REFINE_OUTPUT_DESCRIPTION = """
Generate an improved version of an output based on feedback.

Use this tool to create a refined output that addresses the feedback provided.
The refined output should incorporate all suggestions, especially high-priority ones.

**CRITICAL**: Call read_refinement_state first to see outputs and feedback.

When refining:
- Address ALL feedback, especially high-priority items
- Incorporate improvement suggestions systematically
- The refined output will be at iteration+1 (next refinement iteration)
- Provide quality score to track improvement
- Compare quality_score against quality_threshold if set
- Check if iteration_limit has been reached
- Mark as final if:
  - Quality threshold is met (quality_score >= quality_threshold)
  - Iteration limit is reached (iteration >= iteration_limit)
  - You believe no further refinement is needed

Refinement process:
1. Review the output being refined
2. Review all feedback and identified areas for improvement
3. Prioritize high-priority feedback items
4. Generate improved version addressing all feedback
5. Provide quality score
6. Mark as final if thresholds are met or satisfactory
"""

GET_BEST_OUTPUT_DESCRIPTION = """
Find the best refined output.

Use this tool to identify the highest-quality output, typically the most refined version
or the one marked as final.

**CRITICAL**: Call read_refinement_state first to see all outputs.

Selection criteria:
- Prefer outputs marked as final
- Consider quality scores if available
- Consider refinement iteration (higher iterations may be better)
- Consider quality threshold achievement
- Return the output that best addresses the problem

Returns:
- Best output content
- Output metadata (iteration, quality score, etc.)
- Refinement chain showing how it was improved
"""


def create_self_refine_toolset(
    storage: SelfRefineStorageProtocol | None = None,
    *,
    id: str | None = None,
    track_usage: bool = False,
) -> FunctionToolset[Any]:
    """Create a self-refinement toolset for iterative output improvement.

    This toolset provides tools for AI agents to improve outputs through structured feedback
    and refinement cycles, with support for quality thresholds and iteration limits.

    Args:
        storage: Optional storage backend. Defaults to in-memory SelfRefineStorage.
            You can provide a custom storage implementing SelfRefineStorageProtocol
            for persistence or integration with other systems.
        id: Optional unique ID for the toolset.

    Returns:
        FunctionToolset compatible with any pydantic-ai agent.

    Example (standalone):
        ```python
        from pydantic_ai import Agent
        from pydantic_ai_toolsets import create_self_refine_toolset

        agent = Agent("openai:gpt-4.1", toolsets=[create_self_refine_toolset()])
        result = await agent.run("Solve this problem using self-refinement")
        ```

    Example (with custom storage):
        ```python
        from pydantic_ai_toolsets import create_self_refine_toolset, SelfRefineStorage

        storage = SelfRefineStorage()
        toolset = create_self_refine_toolset(storage=storage)

        # After agent runs, access outputs and feedbacks directly
        print(storage.outputs)
        print(storage.feedbacks)
        ```
    """
    if storage is not None:
        _storage = storage
    else:
        _storage = SelfRefineStorage(track_usage=track_usage)

    toolset: FunctionToolset[Any] = FunctionToolset(id=id)
    _metrics = getattr(_storage, "metrics", None) if hasattr(_storage, "metrics") else None

    def _get_status_summary() -> str:
        """Get one-line status summary."""
        if not _storage.outputs:
            return "Status: ○ Empty"
        max_iter = max((o.iteration for o in _storage.outputs.values()), default=0)
        final_outputs = sum(1 for o in _storage.outputs.values() if o.is_final)
        # Check for iteration limit
        limit = next((o.iteration_limit for o in _storage.outputs.values() if o.iteration_limit), None)
        limit_str = f"/{limit}" if limit else ""
        # Check for quality threshold
        threshold_met = sum(
            1 for o in _storage.outputs.values()
            if o.quality_threshold and o.quality_score and o.quality_score >= o.quality_threshold
        )
        if final_outputs > 0 or threshold_met > 0:
            return f"Status: ✓ Complete | Iteration {max_iter}{limit_str}"
        return f"Status: ● Active | Iteration {max_iter}{limit_str}"

    def _get_next_hint() -> str:
        """Get contextual hint for next action."""
        if not _storage.outputs:
            return "Use generate_output to create your initial output."
        final_outputs = sum(1 for o in _storage.outputs.values() if o.is_final)
        if final_outputs > 0:
            return "Refinement complete. Use get_best_output to retrieve the final result."
        # Find outputs without feedback
        outputs_with_feedback = {f.output_id for f in _storage.feedbacks.values()}
        unfeedback = [o for o in _storage.outputs.values() if o.output_id not in outputs_with_feedback and not o.is_final]
        if unfeedback:
            return f"Use provide_feedback on [{unfeedback[0].output_id}] to identify improvements."
        # Find outputs with feedback that haven't been refined
        parent_ids = {o.parent_id for o in _storage.outputs.values() if o.parent_id}
        unrefined = [oid for oid in outputs_with_feedback if oid not in parent_ids]
        if unrefined:
            return f"Use refine_output on [{unrefined[0]}] to address the feedback."
        return "Continue refining or mark an output as final."

    @toolset.tool(description=READ_REFINEMENT_STATE_DESCRIPTION)
    async def read_refinement_state() -> str:
        """Read the current self-refinement state."""
        start_time = time.perf_counter()

        if not _storage.outputs:
            result = f"{_get_status_summary()}\n\nNo outputs in refinement.\n\nNext: {_get_next_hint()}"
            if _metrics is not None:
                duration_ms = (time.perf_counter() - start_time) * 1000
                _metrics.record_invocation("read_refinement_state", "", result, duration_ms)
            return result

        lines: list[str] = [_get_status_summary(), "", "Self-Refinement State:"]
        lines.append("")

        # Display outputs by iteration
        outputs_by_iteration: dict[int, list[RefinementOutput]] = {}
        for output in _storage.outputs.values():
            if output.iteration not in outputs_by_iteration:
                outputs_by_iteration[output.iteration] = []
            outputs_by_iteration[output.iteration].append(output)

        lines.append("Outputs by Refinement Iteration:")
        for iteration in sorted(outputs_by_iteration.keys()):
            outputs = outputs_by_iteration[iteration]
            lines.append(f"  Iteration {iteration}:")
            for output in outputs:
                final_str = " ⭐ FINAL" if output.is_final else ""
                score_str = (
                    f" (quality: {output.quality_score:.1f})"
                    if output.quality_score is not None
                    else ""
                )
                threshold_str = (
                    f" (threshold: {output.quality_threshold:.1f})"
                    if output.quality_threshold is not None
                    else ""
                )
                limit_str = (
                    f" (limit: {output.iteration_limit})"
                    if output.iteration_limit is not None
                    else ""
                )
                parent_str = (
                    f" (refined from: [{output.parent_id}])"
                    if output.parent_id
                    else " (initial output)"
                )
                output_line = (
                    f"    [{output.output_id}]{final_str}{score_str}"
                    f"{threshold_str}{limit_str}{parent_str}"
                )
                lines.append(output_line)
                lines.append(f"      Content: {output.content}")
                lines.append("")

        # Display feedback grouped by output
        if _storage.feedbacks:
            lines.append("Feedback:")
            feedbacks_by_output: dict[str, list[Feedback]] = {}
            for feedback in _storage.feedbacks.values():
                if feedback.output_id not in feedbacks_by_output:
                    feedbacks_by_output[feedback.output_id] = []
                feedbacks_by_output[feedback.output_id].append(feedback)

            for output_id, feedbacks in feedbacks_by_output.items():
                output = _storage.outputs.get(output_id)
                output_ref = (
                    f"[{output_id}]" if output else f"[{output_id}] (missing)"
                )
                lines.append(f"  Feedback for output {output_ref}:")
                # Sort by priority (highest first)
                sorted_feedbacks = sorted(feedbacks, key=lambda f: f.priority, reverse=True)
                for feedback in sorted_feedbacks:
                    priority_str = (
                        f" (priority: {feedback.priority:.2f})"
                        if feedback.priority != 0.5
                        else ""
                    )
                    lines.append(
                        f"    [{feedback.feedback_id}] {feedback.feedback_type.value} / "
                        f"{feedback.dimension.value}{priority_str}"
                    )
                    lines.append(f"      Description: {feedback.description}")
                    lines.append(f"      Suggestion: {feedback.suggestion}")
                    lines.append("")
                lines.append("")

        # Display refinement chains
        root_outputs = [o for o in _storage.outputs.values() if o.parent_id is None]
        if root_outputs:
            lines.append("Refinement Chains:")
            for root in root_outputs:
                chain: list[RefinementOutput] = [root]
                current = root
                while True:
                    # Find children
                    children = [
                        o for o in _storage.outputs.values() if o.parent_id == current.output_id
                    ]
                    if not children:
                        break
                    # Take the first child (could be multiple, but show one chain)
                    current = children[0]
                    chain.append(current)

                chain_str = " → ".join([f"[{o.output_id}] (iter {o.iteration})" for o in chain])
                lines.append(f"  {chain_str}")
                if chain[-1].is_final:
                    lines.append(f"    Final output: [{chain[-1].output_id}]")
                    if chain[-1].quality_score is not None:
                        lines.append(f"    Quality score: {chain[-1].quality_score:.1f}")
                        if chain[-1].quality_threshold is not None:
                            threshold_met = chain[-1].quality_score >= chain[-1].quality_threshold
                            lines.append(
                                f"    Threshold {'✓ MET' if threshold_met else '✗ NOT MET'}"
                            )
            lines.append("")

        # Summary statistics
        total_outputs = len(_storage.outputs)
        total_feedbacks = len(_storage.feedbacks)
        final_outputs = sum(1 for o in _storage.outputs.values() if o.is_final)
        max_iteration = max((o.iteration for o in _storage.outputs.values()), default=0)
        scored_outputs = sum(1 for o in _storage.outputs.values() if o.quality_score is not None)
        threshold_outputs = sum(
            1 for o in _storage.outputs.values() if o.quality_threshold is not None
        )
        threshold_met_outputs = sum(
            1
            for o in _storage.outputs.values()
            if o.quality_threshold is not None
            and o.quality_score is not None
            and o.quality_score >= o.quality_threshold
        )

        lines.append("Summary:")
        lines.append(f"  Total outputs: {total_outputs}")
        lines.append(f"  Total feedback items: {total_feedbacks}")
        lines.append(f"  Final outputs: {final_outputs}")
        lines.append(f"  Maximum refinement iteration: {max_iteration}")
        lines.append(f"  Scored outputs: {scored_outputs}")
        if threshold_outputs > 0:
            lines.append(f"  Outputs with quality threshold: {threshold_outputs}")
            lines.append(f"  Thresholds met: {threshold_met_outputs}")

        lines.append("")
        lines.append(f"Next: {_get_next_hint()}")

        result = "\n".join(lines)

        if _metrics is not None:
            duration_ms = (time.perf_counter() - start_time) * 1000
            _metrics.record_invocation("read_refinement_state", "", result, duration_ms)

        return result

    @toolset.tool(description=GENERATE_OUTPUT_DESCRIPTION)
    async def generate_output(output: GenerateOutputItem) -> str:
        """Generate an initial output (iteration 0)."""
        start_time = time.perf_counter()
        input_text = output.model_dump_json() if _metrics else ""

        output_id = str(uuid.uuid4())

        new_output = RefinementOutput(
            output_id=output_id,
            content=output.content,
            iteration=0,
            parent_id=None,
            is_final=False,
            quality_score=None,
            quality_threshold=output.quality_threshold,
            iteration_limit=output.iteration_limit,
        )

        _storage.outputs = new_output

        result_parts = [f"Generated initial output [{output_id}] at iteration 0"]
        if output.quality_threshold is not None:
            result_parts.append(f"Quality threshold: {output.quality_threshold:.1f}")
        if output.iteration_limit is not None:
            result_parts.append(f"Iteration limit: {output.iteration_limit}")

        result = ". ".join(result_parts)

        if _metrics is not None:
            duration_ms = (time.perf_counter() - start_time) * 1000
            _metrics.record_invocation("generate_output", input_text, result, duration_ms)

        return result

    @toolset.tool(description=PROVIDE_FEEDBACK_DESCRIPTION)
    async def provide_feedback(feedback: ProvideFeedbackItem) -> str:
        """Provide structured, actionable feedback on an output."""
        start_time = time.perf_counter()
        input_text = feedback.model_dump_json() if _metrics else ""

        if feedback.output_id not in _storage.outputs:
            available = ", ".join([o.output_id for o in _storage.outputs.values()])
            return (
                f"Error: Output '{feedback.output_id}' not found. "
                f"Available: [{available}]. Call read_refinement_state."
            )

        output = _storage.outputs[feedback.output_id]

        # Check iteration limit
        if output.iteration_limit is not None and output.iteration >= output.iteration_limit:
            return (
                f"Warning: Iteration limit ({output.iteration_limit}) reached for output "
                f"'{feedback.output_id}'. Consider marking as final or increasing limit."
            )

        feedback_ids: list[str] = []
        for item in feedback.feedback_items:
            feedback_id = str(uuid.uuid4())
            feedback_ids.append(feedback_id)

            new_feedback = Feedback(
                feedback_id=feedback_id,
                output_id=feedback.output_id,
                feedback_type=item.feedback_type,
                dimension=item.dimension,
                description=item.description,
                suggestion=item.suggestion,
                priority=item.priority,
                is_actionable=item.priority > 0.0,  # Non-zero priority implies actionable
            )

            _storage.feedbacks = new_feedback

        result_parts = [
            f"Provided {len(feedback.feedback_items)} feedback item(s) "
            f"for output [{feedback.output_id}]",
            f"Overall assessment: {feedback.overall_assessment}",
        ]
        if not feedback.should_continue_refining:
            result_parts.append("Refinement should STOP - no further improvements needed")
        else:
            result_parts.append("Refinement should CONTINUE")

        result = ". ".join(result_parts)

        if _metrics is not None:
            duration_ms = (time.perf_counter() - start_time) * 1000
            _metrics.record_invocation("provide_feedback", input_text, result, duration_ms)

        return result

    @toolset.tool(description=REFINE_OUTPUT_DESCRIPTION)
    async def refine_output(refine: RefineOutputItem) -> str:
        """Generate an improved version of an output based on feedback."""
        start_time = time.perf_counter()
        input_text = refine.model_dump_json() if _metrics else ""

        if refine.output_id not in _storage.outputs:
            available = ", ".join([o.output_id for o in _storage.outputs.values()])
            return (
                f"Error: Output '{refine.output_id}' not found. "
                f"Available: [{available}]. Call read_refinement_state."
            )

        parent_output = _storage.outputs[refine.output_id]

        # Check iteration limit
        if (
            parent_output.iteration_limit is not None
            and parent_output.iteration >= parent_output.iteration_limit
        ):
            return (
                f"Error: Iteration limit ({parent_output.iteration_limit}) reached. "
                f"Cannot refine output [{refine.output_id}] further."
            )

        # Check if there's feedback for this output
        feedbacks_for_output = [
            f for f in _storage.feedbacks.values() if f.output_id == refine.output_id
        ]
        if not feedbacks_for_output:
            return (
                f"Warning: No feedback found for output '{refine.output_id}'. "
                "Consider providing feedback first to guide refinement."
            )

        output_id = str(uuid.uuid4())
        new_iteration = parent_output.iteration + 1

        # Determine if should be final based on quality threshold or explicit flag
        is_final = refine.is_final
        if (
            not is_final
            and parent_output.quality_threshold is not None
            and refine.quality_score is not None
        ):
            is_final = refine.quality_score >= parent_output.quality_threshold

        # Check iteration limit
        if (
            parent_output.iteration_limit is not None
            and new_iteration >= parent_output.iteration_limit
        ):
            is_final = True  # Force final if limit reached

        new_output = RefinementOutput(
            output_id=output_id,
            content=refine.refined_content,
            iteration=new_iteration,
            parent_id=refine.output_id,
            is_final=is_final,
            quality_score=refine.quality_score,
            quality_threshold=parent_output.quality_threshold,  # Inherit from parent
            iteration_limit=parent_output.iteration_limit,  # Inherit from parent
        )

        _storage.outputs = new_output

        result_parts = [
            f"Created refined output [{output_id}] at iteration {new_iteration}",
            f"Refined from [{refine.output_id}] (iteration {parent_output.iteration})",
        ]
        if is_final:
            result_parts.append("⭐ MARKED AS FINAL")
        if refine.quality_score is not None:
            result_parts.append(f"Quality score: {refine.quality_score:.1f}")
            if parent_output.quality_threshold is not None:
                threshold_met = refine.quality_score >= parent_output.quality_threshold
                result_parts.append(
                    f"Quality threshold {'✓ MET' if threshold_met else '✗ NOT MET'}"
                )
        if parent_output.iteration_limit is not None:
            result_parts.append(
                f"Iteration limit: {new_iteration}/{parent_output.iteration_limit}"
            )

        result = ". ".join(result_parts)

        if _metrics is not None:
            duration_ms = (time.perf_counter() - start_time) * 1000
            _metrics.record_invocation("refine_output", input_text, result, duration_ms)

        return result

    @toolset.tool(description=GET_BEST_OUTPUT_DESCRIPTION)
    async def get_best_output() -> str:
        """Find the best refined output."""
        start_time = time.perf_counter()

        if not _storage.outputs:
            return "No outputs found. Use generate_output to start."

        # Prefer final outputs
        final_outputs = [o for o in _storage.outputs.values() if o.is_final]
        if final_outputs:
            # Among final outputs, prefer highest quality score or highest iteration
            best = max(
                final_outputs,
                key=lambda o: (
                    o.quality_score if o.quality_score is not None else 0,
                    o.iteration,
                ),
            )
        else:
            # Among all outputs, prefer highest quality score or highest iteration
            best = max(
                _storage.outputs.values(),
                key=lambda o: (
                    o.quality_score if o.quality_score is not None else 0,
                    o.iteration,
                ),
            )

        lines: list[str] = [f"Best Output: [{best.output_id}]"]
        lines.append(f"Iteration: {best.iteration}")
        if best.quality_score is not None:
            lines.append(f"Quality Score: {best.quality_score:.1f}")
        if best.quality_threshold is not None:
            lines.append(f"Quality Threshold: {best.quality_threshold:.1f}")
            if best.quality_score is not None:
                threshold_met = best.quality_score >= best.quality_threshold
                lines.append(f"Threshold Status: {'✓ MET' if threshold_met else '✗ NOT MET'}")
        if best.is_final:
            lines.append("Status: ⭐ FINAL")
        lines.append("")
        lines.append("Content:")
        lines.append(best.content)
        lines.append("")

        # Show refinement chain
        chain: list[RefinementOutput] = []
        current: RefinementOutput | None = best
        while current:
            chain.insert(0, current)
            current = (
                _storage.outputs.get(current.parent_id) if current.parent_id else None
            )

        if len(chain) > 1:
            lines.append("Refinement Chain:")
            for i, output in enumerate(chain):
                marker = " → " if i < len(chain) - 1 else " (best)"
                lines.append(f"  Iteration {output.iteration}: [{output.output_id}]{marker}")

        result = "\n".join(lines)

        if _metrics is not None:
            duration_ms = (time.perf_counter() - start_time) * 1000
            _metrics.record_invocation("get_best_output", "", result, duration_ms)

        return result

    return toolset


def get_self_refine_system_prompt() -> str:
    """Get the system prompt for self-refinement-based reasoning.

    Returns:
        System prompt string that can be used with pydantic-ai agents.
    """
    return SELF_REFINE_SYSTEM_PROMPT


def create_self_refine_toolset_agent(model: str = "openrouter:x-ai/grok-4.1-fast") -> Agent:
    """Create a Pydantic-ai agent with the self-refinement toolset.

    Args:
        model: The model to use for the agent.

    Returns:
        Pydantic-ai agent with the self-refinement toolset.
    """
    storage = SelfRefineStorage()
    toolset = create_self_refine_toolset(storage=storage)
    agent = Agent(
        model,
        system_prompt="""
        You are a self-refinement agent. You have access to tools for improving outputs through iterative refinement:
        - `read_refinement_state`: Read the current refinement state
        - `generate_output`: Create initial output
        - `provide_feedback`: Provide structured, actionable feedback
        - `refine_output`: Generate improved version based on feedback
        - `get_best_output`: Find the best refined output

        **IMPORTANT**: Use these tools to improve outputs through structured feedback and refinement cycles.
        """,
        toolsets=[toolset]
    )

    @agent.instructions
    async def add_prompt() -> str:
        """Add the self-refinement system prompt."""
        return get_self_refine_system_prompt()

    return agent

