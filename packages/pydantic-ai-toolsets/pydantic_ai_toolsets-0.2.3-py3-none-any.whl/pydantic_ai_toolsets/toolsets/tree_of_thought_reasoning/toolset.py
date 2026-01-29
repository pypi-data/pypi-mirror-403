"""Tree of thoughts toolset for pydantic-ai agents."""

from __future__ import annotations

import sys
import time
import uuid
from typing import Any

from pydantic_ai import Agent
from pydantic_ai.toolsets import FunctionToolset

from .storage import ToTStorage, ToTStorageProtocol
from .types import BranchEvaluation, BranchEvaluationItem, NodeItem, ThoughtNode

# =============================================================================
# SYSTEM PROMPT - Contains "when and why" to use the toolset
# =============================================================================

TOT_SYSTEM_PROMPT = """
## Tree of Thoughts

You have access to tools for exploring multiple reasoning paths:
- `read_tree`: Review the current tree structure
- `create_node`: Create a new reasoning node (root or child)
- `evaluate_branch`: Evaluate a branch's promise (0-100 score)
- `prune_branch`: Mark a branch as dead end
- `merge_insights`: Combine insights from multiple branches

### When to Use Tree of Thoughts

Use these tools in these scenarios:
1. Complex problems with multiple valid approaches
2. Problems requiring exploration of alternatives
3. Situations needing backtracking from dead ends
4. Tasks where combining insights from different paths is valuable
5. Problems where evaluation of paths is important

### Tree Structure

- Nodes represent reasoning states
- Branches represent different paths/approaches (identified by branch_id)
- Root nodes have no parent (parent_id=None)
- Child nodes extend existing branches

### Workflow

1. Call `read_tree` to see current state
2. Create root nodes for different initial approaches (use unique branch_ids)
3. Extend promising branches by creating child nodes
4. Evaluate branches to determine which are most promising
5. Prune branches that lead to dead ends
6. Merge insights from multiple branches when appropriate
7. Mark solution nodes with is_solution=true

**IMPORTANT**: Always call `read_tree` before modifying the tree.
"""

# =============================================================================
# TOOL DESCRIPTIONS - Contains "how" to use each specific tool
# =============================================================================

READ_TREE_DESCRIPTION = """Read the current tree structure.

Returns all nodes organized by branch with their status and evaluations.

Returns:
- Tree structure with parent-child relationships
- Node status (active, pruned, merged, completed)
- Branch evaluations and recommendations
- Summary statistics
"""

CREATE_NODE_DESCRIPTION = """Create a new node in the tree.

Parameters:
- content: Reasoning content for this node
- parent_id: Parent node ID (None/omit for root nodes)
- branch_id: Branch identifier (inherited from parent if not specified)
- is_solution: True if this node represents a solution

Returns the new node ID and placement info.

Precondition: Call read_tree first.
"""

EVALUATE_BRANCH_DESCRIPTION = """Evaluate a branch's promise.

Parameters:
- branch_id: Identifier for the branch to evaluate
- score: 0-100 (higher is better)
- reasoning: Why this score was assigned
- recommendation: "continue", "prune", "merge", or "explore_deeper"

Returns confirmation with score applied to branch nodes.

Precondition: Call read_tree first.
"""

PRUNE_BRANCH_DESCRIPTION = """Mark a branch as pruned (dead end).

Parameters:
- branch_id: Identifier for the branch to prune
- reason: Explanation for pruning

Returns count of pruned nodes.

Precondition: Call read_tree first.
"""

MERGE_INSIGHTS_DESCRIPTION = """Combine insights from multiple branches.

Parameters:
- source_branch_ids: List of branch IDs to merge
- merged_content: Combined insight content
- parent_id: Optional parent node ID
- branch_id: Optional branch ID for merged node
- is_solution: True if merged node is a solution

Returns new merged node ID.

Precondition: Call read_tree first.
"""

# Legacy constant for backward compatibility
TOT_TOOL_DESCRIPTION = CREATE_NODE_DESCRIPTION


