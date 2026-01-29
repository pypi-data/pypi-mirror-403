"""Evaluation for Self-Refine toolset using pydantic-evals Dataset API."""

from typing import Any, Callable

from pydantic_ai.toolsets import FunctionToolset
from pydantic_evals import Case, Dataset

from pydantic_ai_toolsets.evals.base import AgentRunner
from pydantic_ai_toolsets.evals.config import EvaluationConfig
from pydantic_ai_toolsets.evals.datasets.reflection_cases import REFLECTION_CASES
from pydantic_ai_toolsets.evals.evaluators import create_evaluators

try:
    from pydantic_ai_toolsets.toolsets.self_refine import SelfRefineStorage, create_self_refine_toolset
    from pydantic_ai_toolsets.toolsets.self_refine.toolset import SELF_REFINE_SYSTEM_PROMPT
except ImportError:
    raise ImportError(
        "pydantic_ai_self_refine not found. Install it or check imports."
    )


def create_self_refine_task_function(
    config: EvaluationConfig,
) -> Callable[[dict[str, Any]], str]:
    """Create a task function for Self-Refine toolset evaluation."""
    runner = AgentRunner(config)

    def self_refine_task(inputs: dict[str, Any]) -> str:
        """Task function for pydantic-evals."""
        import asyncio

        prompt = inputs.get("prompt", "")
        if not prompt:
            return ""

        storage = SelfRefineStorage()

        def toolset_factory() -> FunctionToolset[Any]:
            return create_self_refine_toolset(storage=storage)

        async def run_agent():
            run_result = await runner.run_agent(
                toolset_factory=toolset_factory,
                prompt=prompt,
                storage=storage,
                system_prompt=SELF_REFINE_SYSTEM_PROMPT,
            )

            if run_result.error:
                raise RuntimeError(f"Agent execution failed: {run_result.error}")

            return run_result.output

        return asyncio.run(run_agent())

    return self_refine_task


def create_self_refine_dataset(config: EvaluationConfig) -> tuple[Dataset, Callable]:
    """Create a pydantic-evals Dataset for Self-Refine toolset."""
    self_refine_task = create_self_refine_task_function(config)

    pydantic_cases = []
    for case in REFLECTION_CASES:
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

    dataset = Dataset(
        name="self_refine_toolset_evaluation",
        cases=pydantic_cases,
        evaluators=create_evaluators(config),
    )

    return dataset, self_refine_task


async def evaluate_self_refine_toolset(config: EvaluationConfig):
    """Evaluate Self-Refine toolset using pydantic-evals.

    This creates an Experiment that will show up in Logfire.

    Args:
        config: Evaluation configuration.

    Returns:
        EvaluationReport from pydantic-evals.
    """
    dataset, self_refine_task = create_self_refine_dataset(config)
    # The experiment name comes from the function name (self_refine_task)
    report = await dataset.evaluate(self_refine_task)
    return report

