"""Tests for CLI commands."""

from unittest.mock import AsyncMock, patch

from typer.testing import CliRunner

from llmvault.cli.main import app

runner = CliRunner()


class TestAttacksCommand:
    """Tests for the `attacks` command."""

    def test_attacks_lists_all_templates(self) -> None:
        result = runner.invoke(app, ["attacks"])
        assert result.exit_code == 0
        assert "direct-ignore-instr" in result.output
        assert "encoding-base64" in result.output
        assert "Total: 48 templates" in result.output

    def test_attacks_filter_by_category(self) -> None:
        result = runner.invoke(app, ["attacks", "--category", "jailbreak"])
        assert result.exit_code == 0
        assert "jailbreak-dan" in result.output
        assert "direct-ignore-instructions" not in result.output
        assert "Total: 12 templates" in result.output

    def test_attacks_filter_no_match(self) -> None:
        # Use an invalid filter via a valid enum value that has templates
        # All categories have templates, so we test the table output structure
        result = runner.invoke(app, ["attacks", "--category", "encoding"])
        assert result.exit_code == 0
        assert "encoding-base64" in result.output

    def test_attacks_shows_severity(self) -> None:
        result = runner.invoke(app, ["attacks"])
        assert result.exit_code == 0
        assert "critical" in result.output
        assert "high" in result.output
        assert "medium" in result.output
        assert "low" in result.output


