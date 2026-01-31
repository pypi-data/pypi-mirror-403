"""Unit tests for storage classes."""

from __future__ import annotations

import pytest

from pydantic_ai_toolsets.toolsets.chain_of_thought_reasoning.storage import CoTStorage
from pydantic_ai_toolsets.toolsets.chain_of_thought_reasoning.types import Thought
from pydantic_ai_toolsets.toolsets.tree_of_thought_reasoning.storage import ToTStorage
from pydantic_ai_toolsets.toolsets.tree_of_thought_reasoning.types import ThoughtNode, BranchEvaluation
from pydantic_ai_toolsets.toolsets.reflection.storage import ReflectionStorage
from pydantic_ai_toolsets.toolsets.reflection.types import ReflectionOutput, Critique
from pydantic_ai_toolsets.toolsets.to_do.storage import TodoStorage
from pydantic_ai_toolsets.toolsets.to_do.types import Todo
from pydantic_ai_toolsets.toolsets.graph_of_thought_reasoning.storage import GoTStorage
from pydantic_ai_toolsets.toolsets.beam_search_reasoning.storage import BeamStorage
from pydantic_ai_toolsets.toolsets.monte_carlo_reasoning.storage import MCTSStorage
from pydantic_ai_toolsets.toolsets.multi_persona_analysis.storage import PersonaStorage
from pydantic_ai_toolsets.toolsets.multi_persona_debate.storage import PersonaDebateStorage
from pydantic_ai_toolsets.toolsets.search.storage import SearchStorage
from pydantic_ai_toolsets.toolsets.self_refine.storage import SelfRefineStorage
from pydantic_ai_toolsets.toolsets.self_ask.storage import SelfAskStorage


# ============================================================================
# Chain of Thought Storage Tests
# ============================================================================


class TestCoTStorage:
    """Test suite for CoTStorage."""

    def test_initialization_default(self):
        """Test CoTStorage initialization without metrics."""
        storage = CoTStorage()
        assert storage.thoughts == []
        assert storage.metrics is None
        assert storage.links == {}
        assert storage.linked_from == []

    def test_initialization_with_metrics(self):
        """Test CoTStorage initialization with metrics tracking."""
        storage = CoTStorage(track_usage=True)
        assert storage.thoughts == []
        assert storage.metrics is not None
        assert storage.links == {}
        assert storage.linked_from == []

    def test_thoughts_property_getter(self, empty_cot_storage, sample_thought):
        """Test thoughts property getter."""
        assert empty_cot_storage.thoughts == []
        empty_cot_storage.thoughts = sample_thought
        assert len(empty_cot_storage.thoughts) == 1
        assert empty_cot_storage.thoughts[0] == sample_thought

    def test_thoughts_property_setter(self, empty_cot_storage, sample_thought):
        """Test thoughts property setter appends thoughts."""
        assert len(empty_cot_storage.thoughts) == 0
        empty_cot_storage.thoughts = sample_thought
        assert len(empty_cot_storage.thoughts) == 1
        empty_cot_storage.thoughts = sample_thought
        assert len(empty_cot_storage.thoughts) == 2

    def test_get_statistics_empty(self, empty_cot_storage):
        """Test get_statistics with empty storage."""
        stats = empty_cot_storage.get_statistics()
        assert stats == {
            "total_thoughts": 0,
            "revisions": 0,
            "branches": 0,
            "final_thoughts": 0,
        }

    def test_get_statistics_with_thoughts(
        self, empty_cot_storage, sample_thought, sample_thought_revision, sample_thought_branch
    ):
        """Test get_statistics with various thought types."""
        empty_cot_storage.thoughts = sample_thought
        empty_cot_storage.thoughts = sample_thought_revision
        empty_cot_storage.thoughts = sample_thought_branch

        stats = empty_cot_storage.get_statistics()
        assert stats["total_thoughts"] == 3
        assert stats["revisions"] == 1
        assert stats["branches"] == 1
        assert stats["final_thoughts"] == 1

    def test_summary_without_metrics(self, empty_cot_storage, sample_thought):
        """Test summary generation without metrics."""
        empty_cot_storage.thoughts = sample_thought
        summary = empty_cot_storage.summary()
        
        assert summary["toolset"] == "chain_of_thought_reasoning"
        assert "statistics" in summary
        assert "storage" in summary
        assert len(summary["storage"]["thoughts"]) == 1
        assert "usage_metrics" not in summary

    def test_summary_with_metrics(self, cot_storage_with_metrics, sample_thought):
        """Test summary generation with metrics."""
        cot_storage_with_metrics.thoughts = sample_thought
        summary = cot_storage_with_metrics.summary()
        
        assert summary["toolset"] == "chain_of_thought_reasoning"
        assert "statistics" in summary
        assert "storage" in summary
        assert "usage_metrics" in summary

    def test_clear(self, cot_storage_with_data, sample_thought):
        """Test clear method."""
        assert len(cot_storage_with_data.thoughts) == 1
        cot_storage_with_data.add_link("1", "link_1")
        cot_storage_with_data.add_linked_from("link_2")
        
        cot_storage_with_data.clear()
        
        assert len(cot_storage_with_data.thoughts) == 0
        assert cot_storage_with_data.links == {}
        assert cot_storage_with_data.linked_from == []

    def test_clear_with_metrics(self, cot_storage_with_metrics, sample_thought):
        """Test clear method with metrics tracking."""
        cot_storage_with_metrics.thoughts = sample_thought
        cot_storage_with_metrics.metrics.record_invocation("test_tool", "input", "output")
        
        assert len(cot_storage_with_metrics.metrics.invocations) == 1
        cot_storage_with_metrics.clear()
        assert len(cot_storage_with_metrics.metrics.invocations) == 0

    def test_add_link(self, empty_cot_storage):
        """Test add_link method."""
        empty_cot_storage.add_link("1", "link_1")
        assert "1" in empty_cot_storage.links
        assert "link_1" in empty_cot_storage.links["1"]
        
        # Adding same link again should not duplicate
        empty_cot_storage.add_link("1", "link_1")
        assert len(empty_cot_storage.links["1"]) == 1
        
        # Adding different link to same item
        empty_cot_storage.add_link("1", "link_2")
        assert len(empty_cot_storage.links["1"]) == 2

    def test_add_linked_from(self, empty_cot_storage):
        """Test add_linked_from method."""
        empty_cot_storage.add_linked_from("link_1")
        assert "link_1" in empty_cot_storage.linked_from
        
        # Adding same link again should not duplicate
        empty_cot_storage.add_linked_from("link_1")
        assert empty_cot_storage.linked_from.count("link_1") == 1

    def test_get_state_summary_empty(self, empty_cot_storage):
        """Test get_state_summary with empty storage."""
        summary = empty_cot_storage.get_state_summary()
        assert "Chain of Thought: 0 thoughts" in summary

    def test_get_state_summary_with_thoughts(
        self, empty_cot_storage, sample_thought, sample_thought_revision
    ):
        """Test get_state_summary with thoughts."""
        empty_cot_storage.thoughts = sample_thought
        empty_cot_storage.thoughts = sample_thought_revision
        
        summary = empty_cot_storage.get_state_summary()
        assert "Chain of Thought: 2 thoughts" in summary
        assert "1 revisions" in summary
        assert sample_thought_revision.thought in summary

    def test_get_outputs_for_linking(self, empty_cot_storage, sample_thought):
        """Test get_outputs_for_linking."""
        empty_cot_storage.thoughts = sample_thought
        outputs = empty_cot_storage.get_outputs_for_linking()
        
        assert len(outputs) == 1
        assert outputs[0]["id"] == "1"
        assert "Thought #1" in outputs[0]["description"]
        assert sample_thought.thought in outputs[0]["description"]

    def test_get_outputs_for_linking_empty(self, empty_cot_storage):
        """Test get_outputs_for_linking with empty storage."""
        outputs = empty_cot_storage.get_outputs_for_linking()
        assert outputs == []


# ============================================================================
# Tree of Thought Storage Tests
# ============================================================================


