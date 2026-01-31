"""Base classes and utilities for toolset evaluation."""

from __future__ import annotations

import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Generic, TypeVar

from pydantic_ai import Agent
from pydantic_ai.toolsets import FunctionToolset

from pydantic_ai_toolsets.evals.config import EvaluationConfig, default_config

T = TypeVar("T")
S = TypeVar("S")  # Storage type


@dataclass
class EvaluationResult:
    """Result from evaluating a single case."""

    case_name: str
    toolset_name: str
    output: str
    storage_state: dict[str, Any] = field(default_factory=dict)
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    execution_time: float = 0.0
    token_usage: dict[str, int] = field(default_factory=dict)
    error: str | None = None
    scores: dict[str, float] = field(default_factory=dict)


@dataclass
class AgentRunResult:
    """Result from running an agent."""

    output: str
    storage: Any | None = None
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    execution_time: float = 0.0
    token_usage: dict[str, int] = field(default_factory=dict)
    error: str | None = None


class AgentRunner:
    """Utility to run agents with toolsets in a standardized way."""

    def __init__(self, config: EvaluationConfig | None = None):
        """Initialize the agent runner.

        Args:
            config: Evaluation configuration. Uses default if not provided.
        """
        self.config = config or default_config
        self.model_string = self.config.get_model_string()
        # Set up environment for OpenRouter API key BEFORE creating agents
        # This must happen early so pydantic-ai can pick it up
        self.config.setup_environment()

    async def run_agent(
        self,
        toolset_factory: Callable[[], FunctionToolset[Any]],
        prompt: str,
        storage: Any | None = None,
        system_prompt: str | None = None,
    ) -> AgentRunResult:
        """Run an agent with a toolset.

        Args:
            toolset_factory: Function that creates the toolset (may accept storage).
            prompt: User prompt to run.
            storage: Optional storage object to pass to toolset factory.
            system_prompt: Optional system prompt.

        Returns:
            AgentRunResult with output, storage, tool calls, timing, etc.
        """
        start_time = time.time()
        error: str | None = None
        output = ""
        tool_calls: list[dict[str, Any]] = []
        token_usage: dict[str, int] = {}

        try:
            # Create toolset
            # The toolset_factory is a closure that already captures storage,
            # so it doesn't accept any arguments
            toolset = toolset_factory()

            # Create agent with OpenRouter model string directly
            # The API key is already set in environment via setup_environment()
            agent = Agent(
                self.model_string,
                toolsets=[toolset],
                system_prompt=system_prompt,
            )

            # Run agent
            agent_result = await agent.run(prompt)

            # Extract information from pydantic-ai result
            # pydantic-ai Agent.run() returns a RunResult object
            # The actual data is in agent_result.data
            output = ""
            try:
                # Debug: print the type of agent_result
                result_type = type(agent_result).__name__
                
                # Try to get the data attribute
                if hasattr(agent_result, "data"):
                    data_value = agent_result.data
                    output = str(data_value) if data_value is not None else ""
                elif hasattr(agent_result, "output"):
                    output_value = agent_result.output
                    output = str(output_value) if output_value is not None else ""
                elif hasattr(agent_result, "response"):
                    response_value = agent_result.response
                    output = str(response_value) if response_value is not None else ""
                else:
                    # If no data attribute, try to convert the result to string
                    # But first check if it's already a string
                    if isinstance(agent_result, str):
                        output = agent_result
                    else:
                        output = str(agent_result) if agent_result is not None else ""
                        # Log warning if we couldn't find the expected attribute
                        print(f"Warning: agent_result type is {result_type}, no 'data'/'output'/'response' attribute found")
            except AttributeError as e:
                # If extraction fails due to AttributeError, log and use empty string
                print(f"ERROR: Could not extract output from agent result (type: {type(agent_result).__name__}): {e}")
                import traceback
                traceback.print_exc()
                output = str(agent_result) if agent_result is not None else ""
            except Exception as e:
                # If extraction fails for any other reason, log and use empty string
                print(f"Warning: Unexpected error extracting output: {e}")
                output = str(agent_result) if agent_result is not None else ""
            
            execution_time = time.time() - start_time

            # Extract tool calls from agent_result
            # Try multiple ways to get tool calls
            if hasattr(agent_result, "all_messages"):
                try:
                    for msg in agent_result.all_messages():
                        if hasattr(msg, "tool_calls") and msg.tool_calls:
                            for tool_call in msg.tool_calls:
                                tool_calls.append(
                                    {
                                        "name": getattr(tool_call, "name", str(tool_call)),
                                        "args": getattr(tool_call, "args", {}),
                                    }
                                )
                except Exception:
                    pass  # Tool calls extraction is optional

            # Extract token usage if available
            if hasattr(agent_result, "usage") and agent_result.usage:
                try:
                    token_usage = {
                        "input_tokens": getattr(agent_result.usage, "input_tokens", 0) or 0,
                        "output_tokens": getattr(agent_result.usage, "output_tokens", 0) or 0,
                        "total_tokens": getattr(agent_result.usage, "total_tokens", 0) or 0,
                    }
                except Exception:
                    pass  # Token usage extraction is optional

            return AgentRunResult(
                output=output,
                storage=storage,
                tool_calls=tool_calls,
                execution_time=execution_time,
                token_usage=token_usage,
            )

        except Exception as e:
            error = str(e)
            import traceback
            error_details = f"{error}\n{traceback.format_exc()}"
            execution_time = time.time() - start_time
            
            # Check if this is an API validation error (likely transient)
            error_str_lower = error.lower()
            is_api_error = (
                "validation" in error_str_lower
                or "openrouter" in error_str_lower
                or "invalid response" in error_str_lower
                or "unexpectedmodelbehavior" in error_str_lower
            )
            
            if is_api_error:
                # Add helpful context for API errors
                error_details = (
                    f"API Error (likely transient - rate limit, timeout, or API issue):\n"
                    f"{error}\n\n"
                    f"Full traceback:\n{traceback.format_exc()}\n\n"
                    f"Suggestions:\n"
                    f"- Check API key and rate limits\n"
                    f"- Retry the request\n"
                    f"- Check OpenRouter status"
                )
            
            # Print error for debugging
            print(f"ERROR in agent.run: {error}")
            if is_api_error:
                print("NOTE: This appears to be an API error. Consider retrying.")
            
            return AgentRunResult(
                output="",
                storage=storage,
                tool_calls=tool_calls,
                execution_time=execution_time,
                token_usage=token_usage,
                error=error_details,
            )


