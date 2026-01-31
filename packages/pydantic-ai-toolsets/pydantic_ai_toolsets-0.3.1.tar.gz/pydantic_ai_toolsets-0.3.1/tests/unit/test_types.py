"""Unit tests for Pydantic type validation across all toolsets."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from pydantic_ai_toolsets.toolsets.chain_of_thought_reasoning.types import Thought, ThoughtItem
from pydantic_ai_toolsets.toolsets.tree_of_thought_reasoning.types import (
    BranchEvaluation,
    ThoughtNode,
)
from pydantic_ai_toolsets.toolsets.reflection.types import Critique, ReflectionOutput
from pydantic_ai_toolsets.toolsets.to_do.types import Todo, TodoItem
from pydantic_ai_toolsets.toolsets.self_ask.types import (
    Answer,
    AnswerQuestionItem,
    AskMainQuestionItem,
    AskSubQuestionItem,
    ComposeFinalAnswerItem,
    FinalAnswer,
    Question,
    QuestionStatus,
)
from pydantic_ai_toolsets.toolsets.meta_orchestrator.types import (
    CrossToolsetLink,
    LinkType,
    Stage,
    WorkflowTemplate,
)


# ============================================================================
# Chain of Thought Types
# ============================================================================


class TestThought:
    """Test suite for Thought model."""

    def test_valid_thought(self):
        """Test creating a valid Thought."""
        thought = Thought(
            thought="Test thought",
            thought_number=1,
            total_thoughts=3,
        )
        assert thought.thought == "Test thought"
        assert thought.thought_number == 1
        assert thought.total_thoughts == 3
        assert thought.is_revision is False
        assert thought.next_thought_needed is True

    def test_thought_with_revision(self):
        """Test Thought with revision fields."""
        thought = Thought(
            thought="Revised thought",
            thought_number=2,
            total_thoughts=3,
            is_revision=True,
            revises_thought=1,
        )
        assert thought.is_revision is True
        assert thought.revises_thought == 1

    def test_thought_with_branch(self):
        """Test Thought with branch fields."""
        thought = Thought(
            thought="Branched thought",
            thought_number=3,
            total_thoughts=5,
            branch_id="branch_1",
            branch_from_thought=1,
        )
        assert thought.branch_id == "branch_1"
        assert thought.branch_from_thought == 1

    def test_thought_defaults(self):
        """Test Thought default values."""
        thought = Thought(
            thought="Test",
            thought_number=1,
            total_thoughts=1,
        )
        assert thought.is_revision is False
        assert thought.revises_thought is None
        assert thought.branch_id is None
        assert thought.branch_from_thought is None
        assert thought.next_thought_needed is True


class TestThoughtItem:
    """Test suite for ThoughtItem model."""

    def test_valid_thought_item(self):
        """Test creating a valid ThoughtItem."""
        item = ThoughtItem(
            thought="Test thought",
            thought_number=1,
            total_thoughts=3,
        )
        assert item.thought == "Test thought"
        assert item.thought_number == 1


# ============================================================================
# Tree of Thought Types
# ============================================================================


class TestThoughtNode:
    """Test suite for ThoughtNode model."""

    def test_valid_node(self):
        """Test creating a valid ThoughtNode."""
        node = ThoughtNode(
            node_id="node_1",
            content="Test content",
        )
        assert node.node_id == "node_1"
        assert node.content == "Test content"
        assert node.parent_id is None
        assert node.depth == 0
        assert node.status == "active"
        assert node.is_solution is False

    def test_node_with_parent(self):
        """Test ThoughtNode with parent."""
        node = ThoughtNode(
            node_id="node_2",
            content="Child node",
            parent_id="node_1",
            depth=1,
        )
        assert node.parent_id == "node_1"
        assert node.depth == 1

    def test_node_solution(self):
        """Test ThoughtNode marked as solution."""
        node = ThoughtNode(
            node_id="node_1",
            content="Solution",
            is_solution=True,
            status="completed",
        )
        assert node.is_solution is True
        assert node.status == "completed"

    def test_node_status_values(self):
        """Test ThoughtNode status enum values."""
        for status in ["active", "pruned", "merged", "completed"]:
            node = ThoughtNode(
                node_id="node_1",
                content="Test",
                status=status,
            )
            assert node.status == status

    def test_node_invalid_status(self):
        """Test ThoughtNode with invalid status raises error."""
        with pytest.raises(ValidationError):
            ThoughtNode(
                node_id="node_1",
                content="Test",
                status="invalid_status",
            )


class TestBranchEvaluation:
    """Test suite for BranchEvaluation model."""

    def test_valid_evaluation(self):
        """Test creating a valid BranchEvaluation."""
        eval = BranchEvaluation(
            branch_id="branch_1",
            score=85.0,
            reasoning="Good approach",
            recommendation="continue",
        )
        assert eval.branch_id == "branch_1"
        assert eval.score == 85.0
        assert eval.reasoning == "Good approach"
        assert eval.recommendation == "continue"

    def test_evaluation_recommendation_values(self):
        """Test BranchEvaluation recommendation enum values."""
        for rec in ["continue", "prune", "merge", "explore_deeper"]:
            eval = BranchEvaluation(
                branch_id="branch_1",
                score=50.0,
                reasoning="Test",
                recommendation=rec,
            )
            assert eval.recommendation == rec


# ============================================================================
# Reflection Types
# ============================================================================


class TestReflectionOutput:
    """Test suite for ReflectionOutput model."""

    def test_valid_output(self):
        """Test creating a valid ReflectionOutput."""
        output = ReflectionOutput(
            output_id="output_1",
            content="Test output",
        )
        assert output.output_id == "output_1"
        assert output.content == "Test output"
        assert output.cycle == 0
        assert output.parent_id is None
        assert output.is_final is False
        assert output.quality_score is None

    def test_output_with_quality_score(self):
        """Test ReflectionOutput with quality score."""
        output = ReflectionOutput(
            output_id="output_1",
            content="Test",
            quality_score=85.0,
        )
        assert output.quality_score == 85.0

    def test_output_quality_score_bounds(self):
        """Test ReflectionOutput quality score bounds."""
        # Valid range
        ReflectionOutput(
            output_id="output_1",
            content="Test",
            quality_score=0.0,
        )
        ReflectionOutput(
            output_id="output_2",
            content="Test",
            quality_score=100.0,
        )
        
        # Invalid: below 0
        with pytest.raises(ValidationError):
            ReflectionOutput(
                output_id="output_3",
                content="Test",
                quality_score=-1.0,
            )
        
        # Invalid: above 100
        with pytest.raises(ValidationError):
            ReflectionOutput(
                output_id="output_4",
                content="Test",
                quality_score=101.0,
            )

    def test_output_refinement_cycle(self):
        """Test ReflectionOutput refinement cycle."""
        output = ReflectionOutput(
            output_id="output_2",
            content="Refined",
            cycle=1,
            parent_id="output_1",
        )
        assert output.cycle == 1
        assert output.parent_id == "output_1"


class TestCritique:
    """Test suite for Critique model."""

    def test_valid_critique(self):
        """Test creating a valid Critique."""
        critique = Critique(
            critique_id="critique_1",
            output_id="output_1",
            problems=["Problem 1"],
            strengths=["Strength 1"],
            overall_assessment="Overall assessment",
            improvement_suggestions=["Suggestion 1"],
        )
        assert critique.critique_id == "critique_1"
        assert critique.output_id == "output_1"
        assert len(critique.problems) == 1
        assert len(critique.strengths) == 1
        assert len(critique.improvement_suggestions) == 1


# ============================================================================
# Todo Types
# ============================================================================


class TestTodo:
    """Test suite for Todo model."""

    def test_valid_todo(self):
        """Test creating a valid Todo."""
        todo = Todo(
            todo_id="todo_1",
            content="Test task",
            status="pending",
            active_form="Testing task",
        )
        assert todo.todo_id == "todo_1"
        assert todo.content == "Test task"
        assert todo.status == "pending"
        assert todo.active_form == "Testing task"

    def test_todo_status_values(self):
        """Test Todo status enum values."""
        for status in ["pending", "in_progress", "completed"]:
            todo = Todo(
                todo_id="todo_1",
                content="Test",
                status=status,
                active_form="Testing",
            )
            assert todo.status == status

    def test_todo_invalid_status(self):
        """Test Todo with invalid status raises error."""
        with pytest.raises(ValidationError):
            Todo(
                todo_id="todo_1",
                content="Test",
                status="invalid",
                active_form="Testing",
            )


class TestTodoItem:
    """Test suite for TodoItem model."""

    def test_valid_todo_item(self):
        """Test creating a valid TodoItem."""
        item = TodoItem(
            content="Test task",
            status="pending",
            active_form="Testing task",
        )
        assert item.content == "Test task"
        assert item.status == "pending"


# ============================================================================
# Self-Ask Types
# ============================================================================


class TestQuestion:
    """Test suite for Question model."""

    def test_valid_question(self):
        """Test creating a valid Question."""
        question = Question(
            question_id="q1",
            question_text="What is the answer?",
            depth=0,
        )
        assert question.question_id == "q1"
        assert question.question_text == "What is the answer?"
        assert question.depth == 0
        assert question.status == QuestionStatus.PENDING

    def test_question_status_values(self):
        """Test Question status enum values."""
        for status in QuestionStatus:
            question = Question(
                question_id="q1",
                question_text="Test",
                depth=0,
                status=status,
            )
            assert question.status == status


class TestAnswer:
    """Test suite for Answer model."""

    def test_valid_answer(self):
        """Test creating a valid Answer."""
        answer = Answer(
            answer_id="a1",
            question_id="q1",
            answer_text="The answer",
        )
        assert answer.answer_id == "a1"
        assert answer.question_id == "q1"
        assert answer.answer_text == "The answer"


class TestFinalAnswer:
    """Test suite for FinalAnswer model."""

    def test_valid_final_answer(self):
        """Test creating a valid FinalAnswer."""
        final = FinalAnswer(
            final_answer_id="final_1",
            main_question_id="q1",
            final_answer_text="Final answer",
        )
        assert final.final_answer_id == "final_1"
        assert final.main_question_id == "q1"
        assert final.final_answer_text == "Final answer"


# ============================================================================
# Meta-Orchestrator Types
# ============================================================================


class TestCrossToolsetLink:
    """Test suite for CrossToolsetLink model."""

    def test_valid_link(self):
        """Test creating a valid CrossToolsetLink."""
        link = CrossToolsetLink(
            link_id="link_1",
            source_toolset_id="search",
            source_item_id="result_1",
            target_toolset_id="self_ask",
            target_item_id="question_1",
            link_type=LinkType.REFERENCES,
            created_at=1234567890.0,
        )
        assert link.link_id == "link_1"
        assert link.source_toolset_id == "search"
        assert link.link_type == LinkType.REFERENCES

    def test_link_type_values(self):
        """Test CrossToolsetLink link type enum values."""
        for link_type in LinkType:
            link = CrossToolsetLink(
                link_id="link_1",
                source_toolset_id="source",
                source_item_id="item_1",
                target_toolset_id="target",
                target_item_id="item_2",
                link_type=link_type,
                created_at=1234567890.0,
            )
            assert link.link_type == link_type


class TestStage:
    """Test suite for Stage model."""

    def test_valid_stage(self):
        """Test creating a valid Stage."""
        stage = Stage(
            name="research",
            toolset_id="search",
            transition_condition="has_results",
            description="Research stage",
        )
        assert stage.name == "research"
        assert stage.toolset_id == "search"
        assert stage.transition_condition == "has_results"


class TestWorkflowTemplate:
    """Test suite for WorkflowTemplate model."""

    def test_valid_workflow_template(self):
        """Test creating a valid WorkflowTemplate."""
        template = WorkflowTemplate(
            name="test_workflow",
            toolsets=["search", "self_ask"],
            stages=[
                Stage(
                    name="research",
                    toolset_id="search",
                    transition_condition="has_results",
                ),
            ],
            handoff_instructions={},
            description="Test workflow",
        )
        assert template.name == "test_workflow"
        assert len(template.toolsets) == 2
        assert len(template.stages) == 1
