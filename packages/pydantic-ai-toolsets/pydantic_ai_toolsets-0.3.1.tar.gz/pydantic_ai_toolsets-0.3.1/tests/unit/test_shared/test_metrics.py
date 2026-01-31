"""Unit tests for metrics utilities."""

from __future__ import annotations

import asyncio
import time

import pytest

from pydantic_ai_toolsets.toolsets._shared.metrics import (
    ToolInvocation,
    UsageMetrics,
    create_tracking_wrapper,
    estimate_tokens,
)


class TestEstimateTokens:
    """Test suite for estimate_tokens function."""

    def test_empty_string(self):
        """Test empty string returns 0."""
        assert estimate_tokens("") == 0

    def test_short_string(self):
        """Test short string returns at least 1."""
        assert estimate_tokens("a") >= 1
        assert estimate_tokens("test") >= 1

    def test_token_estimation(self):
        """Test token estimation formula."""
        # ~4 characters per token
        text = "a" * 8  # 8 characters
        assert estimate_tokens(text) == 2
        
        text = "a" * 12  # 12 characters
        assert estimate_tokens(text) == 3

    def test_long_string(self):
        """Test long string estimation."""
        text = "This is a longer string with multiple words and characters."
        tokens = estimate_tokens(text)
        assert tokens > 0
        # Should be approximately length / 4
        assert tokens == len(text) // 4


class TestToolInvocation:
    """Test suite for ToolInvocation dataclass."""

    def test_initialization(self):
        """Test ToolInvocation initialization."""
        invocation = ToolInvocation(
            tool_name="test_tool",
            timestamp=1234567890.0,
            input_tokens=10,
            output_tokens=20,
            duration_ms=100.0,
        )
        
        assert invocation.tool_name == "test_tool"
        assert invocation.timestamp == 1234567890.0
        assert invocation.input_tokens == 10
        assert invocation.output_tokens == 20
        assert invocation.duration_ms == 100.0

    def test_default_values(self):
        """Test ToolInvocation default values."""
        invocation = ToolInvocation(
            tool_name="test_tool",
            timestamp=1234567890.0,
        )
        
        assert invocation.input_tokens == 0
        assert invocation.output_tokens == 0
        assert invocation.duration_ms == 0.0


class TestUsageMetrics:
    """Test suite for UsageMetrics class."""

    def test_initialization(self):
        """Test UsageMetrics initialization."""
        metrics = UsageMetrics()
        assert metrics.invocations == []

    def test_record_invocation(self):
        """Test recording an invocation."""
        metrics = UsageMetrics()
        invocation = metrics.record_invocation(
            tool_name="test_tool",
            input_text="input",
            output_text="output",
            duration_ms=50.0,
        )
        
        assert len(metrics.invocations) == 1
        assert invocation.tool_name == "test_tool"
        assert invocation.duration_ms == 50.0

    def test_record_invocation_token_estimation(self):
        """Test that record_invocation estimates tokens."""
        metrics = UsageMetrics()
        invocation = metrics.record_invocation(
            tool_name="test_tool",
            input_text="a" * 8,  # 8 chars = ~2 tokens
            output_text="b" * 12,  # 12 chars = ~3 tokens
        )
        
        assert invocation.input_tokens == 2
        assert invocation.output_tokens == 3

    def test_total_input_tokens(self):
        """Test total_input_tokens calculation."""
        metrics = UsageMetrics()
        metrics.record_invocation("tool1", "a" * 8, "", 0.0)
        metrics.record_invocation("tool2", "b" * 12, "", 0.0)
        
        assert metrics.total_input_tokens() == 5  # 2 + 3

    def test_total_output_tokens(self):
        """Test total_output_tokens calculation."""
        metrics = UsageMetrics()
        metrics.record_invocation("tool1", "", "a" * 8, 0.0)
        metrics.record_invocation("tool2", "", "b" * 12, 0.0)
        
        assert metrics.total_output_tokens() == 5  # 2 + 3

    def test_total_tokens(self):
        """Test total_tokens calculation."""
        metrics = UsageMetrics()
        metrics.record_invocation("tool1", "a" * 8, "b" * 8, 0.0)
        metrics.record_invocation("tool2", "c" * 12, "d" * 12, 0.0)
        
        assert metrics.total_tokens() == 10  # (2+2) + (3+3)

    def test_invocation_count(self):
        """Test invocation_count calculation."""
        metrics = UsageMetrics()
        metrics.record_invocation("tool1", "", "", 0.0)
        metrics.record_invocation("tool1", "", "", 0.0)
        metrics.record_invocation("tool2", "", "", 0.0)
        
        counts = metrics.invocation_count()
        assert counts["tool1"] == 2
        assert counts["tool2"] == 1

    def test_total_duration_ms(self):
        """Test total_duration_ms calculation."""
        metrics = UsageMetrics()
        metrics.record_invocation("tool1", "", "", 10.0)
        metrics.record_invocation("tool2", "", "", 20.0)
        metrics.record_invocation("tool3", "", "", 30.0)
        
        assert metrics.total_duration_ms() == 60.0

    def test_average_duration_ms(self):
        """Test average_duration_ms calculation."""
        metrics = UsageMetrics()
        metrics.record_invocation("tool1", "", "", 10.0)
        metrics.record_invocation("tool2", "", "", 20.0)
        metrics.record_invocation("tool3", "", "", 30.0)
        
        assert metrics.average_duration_ms() == pytest.approx(20.0)

    def test_average_duration_ms_empty(self):
        """Test average_duration_ms with no invocations."""
        metrics = UsageMetrics()
        assert metrics.average_duration_ms() == 0.0

    def test_to_dict(self):
        """Test to_dict serialization."""
        metrics = UsageMetrics()
        metrics.record_invocation("tool1", "input", "output", 10.0)
        
        data = metrics.to_dict()
        assert data["total_invocations"] == 1
        assert "total_input_tokens" in data
        assert "total_output_tokens" in data
        assert "total_tokens" in data
        assert "total_duration_ms" in data
        assert "invocation_counts" in data
        assert "invocations" in data
        assert len(data["invocations"]) == 1

    def test_clear(self):
        """Test clear method."""
        metrics = UsageMetrics()
        metrics.record_invocation("tool1", "", "", 0.0)
        metrics.record_invocation("tool2", "", "", 0.0)
        
        assert len(metrics.invocations) == 2
        metrics.clear()
        assert len(metrics.invocations) == 0


