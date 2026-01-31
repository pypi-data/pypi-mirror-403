"""Test cases for thinking/cognition toolsets (beam, cot, got, mcts, tot)."""

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


# Thinking/cognition test cases (same prompts for all toolsets)
THINKING_CASES = [
#     TestCase(
#         name="optimization_problem",
#         prompt="""Solve this optimization problem step by step:

# A delivery company needs to optimize routes for 5 locations: A, B, C, D, E
# Starting point: Warehouse W
# Distances:
# - W->A: 10km, W->B: 15km, W->C: 20km, W->D: 12km, W->E: 18km
# - A->B: 8km, A->C: 12km, A->D: 6km, A->E: 14km
# - B->C: 10km, B->D: 9km, B->E: 11km
# - C->D: 7km, C->E: 5km
# - D->E: 8km

# Find the shortest route that visits all locations and returns to W.
# Use your reasoning tools to explore different approaches and find the optimal solution.""",
#         difficulty="complex",
#         expected_tools=None,  # Varies by toolset
#         expected_storage_keys=None,  # Varies by toolset
#         min_storage_items=3,
#     ),
    TestCase(
        name="architecture_analysis",
        prompt="""Analyze the pros and cons of microservices architecture vs monolithic architecture.
Consider factors like scalability, maintainability, deployment complexity, team structure, and cost.
Break down your analysis systematically and provide a comprehensive comparison.""",
        difficulty="medium",
        expected_tools=None,
        expected_storage_keys=None,
        min_storage_items=2,
    ),
    TestCase(
        name="project_planning",
        prompt="""Plan a software development project with the following requirements:
- Build a REST API for a task management system
- Use Python and FastAPI
- Include user authentication
- Support CRUD operations for tasks
- Add unit tests and integration tests
- Deploy to cloud infrastructure

Break down the project into phases, identify dependencies, estimate effort, and create a development plan.""",
        difficulty="complex",
        expected_tools=None,
        expected_storage_keys=None,
        min_storage_items=5,
    ),
#     TestCase(
#         name="logical_reasoning",
#         prompt="""Solve this logical reasoning problem:

# Three friends - Alice, Bob, and Charlie - are discussing their favorite programming languages.
# - Alice says: "My favorite is Python or JavaScript"
# - Bob says: "My favorite is not Python"
# - Charlie says: "My favorite is JavaScript"

# If exactly one of them is lying, and the other two are telling the truth, determine each person's favorite language.
# Show your reasoning step by step.""",
#         difficulty="medium",
#         expected_tools=None,
#         expected_storage_keys=None,
#         min_storage_items=3,
#     ),
#     TestCase(
#         name="decision_making",
#         prompt="""A company needs to decide between three cloud providers: AWS, Azure, and GCP.
# Evaluate each option based on:
# - Cost (for their specific workload)
# - Features and services
# - Ease of use and developer experience
# - Support and documentation
# - Integration with existing tools

# Provide a structured analysis and recommendation.""",
#         difficulty="medium",
#         expected_tools=None,
#         expected_storage_keys=None,
#         min_storage_items=3,
#     ),
]

