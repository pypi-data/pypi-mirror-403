"""Monte Carlo Tree Search toolset for pydantic-ai agents."""

from __future__ import annotations

import math
import sys
import time
import uuid
from typing import Any

from pydantic_ai import Agent
from pydantic_ai.toolsets import FunctionToolset

from .storage import MCTSStorage, MCTSStorageProtocol
from .types import (
    BackpropagateItem,
    ExpandNodeItem,
    MCTSNode,
    SelectNodeItem,
    SimulateItem,
)

# =============================================================================
# SYSTEM PROMPT - Contains "when and why" to use the toolset
# =============================================================================

MCTS_SYSTEM_PROMPT = """
## Monte Carlo Tree Search (MCTS)

You have access to tools for MCTS-based reasoning:
- `read_mcts`: Review current tree state
- `select_node`: Select promising node using UCB1
- `expand_node`: Expand node with possible children
- `simulate`: Run simulation from a node
- `backpropagate`: Update statistics from simulation
- `get_best_action`: Get best action based on visits

### When to Use MCTS

Use these tools in these scenarios:
1. Decision-making with many possible actions
2. Game-like problems with win/loss outcomes
3. Problems requiring exploration vs exploitation balance
4. Sequential decision problems
5. Simulations can provide reward signals

### MCTS Four Phases (Per Iteration)

1. **Selection**: Pick promising node (UCB1)
2. **Expansion**: Add children to selected node
3. **Simulation**: Evaluate with reward (0-1)
4. **Backpropagation**: Update path statistics

### UCB1 Formula

UCB1 = win_rate + c × √(ln(parent_visits) / visits)

- `win_rate`: wins/visits (exploitation)
- `c`: exploration constant (default √2 ≈ 1.414)
- Higher c = more exploration

### Workflow

1. Call `read_mcts` to see current state
2. Create root if tree is empty
3. For each iteration:
   a. `select_node` - find promising leaf
   b. `expand_node` - add possible actions
   c. `simulate` - evaluate with reward (0-1)
   d. `backpropagate` - update statistics
4. After iterations, `get_best_action` for result

### Rewards

- Use 0.0-1.0 scale
- 1.0 = best outcome (win)
- 0.0 = worst outcome (loss)
- Intermediate values for partial success

**IMPORTANT**: Always call `read_mcts` before modifying.
"""

# =============================================================================
# TOOL DESCRIPTIONS - Concise "how" for each tool
# =============================================================================

READ_MCTS_DESCRIPTION = """Read the current MCTS tree state.

Returns nodes with visits, wins, UCB1 values.
"""

SELECT_NODE_DESCRIPTION = """Select a promising node using UCB1.

Parameters:
- node_id: Optional specific node (or auto-select from root)
- exploration_constant: c for UCB1 (default 1.414)

Returns selected node for expansion.

Precondition: Call read_mcts first.
"""

EXPAND_NODE_DESCRIPTION = """Expand a node with possible children.

Parameters:
- node_id: Node to expand
- children: List of child contents (possible actions)
- is_terminal: Optional list marking terminal children

Returns created child node IDs.

Precondition: Call read_mcts first.
"""

SIMULATE_DESCRIPTION = """Run simulation and record result.

Parameters:
- node_id: Starting node
- simulation_result: Reward 0.0-1.0
- simulation_path: Optional path of node IDs

Triggers backpropagation automatically.

Precondition: Call read_mcts first.
"""

BACKPROPAGATE_DESCRIPTION = """Update statistics from node to root.

Parameters:
- node_id: Leaf/terminal node
- reward: 0.0-1.0 value from simulation

Updates visits and wins for all ancestors.

Precondition: Call read_mcts first.
"""

GET_BEST_ACTION_DESCRIPTION = """Get best action based on statistics.

Returns highest-visited child of root.
Most robust selection criterion.
"""

