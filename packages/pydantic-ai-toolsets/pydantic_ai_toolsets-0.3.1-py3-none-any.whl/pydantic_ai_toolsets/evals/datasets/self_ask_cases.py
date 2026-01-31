"""Test cases for self-ask toolset."""

from dataclasses import dataclass


@dataclass
class TestCase:
    """A test case with prompt and metadata."""

    name: str
    prompt: str
    difficulty: str = "medium"  # simple, medium, complex
    expected_tools: list[str] | None = None
    expected_storage_keys: list[str] | None = None
    min_storage_items: int = 1
    max_depth_expected: int = 1  # Maximum depth that should be reached (0-3)


# Self-ask test cases
SELF_ASK_CASES = [
    TestCase(
        name="multi_hop_reasoning",
        prompt="What was the population of the city where the 2016 Summer Olympics were held?",
        difficulty="medium",
        expected_tools=["ask_main_question", "ask_sub_question", "answer_question", "compose_final_answer"],
        expected_storage_keys=["questions", "answers", "final_answers"],
        min_storage_items=3,
        max_depth_expected=2,
    ),
    TestCase(
        name="parallel_sub_questions",
        prompt="Compare the economic growth of Japan and Germany from 2010-2020. Consider GDP growth rates, inflation, and unemployment rates for both countries.",
        difficulty="complex",
        expected_tools=["ask_main_question", "ask_sub_question", "answer_question", "compose_final_answer"],
        expected_storage_keys=["questions", "answers", "final_answers"],
        min_storage_items=5,
        max_depth_expected=1,
    ),
    TestCase(
        name="recursive_decomposition",
        prompt="How did World War I affect modern art movements? Explain the connection between the war and the emergence of movements like Dadaism and Surrealism.",
        difficulty="complex",
        expected_tools=["ask_main_question", "ask_sub_question", "answer_question", "compose_final_answer"],
        expected_storage_keys=["questions", "answers", "final_answers"],
        min_storage_items=6,
        max_depth_expected=3,
    ),
    TestCase(
        name="technical_decomposition",
        prompt="Explain how a web browser renders a webpage. Break down the process from receiving HTML to displaying pixels on screen, including parsing, CSS styling, layout, and rendering.",
        difficulty="complex",
        expected_tools=["ask_main_question", "ask_sub_question", "answer_question", "compose_final_answer"],
        expected_storage_keys=["questions", "answers", "final_answers"],
        min_storage_items=5,
        max_depth_expected=2,
    ),
    TestCase(
        name="research_question",
        prompt="What are the main differences between microservices and monolithic architectures? Consider scalability, deployment, team structure, and maintenance complexity.",
        difficulty="medium",
        expected_tools=["ask_main_question", "ask_sub_question", "answer_question", "compose_final_answer"],
        expected_storage_keys=["questions", "answers", "final_answers"],
        min_storage_items=4,
        max_depth_expected=1,
    ),
    TestCase(
        name="simple_decomposition",
        prompt="What are the key features of Python that make it popular for data science?",
        difficulty="simple",
        expected_tools=["ask_main_question", "ask_sub_question", "answer_question", "compose_final_answer"],
        expected_storage_keys=["questions", "answers", "final_answers"],
        min_storage_items=3,
        max_depth_expected=1,
    ),
]
