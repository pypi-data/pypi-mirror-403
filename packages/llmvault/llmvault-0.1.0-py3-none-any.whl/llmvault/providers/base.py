"""Base class for LLM providers."""

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name identifier."""
        ...

    @property
    def supports_system_prompt(self) -> bool:
        """Whether this provider supports system prompts."""
        return True

    @abstractmethod
    async def send(self, prompt: str, system_prompt: str | None = None) -> str:
        """Send a prompt to the LLM and return the response text.

        Args:
            prompt: The user prompt to send.
            system_prompt: Optional system prompt for context.

        Returns:
            The model's response text.
        """
        ...
