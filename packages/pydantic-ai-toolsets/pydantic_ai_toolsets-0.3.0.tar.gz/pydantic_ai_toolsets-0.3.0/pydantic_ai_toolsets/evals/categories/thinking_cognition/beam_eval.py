"""Evaluation for Beam Search toolset using pydantic-evals Dataset API."""

from typing import Any, Callable

from pydantic_ai.toolsets import FunctionToolset
from pydantic_evals import Case, Dataset

from pydantic_ai_toolsets.evals.base import AgentRunner
from pydantic_ai_toolsets.evals.config import EvaluationConfig
from pydantic_ai_toolsets.evals.datasets.thinking_cases import THINKING_CASES
from pydantic_ai_toolsets.evals.evaluators import create_evaluators

try:
    from pydantic_ai_toolsets.toolsets.beam_search_reasoning import BeamStorage, create_beam_toolset
    from pydantic_ai_toolsets.toolsets.beam_search_reasoning.toolset import BEAM_SYSTEM_PROMPT
except ImportError:
    raise ImportError(
        "pydantic_ai_beam not found. Install it or check imports."
    )


def create_beam_task_function(
    config: EvaluationConfig,
) -> Callable[[dict[str, Any]], str]:
    """Create a task function for Beam toolset evaluation."""
    runner = AgentRunner(config)

    def beam_task(inputs: dict[str, Any]) -> str:
        """Task function for pydantic-evals."""
        import asyncio

        prompt = inputs.get("prompt", "")
        if not prompt:
            return ""

        storage = BeamStorage()

        def toolset_factory() -> FunctionToolset[Any]:
            return create_beam_toolset(storage=storage)

        async def run_agent():
            run_result = await runner.run_agent(
                toolset_factory=toolset_factory,
                prompt=prompt,
                storage=storage,
                system_prompt=BEAM_SYSTEM_PROMPT,
            )

            if run_result.error:
                raise RuntimeError(f"Agent execution failed: {run_result.error}")

            return run_result.output

        return asyncio.run(run_agent())

    return beam_task


def create_beam_dataset(config: EvaluationConfig) -> tuple[Dataset, Callable]:
    """Create a pydantic-evals Dataset for Beam toolset."""
    beam_task = create_beam_task_function(config)

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
        name="beam_toolset_evaluation",
        cases=pydantic_cases,
        evaluators=create_evaluators(config),
    )

    return dataset, beam_task


async def evaluate_beam_toolset(config: EvaluationConfig):
    """Evaluate Beam toolset using pydantic-evals.

    This creates an Experiment that will show up in Logfire.

    Args:
        config: Evaluation configuration.

    Returns:
        EvaluationReport from pydantic-evals.
    """
    dataset, beam_task = create_beam_dataset(config)
    # The experiment name comes from the function name (beam_task)
    report = await dataset.evaluate(beam_task)
    return report

