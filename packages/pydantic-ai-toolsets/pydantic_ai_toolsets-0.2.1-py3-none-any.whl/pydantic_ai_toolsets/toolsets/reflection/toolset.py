"""Reflection toolset for pydantic-ai agents."""

from __future__ import annotations

import sys
import time
import uuid
from typing import Any

from pydantic_ai import Agent
from pydantic_ai.toolsets import FunctionToolset

from .storage import ReflectionStorage, ReflectionStorageProtocol
from .types import (
    CreateOutputItem,
    Critique,
    CritiqueOutputItem,
    RefineOutputItem,
    ReflectionOutput,
)

# =============================================================================
# SYSTEM PROMPT - Contains "when and why" to use the toolset
# =============================================================================

REFLECTION_SYSTEM_PROMPT = """
## Reflection

You have access to tools for improving outputs through reflection:
- `read_reflection`: Read current reflection state
- `create_output`: Create initial output (cycle 0)
- `critique_output`: Critically analyze an output
- `refine_output`: Generate improved version based on critique
- `get_best_output`: Find the best refined output

### When to Use Reflection

Use these tools in these scenarios:
1. Tasks requiring high-quality, polished outputs
2. Problems where initial solutions may have flaws
3. Situations where iterative improvement is valuable
4. Tasks where structured critique helps identify issues
5. Problems where multiple refinement cycles improve results

### Reflection Process

1. **Generate**: Create initial output (cycle 0)
2. **Critique**: Step back and analyze the output critically
   - Identify specific problems (logical errors, missing information, poor structure)
   - Note strengths and positive aspects
   - Provide overall assessment
   - Suggest specific improvements
3. **Refine**: Generate improved version addressing the critique
   - Address all identified problems
   - Incorporate improvement suggestions
   - Mark as final if satisfactory
4. **Repeat**: Optionally repeat critique-refine cycles for further improvement
5. **Select**: Choose the best refined output

### Key Principles

- **Structured Critique**: Use a framework to evaluate outputs systematically
  - Clarity: Is the output clear and understandable?
  - Accuracy: Are there logical errors or incorrect information?
  - Completeness: Is all necessary information included?
  - Structure: Is the output well-organized?
  - Relevance: Does it address the problem/question?

- **Iterative Refinement**: Each cycle should improve upon the previous version
- **Quality Tracking**: Use quality scores to track improvement across cycles
- **Final Output**: Mark outputs as final when no further improvement is needed

### Workflow

1. Call `read_reflection` to see current state
2. Create initial output using `create_output` (if none exists)
3. Critically analyze using `critique_output`
4. Refine using `refine_output` based on critique
5. Repeat steps 3-4 until satisfied
6. Use `get_best_output` for final result

**IMPORTANT**: Always call `read_reflection` before creating, critiquing, or refining.
"""

# =============================================================================
# TOOL DESCRIPTIONS - Contains "how" to use each specific tool
# =============================================================================

READ_REFLECTION_DESCRIPTION = """Read the current reflection state.

Returns all outputs organized by cycle with critiques and refinement chains.

Precondition: Call before every create_output, critique_output, or refine_output.
"""

CREATE_OUTPUT_DESCRIPTION = """Create an initial output (cycle 0).

Parameters:
- content: Initial output content (first attempt)

Returns output ID and cycle info.

Precondition: Call read_reflection first.
"""

CRITIQUE_OUTPUT_DESCRIPTION = """Critically analyze an output and identify problems.

Parameters:
- output_id: Output to critique
- problems: List of specific problems identified
- strengths: List of positive aspects (optional)
- overall_assessment: Overall quality assessment
- improvement_suggestions: Specific improvement suggestions

Returns critique ID and summary.

Precondition: Call read_reflection first.
"""

REFINE_OUTPUT_DESCRIPTION = """Generate improved version based on critique.

Parameters:
- output_id: Output to refine (must have critique)
- refined_content: Improved content addressing critique
- is_final: True if no further refinement needed
- quality_score: Optional quality score (0-100)

Returns refined output ID at cycle+1.

Precondition: Call read_reflection first.
"""

GET_BEST_OUTPUT_DESCRIPTION = """Find the best refined output.

Returns highest-quality output (prefers final, then highest score/cycle).

Precondition: Call read_reflection first.
"""

