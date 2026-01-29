"""Graph of thoughts toolset for pydantic-ai agents."""

from __future__ import annotations

import sys
import time
import uuid
from typing import Any

from pydantic_ai import Agent
from pydantic_ai.toolsets import FunctionToolset

from .storage import GoTStorage, GoTStorageProtocol
from .types import (
    AggregateItem,
    EdgeItem,
    GraphEdge,
    GraphNode,
    NodeEvaluation,
    NodeEvaluationItem,
    NodeItem,
    RefineItem,
)

# =============================================================================
# SYSTEM PROMPT - Contains "when and why" to use the toolset
# =============================================================================

GOT_SYSTEM_PROMPT = """
## Graph of Thoughts

You have access to tools for graph-based reasoning:
- `read_graph`: Review current graph state
- `create_node`: Create a reasoning node
- `create_edge`: Connect nodes with edges
- `aggregate_nodes`: Combine multiple nodes
- `refine_node`: Improve a node's content
- `evaluate_node`: Score a node (0-100)
- `prune_node`: Mark node as not useful
- `find_path`: Find paths between nodes

### When to Use Graph of Thoughts

Use these tools in these scenarios:
1. Complex problems with interconnected sub-problems
2. Tasks requiring synthesis from multiple perspectives
3. Iterative refinement of solutions
4. Problems with non-linear dependencies
5. Building on partial solutions

### Graph Structure

- Nodes represent reasoning states/insights
- Edges connect nodes (dependency, aggregation, refinement, reference, merge)
- Not limited to trees - can have cross-links and cycles
- Aggregation combines multiple nodes into one
- Refinement creates improved versions

### Workflow

1. Call `read_graph` to see current state
2. Create initial nodes for different aspects/perspectives
3. Connect related nodes with edges
4. Evaluate nodes to identify promising ones
5. Aggregate complementary insights
6. Refine nodes that need improvement
7. Prune nodes that are dead ends
8. Mark final solution nodes with is_solution=true

### Edge Types

- `dependency`: source depends on target
- `aggregation`: target combines source nodes
- `refinement`: target improves source
- `reference`: source references target
- `merge`: nodes are merged

**IMPORTANT**: Always call `read_graph` before modifying.
"""

# =============================================================================
# TOOL DESCRIPTIONS - Concise "how" for each tool
# =============================================================================

READ_GRAPH_DESCRIPTION = """Read the current graph structure.

Returns nodes, edges, and evaluations.
"""

CREATE_NODE_DESCRIPTION = """Create a new reasoning node.

Parameters:
- content: Reasoning content
- is_solution: True if solution node

Returns node ID.

Precondition: Call read_graph first.
"""

CREATE_EDGE_DESCRIPTION = """Connect two nodes with an edge.

Parameters:
- source_id: Source node ID
- target_id: Target node ID
- edge_type: dependency, aggregation, refinement, reference, merge
- weight: Optional importance (0-1)

Returns edge ID.

Precondition: Call read_graph first.
"""

AGGREGATE_NODES_DESCRIPTION = """Combine multiple nodes into one.

Parameters:
- source_node_ids: List of nodes to aggregate
- aggregated_content: Combined insight
- is_solution: True if solution

Returns new aggregated node ID.

Precondition: Call read_graph first.
"""

REFINE_NODE_DESCRIPTION = """Create improved version of a node.

Parameters:
- node_id: Node to refine
- refined_content: Improved content
- is_solution: True if solution

Returns new refined node ID.

Precondition: Call read_graph first.
"""

EVALUATE_NODE_DESCRIPTION = """Score a node's quality.

Parameters:
- node_id: Node to evaluate
- score: 0-100 (higher is better)
- reasoning: Explanation
- recommendation: keep, refine, aggregate, prune

Precondition: Call read_graph first.
"""

PRUNE_NODE_DESCRIPTION = """Mark a node as pruned (not useful).

Parameters:
- node_id: Node to prune
- reason: Why pruning

Precondition: Call read_graph first.
"""

FIND_PATH_DESCRIPTION = """Find paths between two nodes.

Parameters:
- source_id: Start node
- target_id: End node

Returns path if exists.
"""

# Legacy constant
GOT_TOOL_DESCRIPTION = CREATE_NODE_DESCRIPTION


