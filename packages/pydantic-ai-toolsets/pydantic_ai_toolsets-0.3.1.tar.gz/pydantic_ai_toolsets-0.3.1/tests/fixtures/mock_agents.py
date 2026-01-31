"""Mock agent utilities for testing."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

from pydantic_ai.toolsets import AbstractToolset


class MockAgent:
    """Mock pydantic-ai Agent for testing."""
    
    def __init__(self, model: str = "mock:test", toolsets: list[AbstractToolset[Any]] | None = None):
        """Initialize mock agent."""
        self.model = model
        self.toolsets = toolsets or []
        self.system_prompt = ""
        self._run_calls: list[dict[str, Any]] = []
    
    async def run(self, prompt: str, **kwargs: Any) -> Any:
        """Mock run method."""
        call_info = {"prompt": prompt, "kwargs": kwargs}
        self._run_calls.append(call_info)
        return MagicMock(data="mock response", tool_calls=[])


class MockToolset(AbstractToolset[Any]):
    """Mock toolset for testing combinations."""
    
    def __init__(self, id: str | None = None, label: str | None = None):
        """Initialize mock toolset."""
        self._id = id
        self._label = label
        self._tools: list[Any] = []
    
    @property
    def id(self) -> str | None:
        """Get toolset ID."""
        return self._id
    
    @property
    def label(self) -> str | None:
        """Get toolset label."""
        return self._label
    
    def prefixed(self, prefix: str) -> AbstractToolset[Any]:
        """Create prefixed version."""
        prefixed_toolset = MockToolset(id=self._id, label=self._label)
        prefixed_toolset._id = f"{prefix}{self._id}" if self._id else None
        return prefixed_toolset
    
    async def call_tool(self, tool_name: str, tool_args: dict[str, Any]) -> Any:
        """Mock call_tool implementation."""
        return MagicMock()
    
    def get_tools(self) -> list[Any]:
        """Mock get_tools implementation."""
        return self._tools


def create_mock_tool_invocation(tool_name: str, input_data: dict[str, Any], output_data: Any) -> dict[str, Any]:
    """Create a mock tool invocation record."""
    return {
        "tool_name": tool_name,
        "input": input_data,
        "output": output_data,
        "timestamp": 1234567890.0,
    }
