"""Multi-persona toolset for pydantic-ai agents.

Provides multi-persona analysis capabilities for AI agents through diverse
viewpoints and perspectives. Compatible with any pydantic-ai agent - no specific deps required.

Example:
    ```python
    from pydantic_ai import Agent
    from pydantic_ai_toolsets import create_persona_toolset, PersonaStorage

    # Simple usage
    agent = Agent("openai:gpt-4", toolsets=[create_persona_toolset()])
    result = await agent.run("Analyze: Should we invest in this startup?")

    # With storage access
    storage = PersonaStorage()
    toolset = create_persona_toolset(storage=storage)

    # After agent runs, access persona state directly
    print(storage.session)
    print(storage.personas)
    print(storage.responses)
    ```
"""

from .storage import PersonaStorage, PersonaStorageProtocol
from .toolset import (
    ADD_PERSONA_RESPONSE_DESCRIPTION,
    CREATE_PERSONA_DESCRIPTION,
    INITIATE_PERSONA_SESSION_DESCRIPTION,
    PERSONA_SYSTEM_PROMPT,
    PERSONA_TOOL_DESCRIPTION,
    READ_PERSONAS_DESCRIPTION,
    SYNTHESIZE_DESCRIPTION,
    create_persona_toolset,
    get_persona_system_prompt,
)
from .types import (
    AddPersonaResponseItem,
    CreatePersonaItem,
    InitiatePersonaSessionItem,
    Persona,
    PersonaResponse,
    PersonaSession,
    SynthesizeItem,
)

__all__ = [
    # Main factory
    "create_persona_toolset",
    "get_persona_system_prompt",
    # Types
    "Persona",
    "PersonaResponse",
    "PersonaSession",
    "CreatePersonaItem",
    "AddPersonaResponseItem",
    "SynthesizeItem",
    "InitiatePersonaSessionItem",
    # Storage
    "PersonaStorage",
    "PersonaStorageProtocol",
    # Constants (for customization)
    "PERSONA_TOOL_DESCRIPTION",
    "PERSONA_SYSTEM_PROMPT",
    "READ_PERSONAS_DESCRIPTION",
    "INITIATE_PERSONA_SESSION_DESCRIPTION",
    "CREATE_PERSONA_DESCRIPTION",
    "ADD_PERSONA_RESPONSE_DESCRIPTION",
    "SYNTHESIZE_DESCRIPTION",
]

__version__ = "0.2.7"

