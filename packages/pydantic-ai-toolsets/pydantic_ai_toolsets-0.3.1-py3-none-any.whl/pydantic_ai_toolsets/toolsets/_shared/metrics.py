"""Shared metrics infrastructure for usage cost tracking.

Provides common types and utilities for tracking tool invocations,
token estimates, and performance metrics across all toolset packages.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, TypeVar

T = TypeVar("T")


def estimate_tokens(text: str) -> int:
    """Estimate token count for a string.

    Uses a simple heuristic: ~4 characters per token on average.
    This is a rough estimate suitable for cost tracking purposes.

    Args:
        text: The text to estimate tokens for.

    Returns:
        Estimated token count.
    """
    if not text:
        return 0
    # Rough estimate: ~4 characters per token for English text
    # This matches typical tokenizer behavior for GPT-style models
    return max(1, len(text) // 4)


@dataclass
class ToolInvocation:
    """Record of a single tool invocation.

    Attributes:
        tool_name: Name of the tool that was invoked.
        timestamp: Unix timestamp when the tool was called.
        input_tokens: Estimated tokens in the input/parameters.
        output_tokens: Estimated tokens in the output/response.
        duration_ms: Execution duration in milliseconds.
    """

    tool_name: str
    timestamp: float
    input_tokens: int = 0
    output_tokens: int = 0
    duration_ms: float = 0.0


@dataclass
class UsageMetrics:
    """Aggregated usage metrics for a toolset session.

    Tracks all tool invocations and provides summary statistics.
    Thread-safe for basic append operations.

    Example:
        ```python
        metrics = UsageMetrics()
        metrics.record_invocation("read_thoughts", "", "Chain of thoughts:\\n...")
        print(f"Total tokens: {metrics.total_tokens()}")
        ```
    """

    invocations: list[ToolInvocation] = field(default_factory=list)

    def record_invocation(
        self,
        tool_name: str,
        input_text: str,
        output_text: str,
        duration_ms: float = 0.0,
    ) -> ToolInvocation:
        """Record a tool invocation with automatic token estimation.

        Args:
            tool_name: Name of the tool.
            input_text: Serialized input parameters.
            output_text: Tool output/response.
            duration_ms: Execution time in milliseconds.

        Returns:
            The created ToolInvocation record.
        """
        invocation = ToolInvocation(
            tool_name=tool_name,
            timestamp=time.time(),
            input_tokens=estimate_tokens(input_text),
            output_tokens=estimate_tokens(output_text),
            duration_ms=duration_ms,
        )
        self.invocations.append(invocation)
        return invocation

    def total_input_tokens(self) -> int:
        """Get total estimated input tokens across all invocations."""
        return sum(inv.input_tokens for inv in self.invocations)

    def total_output_tokens(self) -> int:
        """Get total estimated output tokens across all invocations."""
        return sum(inv.output_tokens for inv in self.invocations)

    def total_tokens(self) -> int:
        """Get total estimated tokens (input + output)."""
        return self.total_input_tokens() + self.total_output_tokens()

    def invocation_count(self) -> dict[str, int]:
        """Get count of invocations per tool.

        Returns:
            Dictionary mapping tool names to invocation counts.
        """
        counts: dict[str, int] = {}
        for inv in self.invocations:
            counts[inv.tool_name] = counts.get(inv.tool_name, 0) + 1
        return counts

    def total_duration_ms(self) -> float:
        """Get total execution time across all invocations."""
        return sum(inv.duration_ms for inv in self.invocations)

    def average_duration_ms(self) -> float:
        """Get average execution time per invocation."""
        if not self.invocations:
            return 0.0
        return self.total_duration_ms() / len(self.invocations)

    def to_dict(self) -> dict[str, Any]:
        """Export metrics as a dictionary for serialization.

        Returns:
            Dictionary with all metrics data.
        """
        return {
            "total_invocations": len(self.invocations),
            "total_input_tokens": self.total_input_tokens(),
            "total_output_tokens": self.total_output_tokens(),
            "total_tokens": self.total_tokens(),
            "total_duration_ms": self.total_duration_ms(),
            "invocation_counts": self.invocation_count(),
            "invocations": [
                {
                    "tool_name": inv.tool_name,
                    "timestamp": inv.timestamp,
                    "input_tokens": inv.input_tokens,
                    "output_tokens": inv.output_tokens,
                    "duration_ms": inv.duration_ms,
                }
                for inv in self.invocations
            ],
        }

    def clear(self) -> None:
        """Clear all recorded invocations."""
        self.invocations.clear()


def create_tracking_wrapper(
    metrics: UsageMetrics,
    tool_name: str,
    func: Callable[..., T],
) -> Callable[..., T]:
    """Create a wrapper that tracks tool invocations.

    Args:
        metrics: UsageMetrics instance to record to.
        tool_name: Name of the tool being wrapped.
        func: The tool function to wrap.

    Returns:
        Wrapped function that records metrics.
    """
    import asyncio
    import json

    async def async_wrapper(*args: Any, **kwargs: Any) -> T:
        # Serialize input for token estimation
        input_parts = []
        if args:
            input_parts.append(str(args))
        if kwargs:
            try:
                input_parts.append(json.dumps(kwargs, default=str))
            except (TypeError, ValueError):
                input_parts.append(str(kwargs))
        input_text = " ".join(input_parts)

        start_time = time.perf_counter()
        result = await func(*args, **kwargs)
        duration_ms = (time.perf_counter() - start_time) * 1000

        # Serialize output for token estimation
        output_text = str(result) if result is not None else ""

        metrics.record_invocation(tool_name, input_text, output_text, duration_ms)
        return result

    def sync_wrapper(*args: Any, **kwargs: Any) -> T:
        # Serialize input for token estimation
        input_parts = []
        if args:
            input_parts.append(str(args))
        if kwargs:
            try:
                input_parts.append(json.dumps(kwargs, default=str))
            except (TypeError, ValueError):
                input_parts.append(str(kwargs))
        input_text = " ".join(input_parts)

        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        duration_ms = (time.perf_counter() - start_time) * 1000

        # Serialize output for token estimation
        output_text = str(result) if result is not None else ""

        metrics.record_invocation(tool_name, input_text, output_text, duration_ms)
        return result

    # Return appropriate wrapper based on function type
    if asyncio.iscoroutinefunction(func):
        return async_wrapper  # type: ignore[return-value]
    return sync_wrapper  # type: ignore[return-value]