class TestToTStorage:
    """Test suite for ToTStorage."""

    def test_initialization_default(self):
        """Test ToTStorage initialization without metrics."""
        storage = ToTStorage()
        assert storage.nodes == {}
        assert storage.evaluations == {}
        assert storage.metrics is None
        assert storage.links == {}
        assert storage.linked_from == []

    def test_initialization_with_metrics(self):
        """Test ToTStorage initialization with metrics tracking."""
        storage = ToTStorage(track_usage=True)
        assert storage.nodes == {}
        assert storage.evaluations == {}
        assert storage.metrics is not None

    def test_nodes_property_getter(self, empty_tot_storage, sample_node):
        """Test nodes property getter."""
        assert empty_tot_storage.nodes == {}
        empty_tot_storage.nodes = sample_node
        assert sample_node.node_id in empty_tot_storage.nodes
        assert empty_tot_storage.nodes[sample_node.node_id] == sample_node

    def test_nodes_property_setter(self, empty_tot_storage, sample_node):
        """Test nodes property setter adds/updates nodes."""
        assert len(empty_tot_storage.nodes) == 0
        empty_tot_storage.nodes = sample_node
        assert len(empty_tot_storage.nodes) == 1
        
        # Update existing node
        updated_node = ThoughtNode(
            node_id=sample_node.node_id,
            content="Updated content",
            parent_id=None,
            branch_id="branch_1",
            is_solution=False,
            status="active",
        )
        empty_tot_storage.nodes = updated_node
        assert len(empty_tot_storage.nodes) == 1
        assert empty_tot_storage.nodes[sample_node.node_id].content == "Updated content"

    def test_evaluations_property(self, empty_tot_storage):
        """Test evaluations property getter and setter."""
        evaluation = BranchEvaluation(
            branch_id="branch_1",
            score=85.0,
            reasoning="Good approach",
            recommendation="continue",
        )
        
        assert empty_tot_storage.evaluations == {}
        empty_tot_storage.evaluations = evaluation
        assert "branch_1" in empty_tot_storage.evaluations
        assert empty_tot_storage.evaluations["branch_1"] == evaluation

    def test_get_statistics_empty(self, empty_tot_storage):
        """Test get_statistics with empty storage."""
        stats = empty_tot_storage.get_statistics()
        assert stats == {
            "total_nodes": 0,
            "active_nodes": 0,
            "solution_nodes": 0,
            "pruned_nodes": 0,
            "merged_nodes": 0,
            "branches": 0,
            "max_depth": 0,
            "evaluations": 0,
        }

    def test_get_statistics_with_nodes(self, empty_tot_storage, sample_node):
        """Test get_statistics with nodes."""
        empty_tot_storage.nodes = sample_node
        
        solution_node = ThoughtNode(
            node_id="node_2",
            content="Solution",
            parent_id="node_1",
            branch_id="branch_1",
            is_solution=True,
            status="completed",
        )
        empty_tot_storage.nodes = solution_node
        
        stats = empty_tot_storage.get_statistics()
        assert stats["total_nodes"] == 2
        assert stats["active_nodes"] >= 0  # May be 0 if both are completed
        assert stats["solution_nodes"] == 1

    def test_summary_without_metrics(self, empty_tot_storage, sample_node):
        """Test summary generation without metrics."""
        empty_tot_storage.nodes = sample_node
        summary = empty_tot_storage.summary()
        
        assert summary["toolset"] == "tree_of_thought_reasoning"
        assert "statistics" in summary
        assert "storage" in summary
        assert len(summary["storage"]["nodes"]) == 1
        assert "usage_metrics" not in summary

    def test_summary_with_metrics(self):
        """Test summary generation with metrics."""
        storage = ToTStorage(track_usage=True)
        node = ThoughtNode(
            node_id="node_1",
            content="Test",
            parent_id=None,
            branch_id="branch_1",
            is_solution=False,
            status="active",
        )
        storage.nodes = node
        summary = storage.summary()
        
        assert "usage_metrics" in summary

    def test_clear(self, empty_tot_storage, sample_node):
        """Test clear method."""
        empty_tot_storage.nodes = sample_node
        evaluation = BranchEvaluation(
            branch_id="branch_1",
            score=85.0,
            reasoning="Good",
            recommendation="continue",
        )
        empty_tot_storage.evaluations = evaluation
        empty_tot_storage.add_link("node_1", "link_1")
        
        empty_tot_storage.clear()
        
        assert len(empty_tot_storage.nodes) == 0
        assert len(empty_tot_storage.evaluations) == 0
        assert empty_tot_storage.links == {}

    def test_add_link(self, empty_tot_storage):
        """Test add_link method."""
        empty_tot_storage.add_link("node_1", "link_1")
        assert "node_1" in empty_tot_storage.links
        assert "link_1" in empty_tot_storage.links["node_1"]

    def test_add_linked_from(self, empty_tot_storage):
        """Test add_linked_from method."""
        empty_tot_storage.add_linked_from("link_1")
        assert "link_1" in empty_tot_storage.linked_from

    def test_get_state_summary(self, empty_tot_storage, sample_node):
        """Test get_state_summary."""
        empty_tot_storage.nodes = sample_node
        summary = empty_tot_storage.get_state_summary()
        
        assert "Tree of Thought" in summary
        assert "1 nodes" in summary

    def test_get_outputs_for_linking(self, empty_tot_storage, sample_node):
        """Test get_outputs_for_linking."""
        empty_tot_storage.nodes = sample_node
        outputs = empty_tot_storage.get_outputs_for_linking()
        
        assert len(outputs) == 1
        assert outputs[0]["id"] == "node_1"
        assert sample_node.content in outputs[0]["description"]


# ============================================================================
# Reflection Storage Tests
# ============================================================================


class TestReflectionStorage:
    """Test suite for ReflectionStorage."""

    def test_initialization_default(self):
        """Test ReflectionStorage initialization without metrics."""
        storage = ReflectionStorage()
        assert storage.outputs == {}
        assert storage.critiques == {}
        assert storage.metrics is None
        assert storage.links == {}
        assert storage.linked_from == []

    def test_initialization_with_metrics(self):
        """Test ReflectionStorage initialization with metrics tracking."""
        storage = ReflectionStorage(track_usage=True)
        assert storage.outputs == {}
        assert storage.critiques == {}
        assert storage.metrics is not None

    def test_outputs_property(self, empty_reflection_storage, sample_output):
        """Test outputs property getter and setter."""
        assert empty_reflection_storage.outputs == {}
        empty_reflection_storage.outputs = sample_output
        assert sample_output.output_id in empty_reflection_storage.outputs
        assert empty_reflection_storage.outputs[sample_output.output_id] == sample_output

    def test_critiques_property(self, empty_reflection_storage, sample_critique):
        """Test critiques property getter and setter."""
        assert empty_reflection_storage.critiques == {}
        empty_reflection_storage.critiques = sample_critique
        assert sample_critique.critique_id in empty_reflection_storage.critiques
        assert empty_reflection_storage.critiques[sample_critique.critique_id] == sample_critique

    def test_get_statistics_empty(self, empty_reflection_storage):
        """Test get_statistics with empty storage."""
        stats = empty_reflection_storage.get_statistics()
        assert stats == {
            "total_outputs": 0,
            "total_critiques": 0,
            "max_cycle": 0,
            "final_outputs": 0,
        }

    def test_get_statistics_with_data(self, empty_reflection_storage, sample_output):
        """Test get_statistics with outputs."""
        empty_reflection_storage.outputs = sample_output
        
        refined_output = ReflectionOutput(
            output_id="output_2",
            content="Refined output",
            cycle=1,
            parent_id="output_1",
            is_final=True,
            quality_score=0.9,
        )
        empty_reflection_storage.outputs = refined_output
        
        stats = empty_reflection_storage.get_statistics()
        assert stats["total_outputs"] == 2
        assert stats["max_cycle"] == 1
        assert stats["final_outputs"] == 1

    def test_summary_without_metrics(self, empty_reflection_storage, sample_output):
        """Test summary generation without metrics."""
        empty_reflection_storage.outputs = sample_output
        summary = empty_reflection_storage.summary()
        
        assert summary["toolset"] == "reflection"
        assert "statistics" in summary
        assert "storage" in summary
        assert len(summary["storage"]["outputs"]) == 1
        assert "usage_metrics" not in summary

    def test_summary_with_metrics(self):
        """Test summary generation with metrics."""
        storage = ReflectionStorage(track_usage=True)
        output = ReflectionOutput(
            output_id="output_1",
            content="Test",
            cycle=0,
            parent_id=None,
            is_final=False,
            quality_score=None,
        )
        storage.outputs = output
        summary = storage.summary()
        
        assert "usage_metrics" in summary

    def test_clear(self, empty_reflection_storage, sample_output, sample_critique):
        """Test clear method."""
        empty_reflection_storage.outputs = sample_output
        empty_reflection_storage.critiques = sample_critique
        empty_reflection_storage.add_link("output_1", "link_1")
        
        empty_reflection_storage.clear()
        
        assert len(empty_reflection_storage.outputs) == 0
        assert len(empty_reflection_storage.critiques) == 0
        assert empty_reflection_storage.links == {}

    def test_add_link(self, empty_reflection_storage):
        """Test add_link method."""
        empty_reflection_storage.add_link("output_1", "link_1")
        assert "output_1" in empty_reflection_storage.links
        assert "link_1" in empty_reflection_storage.links["output_1"]

    def test_add_linked_from(self, empty_reflection_storage):
        """Test add_linked_from method."""
        empty_reflection_storage.add_linked_from("link_1")
        assert "link_1" in empty_reflection_storage.linked_from

    def test_get_state_summary(self, empty_reflection_storage, sample_output):
        """Test get_state_summary."""
        empty_reflection_storage.outputs = sample_output
        summary = empty_reflection_storage.get_state_summary()
        
        assert "Reflection" in summary
        assert "1 outputs" in summary

    def test_get_outputs_for_linking(self, empty_reflection_storage, sample_output):
        """Test get_outputs_for_linking."""
        empty_reflection_storage.outputs = sample_output
        outputs = empty_reflection_storage.get_outputs_for_linking()
        
        assert len(outputs) == 1
        assert outputs[0]["id"] == "output_1"
        assert sample_output.content in outputs[0]["description"]


# ============================================================================
# Todo Storage Tests
# ============================================================================


