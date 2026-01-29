"""Multi-persona toolset for pydantic-ai agents."""

from __future__ import annotations

import time
import uuid
from typing import Any

from pydantic_ai import Agent
from pydantic_ai.toolsets import FunctionToolset

from .storage import PersonaStorage, PersonaStorageProtocol
from .types import (
    AddPersonaResponseItem,
    CreatePersonaItem,
    InitiatePersonaSessionItem,
    Persona,
    PersonaResponse,
    PersonaSession,
    SynthesizeItem,
)

PERSONA_TOOL_DESCRIPTION = """
Use this toolset to analyze problems from multiple distinct personas or viewpoints.
This helps you:
- Adopt different expert personas, thinking styles, or stakeholder perspectives
- Generate diverse insights from each persona
- Synthesize perspectives into comprehensive solutions
- Engage in interactive dialogue between personas
- Use devil's advocate patterns for robust solutions

## Workflow

**CRITICAL**: Before adding responses or synthesizing, you MUST call read_personas first!
This ensures you:
- Understand the current session state
- See existing personas and their responses
- Know the process type and round
- Make informed decisions about your next move

## When to Use This Toolset

Use Multi-Personas in these scenarios:
1. Complex problems requiring diverse expertise
2. Decisions needing multiple stakeholder perspectives
3. Problems where different thinking styles improve outcomes
4. Situations where role-playing different experts is valuable
5. Tasks requiring comprehensive analysis from multiple angles

## Process Types

1. **Sequential Consultation**: Each persona provides independent analysis, then synthesis
2. **Interactive Dialogue**: Personas engage in discussion, responding to each other
3. **Devil's Advocate**: Primary persona generates solution, skeptic challenges it

## Persona Types

- **Expert Personas**: Domain specialists (e.g., Clinical Doctor, UX Designer, Data Scientist)
- **Thinking Style Personas**: Cognitive approaches (e.g., Analytical, Intuitive, Risk-Averse)
- **Stakeholder Personas**: Interested parties (e.g., Employee, Manager, Executive)
"""

PERSONA_SYSTEM_PROMPT = """
## Multi-Persona Analysis

You have access to tools for managing multi-persona analysis sessions:
- `read_personas`: Read the current session state and all personas/responses
- `initiate_persona_session`: Start a new persona analysis session
- `create_persona`: Create a new persona with specific expertise
- `add_persona_response`: Add a response from a persona
- `synthesize`: Synthesize all persona responses into a comprehensive solution

**CRITICAL**: You MUST actively use these tools to participate in persona analysis. Do NOT just answer directly.
Instead, use the tools to create personas, gather their perspectives, and synthesize insights.

**IMPORTANT**: Before adding responses or synthesizing, ALWAYS call `read_personas` first to:
- Review the current session state
- See existing personas and responses
- Understand the process type and round
- Make informed decisions about your next move

**STOPPING CONDITIONS**: The session MUST end when:
- Max rounds are reached (status becomes "completed")
- A synthesis is provided via `synthesize` (status becomes "synthesized")
- Once synthesized, do NOT continue adding responses except `read_personas`

Required Workflow:
1. Call `read_personas` to see current state
2. If no session exists, use `initiate_persona_session` to start one
3. Create personas using `create_persona` (typically 3-6 personas)
4. Add responses from each persona using `add_persona_response`
5. For interactive/devils_advocate: Continue dialogue across rounds
6. **STOP** and synthesize using `synthesize` when:
   - All personas have provided initial responses (sequential)
   - Sufficient dialogue has occurred (interactive)
   - Solution has been refined through challenge (devils_advocate)
   - Max rounds reached
   - The user requests synthesis

When creating personas:
- Choose appropriate persona_type (expert, thinking_style, stakeholder)
- Provide detailed descriptions of their background and perspective
- List specific expertise areas

When adding responses:
- Each persona should provide analysis from their unique perspective
- For interactive: reference other responses using references field
- For devils_advocate: skeptic persona should challenge primary persona's solution

When synthesizing:
- Combine insights from all personas
- Identify commonalities and conflicts
- Resolve tensions between perspectives
- Provide comprehensive solution addressing all viewpoints
"""

