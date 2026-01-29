"""Search toolset for pydantic-ai agents.

Provides web search and content extraction capabilities for AI agents.
Compatible with any pydantic-ai agent - requires FIRECRAWL_API_KEY environment variable.

Example:
    ```python
    from pydantic_ai import Agent
    from pydantic_ai_toolsets import create_search_toolset, SearchStorage

    # Simple usage
    agent = Agent("openai:gpt-4.1", toolsets=[create_search_toolset()])

    # With storage access
    storage = SearchStorage()
    agent = Agent("openai:gpt-4.1", toolsets=[create_search_toolset(storage)])
    result = await agent.run("Search for information about Python async")
    print(storage.search_results)  # Access search results directly
    ```
"""

from .storage import SearchStorage, SearchStorageProtocol
from .toolset import (
    EXTRACT_WEB_CONTENT_DESCRIPTION,
    SEARCH_SYSTEM_PROMPT,
    SEARCH_TOOL_DESCRIPTION,
    SEARCH_WEB_DESCRIPTION,
    create_search_toolset,
    get_search_system_prompt,
)
from .types import (
    ExtractedContent,
    ExtractWebContentItem,
    OutputFormat,
    SearchResult,
    SearchWebItem,
)

__all__ = [
    # Main factory
    "create_search_toolset",
    "get_search_system_prompt",
    # Types
    "SearchResult",
    "ExtractedContent",
    "OutputFormat",
    "SearchWebItem",
    "ExtractWebContentItem",
    # Storage
    "SearchStorage",
    "SearchStorageProtocol",
    # Constants (for customization)
    "SEARCH_TOOL_DESCRIPTION",
    "SEARCH_SYSTEM_PROMPT",
    "SEARCH_WEB_DESCRIPTION",
    "EXTRACT_WEB_CONTENT_DESCRIPTION",
]

__version__ = "0.1.0"

