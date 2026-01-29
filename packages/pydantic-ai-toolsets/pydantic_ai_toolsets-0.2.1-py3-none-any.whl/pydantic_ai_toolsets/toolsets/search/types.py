"""Type definitions for search toolset."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class OutputFormat(str, Enum):
    """Output format for extracted web content."""

    TEXT = "txt"  # Plain text format
    MARKDOWN = "markdown"  # Markdown format


class SearchResult(BaseModel):
    """A single search result from a web search.

    Attributes:
        result_id: Unique identifier for this search result.
        query: The search query that produced this result.
        title: Title of the search result.
        url: URL of the search result.
        description: Description or snippet of the search result.
        timestamp: Timestamp when the search was performed.
    """

    result_id: str
    query: str
    title: str
    url: str
    description: str | None = Field(default=None, description="Description or snippet of the result")
    timestamp: str | None = Field(default=None, description="Timestamp when search was performed")


class ExtractedContent(BaseModel):
    """Extracted content from a webpage.

    Attributes:
        content_id: Unique identifier for this extracted content.
        url: URL of the webpage that was extracted.
        content: The extracted content text.
        output_format: Format of the extracted content (txt or markdown).
        timestamp: Timestamp when the extraction was performed.
    """

    content_id: str
    url: str
    content: str
    output_format: OutputFormat = Field(default=OutputFormat.TEXT, description="Format of extracted content")
    timestamp: str | None = Field(default=None, description="Timestamp when extraction was performed")


class SearchWebItem(BaseModel):
    """Input model for the search_web tool.

    This is the model that agents use when calling search_web.
    """

    query: str = Field(
        ...,
        description=(
            "The search query string. Be specific and include relevant keywords "
            "to get the best search results."
        ),
    )
    limit: int = Field(
        default=5,
        ge=1,
        le=5,
        description=(
            "Maximum number of search results to return. "
            "Default is 5, maximum is 5."
        ),
    )


class ExtractWebContentItem(BaseModel):
    """Input model for the extract_web_content tool.

    This is the model that agents use when calling extract_web_content.
    """

    url: str = Field(
        ...,
        description=(
            "The URL of the webpage to extract content from. "
            "Must be a valid HTTP or HTTPS URL."
        ),
    )
    output_format: OutputFormat = Field(
        default=OutputFormat.TEXT,
        description=(
            "Output format for the extracted content. "
            "Use 'txt' for plain text or 'markdown' for markdown format."
        ),
    )

