"""Persona debate toolset for pydantic-ai agents."""

from __future__ import annotations

import sys
import time
import uuid
from typing import Any

from pydantic_ai import Agent
from pydantic_ai.toolsets import FunctionToolset

from .storage import (
    PersonaDebateStorage,
    PersonaDebateStorageProtocol,
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

# =============================================================================
# SYSTEM PROMPT - Contains "when and why" to use the toolset
# =============================================================================

PERSONA_DEBATE_SYSTEM_PROMPT = """
## Persona Debate

You have access to tools for managing structured debates between multiple personas:
- `read_persona_debate`: Read current debate state
- `initiate_persona_debate`: Start a new debate session
- `create_persona`: Create a persona with specific expertise and viewpoint
- `propose_position`: Propose your initial position as a persona
- `critique_position`: Critique another persona's position with logical reasoning
- `agree_with_position`: Agree with another persona's position (with reasoning)
- `defend_position`: Defend and strengthen your position against critiques
- `orchestrate_round`: Orchestrate a debate round with multiple personas
- `resolve_debate`: Resolve the debate with synthesis, winner, or consensus (FINAL STEP)

### When to Use Persona Debate

Use these tools in these scenarios:
1. Complex decisions requiring diverse expert perspectives
2. Problems where multiple viewpoints need structured argumentation
3. Situations where personas can both agree and disagree based on logic
4. Tasks where coalition-building and consensus formation are valuable
5. Problems requiring evidence-based evaluation from different experts

### Debate Process

1. **Initiate**: Start a debate session with a topic
2. **Create Personas**: Define 3-6 personas with distinct viewpoints
3. **Propose**: Personas propose initial positions (round 0-1)
4. **Critique**: Personas critique opposing positions with logic
5. **Agree**: Personas can agree with positions they support (with reasoning)
6. **Defend**: Personas defend and strengthen their positions
7. **Orchestrate**: Manage rounds of argumentation (2-5 rounds typical)
8. **Resolve**: Synthesize views, select winner, or find consensus

### Key Features

- **Personas**: Each persona has distinct expertise, thinking style, or stakeholder perspective
- **Agreement**: Personas can agree with each other's positions (not just refute)
- **Logic-Based**: All critiques and agreements must be supported by logical reasoning
- **Flexible**: Personas can form coalitions or disagree based on their perspectives

### Workflow

1. Call `read_persona_debate` to see current state
2. If no debate exists, use `initiate_persona_debate` to start one
3. Create personas using `create_persona` (typically 3-6 personas)
4. Propose positions using `propose_position` (if round 0-1)
5. Critique opposing positions using `critique_position`
6. Agree with positions using `agree_with_position` (with reasoning)
7. Defend your position using `defend_position`
8. Use `orchestrate_round` to manage multi-persona interactions
9. **STOP** and resolve using `resolve_debate` when:
   - Max rounds reached (status is "completed")
   - You have enough information to make a judgment
   - The user requests resolution

### Stopping Conditions

The debate MUST end when:
- Max rounds are reached (status becomes "completed")
- A resolution is provided via `resolve_debate` (status becomes "resolved")
- Once resolved or completed, do NOT continue debating except `read_persona_debate` or `resolve_debate`

**IMPORTANT**: Always call `read_persona_debate` before proposing, critiquing, defending, or agreeing.
"""

# =============================================================================
# TOOL DESCRIPTIONS - Contains "how" to use each specific tool
# =============================================================================

READ_PERSONA_DEBATE_DESCRIPTION = """Read the current persona debate state.

Returns session info, personas, positions, critiques, agreements, and round status.

Precondition: Call before every propose_position, critique_position, defend_position, or agree_with_position.
"""

INITIATE_PERSONA_DEBATE_DESCRIPTION = """Initiate a new persona debate session.

Parameters:
- topic: Debate topic/question
- max_rounds: Maximum rounds (typically 3-5)

Returns session ID and setup confirmation.

Precondition: Call read_persona_debate first to check if debate exists.
"""

CREATE_PERSONA_DESCRIPTION = """Create a persona with specific expertise and viewpoint.

Parameters:
- name: Persona name
- expertise: Areas of expertise
- viewpoint: Perspective/viewpoint
- thinking_style: How this persona thinks

Returns persona ID and confirmation.

Precondition: Call read_persona_debate first.
"""

PROPOSE_POSITION_DESCRIPTION = """Propose your initial position as a persona.

Parameters:
- persona_id: Your persona ID
- position_content: Your position/argument

Returns position ID and round info.

Precondition: Call read_persona_debate first. Use in rounds 0-1.
"""

CRITIQUE_POSITION_DESCRIPTION = """Critique another persona's position with logical reasoning.

Parameters:
- persona_id: Your persona ID
- target_position_id: Position to critique
- critique_points: List of specific critique points with logical reasoning

Returns critique ID and summary.

Precondition: Call read_persona_debate first.
"""

AGREE_WITH_POSITION_DESCRIPTION = """Agree with another persona's position (with reasoning).

Parameters:
- persona_id: Your persona ID
- position_id: Position to agree with
- reasoning: Why your persona agrees

Returns agreement ID and summary.

Precondition: Call read_persona_debate first.
"""

DEFEND_POSITION_DESCRIPTION = """Defend and strengthen your position against critiques.

Parameters:
- persona_id: Your persona ID
- position_id: Your position to defend
- defense_content: Defense addressing critiques

Returns updated position info.

Precondition: Call read_persona_debate first.
"""

ORCHESTRATE_ROUND_DESCRIPTION = """Orchestrate a debate round with multiple personas.

Parameters:
- round_plan: Plan for the round (which personas speak, order)
- persona_actions: List of actions for each persona

Returns round summary and updated state.

Precondition: Call read_persona_debate first.
"""

RESOLVE_DEBATE_DESCRIPTION = """Resolve the debate with synthesis, winner, or consensus.

Parameters:
- resolution_type: synthesis, winner, or consensus
- resolution_content: Complete resolution (2-3 paragraphs)
- winner_persona_id: Winner persona ID (for winner type)

FINAL STEP - Call once when debate should end.

Precondition: Call read_persona_debate first.
"""

# Legacy constant for backward compatibility
PERSONA_DEBATE_TOOL_DESCRIPTION = PROPOSE_POSITION_DESCRIPTION

READ_PERSONA_DEBATE_DESCRIPTION = """
Read the current persona debate state.

**CRITICAL**: Call this BEFORE every propose_position, critique_position, defend_position, or agree_with_position call to:
- Review the current debate state and round
- See existing personas, positions, critiques, and agreements
- Understand which personas have spoken and what they've said
- Know what critiques you need to address
- Make informed decisions about your next move

Returns:
- Current debate session (topic, round, status)
- All personas with their descriptions and expertise
- All positions with their content and rounds
- All critiques with their targets and points
- All agreements with their targets and reasoning
- Summary of debate progress
"""

INITIATE_PERSONA_DEBATE_DESCRIPTION = """
Initiate a new persona debate session.

Use this tool to start a debate on a topic. This creates the debate session
and sets up the structure for personas, positions, critiques, and agreements.

When initiating:
- Set max_rounds based on complexity (typically 3-5 rounds)
- The debate will start at round 0 with status "active"
"""

CREATE_PERSONA_DESCRIPTION = """
Create a new persona for the debate.

Use this tool to define a persona with specific expertise, background, and perspective.
Create 3-6 personas typically, representing diverse viewpoints.

**CRITICAL**: Call read_persona_debate first to see existing personas and avoid duplicates.

When creating personas:
- Choose appropriate persona_type:
  - expert: Domain specialists (e.g., Clinical Doctor, UX Designer, Data Scientist)
  - thinking_style: Cognitive approaches (e.g., Analytical, Intuitive, Risk-Averse)
  - stakeholder: Interested parties (e.g., Employee, Manager, Executive)
- Provide detailed description of their background, expertise, and perspective
- List specific expertise areas
- Ensure diversity - personas should have distinct viewpoints
"""

PROPOSE_POSITION_DESCRIPTION = """
Propose an initial position in the debate as a persona.

Use this tool to present your initial argument from your persona's unique perspective.
This should be done in rounds 0-1, before extensive critique begins.

**CRITICAL**: Call read_persona_debate first to see current state and ensure it's the right round.

When proposing:
- This should be your initial position (rounds 0-1)
- Make a clear, well-reasoned argument from your persona's perspective
- Include evidence if relevant
- Your persona_id must match an existing persona
"""

CRITIQUE_POSITION_DESCRIPTION = """
Critique another persona's position with logical reasoning.

Use this tool to challenge an opponent's position by identifying weaknesses,
questioning assumptions, or pointing out flaws with logical reasoning.

**CRITICAL**: Call read_persona_debate first to see which positions exist to critique.

When critiquing:
- Target a specific position by its position_id
- Be specific about weaknesses (logical errors, missing evidence, etc.)
- Provide concrete points that can be addressed
- Use logical reasoning - explain why the position is flawed
- Your persona_id must match an existing persona
"""

AGREE_WITH_POSITION_DESCRIPTION = """
Agree with another persona's position, providing reasoning.

Use this tool to express agreement with a position made by another persona.
This allows coalition-building and consensus formation.

**CRITICAL**: Call read_persona_debate first to see which positions exist to agree with.

When agreeing:
- Target a specific position by its position_id
- Explain why your persona agrees with this position
- Provide specific reasoning points
- This allows personas to form coalitions based on logic
- Your persona_id must match an existing persona
"""

DEFEND_POSITION_DESCRIPTION = """
Defend and strengthen a position against critiques.

Use this tool to respond to critiques raised against your position and
strengthen your argument with additional reasoning or evidence.

**CRITICAL**: Call read_persona_debate first to see critiques against your position.

When defending:
- Reference the position_id you're defending
- If there are critiques, address them by including their critique_ids in critiques_addressed
- If there are no critiques yet, you can still strengthen your position (critiques_addressed can be empty)
- Provide additional reasoning or evidence
- Strengthen your argument beyond just responding to critiques
- Your persona_id must match the persona who created the original position
"""

ORCHESTRATE_ROUND_DESCRIPTION = """
Orchestrate a debate round with multiple personas.

Use this tool to manage a round of debate where multiple personas interact.
This creates agents for each persona and manages their turn-taking.

**CRITICAL**: Call read_persona_debate first to see current debate state.

When orchestrating:
- Specify the round_number to orchestrate
- Personas will be created automatically as agents
- Each persona will critique opponents, agree with allies, and defend their positions
- The round will advance automatically
"""

RESOLVE_DEBATE_DESCRIPTION = """
Resolve the debate with synthesis, winner selection, or consensus.

Use this tool to conclude the debate by either:
- Synthesis: Combine best elements from all positions
- Winner: Select a winning persona based on argument strength
- Consensus: Find points where personas reached agreement

**CRITICAL**: Call read_persona_debate first to review all positions, critiques, and agreements.

**IMPORTANT**: This tool directly resolves the debate. Do NOT call this tool recursively.
Provide your resolution directly in resolution_content and related fields.

When resolving:
- Choose appropriate resolution_type
- Provide clear reasoning in resolution_content (this is your final judgment)
- For winner: specify the winner_persona_id
- For synthesis: list elements from different positions in synthesis_elements
- For consensus: list points where agreement was found in consensus_points
- The debate will be marked as resolved after calling this tool once
"""


def create_persona_debate_toolset(
    storage: PersonaDebateStorageProtocol | None = None,
    *,
    id: str | None = None,
    agent_model: str | None = None,
    agent_configs: dict[str, dict[str, Any]] | None = None,
    auto_orchestrate: bool = False,
    track_usage: bool = False,
) -> FunctionToolset[Any]:
    """Create a persona debate toolset for multi-persona structured debates.

    This toolset provides tools for AI agents to engage in structured debates
    between multiple personas, with support for creating and orchestrating
    multiple agent instances.

    Args:
        storage: Optional storage backend. Defaults to in-memory PersonaDebateStorage.
            You can provide a custom storage implementing PersonaDebateStorageProtocol
            for persistence or integration with other systems.
        id: Optional unique ID for the toolset.
        agent_model: Default model string for creating agents (e.g., "openai:gpt-4").
            Required if agent_configs not provided or if auto_orchestrate=True.
        agent_configs: Per-persona agent configurations:
            {
                "persona_id_1": {"model": "openai:gpt-4", "system_prompt": "..."},
                "persona_id_2": {"model": "openai:gpt-4", "system_prompt": "..."},
            }
        auto_orchestrate: If True, tools automatically orchestrate agent interactions.

    Returns:
        FunctionToolset compatible with any pydantic-ai agent.

    Example (standalone):
        ```python
        from pydantic_ai import Agent
        from pydantic_ai_toolsets import create_persona_debate_toolset

        agent = Agent("openai:gpt-4", toolsets=[create_persona_debate_toolset()])
        result = await agent.run("Debate: Should we adopt microservices?")
        ```

    Example (with multi-agent orchestration):
        ```python
        from pydantic_ai_toolsets import create_persona_debate_toolset, PersonaDebateStorage

        storage = PersonaDebateStorage()
        toolset = create_persona_debate_toolset(
            storage=storage,
            agent_model="openai:gpt-4",
            auto_orchestrate=True,
        )

        orchestrator = Agent("openai:gpt-4", toolsets=[toolset])
        result = await orchestrator.run("Start a debate on microservices")
        ```
    """
    if storage is not None:
        _storage = storage
    else:
        _storage = PersonaDebateStorage(track_usage=track_usage)

    # Store agent configs in closure for tools to use
    _agent_model = agent_model
    _agent_configs = agent_configs or {}
    _auto_orchestrate = auto_orchestrate

    # Cache for agent instances (by persona_id)
    _agent_cache: dict[str, Agent] = {}

    # Flag to prevent recursive resolution calls
    _resolving: bool = False

    toolset: FunctionToolset[Any] = FunctionToolset(id=id)
    _metrics = getattr(_storage, "metrics", None) if hasattr(_storage, "metrics") else None

    # Create restricted toolset for persona agents
    # They should NOT have access to orchestration tools
    persona_toolset: FunctionToolset[Any] = FunctionToolset(id=f"{id}_persona" if id else None)

    def _get_status_summary() -> str:
        """Get one-line status summary."""
        if not _storage.session:
            return "Status: ○ No session"
        session = _storage.session
        personas = len(_storage.personas)
        positions = len(_storage.positions)
        if session.status == "resolved":
            winner = _storage.personas.get(session.winner_persona_id)
            winner_name = winner.name if winner else "N/A"
            return f"Status: ✓ Resolved | Winner: {winner_name}"
        return f"Status: ● Active | Round {session.current_round}/{session.max_rounds}, {personas} personas"

    def _get_next_hint() -> str:
        """Get contextual hint for next action."""
        if not _storage.session:
            return "Use initiate_persona_debate to start a debate."
        session = _storage.session
        if session.status == "resolved":
            return "Debate resolved. Review resolution and winner."
        if not _storage.personas:
            return "Use create_debate_persona to add debate participants (2-4 personas)."
        if not _storage.positions:
            return "Use propose_position to have each persona present their argument."
        if session.current_round >= session.max_rounds:
            return "Max rounds reached. Use resolve_persona_debate to determine winner."
        # Check for positions without critiques
        positions_with_critiques = {c.target_position_id for c in _storage.critiques.values()}
        current_positions = [p for p in _storage.positions.values() if p.round_number == session.current_round]
        uncritiqued = [p for p in current_positions if p.position_id not in positions_with_critiques]
        if uncritiqued:
            return f"Use critique_position to challenge [{uncritiqued[0].position_id[:8]}...]."
        return "Use propose_position for rebuttal, agree_with_position, or resolve_persona_debate."

    def _read_debate_state() -> str:
        """Helper function to read debate state (used by tools and internally)."""
        if not _storage.session:
            return f"{_get_status_summary()}\n\nNo active persona debate session.\n\nNext: {_get_next_hint()}"

        session = _storage.session
        lines: list[str] = [_get_status_summary(), "", "Persona Debate State:"]
        lines.append("")
        lines.append(f"Topic: {session.topic}")
        lines.append(f"Round: {session.current_round} / {session.max_rounds}")
        lines.append(f"Status: {session.status}")
        if session.resolution:
            lines.append(f"Resolution: {session.resolution}")
        if session.winner_persona_id:
            winner_persona = _storage.personas.get(session.winner_persona_id)
            winner_name = winner_persona.name if winner_persona else session.winner_persona_id
            lines.append(f"Winner: {winner_name}")
        lines.append("")

        # Display personas
        if _storage.personas:
            lines.append(f"Personas ({len(_storage.personas)}):")
            for persona in _storage.personas.values():
                lines.append(
                    f"  [{persona.persona_id[:8]}...] {persona.name} ({persona.persona_type})"
                )
                if persona.expertise_areas:
                    lines.append(f"    Expertise: {', '.join(persona.expertise_areas)}")
                lines.append(f"    {persona.description[:100]}...")
            lines.append("")

        # Display positions by round
        positions_by_round: dict[int, list[PersonaPosition]] = {}
        for position in _storage.positions.values():
            if position.round_number not in positions_by_round:
                positions_by_round[position.round_number] = []
            positions_by_round[position.round_number].append(position)

        if positions_by_round:
            lines.append("Positions by Round:")
            for round_num in sorted(positions_by_round.keys()):
                positions = positions_by_round[round_num]
                lines.append(f"  Round {round_num}:")
                for position in positions:
                    persona = _storage.personas.get(position.persona_id)
                    persona_name = persona.name if persona else position.persona_id
                    parent_str = (
                        f" (defends [{position.parent_position_id[:8]}...])"
                        if position.parent_position_id
                        else ""
                    )
                    evidence_str = (
                        f" [Evidence: {len(position.evidence)} citations]"
                        if position.evidence
                        else ""
                    )
                    lines.append(
                        f"    Position ID: {position.position_id} | "
                        f"[{position.position_id[:8]}...] {persona_name}{parent_str}{evidence_str}"
                    )
                    lines.append(f"      {position.content[:150]}...")
                    if position.critiques_addressed:
                        lines.append(
                            f"      Addresses critiques: {', '.join([c[:8] + '...' for c in position.critiques_addressed])}"
                        )
                lines.append("")

        # Display critiques
        if _storage.critiques:
            lines.append("Critiques:")
            critiques_by_round: dict[int, list[PersonaCritique]] = {}
            for critique in _storage.critiques.values():
                if critique.round_number not in critiques_by_round:
                    critiques_by_round[critique.round_number] = []
                critiques_by_round[critique.round_number].append(critique)

            for round_num in sorted(critiques_by_round.keys()):
                critiques = critiques_by_round[round_num]
                lines.append(f"  Round {round_num}:")
                for critique in critiques:
                    persona = _storage.personas.get(critique.persona_id)
                    persona_name = persona.name if persona else critique.persona_id
                    target = _storage.positions.get(critique.target_position_id)
                    target_ref = (
                        f"[{critique.target_position_id[:8]}...]"
                        if target
                        else f"[{critique.target_position_id[:8]}...] (missing)"
                    )
                    lines.append(
                        f"    [{critique.critique_id[:8]}...] {persona_name} critiques {target_ref}"
                    )
                    lines.append(f"      {critique.content[:150]}...")
                    if critique.specific_points:
                        lines.append("      Points:")
                        for point in critique.specific_points[:3]:  # Show first 3
                            lines.append(f"        - {point}")
                lines.append("")

        # Display agreements
        if _storage.agreements:
            lines.append("Agreements:")
            agreements_by_round: dict[int, list[PersonaAgreement]] = {}
            for agreement in _storage.agreements.values():
                if agreement.round_number not in agreements_by_round:
                    agreements_by_round[agreement.round_number] = []
                agreements_by_round[agreement.round_number].append(agreement)

            for round_num in sorted(agreements_by_round.keys()):
                agreements = agreements_by_round[round_num]
                lines.append(f"  Round {round_num}:")
                for agreement in agreements:
                    persona = _storage.personas.get(agreement.persona_id)
                    persona_name = persona.name if persona else agreement.persona_id
                    target = _storage.positions.get(agreement.target_position_id)
                    target_ref = (
                        f"[{agreement.target_position_id[:8]}...]"
                        if target
                        else f"[{agreement.target_position_id[:8]}...] (missing)"
                    )
                    lines.append(
                        f"    [{agreement.agreement_id[:8]}...] "
                        f"{persona_name} agrees with {target_ref}"
                    )
                    lines.append(f"      {agreement.content[:150]}...")
                    if agreement.reasoning:
                        lines.append("      Reasoning:")
                        for reason in agreement.reasoning[:3]:  # Show first 3
                            lines.append(f"        - {reason}")
                lines.append("")

        # Summary
        total_positions = len(_storage.positions)
        total_critiques = len(_storage.critiques)
        total_agreements = len(_storage.agreements)
        total_personas = len(_storage.personas)

        lines.append("Summary:")
        lines.append(f"  Total personas: {total_personas}")
        lines.append(f"  Total positions: {total_positions}")
        lines.append(f"  Total critiques: {total_critiques}")
        lines.append(f"  Total agreements: {total_agreements}")
        
        # List all position IDs for easy reference
        if _storage.positions:
            lines.append("\nAll Position IDs (use these exact IDs in tool calls):")
            for position in _storage.positions.values():
                persona = _storage.personas.get(position.persona_id)
                persona_name = persona.name if persona else position.persona_id
                lines.append(f"  - {position.position_id} (Round {position.round_number}, {persona_name})")

        lines.append("")
        lines.append(f"Next: {_get_next_hint()}")

        return "\n".join(lines)

    def _create_agent_for_persona(persona_id: str) -> Agent:
        """Create an agent instance for a specific persona."""
        # Check cache first
        if persona_id in _agent_cache:
            return _agent_cache[persona_id]

        # Get persona-specific config or use defaults
        persona_config = _agent_configs.get(persona_id, {})
        model = persona_config.get("model") or _agent_model

        if not model:
            raise ValueError(
                f"No model configured for persona '{persona_id}'. "
                "Provide agent_model or agent_configs with model for each persona."
            )

        # Persona agents get restricted toolset (no orchestration)
        agent_toolset = persona_toolset
        persona = _storage.personas.get(persona_id)
        persona_name = persona.name if persona else persona_id
        default_prompt = (
            f"You are {persona_name}. Your persona_id is '{persona_id}'. "
            "Use persona debate tools to participate in structured debates. "
            "You can use: read_persona_debate, propose_position, critique_position, agree_with_position, and defend_position. "
            f"**CRITICAL**: Always use persona_id='{persona_id}' in all tool calls that require it. "
            "Do NOT use orchestrate_round, initiate_persona_debate, or resolve_debate - those are for the orchestrator only."
        )

        # Create agent with appropriate toolset (shared storage!)
        agent = Agent(
            model,
            toolsets=[agent_toolset],
            system_prompt=persona_config.get("system_prompt", default_prompt),
        )

        # Cache the agent
        _agent_cache[persona_id] = agent
        return agent

    @toolset.tool(description=READ_PERSONA_DEBATE_DESCRIPTION)
    async def read_persona_debate() -> str:
        """Read the current persona debate state."""
        start_time = time.perf_counter()
        result = _read_debate_state()
        if _metrics is not None:
            duration_ms = (time.perf_counter() - start_time) * 1000
            _metrics.record_invocation("read_persona_debate", "", result, duration_ms)
        return result

    # Add read_persona_debate to persona toolset
    @persona_toolset.tool(description=READ_PERSONA_DEBATE_DESCRIPTION)
    async def read_persona_debate_persona() -> str:
        """Read the current persona debate state."""
        start_time = time.perf_counter()
        result = _read_debate_state()
        if _metrics is not None:
            duration_ms = (time.perf_counter() - start_time) * 1000
            _metrics.record_invocation("read_persona_debate", "", result, duration_ms)
        return result

    @toolset.tool(description=INITIATE_PERSONA_DEBATE_DESCRIPTION)
    async def initiate_persona_debate(debate: InitiatePersonaDebateItem) -> str:
        """Initiate a new persona debate session."""
        start_time = time.perf_counter()
        input_text = debate.model_dump_json() if _metrics else ""

        if _storage.session and _storage.session.status == "active":
            return (
                f"Debate already active: {_storage.session.topic}. "
                "Use read_persona_debate to see current state, or resolve current debate first."
            )

        session = PersonaDebateSession(
            debate_id=str(uuid.uuid4()),
            topic=debate.topic,
            max_rounds=debate.max_rounds,
            current_round=0,
            status="active",
        )
        _storage.session = session

        result = (
            f"Persona debate initiated: {debate.topic}\n"
            f"Max rounds: {debate.max_rounds}\n"
            f"Status: active\n\n"
            "Use create_persona to add personas, then propose_position to present initial positions (rounds 0-1)."
        )

        if _metrics is not None:
            duration_ms = (time.perf_counter() - start_time) * 1000
            _metrics.record_invocation("initiate_persona_debate", input_text, result, duration_ms)

        return result

    @toolset.tool(description=CREATE_PERSONA_DESCRIPTION)
    async def create_persona(item: CreatePersonaItem) -> str:
        """Create a new persona for the debate."""
        start_time = time.perf_counter()
        input_text = item.model_dump_json() if _metrics else ""

        if _storage.session is None:
            return "No active debate session. Use initiate_persona_debate first."

        persona_id = str(uuid.uuid4())
        persona = Persona(
            persona_id=persona_id,
            name=item.name,
            persona_type=item.persona_type,
            description=item.description,
            expertise_areas=item.expertise_areas,
        )
        _storage.personas = persona
        result = (
            f"Created persona [{persona_id}] {persona.name} ({persona.persona_type})\n"
            f"Expertise: {', '.join(persona.expertise_areas) if persona.expertise_areas else 'None'}"
        )

        if _metrics is not None:
            duration_ms = (time.perf_counter() - start_time) * 1000
            _metrics.record_invocation("create_persona", input_text, result, duration_ms)

        return result

    @toolset.tool(description=PROPOSE_POSITION_DESCRIPTION)
    @persona_toolset.tool(description=PROPOSE_POSITION_DESCRIPTION)
    async def propose_position(position: ProposePositionItem) -> str:
        """Propose an initial position in the debate."""
        start_time = time.perf_counter()
        input_text = position.model_dump_json() if _metrics else ""

        session = _storage.session
        if not session:
            return "No active debate. Use initiate_persona_debate first."

        if session.status == "resolved":
            return (
                f"Debate is already resolved: {session.resolution}\n"
                "Cannot propose new positions. The debate is complete."
            )

        if session.status == "completed":
            return (
                f"Debate has reached max rounds ({session.max_rounds}). "
                "Cannot propose new positions. Use resolve_debate to conclude the debate."
            )

        if session.status != "active":
            return f"Debate is {session.status}. Cannot propose positions."

        # Check if max rounds reached
        if session.current_round >= session.max_rounds:
            session.status = "completed"
            return (
                f"Debate has reached max rounds ({session.max_rounds}). "
                "Cannot propose new positions. Use resolve_debate to conclude the debate."
            )

        # Validate persona exists
        if position.persona_id not in _storage.personas:
            return (
                f"Persona '{position.persona_id}' not found. "
                "Call read_persona_debate to see available personas, or create_persona to add one."
            )

        # Validate round (positions typically in rounds 0-1)
        if session.current_round > 1:
            return (
                f"Round {session.current_round} is too late for initial positions. "
                "Use defend_position to strengthen existing positions instead."
            )

        position_id = str(uuid.uuid4())
        new_position = PersonaPosition(
            position_id=position_id,
            persona_id=position.persona_id,
            round_number=session.current_round,
            content=position.content,
            evidence=position.evidence,
            critiques_addressed=[],
            parent_position_id=None,
        )

        _storage.positions = new_position

        persona = _storage.personas[position.persona_id]
        result = (
            f"Position [{position_id[:8]}...] proposed by {persona.name} "
            f"in round {session.current_round}"
        )

        if _metrics is not None:
            duration_ms = (time.perf_counter() - start_time) * 1000
            _metrics.record_invocation("propose_position", input_text, result, duration_ms)

        return result

    @toolset.tool(description=CRITIQUE_POSITION_DESCRIPTION)
    @persona_toolset.tool(description=CRITIQUE_POSITION_DESCRIPTION)
    async def critique_position(critique: CritiquePositionItem) -> str:
        """Critique another persona's position with logical reasoning."""
        start_time = time.perf_counter()
        input_text = critique.model_dump_json() if _metrics else ""

        session = _storage.session
        if not session:
            return "No active debate. Use initiate_persona_debate first."

        if session.status == "resolved":
            return (
                f"Debate is already resolved: {session.resolution}\n"
                "Cannot critique positions. The debate is complete."
            )

        if session.status == "completed":
            return (
                f"Debate has reached max rounds ({session.max_rounds}). "
                "Cannot critique positions. Use resolve_debate to conclude the debate."
            )

        if session.status != "active":
            return f"Debate is {session.status}. Cannot critique positions."

        # Check if max rounds reached
        if session.current_round >= session.max_rounds:
            session.status = "completed"
            return (
                f"Debate has reached max rounds ({session.max_rounds}). "
                "Cannot critique positions. Use resolve_debate to conclude the debate."
            )

        # Validate persona exists
        if critique.persona_id not in _storage.personas:
            return (
                f"Persona '{critique.persona_id}' not found. "
                "Call read_persona_debate to see available personas."
            )

        # Validate target exists
        target = _storage.positions.get(critique.target_position_id)
        if not target:
            available_ids = ", ".join([pos.position_id for pos in _storage.positions.values()])
            return (
                f"Position '{critique.target_position_id}' not found. "
                f"Available position IDs: {available_ids}. "
                "Call read_persona_debate to see all positions with their full IDs."
            )

        # Validate not critiquing own position
        if critique.persona_id == target.persona_id:
            return (
                f"Cannot critique your own position. "
                f"You are {critique.persona_id}, target position is from the same persona. "
                "Critique other personas' positions only."
            )

        critique_id = str(uuid.uuid4())
        new_critique = PersonaCritique(
            critique_id=critique_id,
            target_position_id=critique.target_position_id,
            persona_id=critique.persona_id,
            round_number=session.current_round,
            content=critique.content,
            specific_points=critique.specific_points,
        )

        _storage.critiques = new_critique

        persona = _storage.personas[critique.persona_id]
        result = (
            f"Critique [{critique_id[:8]}...] created by {persona.name} "
            f"targeting position [{critique.target_position_id[:8]}...] "
            f"in round {session.current_round}"
        )

        if _metrics is not None:
            duration_ms = (time.perf_counter() - start_time) * 1000
            _metrics.record_invocation("critique_position", input_text, result, duration_ms)

        return result

    @toolset.tool(description=AGREE_WITH_POSITION_DESCRIPTION)
    @persona_toolset.tool(description=AGREE_WITH_POSITION_DESCRIPTION)
    async def agree_with_position(agreement: AgreeWithPositionItem) -> str:
        """Agree with another persona's position, providing reasoning."""
        start_time = time.perf_counter()
        input_text = agreement.model_dump_json() if _metrics else ""

        session = _storage.session
        if not session:
            return "No active debate. Use initiate_persona_debate first."

        if session.status == "resolved":
            return (
                f"Debate is already resolved: {session.resolution}\n"
                "Cannot agree with positions. The debate is complete."
            )

        if session.status == "completed":
            return (
                f"Debate has reached max rounds ({session.max_rounds}). "
                "Cannot agree with positions. Use resolve_debate to conclude the debate."
            )

        if session.status != "active":
            return f"Debate is {session.status}. Cannot agree with positions."

        # Check if max rounds reached
        if session.current_round >= session.max_rounds:
            session.status = "completed"
            return (
                f"Debate has reached max rounds ({session.max_rounds}). "
                "Cannot agree with positions. Use resolve_debate to conclude the debate."
            )

        # Validate persona exists
        if agreement.persona_id not in _storage.personas:
            return (
                f"Persona '{agreement.persona_id}' not found. "
                "Call read_persona_debate to see available personas."
            )

        # Validate target exists
        target = _storage.positions.get(agreement.target_position_id)
        if not target:
            available_ids = ", ".join([pos.position_id for pos in _storage.positions.values()])
            return (
                f"Position '{agreement.target_position_id}' not found. "
                f"Available position IDs: {available_ids}. "
                "Call read_persona_debate to see all positions with their full IDs."
            )

        # Can agree with own position (strengthening) or others (coalition-building)
        agreement_id = str(uuid.uuid4())
        new_agreement = PersonaAgreement(
            agreement_id=agreement_id,
            target_position_id=agreement.target_position_id,
            persona_id=agreement.persona_id,
            round_number=session.current_round,
            content=agreement.content,
            reasoning=agreement.reasoning,
        )

        _storage.agreements = new_agreement

        persona = _storage.personas[agreement.persona_id]
        target_persona = _storage.personas.get(target.persona_id)
        target_name = target_persona.name if target_persona else target.persona_id
        result = (
            f"Agreement [{agreement_id[:8]}...] created by {persona.name} "
            f"agreeing with {target_name}'s position [{agreement.target_position_id[:8]}...] "
            f"in round {session.current_round}"
        )

        if _metrics is not None:
            duration_ms = (time.perf_counter() - start_time) * 1000
            _metrics.record_invocation("agree_with_position", input_text, result, duration_ms)

        return result

    @toolset.tool(description=DEFEND_POSITION_DESCRIPTION)
    @persona_toolset.tool(description=DEFEND_POSITION_DESCRIPTION)
    async def defend_position(defense: DefendPositionItem) -> str:
        """Defend and strengthen a position against critiques."""
        start_time = time.perf_counter()
        input_text = defense.model_dump_json() if _metrics else ""

        session = _storage.session
        if not session:
            return "No active debate. Use initiate_persona_debate first."

        if session.status == "resolved":
            return (
                f"Debate is already resolved: {session.resolution}\n"
                "Cannot defend positions. The debate is complete."
            )

        if session.status == "completed":
            return (
                f"Debate has reached max rounds ({session.max_rounds}). "
                "Cannot defend positions. Use resolve_debate to conclude the debate."
            )

        if session.status != "active":
            return f"Debate is {session.status}. Cannot defend positions."

        # Check if max rounds reached (before advancing round)
        if session.current_round >= session.max_rounds:
            session.status = "completed"
            return (
                f"Debate has reached max rounds ({session.max_rounds}). "
                "Cannot defend positions. Use resolve_debate to conclude the debate."
            )

        # Validate persona exists
        if defense.persona_id not in _storage.personas:
            return (
                f"Persona '{defense.persona_id}' not found. "
                "Call read_persona_debate to see available personas."
            )

        # Validate position exists
        original = _storage.positions.get(defense.position_id)
        if not original:
            return (
                f"Position '{defense.position_id}' not found. "
                "Call read_persona_debate to see available positions."
            )

        # Validate persona matches
        if defense.persona_id != original.persona_id:
            return (
                f"Persona mismatch. Position is from {original.persona_id}, "
                f"but defense is from {defense.persona_id}."
            )

        # Validate critiques exist (if any are provided)
        if defense.critiques_addressed:
            for critique_id in defense.critiques_addressed:
                if critique_id not in _storage.critiques:
                    return (
                        f"Critique '{critique_id}' not found. "
                        "Call read_persona_debate to see available critiques."
                    )

        # Create new position (defense) as child of original
        position_id = str(uuid.uuid4())
        new_position = PersonaPosition(
            position_id=position_id,
            persona_id=defense.persona_id,
            round_number=session.current_round + 1,
            content=defense.content,
            evidence=defense.evidence,
            critiques_addressed=defense.critiques_addressed,
            parent_position_id=defense.position_id,
        )

        _storage.positions = new_position

        # Advance round
        session.current_round = new_position.round_number

        # Check if max rounds reached after advancing
        if session.current_round >= session.max_rounds:
            session.status = "completed"

        persona = _storage.personas[defense.persona_id]
        critiques_str = (
            f"addressing {len(defense.critiques_addressed)} critique(s)"
            if defense.critiques_addressed
            else "strengthening the position"
        )
        result = (
            f"Position [{position_id[:8]}...] defended by {persona.name} "
            f"in round {new_position.round_number}, {critiques_str}"
        )

        if session.status == "completed":
            result += "\n\nDebate reached max rounds. Consider resolving the debate."

        if _metrics is not None:
            duration_ms = (time.perf_counter() - start_time) * 1000
            _metrics.record_invocation("defend_position", input_text, result, duration_ms)

        return result

    @toolset.tool(description=ORCHESTRATE_ROUND_DESCRIPTION)
    async def orchestrate_round(orchestration: OrchestrateRoundItem) -> str:
        """Manually orchestrate a debate round."""
        start_time = time.perf_counter()
        input_text = orchestration.model_dump_json() if _metrics else ""

        session = _storage.session
        if not session:
            return "No active debate. Use initiate_persona_debate first."

        if session.status == "resolved":
            return (
                f"Debate is already resolved: {session.resolution}\n"
                "Cannot orchestrate more rounds. The debate is complete."
            )

        if session.status == "completed":
            return (
                f"Debate has reached max rounds ({session.max_rounds}). "
                "Cannot orchestrate more rounds. Use resolve_debate to conclude the debate."
            )

        if session.status != "active":
            return f"Debate is {session.status}. Cannot orchestrate."

        if not _agent_model:
            return (
                "No agent_model configured. Provide agent_model or agent_configs "
                "to enable orchestration."
            )

        round_num = orchestration.round_number

        # Check if requested round exceeds max rounds
        if round_num >= session.max_rounds:
            session.status = "completed"
            return (
                f"Cannot orchestrate round {round_num}. "
                f"Debate max rounds is {session.max_rounds}. "
                "Use resolve_debate to conclude the debate."
            )

        if round_num <= session.current_round:
            return (
                f"Round {round_num} already completed (current: {session.current_round}). "
                "Orchestrate a future round."
            )

        if not _storage.personas:
            return "No personas created. Use create_persona to add personas first."

        results: list[str] = []

        # Update round number BEFORE agents participate so tools use correct round
        session.current_round = round_num
        if round_num >= session.max_rounds:
            session.status = "completed"

        # Get current debate state
        debate_state = _read_debate_state()

        # Create agents for each persona and have them participate
        for persona_id, persona in _storage.personas.items():
            try:
                agent = _create_agent_for_persona(persona_id)
                # Get list of all position IDs for this persona's reference
                all_position_ids = [pos.position_id for pos in _storage.positions.values()]
                position_ids_str = ", ".join(all_position_ids) if all_position_ids else "None"
                
                prompt = (
                    f"{debate_state}\n\n"
                    f"You are {persona.name} ({persona.persona_type}) in round {round_num}. "
                    f"**YOUR PERSONA_ID IS: {persona_id}** - You MUST use this exact ID when calling tools.\n"
                    f"Your expertise: {', '.join(persona.expertise_areas) if persona.expertise_areas else 'General'}\n"
                    f"Your perspective: {persona.description}\n\n"
                    f"**CRITICAL**: All available position IDs are: {position_ids_str}\n"
                    "You MUST use the FULL position_id (not truncated) when calling tools.\n"
                    "The debate state above shows positions with format 'Position ID: <full_id> | [<truncated>...]' - use the FULL ID.\n\n"
                    "Review the debate and participate by:\n"
                    f"- Using critique_position with persona_id='{persona_id}' and target_position_id='<FULL_POSITION_ID>' to critique positions you disagree with\n"
                    f"- Using agree_with_position with persona_id='{persona_id}' and target_position_id='<FULL_POSITION_ID>' to agree with positions you support\n"
                    f"- Using defend_position with persona_id='{persona_id}' and position_id='<FULL_POSITION_ID>' to defend your own positions against critiques\n\n"
                    f"**CRITICAL**: Always use persona_id='{persona_id}' and the FULL position_id (not truncated) in all tool calls!"
                )
                result = await agent.run(prompt)
                results.append(f"{persona.name} round {round_num}: {str(result)[:200]}...")
            except Exception as e:
                results.append(f"{persona.name} round {round_num}: Error - {e}")

        # Round already updated above, but ensure status is correct
        if round_num >= session.max_rounds:
            session.status = "completed"
            results.append("\nDebate reached max rounds. Consider resolving.")

        result = "\n".join(results)

        if _metrics is not None:
            duration_ms = (time.perf_counter() - start_time) * 1000
            _metrics.record_invocation("orchestrate_round", input_text, result, duration_ms)

        return result

    @toolset.tool(description=RESOLVE_DEBATE_DESCRIPTION)
    async def resolve_debate(resolution: ResolveDebateItem) -> str:
        """Resolve the debate with synthesis, winner selection, or consensus."""
        start_time = time.perf_counter()
        input_text = resolution.model_dump_json() if _metrics else ""
        nonlocal _resolving

        session = _storage.session
        if not session:
            return "No active debate to resolve."

        if session.status == "resolved":
            return (
                f"Debate already resolved: {session.resolution}\n"
                f"Winner: {session.winner_persona_id or 'None'}\n"
                "The debate cannot be resolved again."
            )

        # Validate debate is ready for resolution
        if session.status != "active" and session.status != "completed":
            return (
                f"Debate status is '{session.status}'. "
                "Can only resolve debates that are 'active' or 'completed'."
            )

        # Validate resolution content is provided
        if not resolution.resolution_content.strip():
            return (
                "resolution_content is required. "
                "Provide your evaluation, reasoning, or synthesis in resolution_content."
            )

        # Validate winner_persona_id for winner type
        if resolution.resolution_type == "winner":
            if not resolution.winner_persona_id:
                return (
                    "winner_persona_id is required for resolution_type='winner'. "
                    "Specify which persona won the debate."
                )
            if resolution.winner_persona_id not in _storage.personas:
                return (
                    f"Winner persona '{resolution.winner_persona_id}' not found. "
                    "Call read_persona_debate to see available personas."
                )

        # Update session - FINAL RESOLUTION
        session.status = "resolved"
        session.resolution = resolution.resolution_content
        session.winner_persona_id = resolution.winner_persona_id
        session.resolution_type = resolution.resolution_type

        result = (
            f"✅ Debate resolved ({resolution.resolution_type}):\n{resolution.resolution_content}"
        )
        if resolution.winner_persona_id:
            winner_persona = _storage.personas.get(resolution.winner_persona_id)
            winner_name = winner_persona.name if winner_persona else resolution.winner_persona_id
            result += f"\n🏆 Winner: {winner_name}"
        if resolution.synthesis_elements:
            result += f"\n📋 Synthesis elements: {', '.join(resolution.synthesis_elements)}"
        if resolution.consensus_points:
            result += f"\n🤝 Consensus points: {', '.join(resolution.consensus_points)}"

        if _metrics is not None:
            duration_ms = (time.perf_counter() - start_time) * 1000
            _metrics.record_invocation("resolve_debate", input_text, result, duration_ms)

        return result

    return toolset


def get_persona_debate_system_prompt() -> str:
    """Get the system prompt for persona debate-based reasoning.

    Returns:
        System prompt string that can be used with pydantic-ai agents.
    """
    return PERSONA_DEBATE_SYSTEM_PROMPT


def create_persona_debate_toolset_agent(model: str = "openrouter:x-ai/grok-4.1-fast") -> Agent:
    """Create a Pydantic-ai agent with the persona debate toolset.

    Args:
        model: The model to use for the agent.

    Returns:
        Pydantic-ai agent with the persona debate toolset.
    """
    storage = PersonaDebateStorage()
    toolset = create_persona_debate_toolset(storage=storage)
    agent = Agent(
        model,
        system_prompt="""
        You are a persona debate agent. You have access to tools for managing structured debates between personas:
        - `read_persona_debate`: Read the current debate state
        - `initiate_persona_debate`: Start a new debate session
        - `create_persona`: Create a persona with specific expertise
        - `propose_position`: Propose your initial position as a persona
        - `critique_position`: Critique another persona's position
        - `agree_with_position`: Agree with another persona's position
        - `defend_position`: Defend and strengthen your position
        - `orchestrate_round`: Orchestrate a debate round
        - `resolve_debate`: Resolve the debate with synthesis, winner, or consensus

        **IMPORTANT**: Use these tools to engage in structured debates between multiple personas.
        """,
        toolsets=[toolset]
    )

    @agent.instructions
    async def add_prompt() -> str:
        """Add the persona debate system prompt."""
        return get_persona_debate_system_prompt()

    return agent
