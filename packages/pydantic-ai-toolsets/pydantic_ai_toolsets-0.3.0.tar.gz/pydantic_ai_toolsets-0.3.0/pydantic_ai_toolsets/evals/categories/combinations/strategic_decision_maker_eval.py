"""Evaluation for Strategic Decision Maker workflow using pydantic-evals Dataset API."""

from typing import Any, Callable

from pydantic_evals import Case, Dataset

from pydantic_ai_toolsets.evals.config import EvaluationConfig
from pydantic_ai_toolsets.evals.datasets.combination_cases import STRATEGIC_DECISION_MAKER_CASES
from pydantic_ai_toolsets.evals.evaluators import create_evaluators
from pydantic_ai_toolsets import (
    STRATEGIC_DECISION_MAKER,
    create_persona_debate_toolset,
    create_mcts_toolset,
    create_reflection_toolset,
    PersonaDebateStorage,
    MCTSStorage,
    ReflectionStorage,
    MetaOrchestratorStorage,
    create_workflow_agent,
)


def create_strategic_decision_maker_task_function(
    config: EvaluationConfig,
) -> Callable[[dict[str, Any]], str]:
    """Create a task function for Strategic Decision Maker workflow evaluation."""
    def strategic_decision_maker_task(inputs: dict[str, Any]) -> str:
        """Task function for pydantic-evals."""
        import asyncio

        prompt = inputs.get("prompt", "")
        if not prompt:
            return ""

        # Create storages for all toolsets
        persona_debate_storage = PersonaDebateStorage(track_usage=True)
        mcts_storage = MCTSStorage(track_usage=True)
        reflection_storage = ReflectionStorage(track_usage=True)
        orchestrator_storage = MetaOrchestratorStorage(track_usage=True)

        # Create toolsets
        persona_debate_toolset = create_persona_debate_toolset(persona_debate_storage, id="persona_debate")
        mcts_toolset = create_mcts_toolset(mcts_storage, id="mcts")
        reflection_toolset = create_reflection_toolset(reflection_storage, id="reflection")

        storages_map = {
            "persona_debate": persona_debate_storage,
            "mcts": mcts_storage,
            "reflection": reflection_storage,
        }

        async def run_agent():
            try:
                # Ensure environment is set up (API key)
                config.setup_environment()
                
                # Create agent with workflow template
                agent = create_workflow_agent(
                    model=config.get_model_string(),
                    workflow_template=STRATEGIC_DECISION_MAKER,
                    toolsets=[persona_debate_toolset, mcts_toolset, reflection_toolset],
                    storages=storages_map,
                    orchestrator_storage=orchestrator_storage,
                )

                # Run agent
                result = await agent.run(prompt)

                # Extract output from pydantic-ai result
                # Try multiple ways to get the output (same pattern as base.py)
                output = ""
                try:
                    if hasattr(result, "data"):
                        data_value = result.data
                        output = str(data_value) if data_value is not None else ""
                    elif hasattr(result, "output"):
                        output_value = result.output
                        output = str(output_value) if output_value is not None else ""
                    elif hasattr(result, "response"):
                        response_value = result.response
                        output = str(response_value) if response_value is not None else ""
                    else:
                        # If no data attribute, try to convert the result to string
                        if isinstance(result, str):
                            output = result
                        else:
                            output = str(result) if result is not None else ""
                except Exception as e:
                    # If extraction fails, log and use empty string
                    output = str(result) if result is not None else ""

                # Validate workflow progression (non-fatal check)
                # Note: The agent can produce correct output without explicitly starting a workflow.
                # The workflow is an organizational mechanism, but toolsets can work independently.
                workflow = orchestrator_storage.get_active_workflow()
                if not workflow:
                    # If we have output, return it even without a workflow
                    # The workflow check is informative but not required for success
                    if output:
                        return output
                    # Only fail if we have no output AND no workflow
                    return "Error: No active workflow found and no output produced."

                return output
            except Exception as e:
                # Re-raise with context so pydantic-evals can capture it properly
                import traceback
                error_msg = f"Agent execution failed: {str(e)}\n{traceback.format_exc()}"
                raise RuntimeError(error_msg) from e

        # Run the async function - pydantic-evals calls this synchronously
        # pydantic-evals task functions are synchronous, so asyncio.run() should work
        try:
            return asyncio.run(run_agent())
        except RuntimeError as e:
            # Check if this is the "no running event loop" error
            if "no running event loop" in str(e).lower() or "get_running_loop" in str(e):
                # This shouldn't happen, but if it does, just use asyncio.run() normally
                import traceback
                error_msg = f"Unexpected event loop error: {str(e)}\n{traceback.format_exc()}"
                raise RuntimeError(error_msg) from e
            # Re-raise other RuntimeErrors
            raise
        except Exception as e:
            # Re-raise with full context
            import traceback
            error_msg = f"Failed to run agent: {str(e)}\n{traceback.format_exc()}"
            raise RuntimeError(error_msg) from e

    return strategic_decision_maker_task


def create_strategic_decision_maker_dataset(config: EvaluationConfig) -> tuple[Dataset, Callable]:
    """Create a pydantic-evals Dataset for Strategic Decision Maker workflow."""
    strategic_decision_maker_task = create_strategic_decision_maker_task_function(config)

    pydantic_cases = []
    for case in STRATEGIC_DECISION_MAKER_CASES:
        pydantic_cases.append(
            Case(
                name=case.name,
                inputs={"prompt": case.prompt},
                metadata={
                    "workflow_template": case.workflow_template,
                    "expected_toolsets": case.expected_toolsets,
                    "expected_transitions": case.expected_transitions,
                    "expected_prefixed_tools": case.expected_prefixed_tools or [],
                    "min_storage_items": case.min_storage_items,
                    "difficulty": case.difficulty,
                    "expected_cross_links": case.expected_cross_links,
                },
            )
        )

    dataset = Dataset(
        name="strategic_decision_maker_workflow_evaluation",
        cases=pydantic_cases,
        evaluators=create_evaluators(config),
    )

    return dataset, strategic_decision_maker_task


async def evaluate_strategic_decision_maker_workflow(config: EvaluationConfig):
    """Evaluate Strategic Decision Maker workflow using pydantic-evals.

    Args:
        config: Evaluation configuration.

    Returns:
        EvaluationReport from pydantic-evals.
    """
    dataset, strategic_decision_maker_task = create_strategic_decision_maker_dataset(config)
    report = await dataset.evaluate(strategic_decision_maker_task)
    return report
