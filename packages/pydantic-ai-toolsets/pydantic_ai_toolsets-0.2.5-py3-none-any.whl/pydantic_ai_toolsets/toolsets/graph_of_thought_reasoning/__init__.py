"""Graph of thoughts toolset for pydantic-ai agents.

Provides graph-based reasoning exploration capabilities for AI agents.
Compatible with any pydantic-ai agent - no specific deps required.

Example:
    ```python
    from pydantic_ai import Agent
    from pydantic_ai_toolsets import create_got_toolset, GoTStorage

    # Simple usage
    agent = Agent("openai:gpt-4.1", toolsets=[create_got_toolset()])

    # With storage access
    storage = GoTStorage()
    agent = Agent("openai:gpt-4.1", toolsets=[create_got_toolset(storage)])
    result = await agent.run("Solve this complex interconnected problem")
    print(storage.nodes)  # Access nodes directly
    print(storage.edges)  # Access edges directly
    print(storage.evaluations)  # Access evaluations directly

    # With usage tracking
    storage = GoTStorage(track_usage=True)
    agent = Agent("openai:gpt-4.1", toolsets=[create_got_toolset(storage)])
    print(storage.metrics.total_tokens())
    ```
"""

from .storage import GoTStorage, GoTStorageProtocol
from .toolset import (
    AGGREGATE_NODES_DESCRIPTION,
    CREATE_EDGE_DESCRIPTION,
    CREATE_NODE_DESCRIPTION,
    EVALUATE_NODE_DESCRIPTION,
    FIND_PATH_DESCRIPTION,
    GOT_SYSTEM_PROMPT,
    GOT_TOOL_DESCRIPTION,
    PRUNE_NODE_DESCRIPTION,
    READ_GRAPH_DESCRIPTION,
    REFINE_NODE_DESCRIPTION,
    create_got_toolset,
    get_got_system_prompt,
)
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

__all__ = [
    # Main factory
    "create_got_toolset",
    "get_got_system_prompt",
    # Types
    "GraphNode",
    "GraphEdge",
    "NodeEvaluation",
    "NodeItem",
    "EdgeItem",
    "AggregateItem",
    "RefineItem",
    "NodeEvaluationItem",
    # Storage
    "GoTStorage",
    "GoTStorageProtocol",
    # Constants (for customization)
    "GOT_TOOL_DESCRIPTION",
    "GOT_SYSTEM_PROMPT",
    "READ_GRAPH_DESCRIPTION",
    "CREATE_NODE_DESCRIPTION",
    "CREATE_EDGE_DESCRIPTION",
    "AGGREGATE_NODES_DESCRIPTION",
    "REFINE_NODE_DESCRIPTION",
    "EVALUATE_NODE_DESCRIPTION",
    "PRUNE_NODE_DESCRIPTION",
    "FIND_PATH_DESCRIPTION",
]

__version__ = "0.1.0"