def create_got_toolset(
    storage: GoTStorageProtocol | None = None,
    *,
    id: str | None = None,
    track_usage: bool = False,
) -> FunctionToolset[Any]:
    """Create a graph of thoughts toolset for graph-based reasoning.

    This toolset provides tools for AI agents to explore reasoning using
    a directed graph structure with nodes (reasoning states) and edges
    (connections/dependencies).

    Args:
        storage: Optional storage backend. Defaults to in-memory GoTStorage.
        id: Optional unique ID for the toolset.
        track_usage: If True, enables usage metrics collection.

    Returns:
        FunctionToolset compatible with any pydantic-ai agent.

    Example:
        ```python
        from pydantic_ai import Agent
        from pydantic_ai_toolsets import create_got_toolset, GoTStorage

        # With storage and metrics
        storage = GoTStorage(track_usage=True)
        agent = Agent("openai:gpt-4.1", toolsets=[create_got_toolset(storage)])
        print(storage.metrics.total_tokens())
        ```
    """
    if storage is not None:
        _storage = storage
    else:
        _storage = GoTStorage(track_usage=track_usage)

    toolset: FunctionToolset[Any] = FunctionToolset(id=id)
    _metrics = getattr(_storage, "metrics", None) if hasattr(_storage, "metrics") else None

    def _get_status_summary() -> str:
        """Get one-line status summary."""
        if not _storage.nodes:
            return "Status: ○ Empty"
        total_nodes = len(_storage.nodes)
        total_edges = len(_storage.edges)
        solutions = sum(1 for n in _storage.nodes.values() if n.is_solution)
        if solutions > 0:
            return f"Status: ✓ Has solutions | {total_nodes} nodes, {total_edges} edges, {solutions} solutions"
        return f"Status: ● Active | {total_nodes} nodes, {total_edges} edges"

    def _get_next_hint() -> str:
        """Get contextual hint for next action."""
        if not _storage.nodes:
            return "Use create_node to create initial reasoning nodes."
        solutions = sum(1 for n in _storage.nodes.values() if n.is_solution)
        if solutions > 0:
            return "Solution nodes found. Review or refine them for final output."
        # Check for unevaluated nodes
        unevaluated = [n for n in _storage.nodes.values() if n.evaluation_score is None and n.status == "active"]
        if unevaluated:
            return f"Use evaluate_node on [{unevaluated[0].node_id[:8]}...] to assess quality."
        # Check for low-scoring nodes that could be refined
        low_score = [n for n in _storage.nodes.values() if n.evaluation_score and n.evaluation_score < 70 and n.status == "active"]
        if low_score:
            return f"Use refine_node on [{low_score[0].node_id[:8]}...] to improve it."
        # Check for nodes that could be aggregated
        active = [n for n in _storage.nodes.values() if n.status == "active"]
        if len(active) >= 2:
            return "Use aggregate_nodes to combine insights, or mark a node as solution."
        return "Create more nodes, aggregate insights, or mark a solution."

    @toolset.tool(description=READ_GRAPH_DESCRIPTION)
    async def read_graph() -> str:
        """Read the current graph of thoughts structure."""
        start_time = time.perf_counter()

        if not _storage.nodes:
            result = f"{_get_status_summary()}\n\nEmpty graph.\n\nNext: {_get_next_hint()}"
            if _metrics is not None:
                duration_ms = (time.perf_counter() - start_time) * 1000
                _metrics.record_invocation("read_graph", "", result, duration_ms)
            return result
        else:
            lines: list[str] = [_get_status_summary(), "", "Graph of Thoughts:"]
            lines.append("")

            # Nodes
            lines.append("Nodes:")
            for node in sorted(_storage.nodes.values(), key=lambda n: n.node_id):
                status_icon = {"active": "●", "completed": "✓", "pruned": "✗"}.get(node.status, "○")
                score = f"({node.evaluation_score:.0f})" if node.evaluation_score is not None else ""
                sol = " ⭐" if node.is_solution else ""
                agg = f" [agg:{len(node.aggregated_from)}]" if node.aggregated_from else ""
                ref = f" [ref:{node.refinement_count}]" if node.refinement_count else ""

                lines.append(f"  {status_icon} [{node.node_id[:8]}]{score}{sol}{agg}{ref}")
                lines.append(f"    {node.content[:80]}{'...' if len(node.content) > 80 else ''}")
            lines.append("")

            # Edges
            if _storage.edges:
                lines.append("Edges:")
                for edge in sorted(_storage.edges.values(), key=lambda e: e.edge_id):
                    weight = f" w={edge.weight:.2f}" if edge.weight is not None else ""
                    lines.append(
                        f"  [{edge.source_id[:8]}] --{edge.edge_type}{weight}--> [{edge.target_id[:8]}]"
                    )
                lines.append("")

            # Evaluations summary
            if _storage.evaluations:
                lines.append("Evaluations:")
                for ev in sorted(_storage.evaluations.values(), key=lambda e: e.score, reverse=True)[:5]:
                    lines.append(f"  [{ev.node_id[:8]}]: {ev.score:.0f}/100 → {ev.recommendation}")
                if len(_storage.evaluations) > 5:
                    lines.append(f"  ... +{len(_storage.evaluations) - 5} more")
                lines.append("")

            # Summary
            stats = _storage.get_statistics() if hasattr(_storage, "get_statistics") else {}
            if stats:
                lines.append(
                    f"Stats: {stats.get('total_nodes', 0)} nodes, "
                    f"{stats.get('total_edges', 0)} edges, "
                    f"{stats.get('solution_nodes', 0)} solutions"
                )

            lines.append("")
            lines.append(f"Next: {_get_next_hint()}")

            result = "\n".join(lines)

        if _metrics is not None:
            duration_ms = (time.perf_counter() - start_time) * 1000
            _metrics.record_invocation("read_graph", "", result, duration_ms)

        return result

    @toolset.tool(description=CREATE_NODE_DESCRIPTION)
    async def create_node(node: NodeItem) -> str:
        """Create a new node in the graph."""
        start_time = time.perf_counter()
        input_text = node.model_dump_json() if _metrics else ""

        node_id = str(uuid.uuid4())
        new_node = GraphNode(
            node_id=node_id,
            content=node.content,
            is_solution=node.is_solution,
        )
        _storage.nodes = new_node

        result = f"Created [{node_id[:8]}]"
        if node.is_solution:
            result += " ⭐"

        if _metrics is not None:
            duration_ms = (time.perf_counter() - start_time) * 1000
            _metrics.record_invocation("create_node", input_text, result, duration_ms)

        return result

    @toolset.tool(description=CREATE_EDGE_DESCRIPTION)
    async def create_edge(edge: EdgeItem) -> str:
        """Create an edge between two nodes."""
        start_time = time.perf_counter()
        input_text = edge.model_dump_json() if _metrics else ""

        if edge.source_id not in _storage.nodes:
            available = ", ".join([n.node_id[:8] for n in list(_storage.nodes.values())[:5]])
            return f"Error: Source '{edge.source_id[:8]}...' not found. Available: [{available}]. Call read_graph."
        if edge.target_id not in _storage.nodes:
            available = ", ".join([n.node_id[:8] for n in list(_storage.nodes.values())[:5]])
            return f"Error: Target '{edge.target_id[:8]}...' not found. Available: [{available}]. Call read_graph."

        edge_id = str(uuid.uuid4())
        new_edge = GraphEdge(
            edge_id=edge_id,
            source_id=edge.source_id,
            target_id=edge.target_id,
            edge_type=edge.edge_type,
            weight=edge.weight,
        )
        _storage.edges = new_edge

        result = f"Edge [{edge.source_id[:8]}] --{edge.edge_type}--> [{edge.target_id[:8]}]"

        if _metrics is not None:
            duration_ms = (time.perf_counter() - start_time) * 1000
            _metrics.record_invocation("create_edge", input_text, result, duration_ms)

        return result

    @toolset.tool(description=AGGREGATE_NODES_DESCRIPTION)
    async def aggregate_nodes(aggregate: AggregateItem) -> str:
        """Combine multiple nodes into a single aggregated node."""
        start_time = time.perf_counter()
        input_text = aggregate.model_dump_json() if _metrics else ""

        missing = [nid for nid in aggregate.source_node_ids if nid not in _storage.nodes]
        if missing:
            available = ", ".join([n.node_id[:8] for n in list(_storage.nodes.values())[:5]])
            return f"Error: Nodes not found: {[m[:8] for m in missing]}. Available: [{available}]. Call read_graph."

        node_id = str(uuid.uuid4())
        new_node = GraphNode(
            node_id=node_id,
            content=aggregate.aggregated_content,
            is_solution=aggregate.is_solution,
            aggregated_from=aggregate.source_node_ids.copy(),
        )
        _storage.nodes = new_node

        # Create aggregation edges
        for src_id in aggregate.source_node_ids:
            edge_id = str(uuid.uuid4())
            edge = GraphEdge(
                edge_id=edge_id,
                source_id=src_id,
                target_id=node_id,
                edge_type="aggregation",
            )
            _storage.edges = edge

        result = f"Aggregated [{node_id[:8]}] from {len(aggregate.source_node_ids)} nodes"
        if aggregate.is_solution:
            result += " ⭐"

        if _metrics is not None:
            duration_ms = (time.perf_counter() - start_time) * 1000
            _metrics.record_invocation("aggregate_nodes", input_text, result, duration_ms)

        return result

    @toolset.tool(description=REFINE_NODE_DESCRIPTION)
    async def refine_node(refine: RefineItem) -> str:
        """Create a refined version of an existing node."""
        start_time = time.perf_counter()
        input_text = refine.model_dump_json() if _metrics else ""

        if refine.node_id not in _storage.nodes:
            available = ", ".join([n.node_id[:8] for n in list(_storage.nodes.values())[:5]])
            return f"Error: Node '{refine.node_id[:8]}...' not found. Available: [{available}]. Call read_graph."

        original = _storage.nodes[refine.node_id]
        new_node_id = str(uuid.uuid4())

        new_node = GraphNode(
            node_id=new_node_id,
            content=refine.refined_content,
            is_solution=refine.is_solution,
            refined_from=refine.node_id,
            refinement_count=original.refinement_count + 1,
        )
        _storage.nodes = new_node

        # Create refinement edge
        edge_id = str(uuid.uuid4())
        edge = GraphEdge(
            edge_id=edge_id,
            source_id=refine.node_id,
            target_id=new_node_id,
            edge_type="refinement",
        )
        _storage.edges = edge

        result = f"Refined [{refine.node_id[:8]}] → [{new_node_id[:8]}] (v{new_node.refinement_count})"
        if refine.is_solution:
            result += " ⭐"

        if _metrics is not None:
            duration_ms = (time.perf_counter() - start_time) * 1000
            _metrics.record_invocation("refine_node", input_text, result, duration_ms)

        return result

    @toolset.tool(description=EVALUATE_NODE_DESCRIPTION)
    async def evaluate_node(evaluation: NodeEvaluationItem) -> str:
        """Evaluate a node to assess its quality."""
        start_time = time.perf_counter()
        input_text = evaluation.model_dump_json() if _metrics else ""

        if evaluation.node_id not in _storage.nodes:
            available = ", ".join([n.node_id[:8] for n in list(_storage.nodes.values())[:5]])
            return f"Error: Node '{evaluation.node_id[:8]}...' not found. Available: [{available}]. Call read_graph."

        node = _storage.nodes[evaluation.node_id]
        node.evaluation_score = evaluation.score

        node_eval = NodeEvaluation(
            node_id=evaluation.node_id,
            score=evaluation.score,
            reasoning=evaluation.reasoning,
            recommendation=evaluation.recommendation,
        )
        _storage.evaluations = node_eval

        result = f"Evaluated [{evaluation.node_id[:8]}]: {evaluation.score:.0f}/100 → {evaluation.recommendation}"

        if _metrics is not None:
            duration_ms = (time.perf_counter() - start_time) * 1000
            _metrics.record_invocation("evaluate_node", input_text, result, duration_ms)

        return result

    @toolset.tool(description=PRUNE_NODE_DESCRIPTION)
    async def prune_node(node_id: str, reason: str) -> str:
        """Mark a node as pruned (not useful)."""
        start_time = time.perf_counter()
        input_text = f"{node_id}: {reason}" if _metrics else ""

        if node_id not in _storage.nodes:
            available = ", ".join([n.node_id[:8] for n in list(_storage.nodes.values())[:5]])
            return f"Error: Node '{node_id[:8]}...' not found. Available: [{available}]. Call read_graph."

        node = _storage.nodes[node_id]
        node.status = "pruned"

        result = f"Pruned [{node_id[:8]}]: {reason}"

        if _metrics is not None:
            duration_ms = (time.perf_counter() - start_time) * 1000
            _metrics.record_invocation("prune_node", input_text, result, duration_ms)

        return result

    @toolset.tool(description=FIND_PATH_DESCRIPTION)
    async def find_path(source_id: str, target_id: str) -> str:
        """Find a path between two nodes in the graph."""
        start_time = time.perf_counter()
        input_text = f"{source_id} -> {target_id}" if _metrics else ""

        if source_id not in _storage.nodes:
            available = ", ".join([n.node_id[:8] for n in list(_storage.nodes.values())[:5]])
            return f"Error: Source '{source_id[:8]}...' not found. Available: [{available}]. Call read_graph."
        if target_id not in _storage.nodes:
            available = ", ".join([n.node_id[:8] for n in list(_storage.nodes.values())[:5]])
            return f"Error: Target '{target_id[:8]}...' not found. Available: [{available}]. Call read_graph."

        # BFS to find path
        adj: dict[str, list[str]] = {}
        for edge in _storage.edges.values():
            adj.setdefault(edge.source_id, []).append(edge.target_id)

        visited: set[str] = set()
        queue: list[list[str]] = [[source_id]]

        while queue:
            path = queue.pop(0)
            current = path[-1]

            if current == target_id:
                path_str = " → ".join(f"[{n[:8]}]" for n in path)
                result = f"Path found: {path_str}"

                if _metrics is not None:
                    duration_ms = (time.perf_counter() - start_time) * 1000
                    _metrics.record_invocation("find_path", input_text, result, duration_ms)

                return result

            if current not in visited:
                visited.add(current)
                for neighbor in adj.get(current, []):
                    if neighbor not in visited:
                        queue.append(path + [neighbor])

        result = f"No path from [{source_id[:8]}] to [{target_id[:8]}]"

        if _metrics is not None:
            duration_ms = (time.perf_counter() - start_time) * 1000
            _metrics.record_invocation("find_path", input_text, result, duration_ms)

        return result

    return toolset


