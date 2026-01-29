"""Todo toolset for pydantic-ai agents."""

from __future__ import annotations

import sys
import time
import uuid
from typing import Any

from pydantic_ai import Agent
from pydantic_ai.toolsets import FunctionToolset

from .storage import TodoStorage, TodoStorageProtocol
from .types import Todo, TodoItem

# =============================================================================
# SYSTEM PROMPT - Contains "when and why" to use the toolset
# =============================================================================

TODO_SYSTEM_PROMPT = """
## Task Management

You have access to tools for managing tasks:
- `read_todos`: Read the current todo list
- `write_todos`: Update the todo list with new items

### When to Use Task Management

Use these tools in these scenarios:
1. Complex multi-step tasks (3+ distinct steps)
2. Non-trivial tasks requiring careful planning
3. User provides multiple tasks
4. After receiving new instructions - capture requirements as todos
5. When starting a task - mark it as in_progress BEFORE beginning work
6. After completing a task - mark it as completed immediately

### Task States

- **pending**: Task not yet started
- **in_progress**: Currently working on (limit to ONE at a time)
- **completed**: Task finished successfully

### Important Rules

- Exactly ONE task should be in_progress at any time
- Mark tasks complete IMMEDIATELY after finishing (don't batch completions)
- If you encounter blockers, keep the task as in_progress and create a new task for the blocker

### Workflow

1. Break down complex tasks into smaller steps
2. Mark exactly one task as in_progress at a time
3. Mark tasks as completed immediately after finishing
4. Use read_todos to check current state before updating
"""

# =============================================================================
# TOOL DESCRIPTIONS - Contains "how" to use each specific tool
# =============================================================================

READ_TODO_DESCRIPTION = """Read the current todo list state.

Returns all todos with their current status (pending, in_progress, completed).

Use before updating task statuses or reporting progress.
"""

WRITE_TODO_DESCRIPTION = """Update the todo list with new items.

Parameters:
- todos: List of todo items with content, status, and active_form

Returns confirmation with updated counts by status.

Precondition: Call read_todos first to see current state.
"""

# Legacy constant for backward compatibility
TODO_TOOL_DESCRIPTION = WRITE_TODO_DESCRIPTION


