"""Self-ask toolset for pydantic-ai agents."""

from __future__ import annotations

import sys
import time
import uuid
from typing import Any

from pydantic_ai import Agent
from pydantic_ai.toolsets import FunctionToolset

from .storage import SelfAskStorage, SelfAskStorageProtocol
from .types import (
    Answer,
    AnswerQuestionItem,
    AskMainQuestionItem,
    AskSubQuestionItem,
    ComposeFinalAnswerItem,
    FinalAnswer,
    Question,
    QuestionStatus,
    MAX_DEPTH,
)

# =============================================================================
# SYSTEM PROMPT - Contains "when and why" to use the toolset
# =============================================================================

SELF_ASK_SYSTEM_PROMPT = f"""
## Self-Ask

You have access to tools for decomposing complex questions into simpler sub-questions:
- `read_self_ask_state`: Read current self-ask state
- `ask_main_question`: Initialize main question (depth 0)
- `ask_sub_question`: Generate sub-question from parent question
- `answer_question`: Answer a question/sub-question
- `compose_final_answer`: Compose final answer from sub-question answers
- `get_final_answer`: Retrieve the final composed answer

### When to Use Self-Ask

Use these tools in these scenarios:
1. Complex questions requiring multi-hop reasoning
2. Questions that need to be broken down into simpler parts
3. Problems where intermediate answers build toward a final answer
4. Questions requiring information gathering from multiple sources
5. Situations where explicit decomposition makes reasoning transparent

### Self-Ask Process

1. **Main Question**: Initialize the main question (depth 0)
2. **Decompose**: Generate sub-questions that help answer the main question
   - Sub-questions are at depth 1
   - Sub-sub-questions are at depth 2
   - Sub-sub-sub-questions are at depth 3 (maximum)
   - **CRITICAL**: Maximum depth is {MAX_DEPTH} (main = 0, sub = 1-3)
3. **Answer**: Answer each sub-question sequentially or in parallel
   - Use answers from earlier sub-questions to answer later ones
   - Mark if a sub-question needs further decomposition
4. **Compose**: Synthesize answers from sub-questions into final answer
5. **Retrieve**: Get the final composed answer

### Depth Constraint

**IMPORTANT**: Maximum depth of {MAX_DEPTH} levels:
- Main question: depth 0
- Sub-questions: depth 1
- Sub-sub-questions: depth 2
- Sub-sub-sub-questions: depth 3 (maximum)

When the depth limit is reached:
- Answer remaining questions at maximum depth
- Use those answers to compose the final answer
- Do not attempt to create questions beyond depth {MAX_DEPTH}

### Question Types

- **Sequential Dependency**: Later questions depend on earlier answers
  - Example: "Where were the 2016 Olympics?" → "What was the population there?"
- **Parallel Questions**: Independent questions that can be answered in any order
  - Example: "Japan's GDP growth?" and "Germany's GDP growth?" (both independent)
- **Recursive Decomposition**: Sub-questions spawn sub-sub-questions
  - Example: "How did WWI affect art?" → "What art movements emerged?" → "What was Dadaism?"

### Key Principles

- **Explicit Decomposition**: Make reasoning transparent by showing sub-questions
- **Sequential Dependency**: Build answers from earlier sub-question answers
- **Compositional Reasoning**: Combine simple facts into complex insights
- **Depth Management**: Respect the depth limit and compose final answer when limit reached
- **Answer Tracking**: Track which answers contribute to the final composition

### Workflow

1. Call `read_self_ask_state` to see current state
2. Initialize main question using `ask_main_question` (if none exists)
3. Generate sub-questions using `ask_sub_question` (respecting depth limit)
4. Answer questions using `answer_question`
5. Continue decomposition and answering until all necessary information is gathered
6. Compose final answer using `compose_final_answer`
7. Use `get_final_answer` to retrieve the final result

**IMPORTANT**: Always call `read_self_ask_state` before asking questions, answering, or composing.
"""

# =============================================================================
# TOOL DESCRIPTIONS - Contains "how" to use each specific tool
# =============================================================================

READ_SELF_ASK_STATE_DESCRIPTION = """
Read the current self-ask state.

**CRITICAL**: Call this BEFORE every ask_main_question, ask_sub_question, answer_question, or compose_final_answer call to:
- Review the current question tree structure
- See which questions exist and their depth levels
- Understand which questions have been answered
- Track depth levels to ensure you don't exceed the maximum depth
- Know which answers are available for composition
- Make informed decisions about next steps

Returns:
- All questions organized by depth with their status
- All answers with their corresponding question IDs
- Final answers if any have been composed
- Question tree structure showing parent-child relationships
- Summary statistics (total questions, max depth reached, answered questions)
- Warning if depth limit has been reached
"""

