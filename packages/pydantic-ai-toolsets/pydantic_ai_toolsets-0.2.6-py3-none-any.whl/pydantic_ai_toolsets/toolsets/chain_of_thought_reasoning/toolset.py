"""Chain of thoughts toolset for pydantic-ai agents."""

from __future__ import annotations

import sys
import time
from typing import Any

from pydantic_ai import Agent
from pydantic_ai.toolsets import FunctionToolset

from .storage import CoTStorage, CoTStorageProtocol
from .types import Thought

# =============================================================================
# SYSTEM PROMPT - Contains "when and why" to use the toolset
# =============================================================================

COT_SYSTEM_PROMPT = """
## Chain of Thoughts

You have access to tools for managing your reasoning process:
- `read_thoughts`: Review your current chain of thoughts
- `write_thoughts`: Add a new thought to your chain

### When to Use Chain of Thoughts

Use these tools in these scenarios:
1. Complex problems requiring multi-step reasoning
2. Planning and design tasks that may need revision
3. Analysis where understanding evolves
4. Multi-step solutions needing context tracking
5. Problems with uncertainty requiring exploration
6. Hypothesis generation and verification

### Workflow

1. Call `read_thoughts` to see your current reasoning state
2. Call `write_thoughts` to add your next thought (increment thought_number)
3. Repeat until you reach a conclusion (set next_thought_needed=false)

### Thought Management

- Start with thought_number=1 and estimate total_thoughts
- Each thought should build on, question, or revise previous insights
- Mark is_revision=true when reconsidering previous thoughts
- Use branch_from_thought and branch_id for alternative paths
- Set next_thought_needed=false when you've reached a satisfactory answer

**IMPORTANT**: Always call `read_thoughts` before `write_thoughts` to:
- Review previous reasoning
- Determine the next thought_number
- Avoid repeating yourself
- Make informed revisions
"""

# =============================================================================
# TOOL DESCRIPTIONS - Contains "how" to use each specific tool
# =============================================================================

READ_THOUGHTS_DESCRIPTION = """Read your current chain of thoughts.

Returns all recorded thoughts with their sequence numbers, revisions, and branches.
Use this to review your reasoning history before adding new thoughts.

Returns:
- Thoughts in sequence with metadata (revisions, branches)
- Summary statistics (total, revisions, branches, final)
"""

WRITE_THOUGHTS_DESCRIPTION = """Add a new thought to your chain.

Parameters:
- thought: Your current thinking step content
- thought_number: Sequential number (1-based, increment from previous)
- total_thoughts: Estimated total needed (adjust as understanding deepens)
- is_revision: True if reconsidering a previous thought
- revises_thought: Which thought number being reconsidered (if is_revision)
- branch_from_thought: Branching point if exploring alternative path
- branch_id: Identifier for the branch (groups related thoughts)
- next_thought_needed: False when you've reached a conclusion

Returns confirmation with updated statistics.

Precondition: Call read_thoughts first to see current state.
"""

# Legacy constant for backward compatibility (now points to write description)
COT_TOOL_DESCRIPTION = WRITE_THOUGHTS_DESCRIPTION