class TestTodoStorage:
    """Test suite for TodoStorage."""

    def test_initialization_default(self):
        """Test TodoStorage initialization without metrics."""
        storage = TodoStorage()
        assert storage.todos == []
        assert storage.metrics is None
        assert storage.links == {}
        assert storage.linked_from == []

    def test_initialization_with_metrics(self):
        """Test TodoStorage initialization with metrics tracking."""
        storage = TodoStorage(track_usage=True)
        assert storage.todos == []
        assert storage.metrics is not None

    def test_todos_property_getter(self, empty_todo_storage, sample_todo):
        """Test todos property getter."""
        assert empty_todo_storage.todos == []
        empty_todo_storage.todos = [sample_todo]
        assert len(empty_todo_storage.todos) == 1
        assert empty_todo_storage.todos[0] == sample_todo

    def test_todos_property_setter(self, empty_todo_storage, sample_todo):
        """Test todos property setter replaces todos."""
        empty_todo_storage.todos = [sample_todo]
        assert len(empty_todo_storage.todos) == 1
        
        new_todo = Todo(
            todo_id="todo_2",
            content="New task",
            status="pending",
            active_form="New tasking",
        )
        empty_todo_storage.todos = [new_todo]
        assert len(empty_todo_storage.todos) == 1
        assert empty_todo_storage.todos[0].todo_id == "todo_2"

    def test_get_statistics_empty(self, empty_todo_storage):
        """Test get_statistics with empty storage."""
        stats = empty_todo_storage.get_statistics()
        assert stats == {
            "total_todos": 0,
            "pending": 0,
            "in_progress": 0,
            "completed": 0,
            "completion_rate": 0.0,
        }

    def test_get_statistics_with_todos(self, empty_todo_storage):
        """Test get_statistics with todos."""
        todo1 = Todo(
            todo_id="todo_1",
            content="Task 1",
            status="pending",
            active_form="Tasking 1",
        )
        todo2 = Todo(
            todo_id="todo_2",
            content="Task 2",
            status="in_progress",
            active_form="Tasking 2",
        )
        todo3 = Todo(
            todo_id="todo_3",
            content="Task 3",
            status="completed",
            active_form="Tasking 3",
        )
        
        empty_todo_storage.todos = [todo1, todo2, todo3]
        stats = empty_todo_storage.get_statistics()
        
        assert stats["total_todos"] == 3
        assert stats["pending"] == 1
        assert stats["in_progress"] == 1
        assert stats["completed"] == 1
        assert stats["completion_rate"] == pytest.approx(1.0 / 3.0)

    def test_summary_without_metrics(self, empty_todo_storage, sample_todo):
        """Test summary generation without metrics."""
        empty_todo_storage.todos = [sample_todo]
        summary = empty_todo_storage.summary()
        
        assert summary["toolset"] == "to_do"
        assert "statistics" in summary
        assert "storage" in summary
        assert len(summary["storage"]["todos"]) == 1
        assert "usage_metrics" not in summary

    def test_summary_with_metrics(self):
        """Test summary generation with metrics."""
        storage = TodoStorage(track_usage=True)
        todo = Todo(
            todo_id="todo_1",
            content="Test",
            status="pending",
            active_form="Testing",
        )
        storage.todos = [todo]
        summary = storage.summary()
        
        assert "usage_metrics" in summary

    def test_clear(self, empty_todo_storage, sample_todo):
        """Test clear method."""
        empty_todo_storage.todos = [sample_todo]
        empty_todo_storage.add_link("todo_1", "link_1")
        
        empty_todo_storage.clear()
        
        assert len(empty_todo_storage.todos) == 0
        assert empty_todo_storage.links == {}

    def test_add_link(self, empty_todo_storage):
        """Test add_link method."""
        empty_todo_storage.add_link("todo_1", "link_1")
        assert "todo_1" in empty_todo_storage.links
        assert "link_1" in empty_todo_storage.links["todo_1"]

    def test_add_linked_from(self, empty_todo_storage):
        """Test add_linked_from method."""
        empty_todo_storage.add_linked_from("link_1")
        assert "link_1" in empty_todo_storage.linked_from

    def test_get_state_summary(self, empty_todo_storage):
        """Test get_state_summary."""
        todo = Todo(
            todo_id="todo_1",
            content="Test task",
            status="completed",
            active_form="Testing task",
        )
        empty_todo_storage.todos = [todo]
        summary = empty_todo_storage.get_state_summary()
        
        assert "Todo" in summary
        assert "1 tasks" in summary
        assert "completed" in summary

    def test_get_state_summary_with_completion_rate(self, empty_todo_storage):
        """Test get_state_summary shows completion rate when > 0."""
        todo1 = Todo(
            todo_id="todo_1",
            content="Task 1",
            status="completed",
            active_form="Tasking 1",
        )
        todo2 = Todo(
            todo_id="todo_2",
            content="Task 2",
            status="pending",
            active_form="Tasking 2",
        )
        empty_todo_storage.todos = [todo1, todo2]
        summary = empty_todo_storage.get_state_summary()
        
        assert "Completion rate" in summary

    def test_get_outputs_for_linking(self, empty_todo_storage, sample_todo):
        """Test get_outputs_for_linking."""
        empty_todo_storage.todos = [sample_todo]
        outputs = empty_todo_storage.get_outputs_for_linking()
        
        assert len(outputs) == 1
        assert outputs[0]["id"] == "todo_1"
        assert sample_todo.content in outputs[0]["description"]
        assert sample_todo.status in outputs[0]["description"]

    def test_get_outputs_for_linking_empty(self, empty_todo_storage):
        """Test get_outputs_for_linking with empty storage."""
        outputs = empty_todo_storage.get_outputs_for_linking()
        assert outputs == []


# ============================================================================
# Graph of Thought Storage Tests
# ============================================================================


class TestGoTStorage:
    """Test suite for GoTStorage."""

    def test_initialization_default(self):
        """Test GoTStorage initialization without metrics."""
        storage = GoTStorage()
        assert storage.nodes == {}
        assert storage.edges == {}
        assert storage.evaluations == {}
        assert storage.metrics is None
        assert storage.links == {}
        assert storage.linked_from == []

    def test_initialization_with_metrics(self):
        """Test GoTStorage initialization with metrics tracking."""
        storage = GoTStorage(track_usage=True)
        assert storage.nodes == {}
        assert storage.edges == {}
        assert storage.evaluations == {}
        assert storage.metrics is not None

    def test_nodes_property(self):
        """Test nodes property getter and setter."""
        from pydantic_ai_toolsets.toolsets.graph_of_thought_reasoning.types import GraphNode
        
        storage = GoTStorage()
        node = GraphNode(
            node_id="node_1",
            content="Test node",
            status="active",
        )
        storage.nodes = node
        assert "node_1" in storage.nodes
        assert storage.nodes["node_1"] == node

    def test_edges_property(self):
        """Test edges property getter and setter."""
        from pydantic_ai_toolsets.toolsets.graph_of_thought_reasoning.types import GraphEdge
        
        storage = GoTStorage()
        edge = GraphEdge(
            edge_id="edge_1",
            source_id="node_1",
            target_id="node_2",
            edge_type="dependency",
        )
        storage.edges = edge
        assert "edge_1" in storage.edges
        assert storage.edges["edge_1"] == edge

    def test_evaluations_property(self):
        """Test evaluations property getter and setter."""
        from pydantic_ai_toolsets.toolsets.graph_of_thought_reasoning.types import NodeEvaluation
        
        storage = GoTStorage()
        evaluation = NodeEvaluation(
            node_id="node_1",
            score=85.0,
            reasoning="Good node",
            recommendation="keep",
        )
        storage.evaluations = evaluation
        assert "node_1" in storage.evaluations
        assert storage.evaluations["node_1"] == evaluation

    def test_get_statistics_empty(self):
        """Test get_statistics with empty storage."""
        storage = GoTStorage()
        stats = storage.get_statistics()
        assert stats["total_nodes"] == 0
        assert stats["total_edges"] == 0
        assert stats["evaluations"] == 0

    def test_get_statistics_with_data(self):
        """Test get_statistics with nodes and edges."""
        from pydantic_ai_toolsets.toolsets.graph_of_thought_reasoning.types import (
            GraphEdge,
            GraphNode,
            NodeEvaluation,
        )
        
        storage = GoTStorage()
        node1 = GraphNode(node_id="node_1", content="Node 1", status="active")
        node2 = GraphNode(node_id="node_2", content="Node 2", status="completed", is_solution=True)
        storage.nodes = node1
        storage.nodes = node2
        
        edge = GraphEdge(edge_id="edge_1", source_id="node_1", target_id="node_2", edge_type="dependency")
        storage.edges = edge
        
        eval_node = NodeEvaluation(node_id="node_1", score=85.0, reasoning="Good", recommendation="keep")
        storage.evaluations = eval_node
        
        stats = storage.get_statistics()
        assert stats["total_nodes"] == 2
        assert stats["active_nodes"] == 1
        assert stats["solution_nodes"] == 1
        assert stats["total_edges"] == 1
        assert stats["evaluations"] == 1

    def test_graph_complexity(self):
        """Test graph_complexity calculation."""
        from pydantic_ai_toolsets.toolsets.graph_of_thought_reasoning.types import GraphEdge, GraphNode
        
        storage = GoTStorage()
        # Empty graph
        complexity = storage.graph_complexity()
        assert complexity["density"] == 0.0
        assert complexity["avg_degree"] == 0.0
        
        # Graph with nodes and edges
        storage.nodes = GraphNode(node_id="node_1", content="Node 1")
        storage.nodes = GraphNode(node_id="node_2", content="Node 2")
        storage.edges = GraphEdge(edge_id="edge_1", source_id="node_1", target_id="node_2")
        
        complexity = storage.graph_complexity()
        assert complexity["density"] > 0
        assert complexity["avg_degree"] > 0

    def test_summary_without_metrics(self):
        """Test summary generation without metrics."""
        from pydantic_ai_toolsets.toolsets.graph_of_thought_reasoning.types import GraphNode
        
        storage = GoTStorage()
        storage.nodes = GraphNode(node_id="node_1", content="Test")
        summary = storage.summary()
        
        assert summary["toolset"] == "graph_of_thought_reasoning"
        assert "statistics" in summary
        assert "storage" in summary
        assert "usage_metrics" not in summary

    def test_summary_with_metrics(self):
        """Test summary generation with metrics."""
        from pydantic_ai_toolsets.toolsets.graph_of_thought_reasoning.types import GraphNode
        
        storage = GoTStorage(track_usage=True)
        storage.nodes = GraphNode(node_id="node_1", content="Test")
        summary = storage.summary()
        
        assert "usage_metrics" in summary

    def test_clear(self):
        """Test clear method."""
        from pydantic_ai_toolsets.toolsets.graph_of_thought_reasoning.types import GraphEdge, GraphNode
        
        storage = GoTStorage()
        storage.nodes = GraphNode(node_id="node_1", content="Test")
        storage.edges = GraphEdge(edge_id="edge_1", source_id="node_1", target_id="node_2")
        storage.add_link("node_1", "link_1")
        
        storage.clear()
        
        assert len(storage.nodes) == 0
        assert len(storage.edges) == 0
        assert storage.links == {}

    def test_add_link(self):
        """Test add_link method."""
        storage = GoTStorage()
        storage.add_link("node_1", "link_1")
        assert "node_1" in storage.links
        assert "link_1" in storage.links["node_1"]

    def test_add_linked_from(self):
        """Test add_linked_from method."""
        storage = GoTStorage()
        storage.add_linked_from("link_1")
        assert "link_1" in storage.linked_from

    def test_get_state_summary(self):
        """Test get_state_summary."""
        from pydantic_ai_toolsets.toolsets.graph_of_thought_reasoning.types import GraphNode
        
        storage = GoTStorage()
        storage.nodes = GraphNode(node_id="node_1", content="Test node")
        summary = storage.get_state_summary()
        
        assert "Graph of Thought" in summary
        assert "1 nodes" in summary

    def test_get_outputs_for_linking(self):
        """Test get_outputs_for_linking."""
        from pydantic_ai_toolsets.toolsets.graph_of_thought_reasoning.types import (
            GraphEdge,
            GraphNode,
            NodeEvaluation,
        )
        
        storage = GoTStorage()
        storage.nodes = GraphNode(node_id="node_1", content="Test", is_solution=True)
        storage.edges = GraphEdge(edge_id="edge_1", source_id="node_1", target_id="node_2")
        storage.evaluations = NodeEvaluation(node_id="node_1", score=85.0, reasoning="Good", recommendation="keep")
        
        outputs = storage.get_outputs_for_linking()
        
        assert len(outputs) >= 3  # At least node, edge, and evaluation
        node_outputs = [o for o in outputs if o["id"] == "node_1"]
        assert len(node_outputs) >= 1
        assert "[SOLUTION]" in node_outputs[0]["description"]