# Legacy constant
MCTS_TOOL_DESCRIPTION = SELECT_NODE_DESCRIPTION


def calculate_ucb1(node: MCTSNode, parent_visits: int, exploration_constant: float) -> float:
    """Calculate UCB1 value for a node.

    UCB1 = win_rate + c * sqrt(ln(parent_visits) / visits)

    Args:
        node: The node to calculate UCB1 for.
        parent_visits: Total visits of the parent node.
        exploration_constant: The exploration constant (c).

    Returns:
        UCB1 value, or infinity if node hasn't been visited.
    """
    if node.visits == 0:
        return float("inf")

    exploitation = node.wins / node.visits
    exploration = exploration_constant * math.sqrt(math.log(parent_visits) / node.visits)
    return exploitation + exploration


def create_mcts_toolset(
    storage: MCTSStorageProtocol | None = None,
    *,
    id: str | None = None,
    track_usage: bool = False,
) -> FunctionToolset[Any]:
    """Create an MCTS toolset for tree-based exploration with statistics.

    This toolset provides tools for AI agents to explore reasoning using
    Monte Carlo Tree Search, balancing exploration and exploitation.

    Args:
        storage: Optional storage backend. Defaults to in-memory MCTSStorage.
        id: Optional unique ID for the toolset.
        track_usage: If True, enables usage metrics collection.

    Returns:
        FunctionToolset compatible with any pydantic-ai agent.

    Example:
        ```python
        from pydantic_ai import Agent
        from pydantic_ai_toolsets import create_mcts_toolset, MCTSStorage

        # With storage and metrics
        storage = MCTSStorage(track_usage=True)
        agent = Agent("openai:gpt-4.1", toolsets=[create_mcts_toolset(storage)])
        print(storage.metrics.total_tokens())
        ```
    """
    if storage is not None:
        _storage = storage
    else:
        _storage = MCTSStorage(track_usage=track_usage)

    toolset: FunctionToolset[Any] = FunctionToolset(id=id)
    _metrics = getattr(_storage, "metrics", None) if hasattr(_storage, "metrics") else None

    def _get_status_summary() -> str:
        """Get one-line status summary."""
        if not _storage.nodes:
            return "Status: ○ Empty"
        stats = _storage.get_statistics() if hasattr(_storage, "get_statistics") else {}
        total = stats.get("total_nodes", len(_storage.nodes))
        iterations = stats.get("iterations", 0)
        terminal = sum(1 for n in _storage.nodes.values() if n.is_terminal)
        if terminal > 0:
            return f"Status: ✓ Has solutions | {total} nodes, {iterations} iterations"
        return f"Status: ● Active | {total} nodes, {iterations} iterations"

    def _get_next_hint() -> str:
        """Get contextual hint for next action."""
        if not _storage.nodes:
            return "Use expand_node with a root node_id to create the tree."
        root = next((n for n in _storage.nodes.values() if n.parent_id is None), None)
        if not root:
            return "Use expand_node to create a root node."
        terminal = [n for n in _storage.nodes.values() if n.is_terminal and n.visits > 0]
        if terminal:
            return "Terminal nodes found. Use get_best_action for the most visited solution."
        # Check for unexpanded nodes
        unexpanded = [n for n in _storage.nodes.values() if not n.is_expanded and not n.is_terminal]
        if unexpanded:
            return f"Use select_node to find a promising leaf, then expand_node and simulate."
        # Standard MCTS iteration
        return "Run MCTS iteration: select_node → expand_node → simulate → backpropagate."

    @toolset.tool(description=READ_MCTS_DESCRIPTION)
    async def read_mcts() -> str:
        """Read the current MCTS tree state."""
        start_time = time.perf_counter()

        if not _storage.nodes:
            result = f"{_get_status_summary()}\n\nEmpty tree.\n\nNext: {_get_next_hint()}"
            if _metrics is not None:
                duration_ms = (time.perf_counter() - start_time) * 1000
                _metrics.record_invocation("read_mcts", "", result, duration_ms)
            return result
        else:
            lines: list[str] = [_get_status_summary(), "", "MCTS Tree:"]
            lines.append("")

            # Find root
            root = next((n for n in _storage.nodes.values() if n.parent_id is None), None)

            def display_node(node: MCTSNode, indent: str = "") -> None:
                term = " ⭐" if node.is_terminal else ""
                rate = f"{node.wins / node.visits:.2f}" if node.visits > 0 else "?"
                ucb = ""
                if node.parent_id and root and root.visits > 0:
                    ucb_val = calculate_ucb1(node, root.visits, math.sqrt(2))
                    ucb = f" ucb={ucb_val:.2f}" if ucb_val != float("inf") else " ucb=∞"

                lines.append(
                    f"{indent}[{node.node_id}] visits={node.visits} "
                    f"wins={node.wins:.1f} rate={rate}{ucb}{term}"
                )
                lines.append(
                    f"{indent}  {node.content}"
                )

                for cid in node.children_ids:
                    child = _storage.nodes.get(cid)
                    if child:
                        display_node(child, indent + "  ")

            if root:
                display_node(root)
            lines.append("")

            # Summary
            stats = _storage.get_statistics() if hasattr(_storage, "get_statistics") else {}
            if stats:
                lines.append(
                    f"Stats: {stats.get('total_nodes', 0)} nodes, "
                    f"{stats.get('iterations', 0)} iterations, "
                    f"depth {stats.get('max_depth', 0)}"
                )

            lines.append("")
            lines.append(f"Next: {_get_next_hint()}")

            result = "\n".join(lines)

        if _metrics is not None:
            duration_ms = (time.perf_counter() - start_time) * 1000
            _metrics.record_invocation("read_mcts", "", result, duration_ms)

        return result

    @toolset.tool(description=SELECT_NODE_DESCRIPTION)
    async def select_node(select: SelectNodeItem) -> str:
        """Select a promising node using UCB1."""
        start_time = time.perf_counter()
        input_text = select.model_dump_json() if _metrics else ""

        if select.node_id:
            if select.node_id not in _storage.nodes:
                available = ", ".join([n.node_id for n in _storage.nodes.values()])
                return f"Error: Node '{select.node_id}' not found. Available: [{available}]. Call read_mcts."
            result = f"Selected [{select.node_id}]"
        else:
            # UCB1 selection from root
            root = next((n for n in _storage.nodes.values() if n.parent_id is None), None)
            if not root:
                return "No root. Create tree with expand_node first."

            current = root
            path: list[str] = [current.node_id]

            # Descend using UCB1
            while current.children_ids and current.is_expanded:
                best_child: MCTSNode | None = None
                best_ucb = -float("inf")

                for cid in current.children_ids:
                    child = _storage.nodes.get(cid)
                    if child:
                        ucb = calculate_ucb1(child, current.visits, select.exploration_constant)
                        if ucb > best_ucb:
                            best_ucb = ucb
                            best_child = child

                if best_child is None:
                    break

                current = best_child
                path.append(current.node_id)

                # Stop at unexpanded or terminal
                if not current.is_expanded or current.is_terminal:
                    break

            path_str = " → ".join(f"[{n}]" for n in path)
            result = f"Selected [{current.node_id}] via {path_str}"

        if _metrics is not None:
            duration_ms = (time.perf_counter() - start_time) * 1000
            _metrics.record_invocation("select_node", input_text, result, duration_ms)

        return result

    @toolset.tool(description=EXPAND_NODE_DESCRIPTION)
    async def expand_node(expand: ExpandNodeItem) -> str:
        """Expand a node by adding children."""
        start_time = time.perf_counter()
        input_text = expand.model_dump_json() if _metrics else ""

        # Handle root creation
        if expand.node_id not in _storage.nodes:
            # Create root if tree is empty
            if not _storage.nodes:
                root = MCTSNode(
                    node_id=expand.node_id,
                    content="Root",
                    depth=0,
                    is_expanded=True,
                )
                _storage.nodes = root
            else:
                available = ", ".join([n.node_id for n in _storage.nodes.values()])
                return f"Error: Node '{expand.node_id}' not found. Available: [{available}]. Call read_mcts."

        parent = _storage.nodes[expand.node_id]
        is_terminal_list = expand.is_terminal

        if is_terminal_list and len(is_terminal_list) != len(expand.children):
            return f"Error: is_terminal length must match children length."

        new_ids: list[str] = []
        for i, content in enumerate(expand.children):
            child_id = str(uuid.uuid4())
            is_term = is_terminal_list[i] if is_terminal_list else False

            child = MCTSNode(
                node_id=child_id,
                content=content,
                parent_id=parent.node_id,
                depth=parent.depth + 1,
                is_terminal=is_term,
            )
            _storage.nodes = child
            parent.children_ids.append(child_id)
            new_ids.append(child_id)

        parent.is_expanded = True

        result = f"Expanded [{expand.node_id}] → {len(expand.children)} children"

        if _metrics is not None:
            duration_ms = (time.perf_counter() - start_time) * 1000
            _metrics.record_invocation("expand_node", input_text, result, duration_ms)

        return result

    @toolset.tool(description=SIMULATE_DESCRIPTION)
    async def simulate(sim: SimulateItem) -> str:
        """Run a simulation and record the result."""
        start_time = time.perf_counter()
        input_text = sim.model_dump_json() if _metrics else ""

        if sim.node_id not in _storage.nodes:
            available = ", ".join([n.node_id for n in _storage.nodes.values()])
            return f"Error: Node '{sim.node_id}' not found. Available: [{available}]. Call read_mcts."

        # Backpropagate from this node
        current: str | None = sim.node_id
        nodes_updated = 0

        while current:
            node = _storage.nodes.get(current)
            if node:
                node.visits += 1
                node.wins += sim.simulation_result
                nodes_updated += 1
                current = node.parent_id
            else:
                break

        # Increment iteration counter
        if hasattr(_storage, "increment_iteration"):
            _storage.increment_iteration()

        result = f"Simulated [{sim.node_id}] reward={sim.simulation_result:.2f}, updated {nodes_updated} nodes"

        if _metrics is not None:
            duration_ms = (time.perf_counter() - start_time) * 1000
            _metrics.record_invocation("simulate", input_text, result, duration_ms)

        return result

    @toolset.tool(description=BACKPROPAGATE_DESCRIPTION)
    async def backpropagate(backprop: BackpropagateItem) -> str:
        """Backpropagate statistics from a node to the root."""
        start_time = time.perf_counter()
        input_text = backprop.model_dump_json() if _metrics else ""

        if backprop.node_id not in _storage.nodes:
            available = ", ".join([n.node_id for n in _storage.nodes.values()])
            return f"Error: Node '{backprop.node_id}' not found. Available: [{available}]. Call read_mcts."

        current: str | None = backprop.node_id
        nodes_updated = 0

        while current:
            node = _storage.nodes.get(current)
            if node:
                node.visits += 1
                node.wins += backprop.reward
                nodes_updated += 1
                current = node.parent_id
            else:
                break

        result = f"Backpropagated from [{backprop.node_id}] reward={backprop.reward:.2f}, updated {nodes_updated} nodes"

        if _metrics is not None:
            duration_ms = (time.perf_counter() - start_time) * 1000
            _metrics.record_invocation("backpropagate", input_text, result, duration_ms)

        return result

    @toolset.tool(description=GET_BEST_ACTION_DESCRIPTION)
    async def get_best_action() -> str:
        """Get the best action based on visit counts."""
        start_time = time.perf_counter()

        root = next((n for n in _storage.nodes.values() if n.parent_id is None), None)
        if not root:
            result = "No root. Create tree first."
        elif not root.children_ids:
            result = "Root has no children. Expand root first."
        else:
            # Select by most visits (most robust)
            best_child: MCTSNode | None = None
            best_visits = -1

            for cid in root.children_ids:
                child = _storage.nodes.get(cid)
                if child and child.visits > best_visits:
                    best_visits = child.visits
                    best_child = child

            if best_child is None:
                result = "No visited children."
            else:
                rate = best_child.wins / best_child.visits if best_child.visits > 0 else 0
                lines = [
                    f"Best action: [{best_child.node_id}]",
                    f"  Visits: {best_child.visits}",
                    f"  Win rate: {rate:.2%}",
                    f"  Content: {best_child.content}",
                ]

                # Show all children for comparison
                lines.append("")
                lines.append("All root children:")
                children = [(cid, _storage.nodes.get(cid)) for cid in root.children_ids]
                children.sort(key=lambda x: x[1].visits if x[1] else 0, reverse=True)

                for cid, child in children:
                    if child:
                        c_rate = child.wins / child.visits if child.visits > 0 else 0
                        star = " ←" if child.node_id == best_child.node_id else ""
                        lines.append(
                            f"  [{cid}] v={child.visits} rate={c_rate:.2%}{star}"
                        )

                result = "\n".join(lines)

        if _metrics is not None:
            duration_ms = (time.perf_counter() - start_time) * 1000
            _metrics.record_invocation("get_best_action", "", result, duration_ms)

        return result

    return toolset


