"""Beam search toolset for pydantic-ai agents."""

from __future__ import annotations

import sys
import time
import uuid
from typing import Any

from pydantic_ai import Agent
from pydantic_ai.toolsets import FunctionToolset

from .storage import BeamStorage, BeamStorageProtocol
from .types import (
    BeamCandidate,
    BeamStep,
    CreateCandidateItem,
    ExpandCandidateItem,
    PruneBeamItem,
    ScoreCandidateItem,
)

# =============================================================================
# SYSTEM PROMPT - Contains "when and why" to use the toolset
# =============================================================================

BEAM_SYSTEM_PROMPT = """
## Beam Search

You have access to tools for beam search exploration:
- `read_beam`: Review current beam state and candidates
- `create_candidate`: Create initial candidates
- `expand_candidate`: Generate next steps from a candidate
- `score_candidate`: Assign quality score (0-100)
- `prune_beam`: Keep only top-k candidates at a step
- `get_best_path`: Find highest-scoring path to terminal

### When to Use Beam Search

Use these tools in these scenarios:
1. Problems requiring simultaneous multi-path exploration
2. Tasks needing systematic exploration with pruning
3. Balancing exploration vs exploitation
4. Problems with clear scoring/evaluation functions
5. When breadth-first is too expensive

### Beam Search Process

1. **Initialize**: Create initial candidates (step 0)
2. **Expand**: Generate possible next steps from beam candidates
3. **Score**: Evaluate each candidate (0-100)
4. **Prune**: Keep only top-k highest-scoring (the "beam")
5. **Repeat**: Continue until terminal states or depth limit
6. **Select**: Return best path via get_best_path

### Key Parameters

- **Beam width (k)**: Candidates to keep per step
  - k=1: greedy search (fast, may miss optimal)
  - k=3-10: typical for practical applications
- **Scoring**: 0-100, higher is better
- **Terminal**: Mark solution candidates with is_terminal=true

### Workflow

1. Call `read_beam` to see current state
2. Create initial candidates if none exist
3. Expand candidates to generate continuations
4. Score all new candidates
5. Prune beam to keep top-k
6. Repeat until terminal candidates found
7. Use get_best_path for final result

**IMPORTANT**: Always call `read_beam` before modifying.
"""

# =============================================================================
# TOOL DESCRIPTIONS - Contains "how" to use each specific tool
# =============================================================================

READ_BEAM_DESCRIPTION = """Read the current beam search state.

Returns candidates organized by depth with scores and terminal status.

Returns:
- Beam steps with candidate lists
- Candidates by depth with scores
- Summary statistics
"""

CREATE_CANDIDATE_DESCRIPTION = """Create a new initial candidate.

Parameters:
- content: Reasoning content for this candidate
- is_terminal: True if this is a solution

Returns candidate ID and placement info.

Precondition: Call read_beam first.
"""

EXPAND_CANDIDATE_DESCRIPTION = """Expand a candidate into next steps.

Parameters:
- candidate_id: ID of candidate to expand
- expansions: List of continuation contents
- is_terminal: Optional list marking which are solutions

Creates new candidates at depth+1 in next step.

Precondition: Call read_beam first.
"""

SCORE_CANDIDATE_DESCRIPTION = """Score a candidate's quality.

Parameters:
- candidate_id: ID to score
- score: 0-100 (higher is better)
- reasoning: Explanation for the score

Score determines pruning priority.

Precondition: Call read_beam first.
"""

PRUNE_BEAM_DESCRIPTION = """Prune beam to keep top-k candidates.

Parameters:
- step_index: Which step to prune
- beam_width: k - how many top candidates to keep

Candidates sorted by score, top-k kept.

Precondition: Score candidates first.
"""

GET_BEST_PATH_DESCRIPTION = """Find best path to terminal candidate.

Returns highest-scoring path from initial to terminal candidates.

Returns:
- Best path with average score
- Full reasoning chain
"""

# Legacy constant
BEAM_TOOL_DESCRIPTION = CREATE_CANDIDATE_DESCRIPTION


