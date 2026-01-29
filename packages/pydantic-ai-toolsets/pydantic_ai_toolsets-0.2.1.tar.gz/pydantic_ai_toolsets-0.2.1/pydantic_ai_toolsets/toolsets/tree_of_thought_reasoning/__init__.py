"""Tree of thoughts toolset for pydantic-ai agents.

Provides multi-path reasoning exploration capabilities for AI agents.
Compatible with any pydantic-ai agent - no specific deps required.

Example:
    ```python
    from pydantic_ai import Agent
    from pydantic_ai_toolsets import create_tot_toolset, ToTStorage

    # Simple usage
    agent = Agent("openai:gpt-4.1", toolsets=[create_tot_toolset()])

    # With storage access
    storage = ToTStorage()
    agent = Agent("openai:gpt-4.1", toolsets=[create_tot_toolset(storage)])
    result = await agent.run("Solve this complex problem exploring multiple approaches")
    print(storage.nodes)  # Access nodes directly
    print(storage.evaluations)  # Access evaluations directly

    # With usage tracking
    storage = ToTStorage(track_usage=True)
    agent = Agent("openai:gpt-4.1", toolsets=[create_tot_toolset(storage)])
    print(storage.metrics.total_tokens())
    ```
"""

from .storage import ToTStorage, ToTStorageProtocol
from .toolset import (
    CREATE_NODE_DESCRIPTION,
    EVALUATE_BRANCH_DESCRIPTION,
    MERGE_INSIGHTS_DESCRIPTION,
    PRUNE_BRANCH_DESCRIPTION,
    READ_TREE_DESCRIPTION,
    TOT_SYSTEM_PROMPT,
    TOT_TOOL_DESCRIPTION,
    create_tot_toolset,
    get_tot_system_prompt,
)
from .types import (
    BranchEvaluation,
    BranchEvaluationItem,
    NodeItem,
    ThoughtNode,
)

__all__ = [
    # Main factory
    "create_tot_toolset",
    "get_tot_system_prompt",
    # Types
    "ThoughtNode",
    "NodeItem",
    "BranchEvaluation",
    "BranchEvaluationItem",
    # Storage
    "ToTStorage",
    "ToTStorageProtocol",
    # Constants (for customization)
    "TOT_TOOL_DESCRIPTION",
    "TOT_SYSTEM_PROMPT",
    "READ_TREE_DESCRIPTION",
    "CREATE_NODE_DESCRIPTION",
    "EVALUATE_BRANCH_DESCRIPTION",
    "PRUNE_BRANCH_DESCRIPTION",
    "MERGE_INSIGHTS_DESCRIPTION",
]

__version__ = "0.1.0"
