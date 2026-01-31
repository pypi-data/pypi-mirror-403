"""Configuration for evaluation framework."""

import os
from typing import Any

from pydantic import BaseModel


class EvaluationConfig(BaseModel):
    """Configuration for evaluations."""

    model_name: str = "openrouter:x-ai/grok-4.1-fast"
    api_key: str | None = None
    temperature: float = 0.7
    max_tokens: int | None = None
    timeout_seconds: int = 300
    logfire_enabled: bool = True
    use_llm_judge: bool = False
    max_duration_seconds: float = 300.0
    llm_judge_model: str | None = None

    def get_model_string(self) -> str:
        """Get the model string for pydantic-ai Agent.

        Returns:
            Model string (e.g., 'openrouter:x-ai/grok-beta').
        """
        return self.model_name

    def get_api_key(self) -> str:
        """Get the API key for OpenRouter.

        Returns:
            API key string.

        Raises:
            ValueError: If API key is not found.
        """
        api_key = self.api_key or os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENROUTER_API_KEY not found. Set it as environment variable "
                "or pass api_key to EvaluationConfig."
            )
        return api_key

    def setup_environment(self) -> None:
        """Set up environment variables for pydantic-ai to use OpenRouter."""
        import os
        os.environ["OPENROUTER_API_KEY"] = self.get_api_key()


# Global default configuration
default_config = EvaluationConfig()

