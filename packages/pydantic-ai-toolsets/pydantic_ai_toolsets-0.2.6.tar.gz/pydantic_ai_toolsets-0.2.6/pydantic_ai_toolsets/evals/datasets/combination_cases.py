"""Test cases for combination workflow templates."""

from dataclasses import dataclass


@dataclass
class CombinationTestCase:
    """A test case for combination workflow evaluation."""

    name: str
    prompt: str
    workflow_template: str
    expected_toolsets: list[str]
    expected_transitions: list[tuple[str, str]]
    expected_prefixed_tools: list[str] | None = None
    min_storage_items: int = 5
    difficulty: str = "medium"
    expected_cross_links: int = 0


# Research Assistant Cases
RESEARCH_ASSISTANT_CASES = [
    CombinationTestCase(
        name="quantum_computing_research",
        prompt="Research the latest developments in quantum computing and explain the key breakthroughs in quantum error correction and quantum algorithms.",
        workflow_template="research_assistant",
        expected_toolsets=["search", "self_ask", "self_refine", "todo"],
        expected_transitions=[
            ("search", "self_ask"),
            ("self_ask", "self_refine"),
            ("self_refine", "todo"),
        ],
        expected_prefixed_tools=["search_search_web", "self_ask_ask_main_question", "self_refine_generate_output", "todo_read_todos"],
        min_storage_items=5,
        difficulty="medium",
        expected_cross_links=2,
    ),
    CombinationTestCase(
        name="renewable_energy_trends",
        prompt="Find information about renewable energy trends in 2026, including solar, wind, and battery storage technologies. Provide a comprehensive analysis.",
        workflow_template="research_assistant",
        expected_toolsets=["search", "self_ask", "self_refine", "todo"],
        expected_transitions=[
            ("search", "self_ask"),
            ("self_ask", "self_refine"),
        ],
        min_storage_items=4,
        difficulty="medium",
        expected_cross_links=1,
    ),
    CombinationTestCase(
        name="indian_cricket_team_news",
        prompt="Find the latest news about the Indian cricket team and provide a summary of the news.",
        workflow_template="research_assistant",
        expected_toolsets=["search", "self_ask", "self_refine", "todo"],
        expected_transitions=[
            ("search", "self_ask"),
            ("self_ask", "self_refine"),
        ],
        min_storage_items=4,
        difficulty="medium",
        expected_cross_links=1,
    ),
    # CombinationTestCase(
    #     name="ai_safety_research",
    #     prompt="Investigate recent AI safety research, focusing on alignment, robustness, and interpretability. Summarize key findings.",
    #     workflow_template="research_assistant",
    #     expected_toolsets=["search", "self_ask", "self_refine", "todo"],
    #     expected_transitions=[
    #         ("search", "self_ask"),
    #         ("self_ask", "self_refine"),
    #     ],
    #     min_storage_items=4,
    #     difficulty="medium",
    #     expected_cross_links=1,
    # ),
    # CombinationTestCase(
    #     name="sustainable_packaging",
    #     prompt="Research sustainable packaging solutions, including biodegradable materials, circular economy approaches, and industry best practices.",
    #     workflow_template="research_assistant",
    #     expected_toolsets=["search", "self_ask", "self_refine", "todo"],
    #     expected_transitions=[
    #         ("search", "self_ask"),
    #         ("self_ask", "self_refine"),
    #     ],
    #     min_storage_items=4,
    #     difficulty="medium",
    #     expected_cross_links=1,
    # ),
    # CombinationTestCase(
    #     name="climate_change_mitigation",
    #     prompt="Research effective climate change mitigation strategies, including carbon capture, renewable energy adoption, and policy interventions.",
    #     workflow_template="research_assistant",
    #     expected_toolsets=["search", "self_ask", "self_refine", "todo"],
    #     expected_transitions=[
    #         ("search", "self_ask"),
    #         ("self_ask", "self_refine"),
    #     ],
    #     min_storage_items=4,
    #     difficulty="complex",
    #     expected_cross_links=2,
    # ),
]