def create_beam_toolset(
    storage: BeamStorageProtocol | None = None,
    *,
    id: str | None = None,
    track_usage: bool = False,
) -> FunctionToolset[Any]:
    """Create a beam search toolset for beam-based reasoning exploration.

    This toolset provides tools for AI agents to explore reasoning using beam search,
    maintaining a beam of top-k candidates at each step.

    Args:
        storage: Optional storage backend. Defaults to in-memory BeamStorage.
        id: Optional unique ID for the toolset.
        track_usage: If True, enables usage metrics collection.

    Returns:
        FunctionToolset compatible with any pydantic-ai agent.

    Example:
        ```python
        from pydantic_ai import Agent
        from pydantic_ai_toolsets import create_beam_toolset, BeamStorage

        # With storage and metrics
        storage = BeamStorage(track_usage=True)
        agent = Agent("openai:gpt-4.1", toolsets=[create_beam_toolset(storage)])
        print(storage.metrics.total_tokens())
        ```
    """
    if storage is not None:
        _storage = storage
    else:
        _storage = BeamStorage(track_usage=track_usage)

    toolset: FunctionToolset[Any] = FunctionToolset(id=id)
    _metrics = getattr(_storage, "metrics", None) if hasattr(_storage, "metrics") else None

    def _get_status_summary() -> str:
        """Get one-line status summary."""
        if not _storage.candidates:
            return "Status: ○ Empty"
        total = len(_storage.candidates)
        terminal = sum(1 for c in _storage.candidates.values() if c.is_terminal)
        max_step = max((s.step_index for s in _storage.steps), default=0) if _storage.steps else 0
        if terminal > 0:
            return f"Status: ✓ Has solutions | Step {max_step}, {total} candidates, {terminal} terminal"
        return f"Status: ● Active | Step {max_step}, {total} candidates"

    def _get_next_hint() -> str:
        """Get contextual hint for next action."""
        if not _storage.candidates:
            return "Use create_candidate to create initial candidates."
        terminal = [c for c in _storage.candidates.values() if c.is_terminal and c.score is not None]
        if terminal:
            return "Terminal candidates found. Use get_best_path to find the best solution."
        unscored = [c for c in _storage.candidates.values() if c.score is None]
        if unscored:
            return f"Use score_candidate on [{unscored[0].candidate_id}] to evaluate quality."
        # Find candidates that can be expanded (non-terminal, scored)
        expandable = [c for c in _storage.candidates.values() if not c.is_terminal and c.score is not None]
        if expandable:
            best = max(expandable, key=lambda c: c.score or 0)
            return f"Use expand_candidate on [{best.candidate_id}] to generate next steps, then prune_beam."
        return "Create more candidates or mark solutions as terminal."

    @toolset.tool(description=READ_BEAM_DESCRIPTION)
    async def read_beam() -> str:
        """Read the current beam search state."""
        start_time = time.perf_counter()

        if not _storage.candidates:
            result = f"{_get_status_summary()}\n\nNo candidates.\n\nNext: {_get_next_hint()}"
            if _metrics is not None:
                duration_ms = (time.perf_counter() - start_time) * 1000
                _metrics.record_invocation("read_beam", "", result, duration_ms)
            return result
        else:
            lines: list[str] = [_get_status_summary(), "", "Beam Search State:"]
            lines.append("")

            # Steps
            if _storage.steps:
                lines.append("Steps:")
                for step in sorted(_storage.steps, key=lambda s: s.step_index):
                    lines.append(f"  Step {step.step_index} (k={step.beam_width}):")
                    for cid in step.candidate_ids:
                        c = _storage.candidates.get(cid)
                        if c:
                            score = f"{c.score:.0f}" if c.score is not None else "?"
                            term = " ⭐" if c.is_terminal else ""
                            lines.append(f"    [{cid}] score={score}{term}")
                lines.append("")

            # Candidates by depth
            by_depth: dict[int, list[BeamCandidate]] = {}
            for c in _storage.candidates.values():
                by_depth.setdefault(c.depth, []).append(c)

            lines.append("Candidates:")
            for depth in sorted(by_depth.keys()):
                candidates = sorted(by_depth[depth], key=lambda c: c.score or -1, reverse=True)
                lines.append(f"  Depth {depth}:")
                for c in candidates:
                    score = f"{c.score:.0f}" if c.score is not None else "?"
                    term = " ⭐" if c.is_terminal else ""
                    parent = f" ←[{c.parent_id}]" if c.parent_id else " (root)"
                    lines.append(f"    [{c.candidate_id}] {score}{term}{parent}")
                    lines.append(f"      {c.content}")
            lines.append("")

            # Summary
            stats = _storage.get_statistics() if hasattr(_storage, "get_statistics") else {}
            if stats:
                lines.append(
                    f"Stats: {stats.get('total_candidates', 0)} candidates, "
                    f"{stats.get('terminal_candidates', 0)} terminal, "
                    f"depth {stats.get('max_depth', 0)}"
                )

            lines.append("")
            lines.append(f"Next: {_get_next_hint()}")

            result = "\n".join(lines)

        if _metrics is not None:
            duration_ms = (time.perf_counter() - start_time) * 1000
            _metrics.record_invocation("read_beam", "", result, duration_ms)

        return result

    @toolset.tool(description=CREATE_CANDIDATE_DESCRIPTION)
    async def create_candidate(candidate: CreateCandidateItem) -> str:
        """Create a new candidate in the beam search."""
        start_time = time.perf_counter()
        input_text = candidate.model_dump_json() if _metrics else ""

        candidate_id = str(uuid.uuid4())
        step_index = 0

        new_candidate = BeamCandidate(
            candidate_id=candidate_id,
            content=candidate.content,
            depth=0,
            is_terminal=candidate.is_terminal,
            step_index=step_index,
        )
        _storage.candidates = new_candidate

        # Find or create step 0
        step = next((s for s in _storage.steps if s.step_index == 0), None)
        if step is None:
            step = BeamStep(step_index=0, candidate_ids=[], beam_width=1)

        step.candidate_ids.append(candidate_id)
        _storage.steps = step

        result = f"Created [{candidate_id}] at step 0"
        if candidate.is_terminal:
            result += " ⭐"

        if _metrics is not None:
            duration_ms = (time.perf_counter() - start_time) * 1000
            _metrics.record_invocation("create_candidate", input_text, result, duration_ms)

        return result

    @toolset.tool(description=EXPAND_CANDIDATE_DESCRIPTION)
    async def expand_candidate(expand: ExpandCandidateItem) -> str:
        """Expand a candidate to generate next steps."""
        start_time = time.perf_counter()
        input_text = expand.model_dump_json() if _metrics else ""

        if expand.candidate_id not in _storage.candidates:
            available = ", ".join([c.candidate_id for c in _storage.candidates.values()])
            return f"Error: Candidate '{expand.candidate_id}' not found. Available: [{available}]. Call read_beam."

        parent = _storage.candidates[expand.candidate_id]

        is_terminal_list = expand.is_terminal
        if is_terminal_list and len(is_terminal_list) != len(expand.expansions):
            return f"Error: is_terminal length ({len(is_terminal_list)}) must match expansions ({len(expand.expansions)})."

        new_ids: list[str] = []
        next_depth = parent.depth + 1
        next_step = parent.step_index + 1

        for i, content in enumerate(expand.expansions):
            cid = str(uuid.uuid4())
            is_term = is_terminal_list[i] if is_terminal_list else False

            new_c = BeamCandidate(
                candidate_id=cid,
                content=content,
                depth=next_depth,
                parent_id=expand.candidate_id,
                is_terminal=is_term,
                step_index=next_step,
            )
            _storage.candidates = new_c
            new_ids.append(cid)

        # Update step
        step = next((s for s in _storage.steps if s.step_index == next_step), None)
        if step:
            step.candidate_ids.extend(new_ids)
        else:
            step = BeamStep(step_index=next_step, candidate_ids=new_ids.copy(), beam_width=len(new_ids))
        _storage.steps = step

        result = f"Expanded [{expand.candidate_id}] → {len(expand.expansions)} candidates at step {next_step}"

        if _metrics is not None:
            duration_ms = (time.perf_counter() - start_time) * 1000
            _metrics.record_invocation("expand_candidate", input_text, result, duration_ms)

        return result

    @toolset.tool(description=SCORE_CANDIDATE_DESCRIPTION)
    async def score_candidate(score: ScoreCandidateItem) -> str:
        """Score a candidate to evaluate its quality."""
        start_time = time.perf_counter()
        input_text = score.model_dump_json() if _metrics else ""

        if score.candidate_id not in _storage.candidates:
            available = ", ".join([c.candidate_id for c in _storage.candidates.values()])
            return f"Error: Candidate '{score.candidate_id}' not found. Available: [{available}]. Call read_beam."

        candidate = _storage.candidates[score.candidate_id]
        candidate.score = score.score

        result = f"Scored [{score.candidate_id}]: {score.score:.0f}/100"

        if _metrics is not None:
            duration_ms = (time.perf_counter() - start_time) * 1000
            _metrics.record_invocation("score_candidate", input_text, result, duration_ms)

        return result

    @toolset.tool(description=PRUNE_BEAM_DESCRIPTION)
    async def prune_beam(prune: PruneBeamItem) -> str:
        """Prune the beam to keep only top-k candidates at a step."""
        start_time = time.perf_counter()
        input_text = prune.model_dump_json() if _metrics else ""

        step = next((s for s in _storage.steps if s.step_index == prune.step_index), None)
        if step is None:
            available_steps = ", ".join([str(s.step_index) for s in _storage.steps])
            return f"Error: Step {prune.step_index} not found. Available steps: [{available_steps}]. Call read_beam."

        candidates_with_scores = [
            (cid, _storage.candidates[cid].score if _storage.candidates.get(cid) and _storage.candidates[cid].score is not None else -1)
            for cid in step.candidate_ids
            if cid in _storage.candidates
        ]

        if not candidates_with_scores:
            return f"No candidates in step {prune.step_index}."

        candidates_with_scores.sort(key=lambda x: x[1], reverse=True)
        kept = [cid for cid, _ in candidates_with_scores[:prune.beam_width]]
        discarded = len(candidates_with_scores) - len(kept)

        step.candidate_ids = kept
        step.beam_width = prune.beam_width
        _storage.steps = step

        result = f"Pruned step {prune.step_index}: kept {len(kept)}, discarded {discarded}"

        if _metrics is not None:
            duration_ms = (time.perf_counter() - start_time) * 1000
            _metrics.record_invocation("prune_beam", input_text, result, duration_ms)

        return result

    @toolset.tool(description=GET_BEST_PATH_DESCRIPTION)
    async def get_best_path() -> str:
        """Find the best path found so far in the beam search."""
        start_time = time.perf_counter()

        if not _storage.candidates:
            result = "No candidates. Create candidates first."
        else:
            terminals = [c for c in _storage.candidates.values() if c.is_terminal and c.score is not None]

            if not terminals:
                result = "No scored terminal candidates. Mark is_terminal=true and score them."
            else:
                # Build parent map
                parent_map = {c.candidate_id: c.parent_id for c in _storage.candidates.values() if c.parent_id}

                def reconstruct(cid: str) -> list[str]:
                    path = []
                    current: str | None = cid
                    while current:
                        path.append(current)
                        current = parent_map.get(current)
                    path.reverse()
                    return path

                best_path: list[str] | None = None
                best_score = -1.0

                for term in terminals:
                    path = reconstruct(term.candidate_id)
                    scores = [_storage.candidates[cid].score for cid in path if _storage.candidates.get(cid) and _storage.candidates[cid].score is not None]
                    if scores:
                        avg = sum(scores) / len(scores)
                        if avg > best_score:
                            best_score = avg
                            best_path = path

                if best_path is None:
                    result = "No scored path found."
                else:
                    lines = [f"Best Path (avg score: {best_score:.0f}/100):", ""]
                    for i, cid in enumerate(best_path):
                        c = _storage.candidates.get(cid)
                        if c:
                            score = f"{c.score:.0f}" if c.score is not None else "?"
                            term = " ⭐" if c.is_terminal else ""
                            lines.append(f"{i+1}. [{cid}] {score}{term}")
                            lines.append(f"   {c.content}")
                    result = "\n".join(lines)

        if _metrics is not None:
            duration_ms = (time.perf_counter() - start_time) * 1000
            _metrics.record_invocation("get_best_path", "", result, duration_ms)

        return result

    return toolset


