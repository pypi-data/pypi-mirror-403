"""Test cases for multi-agent toolsets (debate, multi_personas, persona_debate)."""

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


# Multi-agent test cases (same prompts for all toolsets)
MULTI_AGENT_CASES = [
    TestCase(
        name="architecture_debate",
        prompt="""Debate whether a company should adopt microservices architecture or stick with monolithic architecture.
Have multiple perspectives argue for and against each approach.
Consider factors like team size, complexity, scalability needs, and technical debt.
Reach a conclusion or synthesis.""",
        difficulty="medium",
        expected_tools=None,  # Varies by toolset
        expected_storage_keys=None,  # Varies by toolset
        min_storage_items=2,
    ),
#     TestCase(
#         name="technology_choice",
#         prompt="""A team needs to choose between React, Vue, and Angular for a new frontend project.
# Have different personas (a senior developer, a junior developer, a product manager, and a CTO) 
# discuss the pros and cons of each framework from their perspective.
# Synthesize their viewpoints into a recommendation.""",
#         difficulty="medium",
#         expected_tools=None,
#         expected_storage_keys=None,
#         min_storage_items=3,
#     ),
    TestCase(
        name="feature_prioritization",
        prompt="""A product team needs to prioritize features for the next release:
- User authentication system
- Real-time notifications
- Advanced analytics dashboard
- Mobile app
- API for third-party integrations

Have stakeholders (engineers, product managers, designers, customers) debate priorities.
Consider technical complexity, user value, business impact, and resource constraints.
Reach consensus on the top 3 features.""",
        difficulty="complex",
        expected_tools=None,
        expected_storage_keys=None,
        min_storage_items=4,
    ),
#     TestCase(
#         name="security_policy",
#         prompt="""A company is debating security policies:
# - Should they require 2FA for all employees?
# - What password complexity rules should they enforce?
# - How often should security audits be conducted?

# Have security experts, developers, and business stakeholders debate these policies.
# Consider security benefits vs usability impact vs implementation cost.
# Provide a balanced recommendation.""",
#         difficulty="medium",
#         expected_tools=None,
#         expected_storage_keys=None,
#         min_storage_items=3,
#     ),
#     TestCase(
#         name="remote_work_policy",
#         prompt="""A company is deciding on remote work policies post-pandemic.
# Topics to discuss:
# - Fully remote vs hybrid vs office-first
# - Time zone flexibility
# - Meeting schedules and async communication
# - Performance evaluation for remote workers

# Have different personas (HR, managers, employees, executives) discuss from their perspectives.
# Synthesize into a comprehensive policy recommendation.""",
#         difficulty="medium",
#         expected_tools=None,
#         expected_storage_keys=None,
#         min_storage_items=4,
#     ),
]