def create_cot_toolset(
    storage: CoTStorageProtocol | None = None,
    *,
    id: str | None = None,
    track_usage: bool = False,
) -> FunctionToolset[Any]:
    """Create a chain of thoughts toolset for reasoning exploration.

    This toolset provides read_thoughts and write_thoughts tools for AI agents
    to document and explore their reasoning process during a session.

    Args:
        storage: Optional storage backend. Defaults to in-memory CoTStorage.
            You can provide a custom storage implementing CoTStorageProtocol
            for persistence or integration with other systems.
        id: Optional unique ID for the toolset.
        track_usage: If True, enables usage metrics collection on the default
            storage. Ignored if custom storage is provided.

    Returns:
        FunctionToolset compatible with any pydantic-ai agent.

    Example (standalone):
        ```python
        from pydantic_ai import Agent
        from pydantic_ai_toolsets import create_cot_toolset

        agent = Agent("openai:gpt-4.1", toolsets=[create_cot_toolset()])
        result = await agent.run("Solve this complex problem step by step")
        ```

    Example (with custom storage):
        ```python
        from pydantic_ai_toolsets import create_cot_toolset, CoTStorage

        storage = CoTStorage()
        toolset = create_cot_toolset(storage=storage)

        # After agent runs, access thoughts directly
        print(storage.thoughts)
        ```

    Example (with usage tracking):
        ```python
        from pydantic_ai_toolsets import create_cot_toolset, CoTStorage

        storage = CoTStorage(track_usage=True)
        toolset = create_cot_toolset(storage=storage)

        # After agent runs, check usage metrics
        print(storage.metrics.total_tokens())
        print(storage.metrics.invocation_count())
        ```
    """
    if storage is not None:
        _storage = storage
    else:
        _storage = CoTStorage(track_usage=track_usage)

    toolset: FunctionToolset[Any] = FunctionToolset(id=id)

    # Get metrics for tracking if available
    _metrics = getattr(_storage, "metrics", None) if hasattr(_storage, "metrics") else None

    def _get_status_summary() -> str:
        """Get one-line status summary."""
        if not _storage.thoughts:
            return "Status: ○ Empty"
        total = len(_storage.thoughts)
        branches = len(set(t.branch_id for t in _storage.thoughts if t.branch_id))
        final = sum(1 for t in _storage.thoughts if not t.next_thought_needed)
        if final > 0:
            return f"Status: ✓ Complete | {total} thoughts, {branches} branches"
        return f"Status: ● Active | {total} thoughts, {branches} branches"

    def _get_next_hint() -> str:
        """Get contextual hint for next action."""
        if not _storage.thoughts:
            return "Use write_thoughts with thought_number=1 to start reasoning."
        sorted_thoughts = sorted(_storage.thoughts, key=lambda t: t.thought_number)
        final = sum(1 for t in _storage.thoughts if not t.next_thought_needed)
        if final > 0:
            return "Reasoning complete. Provide your final answer."
        next_num = sorted_thoughts[-1].thought_number + 1
        return f"Continue with write_thoughts using thought_number={next_num}."

    @toolset.tool(description=READ_THOUGHTS_DESCRIPTION)
    async def read_thoughts() -> str:
        """Read the current chain of thoughts."""
        start_time = time.perf_counter()

        if not _storage.thoughts:
            result = f"{_get_status_summary()}\n\nNo thoughts recorded yet.\n\nNext: {_get_next_hint()}"
        else:
            lines: list[str] = [_get_status_summary(), "", "Chain of Thoughts:"]
            lines.append("")

            # Sort by thought_number to ensure correct order
            sorted_thoughts = sorted(_storage.thoughts, key=lambda t: t.thought_number)

            for thought in sorted_thoughts:
                # Thought header
                header_parts: list[str] = [f"#{thought.thought_number}"]
                if thought.is_revision:
                    header_parts.append("(REVISION")
                    if thought.revises_thought:
                        header_parts.append(f"of #{thought.revises_thought}")
                    header_parts.append(")")
                if thought.branch_id:
                    header_parts.append(f"[{thought.branch_id}]")
                if thought.branch_from_thought:
                    header_parts.append(f"(from #{thought.branch_from_thought})")

                lines.append(" ".join(header_parts))
                lines.append(f"  {thought.thought}")

                # Metadata
                if not thought.next_thought_needed:
                    lines.append("  [FINAL]")
                lines.append("")

            # Summary
            total = len(_storage.thoughts)
            revisions = sum(1 for t in _storage.thoughts if t.is_revision)
            branches = len(set(t.branch_id for t in _storage.thoughts if t.branch_id))
            final = sum(1 for t in _storage.thoughts if not t.next_thought_needed)

            lines.append(f"Stats: {total} thoughts")
            if revisions > 0:
                lines.append(f"  Revisions: {revisions}")
            if branches > 0:
                lines.append(f"  Branches: {branches}")
            if final > 0:
                lines.append(f"  Final: {final}")

            lines.append("")
            lines.append(f"Next: {_get_next_hint()}")

            result = "\n".join(lines)

        # Record metrics if tracking is enabled
        if _metrics is not None:
            duration_ms = (time.perf_counter() - start_time) * 1000
            _metrics.record_invocation("read_thoughts", "", result, duration_ms)

        return result

    @toolset.tool(description=WRITE_THOUGHTS_DESCRIPTION)
    async def write_thoughts(thought: Thought) -> str:
        """Add a new thought to the chain.

        Args:
            thought: Thought item with reasoning content and metadata.
        """
        start_time = time.perf_counter()

        # Serialize input for metrics
        input_text = thought.model_dump_json() if _metrics else ""

        _storage.thoughts = thought

        # Count statistics
        total = len(_storage.thoughts)
        revisions = sum(1 for t in _storage.thoughts if t.is_revision)
        branches = len(set(t.branch_id for t in _storage.thoughts if t.branch_id))
        final = sum(1 for t in _storage.thoughts if not t.next_thought_needed)

        parts = [f"Added thought #{thought.thought_number}"]
        if thought.is_revision:
            parts.append("(revision)")
        if thought.branch_id:
            parts.append(f"[{thought.branch_id}]")
        if not thought.next_thought_needed:
            parts.append("[FINAL]")
        parts.append(f"| Total: {total}")
        if revisions > 0:
            parts.append(f"rev:{revisions}")
        if branches > 0:
            parts.append(f"branches:{branches}")

        result = " ".join(parts)

        # Record metrics if tracking is enabled
        if _metrics is not None:
            duration_ms = (time.perf_counter() - start_time) * 1000
            _metrics.record_invocation("write_thoughts", input_text, result, duration_ms)

        return result

    return toolset


