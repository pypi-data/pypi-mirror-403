"""Monte Carlo Tree Search toolset for pydantic-ai agents.

Provides MCTS-based reasoning exploration capabilities for AI agents.
Compatible with any pydantic-ai agent - no specific deps required.

Example:
    ```python
    from pydantic_ai import Agent
    from pydantic_ai_toolsets import create_mcts_toolset, MCTSStorage

    # Simple usage
    agent = Agent("openai:gpt-4.1", toolsets=[create_mcts_toolset()])

    # With storage access
    storage = MCTSStorage()
    agent = Agent("openai:gpt-4.1", toolsets=[create_mcts_toolset(storage)])
    result = await agent.run("Solve this decision problem using MCTS")
    print(storage.nodes)  # Access nodes directly

    # With usage tracking
    storage = MCTSStorage(track_usage=True)
    agent = Agent("openai:gpt-4.1", toolsets=[create_mcts_toolset(storage)])
    print(storage.metrics.total_tokens())
    print(storage.iteration_count)
    ```
"""

from .storage import MCTSStorage, MCTSStorageProtocol
from .toolset import (
    BACKPROPAGATE_DESCRIPTION,
    EXPAND_NODE_DESCRIPTION,
    GET_BEST_ACTION_DESCRIPTION,
    MCTS_SYSTEM_PROMPT,
    MCTS_TOOL_DESCRIPTION,
    READ_MCTS_DESCRIPTION,
    SELECT_NODE_DESCRIPTION,
    SIMULATE_DESCRIPTION,
    calculate_ucb1,
    create_mcts_toolset,
    get_mcts_system_prompt,
)
from .types import (
    BackpropagateItem,
    ExpandNodeItem,
    MCTSNode,
    SelectNodeItem,
    SimulateItem,
)

__all__ = [
    # Main factory
    "create_mcts_toolset",
    "get_mcts_system_prompt",
    "calculate_ucb1",
    # Types
    "MCTSNode",
    "SelectNodeItem",
    "ExpandNodeItem",
    "SimulateItem",
    "BackpropagateItem",
    # Storage
    "MCTSStorage",
    "MCTSStorageProtocol",
    # Constants (for customization)
    "MCTS_TOOL_DESCRIPTION",
    "MCTS_SYSTEM_PROMPT",
    "READ_MCTS_DESCRIPTION",
    "SELECT_NODE_DESCRIPTION",
    "EXPAND_NODE_DESCRIPTION",
    "SIMULATE_DESCRIPTION",
    "BACKPROPAGATE_DESCRIPTION",
    "GET_BEST_ACTION_DESCRIPTION",
]

__version__ = "0.1.0"