def create_todo_toolset(
    storage: TodoStorageProtocol | None = None,
    *,
    id: str | None = None,
    track_usage: bool = False,
) -> FunctionToolset[Any]:
    """Create a todo toolset for task management.

    This toolset provides read_todos and write_todos tools for AI agents
    to track and manage tasks during a session.

    Args:
        storage: Optional storage backend. Defaults to in-memory TodoStorage.
        id: Optional unique ID for the toolset.
        track_usage: If True, enables usage metrics collection.

    Returns:
        FunctionToolset compatible with any pydantic-ai agent.

    Example:
        ```python
        from pydantic_ai import Agent
        from pydantic_ai_toolsets import create_todo_toolset, TodoStorage

        # With storage and metrics
        storage = TodoStorage(track_usage=True)
        agent = Agent("openai:gpt-4.1", toolsets=[create_todo_toolset(storage)])
        print(storage.metrics.total_tokens())
        ```
    """
    if storage is not None:
        _storage = storage
    else:
        _storage = TodoStorage(track_usage=track_usage)

    toolset: FunctionToolset[Any] = FunctionToolset(id=id)
    _metrics = getattr(_storage, "metrics", None) if hasattr(_storage, "metrics") else None

    def _get_status_summary() -> str:
        """Get one-line status summary."""
        total = len(_storage.todos)
        if total == 0:
            return "Status: ○ Empty"
        completed = sum(1 for t in _storage.todos if t.status == "completed")
        in_progress = sum(1 for t in _storage.todos if t.status == "in_progress")
        return f"Status: {completed}/{total} complete, {in_progress} active"

    def _get_next_hint() -> str:
        """Get contextual hint for next action."""
        if not _storage.todos:
            return "Use write_todos to create tasks."
        counts = {"pending": 0, "in_progress": 0, "completed": 0}
        for t in _storage.todos:
            counts[t.status] += 1
        if counts["in_progress"] == 0 and counts["pending"] > 0:
            return "Mark a pending task as in_progress to begin work."
        if counts["pending"] == 0 and counts["in_progress"] == 0:
            return "All tasks complete!"
        return "Complete current task, then mark next as in_progress."

    @toolset.tool(description=READ_TODO_DESCRIPTION)
    async def read_todos() -> str:
        """Read the current todo list."""
        start_time = time.perf_counter()

        if not _storage.todos:
            result = f"{_get_status_summary()}\n\nNo todos in the list.\n\nNext: {_get_next_hint()}"
        else:
            lines = [_get_status_summary(), "", "Current todos:"]
            for i, todo in enumerate(_storage.todos, 1):
                status_icon = {
                    "pending": "[ ]",
                    "in_progress": "[*]",
                    "completed": "[x]",
                }.get(todo.status, "[ ]")
                lines.append(f"{i}. {status_icon} {todo.content}")

            counts = {"pending": 0, "in_progress": 0, "completed": 0}
            for todo in _storage.todos:
                counts[todo.status] += 1

            lines.append("")
            lines.append(
                f"Summary: {counts['completed']} completed, "
                f"{counts['in_progress']} in progress, "
                f"{counts['pending']} pending"
            )
            lines.append("")
            lines.append(f"Next: {_get_next_hint()}")
            result = "\n".join(lines)

        if _metrics is not None:
            duration_ms = (time.perf_counter() - start_time) * 1000
            _metrics.record_invocation("read_todos", "", result, duration_ms)

        return result

    @toolset.tool(description=WRITE_TODO_DESCRIPTION)
    async def write_todos(todos: list[TodoItem]) -> str:
        """Update the todo list with new items."""
        start_time = time.perf_counter()
        input_text = str(todos) if _metrics else ""

        _storage.todos = [
            Todo(todo_id=str(uuid.uuid4()), content=t.content, status=t.status, active_form=t.active_form) for t in todos
        ]

        counts = {"pending": 0, "in_progress": 0, "completed": 0}
        for todo in _storage.todos:
            counts[todo.status] += 1

        result = (
            f"Updated {len(todos)} todos: "
            f"{counts['completed']} completed, "
            f"{counts['in_progress']} in progress, "
            f"{counts['pending']} pending"
        )

        if _metrics is not None:
            duration_ms = (time.perf_counter() - start_time) * 1000
            _metrics.record_invocation("write_todos", input_text, result, duration_ms)

        return result

    return toolset


def get_todo_system_prompt(storage: TodoStorageProtocol | None = None) -> str:
    """Generate dynamic system prompt section for todos.

    Args:
        storage: Optional storage to read current todos from.

    Returns:
        System prompt section with current todos, or base prompt if no todos.
    """
    if storage is None or not storage.todos:
        return TODO_SYSTEM_PROMPT

    lines = [TODO_SYSTEM_PROMPT, "", "## Current Todos"]

    for todo in storage.todos:
        status_icon = {
            "pending": "[ ]",
            "in_progress": "[*]",
            "completed": "[x]",
        }.get(todo.status, "[ ]")
        lines.append(f"- {status_icon} {todo.content}")

    return "\n".join(lines)


def create_todo_toolset_agent(model: str = "openrouter:x-ai/grok-4.1-fast") -> Agent:
    """Create a Pydantic-ai agent with the todo toolset.

    Args:
        model: The model to use for the agent.

    Returns:
        Pydantic-ai agent with the todo toolset.
    """
    storage = TodoStorage()
    toolset = create_todo_toolset(storage=storage)
    agent = Agent(
        model,
        system_prompt=TODO_SYSTEM_PROMPT,
        toolsets=[toolset]
    )

    @agent.instructions
    async def add_prompt() -> str:
        """Add the todo system prompt."""
        return get_todo_system_prompt(storage)

    return agent
