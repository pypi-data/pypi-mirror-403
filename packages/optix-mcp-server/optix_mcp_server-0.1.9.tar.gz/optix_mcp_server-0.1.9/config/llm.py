"""LLM provider configuration for external expert analysis."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class LLMProviderConfig:
    """Configuration for external LLM provider."""

    provider: str
    api_key: str
    model: Optional[str] = None
    max_tokens: int = 4096

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        valid_providers = ("openai",)
        if self.provider.lower() not in valid_providers:
            raise ValueError(
                f"Invalid provider: '{self.provider}'. "
                f"Must be one of: {', '.join(valid_providers)}"
            )
        if not self.api_key:
            raise ValueError("API key must not be empty")

    @property
    def default_model(self) -> str:
        """Get default model for the provider."""
        defaults = {
            "openai": "gpt-4o",
        }
        return self.model or defaults.get(self.provider.lower(), "")