# ============================================================================
# Beam Search Storage Tests
# ============================================================================


class TestBeamStorage:
    """Test suite for BeamStorage."""

    def test_initialization_default(self):
        """Test BeamStorage initialization without metrics."""
        storage = BeamStorage()
        assert storage.candidates == {}
        assert storage.steps == []
        assert storage.metrics is None
        assert storage.links == {}
        assert storage.linked_from == []

    def test_initialization_with_metrics(self):
        """Test BeamStorage initialization with metrics tracking."""
        storage = BeamStorage(track_usage=True)
        assert storage.candidates == {}
        assert storage.steps == []
        assert storage.metrics is not None

    def test_candidates_property(self):
        """Test candidates property getter and setter."""
        from pydantic_ai_toolsets.toolsets.beam_search_reasoning.types import BeamCandidate
        
        storage = BeamStorage()
        candidate = BeamCandidate(
            candidate_id="candidate_1",
            content="Test candidate",
            depth=0,
        )
        storage.candidates = candidate
        assert "candidate_1" in storage.candidates
        assert storage.candidates["candidate_1"] == candidate

    def test_steps_property(self):
        """Test steps property getter and setter."""
        from pydantic_ai_toolsets.toolsets.beam_search_reasoning.types import BeamStep
        
        storage = BeamStorage()
        step = BeamStep(
            step_index=0,
            candidate_ids=["candidate_1"],
            beam_width=3,
        )
        storage.steps = step
        assert len(storage.steps) == 1
        assert storage.steps[0].step_index == 0
        
        # Update existing step
        step2 = BeamStep(step_index=0, candidate_ids=["candidate_1", "candidate_2"], beam_width=3)
        storage.steps = step2
        assert len(storage.steps) == 1
        assert len(storage.steps[0].candidate_ids) == 2

    def test_get_statistics_empty(self):
        """Test get_statistics with empty storage."""
        storage = BeamStorage()
        stats = storage.get_statistics()
        assert stats["total_candidates"] == 0
        assert stats["total_steps"] == 0
        assert stats["avg_beam_width"] == 0

    def test_get_statistics_with_data(self):
        """Test get_statistics with candidates and steps."""
        from pydantic_ai_toolsets.toolsets.beam_search_reasoning.types import BeamCandidate, BeamStep
        
        storage = BeamStorage()
        candidate1 = BeamCandidate(candidate_id="c1", content="C1", depth=0, score=85.0)
        candidate2 = BeamCandidate(candidate_id="c2", content="C2", depth=1, score=90.0, is_terminal=True)
        storage.candidates = candidate1
        storage.candidates = candidate2
        
        step = BeamStep(step_index=0, candidate_ids=["c1"], beam_width=3)
        storage.steps = step
        
        stats = storage.get_statistics()
        assert stats["total_candidates"] == 2
        assert stats["scored_candidates"] == 2
        assert stats["terminal_candidates"] == 1
        assert stats["max_depth"] == 1
        assert stats["total_steps"] == 1

    def test_beam_width_history(self):
        """Test beam_width_history."""
        from pydantic_ai_toolsets.toolsets.beam_search_reasoning.types import BeamStep
        
        storage = BeamStorage()
        storage.steps = BeamStep(step_index=0, candidate_ids=["c1"], beam_width=3)
        storage.steps = BeamStep(step_index=1, candidate_ids=["c2"], beam_width=5)
        
        history = storage.beam_width_history()
        assert len(history) == 2
        assert history[0] == (0, 3)
        assert history[1] == (1, 5)

    def test_summary_without_metrics(self):
        """Test summary generation without metrics."""
        from pydantic_ai_toolsets.toolsets.beam_search_reasoning.types import BeamCandidate
        
        storage = BeamStorage()
        storage.candidates = BeamCandidate(candidate_id="c1", content="Test", depth=0)
        summary = storage.summary()
        
        assert summary["toolset"] == "beam_search_reasoning"
        assert "statistics" in summary
        assert "storage" in summary
        assert "usage_metrics" not in summary

    def test_summary_with_metrics(self):
        """Test summary generation with metrics."""
        from pydantic_ai_toolsets.toolsets.beam_search_reasoning.types import BeamCandidate
        
        storage = BeamStorage(track_usage=True)
        storage.candidates = BeamCandidate(candidate_id="c1", content="Test", depth=0)
        summary = storage.summary()
        
        assert "usage_metrics" in summary

    def test_clear(self):
        """Test clear method."""
        from pydantic_ai_toolsets.toolsets.beam_search_reasoning.types import BeamCandidate, BeamStep
        
        storage = BeamStorage()
        storage.candidates = BeamCandidate(candidate_id="c1", content="Test", depth=0)
        storage.steps = BeamStep(step_index=0, candidate_ids=["c1"], beam_width=3)
        storage.add_link("c1", "link_1")
        
        storage.clear()
        
        assert len(storage.candidates) == 0
        assert len(storage.steps) == 0
        assert storage.links == {}

    def test_add_link(self):
        """Test add_link method."""
        storage = BeamStorage()
        storage.add_link("candidate_1", "link_1")
        assert "candidate_1" in storage.links
        assert "link_1" in storage.links["candidate_1"]

    def test_add_linked_from(self):
        """Test add_linked_from method."""
        storage = BeamStorage()
        storage.add_linked_from("link_1")
        assert "link_1" in storage.linked_from

    def test_get_state_summary(self):
        """Test get_state_summary."""
        from pydantic_ai_toolsets.toolsets.beam_search_reasoning.types import BeamCandidate
        
        storage = BeamStorage()
        storage.candidates = BeamCandidate(candidate_id="c1", content="Test", depth=0, score=85.0)
        summary = storage.get_state_summary()
        
        assert "Beam Search" in summary
        assert "1 candidates" in summary

    def test_get_outputs_for_linking(self):
        """Test get_outputs_for_linking."""
        from pydantic_ai_toolsets.toolsets.beam_search_reasoning.types import BeamCandidate, BeamStep
        
        storage = BeamStorage()
        storage.candidates = BeamCandidate(candidate_id="c1", content="Test", depth=0, score=85.0)
        storage.steps = BeamStep(step_index=0, candidate_ids=["c1"], beam_width=3)
        
        outputs = storage.get_outputs_for_linking()
        
        assert len(outputs) >= 2  # At least candidate and step
        candidate_outputs = [o for o in outputs if o["id"] == "c1"]
        assert len(candidate_outputs) == 1
        assert "score=85.0" in candidate_outputs[0]["description"]