def create_tot_toolset(
    storage: ToTStorageProtocol | None = None,
    *,
    id: str | None = None,
    track_usage: bool = False,
) -> FunctionToolset[Any]:
    """Create a tree of thoughts toolset for multi-path reasoning exploration.

    This toolset provides tools for AI agents to explore multiple reasoning paths
    simultaneously, evaluate branches, prune dead ends, and merge insights.

    Args:
        storage: Optional storage backend. Defaults to in-memory ToTStorage.
        id: Optional unique ID for the toolset.
        track_usage: If True, enables usage metrics collection.

    Returns:
        FunctionToolset compatible with any pydantic-ai agent.

    Example:
        ```python
        from pydantic_ai import Agent
        from pydantic_ai_toolsets import create_tot_toolset, ToTStorage

        # Simple usage
        agent = Agent("openai:gpt-4.1", toolsets=[create_tot_toolset()])

        # With storage and metrics
        storage = ToTStorage(track_usage=True)
        agent = Agent("openai:gpt-4.1", toolsets=[create_tot_toolset(storage)])
        print(storage.metrics.total_tokens())
        ```
    """
    if storage is not None:
        _storage = storage
    else:
        _storage = ToTStorage(track_usage=track_usage)

    toolset: FunctionToolset[Any] = FunctionToolset(id=id)
    _metrics = getattr(_storage, "metrics", None) if hasattr(_storage, "metrics") else None

    def _get_status_summary() -> str:
        """Get one-line status summary."""
        if not _storage.nodes:
            return "Status: ○ Empty"
        total_nodes = len(_storage.nodes)
        branches = len(set(n.branch_id for n in _storage.nodes.values() if n.branch_id))
        solutions = sum(1 for n in _storage.nodes.values() if n.is_solution)
        if solutions > 0:
            return f"Status: ✓ Has solutions | {total_nodes} nodes, {branches} branches, {solutions} solutions"
        return f"Status: ● Active | {total_nodes} nodes, {branches} branches"

    def _get_next_hint() -> str:
        """Get contextual hint for next action."""
        if not _storage.nodes:
            return "Use create_node to create root nodes for different approaches."
        solutions = sum(1 for n in _storage.nodes.values() if n.is_solution)
        if solutions > 0:
            return "Solution found. Review or merge_insights from multiple branches."
        # Check for unevaluated branches
        branch_ids = set(n.branch_id for n in _storage.nodes.values() if n.branch_id)
        unevaluated = [bid for bid in branch_ids if bid not in _storage.evaluations]
        if unevaluated:
            return f"Use evaluate_branch on '{unevaluated[0]}' to assess its promise."
        # Check for promising branches to extend
        promising = [bid for bid, ev in _storage.evaluations.items() if ev.recommendation in ("continue", "explore_deeper")]
        if promising:
            return f"Use create_node to extend promising branch '{promising[0]}'."
        # Check for branches to prune
        prune_candidates = [bid for bid, ev in _storage.evaluations.items() if ev.recommendation == "prune"]
        if prune_candidates:
            return f"Use prune_branch on '{prune_candidates[0]}' to discard dead ends."
        return "Create nodes, evaluate branches, or mark a solution."

    @toolset.tool(description=READ_TREE_DESCRIPTION)
    async def read_tree() -> str:
        """Read the current tree of thoughts structure."""
        start_time = time.perf_counter()

        if not _storage.nodes:
            result = f"{_get_status_summary()}\n\nNo nodes in tree.\n\nNext: {_get_next_hint()}"
            if _metrics is not None:
                duration_ms = (time.perf_counter() - start_time) * 1000
                _metrics.record_invocation("read_tree", "", result, duration_ms)
            return result
        else:
            lines: list[str] = [_get_status_summary(), "", "Tree of Thoughts:"]
            lines.append("")

            # Group nodes by branch
            root_nodes: list[ThoughtNode] = []
            for node in _storage.nodes.values():
                if node.parent_id is None:
                    root_nodes.append(node)

            # Display tree structure
            def display_node(node: ThoughtNode, indent: str = "") -> None:
                status_icon = {"active": "●", "pruned": "✗", "merged": "→", "completed": "✓"}.get(
                    node.status, "○"
                )
                node_line = f"{indent}{status_icon} [{node.node_id[:8]}]"
                if node.branch_id:
                    node_line += f" [{node.branch_id}]"
                if node.is_solution:
                    node_line += " ⭐"
                if node.evaluation_score is not None:
                    node_line += f" ({node.evaluation_score:.0f})"
                lines.append(node_line)
                lines.append(f"{indent}  {node.content[:100]}{'...' if len(node.content) > 100 else ''}")

                children = [n for n in _storage.nodes.values() if n.parent_id == node.node_id]
                for child in sorted(children, key=lambda n: n.node_id):
                    display_node(child, indent + "  ")

            for root in sorted(root_nodes, key=lambda n: n.node_id):
                display_node(root)
                lines.append("")

            # Evaluations
            if _storage.evaluations:
                lines.append("Evaluations:")
                for bid, ev in sorted(_storage.evaluations.items()):
                    lines.append(f"  {bid}: {ev.score:.0f}/100 → {ev.recommendation}")
                lines.append("")

            # Summary
            stats = _storage.get_statistics() if hasattr(_storage, "get_statistics") else {}
            if stats:
                lines.append(
                    f"Stats: {stats.get('total_nodes', 0)} nodes, "
                    f"{stats.get('branches', 0)} branches, "
                    f"{stats.get('solution_nodes', 0)} solutions"
                )

            lines.append("")
            lines.append(f"Next: {_get_next_hint()}")

            result = "\n".join(lines)

        if _metrics is not None:
            duration_ms = (time.perf_counter() - start_time) * 1000
            _metrics.record_invocation("read_tree", "", result, duration_ms)

        return result

    @toolset.tool(description=CREATE_NODE_DESCRIPTION)
    async def create_node(node: NodeItem) -> str:
        """Create a new node in the tree of thoughts."""
        start_time = time.perf_counter()
        input_text = node.model_dump_json() if _metrics else ""

        # Handle string "null" being sent instead of None
        parent_id = None if node.parent_id in (None, "null", "") else node.parent_id
        branch_id = None if node.branch_id in (None, "null", "") else node.branch_id

        node_id = str(uuid.uuid4())
        depth = 0

        if parent_id:
            parent = _storage.nodes.get(parent_id)
            if parent:
                depth = parent.depth + 1
                if branch_id is None:
                    branch_id = parent.branch_id
            else:
                available = ", ".join([n.node_id[:8] for n in list(_storage.nodes.values())[:5]])
                more = f" (+{len(_storage.nodes) - 5} more)" if len(_storage.nodes) > 5 else ""
                return f"Error: Parent '{parent_id[:8]}...' not found. Available: [{available}{more}]. Call read_tree first."

        new_node = ThoughtNode(
            node_id=node_id,
            content=node.content,
            parent_id=parent_id,
            depth=depth,
            branch_id=branch_id,
            status="active",
            is_solution=node.is_solution,
        )
        _storage.nodes = new_node

        parts = [f"Created [{node_id[:8]}]"]
        if parent_id:
            parts.append(f"under [{parent_id[:8]}]")
        else:
            parts.append("(root)")
        if branch_id:
            parts.append(f"[{branch_id}]")
        if node.is_solution:
            parts.append("⭐")

        result = " ".join(parts)

        if _metrics is not None:
            duration_ms = (time.perf_counter() - start_time) * 1000
            _metrics.record_invocation("create_node", input_text, result, duration_ms)

        return result

    @toolset.tool(description=EVALUATE_BRANCH_DESCRIPTION)
    async def evaluate_branch(evaluation: BranchEvaluationItem) -> str:
        """Evaluate a branch to determine if it's promising."""
        start_time = time.perf_counter()
        input_text = evaluation.model_dump_json() if _metrics else ""

        branch_eval = BranchEvaluation(
            branch_id=evaluation.branch_id,
            score=evaluation.score,
            reasoning=evaluation.reasoning,
            recommendation=evaluation.recommendation,
        )
        _storage.evaluations = branch_eval

        nodes_updated = 0
        for node in _storage.nodes.values():
            if node.branch_id == evaluation.branch_id:
                node.evaluation_score = evaluation.score
                nodes_updated += 1

        result = (
            f"Evaluated '{evaluation.branch_id}': {evaluation.score:.0f}/100 "
            f"→ {evaluation.recommendation} ({nodes_updated} nodes)"
        )

        if _metrics is not None:
            duration_ms = (time.perf_counter() - start_time) * 1000
            _metrics.record_invocation("evaluate_branch", input_text, result, duration_ms)

        return result

    @toolset.tool(description=PRUNE_BRANCH_DESCRIPTION)
    async def prune_branch(branch_id: str, reason: str) -> str:
        """Mark a branch as pruned (dead end)."""
        start_time = time.perf_counter()
        input_text = f"{branch_id}: {reason}" if _metrics else ""

        nodes_pruned = 0
        for node in _storage.nodes.values():
            if node.branch_id == branch_id:
                node.status = "pruned"
                nodes_pruned += 1

        if nodes_pruned == 0:
            result = f"No nodes found for branch '{branch_id}'. Call read_tree."
        else:
            result = f"Pruned '{branch_id}': {nodes_pruned} nodes. Reason: {reason}"

        if _metrics is not None:
            duration_ms = (time.perf_counter() - start_time) * 1000
            _metrics.record_invocation("prune_branch", input_text, result, duration_ms)

        return result

    @toolset.tool(description=MERGE_INSIGHTS_DESCRIPTION)
    async def merge_insights(
        source_branch_ids: list[str],
        merged_content: str,
        parent_id: str | None = None,
        branch_id: str | None = None,
        is_solution: bool = False,
    ) -> str:
        """Combine insights from multiple branches into a new merged node."""
        start_time = time.perf_counter()
        input_text = f"{source_branch_ids} -> {merged_content[:50]}" if _metrics else ""

        parent_id = None if parent_id in (None, "null", "") else parent_id
        branch_id = None if branch_id in (None, "null", "") else branch_id

        # Verify source branches exist
        missing = [b for b in source_branch_ids if not any(n.branch_id == b for n in _storage.nodes.values())]
        if missing:
            return f"Error: Branches not found: {missing}. Call read_tree."

        node_id = str(uuid.uuid4())
        depth = 0
        if parent_id:
            parent = _storage.nodes.get(parent_id)
            if parent:
                depth = parent.depth + 1
            else:
                return f"Error: Parent '{parent_id}' not found."

        # Mark source branches as merged
        merged_from: list[str] = []
        for node in _storage.nodes.values():
            if node.branch_id in source_branch_ids:
                node.status = "merged"
                merged_from.append(node.node_id)

        merged_node = ThoughtNode(
            node_id=node_id,
            content=merged_content,
            parent_id=parent_id,
            depth=depth,
            branch_id=branch_id,
            status="active",
            is_solution=is_solution,
            merged_from=merged_from,
        )
        _storage.nodes = merged_node

        result = f"Merged [{node_id[:8]}] from {source_branch_ids}"
        if is_solution:
            result += " ⭐"

        if _metrics is not None:
            duration_ms = (time.perf_counter() - start_time) * 1000
            _metrics.record_invocation("merge_insights", input_text, result, duration_ms)

        return result

    return toolset


