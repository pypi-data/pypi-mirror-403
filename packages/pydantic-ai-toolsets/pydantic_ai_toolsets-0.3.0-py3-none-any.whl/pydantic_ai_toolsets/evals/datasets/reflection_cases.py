"""Test cases for reflection toolsets (self_refine, reflection)."""

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


# Reflection test cases (same prompts for all toolsets)
REFLECTION_CASES = [
    TestCase(
        name="code_explanation",
        prompt="""Write a clear explanation of how async/await works in Python.
Then refine it to make it more accessible to beginners, fix any technical inaccuracies,
and ensure it includes practical examples.""",
        difficulty="medium",
        expected_tools=None,  # Varies by toolset
        expected_storage_keys=None,  # Varies by toolset
        min_storage_items=2,
    ),
#     TestCase(
#         name="api_design",
#         prompt="""Design a REST API for a blog system with endpoints for posts, comments, and users.
# Then refine the design to improve:
# - RESTful principles adherence
# - Error handling
# - Authentication and authorization
# - API versioning strategy
# - Documentation requirements""",
#         difficulty="complex",
#         expected_tools=None,
#         expected_storage_keys=None,
#         min_storage_items=2,
#     ),
#     TestCase(
#         name="documentation_writing",
#         prompt="""Write documentation for a Python function that processes CSV files.
# Then refine it to:
# - Add more examples
# - Clarify edge cases
# - Improve formatting and readability
# - Add type hints documentation
# - Include error handling examples""",
#         difficulty="medium",
#         expected_tools=None,
#         expected_storage_keys=None,
#         min_storage_items=2,
#     ),
    TestCase(
        name="architecture_proposal",
        prompt="""Propose an architecture for a real-time chat application.
Then refine it to address:
- Scalability concerns
- Data consistency
- Security considerations
- Deployment strategy
- Monitoring and observability""",
        difficulty="complex",
        expected_tools=None,
        expected_storage_keys=None,
        min_storage_items=2,
    ),
#     TestCase(
#         name="troubleshooting_guide",
#         prompt="""Write a troubleshooting guide for common Python errors.
# Then refine it to:
# - Add more error types
# - Improve explanations
# - Add code examples for each error
# - Organize by category
# - Include prevention tips""",
#         difficulty="medium",
#         expected_tools=None,
#         expected_storage_keys=None,
#         min_storage_items=2,
#     ),
]

