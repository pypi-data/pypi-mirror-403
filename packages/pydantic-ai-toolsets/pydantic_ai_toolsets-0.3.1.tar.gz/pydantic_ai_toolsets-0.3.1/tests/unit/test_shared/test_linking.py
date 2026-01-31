"""Unit tests for linking utilities."""

from __future__ import annotations

import pytest

from pydantic_ai_toolsets.toolsets._shared.linking import LinkManager
from pydantic_ai_toolsets.toolsets.meta_orchestrator.types import LinkType


class TestLinkManager:
    """Test suite for LinkManager."""

    def test_initialization(self):
        """Test LinkManager initialization."""
        manager = LinkManager()
        assert manager._links == {}
        assert manager._links_by_source == {}
        assert manager._links_by_target == {}

    def test_create_link(self):
        """Test creating a link."""
        manager = LinkManager()
        link_id = manager.create_link(
            source_toolset="search",
            source_id="result_1",
            target_toolset="self_ask",
            target_id="question_1",
            link_type=LinkType.REFERENCES,
        )
        
        assert link_id is not None
        assert link_id in manager._links
        link = manager._links[link_id]
        assert link.source_toolset_id == "search"
        assert link.source_item_id == "result_1"
        assert link.target_toolset_id == "self_ask"
        assert link.target_item_id == "question_1"
        assert link.link_type == LinkType.REFERENCES

    def test_create_link_with_custom_id(self):
        """Test creating a link with custom ID."""
        manager = LinkManager()
        link_id = manager.create_link(
            source_toolset="search",
            source_id="result_1",
            target_toolset="self_ask",
            target_id="question_1",
            link_type=LinkType.REFERENCES,
            link_id="custom_link_1",
        )
        
        assert link_id == "custom_link_1"
        assert "custom_link_1" in manager._links

    def test_create_link_self_reference_raises_error(self):
        """Test that creating a self-link raises ValueError."""
        manager = LinkManager()
        with pytest.raises(ValueError, match="Cannot create link from an item to itself"):
            manager.create_link(
                source_toolset="search",
                source_id="result_1",
                target_toolset="search",
                target_id="result_1",
                link_type=LinkType.REFERENCES,
            )

    def test_create_link_indexes_source(self):
        """Test that links are indexed by source."""
        manager = LinkManager()
        link_id = manager.create_link(
            source_toolset="search",
            source_id="result_1",
            target_toolset="self_ask",
            target_id="question_1",
            link_type=LinkType.REFERENCES,
        )
        
        source_key = ("search", "result_1")
        assert source_key in manager._links_by_source
        assert link_id in manager._links_by_source[source_key]

    def test_create_link_indexes_target(self):
        """Test that links are indexed by target."""
        manager = LinkManager()
        link_id = manager.create_link(
            source_toolset="search",
            source_id="result_1",
            target_toolset="self_ask",
            target_id="question_1",
            link_type=LinkType.REFERENCES,
        )
        
        target_key = ("self_ask", "question_1")
        assert target_key in manager._links_by_target
        assert link_id in manager._links_by_target[target_key]

    def test_get_links_outgoing(self):
        """Test getting outgoing links."""
        manager = LinkManager()
        link_id = manager.create_link(
            source_toolset="search",
            source_id="result_1",
            target_toolset="self_ask",
            target_id="question_1",
            link_type=LinkType.REFERENCES,
        )
        
        links = manager.get_links("search", "result_1")
        assert len(links) == 1
        assert links[0].link_id == link_id

    def test_get_links_incoming(self):
        """Test getting incoming links."""
        manager = LinkManager()
        link_id = manager.create_link(
            source_toolset="search",
            source_id="result_1",
            target_toolset="self_ask",
            target_id="question_1",
            link_type=LinkType.REFERENCES,
        )
        
        links = manager.get_links("self_ask", "question_1")
        assert len(links) == 1
        assert links[0].link_id == link_id

    def test_get_links_both_directions(self):
        """Test getting links when item is both source and target."""
        manager = LinkManager()
        # Create link where item is source
        link1 = manager.create_link(
            source_toolset="search",
            source_id="result_1",
            target_toolset="self_ask",
            target_id="question_1",
            link_type=LinkType.REFERENCES,
        )
        # Create link where item is target
        link2 = manager.create_link(
            source_toolset="self_ask",
            source_id="question_1",
            target_toolset="search",
            target_id="result_1",
            link_type=LinkType.REFERENCES,
        )
        
        links = manager.get_links("search", "result_1")
        assert len(links) == 2
        link_ids = {link.link_id for link in links}
        assert link1 in link_ids
        assert link2 in link_ids

    def test_get_outgoing_links(self):
        """Test getting only outgoing links."""
        manager = LinkManager()
        link_id = manager.create_link(
            source_toolset="search",
            source_id="result_1",
            target_toolset="self_ask",
            target_id="question_1",
            link_type=LinkType.REFERENCES,
        )
        
        links = manager.get_outgoing_links("search", "result_1")
        assert len(links) == 1
        assert links[0].link_id == link_id
        
        # Should return empty for target
        links = manager.get_outgoing_links("self_ask", "question_1")
        assert len(links) == 0

    def test_get_incoming_links(self):
        """Test getting only incoming links."""
        manager = LinkManager()
        link_id = manager.create_link(
            source_toolset="search",
            source_id="result_1",
            target_toolset="self_ask",
            target_id="question_1",
            link_type=LinkType.REFERENCES,
        )
        
        links = manager.get_incoming_links("self_ask", "question_1")
        assert len(links) == 1
        assert links[0].link_id == link_id
        
        # Should return empty for source
        links = manager.get_incoming_links("search", "result_1")
        assert len(links) == 0

    def test_resolve_link(self):
        """Test resolving a link by ID."""
        manager = LinkManager()
        link_id = manager.create_link(
            source_toolset="search",
            source_id="result_1",
            target_toolset="self_ask",
            target_id="question_1",
            link_type=LinkType.REFERENCES,
        )
        
        link = manager.resolve_link(link_id)
        assert link is not None
        assert link.link_id == link_id

    def test_resolve_link_not_found(self):
        """Test resolving a non-existent link."""
        manager = LinkManager()
        link = manager.resolve_link("nonexistent")
        assert link is None

    def test_delete_link(self):
        """Test deleting a link."""
        manager = LinkManager()
        link_id = manager.create_link(
            source_toolset="search",
            source_id="result_1",
            target_toolset="self_ask",
            target_id="question_1",
            link_type=LinkType.REFERENCES,
        )
        
        result = manager.delete_link(link_id)
        assert result is True
        assert link_id not in manager._links
        assert ("search", "result_1") not in manager._links_by_source
        assert ("self_ask", "question_1") not in manager._links_by_target

    def test_delete_link_not_found(self):
        """Test deleting a non-existent link."""
        manager = LinkManager()
        result = manager.delete_link("nonexistent")
        assert result is False

    def test_delete_link_removes_from_indexes(self):
        """Test that deleting a link removes it from all indexes."""
        manager = LinkManager()
        link_id = manager.create_link(
            source_toolset="search",
            source_id="result_1",
            target_toolset="self_ask",
            target_id="question_1",
            link_type=LinkType.REFERENCES,
        )
        
        # Create another link from same source
        link_id2 = manager.create_link(
            source_toolset="search",
            source_id="result_1",
            target_toolset="self_ask",
            target_id="question_2",
            link_type=LinkType.REFERENCES,
        )
        
        # Delete first link
        manager.delete_link(link_id)
        
        # Source should still have second link
        source_key = ("search", "result_1")
        assert source_key in manager._links_by_source
        assert link_id2 in manager._links_by_source[source_key]
        assert link_id not in manager._links_by_source[source_key]

    def test_delete_link_removes_empty_index_entries(self):
        """Test that deleting a link removes empty index entries."""
        manager = LinkManager()
        link_id = manager.create_link(
            source_toolset="search",
            source_id="result_1",
            target_toolset="self_ask",
            target_id="question_1",
            link_type=LinkType.REFERENCES,
        )
        
        manager.delete_link(link_id)
        
        # Indexes should be empty
        assert ("search", "result_1") not in manager._links_by_source
        assert ("self_ask", "question_1") not in manager._links_by_target

    def test_clear(self):
        """Test clearing all links."""
        manager = LinkManager()
        manager.create_link(
            source_toolset="search",
            source_id="result_1",
            target_toolset="self_ask",
            target_id="question_1",
            link_type=LinkType.REFERENCES,
        )
        manager.create_link(
            source_toolset="self_ask",
            source_id="question_1",
            target_toolset="reflection",
            target_id="output_1",
            link_type=LinkType.REFINES,
        )
        
        manager.clear()
        
        assert len(manager._links) == 0
        assert len(manager._links_by_source) == 0
        assert len(manager._links_by_target) == 0

    def test_get_all_links(self):
        """Test getting all links."""
        manager = LinkManager()
        link_id1 = manager.create_link(
            source_toolset="search",
            source_id="result_1",
            target_toolset="self_ask",
            target_id="question_1",
            link_type=LinkType.REFERENCES,
        )
        link_id2 = manager.create_link(
            source_toolset="self_ask",
            source_id="question_1",
            target_toolset="reflection",
            target_id="output_1",
            link_type=LinkType.REFINES,
        )
        
        all_links = manager.get_all_links()
        assert len(all_links) == 2
        link_ids = {link.link_id for link in all_links}
        assert link_id1 in link_ids
        assert link_id2 in link_ids

    def test_get_statistics(self):
        """Test getting link statistics."""
        manager = LinkManager()
        manager.create_link(
            source_toolset="search",
            source_id="result_1",
            target_toolset="self_ask",
            target_id="question_1",
            link_type=LinkType.REFERENCES,
        )
        manager.create_link(
            source_toolset="self_ask",
            source_id="question_1",
            target_toolset="reflection",
            target_id="output_1",
            link_type=LinkType.REFINES,
        )
        manager.create_link(
            source_toolset="reflection",
            source_id="output_1",
            target_toolset="search",
            target_id="result_1",
            link_type=LinkType.REFERENCES,
        )
        
        stats = manager.get_statistics()
        assert stats["total_links"] == 3
        assert "references" in stats["links_by_type"]
        assert stats["links_by_type"]["references"] == 2
        assert stats["links_by_type"]["refines"] == 1

    def test_get_statistics_empty(self):
        """Test getting statistics with no links."""
        manager = LinkManager()
        stats = manager.get_statistics()
        assert stats["total_links"] == 0
        assert stats["links_by_type"] == {}

    def test_all_link_types(self):
        """Test creating links with all link types."""
        manager = LinkManager()
        
        for link_type in LinkType:
            link_id = manager.create_link(
                source_toolset="source",
                source_id="item_1",
                target_toolset="target",
                target_id="item_2",
                link_type=link_type,
            )
            link = manager.resolve_link(link_id)
            assert link.link_type == link_type