ASK_MAIN_QUESTION_DESCRIPTION = """
Initialize the main question (depth 0).

Use this tool to start the self-ask process with the main question that needs to be answered.
This question will be at depth 0 and serves as the root of the question tree.

**CRITICAL**: Call read_self_ask_state first to see existing questions.

When asking the main question:
- This should be the original complex question you need to answer
- It will be at depth 0 (the root)
- Sub-questions will be generated from this main question
- Only one main question should exist per self-ask session
"""

ASK_SUB_QUESTION_DESCRIPTION = f"""
Generate a sub-question from a parent question.

Use this tool to decompose a complex question into simpler sub-questions.
Each sub-question helps answer its parent question.

**CRITICAL**: Call read_self_ask_state first to see existing questions and their depths.

**DEPTH CONSTRAINT**: Maximum depth is {MAX_DEPTH}:
- Main question: depth 0
- Sub-questions: depth 1
- Sub-sub-questions: depth 2
- Sub-sub-sub-questions: depth 3 (maximum)

When asking sub-questions:
- Check the parent question's depth first
- If parent depth >= {MAX_DEPTH}, you cannot create more sub-questions
- New sub-question depth = parent depth + 1
- Provide reasoning for why this sub-question is needed
- Sub-questions should be simpler and more focused than their parent
- Consider whether sub-questions can be answered in parallel or sequentially
"""

ANSWER_QUESTION_DESCRIPTION = """
Answer a question or sub-question.

Use this tool to provide an answer to a question. The answer can then be used
to answer parent questions or compose the final answer.

**CRITICAL**: Call read_self_ask_state first to see which questions need answers.

When answering:
- Provide a complete answer that directly addresses the question
- Use answers from sub-questions if available
- Optionally provide a confidence score (0-100)
- Indicate if the answer requires further sub-questions (requires_followup)
- If requires_followup is true, you may need to ask sub-sub-questions (respecting depth limit)
"""

COMPOSE_FINAL_ANSWER_DESCRIPTION = """
Compose the final answer from sub-question answers.

Use this tool to synthesize answers from sub-questions into a complete answer
to the main question.

**CRITICAL**: Call read_self_ask_state first to see all available answers.

When composing:
- Reference the main question ID
- List all answer IDs that contributed to the final answer
- Synthesize the information from sub-question answers
- Create a coherent, complete answer to the main question
- The final answer should address the original main question comprehensively
"""

GET_FINAL_ANSWER_DESCRIPTION = """
Retrieve the final composed answer.

Use this tool to get the final answer that was composed from sub-question answers.
This is the complete answer to the main question.

**CRITICAL**: Call read_self_ask_state first to see if a final answer exists.

Returns:
- Final answer content
- Which answers were used in composition
- Main question that was answered
- Completion status
"""


