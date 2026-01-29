"""Beam search toolset for pydantic-ai agents.

Provides beam search reasoning exploration capabilities for AI agents.
Compatible with any pydantic-ai agent - no specific deps required.

Example:
    ```python
    from pydantic_ai import Agent
    from pydantic_ai_toolsets import create_beam_toolset, BeamStorage

    # Simple usage
    agent = Agent("openai:gpt-4.1", toolsets=[create_beam_toolset()])

    # With storage access
    storage = BeamStorage()
    agent = Agent("openai:gpt-4.1", toolsets=[create_beam_toolset(storage)])
    result = await agent.run("Solve this problem using beam search")
    print(storage.candidates)  # Access candidates directly
    print(storage.steps)  # Access steps directly

    # With usage tracking
    storage = BeamStorage(track_usage=True)
    agent = Agent("openai:gpt-4.1", toolsets=[create_beam_toolset(storage)])
    print(storage.metrics.total_tokens())
    ```
"""

from .storage import BeamStorage, BeamStorageProtocol
from .toolset import (
    BEAM_SYSTEM_PROMPT,
    BEAM_TOOL_DESCRIPTION,
    CREATE_CANDIDATE_DESCRIPTION,
    EXPAND_CANDIDATE_DESCRIPTION,
    GET_BEST_PATH_DESCRIPTION,
    PRUNE_BEAM_DESCRIPTION,
    READ_BEAM_DESCRIPTION,
    SCORE_CANDIDATE_DESCRIPTION,
    create_beam_toolset,
    get_beam_system_prompt,
)
from .types import (
    BeamCandidate,
    BeamStep,
    CreateCandidateItem,
    ExpandCandidateItem,
    PruneBeamItem,
    ScoreCandidateItem,
)

__all__ = [
    # Main factory
    "create_beam_toolset",
    "get_beam_system_prompt",
    # Types
    "BeamCandidate",
    "BeamStep",
    "CreateCandidateItem",
    "ExpandCandidateItem",
    "PruneBeamItem",
    "ScoreCandidateItem",
    # Storage
    "BeamStorage",
    "BeamStorageProtocol",
    # Constants (for customization)
    "BEAM_TOOL_DESCRIPTION",
    "BEAM_SYSTEM_PROMPT",
    "READ_BEAM_DESCRIPTION",
    "CREATE_CANDIDATE_DESCRIPTION",
    "EXPAND_CANDIDATE_DESCRIPTION",
    "SCORE_CANDIDATE_DESCRIPTION",
    "PRUNE_BEAM_DESCRIPTION",
    "GET_BEST_PATH_DESCRIPTION",
]

__version__ = "0.1.0"
