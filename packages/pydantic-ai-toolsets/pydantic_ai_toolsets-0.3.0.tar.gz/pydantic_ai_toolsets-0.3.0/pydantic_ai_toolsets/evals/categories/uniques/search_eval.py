"""Evaluation for search toolset using pydantic-evals Dataset API."""

from typing import Any, Callable

from pydantic_ai.toolsets import FunctionToolset
from pydantic_evals import Case, Dataset

from pydantic_ai_toolsets.evals.base import AgentRunner
from pydantic_ai_toolsets.evals.config import EvaluationConfig
from pydantic_ai_toolsets.evals.datasets.uniques_cases import SEARCH_CASES
from pydantic_ai_toolsets.evals.evaluators import create_evaluators

try:
    from pydantic_ai_toolsets.toolsets.search import SearchStorage, create_search_toolset
    from pydantic_ai_toolsets.toolsets.search.toolset import SEARCH_SYSTEM_PROMPT
except ImportError as e:
    raise ImportError(
        f"search toolset not found. Check imports. Error: {e}"
    )


def create_search_task_function(
    config: EvaluationConfig,
) -> Callable[[dict[str, Any]], str]:
    """Create a task function for search toolset evaluation.

    This function will be called by pydantic-evals for each case.
    It must be synchronous and take inputs dict, return output string.

    Args:
        config: Evaluation configuration.

    Returns:
        Task function that takes inputs dict and returns output string.
    """
    runner = AgentRunner(config)

    def search_task(inputs: dict[str, Any]) -> str:
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
        storage = SearchStorage()

        def toolset_factory() -> FunctionToolset[Any]:
            return create_search_toolset(storage=storage)

        # Run agent synchronously
        async def run_agent():
            run_result = await runner.run_agent(
                toolset_factory=toolset_factory,
                prompt=prompt,
                storage=storage,
                system_prompt=SEARCH_SYSTEM_PROMPT,
            )

            if run_result.error:
                raise RuntimeError(f"Agent execution failed: {run_result.error}")

            return run_result.output

        return asyncio.run(run_agent())

    return search_task


def create_search_dataset(config: EvaluationConfig) -> tuple[Dataset, Callable]:
    """Create a pydantic-evals Dataset for search toolset.

    Args:
        config: Evaluation configuration.

    Returns:
        Tuple of (Dataset, task_function).
    """
    # Create task function
    search_task = create_search_task_function(config)

    # Convert test cases to pydantic-evals Cases
    pydantic_cases = []
    for case in SEARCH_CASES:
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
        name="search_toolset_evaluation",
        cases=pydantic_cases,
        evaluators=create_evaluators(config),
    )

    return dataset, search_task


async def evaluate_search_toolset(config: EvaluationConfig):
    """Evaluate search toolset using pydantic-evals.

    This creates an Experiment that will show up in Logfire.

    Args:
        config: Evaluation configuration.

    Returns:
        EvaluationReport from pydantic-evals.
    """
    dataset, search_task = create_search_dataset(config)
    # This creates an Experiment that Logfire will track
    # The experiment name comes from the function name (search_task)
    report = await dataset.evaluate(search_task)
    return report