class TestCreateTrackingWrapper:
    """Test suite for create_tracking_wrapper function."""

    def test_sync_wrapper(self):
        """Test wrapper for sync function."""
        metrics = UsageMetrics()
        
        def test_func(x: int, y: int) -> int:
            return x + y
        
        wrapped = create_tracking_wrapper(metrics, "test_func", test_func)
        result = wrapped(2, 3)
        
        assert result == 5
        assert len(metrics.invocations) == 1
        assert metrics.invocations[0].tool_name == "test_func"

    def test_async_wrapper(self):
        """Test wrapper for async function."""
        metrics = UsageMetrics()
        
        async def test_async_func(x: int, y: int) -> int:
            await asyncio.sleep(0.01)
            return x + y
        
        wrapped = create_tracking_wrapper(metrics, "test_async_func", test_async_func)
        
        async def run_test():
            result = await wrapped(2, 3)
            assert result == 5
            assert len(metrics.invocations) == 1
            assert metrics.invocations[0].tool_name == "test_async_func"
            assert metrics.invocations[0].duration_ms > 0
        
        asyncio.run(run_test())

    def test_wrapper_tracks_duration(self):
        """Test that wrapper tracks duration."""
        metrics = UsageMetrics()
        
        def slow_func() -> str:
            time.sleep(0.1)
            return "done"
        
        wrapped = create_tracking_wrapper(metrics, "slow_func", slow_func)
        wrapped()
        
        assert metrics.invocations[0].duration_ms > 0

    def test_wrapper_serializes_inputs(self):
        """Test that wrapper serializes inputs."""
        metrics = UsageMetrics()
        
        def test_func(x: int, y: str, z: dict[str, int]) -> str:
            return f"{x}{y}{z}"
        
        wrapped = create_tracking_wrapper(metrics, "test_func", test_func)
        wrapped(1, "test", {"a": 2})
        
        invocation = metrics.invocations[0]
        assert invocation.input_tokens > 0

    def test_wrapper_serializes_outputs(self):
        """Test that wrapper serializes outputs."""
        metrics = UsageMetrics()
        
        def test_func() -> str:
            return "test output"
        
        wrapped = create_tracking_wrapper(metrics, "test_func", test_func)
        wrapped()
        
        invocation = metrics.invocations[0]
        assert invocation.output_tokens > 0

    def test_wrapper_handles_none_output(self):
        """Test that wrapper handles None output."""
        metrics = UsageMetrics()
        
        def test_func() -> None:
            return None
        
        wrapped = create_tracking_wrapper(metrics, "test_func", test_func)
        wrapped()
        
        invocation = metrics.invocations[0]
        assert invocation.output_tokens == 0

    def test_wrapper_handles_json_serialization_error(self):
        """Test that wrapper handles JSON serialization errors."""
        metrics = UsageMetrics()
        
        def test_func(obj: object) -> str:
            return "done"
        
        wrapped = create_tracking_wrapper(metrics, "test_func", test_func)
        # Pass object that can't be JSON serialized
        wrapped(object())
        
        # Should still record invocation
        assert len(metrics.invocations) == 1
