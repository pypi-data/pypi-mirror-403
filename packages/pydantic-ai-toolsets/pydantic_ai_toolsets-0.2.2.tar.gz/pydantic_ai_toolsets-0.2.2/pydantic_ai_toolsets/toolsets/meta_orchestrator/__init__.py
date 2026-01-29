"""Meta-orchestrator toolset for pydantic-ai agents.

Provides workflow orchestration and multi-toolset coordination capabilities for AI agents.
Compatible with any pydantic-ai agent - no specific deps required.

Example:
    ```python
    from pydantic_ai import Agent
    from pydantic_ai_toolsets import create_meta_orchestrator_toolset, MetaOrchestratorStorage

    # Simple usage
    agent = Agent("openai:gpt-4.1", toolsets=[create_meta_orchestrator_toolset()])

    # With storage access
    storage = MetaOrchestratorStorage()
    agent = Agent("openai:gpt-4.1", toolsets=[create_meta_orchestrator_toolset(storage)])
    result = await agent.run("Start a research assistant workflow")
    workflow = storage.get_active_workflow()
    print(workflow.current_stage)
    ```
"""

from .helpers import (
    create_combined_toolset,
    create_workflow_agent,
    register_toolsets_with_orchestrator,
)
from .storage import MetaOrchestratorStorage, MetaOrchestratorStorageProtocol, WorkflowRegistry
from .toolset import (
    GET_WORKFLOW_STATUS_DESCRIPTION,
    LINK_TOOLSET_OUTPUTS_DESCRIPTION,
    META_ORCHESTRATOR_SYSTEM_PROMPT,
    READ_UNIFIED_STATE_DESCRIPTION,
    START_WORKFLOW_DESCRIPTION,
    SUGGEST_TRANSITION_DESCRIPTION,
    create_meta_orchestrator_toolset,
    get_meta_orchestrator_system_prompt,
)
from .types import (
    CrossToolsetLink,
    GetWorkflowStatusItem,
    LinkToolsetOutputsItem,
    LinkType,
    Stage,
    StartWorkflowItem,
    SuggestTransitionItem,
    ToolsetTransition,
    WorkflowState,
    WorkflowTemplate,
)
from .workflow_templates import (
    ALL_TEMPLATES,
    CODE_ARCHITECT,
    CREATIVE_PROBLEM_SOLVER,
    RESEARCH_ASSISTANT,
    STRATEGIC_DECISION_MAKER,
    TEMPLATE_BY_NAME,
    get_template,
    list_templates,
)

__all__ = [
    # Main factory
    "create_meta_orchestrator_toolset",
    "get_meta_orchestrator_system_prompt",
    # Helper functions
    "create_combined_toolset",
    "create_workflow_agent",
    "register_toolsets_with_orchestrator",
    # Types
    "WorkflowState",
    "WorkflowTemplate",
    "Stage",
    "ToolsetTransition",
    "CrossToolsetLink",
    "LinkType",
    "StartWorkflowItem",
    "SuggestTransitionItem",
    "LinkToolsetOutputsItem",
    "GetWorkflowStatusItem",
    # Storage
    "MetaOrchestratorStorage",
    "MetaOrchestratorStorageProtocol",
    "WorkflowRegistry",
    # Workflow Templates
    "RESEARCH_ASSISTANT",
    "CREATIVE_PROBLEM_SOLVER",
    "STRATEGIC_DECISION_MAKER",
    "CODE_ARCHITECT",
    "ALL_TEMPLATES",
    "TEMPLATE_BY_NAME",
    "get_template",
    "list_templates",
    # Constants (for customization)
    "META_ORCHESTRATOR_SYSTEM_PROMPT",
    "READ_UNIFIED_STATE_DESCRIPTION",
    "SUGGEST_TRANSITION_DESCRIPTION",
    "START_WORKFLOW_DESCRIPTION",
    "LINK_TOOLSET_OUTPUTS_DESCRIPTION",
    "GET_WORKFLOW_STATUS_DESCRIPTION",
]

__version__ = "0.1.0"