def get_beam_system_prompt(storage: BeamStorageProtocol | None = None) -> str:
    """Generate dynamic system prompt section for beam search.

    Args:
        storage: Optional storage to read current beam from.

    Returns:
        System prompt section with current beam state, or base prompt if no candidates.
    """
    if storage is None:
        return BEAM_SYSTEM_PROMPT
    if not hasattr(storage, "candidates"):
        return BEAM_SYSTEM_PROMPT
    if not storage.candidates:
        return BEAM_SYSTEM_PROMPT

    lines: list[str] = [BEAM_SYSTEM_PROMPT, "", "## Current State"]

    total = len(storage.candidates)
    scored = sum(1 for c in storage.candidates.values() if c.score is not None)
    terminal = sum(1 for c in storage.candidates.values() if c.is_terminal)
    max_depth = max((c.depth for c in storage.candidates.values()), default=0)

    lines.append(f"Candidates: {total}, Scored: {scored}, Terminal: {terminal}, Depth: {max_depth}")

    # Top candidates
    scored_list = [c for c in storage.candidates.values() if c.score is not None]
    scored_list.sort(key=lambda c: c.score or 0, reverse=True)

    if scored_list:
        lines.append("")
        lines.append("Top candidates:")
        for c in scored_list:
            term = " ⭐" if c.is_terminal else ""
            lines.append(f"- [{c.candidate_id}] {c.score:.0f}/100{term}")

    return "\n".join(lines)


def create_beam_toolset_agent(model: str = "openrouter:x-ai/grok-4.1-fast") -> Agent:
    """Create a Pydantic-ai agent with the beam search toolset.

    Args:
        model: The model to use for the agent.

    Returns:
        Pydantic-ai agent with the beam search toolset.
    """
    storage = BeamStorage()
    toolset = create_beam_toolset(storage=storage)
    agent = Agent(
        model,
        system_prompt="""
        You are a beam search agent. You have access to tools for beam search exploration:
        - `read_beam`: Review current beam state and candidates
        - `create_candidate`: Create initial candidates
        - `expand_candidate`: Generate next steps from a candidate
        - `score_candidate`: Assign quality score
        - `prune_beam`: Keep only top-k candidates
        - `get_best_path`: Find highest-scoring path

        **IMPORTANT**: Use these tools to explore reasoning using beam search with pruning.
        """,
        toolsets=[toolset]
    )

    @agent.instructions
    async def add_prompt() -> str:
        """Add the beam search system prompt."""
        return get_beam_system_prompt(storage)

    return agent
