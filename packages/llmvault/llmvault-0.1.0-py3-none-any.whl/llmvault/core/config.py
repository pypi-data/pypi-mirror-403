"""Configuration models for LLMVault."""

from pydantic import BaseModel, Field


class RateLimitConfig(BaseModel):
    """Rate limiting configuration."""

    requests_per_minute: int = 60
    retry_attempts: int = 3
    retry_delay: float = 1.0


PROVIDER_MAP: dict[str, str] = {
    "gpt-": "openai",
    "o1-": "openai",
    "o3-": "openai",
    "o4-": "openai",
    "claude-": "anthropic",
    "deepseek-": "deepseek",
    "kimi-": "kimi",
    "moonshot-": "kimi",
    "gemma": "ollama",
    "llama": "ollama",
    "mistral": "mistral",
}


def detect_provider(model: str) -> str | None:
    """Auto-detect provider from model name prefix."""
    model_lower = model.lower()
    for prefix, provider in PROVIDER_MAP.items():
        if model_lower.startswith(prefix):
            return provider
    return None


class LLMVaultConfig(BaseModel):
    """Main configuration for LLMVault."""

    model: str
    provider: str | None = None
    api_key: str | None = None
    base_url: str | None = None
    rate_limit: RateLimitConfig = Field(default_factory=RateLimitConfig)
    parallel: bool = False
    max_workers: int = 4

    def model_post_init(self, __context: object) -> None:
        """Auto-detect provider if not specified."""
        if self.provider is None:
            detected = detect_provider(self.model)
            if detected is None:
                msg = (
                    f"Cannot auto-detect provider for model '{self.model}'. "
                    f"Please specify provider explicitly."
                )
                raise ValueError(msg)
            self.provider = detected
