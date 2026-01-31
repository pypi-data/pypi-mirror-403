"""Test cases for unique toolsets (todo, search)."""

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


# Todo toolset test cases
TODO_CASES = [
    # TestCase(
    #     name="simple_task_planning",
    #     prompt="Create a todo list for planning a birthday party with 5 tasks",
    #     difficulty="simple",
    #     expected_tools=["write_todos"],
    #     expected_storage_keys=["todos"],
    #     min_storage_items=5,
    # ),
    TestCase(
        name="project_breakdown",
        prompt="Break down the task 'Build a web application' into a structured todo list with at least 8 subtasks",
        difficulty="medium",
        expected_tools=["write_todos", "read_todos"],
        expected_storage_keys=["todos"],
        min_storage_items=8,
    ),
    TestCase(
        name="multi_step_project",
        prompt="Plan a software development project: Design a REST API for a todo app. Create todos for requirements gathering, API design, implementation, testing, and deployment",
        difficulty="complex",
        expected_tools=["write_todos", "read_todos"],
        expected_storage_keys=["todos"],
        min_storage_items=5,
    ),
    # TestCase(
    #     name="task_status_tracking",
    #     prompt="Create a todo list with 3 tasks: 'Write documentation' (completed), 'Review code' (in_progress), 'Deploy to production' (pending)",
    #     difficulty="medium",
    #     expected_tools=["write_todos"],
    #     expected_storage_keys=["todos"],
    #     min_storage_items=3,
    # ),
]

# Search toolset test cases
SEARCH_CASES = [
    # TestCase(
    #     name="simple_web_search",
    #     prompt="Search the web for information about Python async programming best practices",
    #     difficulty="simple",
    #     expected_tools=["search_web"],
    #     expected_storage_keys=["search_results"],
    #     min_storage_items=1,
    # ),
    # TestCase(
    #     name="search_and_extract",
    #     prompt="Search for recent articles about AI language models, then extract content from the first 2 results",
    #     difficulty="medium",
    #     expected_tools=["search_web", "extract_web_content"],
    #     expected_storage_keys=["search_results", "extracted_contents"],
    #     min_storage_items=2,
    # ),
    TestCase(
        name="research_task",
        prompt="Research the topic 'microservices architecture patterns'. Search for at least 5 results and extract content from the top 3 most relevant ones",
        difficulty="complex",
        expected_tools=["search_web", "extract_web_content"],
        expected_storage_keys=["search_results", "extracted_contents"],
        min_storage_items=3,
    ),
    TestCase(
        name="information_gathering",
        prompt="Find information about the latest developments in quantum computing. Search for 5 results and extract markdown content from the top 2 results. Create a summary of the information.",
        difficulty="medium",
        expected_tools=["search_web", "extract_web_content"],
        expected_storage_keys=["search_results", "extracted_contents"],
        min_storage_items=2,
    ),
    # TestCase(
    #     name="news_search_recent",
    #     prompt="Search for news articles about artificial intelligence from the past week. Find at least 5 recent news articles and extract content from the top 2 most relevant ones.",
    #     difficulty="medium",
    #     expected_tools=["search_news", "extract_web_content"],
    #     expected_storage_keys=["search_results", "extracted_contents"],
    #     min_storage_items=2,
    # ),
    TestCase(
        name="news_search_past_day",
        prompt="Find the latest news about climate change from the past day. Search for news articles and extract content from the most relevant article.",
        difficulty="simple",
        expected_tools=["search_news", "extract_web_content"],
        expected_storage_keys=["search_results", "extracted_contents"],
        min_storage_items=1,
    ),
    TestCase(
        name="high_resolution_images",
        prompt="Search for high-resolution images of mountain landscapes. Find images that are at least 2560x1440 pixels in resolution. Get at least 5 high-resolution images.",
        difficulty="medium",
        expected_tools=["search_images"],
        expected_storage_keys=["search_results"],
        min_storage_items=5,
    ),
    # TestCase(
    #     name="exact_resolution_images",
    #     prompt="Search for images of sunsets with exact resolution of 1920x1080 pixels. Find at least 3 images with this exact resolution.",
    #     difficulty="simple",
    #     expected_tools=["search_images"],
    #     expected_storage_keys=["search_results"],
    #     min_storage_items=3,
    # ),
    # TestCase(
    #     name="news_and_images_combined",
    #     prompt="Search for recent news about space exploration from the past week, and also find high-resolution images (at least 1920x1080) of space. Extract content from the top news article.",
    #     difficulty="complex",
    #     expected_tools=["search_news", "search_images", "extract_web_content"],
    #     expected_storage_keys=["search_results", "extracted_contents"],
    #     min_storage_items=2,
    # ),
]