# Legacy constant for backward compatibility
REFLECTION_TOOL_DESCRIPTION = CREATE_OUTPUT_DESCRIPTION

READ_REFLECTION_DESCRIPTION = """
Read the current reflection state.

**CRITICAL**: Call this BEFORE every create_output, critique_output, or refine_output call to:
- Review the current reflection state
- See which outputs exist and their refinement cycles
- Understand critiques and identified problems
- Know which outputs have been refined and their quality scores
- Make informed decisions about next steps

Returns:
- All outputs with their content, cycles, and quality scores
- All critiques with identified problems and suggestions
- Output refinement chain (parent-child relationships)
- Summary statistics (total outputs, cycles, final outputs)
"""

CREATE_OUTPUT_DESCRIPTION = """
Create an initial output (cycle 0).

Use this tool to generate your first attempt at solving the problem or answering the question.
This initial output will be the starting point for critique and refinement.

**CRITICAL**: Call read_reflection first to see existing outputs.

When creating outputs:
- This should be your initial attempt (cycle 0)
- Don't worry about perfection - you'll refine it later
- Focus on generating a complete response
- The output will be critiqued and refined in subsequent steps
"""

CRITIQUE_OUTPUT_DESCRIPTION = """
Critically analyze an output and identify problems.

Use this tool to step back and examine an output systematically. Identify specific problems
and provide suggestions for improvement.

**CRITICAL**: Call read_reflection first to see which outputs exist.

When critiquing:
- Be specific about problems (logical errors, missing information, poor structure)
- Note strengths and positive aspects
- Provide an overall assessment
- Suggest concrete improvements
- Use a structured framework:
  - Clarity: Is it clear and understandable?
  - Accuracy: Are there errors?
  - Completeness: Is all necessary info included?
  - Structure: Is it well-organized?
  - Relevance: Does it address the problem?

The critique will guide the refinement process.
"""

REFINE_OUTPUT_DESCRIPTION = """
Generate an improved version of an output based on a critique.

Use this tool to create a refined output that addresses the problems identified in a critique.
The refined output should incorporate the improvement suggestions.

**CRITICAL**: Call read_reflection first to see outputs and critiques.

When refining:
- Address ALL problems identified in the critique
- Incorporate improvement suggestions
- The refined output will be at cycle+1 (next refinement cycle)
- Mark as final if you believe no further refinement is needed
- Optionally provide a quality score to track improvement

Refinement process:
1. Review the output being refined
2. Review the critique and identified problems
3. Generate improved version addressing all problems
4. Mark as final if satisfactory, or prepare for another critique cycle
"""

GET_BEST_OUTPUT_DESCRIPTION = """
Find the best refined output.

Use this tool to identify the highest-quality output, typically the most refined version
or the one marked as final.

**CRITICAL**: Call read_reflection first to see all outputs.

Selection criteria:
- Prefer outputs marked as final
- Consider quality scores if available
- Consider refinement cycle (higher cycles may be better)
- Return the output that best addresses the problem

Returns:
- Best output content
- Output metadata (cycle, quality score, etc.)
- Refinement chain showing how it was improved
"""


