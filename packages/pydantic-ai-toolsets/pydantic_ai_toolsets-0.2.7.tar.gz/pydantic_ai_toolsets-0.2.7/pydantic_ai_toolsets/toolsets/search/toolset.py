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
    SearchImagesItem,
    SearchNewsItem,
    SearchResult,
    SearchSource,
    SearchWebItem,
    TimeFilter,
)

load_dotenv()

# =============================================================================
# SYSTEM PROMPT - Contains "when and why" to use the toolset
# =============================================================================

SEARCH_SYSTEM_PROMPT = """
## Web Search, News Search, and Image Search

You have access to tools for searching the web, news, and images, and extracting content:
- `search_web`: Search the web for information using Firecrawl
- `search_news`: Search for news articles using Firecrawl (supports time filtering)
- `search_images`: Search for images using Firecrawl (supports resolution filtering)
- `extract_web_content`: Extract main content from webpages using Trafilatura (works with web and news results only)

### When to Use Each Search Type

**Web Search (`search_web`):**
1. Finding current information on the web
2. Researching topics that require up-to-date data
3. Gathering information from multiple sources
4. Verifying facts or finding authoritative sources

**News Search (`search_news`):**
1. Finding recent news articles and developments
2. Searching for time-specific news (use time_filter parameter)
3. Getting news from specific date ranges
4. When you need news-focused results rather than general web results

**Image Search (`search_images`):**
1. Finding images related to a topic
2. Searching for high-resolution images (use resolution parameters)
3. Finding images of specific sizes
4. When visual content is needed

### Workflow

1. **Search**: Choose the appropriate search tool based on your needs
   - `search_web`: General web search
   - `search_news`: News articles (use time_filter for recent news: PAST_HOUR, PAST_DAY, PAST_WEEK, PAST_MONTH, PAST_YEAR, or CUSTOM with dates)
   - `search_images`: Images (use exact_width/exact_height for exact size, or min_width/min_height for minimum size)
   - Provide specific, keyword-rich queries for better results
   - Specify number of results needed (default: 5, max: 50)
   - Results include titles, URLs, and descriptions (images also include image dimensions)

2. **Extract**: Use `extract_web_content` to get content from specific URLs
   - **Only works with web and news search results** (not image results)
   - Choose URLs from search results that are most relevant
   - Choose output format: 'txt' for plain text or 'markdown' for markdown
   - Previously extracted content is stored and can be accessed without re-extraction

### Key Principles

- **Specific Queries**: Use specific, keyword-rich queries for better results
- **Time Filtering**: Use `search_news` with time_filter when you need recent news (e.g., "news from past week")
- **Resolution Filtering**: Use `search_images` with exact_width/exact_height for exact sizes (e.g., "1920x1080 images") or min_width/min_height for minimum sizes (e.g., "high-resolution images at least 2560x1440")
- **Relevant URLs**: Extract content from URLs that are most relevant to your task
- **Format Choice**: Use markdown format if you need structured content, txt for simple text
- **Efficiency**: Previously extracted content is stored and can be accessed without re-extraction
- **Content Extraction**: Only web and news results support content extraction; image results cannot be extracted
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
- url: Valid HTTP or HTTPS URL from web or news search results (image results not supported)
- output_format: 'txt' for plain text, 'markdown' for markdown (default: 'txt')

Returns extracted content as a string.
Content is stored to avoid re-extraction.
Note: Only works with URLs from web or news search results, not image search results.
"""

SEARCH_NEWS_DESCRIPTION = """Search for news articles using Firecrawl. Supports time-based filtering via time_filter parameter (past hour/day/week/month/year or custom date range).

Parameters:
- query: Specific, keyword-rich search query for news articles
- limit: Maximum results (default: 5, max: 50)
- time_filter: Optional time filter (PAST_HOUR, PAST_DAY, PAST_WEEK, PAST_MONTH, PAST_YEAR, or CUSTOM)
- custom_date_min: Minimum date for custom range (format: MM/DD/YYYY, required if time_filter is CUSTOM)
- custom_date_max: Maximum date for custom range (format: MM/DD/YYYY, required if time_filter is CUSTOM)

Returns list of news search results with titles, URLs, descriptions, and dates.
Results are stored for future reference.
"""

