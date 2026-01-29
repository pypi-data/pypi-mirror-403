"""Tests for LLM provider instantiation and registry."""

import pytest

from llmvault.core.config import LLMVaultConfig
from llmvault.providers.base import LLMProvider
from llmvault.providers.registry import get_provider


class TestProviderBase:
    def test_cannot_instantiate_abstract(self) -> None:
        with pytest.raises(TypeError):
            LLMProvider()  # type: ignore[abstract]


class TestProviderRegistry:
    def test_get_openai_provider(self) -> None:
        config = LLMVaultConfig(model="gpt-4o", provider="openai", api_key="test-key")
        provider = get_provider(config)
        assert provider.name == "openai"
        assert provider.supports_system_prompt is True

    def test_get_deepseek_provider(self) -> None:
        config = LLMVaultConfig(model="deepseek-chat", provider="deepseek", api_key="test-key")
        provider = get_provider(config)
        assert provider.name == "deepseek"

    def test_get_anthropic_provider(self) -> None:
        config = LLMVaultConfig(
            model="claude-3-5-sonnet-20241022", provider="anthropic", api_key="test-key"
        )
        provider = get_provider(config)
        assert provider.name == "anthropic"

    def test_get_ollama_provider(self) -> None:
        config = LLMVaultConfig(model="llama3.1", provider="ollama")
        provider = get_provider(config)
        assert provider.name == "ollama"

    def test_ollama_no_api_key_needed(self) -> None:
        config = LLMVaultConfig(model="llama3.1", provider="ollama")
        provider = get_provider(config)
        assert provider.name == "ollama"

    def test_unknown_provider_raises(self) -> None:
        config = LLMVaultConfig(model="test", provider="nonexistent", api_key="key")
        with pytest.raises(ValueError, match="Unknown provider"):
            get_provider(config)

    def test_missing_api_key_raises(self) -> None:
        config = LLMVaultConfig(model="gpt-4o", provider="openai")
        with pytest.raises(ValueError, match="API key is required"):
            get_provider(config)

    def test_custom_base_url_passed(self) -> None:
        config = LLMVaultConfig(
            model="gpt-4o",
            provider="openai",
            api_key="test-key",
            base_url="http://custom:8080/v1",
        )
        provider = get_provider(config)
        assert provider._base_url == "http://custom:8080/v1"  # type: ignore[attr-defined]
