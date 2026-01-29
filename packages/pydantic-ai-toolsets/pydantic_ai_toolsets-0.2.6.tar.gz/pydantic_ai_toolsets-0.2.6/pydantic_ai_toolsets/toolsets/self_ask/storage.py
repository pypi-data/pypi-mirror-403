"""Storage abstraction for self-ask."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from .types import Answer, FinalAnswer, Question, MAX_DEPTH

if TYPE_CHECKING:
    from .._shared.metrics import UsageMetrics


@runtime_checkable
class SelfAskStorageProtocol(Protocol):
    """Protocol for self-ask storage implementations.

    Any class that has `questions`, `answers`, and `final_answers` properties can be used
    as storage for the self-ask toolset.

    Example:
        ```python
        class MyCustomStorage:
            def __init__(self):
                self._questions: dict[str, Question] = {}
                self._answers: dict[str, Answer] = {}
                self._final_answers: dict[str, FinalAnswer] = {}

            @property
            def questions(self) -> dict[str, Question]:
                return self._questions

            @questions.setter
            def questions(self, value: Question) -> None:
                self._questions[value.question_id] = value

            @property
            def answers(self) -> dict[str, Answer]:
                return self._answers

            @answers.setter
            def answers(self, value: Answer) -> None:
                self._answers[value.answer_id] = value

            @property
            def final_answers(self) -> dict[str, FinalAnswer]:
                return self._final_answers

            @final_answers.setter
            def final_answers(self, value: FinalAnswer) -> None:
                self._final_answers[value.final_answer_id] = value
        ```
    """

    @property
    def questions(self) -> dict[str, Question]:
        """Get the current dictionary of questions (question_id -> Question)."""
        ...

    @questions.setter
    def questions(self, value: Question) -> None:
        """Add or update a question in the dictionary."""
        ...

    @property
    def answers(self) -> dict[str, Answer]:
        """Get the current dictionary of answers (answer_id -> Answer)."""
        ...

    @answers.setter
    def answers(self, value: Answer) -> None:
        """Add or update an answer in the dictionary."""
        ...

    @property
    def final_answers(self) -> dict[str, FinalAnswer]:
        """Get the current dictionary of final answers (final_answer_id -> FinalAnswer)."""
        ...

    @final_answers.setter
    def final_answers(self, value: FinalAnswer) -> None:
        """Add or update a final answer in the dictionary."""
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
            item_id: ID of the item (question_id, answer_id, or final_answer_id)
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
class SelfAskStorage:
    """Default in-memory self-ask storage.

    Simple implementation that stores questions, answers, and final answers in memory.
    Use this for standalone agents or testing.

    Example:
        ```python
        from pydantic_ai_toolsets import create_self_ask_toolset, SelfAskStorage

        storage = SelfAskStorage()
        toolset = create_self_ask_toolset(storage=storage)

        # After agent runs, access questions, answers, and final answers directly
        print(storage.questions)
        print(storage.answers)
        print(storage.final_answers)

        # With metrics tracking
        storage = SelfAskStorage(track_usage=True)
        toolset = create_self_ask_toolset(storage=storage)
        print(storage.metrics.total_tokens())
        ```
    """

    _questions: dict[str, Question] = field(default_factory=dict)
    _answers: dict[str, Answer] = field(default_factory=dict)
    _final_answers: dict[str, FinalAnswer] = field(default_factory=dict)
    _metrics: UsageMetrics | None = field(default=None)
    _links: dict[str, list[str]] = field(default_factory=dict)  # item_id -> list of link IDs
    _linked_from: list[str] = field(default_factory=list)  # list of link IDs where this storage is target

    # Maximum depth constant
    MAX_DEPTH: int = MAX_DEPTH

    def __init__(self, *, track_usage: bool = False) -> None:
        """Initialize storage with optional metrics tracking.

        Args:
            track_usage: If True, enables usage metrics collection.
        """
        self._questions = {}
        self._answers = {}
        self._final_answers = {}
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
    def questions(self) -> dict[str, Question]:
        """Get the current dictionary of questions."""
        return self._questions

    @questions.setter
    def questions(self, value: Question) -> None:
        """Add or update a question in the dictionary."""
        self._questions[value.question_id] = value

    @property
    def answers(self) -> dict[str, Answer]:
        """Get the current dictionary of answers."""
        return self._answers

    @answers.setter
    def answers(self, value: Answer) -> None:
        """Add or update an answer in the dictionary."""
        self._answers[value.answer_id] = value

    @property
    def final_answers(self) -> dict[str, FinalAnswer]:
        """Get the current dictionary of final answers."""
        return self._final_answers

    @final_answers.setter
    def final_answers(self, value: FinalAnswer) -> None:
        """Add or update a final answer in the dictionary."""
        self._final_answers[value.final_answer_id] = value

    @property
    def metrics(self) -> UsageMetrics | None:
        """Get usage metrics if tracking is enabled."""
        return self._metrics

    def get_statistics(self) -> dict[str, int | float]:
        """Get summary statistics about self-ask operations.

        Returns:
            Dictionary with question, answer, and final answer counts, plus max depth reached.
        """
        total_questions = len(self._questions)
        main_questions = sum(1 for q in self._questions.values() if q.is_main)
        answered_questions = sum(
            1 for q in self._questions.values() if q.status.value == "answered"
        )
        max_depth_reached = max((q.depth for q in self._questions.values()), default=0)
        total_answers = len(self._answers)
        total_final_answers = len(self._final_answers)
        avg_confidence = None
        confidence_scores = [
            a.confidence_score for a in self._answers.values() if a.confidence_score is not None
        ]
        if confidence_scores:
            avg_confidence = sum(confidence_scores) / len(confidence_scores)

        stats: dict[str, int | float] = {
            "total_questions": total_questions,
            "main_questions": main_questions,
            "answered_questions": answered_questions,
            "max_depth_reached": max_depth_reached,
            "total_answers": total_answers,
            "total_final_answers": total_final_answers,
        }
        if avg_confidence is not None:
            stats["avg_confidence_score"] = avg_confidence

        return stats

    def summary(self) -> dict[str, Any]:
        """Get comprehensive JSON summary of storage state and metrics.

        Returns:
            Dictionary containing storage state, statistics, and usage metrics.
        """
        summary_dict: dict[str, Any] = {
            "toolset": "self_ask",
            "statistics": self.get_statistics(),
        }

        # Add storage-specific data
        summary_dict["storage"] = {
            "questions": {
                question_id: {
                    "question_id": question.question_id,
                    "question": question.question,
                    "depth": question.depth,
                    "is_main": question.is_main,
                    "status": question.status.value if hasattr(question.status, "value") else str(question.status),
                    "parent_question_id": question.parent_question_id,
                }
                for question_id, question in self._questions.items()
            },
            "answers": {
                answer_id: {
                    "answer_id": answer.answer_id,
                    "question_id": answer.question_id,
                    "content": answer.content,
                    "confidence_score": answer.confidence_score,
                    "requires_followup": answer.requires_followup,
                }
                for answer_id, answer in self._answers.items()
            },
            "final_answers": {
                final_answer_id: {
                    "final_answer_id": fa.final_answer_id,
                    "main_question_id": fa.main_question_id,
                    "content": fa.content,
                    "is_complete": fa.is_complete,
                    "composed_from_answers": fa.composed_from_answers,
                }
                for final_answer_id, fa in self._final_answers.items()
            },
        }

        # Add metrics if available
        if self._metrics:
            summary_dict["usage_metrics"] = self._metrics.to_dict()

        return summary_dict

    def clear(self) -> None:
        """Clear all questions, answers, final answers, and reset metrics."""
        self._questions.clear()
        self._answers.clear()
        self._final_answers.clear()
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
            item_id: ID of the item (question_id, answer_id, or final_answer_id)
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
            Formatted string summary of questions, answers, and final answers.
        """
        stats = self.get_statistics()
        lines: list[str] = []
        lines.append(f"Self-Ask: {stats['total_questions']} questions, {stats['total_answers']} answers, {stats['total_final_answers']} final answers")
        if stats["main_questions"] > 0:
            lines.append(f"  - {stats['main_questions']} main questions")
        if stats["answered_questions"] > 0:
            lines.append(f"  - {stats['answered_questions']} answered")
        if stats["max_depth_reached"] > 0:
            lines.append(f"  - Max depth: {stats['max_depth_reached']}")
        if self._final_answers:
            latest_fa = list(self._final_answers.values())[-1]
            lines.append(f"  Latest final answer: {latest_fa.content}")
        return "\n".join(lines)

    def get_outputs_for_linking(self) -> list[dict[str, str]]:
        """Get list of linkable items with their IDs and descriptions.

        Returns:
            List of dictionaries with 'id' and 'description' keys for questions, answers, and final answers.
        """
        linkable_items: list[dict[str, str]] = []
        # Add questions
        for question_id, question in self._questions.items():
            description = f"Question: {question.question}"
            linkable_items.append({"id": question_id, "description": description})
        # Add answers
        for answer_id, answer in self._answers.items():
            description = f"Answer: {answer.content}"
            linkable_items.append({"id": answer_id, "description": description})
        # Add final answers
        for final_answer_id, final_answer in self._final_answers.items():
            description = f"Final Answer: {final_answer.content}"
            linkable_items.append({"id": final_answer_id, "description": description})
        return linkable_items