READ_PERSONAS_DESCRIPTION = """
Read the current persona session state.

**CRITICAL**: Call this BEFORE every add_persona_response or synthesize call to:
- Review the current session state and round
- See existing personas and their responses
- Understand the process type
- Know which personas have responded
- Make informed decisions about your next move

Returns:
- Current session (problem, process_type, round, status)
- All personas with their descriptions and expertise
- All responses organized by persona and round
- Summary of session progress
"""

INITIATE_PERSONA_SESSION_DESCRIPTION = """
Initiate a new persona analysis session.

Use this tool to start a persona analysis on a problem or question. This creates
the session and sets up the structure for personas and responses.

When initiating:
- Choose an appropriate process_type for the problem:
  - sequential: Each persona provides independent analysis, then synthesis
  - interactive: Personas engage in dialogue, responding to each other
  - devils_advocate: Primary persona generates solution, skeptic challenges it
- Set max_rounds based on complexity (typically 3-5 rounds for interactive/devils_advocate)
- The session will start at round 0 with status "active"
"""

CREATE_PERSONA_DESCRIPTION = """
Create a new persona for the session.

Use this tool to define a persona with specific expertise, background, and perspective.
Create 3-6 personas typically, representing diverse viewpoints.

**CRITICAL**: Call read_personas first to see existing personas and avoid duplicates.

When creating personas:
- Choose appropriate persona_type:
  - expert: Domain specialists (e.g., Clinical Doctor, UX Designer, Data Scientist)
  - thinking_style: Cognitive approaches (e.g., Analytical, Intuitive, Risk-Averse)
  - stakeholder: Interested parties (e.g., Employee, Manager, Executive)
- Provide detailed description of their background, expertise, and perspective
- List specific expertise areas
- Ensure diversity - personas should have distinct viewpoints
"""

ADD_PERSONA_RESPONSE_DESCRIPTION = """
Add a response from a persona.

Use this tool to capture a persona's analysis, insights, or perspective on the problem.

**CRITICAL**: Call read_personas first to see current state and which personas have responded.

When adding responses:
- Reference the persona_id of the persona providing the response
- Provide analysis from that persona's unique perspective
- For sequential: Each persona provides independent analysis
- For interactive: Reference other responses using references field to engage in dialogue
- For devils_advocate: 
  - Primary persona generates solution
  - Skeptic persona challenges assumptions and finds weaknesses
  - Primary persona defends and refines
"""

SYNTHESIZE_DESCRIPTION = """
Synthesize all persona responses into a comprehensive solution.

Use this tool to combine insights from all personas, identify commonalities and conflicts,
and produce a final synthesis addressing all perspectives.

**CRITICAL**: Call read_personas first to review all personas and responses.

**IMPORTANT**: This tool directly synthesizes the session. Do NOT call this tool recursively.
Provide your synthesis directly in synthesis_content, key_insights, and conflicts_resolved fields.

When synthesizing:
- Combine insights from all personas into a coherent solution
- Identify key insights from each persona
- Resolve conflicts or tensions between perspectives
- Address all stakeholder concerns
- Provide comprehensive solution that incorporates diverse viewpoints
- The session will be marked as synthesized after calling this tool once
"""


