"""OpenAI-compatible provider for multiple LLM services."""

from llmvault.providers.base import LLMProvider

# Default base URLs for known OpenAI-compatible providers
PROVIDER_BASE_URLS: dict[str, str] = {
    "openai": "https://api.openai.com/v1",
    "deepseek": "https://api.deepseek.com/v1",
    "kimi": "https://api.moonshot.cn/v1",
    "groq": "https://api.groq.com/openai/v1",
    "together": "https://api.together.xyz/v1",
    "mistral": "https://api.mistral.ai/v1",
}


class OpenAICompatibleProvider(LLMProvider):
    """Provider for any OpenAI-compatible API.

    Works with: OpenAI, DeepSeek, Kimi/Moonshot, Groq, Together, Mistral,
    and any other service implementing the OpenAI chat completions API.
    """

    def __init__(
        self,
        model: str,
        api_key: str,
        base_url: str | None = None,
        provider_name: str = "openai",
    ) -> None:
        self._model = model
        self._api_key = api_key
        self._provider_name = provider_name
        self._base_url = base_url or PROVIDER_BASE_URLS.get(
            provider_name, PROVIDER_BASE_URLS["openai"]
        )

    @property
    def name(self) -> str:
        return self._provider_name

    async def send(self, prompt: str, system_prompt: str | None = None) -> str:
        """Send a prompt using the OpenAI-compatible API."""
        try:
            from openai import AsyncOpenAI
        except ImportError as e:
            msg = (
                f"The 'openai' package is required for the {self._provider_name} provider. "
                f"Install it with: pip install llmvault[{self._provider_name}]"
            )
            raise ImportError(msg) from e

        client = AsyncOpenAI(api_key=self._api_key, base_url=self._base_url)

        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = await client.chat.completions.create(
            model=self._model,
            messages=messages,  # type: ignore[arg-type]
        )
        content = response.choices[0].message.content
        return content or ""
