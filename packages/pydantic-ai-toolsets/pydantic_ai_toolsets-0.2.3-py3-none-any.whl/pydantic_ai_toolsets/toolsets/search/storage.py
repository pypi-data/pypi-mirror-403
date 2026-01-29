"""Storage abstraction for search toolset."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from .types import ExtractedContent, SearchResult

if TYPE_CHECKING:
    from .._shared.metrics import UsageMetrics


@runtime_checkable
class SearchStorageProtocol(Protocol):
    """Protocol for search storage implementations.

    Any class that has `search_results` and `extracted_contents` properties can be used
    as storage for the search toolset.

    Example:
        ```python
        class MyCustomStorage:
            def __init__(self):
                self._search_results: dict[str, SearchResult] = {}
                self._extracted_contents: dict[str, ExtractedContent] = {}

            @property
            def search_results(self) -> dict[str, SearchResult]:
                return self._search_results

            @search_results.setter
            def search_results(self, value: SearchResult) -> None:
                self._search_results[value.result_id] = value

            @property
            def extracted_contents(self) -> dict[str, ExtractedContent]:
                return self._extracted_contents

            @extracted_contents.setter
            def extracted_contents(self, value: ExtractedContent) -> None:
                self._extracted_contents[value.content_id] = value
        ```
    """

    @property
    def search_results(self) -> dict[str, SearchResult]:
        """Get the current dictionary of search results (result_id -> SearchResult)."""
        ...

    @search_results.setter
    def search_results(self, value: SearchResult) -> None:
        """Add or update a search result in the dictionary."""
        ...

    @property
    def extracted_contents(self) -> dict[str, ExtractedContent]:
        """Get the current dictionary of extracted contents (content_id -> ExtractedContent)."""
        ...

    @extracted_contents.setter
    def extracted_contents(self, value: ExtractedContent) -> None:
        """Add or update an extracted content in the dictionary."""
        ...

    def summary(self) -> dict[str, Any]:
        """Get comprehensive JSON summary of storage state and metrics.
        
        Returns:
            Dictionary containing storage state, statistics, and usage metrics.
        """
        ...

    def add_link(self, item_id: str, link_id: str) -> None:
        """Add an outgoing link for an item.
        
        Args:
            item_id: ID of the item (result_id or content_id)
            link_id: ID of the link
        """
        ...

    def add_linked_from(self, link_id: str) -> None:
        """Add an incoming link.
        
        Args:
            link_id: ID of the link
        """
        ...


@dataclass
class SearchStorage:
    """Default in-memory search storage.

    Simple implementation that stores search results and extracted contents in memory.
    Use this for standalone agents or testing.

    Example:
        ```python
        from pydantic_ai_toolsets import create_search_toolset, SearchStorage

        storage = SearchStorage()
        toolset = create_search_toolset(storage=storage)

        # After agent runs, access search results and extracted contents directly
        print(storage.search_results)
        print(storage.extracted_contents)

        # With metrics tracking
        storage = SearchStorage(track_usage=True)
        toolset = create_search_toolset(storage=storage)
        print(storage.metrics.total_tokens())
        ```
    """

    _search_results: dict[str, SearchResult] = field(default_factory=dict)
    _extracted_contents: dict[str, ExtractedContent] = field(default_factory=dict)
    _metrics: UsageMetrics | None = field(default=None)
    _links: dict[str, list[str]] = field(default_factory=dict)  # item_id -> list of link IDs
    _linked_from: list[str] = field(default_factory=list)  # list of link IDs where this storage is target

    def __init__(self, *, track_usage: bool = False) -> None:
        """Initialize storage with optional metrics tracking.

        Args:
            track_usage: If True, enables usage metrics collection.
        """
        self._search_results = {}
        self._extracted_contents = {}
        self._metrics = None
        self._links = {}
        self._linked_from = []
        if track_usage:
            import os

            toolsets_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if toolsets_dir not in sys.path:
                sys.path.insert(0, toolsets_dir)
            from .._shared.metrics import UsageMetrics

            self._metrics = UsageMetrics()

    @property
    def search_results(self) -> dict[str, SearchResult]:
        """Get the current dictionary of search results."""
        return self._search_results

    @search_results.setter
    def search_results(self, value: SearchResult) -> None:
        """Add or update a search result in the dictionary."""
        self._search_results[value.result_id] = value

    @property
    def extracted_contents(self) -> dict[str, ExtractedContent]:
        """Get the current dictionary of extracted contents."""
        return self._extracted_contents

    @extracted_contents.setter
    def extracted_contents(self, value: ExtractedContent) -> None:
        """Add or update an extracted content in the dictionary."""
        self._extracted_contents[value.content_id] = value

    @property
    def metrics(self) -> UsageMetrics | None:
        """Get usage metrics if tracking is enabled."""
        return self._metrics

    def get_statistics(self) -> dict[str, int | float]:
        """Get summary statistics about search operations.

        Returns:
            Dictionary with search and extraction counts.
        """
        unique_queries = len(set(r.query for r in self._search_results.values()))
        unique_urls = len(set(c.url for c in self._extracted_contents.values()))
        total_extracted_chars = sum(len(c.content) for c in self._extracted_contents.values())

        return {
            "total_searches": unique_queries,
            "total_results": len(self._search_results),
            "total_extractions": len(self._extracted_contents),
            "unique_urls": unique_urls,
            "total_extracted_chars": total_extracted_chars,
        }

    def summary(self) -> dict[str, Any]:
        """Get comprehensive JSON summary of storage state and metrics.

        Returns:
            Dictionary containing storage state, statistics, and usage metrics.
        """
        summary_dict: dict[str, Any] = {
            "toolset": "search",
            "statistics": self.get_statistics(),
        }

        # Add storage-specific data
        summary_dict["storage"] = {
            "search_results": {
                result_id: {
                    "result_id": result.result_id,
                    "query": result.query,
                    "title": result.title,
                    "url": result.url,
                    "description": result.description,
                    "timestamp": result.timestamp,
                }
                for result_id, result in self._search_results.items()
            },
            "extracted_contents": {
                content_id: {
                    "content_id": content.content_id,
                    "url": content.url,
                    "content": content.content,
                    "output_format": content.output_format.value if hasattr(content.output_format, "value") else str(content.output_format),
                }
                for content_id, content in self._extracted_contents.items()
            },
        }

        # Add metrics if available
        if self._metrics:
            summary_dict["usage_metrics"] = self._metrics.to_dict()

        return summary_dict

    def clear(self) -> None:
        """Clear all search results, extracted contents, and reset metrics."""
        self._search_results.clear()
        self._extracted_contents.clear()
        self._links.clear()
        self._linked_from.clear()
        if self._metrics:
            self._metrics.clear()

    @property
    def links(self) -> dict[str, list[str]]:
        """Get outgoing links dictionary (item_id -> list of link IDs)."""
        return self._links

    @property
    def linked_from(self) -> list[str]:
        """Get incoming links list (link IDs where this storage is target)."""
        return self._linked_from

    def add_link(self, item_id: str, link_id: str) -> None:
        """Add an outgoing link for an item.

        Args:
            item_id: ID of the item (search_result_id or extracted_content_id)
            link_id: ID of the link
        """
        if item_id not in self._links:
            self._links[item_id] = []
        if link_id not in self._links[item_id]:
            self._links[item_id].append(link_id)

    def add_linked_from(self, link_id: str) -> None:
        """Add an incoming link.

        Args:
            link_id: ID of the link
        """
        if link_id not in self._linked_from:
            self._linked_from.append(link_id)

    def get_state_summary(self) -> str:
        """Get a human-readable summary of the storage state.

        Returns:
            Formatted string summary of search results and extracted contents.
        """
        stats = self.get_statistics()
        lines: list[str] = []
        lines.append(f"Search: {stats['total_searches']} queries, {stats['total_results']} results, {stats['total_extractions']} extractions")
        if stats["unique_urls"] > 0:
            lines.append(f"  - {stats['unique_urls']} unique URLs")
        if self._search_results:
            latest_result = list(self._search_results.values())[-1]
            lines.append(f"  Latest result: {latest_result.title[:100]}..." if len(latest_result.title) > 100 else f"  Latest result: {latest_result.title}")
        return "\n".join(lines)

    def get_outputs_for_linking(self) -> list[dict[str, str]]:
        """Get list of linkable items with their IDs and descriptions.

        Returns:
            List of dictionaries with 'id' and 'description' keys for search results and extracted contents.
        """
        linkable_items: list[dict[str, str]] = []
        # Add search results
        for result_id, result in self._search_results.items():
            description = f"Search result: {result.title[:100]}..." if len(result.title) > 100 else f"Search result: {result.title}"
            linkable_items.append({"id": result_id, "description": description})
        # Add extracted contents
        for content_id, content in self._extracted_contents.items():
            description = f"Extracted content from {content.url}: {content.content[:100]}..." if len(content.content) > 100 else f"Extracted content from {content.url}: {content.content}"
            linkable_items.append({"id": content_id, "description": description})
        return linkable_items