def create_persona_toolset(
    storage: PersonaStorageProtocol | None = None,
    *,
    id: str | None = None,
    track_usage: bool = False,
) -> FunctionToolset[Any]:
    """Create a multi-persona toolset for diverse perspective analysis.

    This toolset provides tools for AI agents to adopt multiple personas and
    synthesize diverse perspectives on problems.

    Args:
        storage: Optional storage backend. Defaults to in-memory PersonaStorage.
            You can provide a custom storage implementing PersonaStorageProtocol
            for persistence or integration with other systems.
        id: Optional unique ID for the toolset.
        track_usage: If True, enables usage metrics collection in storage.

    Returns:
        FunctionToolset compatible with any pydantic-ai agent.

    Example (standalone):
        ```python
        from pydantic_ai import Agent
        from pydantic_ai_toolsets import create_persona_toolset

        agent = Agent("openai:gpt-4", toolsets=[create_persona_toolset()])
        result = await agent.run("Analyze: Should we invest in this startup?")
        ```

    Example (with storage access):
        ```python
        from pydantic_ai_toolsets import create_persona_toolset, PersonaStorage

        storage = PersonaStorage()
        toolset = create_persona_toolset(storage=storage)

        # After agent runs, access persona state directly
        print(storage.session)
        print(storage.personas)
        print(storage.responses)

        # With metrics tracking
        storage = PersonaStorage(track_usage=True)
        toolset = create_persona_toolset(storage=storage)
        print(storage.metrics.total_tokens())
        ```
    """
    if storage is not None:
        _storage = storage
    else:
        _storage = PersonaStorage(track_usage=track_usage)

    toolset: FunctionToolset[Any] = FunctionToolset(id=id)
    _metrics = getattr(_storage, "metrics", None) if hasattr(_storage, "metrics") else None

    def _get_status_summary() -> str:
        """Get one-line status summary."""
        if _storage.session is None:
            return "Status: ○ No session"
        session = _storage.session
        personas = len(_storage.personas)
        responses = len(_storage.responses)
        if session.status == "synthesized":
            return f"Status: ✓ Synthesized | {personas} personas, {responses} responses"
        if session.status == "completed":
            return f"Status: ● Completed | Round {session.current_round}/{session.max_rounds}"
        return f"Status: ● Active | Round {session.current_round}/{session.max_rounds}, {personas} personas"

    def _get_next_hint() -> str:
        """Get contextual hint for next action."""
        if _storage.session is None:
            return "Use initiate_persona_session to start a new session."
        session = _storage.session
        if session.status == "synthesized":
            return "Session synthesized. Review the synthesis in read_personas output."
        if not _storage.personas:
            return "Use create_persona to add personas (typically 3-6)."
        if session.status == "completed":
            return "Max rounds reached. Use synthesize to combine insights."
        # Check if all personas have responded in current round
        personas_responded = set()
        for r in _storage.responses.values():
            if r.round_number == session.current_round:
                personas_responded.add(r.persona_id)
        missing = [p for p in _storage.personas if p not in personas_responded]
        if missing:
            return f"Use add_persona_response for persona [{missing[0]}]."
        return "All personas responded. Continue dialogue or use synthesize."

    @toolset.tool(description=READ_PERSONAS_DESCRIPTION)
    async def read_personas() -> str:
        """Read the current persona session state."""
        start_time = time.perf_counter()

        if _storage.session is None:
            return f"{_get_status_summary()}\n\nNo persona session active.\n\nNext: {_get_next_hint()}"

        session = _storage.session
        lines = [
            _get_status_summary(),
            "",
            f"Persona Session: {session.session_id}",
            f"Problem: {session.problem}",
            f"Process Type: {session.process_type}",
            f"Status: {session.status}",
            f"Round: {session.current_round} / {session.max_rounds}",
        ]

        if session.synthesis:
            lines.append(f"Synthesis: {session.synthesis}")

        lines.append("")

        if not _storage.personas:
            lines.append("No personas created yet. Use create_persona to add personas.")
        else:
            lines.append(f"Personas ({len(_storage.personas)}):")
            for persona_id, persona in _storage.personas.items():
                lines.append(f"  [{persona_id}] {persona.name} ({persona.persona_type})")
                if persona.expertise_areas:
                    lines.append(f"    Expertise: {', '.join(persona.expertise_areas)}")
                lines.append(f"    Description: {persona.description}")
                lines.append("")

        if not _storage.responses:
            lines.append("No responses yet. Use add_persona_response to add responses.")
        else:
            lines.append(f"Responses ({len(_storage.responses)}):")
            # Group responses by persona
            by_persona: dict[str, list[PersonaResponse]] = {}
            for response in _storage.responses.values():
                if response.persona_id not in by_persona:
                    by_persona[response.persona_id] = []
                by_persona[response.persona_id].append(response)

            for persona_id, responses in by_persona.items():
                persona = _storage.personas.get(persona_id)
                persona_name = persona.name if persona else persona_id
                lines.append(f"  {persona_name} ({len(responses)} response(s)):")
                for response in sorted(responses, key=lambda r: (r.round_number, r.response_id)):
                    lines.append(f"    [Round {response.round_number}] {response.response_id}")
                    if response.references:
                        lines.append(f"      References: {', '.join(response.references)}")
                    lines.append(f"      {response.content}")
                    lines.append("")

        lines.append("")
        lines.append(f"Next: {_get_next_hint()}")

        result = "\n".join(lines)

        # Record metrics if tracking is enabled
        if _metrics is not None:
            duration_ms = (time.perf_counter() - start_time) * 1000
            _metrics.record_invocation("read_personas", "", result, duration_ms)

        return result

    @toolset.tool(description=INITIATE_PERSONA_SESSION_DESCRIPTION)
    async def initiate_persona_session(item: InitiatePersonaSessionItem) -> str:
        """Initiate a new persona analysis session."""
        start_time = time.perf_counter()
        input_text = item.model_dump_json() if _metrics else ""

        session_id = str(uuid.uuid4())
        session = PersonaSession(
            session_id=session_id,
            problem=item.problem,
            process_type=item.process_type,
            max_rounds=item.max_rounds,
            current_round=0,
            status="active",
        )
        _storage.session = session
        result = (
            f"Initiated persona session {session_id} on problem: {item.problem}\n"
            f"Process type: {item.process_type}, Max rounds: {item.max_rounds}"
        )

        # Record metrics if tracking is enabled
        if _metrics is not None:
            duration_ms = (time.perf_counter() - start_time) * 1000
            _metrics.record_invocation("initiate_persona_session", input_text, result, duration_ms)

        return result

    @toolset.tool(description=CREATE_PERSONA_DESCRIPTION)
    async def create_persona(item: CreatePersonaItem) -> str:
        """Create a new persona for the session."""
        start_time = time.perf_counter()
        input_text = item.model_dump_json() if _metrics else ""

        if _storage.session is None:
            return "No active session. Use initiate_persona_session first."

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

        # Record metrics if tracking is enabled
        if _metrics is not None:
            duration_ms = (time.perf_counter() - start_time) * 1000
            _metrics.record_invocation("create_persona", input_text, result, duration_ms)

        return result

    @toolset.tool(description=ADD_PERSONA_RESPONSE_DESCRIPTION)
    async def add_persona_response(item: AddPersonaResponseItem) -> str:
        """Add a response from a persona."""
        start_time = time.perf_counter()
        input_text = item.model_dump_json() if _metrics else ""

        if _storage.session is None:
            return "No active session. Use initiate_persona_session first."

        if _storage.session.status != "active":
            return f"Session is {_storage.session.status}. Cannot add responses."

        if item.persona_id not in _storage.personas:
            return f"Persona {item.persona_id} not found. Use create_persona first."

        # Determine round number based on process type
        session = _storage.session
        round_number = session.current_round

        # For interactive/devils_advocate, check if this is a response to another response
        if item.references:
            # Find the max round of referenced responses
            max_ref_round = 0
            for ref_id in item.references:
                if ref_id in _storage.responses:
                    ref_response = _storage.responses[ref_id]
                    max_ref_round = max(max_ref_round, ref_response.round_number)
            # This response is in the next round
            round_number = max_ref_round + 1
        else:
            # Initial response - check if this persona already responded in current round
            existing_responses = [
                r
                for r in _storage.responses.values()
                if r.persona_id == item.persona_id and r.round_number == round_number
            ]
            if existing_responses:
                # Move to next round
                round_number = round_number + 1

        # Update session round if needed
        if round_number > session.current_round:
            session.current_round = round_number
            if round_number >= session.max_rounds:
                session.status = "completed"

        response_id = str(uuid.uuid4())
        response = PersonaResponse(
            response_id=response_id,
            persona_id=item.persona_id,
            content=item.content,
            references=item.references,
            round_number=round_number,
        )
        _storage.responses = response

        persona = _storage.personas[item.persona_id]
        status_note = ""
        if session.status == "completed":
            status_note = " (Max rounds reached - session completed)"

        result = (
            f"Added response [{response_id}] from {persona.name} "
            f"(Round {round_number}){status_note}"
        )

        # Record metrics if tracking is enabled
        if _metrics is not None:
            duration_ms = (time.perf_counter() - start_time) * 1000
            _metrics.record_invocation("add_persona_response", input_text, result, duration_ms)

        return result

    @toolset.tool(description=SYNTHESIZE_DESCRIPTION)
    async def synthesize(item: SynthesizeItem) -> str:
        """Synthesize all persona responses into a comprehensive solution."""
        start_time = time.perf_counter()
        input_text = item.model_dump_json() if _metrics else ""

        if _storage.session is None:
            return "No active session. Use initiate_persona_session first."

        session = _storage.session
        if session.status == "synthesized":
            return "Session already synthesized. Use read_personas to view the synthesis."

        session.synthesis = item.synthesis_content
        session.status = "synthesized"

        lines = [
            "Synthesis completed:",
            f"Key Insights ({len(item.key_insights)}):",
        ]
        for i, insight in enumerate(item.key_insights, 1):
            lines.append(f"  {i}. {insight}")

        if item.conflicts_resolved:
            lines.append(f"\nConflicts Resolved ({len(item.conflicts_resolved)}):")
            for i, conflict in enumerate(item.conflicts_resolved, 1):
                lines.append(f"  {i}. {conflict}")

        lines.append(f"\nSynthesis:\n{item.synthesis_content}")

        result = "\n".join(lines)

        # Record metrics if tracking is enabled
        if _metrics is not None:
            duration_ms = (time.perf_counter() - start_time) * 1000
            _metrics.record_invocation("synthesize", input_text, result, duration_ms)

        return result

    return toolset


