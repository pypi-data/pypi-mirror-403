"""Search toolset for pydantic-ai agents."""

from __future__ import annotations

import os
import sys
import time
import uuid
from datetime import datetime
from typing import Any

from dotenv import load_dotenv
from firecrawl import Firecrawl
from pydantic_ai import Agent
from pydantic_ai.toolsets import FunctionToolset
import trafilatura

from .storage import SearchStorage, SearchStorageProtocol
from .types import (
    ExtractWebContentItem,
    ExtractedContent,
    OutputFormat,
    SearchResult,
    SearchWebItem,
)

load_dotenv()

# =============================================================================
# SYSTEM PROMPT - Contains "when and why" to use the toolset
# =============================================================================

SEARCH_SYSTEM_PROMPT = """
## Web Search

You have access to tools for searching the web and extracting content:
- `search_web`: Search the web for information using Firecrawl
- `extract_web_content`: Extract main content from webpages using Trafilatura

### When to Use Web Search

Use these tools in these scenarios:
1. Finding current information on the web
2. Researching topics that require up-to-date data
3. Extracting readable content from webpages
4. Gathering information from multiple sources
5. Verifying facts or finding authoritative sources
6. Discovering recent developments or news

### Workflow

1. **Search**: Use `search_web` with a specific query to find relevant webpages
   - Provide specific, keyword-rich queries for better results
   - Specify number of results needed (default: 10, max: 50)
   - Results include titles, URLs, and descriptions
2. **Extract**: Use `extract_web_content` to get content from specific URLs
   - Choose URLs from search results that are most relevant
   - Choose output format: 'txt' for plain text or 'markdown' for markdown
   - Previously extracted content is stored and can be accessed without re-extraction

### Key Principles

- **Specific Queries**: Use specific, keyword-rich queries for better results
- **Relevant URLs**: Extract content from URLs that are most relevant to your task
- **Format Choice**: Use markdown format if you need structured content, txt for simple text
- **Efficiency**: Previously extracted content is stored and can be accessed without re-extraction
"""

# =============================================================================
# TOOL DESCRIPTIONS - Contains "how" to use each specific tool
# =============================================================================

SEARCH_WEB_DESCRIPTION = """Search the web for information using Firecrawl.

Parameters:
- query: Specific, keyword-rich search query
- limit: Maximum results (default: 10, max: 50)

Returns list of search results with titles, URLs, and descriptions.
Results are stored for future reference.
"""

EXTRACT_WEB_CONTENT_DESCRIPTION = """Extract main content from a webpage using Trafilatura.

Parameters:
- url: Valid HTTP or HTTPS URL
- output_format: 'txt' for plain text, 'markdown' for markdown (default: 'txt')

Returns extracted content as a string.
Content is stored to avoid re-extraction.
"""

# Legacy constant for backward compatibility
SEARCH_TOOL_DESCRIPTION = SEARCH_WEB_DESCRIPTION


