"""Self-refinement toolset for pydantic-ai agents.

Provides self-refinement capabilities for AI agents through iterative feedback
and refinement cycles.
Compatible with any pydantic-ai agent - no specific deps required.

Example:
    ```python
    from pydantic_ai import Agent
    from pydantic_ai_toolsets import create_self_refine_toolset, SelfRefineStorage

    # Simple usage
    agent = Agent("openai:gpt-4.1", toolsets=[create_self_refine_toolset()])

    # With storage access
    storage = SelfRefineStorage()
    agent = Agent("openai:gpt-4.1", toolsets=[create_self_refine_toolset(storage)])
    result = await agent.run("Solve this problem using self-refinement")
    print(storage.outputs)  # Access outputs directly
    ```
"""

from .storage import SelfRefineStorage, SelfRefineStorageProtocol
from .toolset import (
    GENERATE_OUTPUT_DESCRIPTION,
    GET_BEST_OUTPUT_DESCRIPTION,
    PROVIDE_FEEDBACK_DESCRIPTION,
    READ_REFINEMENT_STATE_DESCRIPTION,
    REFINE_OUTPUT_DESCRIPTION,
    SELF_REFINE_SYSTEM_PROMPT,
    SELF_REFINE_TOOL_DESCRIPTION,
    create_self_refine_toolset,
    get_self_refine_system_prompt,
)
from .types import (
    Feedback,
    FeedbackDimension,
    FeedbackItem,
    FeedbackType,
    GenerateOutputItem,
    ProvideFeedbackItem,
    RefinementOutput,
    RefineOutputItem,
)

__all__ = [
    # Main factory
    "create_self_refine_toolset",
    "get_self_refine_system_prompt",
    # Types
    "RefinementOutput",
    "Feedback",
    "FeedbackType",
    "FeedbackDimension",
    "FeedbackItem",
    "GenerateOutputItem",
    "ProvideFeedbackItem",
    "RefineOutputItem",
    # Storage
    "SelfRefineStorage",
    "SelfRefineStorageProtocol",
    # Constants (for customization)
    "SELF_REFINE_TOOL_DESCRIPTION",
    "SELF_REFINE_SYSTEM_PROMPT",
    "READ_REFINEMENT_STATE_DESCRIPTION",
    "GENERATE_OUTPUT_DESCRIPTION",
    "PROVIDE_FEEDBACK_DESCRIPTION",
    "REFINE_OUTPUT_DESCRIPTION",
    "GET_BEST_OUTPUT_DESCRIPTION",
]

__version__ = "0.1.0"