def create_self_ask_toolset(
    storage: SelfAskStorageProtocol | None = None,
    *,
    id: str | None = None,
    track_usage: bool = False,
) -> FunctionToolset[Any]:
    """Create a self-ask toolset for question decomposition.

    This toolset provides tools for AI agents to decompose complex questions into
    simpler sub-questions, answer them sequentially, and compose final answers.

    Args:
        storage: Optional storage backend. Defaults to in-memory SelfAskStorage.
            You can provide a custom storage implementing SelfAskStorageProtocol
            for persistence or integration with other systems.
        id: Optional unique ID for the toolset.
        track_usage: If True, enables usage metrics collection in storage.

    Returns:
        FunctionToolset compatible with any pydantic-ai agent.

    Example (standalone):
        ```python
        from pydantic_ai import Agent
        from pydantic_ai_toolsets import create_self_ask_toolset

        agent = Agent("openai:gpt-4.1", toolsets=[create_self_ask_toolset()])
        result = await agent.run("What was the population of the city where the 2016 Summer Olympics were held?")
        ```

    Example (with custom storage):
        ```python
        from pydantic_ai_toolsets import create_self_ask_toolset, SelfAskStorage

        storage = SelfAskStorage()
        toolset = create_self_ask_toolset(storage=storage)

        # After agent runs, access questions, answers, and final answers directly
        print(storage.questions)
        print(storage.answers)
        print(storage.final_answers)
        ```
    """
    if storage is not None:
        _storage = storage
    else:
        _storage = SelfAskStorage(track_usage=track_usage)

    toolset: FunctionToolset[Any] = FunctionToolset(id=id)
    _metrics = getattr(_storage, "metrics", None) if hasattr(_storage, "metrics") else None

    def _get_status_summary() -> str:
        """Get one-line status summary."""
        if not _storage.questions:
            return "Status: ○ Empty"
        main_questions = [q for q in _storage.questions.values() if q.is_main]
        if not main_questions:
            return "Status: ● No main question"
        main_q = main_questions[0]
        answered_count = sum(
            1 for q in _storage.questions.values() if q.status == QuestionStatus.ANSWERED
        )
        total_questions = len(_storage.questions)
        max_depth = max((q.depth for q in _storage.questions.values()), default=0)
        final_answers = len(_storage.final_answers)
        if final_answers > 0:
            return f"Status: ✓ Complete | {total_questions} questions, depth {max_depth}, {answered_count} answered"
        depth_warning = f" (max depth {MAX_DEPTH} reached)" if max_depth >= MAX_DEPTH else ""
        return f"Status: ● Active | {total_questions} questions, depth {max_depth}, {answered_count} answered{depth_warning}"

    def _get_next_hint() -> str:
        """Get contextual hint for next action."""
        if not _storage.questions:
            return "Use ask_main_question to initialize the main question."
        main_questions = [q for q in _storage.questions.values() if q.is_main]
        if not main_questions:
            return "Use ask_main_question to initialize the main question."
        if _storage.final_answers:
            return "Self-ask complete. Use get_final_answer to retrieve the final result."
        # Find unanswered questions
        unanswered = [
            q
            for q in _storage.questions.values()
            if q.status == QuestionStatus.PENDING
        ]
        if unanswered:
            # Check if we can ask sub-questions
            can_ask_sub = [
                q for q in unanswered if q.depth < MAX_DEPTH
            ]
            if can_ask_sub:
                return f"Use ask_sub_question or answer_question on [{can_ask_sub[0].question_id}] (depth {can_ask_sub[0].depth})."
            else:
                return f"Use answer_question on [{unanswered[0].question_id}] (depth {unanswered[0].depth}, max depth reached)."
        # All questions answered, need to compose
        answered_questions = [
            q for q in _storage.questions.values() if q.status == QuestionStatus.ANSWERED
        ]
        if answered_questions:
            main_q = main_questions[0]
            return f"All questions answered. Use compose_final_answer for main question [{main_q.question_id}]."
        return "Continue asking sub-questions or answering questions."

    @toolset.tool(description=READ_SELF_ASK_STATE_DESCRIPTION)
    async def read_self_ask_state() -> str:
        """Read the current self-ask state."""
        start_time = time.perf_counter()

        if not _storage.questions:
            result = f"{_get_status_summary()}\n\nNo questions in self-ask state.\n\nNext: {_get_next_hint()}"
            if _metrics is not None:
                duration_ms = (time.perf_counter() - start_time) * 1000
                _metrics.record_invocation("read_self_ask_state", "", result, duration_ms)
            return result

        lines: list[str] = [_get_status_summary(), "", "Self-Ask State:"]
        lines.append("")

        # Display questions by depth
        questions_by_depth: dict[int, list[Question]] = {}
        for question in _storage.questions.values():
            if question.depth not in questions_by_depth:
                questions_by_depth[question.depth] = []
            questions_by_depth[question.depth].append(question)

        lines.append("Questions by Depth:")
        for depth in sorted(questions_by_depth.keys()):
            questions = questions_by_depth[depth]
            depth_label = "Main" if depth == 0 else f"Depth {depth}"
            depth_warning = f" ⚠️ MAX DEPTH" if depth >= MAX_DEPTH else ""
            lines.append(f"  {depth_label} (depth {depth}):{depth_warning}")
            for question in questions:
                status_icon = "✓" if question.status == QuestionStatus.ANSWERED else "○"
                main_str = " [MAIN]" if question.is_main else ""
                lines.append(f"    {status_icon} [{question.question_id}]{main_str} - {question.question_text}")
                if question.parent_question_id:
                    parent = _storage.questions.get(question.parent_question_id)
                    parent_ref = (
                        f"[{question.parent_question_id}]"
                        if parent
                        else f"[{question.parent_question_id}] (missing)"
                    )
                    lines.append(f"      Parent: {parent_ref}")
            lines.append("")

        # Display answers
        if _storage.answers:
            lines.append("Answers:")
            for answer in _storage.answers.values():
                question = _storage.questions.get(answer.question_id)
                question_ref = (
                    f"[{answer.question_id}]"
                    if question
                    else f"[{answer.question_id}] (missing)"
                )
                confidence_str = (
                    f" (confidence: {answer.confidence_score:.1f})"
                    if answer.confidence_score is not None
                    else ""
                )
                followup_str = " [needs followup]" if answer.requires_followup else ""
                lines.append(f"  Answer [{answer.answer_id}] for question {question_ref}{confidence_str}{followup_str}:")
                lines.append(f"    {answer.answer_text}")
                lines.append("")

        # Display final answers
        if _storage.final_answers:
            lines.append("Final Answers:")
            for final_answer in _storage.final_answers.values():
                main_q = _storage.questions.get(final_answer.main_question_id)
                main_ref = (
                    f"[{final_answer.main_question_id}]"
                    if main_q
                    else f"[{final_answer.main_question_id}] (missing)"
                )
                complete_str = " ✓ COMPLETE" if final_answer.is_complete else ""
                lines.append(f"  Final Answer [{final_answer.final_answer_id}] for {main_ref}{complete_str}:")
                lines.append(f"    {final_answer.final_answer_text}")
                if final_answer.composed_from_answers:
                    answer_refs = ", ".join([f"[{aid}]" for aid in final_answer.composed_from_answers])
                    lines.append(f"    Composed from: {answer_refs}")
                lines.append("")

        # Display question tree
        main_questions = [q for q in _storage.questions.values() if q.is_main]
        if main_questions:
            lines.append("Question Tree:")
            for main_q in main_questions:
                lines.append(f"  Main: [{main_q.question_id}] - {main_q.question_text}")
                # Build tree recursively
                def _print_tree(question_id: str, prefix: str = "    ", depth: int = 0) -> None:
                    if depth > MAX_DEPTH:
                        return
                    children = [
                        q
                        for q in _storage.questions.values()
                        if q.parent_question_id == question_id
                    ]
                    for i, child in enumerate(children):
                        is_last = i == len(children) - 1
                        connector = "└── " if is_last else "├── "
                        status_icon = "✓" if child.status == QuestionStatus.ANSWERED else "○"
                        lines.append(f"{prefix}{connector}{status_icon} [{child.question_id}] (depth {child.depth}) - {child.question_text}")
                        if not is_last:
                            _print_tree(child.question_id, prefix + "│   ", depth + 1)
                        else:
                            _print_tree(child.question_id, prefix + "    ", depth + 1)

                _print_tree(main_q.question_id)
            lines.append("")

        # Summary statistics
        stats = _storage.get_statistics()
        lines.append("Summary:")
        lines.append(f"  Total questions: {stats['total_questions']}")
        lines.append(f"  Main questions: {stats['main_questions']}")
        lines.append(f"  Answered questions: {stats['answered_questions']}")
        lines.append(f"  Maximum depth reached: {stats['max_depth_reached']}")
        if stats['max_depth_reached'] >= MAX_DEPTH:
            lines.append(f"  ⚠️ WARNING: Maximum depth {MAX_DEPTH} reached. Cannot create deeper sub-questions.")
        lines.append(f"  Total answers: {stats['total_answers']}")
        lines.append(f"  Total final answers: {stats['total_final_answers']}")
        if 'avg_confidence_score' in stats:
            lines.append(f"  Average confidence: {stats['avg_confidence_score']:.1f}")

        lines.append("")
        lines.append(f"Next: {_get_next_hint()}")

        result = "\n".join(lines)

        if _metrics is not None:
            duration_ms = (time.perf_counter() - start_time) * 1000
            _metrics.record_invocation("read_self_ask_state", "", result, duration_ms)

        return result

    @toolset.tool(description=ASK_MAIN_QUESTION_DESCRIPTION)
    async def ask_main_question(item: AskMainQuestionItem) -> str:
        """Initialize the main question (depth 0)."""
        start_time = time.perf_counter()
        input_text = item.model_dump_json() if _metrics else ""

        # Check if main question already exists
        existing_main = [q for q in _storage.questions.values() if q.is_main]
        if existing_main:
            main_q = existing_main[0]
            return (
                f"Main question already exists: [{main_q.question_id}] - {main_q.question_text}. "
                "Use ask_sub_question to create sub-questions."
            )

        question_id = str(uuid.uuid4())

        new_question = Question(
            question_id=question_id,
            question_text=item.question_text,
            is_main=True,
            parent_question_id=None,
            depth=0,
            status=QuestionStatus.PENDING,
        )

        _storage.questions = new_question

        result = f"Created main question [{question_id}] at depth 0: {item.question_text}"

        if _metrics is not None:
            duration_ms = (time.perf_counter() - start_time) * 1000
            _metrics.record_invocation("ask_main_question", input_text, result, duration_ms)

        return result

    @toolset.tool(description=ASK_SUB_QUESTION_DESCRIPTION)
    async def ask_sub_question(item: AskSubQuestionItem) -> str:
        """Generate a sub-question from a parent question."""
        start_time = time.perf_counter()
        input_text = item.model_dump_json() if _metrics else ""

        if item.parent_question_id not in _storage.questions:
            available = ", ".join([q.question_id for q in _storage.questions.values()])
            return (
                f"Error: Parent question '{item.parent_question_id}' not found. "
                f"Available: [{available}]. Call read_self_ask_state."
            )

        parent_question = _storage.questions[item.parent_question_id]

        # CRITICAL: Check depth limit
        if parent_question.depth >= MAX_DEPTH:
            return (
                f"Error: Cannot create sub-question. Parent question [{item.parent_question_id}] "
                f"is at depth {parent_question.depth}, which is the maximum depth ({MAX_DEPTH}). "
                f"Answer the parent question and compose the final answer instead."
            )

        new_depth = parent_question.depth + 1
        question_id = str(uuid.uuid4())

        new_question = Question(
            question_id=question_id,
            question_text=item.sub_question_text,
            is_main=False,
            parent_question_id=item.parent_question_id,
            depth=new_depth,
            status=QuestionStatus.PENDING,
        )

        _storage.questions = new_question

        depth_warning = f" (max depth {MAX_DEPTH} reached)" if new_depth >= MAX_DEPTH else ""
        result = (
            f"Created sub-question [{question_id}] at depth {new_depth} "
            f"from parent [{item.parent_question_id}]{depth_warning}: {item.sub_question_text}"
        )

        if _metrics is not None:
            duration_ms = (time.perf_counter() - start_time) * 1000
            _metrics.record_invocation("ask_sub_question", input_text, result, duration_ms)

        return result

    @toolset.tool(description=ANSWER_QUESTION_DESCRIPTION)
    async def answer_question(item: AnswerQuestionItem) -> str:
        """Answer a question or sub-question."""
        start_time = time.perf_counter()
        input_text = item.model_dump_json() if _metrics else ""

        if item.question_id not in _storage.questions:
            available = ", ".join([q.question_id for q in _storage.questions.values()])
            return (
                f"Error: Question '{item.question_id}' not found. "
                f"Available: [{available}]. Call read_self_ask_state."
            )

        question = _storage.questions[item.question_id]
        answer_id = str(uuid.uuid4())

        new_answer = Answer(
            answer_id=answer_id,
            question_id=item.question_id,
            answer_text=item.answer_text,
            confidence_score=item.confidence_score,
            requires_followup=item.requires_followup,
        )

        _storage.answers = new_answer

        # Update question status
        question.status = QuestionStatus.ANSWERED
        _storage.questions = question

        confidence_str = (
            f" (confidence: {item.confidence_score:.1f})"
            if item.confidence_score is not None
            else ""
        )
        followup_str = " [needs followup]" if item.requires_followup else ""
        result = (
            f"Answered question [{item.question_id}] "
            f"with answer [{answer_id}]{confidence_str}{followup_str}"
        )

        if _metrics is not None:
            duration_ms = (time.perf_counter() - start_time) * 1000
            _metrics.record_invocation("answer_question", input_text, result, duration_ms)

        return result

    @toolset.tool(description=COMPOSE_FINAL_ANSWER_DESCRIPTION)
    async def compose_final_answer(item: ComposeFinalAnswerItem) -> str:
        """Compose the final answer from sub-question answers."""
        start_time = time.perf_counter()
        input_text = item.model_dump_json() if _metrics else ""

        if item.main_question_id not in _storage.questions:
            available = ", ".join([q.question_id for q in _storage.questions.values()])
            return (
                f"Error: Main question '{item.main_question_id}' not found. "
                f"Available: [{available}]. Call read_self_ask_state."
            )

        main_question = _storage.questions[item.main_question_id]
        if not main_question.is_main:
            return (
                f"Error: Question [{item.main_question_id}] is not a main question. "
                "Use the main question ID to compose the final answer."
            )

        # Verify answer IDs exist
        missing_answers = [
            aid for aid in item.answer_ids_used if aid not in _storage.answers
        ]
        if missing_answers:
            return (
                f"Error: Some answer IDs not found: {missing_answers}. "
                "Call read_self_ask_state to see available answers."
            )

        final_answer_id = str(uuid.uuid4())

        new_final_answer = FinalAnswer(
            final_answer_id=final_answer_id,
            main_question_id=item.main_question_id,
            final_answer_text=item.final_answer_text,
            composed_from_answers=item.answer_ids_used,
            is_complete=True,
        )

        _storage.final_answers = new_final_answer

        # Update main question status
        main_question.status = QuestionStatus.COMPOSED
        _storage.questions = main_question

        result = (
            f"Composed final answer [{final_answer_id}] for main question "
            f"[{item.main_question_id}] using {len(item.answer_ids_used)} answer(s)"
        )

        if _metrics is not None:
            duration_ms = (time.perf_counter() - start_time) * 1000
            _metrics.record_invocation("compose_final_answer", input_text, result, duration_ms)

        return result

    @toolset.tool(description=GET_FINAL_ANSWER_DESCRIPTION)
    async def get_final_answer() -> str:
        """Retrieve the final composed answer."""
        start_time = time.perf_counter()

        if not _storage.final_answers:
            return "No final answer found. Use compose_final_answer to create one."

        # Get the most recent final answer (or first one)
        final_answer = list(_storage.final_answers.values())[0]

        main_question = _storage.questions.get(final_answer.main_question_id)
        main_text = (
            main_question.question_text
            if main_question
            else f"[{final_answer.main_question_id}] (missing)"
        )

        lines: list[str] = [f"Final Answer: [{final_answer.final_answer_id}]"]
        lines.append(f"Main Question: {main_text}")
        if final_answer.is_complete:
            lines.append("Status: ✓ COMPLETE")
        lines.append("")
        lines.append("Final Answer:")
        lines.append(final_answer.final_answer_text)
        lines.append("")

        # Show which answers were used
        if final_answer.composed_from_answers:
            lines.append("Composed from answers:")
            for answer_id in final_answer.composed_from_answers:
                answer = _storage.answers.get(answer_id)
                question = (
                    _storage.questions.get(answer.question_id)
                    if answer
                    else None
                )
                if answer and question:
                    lines.append(f"  [{answer_id}] - Answer to: {question.question_text}")
                    lines.append(f"    {answer.answer_text}")
                else:
                    lines.append(f"  [{answer_id}] - (missing)")
            lines.append("")

        result = "\n".join(lines)

        if _metrics is not None:
            duration_ms = (time.perf_counter() - start_time) * 1000
            _metrics.record_invocation("get_final_answer", "", result, duration_ms)

        return result

    return toolset