def get_mcts_system_prompt(storage: MCTSStorageProtocol | None = None) -> str:
    """Generate dynamic system prompt section for MCTS.

    Args:
        storage: Optional storage to read current tree from.

    Returns:
        System prompt section with current tree state, or base prompt if empty.
    """
    if storage is None or not storage.nodes:
        return MCTS_SYSTEM_PROMPT

    lines: list[str] = [MCTS_SYSTEM_PROMPT, "", "## Current State"]

    total = len(storage.nodes)
    root = next((n for n in storage.nodes.values() if n.parent_id is None), None)

    if root:
        lines.append(f"Root visits: {root.visits}, Total nodes: {total}")

        if root.children_ids:
            lines.append("")
            lines.append("Top actions by visits:")
            children = [
                (cid, storage.nodes.get(cid))
                for cid in root.children_ids
                if storage.nodes.get(cid)
            ]
            children.sort(key=lambda x: x[1].visits if x[1] else 0, reverse=True)

            for cid, child in children:
                if child:
                    rate = child.wins / child.visits if child.visits > 0 else 0
                    lines.append(f"- [{cid}] v={child.visits} rate={rate:.2%}")

    return "\n".join(lines)


def create_mcts_toolset_agent(model: str = "openrouter:x-ai/grok-4.1-fast") -> Agent:
    """Create a Pydantic-ai agent with the MCTS toolset.

    Args:
        model: The model to use for the agent.

    Returns:
        Pydantic-ai agent with the MCTS toolset.
    """
    storage = MCTSStorage()
    toolset = create_mcts_toolset(storage=storage)
    agent = Agent(
        model,
        system_prompt="""
        You are an MCTS agent. You have access to tools for MCTS-based reasoning:
        - `read_mcts`: Review current tree state
        - `select_node`: Select promising node using UCB1
        - `expand_node`: Expand node with possible children
        - `simulate`: Run simulation from a node
        - `backpropagate`: Update statistics from simulation
        - `get_best_action`: Get best action based on visits

        **IMPORTANT**: Use these tools to explore reasoning using Monte Carlo Tree Search.
        """,
        toolsets=[toolset]
    )

    @agent.instructions
    async def add_prompt() -> str:
        """Add the MCTS system prompt."""
        return get_mcts_system_prompt(storage)

    return agent
