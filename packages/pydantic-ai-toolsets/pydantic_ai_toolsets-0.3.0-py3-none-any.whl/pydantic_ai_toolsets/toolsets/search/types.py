"""Type definitions for search toolset."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class OutputFormat(str, Enum):
    """Output format for extracted web content."""

    TEXT = "txt"  # Plain text format
    MARKDOWN = "markdown"  # Markdown format


class SearchSource(str, Enum):
    """Source type for search results."""

    WEB = "web"  # Standard web results
    NEWS = "news"  # News-focused results
    IMAGES = "images"  # Image search results


class TimeFilter(str, Enum):
    """Time filter for news search."""

    PAST_HOUR = "qdr:h"  # Past hour
    PAST_DAY = "qdr:d"  # Past 24 hours
    PAST_WEEK = "qdr:w"  # Past week
    PAST_MONTH = "qdr:m"  # Past month
    PAST_YEAR = "qdr:y"  # Past year
    CUSTOM = "custom"  # Custom date range


class SearchResult(BaseModel):
    """A single search result from a web search.

    Attributes:
        result_id: Unique identifier for this search result.
        query: The search query that produced this result.
        title: Title of the search result.
        url: URL of the search result.
        description: Description or snippet of the search result.
        timestamp: Timestamp when the search was performed.
        source_type: Type of search source (web, news, or images).
        date: Date string for news results (e.g., "3 months ago").
        image_url: Direct image URL for image results.
        image_width: Image width in pixels for image results.
        image_height: Image height in pixels for image results.
    """

    result_id: str
    query: str
    title: str
    url: str
    description: str | None = Field(default=None, description="Description or snippet of the result")
    timestamp: str | None = Field(default=None, description="Timestamp when search was performed")
    source_type: SearchSource = Field(default=SearchSource.WEB, description="Type of search source")
    date: str | None = Field(default=None, description="Date string for news results")
    image_url: str | None = Field(default=None, description="Direct image URL for image results")
    image_width: int | None = Field(default=None, description="Image width in pixels for image results")
    image_height: int | None = Field(default=None, description="Image height in pixels for image results")


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
    Note: Content extraction only works with web and news search results, not image results.
    """

    url: str = Field(
        ...,
        description=(
            "The URL of the webpage to extract content from. "
            "Must be a valid HTTP or HTTPS URL from web or news search results. "
            "Image search results are not supported for content extraction."
        ),
    )
    output_format: OutputFormat = Field(
        default=OutputFormat.TEXT,
        description=(
            "Output format for the extracted content. "
            "Use 'txt' for plain text or 'markdown' for markdown format."
        ),
    )


class SearchNewsItem(BaseModel):
    """Input model for the search_news tool.

    This is the model that agents use when calling search_news.
    """

    query: str = Field(
        ...,
        description=(
            "The search query string for news articles. Be specific and include relevant keywords "
            "to get the best search results."
        ),
    )
    limit: int = Field(
        default=5,
        ge=1,
        le=50,
        description=(
            "Maximum number of search results to return. "
            "Default is 5, maximum is 50."
        ),
    )
    time_filter: TimeFilter | None = Field(
        default=None,
        description=(
            "Optional time filter for news results. "
            "Options: PAST_HOUR, PAST_DAY, PAST_WEEK, PAST_MONTH, PAST_YEAR, or CUSTOM. "
            "If CUSTOM is selected, provide custom_date_min and custom_date_max."
        ),
    )
    custom_date_min: str | None = Field(
        default=None,
        description=(
            "Minimum date for custom date range filter (format: MM/DD/YYYY). "
            "Required if time_filter is CUSTOM."
        ),
    )
    custom_date_max: str | None = Field(
        default=None,
        description=(
            "Maximum date for custom date range filter (format: MM/DD/YYYY). "
            "Required if time_filter is CUSTOM."
        ),
    )


class SearchImagesItem(BaseModel):
    """Input model for the search_images tool.

    This is the model that agents use when calling search_images.
    """

    query: str = Field(
        ...,
        description=(
            "The search query string for images. Be specific and include relevant keywords "
            "to get the best search results. Can include resolution operators manually, "
            "or use exact_width/exact_height or min_width/min_height parameters."
        ),
    )
    limit: int = Field(
        default=5,
        ge=1,
        le=50,
        description=(
            "Maximum number of search results to return. "
            "Default is 5, maximum is 50."
        ),
    )
    min_width: int | None = Field(
        default=None,
        ge=1,
        description=(
            "Optional minimum image width in pixels. "
            "If both min_width and min_height are provided, appends 'larger:WxH' to query."
        ),
    )
    min_height: int | None = Field(
        default=None,
        ge=1,
        description=(
            "Optional minimum image height in pixels. "
            "If both min_width and min_height are provided, appends 'larger:WxH' to query."
        ),
    )
    exact_width: int | None = Field(
        default=None,
        ge=1,
        description=(
            "Optional exact image width in pixels. "
            "If both exact_width and exact_height are provided, appends 'imagesize:WxH' to query."
        ),
    )
    exact_height: int | None = Field(
        default=None,
        ge=1,
        description=(
            "Optional exact image height in pixels. "
            "If both exact_width and exact_height are provided, appends 'imagesize:WxH' to query."
        ),
    )

