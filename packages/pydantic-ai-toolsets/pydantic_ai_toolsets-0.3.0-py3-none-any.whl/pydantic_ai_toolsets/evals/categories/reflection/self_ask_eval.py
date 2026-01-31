"""Evaluation for Self-Ask toolset using pydantic-evals Dataset API."""

from typing import Any, Callable

from pydantic_ai.toolsets import FunctionToolset
from pydantic_evals import Case, Dataset

from pydantic_ai_toolsets.evals.base import AgentRunner
from pydantic_ai_toolsets.evals.config import EvaluationConfig
from pydantic_ai_toolsets.evals.datasets.self_ask_cases import SELF_ASK_CASES
from pydantic_ai_toolsets.evals.evaluators import create_evaluators

try:
    from pydantic_ai_toolsets.toolsets.self_ask import SelfAskStorage, create_self_ask_toolset
    from pydantic_ai_toolsets.toolsets.self_ask.toolset import SELF_ASK_SYSTEM_PROMPT
except ImportError:
    raise ImportError(
        "pydantic_ai_self_ask not found. Install it or check imports."
    )


def create_self_ask_task_function(
    config: EvaluationConfig,
) -> Callable[[dict[str, Any]], str]:
    """Create a task function for Self-Ask toolset evaluation."""
    runner = AgentRunner(config)

    def self_ask_task(inputs: dict[str, Any]) -> str:
        """Task function for pydantic-evals."""
        import asyncio

        prompt = inputs.get("prompt", "")
        if not prompt:
            return ""

        storage = SelfAskStorage()

        def toolset_factory() -> FunctionToolset[Any]:
            return create_self_ask_toolset(storage=storage)

        async def run_agent():
            run_result = await runner.run_agent(
                toolset_factory=toolset_factory,
                prompt=prompt,
                storage=storage,
                system_prompt=SELF_ASK_SYSTEM_PROMPT,
            )

            if run_result.error:
                raise RuntimeError(f"Agent execution failed: {run_result.error}")

            return run_result.output

        return asyncio.run(run_agent())

    return self_ask_task


def create_self_ask_dataset(config: EvaluationConfig) -> tuple[Dataset, Callable]:
    """Create a pydantic-evals Dataset for Self-Ask toolset."""
    self_ask_task = create_self_ask_task_function(config)

    pydantic_cases = []
    for case in SELF_ASK_CASES:
        pydantic_cases.append(
            Case(
                name=case.name,
                inputs={"prompt": case.prompt},
                metadata={
                    "difficulty": case.difficulty,
                    "expected_tools": case.expected_tools or [],
                    "expected_storage_keys": case.expected_storage_keys or [],
                    "min_storage_items": case.min_storage_items,
                    "max_depth_expected": case.max_depth_expected,
                },
            )
        )

    dataset = Dataset(
        name="self_ask_toolset_evaluation",
        cases=pydantic_cases,
        evaluators=create_evaluators(config),
    )

    return dataset, self_ask_task


async def evaluate_self_ask_toolset(config: EvaluationConfig):
    """Evaluate Self-Ask toolset using pydantic-evals.

    This creates an Experiment that will show up in Logfire.

    Args:
        config: Evaluation configuration.

    Returns:
        EvaluationReport from pydantic-evals.
    """
    dataset, self_ask_task = create_self_ask_dataset(config)
    # The experiment name comes from the function name (self_ask_task)
    report = await dataset.evaluate(self_ask_task)
    return report