def get_self_ask_system_prompt() -> str:
    """Get the system prompt for self-ask reasoning.

    Returns:
        System prompt string that can be used with pydantic-ai agents.
    """
    return SELF_ASK_SYSTEM_PROMPT


def create_self_ask_toolset_agent(model: str = "openrouter:x-ai/grok-4.1-fast") -> Agent:
    """Create a Pydantic-ai agent with the self-ask toolset.

    Args:
        model: The model to use for the agent.

    Returns:
        Pydantic-ai agent with the self-ask toolset.
    """
    storage = SelfAskStorage()
    toolset = create_self_ask_toolset(storage=storage)
    agent = Agent(
        model,
        system_prompt="""
        You are a self-ask agent. You have access to tools for decomposing complex questions:
        - `read_self_ask_state`: Read the current self-ask state
        - `ask_main_question`: Initialize main question (depth 0)
        - `ask_sub_question`: Generate sub-question from parent question
        - `answer_question`: Answer a question/sub-question
        - `compose_final_answer`: Compose final answer from sub-question answers
        - `get_final_answer`: Retrieve the final composed answer

        **IMPORTANT**: Use these tools to decompose complex questions into simpler sub-questions,
        answer them sequentially, and compose final answers. Respect the maximum depth limit of 3.
        """,
        toolsets=[toolset]
    )

    @agent.instructions
    async def add_prompt() -> str:
        """Add the self-ask system prompt."""
        return get_self_ask_system_prompt()

    return agent
