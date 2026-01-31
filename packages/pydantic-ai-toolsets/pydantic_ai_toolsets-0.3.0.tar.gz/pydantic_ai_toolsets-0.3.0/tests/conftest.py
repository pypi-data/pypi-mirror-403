"""Shared fixtures and test configuration for pytest."""

from __future__ import annotations

import pytest
from typing import Any

from pydantic_ai_toolsets.toolsets.chain_of_thought_reasoning.storage import CoTStorage
from pydantic_ai_toolsets.toolsets.chain_of_thought_reasoning.types import Thought
from pydantic_ai_toolsets.toolsets.tree_of_thought_reasoning.storage import ToTStorage
from pydantic_ai_toolsets.toolsets.tree_of_thought_reasoning.types import ThoughtNode, BranchEvaluation
from pydantic_ai_toolsets.toolsets.reflection.storage import ReflectionStorage
from pydantic_ai_toolsets.toolsets.reflection.types import ReflectionOutput, Critique
from pydantic_ai_toolsets.toolsets.to_do.storage import TodoStorage
from pydantic_ai_toolsets.toolsets.to_do.types import Todo


@pytest.fixture
def empty_cot_storage() -> CoTStorage:
    """Create an empty CoTStorage instance."""
    return CoTStorage()


@pytest.fixture
def cot_storage_with_metrics() -> CoTStorage:
    """Create a CoTStorage instance with metrics tracking enabled."""
    return CoTStorage(track_usage=True)


@pytest.fixture
def sample_thought() -> Thought:
    """Create a sample Thought for testing."""
    return Thought(
        thought_number=1,
        thought="This is a test thought",
        total_thoughts=3,
        is_revision=False,
        revises_thought=None,
        branch_id=None,
        branch_from_thought=None,
        next_thought_needed=True,
    )


@pytest.fixture
def sample_thought_revision() -> Thought:
    """Create a sample revision Thought for testing."""
    return Thought(
        thought_number=2,
        thought="This is a revised thought",
        total_thoughts=3,
        is_revision=True,
        revises_thought=1,
        branch_id=None,
        branch_from_thought=None,
        next_thought_needed=True,
    )


@pytest.fixture
def sample_thought_branch() -> Thought:
    """Create a sample branched Thought for testing."""
    return Thought(
        thought_number=3,
        thought="This is a branched thought",
        total_thoughts=5,
        is_revision=False,
        revises_thought=None,
        branch_id="branch_1",
        branch_from_thought=1,
        next_thought_needed=False,
    )


@pytest.fixture
def cot_storage_with_data(empty_cot_storage: CoTStorage, sample_thought: Thought) -> CoTStorage:
    """Create a CoTStorage instance with sample data."""
    empty_cot_storage.thoughts = sample_thought
    return empty_cot_storage


@pytest.fixture
def empty_tot_storage() -> ToTStorage:
    """Create an empty ToTStorage instance."""
    return ToTStorage()


@pytest.fixture
def sample_node() -> ThoughtNode:
    """Create a sample ThoughtNode for testing."""
    return ThoughtNode(
        node_id="node_1",
        content="This is a test node",
        parent_id=None,
        branch_id="branch_1",
        is_solution=False,
        status="active",
    )


@pytest.fixture
def empty_reflection_storage() -> ReflectionStorage:
    """Create an empty ReflectionStorage instance."""
    return ReflectionStorage()


@pytest.fixture
def sample_output() -> ReflectionOutput:
    """Create a sample ReflectionOutput for testing."""
    return ReflectionOutput(
        output_id="output_1",
        content="This is a test output",
        cycle=0,
        parent_id=None,
        quality_score=80.0,
        is_final=False,
    )


@pytest.fixture
def sample_critique() -> Critique:
    """Create a sample Critique for testing."""
    return Critique(
        critique_id="critique_1",
        output_id="output_1",
        problems=["Problem 1"],
        strengths=["Strength 1"],
        overall_assessment="Overall assessment",
        improvement_suggestions=["Suggestion 1"],
    )


@pytest.fixture
def empty_todo_storage() -> TodoStorage:
    """Create an empty TodoStorage instance."""
    return TodoStorage()


@pytest.fixture
def sample_todo() -> Todo:
    """Create a sample Todo for testing."""
    return Todo(
        todo_id="todo_1",
        content="Test task",
        status="pending",
        active_form="Testing task",
    )


@pytest.fixture
def mock_storage() -> Any:
    """Factory fixture for creating mock storage objects."""
    from unittest.mock import MagicMock
    
    mock = MagicMock()
    mock.thoughts = []
    mock.metrics = None
    return mock
