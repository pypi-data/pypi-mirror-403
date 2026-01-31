"""Evaluation for ToT (Tree of Thoughts) toolset using pydantic-evals Dataset API."""

from typing import Any, Callable

from pydantic_ai.toolsets import FunctionToolset
from pydantic_evals import Case, Dataset

from pydantic_ai_toolsets.evals.base import AgentRunner
from pydantic_ai_toolsets.evals.config import EvaluationConfig
from pydantic_ai_toolsets.evals.datasets.thinking_cases import THINKING_CASES
from pydantic_ai_toolsets.evals.evaluators import create_evaluators

try:
    from pydantic_ai_toolsets.toolsets.tree_of_thought_reasoning import ToTStorage, create_tot_toolset
    from pydantic_ai_toolsets.toolsets.tree_of_thought_reasoning.toolset import TOT_SYSTEM_PROMPT
except ImportError:
    raise ImportError(
        "pydantic_ai_tot not found. Install it or check imports."
    )


def create_tot_task_function(
    config: EvaluationConfig,
) -> Callable[[dict[str, Any]], str]:
    """Create a task function for ToT toolset evaluation."""
    runner = AgentRunner(config)

    def tot_task(inputs: dict[str, Any]) -> str:
        """Task function for pydantic-evals."""
        import asyncio

        prompt = inputs.get("prompt", "")
        if not prompt:
            return ""

        storage = ToTStorage()

        def toolset_factory() -> FunctionToolset[Any]:
            return create_tot_toolset(storage=storage)

        async def run_agent():
            # Retry logic for API errors
            max_retries = 3
            retry_delay = 1.0
            
            for attempt in range(max_retries):
                try:
                    run_result = await runner.run_agent(
                        toolset_factory=toolset_factory,
                        prompt=prompt,
                        storage=storage,
                        system_prompt=TOT_SYSTEM_PROMPT,
                    )

                    if run_result.error:
                        # Check if it's an API error that might be transient
                        error_lower = run_result.error.lower()
                        is_transient = (
                            "validation" in error_lower
                            or "openrouter" in error_lower
                            or "invalid response" in error_lower
                        )
                        
                        if is_transient and attempt < max_retries - 1:
                            print(f"API error detected, retrying ({attempt + 1}/{max_retries})...")
                            await asyncio.sleep(retry_delay * (attempt + 1))
                            continue
                        
                        raise RuntimeError(f"Agent execution failed: {run_result.error}")

                    return run_result.output
                    
                except RuntimeError:
                    # Re-raise RuntimeError immediately (it's from our code)
                    raise
                except Exception as e:
                    # For other exceptions, check if retryable
                    error_str = str(e).lower()
                    is_transient = (
                        "validation" in error_str
                        or "openrouter" in error_str
                        or "invalid response" in error_str
                        or "timeout" in error_str
                    )
                    
                    if is_transient and attempt < max_retries - 1:
                        print(f"Transient error detected, retrying ({attempt + 1}/{max_retries}): {e}")
                        await asyncio.sleep(retry_delay * (attempt + 1))
                        continue
                    
                    # Not retryable or out of retries
                    raise RuntimeError(f"Agent execution failed after {attempt + 1} attempts: {e}") from e
            
            # Should not reach here, but just in case
            raise RuntimeError("Failed to execute agent after all retries")

        return asyncio.run(run_agent())

    return tot_task


def create_tot_dataset(config: EvaluationConfig) -> tuple[Dataset, Callable]:
    """Create a pydantic-evals Dataset for ToT toolset."""
    tot_task = create_tot_task_function(config)

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
        name="tot_toolset_evaluation",
        cases=pydantic_cases,
        evaluators=create_evaluators(config),
    )

    return dataset, tot_task


async def evaluate_tot_toolset(config: EvaluationConfig):
    """Evaluate ToT toolset using pydantic-evals.

    This creates an Experiment that will show up in Logfire.

    Args:
        config: Evaluation configuration.

    Returns:
        EvaluationReport from pydantic-evals.
    """
    dataset, tot_task = create_tot_dataset(config)
    # The experiment name comes from the function name (tot_task)
    report = await dataset.evaluate(tot_task)
    return report