def get_cot_system_prompt(storage: CoTStorageProtocol | None = None) -> str:
    """Generate dynamic system prompt section for chain of thoughts.

    Args:
        storage: Optional storage to read current thoughts from.

    Returns:
        System prompt section with current thoughts, or base prompt if no thoughts.
    """
    if storage is None or not storage.thoughts:
        return COT_SYSTEM_PROMPT

    lines: list[str] = [COT_SYSTEM_PROMPT, "", "## Current State"]

    # Sort by thought_number
    sorted_thoughts = sorted(storage.thoughts, key=lambda t: t.thought_number)
    total = len(sorted_thoughts)

    lines.append(f"Thoughts recorded: {total}")

    # Show last few thoughts as preview
    preview_count = min(3, total)
    if preview_count > 0:
        lines.append("")
        lines.append("Recent thoughts:")
        for thought in sorted_thoughts[-preview_count:]:
            header = f"#{thought.thought_number}"
            if thought.is_revision:
                header += " (rev)"
            if thought.branch_id:
                header += f" [{thought.branch_id}]"

            lines.append(f"- {header}: {thought.thought}")

    # Next thought number hint
    next_num = sorted_thoughts[-1].thought_number + 1 if sorted_thoughts else 1
    lines.append("")
    lines.append(f"Next thought_number: {next_num}")

    return "\n".join(lines)


def create_cot_toolset_agent(model: str = "openrouter:x-ai/grok-4.1-fast") -> Agent:
    """Create a Pydantic-ai agent with the chain of thoughts toolset.

    Args:
        model: The model to use for the agent.

    Returns:
        Pydantic-ai agent with the chain of thoughts toolset.
    """
    storage = CoTStorage()
    toolset = create_cot_toolset(storage=storage)
    agent = Agent(
        model,
        system_prompt="""
        You are a reasoning agent. You have access to tools for managing your reasoning process:
        - `read_thoughts`: Review your current chain of thoughts
        - `write_thoughts`: Add a new thought to your chain

        **IMPORTANT**: Use these tools to document and explore your reasoning process during complex problems.
        """,
        toolsets=[toolset]
    )

    @agent.instructions
    async def add_prompt() -> str:
        """Add the chain of thoughts system prompt."""
        return get_cot_system_prompt(storage)

    return agent
