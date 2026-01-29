"""Type definitions for pydantic-ai-self-ask."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

# Maximum depth for sub-questions (main question = depth 0, max sub-question = depth 3)
MAX_DEPTH = 3


class QuestionStatus(str, Enum):
    """Status of a question in the self-ask process."""

    PENDING = "pending"  # Question has been asked but not answered
    ANSWERED = "answered"  # Question has been answered
    COMPOSED = "composed"  # Question's answer has been used in final composition


class Question(BaseModel):
    """A question being decomposed in the self-ask process.

    Questions form a tree structure where the main question is the root (depth 0),
    and sub-questions are children (depth 1-3). Each question can spawn sub-questions
    up to the maximum depth of 3.

    Attributes:
        question_id: Unique identifier for this question.
        question_text: The actual question text.
        is_main: Whether this is the main question (depth 0).
        parent_question_id: ID of the parent question (None for main question).
        depth: Depth level in the question tree (0 for main, 1-3 for sub-questions).
        status: Current status of the question (pending, answered, composed).
    """

    question_id: str
    question_text: str
    is_main: bool = Field(default=False, description="Whether this is the main question")
    parent_question_id: str | None = Field(
        default=None, description="ID of the parent question (None for main question)"
    )
    depth: int = Field(
        default=0,
        ge=0,
        le=MAX_DEPTH,
        description=f"Depth level in question tree (0 for main, max {MAX_DEPTH} for sub-questions)",
    )
    status: QuestionStatus = Field(
        default=QuestionStatus.PENDING, description="Current status of the question"
    )


class Answer(BaseModel):
    """An answer to a question or sub-question.

    Each answer corresponds to a specific question and can be used to answer
    parent questions or compose the final answer.

    Attributes:
        answer_id: Unique identifier for this answer.
        question_id: ID of the question this answer addresses.
        answer_text: The actual answer content.
        confidence_score: Optional confidence score (0-100, higher is more confident).
        requires_followup: Whether this answer needs further sub-questions.
    """

    answer_id: str
    question_id: str
    answer_text: str
    confidence_score: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Optional confidence score (0-100, higher is more confident)",
    )
    requires_followup: bool = Field(
        default=False,
        description="Whether this answer needs further sub-questions to be complete",
    )


class FinalAnswer(BaseModel):
    """The final composed answer to the main question.

    The final answer is composed from answers to sub-questions and represents
    the complete solution to the original question.

    Attributes:
        final_answer_id: Unique identifier for this final answer.
        main_question_id: ID of the main question this answers.
        final_answer_text: The composed final answer content.
        composed_from_answers: List of answer IDs used to compose this answer.
        is_complete: Whether the final answer is complete and ready.
    """

    final_answer_id: str
    main_question_id: str
    final_answer_text: str
    composed_from_answers: list[str] = Field(
        default_factory=list,
        description="List of answer IDs used to compose this final answer",
    )
    is_complete: bool = Field(
        default=True, description="Whether the final answer is complete and ready"
    )


class AskMainQuestionItem(BaseModel):
    """Input model for the ask_main_question tool.

    This is the model that agents use when calling ask_main_question.
    """

    question_text: str = Field(
        ...,
        description=(
            "The main question to decompose. This will be the root question "
            "at depth 0 from which sub-questions will be generated."
        ),
    )


class AskSubQuestionItem(BaseModel):
    """Input model for the ask_sub_question tool."""

    parent_question_id: str = Field(
        ..., description="ID of the parent question to create a sub-question for"
    )
    sub_question_text: str = Field(
        ...,
        description=(
            "The sub-question text. This should be a simpler question that helps "
            "answer the parent question."
        ),
    )
    reasoning: str = Field(
        ...,
        description=(
            "Explanation of why this sub-question is needed. "
            "Describe how answering this sub-question will help answer the parent question."
        ),
    )


class AnswerQuestionItem(BaseModel):
    """Input model for the answer_question tool."""

    question_id: str = Field(..., description="ID of the question to answer")
    answer_text: str = Field(
        ...,
        description=(
            "The answer to the question. This should be a complete answer "
            "that addresses the question directly."
        ),
    )
    confidence_score: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description=(
            "Optional confidence score (0-100, higher is more confident). "
            "Use this to indicate how certain you are about this answer."
        ),
    )
    requires_followup: bool = Field(
        default=False,
        description=(
            "Whether this answer needs further sub-questions to be complete. "
            "Set to true if you need to ask sub-sub-questions to fully answer this question."
        ),
    )


class ComposeFinalAnswerItem(BaseModel):
    """Input model for the compose_final_answer tool."""

    main_question_id: str = Field(
        ..., description="ID of the main question to compose the final answer for"
    )
    final_answer_text: str = Field(
        ...,
        description=(
            "The final composed answer. This should synthesize answers from "
            "sub-questions into a complete answer to the main question."
        ),
    )
    answer_ids_used: list[str] = Field(
        ...,
        min_length=1,
        description=(
            "List of answer IDs that were used to compose this final answer. "
            "These should be answers to sub-questions that contributed to the final answer."
        ),
    )