# Creative Problem Solver Cases
CREATIVE_PROBLEM_SOLVER_CASES = [
    CombinationTestCase(
        name="sustainable_transportation",
        prompt="Design a sustainable urban transportation system that integrates public transit, bike-sharing, electric vehicles, and pedestrian infrastructure.",
        workflow_template="creative_problem_solver",
        expected_toolsets=["persona", "got", "reflection"],
        expected_transitions=[
            ("persona", "got"),
            ("got", "reflection"),
        ],
        expected_prefixed_tools=["persona_create_persona", "got_create_node", "reflection_create_output"],
        min_storage_items=6,
        difficulty="complex",
        expected_cross_links=2,
    ),
    CombinationTestCase(
        name="food_waste_reduction",
        prompt="Create a comprehensive strategy for reducing food waste at the household, restaurant, and supply chain levels.",
        workflow_template="creative_problem_solver",
        expected_toolsets=["persona", "got", "reflection"],
        expected_transitions=[
            ("persona", "got"),
            ("got", "reflection"),
        ],
        min_storage_items=5,
        difficulty="medium",
        expected_cross_links=1,
    ),
    CombinationTestCase(
        name="inclusive_education_platform",
        prompt="Design an inclusive educational platform that accommodates different learning styles, disabilities, and cultural backgrounds.",
        workflow_template="creative_problem_solver",
        expected_toolsets=["persona", "got", "reflection"],
        expected_transitions=[
            ("persona", "got"),
            ("got", "reflection"),
        ],
        min_storage_items=5,
        difficulty="complex",
        expected_cross_links=2,
    ),
    # CombinationTestCase(
    #     name="carbon_neutral_manufacturing",
    #     prompt="Develop a plan for carbon-neutral manufacturing that balances environmental goals with economic viability.",
    #     workflow_template="creative_problem_solver",
    #     expected_toolsets=["persona", "got", "reflection"],
    #     expected_transitions=[
    #         ("persona", "got"),
    #         ("got", "reflection"),
    #     ],
    #     min_storage_items=5,
    #     difficulty="complex",
    #     expected_cross_links=2,
    # ),
    # CombinationTestCase(
    #     name="mental_health_support",
    #     prompt="Create a mental health support system that provides accessible, affordable, and effective care for diverse populations.",
    #     workflow_template="creative_problem_solver",
    #     expected_toolsets=["persona", "got", "reflection"],
    #     expected_transitions=[
    #         ("persona", "got"),
    #         ("got", "reflection"),
    #     ],
    #     min_storage_items=5,
    #     difficulty="complex",
    #     expected_cross_links=2,
    # ),
    # CombinationTestCase(
    #     name="urban_green_spaces",
    #     prompt="Design a strategy for increasing urban green spaces that addresses space constraints, maintenance costs, and community needs.",
    #     workflow_template="creative_problem_solver",
    #     expected_toolsets=["persona", "got", "reflection"],
    #     expected_transitions=[
    #         ("persona", "got"),
    #         ("got", "reflection"),
    #     ],
    #     min_storage_items=5,
    #     difficulty="medium",
    #     expected_cross_links=1,
    # ),
]

# Strategic Decision Maker Cases
STRATEGIC_DECISION_MAKER_CASES = [
    CombinationTestCase(
        name="microservices_migration",
        prompt="Should a company migrate from monolith to microservices? Consider technical complexity, team structure, business needs, and timeline.",
        workflow_template="strategic_decision_maker",
        expected_toolsets=["persona_debate", "mcts", "reflection"],
        expected_transitions=[
            ("persona_debate", "mcts"),
            ("mcts", "reflection"),
        ],
        expected_prefixed_tools=["persona_debate_initiate_persona_debate", "mcts_simulate", "reflection_create_output"],
        min_storage_items=6,
        difficulty="complex",
        expected_cross_links=2,
    ),
    CombinationTestCase(
        name="inhouse_ai_team",
        prompt="Should we invest in building an in-house AI team or partner with external vendors? Evaluate cost, expertise, control, and strategic value.",
        workflow_template="strategic_decision_maker",
        expected_toolsets=["persona_debate", "mcts", "reflection"],
        expected_transitions=[
            ("persona_debate", "mcts"),
            ("mcts", "reflection"),
        ],
        min_storage_items=5,
        difficulty="medium",
        expected_cross_links=1,
    ),
    CombinationTestCase(
        name="acquisition_vs_retention",
        prompt="Should we prioritize user acquisition or user retention? Analyze market conditions, product maturity, and resource constraints.",
        workflow_template="strategic_decision_maker",
        expected_toolsets=["persona_debate", "mcts", "reflection"],
        expected_transitions=[
            ("persona_debate", "mcts"),
            ("mcts", "reflection"),
        ],
        min_storage_items=5,
        difficulty="medium",
        expected_cross_links=1,
    ),
    # CombinationTestCase(
    #     name="international_expansion",
    #     prompt="Should we expand to international markets now or wait? Consider market readiness, competition, regulatory challenges, and resource availability.",
    #     workflow_template="strategic_decision_maker",
    #     expected_toolsets=["persona_debate", "mcts", "reflection"],
    #     expected_transitions=[
    #         ("persona_debate", "mcts"),
    #         ("mcts", "reflection"),
    #     ],
    #     min_storage_items=5,
    #     difficulty="complex",
    #     expected_cross_links=2,
    # ),
    # CombinationTestCase(
    #     name="remote_work_permanent",
    #     prompt="Should we adopt a fully remote work model permanently? Evaluate productivity, culture, costs, and talent access.",
    #     workflow_template="strategic_decision_maker",
    #     expected_toolsets=["persona_debate", "mcts", "reflection"],
    #     expected_transitions=[
    #         ("persona_debate", "mcts"),
    #         ("mcts", "reflection"),
    #     ],
    #     min_storage_items=5,
    #     difficulty="medium",
    #     expected_cross_links=1,
    # ),
    # CombinationTestCase(
    #     name="product_pricing_strategy",
    #     prompt="Should we adopt a freemium model, subscription, or one-time purchase? Analyze market dynamics, customer behavior, and revenue potential.",
    #     workflow_template="strategic_decision_maker",
    #     expected_toolsets=["persona_debate", "mcts", "reflection"],
    #     expected_transitions=[
    #         ("persona_debate", "mcts"),
    #         ("mcts", "reflection"),
    #     ],
    #     min_storage_items=5,
    #     difficulty="medium",
    #     expected_cross_links=1,
    # ),
]

