"""Integration tests for cross-toolset linking."""

from __future__ import annotations

import pytest

from pydantic_ai_toolsets.toolsets._shared.linking import LinkManager
from pydantic_ai_toolsets.toolsets.meta_orchestrator.types import LinkType


class TestCrossToolsetLinking:
    """Test suite for cross-toolset linking functionality."""

    def test_create_link_between_toolsets(self):
        """Test creating links between different toolsets."""
        manager = LinkManager()
        
        link_id = manager.create_link(
            source_toolset="search",
            source_id="result_123",
            target_toolset="self_ask",
            target_id="question_456",
            link_type=LinkType.REFERENCES,
        )
        
        assert link_id is not None
        link = manager.resolve_link(link_id)
        assert link is not None
        assert link.source_toolset_id == "search"
        assert link.target_toolset_id == "self_ask"

    def test_create_multiple_link_types(self):
        """Test creating links with different link types."""
        manager = LinkManager()
        
        link1 = manager.create_link(
            source_toolset="search",
            source_id="result_1",
            target_toolset="self_ask",
            target_id="question_1",
            link_type=LinkType.REFERENCES,
        )
        
        link2 = manager.create_link(
            source_toolset="self_ask",
            source_id="question_1",
            target_toolset="reflection",
            target_id="output_1",
            link_type=LinkType.REFINES,
        )
        
        link3 = manager.create_link(
            source_toolset="cot",
            source_id="thought_1",
            target_toolset="tot",
            target_id="node_1",
            link_type=LinkType.EXPLORES,
        )
        
        assert link1 != link2 != link3
        assert manager.get_statistics()["total_links"] == 3

    def test_get_links_for_item(self):
        """Test getting all links for a specific item."""
        manager = LinkManager()
        
        # Create multiple links from same source
        manager.create_link(
            source_toolset="search",
            source_id="result_1",
            target_toolset="self_ask",
            target_id="question_1",
            link_type=LinkType.REFERENCES,
        )
        manager.create_link(
            source_toolset="search",
            source_id="result_1",
            target_toolset="self_ask",
            target_id="question_2",
            link_type=LinkType.REFERENCES,
        )
        
        links = manager.get_links("search", "result_1")
        assert len(links) == 2

    def test_link_statistics(self):
        """Test link statistics across multiple link types."""
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
        assert stats["links_by_type"]["references"] == 2
        assert stats["links_by_type"]["refines"] == 1