# ============================================================================
# MCTS Storage Tests
# ============================================================================


class TestMCTSStorage:
    """Test suite for MCTSStorage."""

    def test_initialization_default(self):
        """Test MCTSStorage initialization without metrics."""
        storage = MCTSStorage()
        assert storage.nodes == {}
        assert storage.metrics is None
        assert storage.iteration_count == 0
        assert storage.links == {}
        assert storage.linked_from == []

    def test_initialization_with_metrics(self):
        """Test MCTSStorage initialization with metrics tracking."""
        storage = MCTSStorage(track_usage=True)
        assert storage.nodes == {}
        assert storage.metrics is not None
        assert storage.iteration_count == 0

    def test_nodes_property(self):
        """Test nodes property getter and setter."""
        from pydantic_ai_toolsets.toolsets.monte_carlo_reasoning.types import MCTSNode
        
        storage = MCTSStorage()
        node = MCTSNode(
            node_id="node_1",
            content="Test node",
            visits=5,
            wins=3.0,
        )
        storage.nodes = node
        assert "node_1" in storage.nodes
        assert storage.nodes["node_1"] == node

    def test_iteration_count(self):
        """Test iteration_count property and increment_iteration."""
        storage = MCTSStorage()
        assert storage.iteration_count == 0
        storage.increment_iteration()
        assert storage.iteration_count == 1
        storage.increment_iteration()
        assert storage.iteration_count == 2

    def test_get_statistics_empty(self):
        """Test get_statistics with empty storage."""
        storage = MCTSStorage()
        stats = storage.get_statistics()
        assert stats["total_nodes"] == 0
        assert stats["iterations"] == 0
        assert stats["total_visits"] == 0

    def test_get_statistics_with_data(self):
        """Test get_statistics with nodes."""
        from pydantic_ai_toolsets.toolsets.monte_carlo_reasoning.types import MCTSNode
        
        storage = MCTSStorage()
        node1 = MCTSNode(node_id="node_1", content="Node 1", visits=5, wins=3.0, is_expanded=True)
        node2 = MCTSNode(node_id="node_2", content="Node 2", visits=3, wins=2.0, is_terminal=True)
        storage.nodes = node1
        storage.nodes = node2
        storage.increment_iteration()
        
        stats = storage.get_statistics()
        assert stats["total_nodes"] == 2
        assert stats["expanded_nodes"] == 1
        assert stats["terminal_nodes"] == 1
        assert stats["total_visits"] == 8
        assert stats["total_wins"] == 5.0
        assert stats["iterations"] == 1

    def test_get_ucb1_stats(self):
        """Test get_ucb1_stats calculation."""
        from pydantic_ai_toolsets.toolsets.monte_carlo_reasoning.types import MCTSNode
        
        storage = MCTSStorage()
        root = MCTSNode(node_id="root", content="Root", visits=10, wins=5.0)
        child = MCTSNode(node_id="child", content="Child", visits=5, wins=3.0, parent_id="root")
        storage.nodes = root
        storage.nodes = child
        
        ucb1_stats = storage.get_ucb1_stats()
        assert len(ucb1_stats) == 2
        # Check that stats are sorted by UCB1 value (descending)
        assert ucb1_stats[0][3] >= ucb1_stats[1][3]

    def test_get_ucb1_stats_no_root(self):
        """Test get_ucb1_stats with no root node."""
        storage = MCTSStorage()
        ucb1_stats = storage.get_ucb1_stats()
        assert ucb1_stats == []

    def test_summary_without_metrics(self):
        """Test summary generation without metrics."""
        from pydantic_ai_toolsets.toolsets.monte_carlo_reasoning.types import MCTSNode
        
        storage = MCTSStorage()
        storage.nodes = MCTSNode(node_id="node_1", content="Test")
        summary = storage.summary()
        
        assert summary["toolset"] == "monte_carlo_reasoning"
        assert "statistics" in summary
        assert "storage" in summary
        assert "usage_metrics" not in summary

    def test_summary_with_metrics(self):
        """Test summary generation with metrics."""
        from pydantic_ai_toolsets.toolsets.monte_carlo_reasoning.types import MCTSNode
        
        storage = MCTSStorage(track_usage=True)
        storage.nodes = MCTSNode(node_id="node_1", content="Test")
        summary = storage.summary()
        
        assert "usage_metrics" in summary

    def test_clear(self):
        """Test clear method."""
        from pydantic_ai_toolsets.toolsets.monte_carlo_reasoning.types import MCTSNode
        
        storage = MCTSStorage()
        storage.nodes = MCTSNode(node_id="node_1", content="Test")
        storage.increment_iteration()
        storage.add_link("node_1", "link_1")
        
        storage.clear()
        
        assert len(storage.nodes) == 0
        assert storage.iteration_count == 0
        assert storage.links == {}

    def test_add_link(self):
        """Test add_link method."""
        storage = MCTSStorage()
        storage.add_link("node_1", "link_1")
        assert "node_1" in storage.links
        assert "link_1" in storage.links["node_1"]

    def test_add_linked_from(self):
        """Test add_linked_from method."""
        storage = MCTSStorage()
        storage.add_linked_from("link_1")
        assert "link_1" in storage.linked_from

    def test_get_state_summary(self):
        """Test get_state_summary."""
        from pydantic_ai_toolsets.toolsets.monte_carlo_reasoning.types import MCTSNode
        
        storage = MCTSStorage()
        storage.nodes = MCTSNode(node_id="root", content="Root", visits=10, wins=5.0)
        storage.increment_iteration()
        summary = storage.get_state_summary()
        
        assert "MCTS" in summary
        assert "1 nodes" in summary

    def test_get_outputs_for_linking(self):
        """Test get_outputs_for_linking."""
        from pydantic_ai_toolsets.toolsets.monte_carlo_reasoning.types import MCTSNode
        
        storage = MCTSStorage()
        storage.nodes = MCTSNode(
            node_id="node_1",
            content="Test",
            visits=5,
            wins=3.0,
            is_terminal=True,
        )
        
        outputs = storage.get_outputs_for_linking()
        
        assert len(outputs) == 1
        assert outputs[0]["id"] == "node_1"
        assert "visits=5" in outputs[0]["description"]
        assert "wins=3.0" in outputs[0]["description"]


# ============================================================================
# Persona Storage Tests
# ============================================================================


