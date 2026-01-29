"""Cross-toolset linking infrastructure for creating references between toolset outputs."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from ..meta_orchestrator.types import CrossToolsetLink, LinkType


@dataclass
class LinkManager:
    """Manages cross-toolset links between outputs from different toolsets.

    This class provides a centralized way to create, track, and resolve links
    between items across different toolsets. Links can represent relationships
    like "refines", "explores", "synthesizes", or "references".

    Attributes:
        _links: Dictionary mapping link IDs to CrossToolsetLink objects
        _links_by_source: Dictionary mapping (toolset_id, item_id) to list of link IDs
        _links_by_target: Dictionary mapping (toolset_id, item_id) to list of link IDs

    Example:
        ```python
        from pydantic_ai_toolsets.toolsets._shared.linking import LinkManager

        link_manager = LinkManager()

        # Create a link
        link_id = link_manager.create_link(
            source_toolset="search",
            source_id="result_123",
            target_toolset="self_ask",
            target_id="question_456",
            link_type=LinkType.REFERENCES
        )

        # Get all links for an item
        links = link_manager.get_links("search", "result_123")

        # Resolve a link
        link = link_manager.resolve_link(link_id)
        ```
    """

    _links: dict[str, CrossToolsetLink] = field(default_factory=dict)
    _links_by_source: dict[tuple[str, str], list[str]] = field(default_factory=dict)
    _links_by_target: dict[tuple[str, str], list[str]] = field(default_factory=dict)

    def create_link(
        self,
        source_toolset: str,
        source_id: str,
        target_toolset: str,
        target_id: str,
        link_type: LinkType,
        link_id: str | None = None,
    ) -> str:
        """Create a link between outputs from different toolsets.

        Args:
            source_toolset: ID of the source toolset
            source_id: ID of the item in the source toolset
            target_toolset: ID of the target toolset
            target_id: ID of the item in the target toolset
            link_type: Type of link (refines, explores, synthesizes, references)
            link_id: Optional custom link ID. If not provided, generates a unique ID.

        Returns:
            The link ID (either provided or generated)

        Raises:
            ValueError: If source and target are the same item
        """
        if source_toolset == target_toolset and source_id == target_id:
            raise ValueError("Cannot create link from an item to itself")

        if link_id is None:
            import uuid

            link_id = str(uuid.uuid4())

        link = CrossToolsetLink(
            link_id=link_id,
            source_toolset_id=source_toolset,
            source_item_id=source_id,
            target_toolset_id=target_toolset,
            target_item_id=target_id,
            link_type=link_type,
            created_at=time.time(),
        )

        self._links[link_id] = link

        # Index by source
        source_key = (source_toolset, source_id)
        if source_key not in self._links_by_source:
            self._links_by_source[source_key] = []
        self._links_by_source[source_key].append(link_id)

        # Index by target
        target_key = (target_toolset, target_id)
        if target_key not in self._links_by_target:
            self._links_by_target[target_key] = []
        self._links_by_target[target_key].append(link_id)

        return link_id

    def get_links(self, toolset_id: str, item_id: str) -> list[CrossToolsetLink]:
        """Get all links for a specific item (both outgoing and incoming).

        Args:
            toolset_id: ID of the toolset
            item_id: ID of the item

        Returns:
            List of CrossToolsetLink objects where the item is either source or target
        """
        links: list[CrossToolsetLink] = []

        # Get outgoing links (where this item is the source)
        source_key = (toolset_id, item_id)
        if source_key in self._links_by_source:
            for link_id in self._links_by_source[source_key]:
                if link_id in self._links:
                    links.append(self._links[link_id])

        # Get incoming links (where this item is the target)
        target_key = (toolset_id, item_id)
        if target_key in self._links_by_target:
            for link_id in self._links_by_target[target_key]:
                if link_id in self._links:
                    links.append(self._links[link_id])

        return links

    def get_outgoing_links(self, toolset_id: str, item_id: str) -> list[CrossToolsetLink]:
        """Get outgoing links from a specific item.

        Args:
            toolset_id: ID of the toolset
            item_id: ID of the item

        Returns:
            List of CrossToolsetLink objects where the item is the source
        """
        links: list[CrossToolsetLink] = []
        source_key = (toolset_id, item_id)
        if source_key in self._links_by_source:
            for link_id in self._links_by_source[source_key]:
                if link_id in self._links:
                    links.append(self._links[link_id])
        return links

    def get_incoming_links(self, toolset_id: str, item_id: str) -> list[CrossToolsetLink]:
        """Get incoming links to a specific item.

        Args:
            toolset_id: ID of the toolset
            item_id: ID of the item

        Returns:
            List of CrossToolsetLink objects where the item is the target
        """
        links: list[CrossToolsetLink] = []
        target_key = (toolset_id, item_id)
        if target_key in self._links_by_target:
            for link_id in self._links_by_target[target_key]:
                if link_id in self._links:
                    links.append(self._links[link_id])
        return links

    def resolve_link(self, link_id: str) -> CrossToolsetLink | None:
        """Get a link by its ID.

        Args:
            link_id: ID of the link to resolve

        Returns:
            CrossToolsetLink if found, None otherwise
        """
        return self._links.get(link_id)

    def delete_link(self, link_id: str) -> bool:
        """Delete a link by its ID.

        Args:
            link_id: ID of the link to delete

        Returns:
            True if link was deleted, False if not found
        """
        if link_id not in self._links:
            return False

        link = self._links[link_id]

        # Remove from source index
        source_key = (link.source_toolset_id, link.source_item_id)
        if source_key in self._links_by_source:
            self._links_by_source[source_key] = [
                lid for lid in self._links_by_source[source_key] if lid != link_id
            ]
            if not self._links_by_source[source_key]:
                del self._links_by_source[source_key]

        # Remove from target index
        target_key = (link.target_toolset_id, link.target_item_id)
        if target_key in self._links_by_target:
            self._links_by_target[target_key] = [
                lid for lid in self._links_by_target[target_key] if lid != link_id
            ]
            if not self._links_by_target[target_key]:
                del self._links_by_target[target_key]

        # Remove from main dictionary
        del self._links[link_id]

        return True

    def clear(self) -> None:
        """Clear all links."""
        self._links.clear()
        self._links_by_source.clear()
        self._links_by_target.clear()

    def get_all_links(self) -> list[CrossToolsetLink]:
        """Get all links.

        Returns:
            List of all CrossToolsetLink objects
        """
        return list(self._links.values())

    def get_statistics(self) -> dict[str, Any]:
        """Get statistics about links.

        Returns:
            Dictionary with link counts by type and total counts
        """
        stats: dict[str, Any] = {
            "total_links": len(self._links),
            "links_by_type": {},
        }

        for link in self._links.values():
            link_type_str = link.link_type.value
            stats["links_by_type"][link_type_str] = stats["links_by_type"].get(link_type_str, 0) + 1

        return stats