SEARCH_IMAGES_DESCRIPTION = """Search for images using Firecrawl. Supports resolution filtering via exact_width/exact_height (for exact size) or min_width/min_height (for minimum size).

Parameters:
- query: Specific, keyword-rich search query for images
- limit: Maximum results (default: 5, max: 50)
- exact_width: Optional exact image width in pixels (use with exact_height for exact size matching)
- exact_height: Optional exact image height in pixels (use with exact_width for exact size matching)
- min_width: Optional minimum image width in pixels (use with min_height for minimum size filtering)
- min_height: Optional minimum image height in pixels (use with min_width for minimum size filtering)

Returns list of image search results with titles, URLs, image URLs, and dimensions.
Results are stored for future reference.
Note: Content extraction is not supported for image results.
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
                sources=["web"],
                tbs="qdr:d",  # Search results from the past day
            )

            timestamp = datetime.now().isoformat()
            stored_results: list[str] = []

            # Parse web results specifically
            if isinstance(results, dict):
                if "data" in results and isinstance(results["data"], dict):
                    results_list = results["data"].get("web", [])
                elif "data" in results:
                    results_list = results["data"] if isinstance(results["data"], list) else []
                elif "results" in results:
                    results_list = results["results"] if isinstance(results["results"], list) else []
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
                        source_type=SearchSource.WEB,
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

    @toolset.tool(description=SEARCH_NEWS_DESCRIPTION)
    async def search_news(search: SearchNewsItem) -> str:
        """Search for news articles using Firecrawl."""
        start_time = time.perf_counter()
        input_text = search.model_dump_json() if _metrics else ""

        try:
            api_key = os.getenv("FIRECRAWL_API_KEY")
            if not api_key:
                result = "Error: FIRECRAWL_API_KEY not found in environment variables"
                if _metrics is not None:
                    duration_ms = (time.perf_counter() - start_time) * 1000
                    _metrics.record_invocation("search_news", input_text, result, duration_ms)
                return result

            firecrawl = Firecrawl(api_key=api_key)
            
            # Build search parameters
            search_params: dict[str, Any] = {
                "query": search.query,
                "limit": search.limit,
                "sources": ["news"],
            }
            
            # Handle time filter
            if search.time_filter:
                if search.time_filter == TimeFilter.CUSTOM:
                    if search.custom_date_min and search.custom_date_max:
                        search_params["tbs"] = f"cdr:1,cd_min:{search.custom_date_min},cd_max:{search.custom_date_max}"
                    else:
                        result = "Error: custom_date_min and custom_date_max are required when time_filter is CUSTOM"
                        if _metrics is not None:
                            duration_ms = (time.perf_counter() - start_time) * 1000
                            _metrics.record_invocation("search_news", input_text, result, duration_ms)
                        return result
                else:
                    search_params["tbs"] = search.time_filter.value
            
            results = firecrawl.search(**search_params)

            timestamp = datetime.now().isoformat()
            stored_results: list[str] = []

            # Parse news results specifically
            if isinstance(results, dict):
                if "data" in results and isinstance(results["data"], dict):
                    results_list = results["data"].get("news", [])
                elif "data" in results:
                    results_list = results["data"] if isinstance(results["data"], list) else []
                else:
                    results_list = []
            elif isinstance(results, list):
                results_list = results
            else:
                results_list = []

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
                        source_type=SearchSource.NEWS,
                        date=result.get("date", None),
                    )
                    _storage.search_results = search_result
                    stored_results.append(result_id)

            if stored_results:
                lines = [
                    f"Found {len(stored_results)} news result(s) for query: '{search.query}'",
                    "",
                ]
                for result_id in stored_results:
                    result = _storage.search_results[result_id]
                    lines.append(f"[{result_id}] {result.title}")
                    lines.append(f"  URL: {result.url}")
                    if result.date:
                        lines.append(f"  Date: {result.date}")
                    if result.description:
                        lines.append(f"  Description: {result.description}")
                    lines.append("")
                result = "\n".join(lines)
            else:
                result = f"Search completed for query: '{search.query}'. Results: {results}"

            if _metrics is not None:
                duration_ms = (time.perf_counter() - start_time) * 1000
                _metrics.record_invocation("search_news", input_text, result, duration_ms)

            return result

        except Exception as e:
            result = f"Error searching news: {str(e)}"
            if _metrics is not None:
                duration_ms = (time.perf_counter() - start_time) * 1000
                _metrics.record_invocation("search_news", input_text, result, duration_ms)
            return result

    @toolset.tool(description=SEARCH_IMAGES_DESCRIPTION)
    async def search_images(search: SearchImagesItem) -> str:
        """Search for images using Firecrawl."""
        start_time = time.perf_counter()
        input_text = search.model_dump_json() if _metrics else ""

        try:
            api_key = os.getenv("FIRECRAWL_API_KEY")
            if not api_key:
                result = "Error: FIRECRAWL_API_KEY not found in environment variables"
                if _metrics is not None:
                    duration_ms = (time.perf_counter() - start_time) * 1000
                    _metrics.record_invocation("search_images", input_text, result, duration_ms)
                return result

            # Build query with resolution operators if provided
            query = search.query
            if search.exact_width and search.exact_height:
                query = f"{query} imagesize:{search.exact_width}x{search.exact_height}"
            elif search.min_width and search.min_height:
                query = f"{query} larger:{search.min_width}x{search.min_height}"

            firecrawl = Firecrawl(api_key=api_key)
            results = firecrawl.search(
                query=query,
                limit=search.limit,
                sources=["images"],
            )

            timestamp = datetime.now().isoformat()
            stored_results: list[str] = []

            # Parse image results specifically
            if isinstance(results, dict):
                if "data" in results and isinstance(results["data"], dict):
                    results_list = results["data"].get("images", [])
                elif "data" in results:
                    results_list = results["data"] if isinstance(results["data"], list) else []
                else:
                    results_list = []
            elif isinstance(results, list):
                results_list = results
            else:
                results_list = []

            for idx, result in enumerate(results_list):
                if isinstance(result, dict):
                    result_id = str(uuid.uuid4())
                    search_result = SearchResult(
                        result_id=result_id,
                        query=search.query,
                        title=result.get("title", result.get("name", "Untitled")),
                        url=result.get("url", result.get("link", "")),
                        description=result.get("description", None),
                        timestamp=timestamp,
                        source_type=SearchSource.IMAGES,
                        image_url=result.get("imageUrl", None),
                        image_width=result.get("imageWidth", None),
                        image_height=result.get("imageHeight", None),
                    )
                    _storage.search_results = search_result
                    stored_results.append(result_id)

            if stored_results:
                lines = [
                    f"Found {len(stored_results)} image result(s) for query: '{search.query}'",
                    "",
                ]
                for result_id in stored_results:
                    result = _storage.search_results[result_id]
                    lines.append(f"[{result_id}] {result.title}")
                    if result.image_url:
                        lines.append(f"  Image URL: {result.image_url}")
                    lines.append(f"  Page URL: {result.url}")
                    if result.image_width and result.image_height:
                        lines.append(f"  Dimensions: {result.image_width}x{result.image_height}")
                    if result.description:
                        lines.append(f"  Description: {result.description}")
                    lines.append("")
                result = "\n".join(lines)
            else:
                result = f"Search completed for query: '{search.query}'. Results: {results}"

            if _metrics is not None:
                duration_ms = (time.perf_counter() - start_time) * 1000
                _metrics.record_invocation("search_images", input_text, result, duration_ms)

            return result

        except Exception as e:
            result = f"Error searching images: {str(e)}"
            if _metrics is not None:
                duration_ms = (time.perf_counter() - start_time) * 1000
                _metrics.record_invocation("search_images", input_text, result, duration_ms)
            return result

    @toolset.tool(description=EXTRACT_WEB_CONTENT_DESCRIPTION)
    async def extract_web_content(extract: ExtractWebContentItem) -> str:
        """Extract main content from a webpage using Trafilatura."""
        start_time = time.perf_counter()
        input_text = extract.model_dump_json() if _metrics else ""

        try:
            # Check if URL is from an image search result
            for search_result in _storage.search_results.values():
                if search_result.url == extract.url and search_result.source_type == SearchSource.IMAGES:
                    result = "Error: Content extraction is not supported for image search results. Use web or news search results instead."
                    if _metrics is not None:
                        duration_ms = (time.perf_counter() - start_time) * 1000
                        _metrics.record_invocation("extract_web_content", input_text, result, duration_ms)
                    return result

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