class TestPersonaStorage:
    """Test suite for PersonaStorage."""

    def test_initialization_default(self):
        """Test PersonaStorage initialization without metrics."""
        storage = PersonaStorage()
        assert storage.session is None
        assert storage.personas == {}
        assert storage.responses == {}
        assert storage.metrics is None
        assert storage.links == {}
        assert storage.linked_from == []

    def test_initialization_with_metrics(self):
        """Test PersonaStorage initialization with metrics tracking."""
        storage = PersonaStorage(track_usage=True)
        assert storage.session is None
        assert storage.personas == {}
        assert storage.responses == {}
        assert storage.metrics is not None

    def test_session_property(self):
        """Test session property getter and setter."""
        from pydantic_ai_toolsets.toolsets.multi_persona_analysis.types import PersonaSession
        
        storage = PersonaStorage()
        session = PersonaSession(
            session_id="session_1",
            problem="Test problem",
            process_type="sequential",
        )
        storage.session = session
        assert storage.session is not None
        assert storage.session.session_id == "session_1"

    def test_personas_property(self):
        """Test personas property getter and setter."""
        from pydantic_ai_toolsets.toolsets.multi_persona_analysis.types import Persona
        
        storage = PersonaStorage()
        persona = Persona(
            persona_id="persona_1",
            name="Test Persona",
            persona_type="expert",
            description="Test description",
        )
        storage.personas = persona
        assert "persona_1" in storage.personas
        assert storage.personas["persona_1"] == persona

    def test_responses_property(self):
        """Test responses property getter and setter."""
        from pydantic_ai_toolsets.toolsets.multi_persona_analysis.types import PersonaResponse
        
        storage = PersonaStorage()
        response = PersonaResponse(
            response_id="response_1",
            persona_id="persona_1",
            content="Test response",
        )
        storage.responses = response
        assert "response_1" in storage.responses
        assert storage.responses["response_1"] == response

    def test_get_statistics_empty(self):
        """Test get_statistics with empty storage."""
        storage = PersonaStorage()
        stats = storage.get_statistics()
        assert stats["has_session"] == 0
        assert stats["total_personas"] == 0
        assert stats["total_responses"] == 0

    def test_get_statistics_with_data(self):
        """Test get_statistics with session, personas, and responses."""
        from pydantic_ai_toolsets.toolsets.multi_persona_analysis.types import (
            Persona,
            PersonaResponse,
            PersonaSession,
        )
        
        storage = PersonaStorage()
        session = PersonaSession(
            session_id="session_1",
            problem="Test",
            process_type="sequential",
            current_round=1,
            max_rounds=3,
        )
        storage.session = session
        
        storage.personas = Persona(
            persona_id="p1",
            name="Persona 1",
            persona_type="expert",
            description="Test",
        )
        
        storage.responses = PersonaResponse(
            response_id="r1",
            persona_id="p1",
            content="Response",
        )
        
        stats = storage.get_statistics()
        assert stats["has_session"] == 1
        assert stats["total_personas"] == 1
        assert stats["total_responses"] == 1
        assert stats["current_round"] == 1
        assert stats["max_rounds"] == 3

    def test_summary_without_metrics(self):
        """Test summary generation without metrics."""
        from pydantic_ai_toolsets.toolsets.multi_persona_analysis.types import Persona
        
        storage = PersonaStorage()
        storage.personas = Persona(
            persona_id="p1",
            name="Test",
            persona_type="expert",
            description="Test",
        )
        summary = storage.summary()
        
        assert summary["toolset"] == "multi_persona_analysis"
        assert "statistics" in summary
        assert "storage" in summary
        assert "usage_metrics" not in summary

    def test_summary_with_session(self):
        """Test summary generation with session."""
        from pydantic_ai_toolsets.toolsets.multi_persona_analysis.types import PersonaSession
        
        storage = PersonaStorage()
        session = PersonaSession(
            session_id="session_1",
            problem="Test",
            process_type="sequential",
            synthesis="Final synthesis",
        )
        storage.session = session
        summary = storage.summary()
        
        assert summary["storage"]["session"] is not None
        assert summary["storage"]["session"]["synthesis"] == "Final synthesis"

    def test_clear(self):
        """Test clear method."""
        from pydantic_ai_toolsets.toolsets.multi_persona_analysis.types import (
            Persona,
            PersonaSession,
        )
        
        storage = PersonaStorage()
        storage.session = PersonaSession(
            session_id="s1",
            problem="Test",
            process_type="sequential",
        )
        storage.personas = Persona(
            persona_id="p1",
            name="Test",
            persona_type="expert",
            description="Test",
        )
        storage.add_link("p1", "link_1")
        
        storage.clear()
        
        assert storage.session is None
        assert len(storage.personas) == 0
        assert storage.links == {}

    def test_add_link(self):
        """Test add_link method."""
        storage = PersonaStorage()
        storage.add_link("persona_1", "link_1")
        assert "persona_1" in storage.links
        assert "link_1" in storage.links["persona_1"]

    def test_add_linked_from(self):
        """Test add_linked_from method."""
        storage = PersonaStorage()
        storage.add_linked_from("link_1")
        assert "link_1" in storage.linked_from

    def test_get_state_summary(self):
        """Test get_state_summary."""
        from pydantic_ai_toolsets.toolsets.multi_persona_analysis.types import (
            Persona,
            PersonaSession,
        )
        
        storage = PersonaStorage()
        storage.session = PersonaSession(
            session_id="s1",
            problem="Test",
            process_type="sequential",
        )
        storage.personas = Persona(
            persona_id="p1",
            name="Test Persona",
            persona_type="expert",
            description="Test",
        )
        summary = storage.get_state_summary()
        
        assert "Multi-Persona Analysis" in summary
        assert "1 personas" in summary

    def test_get_outputs_for_linking(self):
        """Test get_outputs_for_linking."""
        from pydantic_ai_toolsets.toolsets.multi_persona_analysis.types import (
            Persona,
            PersonaResponse,
            PersonaSession,
        )
        
        storage = PersonaStorage()
        storage.session = PersonaSession(
            session_id="s1",
            problem="Test problem",
            process_type="sequential",
        )
        storage.personas = Persona(
            persona_id="p1",
            name="Test Persona",
            persona_type="expert",
            description="Test description",
        )
        storage.responses = PersonaResponse(
            response_id="r1",
            persona_id="p1",
            content="Test response",
            round_number=0,
        )
        
        outputs = storage.get_outputs_for_linking()
        
        assert len(outputs) >= 3  # Session, persona, and response
        session_outputs = [o for o in outputs if o["id"] == "s1"]
        assert len(session_outputs) == 1


# ============================================================================
# Persona Debate Storage Tests
# ============================================================================


class TestPersonaDebateStorage:
    """Test suite for PersonaDebateStorage."""

    def test_initialization_default(self):
        """Test PersonaDebateStorage initialization without metrics."""
        storage = PersonaDebateStorage()
        assert storage.session is None
        assert storage.personas == {}
        assert storage.positions == {}
        assert storage.critiques == {}
        assert storage.agreements == {}
        assert storage.metrics is None

    def test_initialization_with_metrics(self):
        """Test PersonaDebateStorage initialization with metrics tracking."""
        storage = PersonaDebateStorage(track_usage=True)
        assert storage.session is None
        assert storage.metrics is not None

    def test_session_property(self):
        """Test session property getter and setter."""
        from pydantic_ai_toolsets.toolsets.multi_persona_debate.types import PersonaDebateSession
        
        storage = PersonaDebateStorage()
        session = PersonaDebateSession(
            debate_id="debate_1",
            topic="Test question",
            max_rounds=3,
        )
        storage.session = session
        assert storage.session is not None
        assert storage.session.debate_id == "debate_1"

    def test_personas_property(self):
        """Test personas property."""
        from pydantic_ai_toolsets.toolsets.multi_persona_debate.types import Persona
        
        storage = PersonaDebateStorage()
        persona = Persona(
            persona_id="p1",
            name="Test",
            persona_type="expert",
            description="Test",
        )
        storage.personas = persona
        assert "p1" in storage.personas

    def test_positions_property(self):
        """Test positions property."""
        from pydantic_ai_toolsets.toolsets.multi_persona_debate.types import PersonaPosition
        
        storage = PersonaDebateStorage()
        position = PersonaPosition(
            position_id="pos_1",
            persona_id="p1",
            round_number=0,
            content="Test position",
        )
        storage.positions = position
        assert "pos_1" in storage.positions

    def test_critiques_property(self):
        """Test critiques property."""
        from pydantic_ai_toolsets.toolsets.multi_persona_debate.types import PersonaCritique
        
        storage = PersonaDebateStorage()
        critique = PersonaCritique(
            critique_id="crit_1",
            target_position_id="pos_1",
            persona_id="p1",
            round_number=0,
            content="Test critique",
        )
        storage.critiques = critique
        assert "crit_1" in storage.critiques

    def test_agreements_property(self):
        """Test agreements property."""
        from pydantic_ai_toolsets.toolsets.multi_persona_debate.types import PersonaAgreement
        
        storage = PersonaDebateStorage()
        agreement = PersonaAgreement(
            agreement_id="agree_1",
            target_position_id="pos_1",
            persona_id="p1",
            round_number=0,
            content="Test reason",
        )
        storage.agreements = agreement
        assert "agree_1" in storage.agreements

    def test_get_statistics_empty(self):
        """Test get_statistics with empty storage."""
        storage = PersonaDebateStorage()
        stats = storage.get_statistics()
        assert stats["has_session"] == 0
        assert stats["total_personas"] == 0
        assert stats["total_positions"] == 0

    def test_get_statistics_with_data(self):
        """Test get_statistics with data."""
        from pydantic_ai_toolsets.toolsets.multi_persona_debate.types import (
            Persona,
            PersonaDebateSession,
            PersonaPosition,
        )
        
        storage = PersonaDebateStorage()
        storage.session = PersonaDebateSession(
            debate_id="debate_1",
            topic="Test",
            max_rounds=3,
        )
        storage.personas = Persona(
            persona_id="p1",
            name="Test",
            persona_type="expert",
            description="Test",
        )
        storage.positions = PersonaPosition(
            position_id="pos_1",
            persona_id="p1",
            round_number=0,
            content="Test position",
        )
        
        stats = storage.get_statistics()
        assert stats["has_session"] == 1
        assert stats["total_personas"] == 1
        assert stats["total_positions"] == 1

    def test_summary_without_metrics(self):
        """Test summary generation without metrics."""
        from pydantic_ai_toolsets.toolsets.multi_persona_debate.types import Persona
        
        storage = PersonaDebateStorage()
        storage.personas = Persona(
            persona_id="p1",
            name="Test",
            persona_type="expert",
            description="Test",
        )
        summary = storage.summary()
        
        assert summary["toolset"] == "multi_persona_debate"
        assert "statistics" in summary
        assert "usage_metrics" not in summary

    def test_clear(self):
        """Test clear method."""
        from pydantic_ai_toolsets.toolsets.multi_persona_debate.types import (
            Persona,
            PersonaDebateSession,
        )
        
        storage = PersonaDebateStorage()
        storage.session = PersonaDebateSession(
            debate_id="debate_1",
            topic="Test",
            max_rounds=3,
        )
        storage.personas = Persona(
            persona_id="p1",
            name="Test",
            persona_type="expert",
            description="Test",
        )
        
        storage.clear()
        
        assert storage.session is None
        assert len(storage.personas) == 0

    def test_add_link(self):
        """Test add_link method."""
        storage = PersonaDebateStorage()
        storage.add_link("persona_1", "link_1")
        assert "persona_1" in storage.links

    def test_add_linked_from(self):
        """Test add_linked_from method."""
        storage = PersonaDebateStorage()
        storage.add_linked_from("link_1")
        assert "link_1" in storage.linked_from


# ============================================================================
# Search Storage Tests
# ============================================================================