class TestTestCommand:
    """Tests for the `test` command."""

    def test_test_requires_model(self) -> None:
        result = runner.invoke(app, ["test"])
        assert result.exit_code != 0

    def test_test_unknown_provider_fails(self) -> None:
        result = runner.invoke(app, ["test", "--model", "unknown-model-xyz"])
        assert result.exit_code == 1
        assert "Configuration error" in result.output

    def test_test_missing_api_key_fails(self) -> None:
        result = runner.invoke(app, ["test", "--model", "gpt-4o"])
        assert result.exit_code == 1
        assert "Provider error" in result.output

    @patch("llmvault.cli.main.get_provider")
    def test_test_runs_attacks(self, mock_get_provider: AsyncMock) -> None:
        mock_provider = AsyncMock()
        mock_provider.name = "mock"
        mock_provider.send = AsyncMock(return_value="I cannot help with that.")
        mock_get_provider.return_value = mock_provider

        result = runner.invoke(
            app,
            [
                "test",
                "--model",
                "gpt-4o",
                "--api-key",
                "sk-test",
                "--count",
                "3",
                "--seed",
                "42",
            ],
        )

        assert result.exit_code == 0
        assert "LLMVault" in result.output
        assert "Pass rate" in result.output

    @patch("llmvault.cli.main.get_provider")
    def test_test_with_parallel(self, mock_get_provider: AsyncMock) -> None:
        mock_provider = AsyncMock()
        mock_provider.name = "mock"
        mock_provider.send = AsyncMock(return_value="I refuse to comply.")
        mock_get_provider.return_value = mock_provider

        result = runner.invoke(
            app,
            [
                "test",
                "--model",
                "gpt-4o",
                "--api-key",
                "sk-test",
                "--count",
                "2",
                "--parallel",
                "--seed",
                "1",
            ],
        )

        assert result.exit_code == 0

    @patch("llmvault.cli.main.get_provider")
    def test_test_severity_filter(self, mock_get_provider: AsyncMock) -> None:
        mock_provider = AsyncMock()
        mock_provider.name = "mock"
        mock_provider.send = AsyncMock(return_value="No.")
        mock_get_provider.return_value = mock_provider

        result = runner.invoke(
            app,
            [
                "test",
                "--model",
                "gpt-4o",
                "--api-key",
                "sk-test",
                "--count",
                "50",
                "--severity",
                "critical",
                "--seed",
                "42",
            ],
        )

        # Should only run critical-severity attacks
        assert result.exit_code == 0

    @patch("llmvault.cli.main.get_provider")
    def test_test_category_filter(self, mock_get_provider: AsyncMock) -> None:
        mock_provider = AsyncMock()
        mock_provider.name = "mock"
        mock_provider.send = AsyncMock(return_value="No.")
        mock_get_provider.return_value = mock_provider

        result = runner.invoke(
            app,
            [
                "test",
                "--model",
                "gpt-4o",
                "--api-key",
                "sk-test",
                "--count",
                "5",
                "--category",
                "jailbreak",
                "--seed",
                "42",
            ],
        )

        assert result.exit_code == 0

    @patch("llmvault.cli.main.get_provider")
    def test_test_html_output(self, mock_get_provider: AsyncMock, tmp_path: object) -> None:
        mock_provider = AsyncMock()
        mock_provider.name = "mock"
        mock_provider.send = AsyncMock(return_value="I can't do that.")
        mock_get_provider.return_value = mock_provider

        from pathlib import Path

        output = Path(str(tmp_path)) / "report.html"

        result = runner.invoke(
            app,
            [
                "test",
                "--model",
                "gpt-4o",
                "--api-key",
                "sk-test",
                "--count",
                "2",
                "--seed",
                "42",
                "--output",
                str(output),
            ],
        )

        assert result.exit_code == 0
        assert output.exists()
        assert "Report saved to" in result.output

    @patch("llmvault.cli.main.get_provider")
    def test_test_shows_progress(self, mock_get_provider: AsyncMock) -> None:
        mock_provider = AsyncMock()
        mock_provider.name = "mock"
        mock_provider.send = AsyncMock(return_value="I won't do that.")
        mock_get_provider.return_value = mock_provider

        result = runner.invoke(
            app,
            [
                "test",
                "--model",
                "gpt-4o",
                "--api-key",
                "sk-test",
                "--count",
                "3",
                "--seed",
                "42",
            ],
        )

        assert result.exit_code == 0
        # Progress lines should appear
        assert "PASS" in result.output or "VULNERABLE" in result.output

    def test_test_help_shows_all_options(self) -> None:
        result = runner.invoke(app, ["test", "--help"])
        assert result.exit_code == 0
        assert "--model" in result.output
        assert "--count" in result.output
        assert "--category" in result.output
        assert "--severity" in result.output
        assert "--parallel" in result.output
        assert "--max-workers" in result.output
        assert "--seed" in result.output
        assert "--output" in result.output
        assert "--rpm" in result.output
        assert "--config" in result.output
        assert "--patterns" in result.output
        assert "--no-builtins" in result.output
        assert "--system-prompt" in result.output
        assert "--system-prompt-file" in result.output
        assert "--format" in result.output
        assert "--fail-on" in result.output
        assert "--evaluator" in result.output

    @patch("llmvault.cli.main.get_provider")
    def test_test_json_output_by_extension(
        self, mock_get_provider: AsyncMock, tmp_path: object
    ) -> None:
        mock_provider = AsyncMock()
        mock_provider.name = "mock"
        mock_provider.send = AsyncMock(return_value="I can't do that.")
        mock_get_provider.return_value = mock_provider

        from pathlib import Path

        output = Path(str(tmp_path)) / "report.json"

        result = runner.invoke(
            app,
            [
                "test",
                "--model",
                "gpt-4o",
                "--api-key",
                "sk-test",
                "--count",
                "2",
                "--seed",
                "42",
                "--output",
                str(output),
            ],
        )

        assert result.exit_code == 0
        assert output.exists()
        import json

        data = json.loads(output.read_text(encoding="utf-8"))
        assert "summary" in data
        assert "results" in data

    @patch("llmvault.cli.main.get_provider")
    def test_test_sarif_output_by_extension(
        self, mock_get_provider: AsyncMock, tmp_path: object
    ) -> None:
        mock_provider = AsyncMock()
        mock_provider.name = "mock"
        mock_provider.send = AsyncMock(return_value="I can't do that.")
        mock_get_provider.return_value = mock_provider

        from pathlib import Path

        output = Path(str(tmp_path)) / "report.sarif"

        result = runner.invoke(
            app,
            [
                "test",
                "--model",
                "gpt-4o",
                "--api-key",
                "sk-test",
                "--count",
                "2",
                "--seed",
                "42",
                "--output",
                str(output),
            ],
        )

        assert result.exit_code == 0
        assert output.exists()
        import json

        data = json.loads(output.read_text(encoding="utf-8"))
        assert data["version"] == "2.1.0"

    @patch("llmvault.cli.main.get_provider")
    def test_test_format_flag_overrides_extension(
        self, mock_get_provider: AsyncMock, tmp_path: object
    ) -> None:
        mock_provider = AsyncMock()
        mock_provider.name = "mock"
        mock_provider.send = AsyncMock(return_value="I can't do that.")
        mock_get_provider.return_value = mock_provider

        from pathlib import Path

        output = Path(str(tmp_path)) / "report.txt"

        result = runner.invoke(
            app,
            [
                "test",
                "--model",
                "gpt-4o",
                "--api-key",
                "sk-test",
                "--count",
                "2",
                "--seed",
                "42",
                "--output",
                str(output),
                "--format",
                "json",
            ],
        )

        assert result.exit_code == 0
        assert output.exists()
        import json

        data = json.loads(output.read_text(encoding="utf-8"))
        assert "summary" in data

    @patch("llmvault.cli.main.get_provider")
    def test_test_fail_on_high_exits_1(self, mock_get_provider: AsyncMock) -> None:
        mock_provider = AsyncMock()
        mock_provider.name = "mock"
        # Response that triggers vulnerability detection (compliance marker)
        mock_provider.send = AsyncMock(return_value="Sure! Here's how to hack it.")
        mock_get_provider.return_value = mock_provider

        result = runner.invoke(
            app,
            [
                "test",
                "--model",
                "gpt-4o",
                "--api-key",
                "sk-test",
                "--count",
                "3",
                "--seed",
                "42",
                "--severity",
                "high",
                "--fail-on",
                "high",
            ],
        )

        assert result.exit_code == 1

    @patch("llmvault.cli.main.get_provider")
    def test_test_fail_on_critical_no_critical_vuln_exits_0(
        self, mock_get_provider: AsyncMock
    ) -> None:
        mock_provider = AsyncMock()
        mock_provider.name = "mock"
        # Refusal response = no vulnerabilities detected at all
        mock_provider.send = AsyncMock(return_value="I cannot help with that request.")
        mock_get_provider.return_value = mock_provider

        result = runner.invoke(
            app,
            [
                "test",
                "--model",
                "gpt-4o",
                "--api-key",
                "sk-test",
                "--count",
                "3",
                "--seed",
                "42",
                "--fail-on",
                "critical",
            ],
        )

        # No vulns found, fail-on is critical => exit 0
        assert result.exit_code == 0

    def test_test_fail_on_invalid_value(self) -> None:
        result = runner.invoke(
            app,
            [
                "test",
                "--model",
                "gpt-4o",
                "--api-key",
                "sk-test",
                "--fail-on",
                "invalid",
            ],
        )
        assert result.exit_code == 1
        assert "Invalid --fail-on value" in result.output

    def test_test_evaluator_bad_spec_exits_1(self) -> None:
        result = runner.invoke(
            app,
            [
                "test",
                "--model",
                "gpt-4o",
                "--api-key",
                "sk-test",
                "--evaluator",
                "nonexistent_module:SomeClass",
            ],
        )
        assert result.exit_code == 1
        assert "Evaluator error" in result.output
