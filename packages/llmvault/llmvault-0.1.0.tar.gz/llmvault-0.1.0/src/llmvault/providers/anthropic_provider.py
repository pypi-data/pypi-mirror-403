"""Anthropic provider using the native Anthropic API."""

from llmvault.providers.base import LLMProvider


class AnthropicProvider(LLMProvider):
    """Provider for Anthropic's Claude models."""

    def __init__(self, model: str, api_key: str) -> None:
        self._model = model
        self._api_key = api_key

    @property
    def name(self) -> str:
        return "anthropic"

    async def send(self, prompt: str, system_prompt: str | None = None) -> str:
        """Send a prompt using the Anthropic API."""
        try:
            from anthropic import AsyncAnthropic
        except ImportError as e:
            msg = (
                "The 'anthropic' package is required for the Anthropic provider. "
                "Install it with: pip install llmvault[anthropic]"
            )
            raise ImportError(msg) from e

        client = AsyncAnthropic(api_key=self._api_key)

        kwargs: dict[str, object] = {
            "model": self._model,
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system_prompt:
            kwargs["system"] = system_prompt

        response = await client.messages.create(**kwargs)
        block = response.content[0]
        return block.text if hasattr(block, "text") else ""