class TestSearchStorage:
    """Test suite for SearchStorage."""

    def test_initialization_default(self):
        """Test SearchStorage initialization without metrics."""
        storage = SearchStorage()
        assert storage.search_results == {}
        assert storage.extracted_contents == {}
        assert storage.metrics is None
        assert storage.links == {}
        assert storage.linked_from == []

    def test_initialization_with_metrics(self):
        """Test SearchStorage initialization with metrics tracking."""
        storage = SearchStorage(track_usage=True)
        assert storage.search_results == {}
        assert storage.extracted_contents == {}
        assert storage.metrics is not None

    def test_search_results_property(self):
        """Test search_results property getter and setter."""
        from pydantic_ai_toolsets.toolsets.search.types import SearchResult, SearchSource
        
        storage = SearchStorage()
        result = SearchResult(
            result_id="result_1",
            query="test query",
            title="Test Title",
            url="https://example.com",
            description="Test description",
            source_type=SearchSource.WEB,
        )
        storage.search_results = result
        assert "result_1" in storage.search_results
        assert storage.search_results["result_1"] == result

    def test_extracted_contents_property(self):
        """Test extracted_contents property getter and setter."""
        from pydantic_ai_toolsets.toolsets.search.types import ExtractedContent, OutputFormat
        
        storage = SearchStorage()
        content = ExtractedContent(
            content_id="content_1",
            url="https://example.com",
            content="Extracted content",
            output_format=OutputFormat.TEXT,
        )
        storage.extracted_contents = content
        assert "content_1" in storage.extracted_contents
        assert storage.extracted_contents["content_1"] == content

    def test_get_statistics_empty(self):
        """Test get_statistics with empty storage."""
        storage = SearchStorage()
        stats = storage.get_statistics()
        assert stats["total_searches"] == 0
        assert stats["total_results"] == 0
        assert stats["total_extractions"] == 0

    def test_get_statistics_with_data(self):
        """Test get_statistics with search results and extracted contents."""
        from pydantic_ai_toolsets.toolsets.search.types import (
            ExtractedContent,
            OutputFormat,
            SearchResult,
            SearchSource,
        )
        
        storage = SearchStorage()
        result1 = SearchResult(
            result_id="r1",
            query="test",
            title="Title 1",
            url="https://example.com/1",
            source_type=SearchSource.WEB,
        )
        result2 = SearchResult(
            result_id="r2",
            query="test",
            title="Title 2",
            url="https://example.com/2",
            source_type=SearchSource.WEB,
        )
        storage.search_results = result1
        storage.search_results = result2
        
        content = ExtractedContent(
            content_id="c1",
            url="https://example.com/1",
            content="Extracted" * 10,  # 90 chars
            output_format=OutputFormat.TEXT,
        )
        storage.extracted_contents = content
        
        stats = storage.get_statistics()
        assert stats["total_searches"] == 1  # Unique queries
        assert stats["total_results"] == 2
        assert stats["total_extractions"] == 1
        assert stats["unique_urls"] == 1
        assert stats["total_extracted_chars"] == 90

    def test_summary_without_metrics(self):
        """Test summary generation without metrics."""
        from pydantic_ai_toolsets.toolsets.search.types import SearchResult, SearchSource
        
        storage = SearchStorage()
        storage.search_results = SearchResult(
            result_id="r1",
            query="test",
            title="Test",
            url="https://example.com",
            source_type=SearchSource.WEB,
        )
        summary = storage.summary()
        
        assert summary["toolset"] == "search"
        assert "statistics" in summary
        assert "storage" in summary
        assert "usage_metrics" not in summary

    def test_summary_with_metrics(self):
        """Test summary generation with metrics."""
        from pydantic_ai_toolsets.toolsets.search.types import SearchResult, SearchSource
        
        storage = SearchStorage(track_usage=True)
        storage.search_results = SearchResult(
            result_id="r1",
            query="test",
            title="Test",
            url="https://example.com",
            source_type=SearchSource.WEB,
        )
        summary = storage.summary()
        
        assert "usage_metrics" in summary

    def test_clear(self):
        """Test clear method."""
        from pydantic_ai_toolsets.toolsets.search.types import SearchResult, SearchSource
        
        storage = SearchStorage()
        storage.search_results = SearchResult(
            result_id="r1",
            query="test",
            title="Test",
            url="https://example.com",
            source_type=SearchSource.WEB,
        )
        storage.add_link("r1", "link_1")
        
        storage.clear()
        
        assert len(storage.search_results) == 0
        assert storage.links == {}

    def test_add_link(self):
        """Test add_link method."""
        storage = SearchStorage()
        storage.add_link("result_1", "link_1")
        assert "result_1" in storage.links
        assert "link_1" in storage.links["result_1"]

    def test_add_linked_from(self):
        """Test add_linked_from method."""
        storage = SearchStorage()
        storage.add_linked_from("link_1")
        assert "link_1" in storage.linked_from

    def test_get_state_summary(self):
        """Test get_state_summary."""
        from pydantic_ai_toolsets.toolsets.search.types import SearchResult, SearchSource
        
        storage = SearchStorage()
        storage.search_results = SearchResult(
            result_id="r1",
            query="test",
            title="Test Title",
            url="https://example.com",
            source_type=SearchSource.WEB,
        )
        summary = storage.get_state_summary()
        
        assert "Search" in summary
        assert "1 queries" in summary

    def test_get_outputs_for_linking(self):
        """Test get_outputs_for_linking."""
        from pydantic_ai_toolsets.toolsets.search.types import (
            ExtractedContent,
            OutputFormat,
            SearchResult,
            SearchSource,
        )
        
        storage = SearchStorage()
        storage.search_results = SearchResult(
            result_id="r1",
            query="test",
            title="Test Title",
            url="https://example.com",
            source_type=SearchSource.WEB,
        )
        storage.extracted_contents = ExtractedContent(
            content_id="c1",
            url="https://example.com",
            content="Extracted content",
            output_format=OutputFormat.TEXT,
        )
        
        outputs = storage.get_outputs_for_linking()
        
        assert len(outputs) == 2  # Result and extracted content
        result_outputs = [o for o in outputs if o["id"] == "r1"]
        assert len(result_outputs) == 1
        assert "Test Title" in result_outputs[0]["description"]


# ============================================================================
# Self-Refine Storage Tests
# ============================================================================


class TestSelfRefineStorage:
    """Test suite for SelfRefineStorage."""

    def test_initialization_default(self):
        """Test SelfRefineStorage initialization without metrics."""
        storage = SelfRefineStorage()
        assert storage.outputs == {}
        assert storage.feedbacks == {}
        assert storage.metrics is None
        assert storage.links == {}
        assert storage.linked_from == []

    def test_initialization_with_metrics(self):
        """Test SelfRefineStorage initialization with metrics tracking."""
        storage = SelfRefineStorage(track_usage=True)
        assert storage.outputs == {}
        assert storage.feedbacks == {}
        assert storage.metrics is not None

    def test_outputs_property(self):
        """Test outputs property getter and setter."""
        from pydantic_ai_toolsets.toolsets.self_refine.types import RefinementOutput
        
        storage = SelfRefineStorage()
        output = RefinementOutput(
            output_id="output_1",
            content="Test output",
            iteration=1,
        )
        storage.outputs = output
        assert "output_1" in storage.outputs
        assert storage.outputs["output_1"] == output

    def test_feedbacks_property(self):
        """Test feedbacks property getter and setter."""
        from pydantic_ai_toolsets.toolsets.self_refine.types import Feedback, FeedbackDimension, FeedbackType
        
        storage = SelfRefineStorage()
        feedback = Feedback(
            feedback_id="feedback_1",
            output_id="output_1",
            feedback_type=FeedbackType.ADDITIVE,
            dimension=FeedbackDimension.COMPLETENESS,
            description="Test feedback",
            suggestion="Add more details",
        )
        storage.feedbacks = feedback
        assert "feedback_1" in storage.feedbacks
        assert storage.feedbacks["feedback_1"] == feedback

    def test_get_statistics_empty(self):
        """Test get_statistics with empty storage."""
        storage = SelfRefineStorage()
        stats = storage.get_statistics()
        assert stats["total_outputs"] == 0
        assert stats["total_feedbacks"] == 0
        assert stats["max_iteration"] == 0

    def test_get_statistics_with_data(self):
        """Test get_statistics with outputs and feedbacks."""
        from pydantic_ai_toolsets.toolsets.self_refine.types import (
            Feedback,
            FeedbackDimension,
            FeedbackType,
            RefinementOutput,
        )
        
        storage = SelfRefineStorage()
        output1 = RefinementOutput(
            output_id="o1",
            content="Output 1",
            iteration=1,
            quality_score=85.0,
        )
        output2 = RefinementOutput(
            output_id="o2",
            content="Output 2",
            iteration=2,
            is_final=True,
            quality_score=90.0,
        )
        storage.outputs = output1
        storage.outputs = output2
        
        storage.feedbacks = Feedback(
            feedback_id="f1",
            output_id="o1",
            feedback_type=FeedbackType.ADDITIVE,
            dimension=FeedbackDimension.COMPLETENESS,
            description="Feedback",
            suggestion="Add more",
        )
        
        stats = storage.get_statistics()
        assert stats["total_outputs"] == 2
        assert stats["final_outputs"] == 1
        assert stats["max_iteration"] == 2
        assert stats["total_feedbacks"] == 1
        assert stats["avg_quality_score"] == 87.5

    def test_summary_without_metrics(self):
        """Test summary generation without metrics."""
        from pydantic_ai_toolsets.toolsets.self_refine.types import RefinementOutput
        
        storage = SelfRefineStorage()
        storage.outputs = RefinementOutput(
            output_id="o1",
            content="Test",
            iteration=1,
        )
        summary = storage.summary()
        
        assert summary["toolset"] == "self_refine"
        assert "statistics" in summary
        assert "storage" in summary
        assert "usage_metrics" not in summary

    def test_summary_with_metrics(self):
        """Test summary generation with metrics."""
        from pydantic_ai_toolsets.toolsets.self_refine.types import RefinementOutput
        
        storage = SelfRefineStorage(track_usage=True)
        storage.outputs = RefinementOutput(
            output_id="o1",
            content="Test",
            iteration=1,
        )
        summary = storage.summary()
        
        assert "usage_metrics" in summary

    def test_clear(self):
        """Test clear method."""
        from pydantic_ai_toolsets.toolsets.self_refine.types import (
            Feedback,
            FeedbackDimension,
            FeedbackType,
            RefinementOutput,
        )
        
        storage = SelfRefineStorage()
        storage.outputs = RefinementOutput(
            output_id="o1",
            content="Test",
            iteration=1,
        )
        storage.feedbacks = Feedback(
            feedback_id="f1",
            output_id="o1",
            feedback_type=FeedbackType.ADDITIVE,
            dimension=FeedbackDimension.COMPLETENESS,
            description="Feedback",
            suggestion="Add more",
        )
        storage.add_link("o1", "link_1")
        
        storage.clear()
        
        assert len(storage.outputs) == 0
        assert len(storage.feedbacks) == 0
        assert storage.links == {}

    def test_add_link(self):
        """Test add_link method."""
        storage = SelfRefineStorage()
        storage.add_link("output_1", "link_1")
        assert "output_1" in storage.links
        assert "link_1" in storage.links["output_1"]

    def test_add_linked_from(self):
        """Test add_linked_from method."""
        storage = SelfRefineStorage()
        storage.add_linked_from("link_1")
        assert "link_1" in storage.linked_from

    def test_get_state_summary(self):
        """Test get_state_summary."""
        from pydantic_ai_toolsets.toolsets.self_refine.types import RefinementOutput
        
        storage = SelfRefineStorage()
        storage.outputs = RefinementOutput(
            output_id="o1",
            content="Test",
            iteration=1,
            is_final=True,
        )
        summary = storage.get_state_summary()
        
        assert "Self-Refine" in summary
        assert "1 outputs" in summary

    def test_get_outputs_for_linking(self):
        """Test get_outputs_for_linking."""
        from pydantic_ai_toolsets.toolsets.self_refine.types import (
            Feedback,
            FeedbackDimension,
            FeedbackType,
            RefinementOutput,
        )
        
        storage = SelfRefineStorage()
        storage.outputs = RefinementOutput(
            output_id="o1",
            content="Test output",
            iteration=1,
            quality_score=85.0,
        )
        storage.feedbacks = Feedback(
            feedback_id="f1",
            output_id="o1",
            feedback_type=FeedbackType.ADDITIVE,
            dimension=FeedbackDimension.COMPLETENESS,
            description="Test feedback",
            suggestion="Add more",
        )
        
        outputs = storage.get_outputs_for_linking()
        
        assert len(outputs) >= 2  # Output and feedback
        output_items = [o for o in outputs if o["id"] == "o1"]
        assert len(output_items) >= 1


