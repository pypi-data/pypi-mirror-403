"""Evaluation for CoT (Chain of Thoughts) toolset using pydantic-evals Dataset API."""

from typing import Any, Callable

from pydantic_ai.toolsets import FunctionToolset
from pydantic_evals import Case, Dataset

from pydantic_ai_toolsets.evals.base import AgentRunner
from pydantic_ai_toolsets.evals.config import EvaluationConfig
from pydantic_ai_toolsets.evals.datasets.thinking_cases import THINKING_CASES
from pydantic_ai_toolsets.evals.evaluators import create_evaluators

try:
    from pydantic_ai_toolsets.toolsets.chain_of_thought_reasoning import CoTStorage, create_cot_toolset
    from pydantic_ai_toolsets.toolsets.chain_of_thought_reasoning.toolset import COT_SYSTEM_PROMPT
except ImportError:
    raise ImportError(
        "pydantic_ai_cot not found. Install it or check imports."
    )


def create_cot_task_function(
    config: EvaluationConfig,
) -> Callable[[dict[str, Any]], str]:
    """Create a task function for CoT toolset evaluation."""
    runner = AgentRunner(config)

    def cot_task(inputs: dict[str, Any]) -> str:
        """Task function for pydantic-evals."""
        import asyncio

        prompt = inputs.get("prompt", "")
        if not prompt:
            return ""

        storage = CoTStorage()

        def toolset_factory() -> FunctionToolset[Any]:
            return create_cot_toolset(storage=storage)

        async def run_agent():
            run_result = await runner.run_agent(
                toolset_factory=toolset_factory,
                prompt=prompt,
                storage=storage,
                system_prompt=COT_SYSTEM_PROMPT,
            )

            if run_result.error:
                raise RuntimeError(f"Agent execution failed: {run_result.error}")

            return run_result.output

        return asyncio.run(run_agent())

    return cot_task


def create_cot_dataset(config: EvaluationConfig) -> tuple[Dataset, Callable]:
    """Create a pydantic-evals Dataset for CoT toolset."""
    cot_task = create_cot_task_function(config)

    pydantic_cases = []
    for case in THINKING_CASES:
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
        name="cot_toolset_evaluation",
        cases=pydantic_cases,
        evaluators=create_evaluators(config),
    )

    return dataset, cot_task


async def evaluate_cot_toolset(config: EvaluationConfig):
    """Evaluate CoT toolset using pydantic-evals.

    This creates an Experiment that will show up in Logfire.

    Args:
        config: Evaluation configuration.

    Returns:
        EvaluationReport from pydantic-evals.
    """
    dataset, cot_task = create_cot_dataset(config)
    # The experiment name comes from the function name (cot_task)
    report = await dataset.evaluate(cot_task)
    return report