class StorageInspector:
    """Utilities to inspect toolset storage states."""

    @staticmethod
    def extract_storage_state(storage: Any) -> dict[str, Any]:
        """Extract state from a storage object.

        Args:
            storage: Storage object from a toolset.

        Returns:
            Dictionary representation of storage state.
        """
        if storage is None:
            return {}

        state: dict[str, Any] = {}

        # Extract usage metrics if available (from new metrics system)
        if hasattr(storage, "metrics") and storage.metrics is not None:
            metrics = storage.metrics
            state["usage_metrics"] = {
                "total_invocations": len(metrics.invocations),
                "total_input_tokens": metrics.total_input_tokens(),
                "total_output_tokens": metrics.total_output_tokens(),
                "total_tokens": metrics.total_tokens(),
                "total_duration_ms": metrics.total_duration_ms(),
                "invocations_by_tool": metrics.invocation_count(),
            }

        # Extract statistics if available
        if hasattr(storage, "get_statistics") and callable(storage.get_statistics):
            state["statistics"] = storage.get_statistics()

        # Common storage attributes
        if hasattr(storage, "todos"):
            state["todos"] = [
                {
                    "content": todo.content,
                    "status": todo.status,
                }
                for todo in storage.todos
            ]

        if hasattr(storage, "thoughts"):
            state["thoughts"] = [
                {
                    "thought_number": thought.thought_number,
                    "thought": thought.thought,
                    "is_revision": thought.is_revision,
                }
                for thought in storage.thoughts
            ]

        if hasattr(storage, "nodes"):
            state["nodes"] = {
                node_id: {
                    "content": node.content,
                    "status": getattr(node, "status", None),
                }
                for node_id, node in storage.nodes.items()
            }

        if hasattr(storage, "candidates"):
            state["candidates"] = [
                {
                    "candidate_id": c.candidate_id,
                    "content": c.content,
                    "score": getattr(c, "score", None),
                }
                for c in storage.candidates
            ]

        if hasattr(storage, "search_results"):
            state["search_results"] = {
                result_id: {
                    "query": result.query,
                    "title": result.title,
                    "url": result.url,
                    "source_type": result.source_type.value if hasattr(result.source_type, "value") else str(result.source_type),
                    "date": result.date,
                    "image_url": result.image_url,
                    "image_width": result.image_width,
                    "image_height": result.image_height,
                }
                for result_id, result in storage.search_results.items()
            }

        if hasattr(storage, "extracted_contents"):
            state["extracted_contents"] = {
                content_id: {
                    "url": content.url,
                    "format": content.output_format.value if hasattr(content.output_format, "value") else str(content.output_format),
                }
                for content_id, content in storage.extracted_contents.items()
            }

        # For debate/persona toolsets
        if hasattr(storage, "sessions"):
            state["sessions"] = len(storage.sessions) if isinstance(storage.sessions, dict) else 0

        if hasattr(storage, "positions"):
            state["positions"] = len(storage.positions) if isinstance(storage.positions, dict) else 0

        if hasattr(storage, "personas"):
            state["personas"] = len(storage.personas) if isinstance(storage.personas, dict) else 0

        # For reflection toolsets
        if hasattr(storage, "outputs"):
            state["outputs"] = [
                {
                    "iteration": output.iteration,
                    "is_final": getattr(output, "is_final", False),
                }
                for output in storage.outputs
            ]

        # For self-ask toolsets
        if hasattr(storage, "questions"):
            state["questions"] = [
                {
                    "question_id": q.question_id,
                    "depth": q.depth,
                    "is_main": q.is_main,
                    "status": q.status.value if hasattr(q.status, "value") else str(q.status),
                }
                for q in storage.questions.values()
            ]

        if hasattr(storage, "answers"):
            state["answers"] = [
                {
                    "answer_id": a.answer_id,
                    "question_id": a.question_id,
                    "confidence_score": a.confidence_score,
                    "requires_followup": a.requires_followup,
                }
                for a in storage.answers.values()
            ]

        if hasattr(storage, "final_answers"):
            state["final_answers"] = [
                {
                    "final_answer_id": fa.final_answer_id,
                    "main_question_id": fa.main_question_id,
                    "is_complete": fa.is_complete,
                    "composed_from_count": len(fa.composed_from_answers),
                }
                for fa in storage.final_answers.values()
            ]

        return state