def create_search_toolset(
    storage: SearchStorageProtocol | None = None,
    *,
    id: str | None = None,
    track_usage: bool = False,
) -> FunctionToolset[Any]:
    """Create a search toolset for web search and content extraction.

    This toolset provides tools for AI agents to search the web and extract content
    from webpages, with support for tracking search history and extracted content.

    Args:
        storage: Optional storage backend. Defaults to in-memory SearchStorage.
        id: Optional unique ID for the toolset.
        track_usage: If True, enables usage metrics collection.

    Returns:
        FunctionToolset compatible with any pydantic-ai agent.

    Example:
        ```python
        from pydantic_ai import Agent
        from pydantic_ai_toolsets import create_search_toolset, SearchStorage

        # With storage and metrics
        storage = SearchStorage(track_usage=True)
        agent = Agent("openai:gpt-4.1", toolsets=[create_search_toolset(storage)])
        print(storage.metrics.total_tokens())
        ```
    """
    if storage is not None:
        _storage = storage
    else:
        _storage = SearchStorage(track_usage=track_usage)

    toolset: FunctionToolset[Any] = FunctionToolset(id=id)
    _metrics = getattr(_storage, "metrics", None) if hasattr(_storage, "metrics") else None

    @toolset.tool(description=SEARCH_WEB_DESCRIPTION)
    async def search_web(search: SearchWebItem) -> str:
        """Search the web for information using Firecrawl."""
        start_time = time.perf_counter()
        input_text = search.model_dump_json() if _metrics else ""

        try:
            api_key = os.getenv("FIRECRAWL_API_KEY")
            if not api_key:
                result = "Error: FIRECRAWL_API_KEY not found in environment variables"
                if _metrics is not None:
                    duration_ms = (time.perf_counter() - start_time) * 1000
                    _metrics.record_invocation("search_web", input_text, result, duration_ms)
                return result

            firecrawl = Firecrawl(api_key=api_key)
            results = firecrawl.search(
                query=search.query,
                limit=search.limit,
                tbs="qdr:d",  # Search results from the past day
            )

            timestamp = datetime.now().isoformat()
            stored_results: list[str] = []

            if isinstance(results, dict):
                if "data" in results:
                    results_list = results["data"]
                elif "results" in results:
                    results_list = results["results"]
                else:
                    results_list = list(results.values()) if results else []
            elif isinstance(results, list):
                results_list = results
            else:
                results_list = [results] if results else []

            for idx, result in enumerate(results_list):
                if isinstance(result, dict):
                    result_id = str(uuid.uuid4())
                    search_result = SearchResult(
                        result_id=result_id,
                        query=search.query,
                        title=result.get("title", result.get("name", "Untitled")),
                        url=result.get("url", result.get("link", "")),
                        description=result.get("description", result.get("snippet", None)),
                        timestamp=timestamp,
                    )
                    _storage.search_results = search_result
                    stored_results.append(result_id)

            if stored_results:
                lines = [
                    f"Found {len(stored_results)} search result(s) for query: '{search.query}'",
                    "",
                ]
                for result_id in stored_results:
                    result = _storage.search_results[result_id]
                    lines.append(f"[{result_id}] {result.title}")
                    lines.append(f"  URL: {result.url}")
                    if result.description:
                        lines.append(f"  Description: {result.description}")
                    lines.append("")
                result = "\n".join(lines)
            else:
                result = f"Search completed for query: '{search.query}'. Results: {results}"

            if _metrics is not None:
                duration_ms = (time.perf_counter() - start_time) * 1000
                _metrics.record_invocation("search_web", input_text, result, duration_ms)

            return result

        except Exception as e:
            result = f"Error searching the web: {str(e)}"
            if _metrics is not None:
                duration_ms = (time.perf_counter() - start_time) * 1000
                _metrics.record_invocation("search_web", input_text, result, duration_ms)
            return result

    @toolset.tool(description=EXTRACT_WEB_CONTENT_DESCRIPTION)
    async def extract_web_content(extract: ExtractWebContentItem) -> str:
        """Extract main content from a webpage using Trafilatura."""
        start_time = time.perf_counter()
        input_text = extract.model_dump_json() if _metrics else ""

        try:
            for content in _storage.extracted_contents.values():
                if content.url == extract.url and content.output_format == extract.output_format:
                    result = (
                        f"Using previously extracted content [{content.content_id}]:\n\n"
                        f"{content.content}"
                    )
                    if _metrics is not None:
                        duration_ms = (time.perf_counter() - start_time) * 1000
                        _metrics.record_invocation("extract_web_content", input_text, result, duration_ms)
                    return result

            downloaded = trafilatura.fetch_url(extract.url)
            if downloaded is None:
                result = f"Error: Could not fetch content from URL: {extract.url}"
                if _metrics is not None:
                    duration_ms = (time.perf_counter() - start_time) * 1000
                    _metrics.record_invocation("extract_web_content", input_text, result, duration_ms)
                return result

            if extract.output_format == OutputFormat.MARKDOWN:
                extracted = trafilatura.extract(downloaded, output_format="markdown")
            else:
                extracted = trafilatura.extract(downloaded, output_format="txt")

            if extracted is None or not extracted.strip():
                metadata = trafilatura.extract_metadata(downloaded)
                if metadata:
                    result = (
                        f"Could not extract main content, but found metadata:\n"
                        f"Title: {metadata.title}\n"
                        f"Author: {metadata.author}\n"
                        f"Date: {metadata.date}"
                    )
                else:
                    result = f"Error: Could not extract content from URL: {extract.url}"
                if _metrics is not None:
                    duration_ms = (time.perf_counter() - start_time) * 1000
                    _metrics.record_invocation("extract_web_content", input_text, result, duration_ms)
                return result

            content_id = str(uuid.uuid4())
            timestamp = datetime.now().isoformat()
            extracted_content = ExtractedContent(
                content_id=content_id,
                url=extract.url,
                content=extracted,
                output_format=extract.output_format,
                timestamp=timestamp,
            )
            _storage.extracted_contents = extracted_content

            result = (
                f"Extracted content [{content_id}] from {extract.url} "
                f"(format: {extract.output_format.value}):\n\n{extracted}"
            )

            if _metrics is not None:
                duration_ms = (time.perf_counter() - start_time) * 1000
                _metrics.record_invocation("extract_web_content", input_text, result, duration_ms)

            return result

        except Exception as e:
            result = f"Error extracting content from {extract.url}: {str(e)}"
            if _metrics is not None:
                duration_ms = (time.perf_counter() - start_time) * 1000
                _metrics.record_invocation("extract_web_content", input_text, result, duration_ms)
            return result

    return toolset


def get_search_system_prompt() -> str:
    """Get the system prompt for search-based reasoning.

    Returns:
        System prompt string that can be used with pydantic-ai agents.
    """
    return SEARCH_SYSTEM_PROMPT


def create_search_toolset_agent(model: str = "openrouter:x-ai/grok-4.1-fast") -> Agent:
    """Create a Pydantic-ai agent with the search toolset.

    Args:
        model: The model to use for the agent.

    Returns:
        Pydantic-ai agent with the search toolset.
    """
    storage = SearchStorage()
    toolset = create_search_toolset(storage=storage)
    agent = Agent(
        model,
        system_prompt=SEARCH_SYSTEM_PROMPT,
        toolsets=[toolset]
    )

    @agent.instructions
    async def add_prompt() -> str:
        """Add the search system prompt."""
        return get_search_system_prompt()

    return agent
