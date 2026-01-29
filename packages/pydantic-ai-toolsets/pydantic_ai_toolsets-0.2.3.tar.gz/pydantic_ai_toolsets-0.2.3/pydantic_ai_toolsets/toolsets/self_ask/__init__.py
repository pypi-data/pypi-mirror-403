"""Self-ask toolset for pydantic-ai agents.

Provides self-ask reasoning capabilities for AI agents.
Compatible with any pydantic-ai agent - no specific deps required.

Example:
    ```python
    from pydantic_ai import Agent
    from pydantic_ai_toolsets import create_self_ask_toolset, SelfAskStorage

    # Simple usage
    agent = Agent("openai:gpt-4.1", toolsets=[create_self_ask_toolset()])

    # With storage access
    storage = SelfAskStorage()
    agent = Agent("openai:gpt-4.1", toolsets=[create_self_ask_toolset(storage)])
    result = await agent.run("What was the population of the city where the 2016 Summer Olympics were held?")
    print(storage.questions)  # Access questions directly
    print(storage.answers)  # Access answers directly
    print(storage.final_answers)  # Access final answers directly
    ```
"""

from .storage import SelfAskStorage, SelfAskStorageProtocol
from .toolset import (
    ASK_MAIN_QUESTION_DESCRIPTION,
    ASK_SUB_QUESTION_DESCRIPTION,
    ANSWER_QUESTION_DESCRIPTION,
    COMPOSE_FINAL_ANSWER_DESCRIPTION,
    GET_FINAL_ANSWER_DESCRIPTION,
    READ_SELF_ASK_STATE_DESCRIPTION,
    SELF_ASK_SYSTEM_PROMPT,
    create_self_ask_toolset,
    get_self_ask_system_prompt,
)
from .types import (
    Answer,
    AnswerQuestionItem,
    AskMainQuestionItem,
    AskSubQuestionItem,
    ComposeFinalAnswerItem,
    FinalAnswer,
    Question,
    QuestionStatus,
    MAX_DEPTH,
)

__all__ = [
    # Main factory
    "create_self_ask_toolset",
    "get_self_ask_system_prompt",
    # Types
    "Question",
    "Answer",
    "FinalAnswer",
    "QuestionStatus",
    "AskMainQuestionItem",
    "AskSubQuestionItem",
    "AnswerQuestionItem",
    "ComposeFinalAnswerItem",
    # Storage
    "SelfAskStorage",
    "SelfAskStorageProtocol",
    # Constants
    "MAX_DEPTH",
    "SELF_ASK_SYSTEM_PROMPT",
    "READ_SELF_ASK_STATE_DESCRIPTION",
    "ASK_MAIN_QUESTION_DESCRIPTION",
    "ASK_SUB_QUESTION_DESCRIPTION",
    "ANSWER_QUESTION_DESCRIPTION",
    "COMPOSE_FINAL_ANSWER_DESCRIPTION",
    "GET_FINAL_ANSWER_DESCRIPTION",
]

__version__ = "0.1.0"
