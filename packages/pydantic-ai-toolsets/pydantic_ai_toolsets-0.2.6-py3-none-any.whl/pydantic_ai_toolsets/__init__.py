"""Pydantic AI Toolsets - Collection of reasoning and agent toolsets.

This package provides a comprehensive set of toolsets for pydantic-ai agents,
including reasoning strategies, reflection techniques, and multi-agent capabilities.

Example:
    ```python
    from pydantic_ai import Agent
    from pydantic_ai_toolsets import create_cot_toolset, CoTStorage
    
    storage = CoTStorage()
    agent = Agent("openai:gpt-4", toolsets=[create_cot_toolset(storage)])
    result = await agent.run("Solve this problem step by step")
    ```
"""

__version__ = "0.2.6"


# Chain of Thought
from pydantic_ai_toolsets.toolsets.chain_of_thought_reasoning import *

# Reflection
from pydantic_ai_toolsets.toolsets.reflection import *

# Self-Ask
from pydantic_ai_toolsets.toolsets.self_ask import *

# Self-Refine
from pydantic_ai_toolsets.toolsets.self_refine import *

# Tree of Thought
from pydantic_ai_toolsets.toolsets.tree_of_thought_reasoning import *

# To-Do
from pydantic_ai_toolsets.toolsets.to_do import *

# Monte Carlo Tree Search
from pydantic_ai_toolsets.toolsets.monte_carlo_reasoning import *

# Graph of Thought
from pydantic_ai_toolsets.toolsets.graph_of_thought_reasoning import *

# Beam Search
from pydantic_ai_toolsets.toolsets.beam_search_reasoning import *

# Multi-Persona Analysis
from pydantic_ai_toolsets.toolsets.multi_persona_analysis import *

# Multi-Persona Debate
from pydantic_ai_toolsets.toolsets.multi_persona_debate import *

# Search (optional - requires firecrawl)
try:
    from pydantic_ai_toolsets.toolsets.search import *
except ImportError:
    pass  # firecrawl not installed

# Meta-Orchestrator and Workflow Templates
from pydantic_ai_toolsets.toolsets.meta_orchestrator import (
    CODE_ARCHITECT,
    CREATIVE_PROBLEM_SOLVER,
    MetaOrchestratorStorage,
    RESEARCH_ASSISTANT,
    STRATEGIC_DECISION_MAKER,
    WorkflowTemplate,
    create_combined_toolset,
    create_meta_orchestrator_toolset,
    create_workflow_agent,
    get_template,
    list_templates,
    register_toolsets_with_orchestrator,
)

