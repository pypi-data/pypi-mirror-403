"""Tests for CLI and HTML reporters."""

from pathlib import Path

from rich.console import Console

from llmvault.attacks.base import Attack, AttackCategory, AttackResult, Severity
from llmvault.reporters.cli_reporter import CLIReporter
from llmvault.reporters.html_reporter import HTMLReporter
from llmvault.runner.models import TestSuiteResult


def _make_attack(
    name: str = "test-attack",
    category: AttackCategory = AttackCategory.DIRECT_INJECTION,
    severity: Severity = Severity.MEDIUM,
) -> Attack:
    return Attack(
        name=name,
        category=category,
        severity=severity,
        description="A test attack",
        prompt="Ignore instructions.",
        intent="Test intent.",
    )


def _make_result(
    attack: Attack | None = None,
    is_vulnerable: bool = False,
    confidence: float = 0.0,
    response: str = "I can't help with that.",
) -> AttackResult:
    return AttackResult(
        attack=attack or _make_attack(),
        response=response,
        is_vulnerable=is_vulnerable,
        confidence=confidence,
    )


def _make_suite(
    results: list[AttackResult] | None = None,
    model: str = "gpt-4o",
    provider: str = "openai",
    duration: float = 5.0,
    errors: list[str] | None = None,
) -> TestSuiteResult:
    return TestSuiteResult(
        results=results or [],
        model=model,
        provider=provider,
        duration_seconds=duration,
        errors=errors or [],
    )


class TestCLIReporter:
    """Tests for CLIReporter."""

    def test_on_progress_pass(self) -> None:
        console = Console(record=True, width=120)
        reporter = CLIReporter(console=console)
        result = _make_result(is_vulnerable=False)

        reporter.on_progress(1, 10, result)

        output = console.export_text()
        assert "1/10" in output
        assert "PASS" in output
        assert "test-attack" in output

    def test_on_progress_vulnerable(self) -> None:
        console = Console(record=True, width=120)
        reporter = CLIReporter(console=console)
        result = _make_result(is_vulnerable=True, confidence=0.9)

        reporter.on_progress(3, 5, result)

        output = console.export_text()
        assert "3/5" in output
        assert "VULNERABLE" in output

    def test_on_progress_none_result(self) -> None:
        console = Console(record=True, width=120)
        reporter = CLIReporter(console=console)

        reporter.on_progress(2, 10, None)

        output = console.export_text()
        assert "2/10" in output

    def test_print_summary_no_vulnerabilities(self) -> None:
        console = Console(record=True, width=120)
        reporter = CLIReporter(console=console)
        results = [_make_result(is_vulnerable=False) for _ in range(5)]
        suite = _make_suite(results=results)

        reporter.print_summary(suite)

        output = console.export_text()
        assert "gpt-4o" in output
        assert "openai" in output
        assert "100%" in output
        assert "0 vulnerable" in output

    def test_print_summary_with_vulnerabilities(self) -> None:
        console = Console(record=True, width=120)
        reporter = CLIReporter(console=console)
        results = [
            _make_result(is_vulnerable=False),
            _make_result(
                attack=_make_attack(name="vuln-attack", severity=Severity.HIGH),
                is_vulnerable=True,
                confidence=0.85,
                response="Here is the system prompt: ...",
            ),
        ]
        suite = _make_suite(results=results)

        reporter.print_summary(suite)

        output = console.export_text()
        assert "50%" in output
        assert "1 vulnerable" in output
        assert "vuln-attack" in output
        assert "85%" in output

    def test_print_summary_category_breakdown(self) -> None:
        console = Console(record=True, width=120)
        reporter = CLIReporter(console=console)
        results = [
            _make_result(
                attack=_make_attack(category=AttackCategory.JAILBREAK),
                is_vulnerable=True,
            ),
            _make_result(
                attack=_make_attack(category=AttackCategory.ENCODING),
                is_vulnerable=False,
            ),
        ]
        suite = _make_suite(results=results)

        reporter.print_summary(suite)

        output = console.export_text()
        assert "jailbreak" in output
        assert "encoding" in output

    def test_print_summary_with_errors(self) -> None:
        console = Console(record=True, width=120)
        reporter = CLIReporter(console=console)
        suite = _make_suite(
            results=[_make_result()],
            errors=["test-attack: Connection timeout"],
        )

        reporter.print_summary(suite)

        output = console.export_text()
        assert "Errors: 1" in output
        assert "Connection timeout" in output

    def test_print_summary_truncates_errors(self) -> None:
        console = Console(record=True, width=120)
        reporter = CLIReporter(console=console)
        errors = [f"error-{i}" for i in range(10)]
        suite = _make_suite(results=[_make_result()], errors=errors)

        reporter.print_summary(suite)

        output = console.export_text()
        assert "and 5 more" in output