class ToolsetEvaluator(ABC, Generic[T, S]):
    """Base class for toolset evaluators."""

    def __init__(
        self,
        toolset_name: str,
        config: EvaluationConfig | None = None,
    ):
        """Initialize the evaluator.

        Args:
            toolset_name: Name of the toolset being evaluated.
            config: Evaluation configuration.
        """
        self.toolset_name = toolset_name
        self.config = config or default_config
        self.runner = AgentRunner(self.config)

    @abstractmethod
    def create_toolset_factory(
        self, storage: S | None = None
    ) -> Callable[[], FunctionToolset[Any]]:
        """Create a factory function for the toolset.

        Args:
            storage: Optional storage object.

        Returns:
            Function that creates the toolset.
        """
        pass

    @abstractmethod
    def create_storage(self) -> S:
        """Create a new storage instance.

        Returns:
            Storage instance.
        """
        pass

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Get the system prompt for this toolset.

        Returns:
            System prompt string.
        """
        pass

    async def evaluate_case(
        self, prompt: str, expected_output: T | None = None
    ) -> EvaluationResult:
        """Evaluate a single test case.

        Args:
            prompt: User prompt.
            expected_output: Expected output (optional).

        Returns:
            EvaluationResult with scores and metrics.
        """
        storage = self.create_storage()
        toolset_factory = self.create_toolset_factory(storage=storage)
        system_prompt = self.get_system_prompt()

        run_result = await self.runner.run_agent(
            toolset_factory=toolset_factory,
            prompt=prompt,
            storage=storage,
            system_prompt=system_prompt,
        )

        # Extract storage state
        storage_state = StorageInspector.extract_storage_state(storage)

        # Create evaluation result
        result = EvaluationResult(
            case_name=prompt,
            toolset_name=self.toolset_name,
            output=run_result.output,
            storage_state=storage_state,
            tool_calls=run_result.tool_calls,
            execution_time=run_result.execution_time,
            token_usage=run_result.token_usage,
            error=run_result.error,
        )

        return result

