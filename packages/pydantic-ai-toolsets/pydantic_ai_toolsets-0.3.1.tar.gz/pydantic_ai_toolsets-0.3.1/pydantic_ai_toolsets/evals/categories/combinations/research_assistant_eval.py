"""Evaluation for Research Assistant workflow using pydantic-evals Dataset API."""

from typing import Any, Callable

from pydantic_evals import Case, Dataset

from pydantic_ai_toolsets.evals.config import EvaluationConfig
from pydantic_ai_toolsets.evals.datasets.combination_cases import RESEARCH_ASSISTANT_CASES
from pydantic_ai_toolsets.evals.evaluators import create_evaluators
from pydantic_ai_toolsets import (
    RESEARCH_ASSISTANT,
    create_search_toolset,
    create_self_ask_toolset,
    create_self_refine_toolset,
    create_todo_toolset,
    SearchStorage,
    SelfAskStorage,
    SelfRefineStorage,
    TodoStorage,
    MetaOrchestratorStorage,
    create_workflow_agent,
)


def create_research_assistant_task_function(
    config: EvaluationConfig,
) -> Callable[[dict[str, Any]], str]:
    """Create a task function for Research Assistant workflow evaluation."""
    def research_assistant_task(inputs: dict[str, Any]) -> str:
        """Task function for pydantic-evals."""
        import asyncio

        prompt = inputs.get("prompt", "")
        if not prompt:
            return ""

        # Create storages for all toolsets
        search_storage = SearchStorage(track_usage=True)
        self_ask_storage = SelfAskStorage(track_usage=True)
        self_refine_storage = SelfRefineStorage(track_usage=True)
        todo_storage = TodoStorage(track_usage=True)
        orchestrator_storage = MetaOrchestratorStorage(track_usage=True)

        # Create toolsets (original function names preserved - backward compatible)
        search_toolset = create_search_toolset(search_storage, id="search")
        self_ask_toolset = create_self_ask_toolset(self_ask_storage, id="self_ask")
        self_refine_toolset = create_self_refine_toolset(self_refine_storage, id="self_refine")
        todo_toolset = create_todo_toolset(todo_storage, id="todo")

        storages_map = {
            "search": search_storage,
            "self_ask": self_ask_storage,
            "self_refine": self_refine_storage,
            "todo": todo_storage,
        }

        async def run_agent():
            try:
                # Ensure environment is set up (API key)
                config.setup_environment()
                
                # Create agent with workflow template
                agent = create_workflow_agent(
                    model=config.get_model_string(),
                    workflow_template=RESEARCH_ASSISTANT,
                    toolsets=[search_toolset, self_ask_toolset, self_refine_toolset, todo_toolset],
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

                # Return the result
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
        except Exception as e:
            # Re-raise with full context so pydantic-evals can capture it properly
            import traceback
            error_msg = f"Failed to run agent: {str(e)}\n{traceback.format_exc()}"
            raise RuntimeError(error_msg) from e

    return research_assistant_task


def create_research_assistant_dataset(config: EvaluationConfig) -> tuple[Dataset, Callable]:
    """Create a pydantic-evals Dataset for Research Assistant workflow."""
    research_assistant_task = create_research_assistant_task_function(config)

    pydantic_cases = []
    for case in RESEARCH_ASSISTANT_CASES:
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
        name="research_assistant_workflow_evaluation",
        cases=pydantic_cases,
        evaluators=create_evaluators(config),
    )

    return dataset, research_assistant_task


async def evaluate_research_assistant_workflow(config: EvaluationConfig):
    """Evaluate Research Assistant workflow using pydantic-evals.

    Args:
        config: Evaluation configuration.

    Returns:
        EvaluationReport from pydantic-evals.
    """
    dataset, research_assistant_task = create_research_assistant_dataset(config)
    report = await dataset.evaluate(research_assistant_task)
    return report