__all__ = [
    "ADD_PERSONA_RESPONSE_DESCRIPTION",
    "AGGREGATE_NODES_DESCRIPTION",
    "AGREE_WITH_POSITION_DESCRIPTION",
    "ANSWER_QUESTION_DESCRIPTION",
    "ASK_MAIN_QUESTION_DESCRIPTION",
    "ASK_SUB_QUESTION_DESCRIPTION",
    "AddPersonaResponseItem",
    "AggregateItem",
    "AgreeWithPositionItem",
    "Answer",
    "AnswerQuestionItem",
    "AskMainQuestionItem",
    "AskSubQuestionItem",
    "BACKPROPAGATE_DESCRIPTION",
    "BEAM_SYSTEM_PROMPT",
    "BEAM_TOOL_DESCRIPTION",
    "BackpropagateItem",
    "BeamCandidate",
    "BeamStep",
    "BeamStorage",
    "BeamStorageProtocol",
    "BranchEvaluation",
    "BranchEvaluationItem",
    "COMPOSE_FINAL_ANSWER_DESCRIPTION",
    "COT_SYSTEM_PROMPT",
    "COT_TOOL_DESCRIPTION",
    "CREATE_CANDIDATE_DESCRIPTION",
    "CREATE_EDGE_DESCRIPTION",
    "CREATE_NODE_DESCRIPTION",
    "CREATE_OUTPUT_DESCRIPTION",
    "CREATE_PERSONA_DESCRIPTION",
    "CRITIQUE_OUTPUT_DESCRIPTION",
    "CRITIQUE_POSITION_DESCRIPTION",
    "CoTStorage",
    "CoTStorageProtocol",
    "ComposeFinalAnswerItem",
    "CreateCandidateItem",
    "CreateOutputItem",
    "CreatePersonaItem",
    "CritiqueOutputItem",
    "CritiquePositionItem",
    "DEFEND_POSITION_DESCRIPTION",
    "DefendPositionItem",
    "EVALUATE_BRANCH_DESCRIPTION",
    "EVALUATE_NODE_DESCRIPTION",
    "EXPAND_CANDIDATE_DESCRIPTION",
    "EXPAND_NODE_DESCRIPTION",
    "EXTRACT_WEB_CONTENT_DESCRIPTION",
    "EdgeItem",
    "ExpandCandidateItem",
    "ExpandNodeItem",
    "ExtractWebContentItem",
    "ExtractedContent",
    "FIND_PATH_DESCRIPTION",
    "Feedback",
    "FeedbackDimension",
    "FeedbackItem",
    "FeedbackType",
    "FinalAnswer",
    "GENERATE_OUTPUT_DESCRIPTION",
    "GET_BEST_ACTION_DESCRIPTION",
    "GET_BEST_OUTPUT_DESCRIPTION",
    "GET_BEST_PATH_DESCRIPTION",
    "GET_FINAL_ANSWER_DESCRIPTION",
    "GOT_SYSTEM_PROMPT",
    "GOT_TOOL_DESCRIPTION",
    "GenerateOutputItem",
    "GoTStorage",
    "GoTStorageProtocol",
    "GraphEdge",
    "GraphNode",
    "INITIATE_PERSONA_DEBATE_DESCRIPTION",
    "INITIATE_PERSONA_SESSION_DESCRIPTION",
    "InitiatePersonaDebateItem",
    "InitiatePersonaSessionItem",
    "MAX_DEPTH",
    "MCTSNode",
    "MCTSStorage",
    "MCTSStorageProtocol",
    "MCTS_SYSTEM_PROMPT",
    "MCTS_TOOL_DESCRIPTION",
    "MERGE_INSIGHTS_DESCRIPTION",
    "NodeEvaluation",
    "NodeEvaluationItem",
    "NodeItem",
    "ORCHESTRATE_ROUND_DESCRIPTION",
    "OrchestrateRoundItem",
    "OutputFormat",
    "PERSONA_DEBATE_SYSTEM_PROMPT",
    "PERSONA_DEBATE_TOOL_DESCRIPTION",
    "PERSONA_SYSTEM_PROMPT",
    "PERSONA_TOOL_DESCRIPTION",
    "PROPOSE_POSITION_DESCRIPTION",
    "PROVIDE_FEEDBACK_DESCRIPTION",
    "PRUNE_BEAM_DESCRIPTION",
    "PRUNE_BRANCH_DESCRIPTION",
    "PRUNE_NODE_DESCRIPTION",
    "Persona",
    "PersonaAgreement",
    "PersonaCritique",
    "PersonaDebateSession",
    "PersonaDebateStorage",
    "PersonaDebateStorageProtocol",
    "PersonaPosition",
    "PersonaResponse",
    "PersonaSession",
    "PersonaStorage",
    "PersonaStorageProtocol",
    "ProposePositionItem",
    "ProvideFeedbackItem",
    "PruneBeamItem",
    "Question",
    "QuestionStatus",
    "READ_BEAM_DESCRIPTION",
    "READ_GRAPH_DESCRIPTION",
    "READ_MCTS_DESCRIPTION",
    "READ_PERSONAS_DESCRIPTION",
    "READ_PERSONA_DEBATE_DESCRIPTION",
    "READ_REFINEMENT_STATE_DESCRIPTION",
    "READ_REFLECTION_DESCRIPTION",
    "READ_SELF_ASK_STATE_DESCRIPTION",
    "READ_THOUGHTS_DESCRIPTION",
    "READ_TODO_DESCRIPTION",
    "READ_TREE_DESCRIPTION",
    "REFINE_NODE_DESCRIPTION",
    "REFINE_OUTPUT_DESCRIPTION",
    "REFLECTION_SYSTEM_PROMPT",
    "REFLECTION_TOOL_DESCRIPTION",
    "RESOLVE_DEBATE_DESCRIPTION",
    "RefineItem",
    "RefineOutputItem",
    "RefinementOutput",
    "ReflectionOutput",
    "ReflectionStorage",
    "ReflectionStorageProtocol",
    "ResolveDebateItem",
    "SCORE_CANDIDATE_DESCRIPTION",
    "SEARCH_SYSTEM_PROMPT",
    "SEARCH_TOOL_DESCRIPTION",
    "SEARCH_WEB_DESCRIPTION",
    "SELECT_NODE_DESCRIPTION",
    "SELF_ASK_SYSTEM_PROMPT",
    "SELF_REFINE_SYSTEM_PROMPT",
    "SELF_REFINE_TOOL_DESCRIPTION",
    "SIMULATE_DESCRIPTION",
    "SYNTHESIZE_DESCRIPTION",
    "ScoreCandidateItem",
    "SearchResult",
    "SearchStorage",
    "SearchStorageProtocol",
    "SearchWebItem",
    "SelectNodeItem",
    "SelfAskStorage",
    "SelfAskStorageProtocol",
    "SelfRefineStorage",
    "SelfRefineStorageProtocol",
    "SimulateItem",
    "SynthesizeItem",
    "TODO_SYSTEM_PROMPT",
    "TODO_TOOL_DESCRIPTION",
    "TOT_SYSTEM_PROMPT",
    "TOT_TOOL_DESCRIPTION",
    "Thought",
    "ThoughtItem",
    "ThoughtNode",
    "ToTStorage",
    "ToTStorageProtocol",
    "Todo",
    "TodoItem",
    "TodoStorage",
    "TodoStorageProtocol",
    "WRITE_THOUGHTS_DESCRIPTION",
    "calculate_ucb1",
    "create_beam_toolset",
    "create_cot_toolset",
    "create_got_toolset",
    "create_mcts_toolset",
    "create_persona_debate_toolset",
    "create_persona_toolset",
    "create_reflection_toolset",
    "create_search_toolset",
    "create_self_ask_toolset",
    "create_self_refine_toolset",
    "create_todo_toolset",
    "create_tot_toolset",
    "get_beam_system_prompt",
    "get_cot_system_prompt",
    "get_got_system_prompt",
    "get_mcts_system_prompt",
    "get_persona_debate_system_prompt",
    "get_persona_system_prompt",
    "get_reflection_system_prompt",
    "get_search_system_prompt",
    "get_self_ask_system_prompt",
    "get_self_refine_system_prompt",
    "get_todo_system_prompt",
    "get_tot_system_prompt",
    # Meta-Orchestrator
    "CODE_ARCHITECT",
    "CREATIVE_PROBLEM_SOLVER",
    "MetaOrchestratorStorage",
    "RESEARCH_ASSISTANT",
    "STRATEGIC_DECISION_MAKER",
    "WorkflowTemplate",
    "create_combined_toolset",
    "create_meta_orchestrator_toolset",
    "create_workflow_agent",
    "get_template",
    "list_templates",
    "register_toolsets_with_orchestrator",
]