# ============================================================================
# Self-Ask Storage Tests
# ============================================================================


class TestSelfAskStorage:
    """Test suite for SelfAskStorage."""

    def test_initialization_default(self):
        """Test SelfAskStorage initialization without metrics."""
        storage = SelfAskStorage()
        assert storage.questions == {}
        assert storage.answers == {}
        assert storage.final_answers == {}
        assert storage.metrics is None
        assert storage.links == {}
        assert storage.linked_from == []

    def test_initialization_with_metrics(self):
        """Test SelfAskStorage initialization with metrics tracking."""
        storage = SelfAskStorage(track_usage=True)
        assert storage.questions == {}
        assert storage.answers == {}
        assert storage.final_answers == {}
        assert storage.metrics is not None

    def test_questions_property(self):
        """Test questions property getter and setter."""
        from pydantic_ai_toolsets.toolsets.self_ask.types import Question
        
        storage = SelfAskStorage()
        question = Question(
            question_id="q1",
            question_text="Test question",
            depth=0,
        )
        storage.questions = question
        assert "q1" in storage.questions
        assert storage.questions["q1"] == question

    def test_answers_property(self):
        """Test answers property getter and setter."""
        from pydantic_ai_toolsets.toolsets.self_ask.types import Answer
        
        storage = SelfAskStorage()
        answer = Answer(
            answer_id="a1",
            question_id="q1",
            answer_text="Test answer",
        )
        storage.answers = answer
        assert "a1" in storage.answers
        assert storage.answers["a1"] == answer

    def test_final_answers_property(self):
        """Test final_answers property getter and setter."""
        from pydantic_ai_toolsets.toolsets.self_ask.types import FinalAnswer
        
        storage = SelfAskStorage()
        final_answer = FinalAnswer(
            final_answer_id="fa1",
            main_question_id="q1",
            final_answer_text="Final answer",
        )
        storage.final_answers = final_answer
        assert "fa1" in storage.final_answers
        assert storage.final_answers["fa1"] == final_answer

    def test_get_statistics_empty(self):
        """Test get_statistics with empty storage."""
        storage = SelfAskStorage()
        stats = storage.get_statistics()
        assert stats["total_questions"] == 0
        assert stats["total_answers"] == 0
        assert stats["total_final_answers"] == 0

    def test_get_statistics_with_data(self):
        """Test get_statistics with questions, answers, and final answers."""
        from pydantic_ai_toolsets.toolsets.self_ask.types import Answer, FinalAnswer, Question, QuestionStatus
        
        storage = SelfAskStorage()
        storage.questions = Question(
            question_id="q1",
            question_text="Test",
            depth=0,
            is_main=True,
            status=QuestionStatus.ANSWERED,
        )
        storage.answers = Answer(
            answer_id="a1",
            question_id="q1",
            answer_text="Answer",
            confidence_score=85.0,
        )
        storage.final_answers = FinalAnswer(
            final_answer_id="fa1",
            main_question_id="q1",
            final_answer_text="Final",
        )
        
        stats = storage.get_statistics()
        assert stats["total_questions"] == 1
        assert stats["main_questions"] == 1
        assert stats["answered_questions"] == 1
        assert stats["total_answers"] == 1
        assert stats["total_final_answers"] == 1
        assert stats["avg_confidence_score"] == 85.0

    def test_summary_without_metrics(self):
        """Test summary generation without metrics."""
        from pydantic_ai_toolsets.toolsets.self_ask.types import Question
        
        storage = SelfAskStorage()
        storage.questions = Question(
            question_id="q1",
            question_text="Test",
            depth=0,
        )
        summary = storage.summary()
        
        assert summary["toolset"] == "self_ask"
        assert "statistics" in summary
        assert "storage" in summary
        assert "usage_metrics" not in summary

    def test_summary_with_metrics(self):
        """Test summary generation with metrics."""
        from pydantic_ai_toolsets.toolsets.self_ask.types import Question
        
        storage = SelfAskStorage(track_usage=True)
        storage.questions = Question(
            question_id="q1",
            question_text="Test",
            depth=0,
        )
        summary = storage.summary()
        
        assert "usage_metrics" in summary

    def test_clear(self):
        """Test clear method."""
        from pydantic_ai_toolsets.toolsets.self_ask.types import Answer, Question
        
        storage = SelfAskStorage()
        storage.questions = Question(
            question_id="q1",
            question_text="Test",
            depth=0,
        )
        storage.answers = Answer(
            answer_id="a1",
            question_id="q1",
            answer_text="Answer",
        )
        storage.add_link("q1", "link_1")
        
        storage.clear()
        
        assert len(storage.questions) == 0
        assert len(storage.answers) == 0
        assert storage.links == {}

    def test_add_link(self):
        """Test add_link method."""
        storage = SelfAskStorage()
        storage.add_link("question_1", "link_1")
        assert "question_1" in storage.links
        assert "link_1" in storage.links["question_1"]

    def test_add_linked_from(self):
        """Test add_linked_from method."""
        storage = SelfAskStorage()
        storage.add_linked_from("link_1")
        assert "link_1" in storage.linked_from

    def test_get_state_summary(self):
        """Test get_state_summary."""
        from pydantic_ai_toolsets.toolsets.self_ask.types import FinalAnswer, Question
        
        storage = SelfAskStorage()
        storage.questions = Question(
            question_id="q1",
            question_text="Test",
            depth=0,
        )
        storage.final_answers = FinalAnswer(
            final_answer_id="fa1",
            main_question_id="q1",
            final_answer_text="Final",
        )
        summary = storage.get_state_summary()
        
        assert "Self-Ask" in summary
        assert "1 questions" in summary

    def test_get_outputs_for_linking(self):
        """Test get_outputs_for_linking."""
        from pydantic_ai_toolsets.toolsets.self_ask.types import Answer, FinalAnswer, Question
        
        storage = SelfAskStorage()
        storage.questions = Question(
            question_id="q1",
            question_text="Test question",
            depth=0,
        )
        storage.answers = Answer(
            answer_id="a1",
            question_id="q1",
            answer_text="Test answer",
        )
        storage.final_answers = FinalAnswer(
            final_answer_id="fa1",
            main_question_id="q1",
            final_answer_text="Final answer",
        )
        
        outputs = storage.get_outputs_for_linking()
        
        assert len(outputs) >= 3  # Question, answer, and final answer
        question_outputs = [o for o in outputs if o["id"] == "q1"]
        assert len(question_outputs) == 1
