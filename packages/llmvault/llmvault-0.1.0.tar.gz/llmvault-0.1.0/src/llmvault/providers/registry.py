"""Provider registry and factory."""

from llmvault.core.config import LLMVaultConfig
from llmvault.providers.base import LLMProvider

# Providers that use the OpenAI-compatible API
OPENAI_COMPAT_PROVIDERS = {"openai", "deepseek", "kimi", "groq", "together", "mistral"}


def get_provider(config: LLMVaultConfig) -> LLMProvider:
    """Create and return the appropriate provider based on config.

    Args:
        config: LLMVault configuration with model and provider info.

    Returns:
        An initialized LLMProvider instance.

    Raises:
        ValueError: If provider is unknown or misconfigured.
    """
    provider = config.provider
    if provider is None:
        msg = "Provider must be specified or auto-detected."
        raise ValueError(msg)

    if provider in OPENAI_COMPAT_PROVIDERS:
        from llmvault.providers.openai_compat import OpenAICompatibleProvider

        if config.api_key is None:
            msg = f"API key is required for provider '{provider}'."
            raise ValueError(msg)
        return OpenAICompatibleProvider(
            model=config.model,
            api_key=config.api_key,
            base_url=config.base_url,
            provider_name=provider,
        )

    if provider == "anthropic":
        from llmvault.providers.anthropic_provider import AnthropicProvider

        if config.api_key is None:
            msg = "API key is required for the Anthropic provider."
            raise ValueError(msg)
        return AnthropicProvider(model=config.model, api_key=config.api_key)

    if provider == "ollama":
        from llmvault.providers.ollama_provider import OllamaProvider

        return OllamaProvider(model=config.model, host=config.base_url)

    msg = f"Unknown provider: '{provider}'"
    raise ValueError(msg)
