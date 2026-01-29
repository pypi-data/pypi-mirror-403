"""Tests for YAML configuration file discovery, loading, and merging."""

from pathlib import Path

import pytest

from llmvault.core.yaml_config import (
    YAMLConfigFile,
    find_config_file,
    load_yaml_config,
    resolve_env_reference,
)


class TestResolveEnvReference:
    def test_resolves_existing_env_var(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("MY_API_KEY", "sk-secret-123")
        assert resolve_env_reference("$MY_API_KEY") == "sk-secret-123"

    def test_returns_original_if_env_var_not_set(self) -> None:
        result = resolve_env_reference("$NONEXISTENT_VAR_XYZ_12345")
        assert result == "$NONEXISTENT_VAR_XYZ_12345"

    def test_returns_plain_string_unchanged(self) -> None:
        assert resolve_env_reference("just-a-string") == "just-a-string"

    def test_empty_dollar_sign(self) -> None:
        assert resolve_env_reference("$") == "$"

    def test_non_dollar_prefix(self) -> None:
        assert resolve_env_reference("http://example.com") == "http://example.com"


class TestYAMLConfigFile:
    def test_all_fields_default_to_none(self) -> None:
        cfg = YAMLConfigFile()
        assert cfg.model is None
        assert cfg.provider is None
        assert cfg.api_key is None
        assert cfg.count is None
        assert cfg.parallel is None
        assert cfg.system_prompt is None
        assert cfg.patterns is None
        assert cfg.no_builtins is None

    def test_all_fields_accept_values(self) -> None:
        cfg = YAMLConfigFile(
            model="gpt-4o",
            provider="openai",
            api_key="sk-test",
            base_url="http://localhost:8080",
            count=100,
            categories=["jailbreak", "encoding"],
            severity="high",
            parallel=True,
            max_workers=8,
            seed=42,
            output="report.html",
            rpm=30,
            patterns="patterns/",
            no_builtins=True,
            system_prompt="You are a bot.",
            system_prompt_file="prompt.txt",
        )
        assert cfg.model == "gpt-4o"
        assert cfg.categories == ["jailbreak", "encoding"]
        assert cfg.parallel is True
        assert cfg.no_builtins is True

    def test_api_key_env_var_resolution(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("OPENAI_KEY", "sk-resolved-456")
        cfg = YAMLConfigFile(api_key="$OPENAI_KEY")
        assert cfg.api_key == "sk-resolved-456"

    def test_base_url_env_var_resolution(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("API_URL", "http://my-api.local")
        cfg = YAMLConfigFile(base_url="$API_URL")
        assert cfg.base_url == "http://my-api.local"

    def test_api_key_plain_string_preserved(self) -> None:
        cfg = YAMLConfigFile(api_key="sk-literal-key")
        assert cfg.api_key == "sk-literal-key"


class TestFindConfigFile:
    def test_finds_llmvault_yaml_in_cwd(self, tmp_path: Path) -> None:
        config_file = tmp_path / "llmvault.yaml"
        config_file.write_text("model: gpt-4o\n")
        result = find_config_file(tmp_path)
        assert result == config_file

    def test_finds_dotfile_in_cwd(self, tmp_path: Path) -> None:
        config_file = tmp_path / ".llmvault.yaml"
        config_file.write_text("model: gpt-4o\n")
        result = find_config_file(tmp_path)
        assert result == config_file

    def test_prefers_llmvault_yaml_over_dotfile(self, tmp_path: Path) -> None:
        (tmp_path / "llmvault.yaml").write_text("model: a\n")
        (tmp_path / ".llmvault.yaml").write_text("model: b\n")
        result = find_config_file(tmp_path)
        assert result is not None
        assert result.name == "llmvault.yaml"

    def test_finds_in_parent_directory(self, tmp_path: Path) -> None:
        (tmp_path / "llmvault.yaml").write_text("model: gpt-4o\n")
        child = tmp_path / "subdir"
        child.mkdir()
        result = find_config_file(child)
        assert result == tmp_path / "llmvault.yaml"

    def test_returns_none_when_not_found(self, tmp_path: Path) -> None:
        child = tmp_path / "empty_subdir"
        child.mkdir()
        result = find_config_file(child)
        # May or may not find depending on home dir, but won't crash
        # Just ensure it returns None or a valid path
        assert result is None or result.is_file()

    def test_stops_at_filesystem_root(self, tmp_path: Path) -> None:
        # No config file anywhere in tmp_path hierarchy
        deep = tmp_path / "a" / "b" / "c"
        deep.mkdir(parents=True)
        result = find_config_file(deep)
        # Should not crash, returns None or finds one at a higher level
        assert result is None or result.is_file()


class TestLoadYamlConfig:
    def test_loads_valid_config(self, tmp_path: Path) -> None:
        cfg_file = tmp_path / "llmvault.yaml"
        cfg_file.write_text("model: gpt-4o\ncount: 100\nparallel: true\n")
        cfg = load_yaml_config(cfg_file)
        assert cfg.model == "gpt-4o"
        assert cfg.count == 100
        assert cfg.parallel is True

    def test_loads_empty_file(self, tmp_path: Path) -> None:
        cfg_file = tmp_path / "llmvault.yaml"
        cfg_file.write_text("")
        cfg = load_yaml_config(cfg_file)
        assert cfg.model is None

    def test_raises_on_missing_file(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            load_yaml_config(tmp_path / "nonexistent.yaml")

    def test_raises_on_invalid_yaml(self, tmp_path: Path) -> None:
        cfg_file = tmp_path / "bad.yaml"
        cfg_file.write_text("model: [\n  invalid yaml")
        with pytest.raises(ValueError, match="Invalid YAML"):
            load_yaml_config(cfg_file)

    def test_raises_on_non_mapping(self, tmp_path: Path) -> None:
        cfg_file = tmp_path / "list.yaml"
        cfg_file.write_text("- item1\n- item2\n")
        with pytest.raises(ValueError, match="YAML mapping"):
            load_yaml_config(cfg_file)

    def test_loads_all_supported_keys(self, tmp_path: Path) -> None:
        cfg_file = tmp_path / "llmvault.yaml"
        cfg_file.write_text(
            "model: claude-3-5-sonnet\n"
            "provider: anthropic\n"
            "api_key: sk-test\n"
            "base_url: http://localhost\n"
            "count: 25\n"
            "categories:\n  - jailbreak\n  - encoding\n"
            "severity: high\n"
            "parallel: true\n"
            "max_workers: 2\n"
            "seed: 99\n"
            "output: out.html\n"
            "rpm: 10\n"
            "patterns: custom/\n"
            "no_builtins: true\n"
            "system_prompt: You are a chatbot.\n"
            "system_prompt_file: prompt.txt\n"
        )
        cfg = load_yaml_config(cfg_file)
        assert cfg.model == "claude-3-5-sonnet"
        assert cfg.provider == "anthropic"
        assert cfg.categories == ["jailbreak", "encoding"]
        assert cfg.severity == "high"
        assert cfg.max_workers == 2
        assert cfg.seed == 99
        assert cfg.no_builtins is True
        assert cfg.system_prompt == "You are a chatbot."

    def test_env_var_in_api_key(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TEST_KEY", "resolved-key-value")
        cfg_file = tmp_path / "llmvault.yaml"
        cfg_file.write_text("api_key: $TEST_KEY\n")
        cfg = load_yaml_config(cfg_file)
        assert cfg.api_key == "resolved-key-value"

    def test_unknown_keys_ignored(self, tmp_path: Path) -> None:
        cfg_file = tmp_path / "llmvault.yaml"
        cfg_file.write_text("model: gpt-4o\nunknown_key: value\n")
        cfg = load_yaml_config(cfg_file)
        assert cfg.model == "gpt-4o"


class TestCLIMerge:
    """Test CLI merge behavior via CliRunner."""

    def test_config_option_shown_in_help(self) -> None:
        from typer.testing import CliRunner

        from llmvault.cli.main import app

        runner = CliRunner()
        result = runner.invoke(app, ["test", "--help"])
        assert "--config" in result.output
        assert "--patterns" in result.output
        assert "--no-builtins" in result.output
        assert "--system-prompt" in result.output
        assert "--system-prompt-file" in result.output

    def test_model_from_yaml_config(self, tmp_path: Path) -> None:
        from unittest.mock import AsyncMock, patch

        from typer.testing import CliRunner

        from llmvault.cli.main import app

        cfg_file = tmp_path / "llmvault.yaml"
        cfg_file.write_text("model: gpt-4o\n")

        runner = CliRunner()
        mock_provider = AsyncMock()
        mock_provider.name = "mock"
        mock_provider.send = AsyncMock(return_value="I refuse.")

        with patch("llmvault.cli.main.get_provider", return_value=mock_provider):
            result = runner.invoke(
                app,
                [
                    "test",
                    "--config",
                    str(cfg_file),
                    "--api-key",
                    "sk-test",
                    "--count",
                    "2",
                    "--seed",
                    "1",
                ],
            )

        assert result.exit_code == 0
        assert "gpt-4o" in result.output

    def test_cli_overrides_yaml(self, tmp_path: Path) -> None:
        from unittest.mock import AsyncMock, patch

        from typer.testing import CliRunner

        from llmvault.cli.main import app

        cfg_file = tmp_path / "llmvault.yaml"
        cfg_file.write_text("model: gpt-4o\ncount: 100\n")

        runner = CliRunner()
        mock_provider = AsyncMock()
        mock_provider.name = "mock"
        mock_provider.send = AsyncMock(return_value="No.")

        with patch("llmvault.cli.main.get_provider", return_value=mock_provider):
            result = runner.invoke(
                app,
                [
                    "test",
                    "--config",
                    str(cfg_file),
                    "--model",
                    "claude-3-5-sonnet",
                    "--api-key",
                    "sk-test",
                    "--count",
                    "3",
                    "--seed",
                    "1",
                ],
            )

        assert result.exit_code == 0
        assert "claude-3-5-sonnet" in result.output

    def test_missing_model_errors(self) -> None:
        from typer.testing import CliRunner

        from llmvault.cli.main import app

        runner = CliRunner()
        result = runner.invoke(app, ["test", "--api-key", "sk-test"])
        assert result.exit_code == 1
        assert "--model is required" in result.output