def get_got_system_prompt(storage: GoTStorageProtocol | None = None) -> str:
    """Generate dynamic system prompt section for graph of thoughts.

    Args:
        storage: Optional storage to read current graph from.

    Returns:
        System prompt section with current graph state, or base prompt if empty.
    """
    if storage is None or not storage.nodes:
        return GOT_SYSTEM_PROMPT

    lines: list[str] = [GOT_SYSTEM_PROMPT, "", "## Current State"]

    total = len(storage.nodes)
    edges = len(storage.edges)
    solutions = sum(1 for n in storage.nodes.values() if n.is_solution)
    evals = len(storage.evaluations)

    lines.append(f"Nodes: {total}, Edges: {edges}, Solutions: {solutions}, Evaluations: {evals}")

    # Top evaluated nodes
    evaluated = [
        (nid, ev.score) for nid, ev in storage.evaluations.items() if ev.score is not None
    ]
    evaluated.sort(key=lambda x: x[1], reverse=True)

    if evaluated:
        lines.append("")
        lines.append("Top nodes:")
        for nid, score in evaluated[:3]:
            node = storage.nodes.get(nid)
            sol = " ⭐" if node and node.is_solution else ""
            lines.append(f"- [{nid[:8]}] {score:.0f}/100{sol}")

    return "\n".join(lines)


def create_got_toolset_agent(model: str = "openrouter:x-ai/grok-4.1-fast") -> Agent:
    """Create a Pydantic-ai agent with the graph of thoughts toolset.

    Args:
        model: The model to use for the agent.

    Returns:
        Pydantic-ai agent with the graph of thoughts toolset.
    """
    storage = GoTStorage()
    toolset = create_got_toolset(storage=storage)
    agent = Agent(
        model,
        system_prompt="""
        You are a graph reasoning agent. You have access to tools for graph-based reasoning:
        - `read_graph`: Review current graph state
        - `create_node`: Create a reasoning node
        - `create_edge`: Connect nodes with edges
        - `aggregate_nodes`: Combine multiple nodes
        - `refine_node`: Improve a node's content
        - `evaluate_node`: Score a node
        - `prune_node`: Mark node as not useful
        - `find_path`: Find paths between nodes

        **IMPORTANT**: Use these tools to explore reasoning using a directed graph structure.
        """,
        toolsets=[toolset]
    )

    @agent.instructions
    async def add_prompt() -> str:
        """Add the graph of thoughts system prompt."""
        return get_got_system_prompt(storage)

    return agent
