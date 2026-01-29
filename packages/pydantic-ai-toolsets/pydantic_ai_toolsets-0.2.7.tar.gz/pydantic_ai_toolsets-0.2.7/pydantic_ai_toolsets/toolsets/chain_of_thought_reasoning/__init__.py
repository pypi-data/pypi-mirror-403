"""Chain of thoughts toolset for pydantic-ai agents.

Provides reasoning exploration and documentation capabilities for AI agents.
Compatible with any pydantic-ai agent - no specific deps required.

Example:
    ```python
    from pydantic_ai import Agent
    from pydantic_ai_toolsets import create_cot_toolset, CoTStorage

    # Simple usage
    agent = Agent("openai:gpt-4.1", toolsets=[create_cot_toolset()])

    # With storage access
    storage = CoTStorage()
    agent = Agent("openai:gpt-4.1", toolsets=[create_cot_toolset(storage)])
    result = await agent.run("Solve this complex problem step by step")
    print(storage.thoughts)  # Access thoughts directly

    # With usage tracking
    storage = CoTStorage(track_usage=True)
    agent = Agent("openai:gpt-4.1", toolsets=[create_cot_toolset(storage)])
    result = await agent.run("Solve this problem")
    print(storage.metrics.total_tokens())  # Check token usage
    ```
"""

from .storage import CoTStorage, CoTStorageProtocol
from .toolset import (
    COT_SYSTEM_PROMPT,
    COT_TOOL_DESCRIPTION,
    READ_THOUGHTS_DESCRIPTION,
    WRITE_THOUGHTS_DESCRIPTION,
    create_cot_toolset,
    get_cot_system_prompt,
)
from .types import Thought, ThoughtItem

__all__ = [
    # Main factory
    "create_cot_toolset",
    "get_cot_system_prompt",
    # Types
    "Thought",
    "ThoughtItem",
    # Storage
    "CoTStorage",
    "CoTStorageProtocol",
    # Constants (for customization)
    "COT_TOOL_DESCRIPTION",
    "COT_SYSTEM_PROMPT",
    "READ_THOUGHTS_DESCRIPTION",
    "WRITE_THOUGHTS_DESCRIPTION",
]

__version__ = "0.2.7"
