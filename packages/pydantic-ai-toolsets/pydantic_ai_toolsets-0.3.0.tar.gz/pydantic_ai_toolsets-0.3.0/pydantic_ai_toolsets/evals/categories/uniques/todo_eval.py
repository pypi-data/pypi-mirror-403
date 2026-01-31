"""Evaluation for todo toolset using pydantic-evals Dataset API."""

from typing import Any, Callable

from pydantic_ai.toolsets import FunctionToolset
from pydantic_evals import Case, Dataset

from pydantic_ai_toolsets.evals.base import AgentRunner
from pydantic_ai_toolsets.evals.config import EvaluationConfig
from pydantic_ai_toolsets.evals.datasets.uniques_cases import TODO_CASES
from pydantic_ai_toolsets.evals.evaluators import create_evaluators

try:
    from pydantic_ai_toolsets.toolsets.to_do import TodoStorage, create_todo_toolset
    from pydantic_ai_toolsets.toolsets.to_do.toolset import TODO_SYSTEM_PROMPT
except ImportError:
    raise ImportError(
        "pydantic_ai_todo not found. Install it or check imports."
    )


def create_todo_task_function(
    config: EvaluationConfig,
) -> Callable[[dict[str, Any]], str]:
    """Create a task function for todo toolset evaluation.

    This function will be called by pydantic-evals for each case.
    It must be synchronous and take inputs dict, return output string.

    Args:
        config: Evaluation configuration.

    Returns:
        Task function that takes inputs dict and returns output string.
    """
    runner = AgentRunner(config)

    def todo_task(inputs: dict[str, Any]) -> str:
        """Task function for pydantic-evals.

        Args:
            inputs: Dictionary with 'prompt' key containing the user prompt.

        Returns:
            Agent output as string.
        """
        import asyncio

        prompt = inputs.get("prompt", "")
        if not prompt:
            return ""

        # Create storage for this evaluation
        storage = TodoStorage()

        def toolset_factory() -> FunctionToolset[Any]:
            return create_todo_toolset(storage=storage)

        # Run agent synchronously
        async def run_agent():
            run_result = await runner.run_agent(
                toolset_factory=toolset_factory,
                prompt=prompt,
                storage=storage,
                system_prompt=TODO_SYSTEM_PROMPT,
            )

            if run_result.error:
                raise RuntimeError(f"Agent execution failed: {run_result.error}")

            return run_result.output

        return asyncio.run(run_agent())

    return todo_task


def create_todo_dataset(config: EvaluationConfig) -> tuple[Dataset, Callable]:
    """Create a pydantic-evals Dataset for todo toolset.

    Args:
        config: Evaluation configuration.

    Returns:
        Tuple of (Dataset, task_function).
    """
    # Create task function
    todo_task = create_todo_task_function(config)

    # Convert test cases to pydantic-evals Cases
    pydantic_cases = []
    for case in TODO_CASES:
        pydantic_cases.append(
            Case(
                name=case.name,
                inputs={"prompt": case.prompt},
                metadata={
                    "difficulty": case.difficulty,
                    "expected_tools": case.expected_tools or [],
                    "expected_storage_keys": case.expected_storage_keys or [],
                    "min_storage_items": case.min_storage_items,
                },
            )
        )

    # Create dataset - this will create an Experiment when evaluated
    dataset = Dataset(
        name="todo_toolset_evaluation",
        cases=pydantic_cases,
        evaluators=create_evaluators(config),
    )

    return dataset, todo_task


async def evaluate_todo_toolset(config: EvaluationConfig):
    """Evaluate todo toolset using pydantic-evals.

    This creates an Experiment that will show up in Logfire.

    Args:
        config: Evaluation configuration.

    Returns:
        EvaluationReport from pydantic-evals.
    """
    dataset, todo_task = create_todo_dataset(config)
    # This creates an Experiment that Logfire will track
    # The experiment name comes from the function name (todo_task)
    report = await dataset.evaluate(todo_task)
    return report