def get_tot_system_prompt(storage: ToTStorageProtocol | None = None) -> str:
    """Generate dynamic system prompt section for tree of thoughts.

    Args:
        storage: Optional storage to read current tree from.

    Returns:
        System prompt section with current tree state, or base prompt if no nodes.
    """
    if storage is None or not storage.nodes:
        return TOT_SYSTEM_PROMPT

    lines: list[str] = [TOT_SYSTEM_PROMPT, "", "## Current State"]

    total_nodes = len(storage.nodes)
    branches = len(set(n.branch_id for n in storage.nodes.values() if n.branch_id))
    solutions = sum(1 for n in storage.nodes.values() if n.is_solution)

    lines.append(f"Nodes: {total_nodes}, Branches: {branches}, Solutions: {solutions}")

    if storage.evaluations:
        lines.append("")
        lines.append("Evaluations:")
        for bid, ev in sorted(storage.evaluations.items())[:5]:
            lines.append(f"- {bid}: {ev.score:.0f}/100 → {ev.recommendation}")
        if len(storage.evaluations) > 5:
            lines.append(f"  ... and {len(storage.evaluations) - 5} more")

    return "\n".join(lines)


def create_tot_toolset_agent(model: str = "openrouter:x-ai/grok-4.1-fast") -> Agent:
    """Create a Pydantic-ai agent with the tree of thoughts toolset.

    Args:
        model: The model to use for the agent.

    Returns:
        Pydantic-ai agent with the tree of thoughts toolset.
    """
    storage = ToTStorage()
    toolset = create_tot_toolset(storage=storage)
    agent = Agent(
        model,
        system_prompt="""
        You are a reasoning agent. You have access to tools for exploring multiple reasoning paths:
        - `read_tree`: Review the current tree structure
        - `create_node`: Create a new reasoning node
        - `evaluate_branch`: Evaluate a branch's promise
        - `prune_branch`: Mark a branch as dead end
        - `merge_insights`: Combine insights from multiple branches

        **IMPORTANT**: Use these tools to explore multiple reasoning paths simultaneously.
        """,
        toolsets=[toolset]
    )

    @agent.instructions
    async def add_prompt() -> str:
        """Add the tree of thoughts system prompt."""
        return get_tot_system_prompt(storage)

    return agent
