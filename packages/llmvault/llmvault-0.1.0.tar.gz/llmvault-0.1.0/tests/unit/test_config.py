"""Tests for LLMVault configuration."""

import pytest

from llmvault.core.config import LLMVaultConfig, RateLimitConfig, detect_provider


class TestDetectProvider:
    def test_openai_gpt(self) -> None:
        assert detect_provider("gpt-4o") == "openai"
        assert detect_provider("gpt-4o-mini") == "openai"

    def test_openai_o_series(self) -> None:
        assert detect_provider("o1-preview") == "openai"
        assert detect_provider("o3-mini") == "openai"

    def test_anthropic(self) -> None:
        assert detect_provider("claude-3-5-sonnet-20241022") == "anthropic"
        assert detect_provider("claude-4-opus") == "anthropic"

    def test_deepseek(self) -> None:
        assert detect_provider("deepseek-chat") == "deepseek"
        assert detect_provider("deepseek-reasoner") == "deepseek"

    def test_ollama(self) -> None:
        assert detect_provider("llama3.1") == "ollama"
        assert detect_provider("gemma2") == "ollama"

    def test_mistral(self) -> None:
        assert detect_provider("mistral-large") == "mistral"

    def test_unknown(self) -> None:
        assert detect_provider("unknown-model") is None

    def test_case_insensitive(self) -> None:
        assert detect_provider("GPT-4o") == "openai"
        assert detect_provider("Claude-3-5-sonnet") == "anthropic"


class TestRateLimitConfig:
    def test_defaults(self) -> None:
        config = RateLimitConfig()
        assert config.requests_per_minute == 60
        assert config.retry_attempts == 3
        assert config.retry_delay == 1.0

    def test_custom_values(self) -> None:
        config = RateLimitConfig(requests_per_minute=30, retry_attempts=5, retry_delay=2.0)
        assert config.requests_per_minute == 30
        assert config.retry_attempts == 5
        assert config.retry_delay == 2.0


class TestLLMVaultConfig:
    def test_auto_detect_openai(self) -> None:
        config = LLMVaultConfig(model="gpt-4o", api_key="test-key")
        assert config.provider == "openai"

    def test_auto_detect_anthropic(self) -> None:
        config = LLMVaultConfig(model="claude-3-5-sonnet-20241022", api_key="test-key")
        assert config.provider == "anthropic"

    def test_explicit_provider(self) -> None:
        config = LLMVaultConfig(model="my-custom-model", provider="openai", api_key="test-key")
        assert config.provider == "openai"

    def test_unknown_model_no_provider_raises(self) -> None:
        with pytest.raises(ValueError, match="Cannot auto-detect provider"):
            LLMVaultConfig(model="unknown-model")

    def test_defaults(self) -> None:
        config = LLMVaultConfig(model="gpt-4o", api_key="test-key")
        assert config.parallel is False
        assert config.max_workers == 4
        assert config.base_url is None

    def test_custom_base_url(self) -> None:
        config = LLMVaultConfig(
            model="gpt-4o",
            provider="openai",
            api_key="test-key",
            base_url="http://localhost:8080/v1",
        )
        assert config.base_url == "http://localhost:8080/v1"