# Code Architect Cases
CODE_ARCHITECT_CASES = [
    CombinationTestCase(
        name="distributed_task_queue",
        prompt="Design the architecture for a distributed task queue system that handles millions of tasks per day with high reliability and low latency.",
        workflow_template="code_architect",
        expected_toolsets=["self_ask", "tot", "reflection", "todo"],
        expected_transitions=[
            ("self_ask", "tot"),
            ("tot", "reflection"),
            ("reflection", "todo"),
        ],
        expected_prefixed_tools=["self_ask_ask_main_question", "tot_create_node", "reflection_create_output", "todo_read_todos"],
        min_storage_items=7,
        difficulty="complex",
        expected_cross_links=3,
    ),
    CombinationTestCase(
        name="realtime_chat_application",
        prompt="Design a scalable real-time chat application supporting millions of concurrent users with message persistence, presence, and notifications.",
        workflow_template="code_architect",
        expected_toolsets=["self_ask", "tot", "reflection", "todo"],
        expected_transitions=[
            ("self_ask", "tot"),
            ("tot", "reflection"),
        ],
        min_storage_items=6,
        difficulty="complex",
        expected_cross_links=2,
    ),
    CombinationTestCase(
        name="multitenant_saas_platform",
        prompt="Create the architecture for a multi-tenant SaaS platform with data isolation, resource quotas, and tenant-specific customizations.",
        workflow_template="code_architect",
        expected_toolsets=["self_ask", "tot", "reflection", "todo"],
        expected_transitions=[
            ("self_ask", "tot"),
            ("tot", "reflection"),
        ],
        min_storage_items=6,
        difficulty="complex",
        expected_cross_links=2,
    ),
    # CombinationTestCase(
    #     name="ecommerce_microservices",
    #     prompt="Design a microservices architecture for an e-commerce platform handling product catalog, inventory, orders, payments, and recommendations.",
    #     workflow_template="code_architect",
    #     expected_toolsets=["self_ask", "tot", "reflection", "todo"],
    #     expected_transitions=[
    #         ("self_ask", "tot"),
    #         ("tot", "reflection"),
    #     ],
    #     min_storage_items=6,
    #     difficulty="complex",
    #     expected_cross_links=2,
    # ),
    # CombinationTestCase(
    #     name="data_pipeline_system",
    #     prompt="Plan the architecture for a data pipeline processing system that ingests, transforms, and stores terabytes of data daily with real-time analytics.",
    #     workflow_template="code_architect",
    #     expected_toolsets=["self_ask", "tot", "reflection", "todo"],
    #     expected_transitions=[
    #         ("self_ask", "tot"),
    #         ("tot", "reflection"),
    #     ],
    #     min_storage_items=6,
    #     difficulty="complex",
    #     expected_cross_links=2,
    # ),
    # CombinationTestCase(
    #     name="content_delivery_network",
    #     prompt="Design the architecture for a content delivery network (CDN) that efficiently distributes media content globally with caching and edge computing.",
    #     workflow_template="code_architect",
    #     expected_toolsets=["self_ask", "tot", "reflection", "todo"],
    #     expected_transitions=[
    #         ("self_ask", "tot"),
    #         ("tot", "reflection"),
    #     ],
    #     min_storage_items=6,
    #     difficulty="complex",
    #     expected_cross_links=2,
    # ),
]

# All combination cases
COMBINATION_CASES = (
    RESEARCH_ASSISTANT_CASES
    + CREATIVE_PROBLEM_SOLVER_CASES
    + STRATEGIC_DECISION_MAKER_CASES
    + CODE_ARCHITECT_CASES
)