def create_reflection_toolset(
    storage: ReflectionStorageProtocol | None = None,
    *,
    id: str | None = None,
    track_usage: bool = False,
) -> FunctionToolset[Any]:
    """Create a reflection toolset for iterative output improvement.

    This toolset provides tools for AI agents to improve outputs through critical analysis
    and refinement cycles.

    Args:
        storage: Optional storage backend. Defaults to in-memory ReflectionStorage.
            You can provide a custom storage implementing ReflectionStorageProtocol
            for persistence or integration with other systems.
        id: Optional unique ID for the toolset.

    Returns:
        FunctionToolset compatible with any pydantic-ai agent.

    Example (standalone):
        ```python
        from pydantic_ai import Agent
        from pydantic_ai_toolsets import create_reflection_toolset

        agent = Agent("openai:gpt-4.1", toolsets=[create_reflection_toolset()])
        result = await agent.run("Solve this problem using reflection")
        ```

    Example (with custom storage):
        ```python
        from pydantic_ai_toolsets import create_reflection_toolset, ReflectionStorage

        storage = ReflectionStorage()
        toolset = create_reflection_toolset(storage=storage)

        # After agent runs, access outputs and critiques directly
        print(storage.outputs)
        print(storage.critiques)
        ```
    """
    if storage is not None:
        _storage = storage
    else:
        _storage = ReflectionStorage(track_usage=track_usage)

    toolset: FunctionToolset[Any] = FunctionToolset(id=id)
    _metrics = getattr(_storage, "metrics", None) if hasattr(_storage, "metrics") else None

    def _get_status_summary() -> str:
        """Get one-line status summary."""
        if not _storage.outputs:
            return "Status: ○ Empty"
        max_cycle = max((o.cycle for o in _storage.outputs.values()), default=0)
        total_critiques = len(_storage.critiques)
        final_outputs = sum(1 for o in _storage.outputs.values() if o.is_final)
        if final_outputs > 0:
            return f"Status: ✓ Complete | Cycle {max_cycle}, {total_critiques} critiques"
        return f"Status: ● Active | Cycle {max_cycle}, {total_critiques} critiques"

    def _get_next_hint() -> str:
        """Get contextual hint for next action."""
        if not _storage.outputs:
            return "Use create_output to generate your initial output."
        final_outputs = sum(1 for o in _storage.outputs.values() if o.is_final)
        if final_outputs > 0:
            return "Reflection complete. Use get_best_output to retrieve the final result."
        # Find outputs without critiques
        outputs_with_critiques = {c.output_id for c in _storage.critiques.values()}
        uncritiqued = [o for o in _storage.outputs.values() if o.output_id not in outputs_with_critiques and not o.is_final]
        if uncritiqued:
            return f"Use critique_output on [{uncritiqued[0].output_id[:8]}...] to identify improvements."
        # Find critiqued outputs that haven't been refined
        critiqued_ids = {c.output_id for c in _storage.critiques.values()}
        parent_ids = {o.parent_id for o in _storage.outputs.values() if o.parent_id}
        unrefined = [oid for oid in critiqued_ids if oid not in parent_ids]
        if unrefined:
            return f"Use refine_output on [{unrefined[0][:8]}...] to address the critique."
        return "Continue refining or mark an output as final."

    @toolset.tool(description=READ_REFLECTION_DESCRIPTION)
    async def read_reflection() -> str:
        """Read the current reflection state."""
        start_time = time.perf_counter()

        if not _storage.outputs:
            result = f"{_get_status_summary()}\n\nNo outputs in reflection.\n\nNext: {_get_next_hint()}"
            if _metrics is not None:
                duration_ms = (time.perf_counter() - start_time) * 1000
                _metrics.record_invocation("read_reflection", "", result, duration_ms)
            return result

        lines: list[str] = [_get_status_summary(), "", "Reflection State:"]
        lines.append("")

        # Display outputs by cycle
        outputs_by_cycle: dict[int, list[ReflectionOutput]] = {}
        for output in _storage.outputs.values():
            if output.cycle not in outputs_by_cycle:
                outputs_by_cycle[output.cycle] = []
            outputs_by_cycle[output.cycle].append(output)

        lines.append("Outputs by Refinement Cycle:")
        for cycle in sorted(outputs_by_cycle.keys()):
            outputs = outputs_by_cycle[cycle]
            lines.append(f"  Cycle {cycle}:")
            for output in outputs:
                final_str = " ⭐ FINAL" if output.is_final else ""
                score_str = (
                    f" (quality: {output.quality_score:.1f})"
                    if output.quality_score is not None
                    else ""
                )
                parent_str = (
                    f" (refined from: [{output.parent_id}])"
                    if output.parent_id
                    else " (initial output)"
                )
                lines.append(f"    [{output.output_id}]{final_str}{score_str}{parent_str}")
                lines.append(f"      Content: {output.content}")
                lines.append("")

        # Display critiques
        if _storage.critiques:
            lines.append("Critiques:")
            for critique in _storage.critiques.values():
                output = _storage.outputs.get(critique.output_id)
                output_ref = (
                    f"[{critique.output_id}]" if output else f"[{critique.output_id}] (missing)"
                )
                lines.append(f"  Critique [{critique.critique_id}] for output {output_ref}:")
                lines.append(f"    Overall Assessment: {critique.overall_assessment}")
                if critique.problems:
                    lines.append("    Problems Identified:")
                    for problem in critique.problems:
                        lines.append(f"      - {problem}")
                if critique.strengths:
                    lines.append("    Strengths:")
                    for strength in critique.strengths:
                        lines.append(f"      + {strength}")
                if critique.improvement_suggestions:
                    lines.append("    Improvement Suggestions:")
                    for suggestion in critique.improvement_suggestions:
                        lines.append(f"      → {suggestion}")
                lines.append("")

        # Display refinement chains
        root_outputs = [o for o in _storage.outputs.values() if o.parent_id is None]
        if root_outputs:
            lines.append("Refinement Chains:")
            for root in root_outputs:
                chain: list[ReflectionOutput] = [root]
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

                chain_str = " → ".join([f"[{o.output_id}] (cycle {o.cycle})" for o in chain])
                lines.append(f"  {chain_str}")
                if chain[-1].is_final:
                    lines.append(f"    Final output: [{chain[-1].output_id}]")
            lines.append("")

        # Summary statistics
        total_outputs = len(_storage.outputs)
        total_critiques = len(_storage.critiques)
        final_outputs = sum(1 for o in _storage.outputs.values() if o.is_final)
        max_cycle = max((o.cycle for o in _storage.outputs.values()), default=0)
        scored_outputs = sum(1 for o in _storage.outputs.values() if o.quality_score is not None)

        lines.append("Summary:")
        lines.append(f"  Total outputs: {total_outputs}")
        lines.append(f"  Total critiques: {total_critiques}")
        lines.append(f"  Final outputs: {final_outputs}")
        lines.append(f"  Maximum refinement cycle: {max_cycle}")
        lines.append(f"  Scored outputs: {scored_outputs}")

        lines.append("")
        lines.append(f"Next: {_get_next_hint()}")

        result = "\n".join(lines)

        if _metrics is not None:
            duration_ms = (time.perf_counter() - start_time) * 1000
            _metrics.record_invocation("read_reflection", "", result, duration_ms)

        return result

    @toolset.tool(description=CREATE_OUTPUT_DESCRIPTION)
    async def create_output(output: CreateOutputItem) -> str:
        """Create an initial output (cycle 0)."""
        start_time = time.perf_counter()
        input_text = output.model_dump_json() if _metrics else ""

        output_id = str(uuid.uuid4())

        new_output = ReflectionOutput(
            output_id=output_id,
            content=output.content,
            cycle=0,
            parent_id=None,
            is_final=False,
            quality_score=None,
        )

        _storage.outputs = new_output

        result = f"Created initial output [{output_id}] at cycle 0"

        if _metrics is not None:
            duration_ms = (time.perf_counter() - start_time) * 1000
            _metrics.record_invocation("create_output", input_text, result, duration_ms)

        return result

    @toolset.tool(description=CRITIQUE_OUTPUT_DESCRIPTION)
    async def critique_output(critique: CritiqueOutputItem) -> str:
        """Critically analyze an output and identify problems."""
        start_time = time.perf_counter()
        input_text = critique.model_dump_json() if _metrics else ""

        if critique.output_id not in _storage.outputs:
            available = ", ".join([o.output_id[:8] for o in list(_storage.outputs.values())[:5]])
            return (
                f"Error: Output '{critique.output_id[:8]}...' not found. "
                f"Available: [{available}]. Call read_reflection."
            )

        critique_id = str(uuid.uuid4())

        new_critique = Critique(
            critique_id=critique_id,
            output_id=critique.output_id,
            problems=critique.problems,
            strengths=critique.strengths,
            overall_assessment=critique.overall_assessment,
            improvement_suggestions=critique.improvement_suggestions,
        )

        _storage.critiques = new_critique

        result_parts = [
            f"Created critique [{critique_id}] for output [{critique.output_id}]",
            f"Identified {len(critique.problems)} problem(s)",
            f"Provided {len(critique.improvement_suggestions)} improvement suggestion(s)",
        ]

        result = ". ".join(result_parts)

        if _metrics is not None:
            duration_ms = (time.perf_counter() - start_time) * 1000
            _metrics.record_invocation("critique_output", input_text, result, duration_ms)

        return result

    @toolset.tool(description=REFINE_OUTPUT_DESCRIPTION)
    async def refine_output(refine: RefineOutputItem) -> str:
        """Generate an improved version of an output based on a critique."""
        start_time = time.perf_counter()
        input_text = refine.model_dump_json() if _metrics else ""

        if refine.output_id not in _storage.outputs:
            available = ", ".join([o.output_id[:8] for o in list(_storage.outputs.values())[:5]])
            return (
                f"Error: Output '{refine.output_id[:8]}...' not found. "
                f"Available: [{available}]. Call read_reflection."
            )

        parent_output = _storage.outputs[refine.output_id]

        # Check if there's a critique for this output
        critiques_for_output = [
            c for c in _storage.critiques.values() if c.output_id == refine.output_id
        ]
        if not critiques_for_output:
            return (
                f"Warning: No critique found for output '{refine.output_id}'. "
                "Consider critiquing the output first to guide refinement."
            )

        output_id = str(uuid.uuid4())
        new_cycle = parent_output.cycle + 1

        new_output = ReflectionOutput(
            output_id=output_id,
            content=refine.refined_content,
            cycle=new_cycle,
            parent_id=refine.output_id,
            is_final=refine.is_final,
            quality_score=refine.quality_score,
        )

        _storage.outputs = new_output

        result_parts = [
            f"Created refined output [{output_id}] at cycle {new_cycle}",
            f"Refined from [{refine.output_id}] (cycle {parent_output.cycle})",
        ]
        if refine.is_final:
            result_parts.append("⭐ MARKED AS FINAL")
        if refine.quality_score is not None:
            result_parts.append(f"Quality score: {refine.quality_score:.1f}")

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
            return "No outputs found. Use create_output to start."

        # Prefer final outputs
        final_outputs = [o for o in _storage.outputs.values() if o.is_final]
        if final_outputs:
            # Among final outputs, prefer highest quality score or highest cycle
            best = max(
                final_outputs,
                key=lambda o: (
                    o.quality_score if o.quality_score is not None else 0,
                    o.cycle,
                ),
            )
        else:
            # Among all outputs, prefer highest quality score or highest cycle
            best = max(
                _storage.outputs.values(),
                key=lambda o: (
                    o.quality_score if o.quality_score is not None else 0,
                    o.cycle,
                ),
            )

        lines: list[str] = [f"Best Output: [{best.output_id}]"]
        lines.append(f"Cycle: {best.cycle}")
        if best.quality_score is not None:
            lines.append(f"Quality Score: {best.quality_score:.1f}")
        if best.is_final:
            lines.append("Status: ⭐ FINAL")
        lines.append("")
        lines.append("Content:")
        lines.append(best.content)
        lines.append("")

        # Show refinement chain
        chain: list[ReflectionOutput] = []
        current: ReflectionOutput | None = best
        while current:
            chain.insert(0, current)
            current = (
                _storage.outputs.get(current.parent_id) if current.parent_id else None
            )

        if len(chain) > 1:
            lines.append("Refinement Chain:")
            for i, output in enumerate(chain):
                marker = " → " if i < len(chain) - 1 else " (best)"
                lines.append(f"  Cycle {output.cycle}: [{output.output_id}]{marker}")

        result = "\n".join(lines)

        if _metrics is not None:
            duration_ms = (time.perf_counter() - start_time) * 1000
            _metrics.record_invocation("get_best_output", "", result, duration_ms)

        return result

    return toolset


def get_reflection_system_prompt() -> str:
    """Get the system prompt for reflection-based reasoning.

    Returns:
        System prompt string that can be used with pydantic-ai agents.
    """
    return REFLECTION_SYSTEM_PROMPT


def create_reflection_toolset_agent(model: str = "openrouter:x-ai/grok-4.1-fast") -> Agent:
    """Create a Pydantic-ai agent with the reflection toolset.

    Args:
        model: The model to use for the agent.

    Returns:
        Pydantic-ai agent with the reflection toolset.
    """
    storage = ReflectionStorage()
    toolset = create_reflection_toolset(storage=storage)
    agent = Agent(
        model,
        system_prompt="""
        You are a reflection agent. You have access to tools for improving outputs through reflection:
        - `read_reflection`: Read the current reflection state
        - `create_output`: Create initial output
        - `critique_output`: Critically analyze an output
        - `refine_output`: Generate improved version based on critique
        - `get_best_output`: Find the best refined output

        **IMPORTANT**: Use these tools to improve outputs through critical analysis and refinement cycles.
        """,
        toolsets=[toolset]
    )

    @agent.instructions
    async def add_prompt() -> str:
        """Add the reflection system prompt."""
        return get_reflection_system_prompt()

    return agent