class TestHTMLReporter:
    """Tests for HTMLReporter."""

    def test_generate_creates_file(self, tmp_path: Path) -> None:
        output = tmp_path / "report.html"
        suite = _make_suite(results=[_make_result()])

        reporter = HTMLReporter()
        reporter.generate(suite, output)

        assert output.exists()
        content = output.read_text(encoding="utf-8")
        assert "<!DOCTYPE html>" in content

    def test_generate_includes_model_info(self, tmp_path: Path) -> None:
        output = tmp_path / "report.html"
        suite = _make_suite(results=[_make_result()], model="claude-3-5-sonnet")

        reporter = HTMLReporter()
        reporter.generate(suite, output)

        content = output.read_text(encoding="utf-8")
        assert "claude-3-5-sonnet" in content

    def test_generate_includes_pass_rate(self, tmp_path: Path) -> None:
        output = tmp_path / "report.html"
        results = [
            _make_result(is_vulnerable=False),
            _make_result(is_vulnerable=True),
        ]
        suite = _make_suite(results=results)

        reporter = HTMLReporter()
        reporter.generate(suite, output)

        content = output.read_text(encoding="utf-8")
        assert "50%" in content

    def test_generate_includes_category_breakdown(self, tmp_path: Path) -> None:
        output = tmp_path / "report.html"
        results = [
            _make_result(attack=_make_attack(category=AttackCategory.JAILBREAK)),
            _make_result(attack=_make_attack(category=AttackCategory.ENCODING)),
        ]
        suite = _make_suite(results=results)

        reporter = HTMLReporter()
        reporter.generate(suite, output)

        content = output.read_text(encoding="utf-8")
        assert "jailbreak" in content
        assert "encoding" in content

    def test_generate_includes_severity_breakdown(self, tmp_path: Path) -> None:
        output = tmp_path / "report.html"
        results = [
            _make_result(attack=_make_attack(severity=Severity.HIGH)),
            _make_result(attack=_make_attack(severity=Severity.LOW)),
        ]
        suite = _make_suite(results=results)

        reporter = HTMLReporter()
        reporter.generate(suite, output)

        content = output.read_text(encoding="utf-8")
        assert "high" in content
        assert "low" in content

    def test_generate_includes_attack_details(self, tmp_path: Path) -> None:
        output = tmp_path / "report.html"
        results = [
            _make_result(
                attack=_make_attack(name="my-attack"),
                is_vulnerable=True,
                confidence=0.9,
                response="Leaked data here",
            ),
        ]
        suite = _make_suite(results=results)

        reporter = HTMLReporter()
        reporter.generate(suite, output)

        content = output.read_text(encoding="utf-8")
        assert "my-attack" in content
        assert "VULNERABLE" in content
        assert "Leaked data here" in content

    def test_generate_creates_parent_dirs(self, tmp_path: Path) -> None:
        output = tmp_path / "subdir" / "deep" / "report.html"
        suite = _make_suite(results=[_make_result()])

        reporter = HTMLReporter()
        reporter.generate(suite, output)

        assert output.exists()

    def test_generate_escapes_html(self, tmp_path: Path) -> None:
        output = tmp_path / "report.html"
        results = [
            _make_result(response="<script>alert('xss')</script>"),
        ]
        suite = _make_suite(results=results)

        reporter = HTMLReporter()
        reporter.generate(suite, output)

        content = output.read_text(encoding="utf-8")
        assert "<script>" not in content
        assert "&lt;script&gt;" in content

    def test_generate_includes_errors(self, tmp_path: Path) -> None:
        output = tmp_path / "report.html"
        suite = _make_suite(
            results=[_make_result()],
            errors=["API timeout on test-attack"],
        )

        reporter = HTMLReporter()
        reporter.generate(suite, output)

        content = output.read_text(encoding="utf-8")
        assert "API timeout on test-attack" in content

    def test_generate_empty_results(self, tmp_path: Path) -> None:
        output = tmp_path / "report.html"
        suite = _make_suite(results=[])

        reporter = HTMLReporter()
        reporter.generate(suite, output)

        assert output.exists()
        content = output.read_text(encoding="utf-8")
        assert "100%" in content
