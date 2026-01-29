"""Reflection toolset for pydantic-ai agents.

Provides reflection-based reasoning capabilities for AI agents.
Compatible with any pydantic-ai agent - no specific deps required.

Example:
    ```python
    from pydantic_ai import Agent
    from pydantic_ai_toolsets import create_reflection_toolset, ReflectionStorage

    # Simple usage
    agent = Agent("openai:gpt-4.1", toolsets=[create_reflection_toolset()])

    # With storage access
    storage = ReflectionStorage()
    agent = Agent("openai:gpt-4.1", toolsets=[create_reflection_toolset(storage)])
    result = await agent.run("Solve this problem using reflection")
    print(storage.outputs)  # Access outputs directly
    ```
"""

from .storage import ReflectionStorage, ReflectionStorageProtocol
from .toolset import (
    CREATE_OUTPUT_DESCRIPTION,
    CRITIQUE_OUTPUT_DESCRIPTION,
    GET_BEST_OUTPUT_DESCRIPTION,
    READ_REFLECTION_DESCRIPTION,
    REFINE_OUTPUT_DESCRIPTION,
    REFLECTION_SYSTEM_PROMPT,
    REFLECTION_TOOL_DESCRIPTION,
    create_reflection_toolset,
    get_reflection_system_prompt,
)
from .types import (
    CreateOutputItem,
    Critique,
    CritiqueOutputItem,
    RefineOutputItem,
    ReflectionOutput,
)

__all__ = [
    # Main factory
    "create_reflection_toolset",
    "get_reflection_system_prompt",
    # Types
    "ReflectionOutput",
    "Critique",
    "CreateOutputItem",
    "CritiqueOutputItem",
    "RefineOutputItem",
    # Storage
    "ReflectionStorage",
    "ReflectionStorageProtocol",
    # Constants (for customization)
    "REFLECTION_TOOL_DESCRIPTION",
    "REFLECTION_SYSTEM_PROMPT",
    "READ_REFLECTION_DESCRIPTION",
    "CREATE_OUTPUT_DESCRIPTION",
    "CRITIQUE_OUTPUT_DESCRIPTION",
    "REFINE_OUTPUT_DESCRIPTION",
    "GET_BEST_OUTPUT_DESCRIPTION",
]

__version__ = "0.1.0"
