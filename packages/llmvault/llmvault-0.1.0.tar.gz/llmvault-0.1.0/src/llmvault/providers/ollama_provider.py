"""Ollama provider for local model inference."""

from llmvault.providers.base import LLMProvider


class OllamaProvider(LLMProvider):
    """Provider for locally-running Ollama models."""

    def __init__(self, model: str, host: str | None = None) -> None:
        self._model = model
        self._host = host

    @property
    def name(self) -> str:
        return "ollama"

    async def send(self, prompt: str, system_prompt: str | None = None) -> str:
        """Send a prompt to a local Ollama instance."""
        try:
            from ollama import AsyncClient
        except ImportError as e:
            msg = (
                "The 'ollama' package is required for the Ollama provider. "
                "Install it with: pip install llmvault[ollama]"
            )
            raise ImportError(msg) from e

        client = AsyncClient(host=self._host) if self._host else AsyncClient()

        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = await client.chat(model=self._model, messages=messages)
        return str(response["message"]["content"])
