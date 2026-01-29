"""Persona debate toolset for pydantic-ai agents.

Provides structured debate capabilities between multiple personas for AI agents through
multi-persona argumentation. Compatible with any pydantic-ai agent - no specific deps required.

Example:
    ```python
    from pydantic_ai import Agent
    from pydantic_ai_toolsets import create_persona_debate_toolset, PersonaDebateStorage

    # Simple usage
    agent = Agent("openai:gpt-4", toolsets=[create_persona_debate_toolset()])
    result = await agent.run("Debate: Should we adopt microservices?")

    # With multi-agent orchestration
    storage = PersonaDebateStorage()
    toolset = create_persona_debate_toolset(
        storage=storage,
        agent_model="openai:gpt-4",
        auto_orchestrate=True,
    )

    orchestrator = Agent("openai:gpt-4", toolsets=[toolset])
    result = await orchestrator.run("Start a debate on microservices")
    print(storage.session)  # Access debate state directly
    ```
"""

from .storage import (
    PersonaDebateStorage,
    PersonaDebateStorageProtocol,
)
from .toolset import (
    AGREE_WITH_POSITION_DESCRIPTION,
    CREATE_PERSONA_DESCRIPTION,
    CRITIQUE_POSITION_DESCRIPTION,
    DEFEND_POSITION_DESCRIPTION,
    INITIATE_PERSONA_DEBATE_DESCRIPTION,
    ORCHESTRATE_ROUND_DESCRIPTION,
    PERSONA_DEBATE_SYSTEM_PROMPT,
    PERSONA_DEBATE_TOOL_DESCRIPTION,
    PROPOSE_POSITION_DESCRIPTION,
    READ_PERSONA_DEBATE_DESCRIPTION,
    RESOLVE_DEBATE_DESCRIPTION,
    create_persona_debate_toolset,
    get_persona_debate_system_prompt,
)
from .types import (
    AgreeWithPositionItem,
    CreatePersonaItem,
    CritiquePositionItem,
    DefendPositionItem,
    InitiatePersonaDebateItem,
    OrchestrateRoundItem,
    Persona,
    PersonaAgreement,
    PersonaCritique,
    PersonaDebateSession,
    PersonaPosition,
    ProposePositionItem,
    ResolveDebateItem,
)

__all__ = [
    # Main factory
    "create_persona_debate_toolset",
    "get_persona_debate_system_prompt",
    # Types
    "Persona",
    "PersonaPosition",
    "PersonaCritique",
    "PersonaAgreement",
    "PersonaDebateSession",
    "CreatePersonaItem",
    "ProposePositionItem",
    "CritiquePositionItem",
    "AgreeWithPositionItem",
    "DefendPositionItem",
    "ResolveDebateItem",
    "InitiatePersonaDebateItem",
    "OrchestrateRoundItem",
    # Storage
    "PersonaDebateStorage",
    "PersonaDebateStorageProtocol",
    # Constants (for customization)
    "PERSONA_DEBATE_TOOL_DESCRIPTION",
    "PERSONA_DEBATE_SYSTEM_PROMPT",
    "READ_PERSONA_DEBATE_DESCRIPTION",
    "INITIATE_PERSONA_DEBATE_DESCRIPTION",
    "CREATE_PERSONA_DESCRIPTION",
    "PROPOSE_POSITION_DESCRIPTION",
    "CRITIQUE_POSITION_DESCRIPTION",
    "AGREE_WITH_POSITION_DESCRIPTION",
    "DEFEND_POSITION_DESCRIPTION",
    "ORCHESTRATE_ROUND_DESCRIPTION",
    "RESOLVE_DEBATE_DESCRIPTION",
]

__version__ = "0.1.0"