def get_persona_system_prompt(storage: PersonaStorageProtocol | None = None) -> str:
    """Generate dynamic system prompt section for personas.

    Args:
        storage: Optional storage to read current session from.

    Returns:
        System prompt section with current session info, or base prompt if no session.
    """
    if storage is None or storage.session is None:
        return PERSONA_SYSTEM_PROMPT

    session = storage.session
    lines = [
        PERSONA_SYSTEM_PROMPT,
        "",
        "## Current Persona Session",
        f"Problem: {session.problem}",
        f"Process Type: {session.process_type}",
        f"Status: {session.status}",
        f"Round: {session.current_round} / {session.max_rounds}",
    ]

    if storage.personas:
        lines.append(f"\nPersonas ({len(storage.personas)}):")
        for persona in storage.personas.values():
            lines.append(f"- {persona.name} ({persona.persona_type})")

    if storage.responses:
        lines.append(f"\nResponses ({len(storage.responses)}):")
        for response in storage.responses.values():
            persona = storage.personas.get(response.persona_id)
            persona_name = persona.name if persona else response.persona_id
            lines.append(f"- {persona_name} (Round {response.round_number})")

    if session.synthesis:
        lines.append(f"\nSynthesis: {session.synthesis}")

    return "\n".join(lines)


def create_persona_toolset_agent(model: str = "openrouter:x-ai/grok-4.1-fast") -> Agent:
    """Create a Pydantic-ai agent with the multi-persona toolset.

    Args:
        model: The model to use for the agent.

    Returns:
        Pydantic-ai agent with the multi-persona toolset.
    """
    storage = PersonaStorage()
    toolset = create_persona_toolset(storage=storage)
    agent = Agent(
        model,
        system_prompt="""
        You are a multi-persona agent. You have access to tools for managing multi-persona analysis:
        - `read_personas`: Read the current session state
        - `initiate_persona_session`: Start a new persona analysis session
        - `create_persona`: Create a new persona with specific expertise
        - `add_persona_response`: Add a response from a persona
        - `synthesize`: Synthesize all persona responses into a comprehensive solution

        **IMPORTANT**: Use these tools to adopt multiple personas and synthesize diverse perspectives.
        """,
        toolsets=[toolset]
    )

    @agent.instructions
    async def add_prompt() -> str:
        """Add the multi-persona system prompt."""
        return get_persona_system_prompt(storage)

    return agent

