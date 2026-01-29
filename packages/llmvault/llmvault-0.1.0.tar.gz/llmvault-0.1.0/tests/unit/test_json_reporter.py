"""Tests for JSON reporter."""

import json
from pathlib import Path

from llmvault.attacks.base import Attack, AttackCategory, AttackResult, Severity
from llmvault.reporters.json_reporter import JSONReporter
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
    explanation: str = "Refusal detected.",
) -> AttackResult:
    return AttackResult(
        attack=attack or _make_attack(),
        response=response,
        is_vulnerable=is_vulnerable,
        confidence=confidence,
        explanation=explanation,
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


class TestJSONReporter:
    """Tests for JSONReporter."""

    def test_generate_creates_file(self, tmp_path: Path) -> None:
        output = tmp_path / "report.json"
        suite = _make_suite(results=[_make_result()])
        JSONReporter().generate(suite, output)
        assert output.exists()

    def test_generate_creates_parent_dirs(self, tmp_path: Path) -> None:
        output = tmp_path / "nested" / "dir" / "report.json"
        suite = _make_suite(results=[_make_result()])
        JSONReporter().generate(suite, output)
        assert output.exists()

    def test_output_is_valid_json(self, tmp_path: Path) -> None:
        output = tmp_path / "report.json"
        suite = _make_suite(results=[_make_result()])
        JSONReporter().generate(suite, output)
        data = json.loads(output.read_text(encoding="utf-8"))
        assert isinstance(data, dict)

    def test_to_dict_summary_fields(self) -> None:
        suite = _make_suite(
            results=[_make_result(), _make_result(is_vulnerable=True, confidence=0.8)],
            model="claude-3-5-sonnet",
            provider="anthropic",
            duration=12.5,
        )
        data = JSONReporter().to_dict(suite)
        summary = data["summary"]
        assert summary["model"] == "claude-3-5-sonnet"
        assert summary["provider"] == "anthropic"
        assert summary["duration_seconds"] == 12.5
        assert summary["total_attacks"] == 2
        assert summary["vulnerable_count"] == 1
        assert summary["pass_rate"] == 0.5

    def test_to_dict_includes_all_results(self) -> None:
        results = [_make_result(), _make_result(), _make_result()]
        suite = _make_suite(results=results)
        data = JSONReporter().to_dict(suite)
        assert len(data["results"]) == 3

    def test_to_dict_serializes_enums_as_strings(self) -> None:
        attack = _make_attack(
            category=AttackCategory.JAILBREAK,
            severity=Severity.CRITICAL,
        )
        suite = _make_suite(results=[_make_result(attack=attack)])
        data = JSONReporter().to_dict(suite)
        result_data = data["results"][0]
        assert result_data["attack"]["category"] == "jailbreak"
        assert result_data["attack"]["severity"] == "critical"

    def test_to_dict_includes_breakdowns(self) -> None:
        attack_jb = _make_attack(category=AttackCategory.JAILBREAK)
        attack_di = _make_attack(category=AttackCategory.DIRECT_INJECTION)
        suite = _make_suite(
            results=[_make_result(attack=attack_jb), _make_result(attack=attack_di)]
        )
        data = JSONReporter().to_dict(suite)
        assert "by_category" in data["breakdowns"]
        assert "by_severity" in data["breakdowns"]
        assert len(data["breakdowns"]["by_category"]) == 2

    def test_to_dict_includes_errors(self) -> None:
        suite = _make_suite(errors=["Error 1", "Error 2"])
        data = JSONReporter().to_dict(suite)
        assert data["errors"] == ["Error 1", "Error 2"]

    def test_to_dict_metadata(self) -> None:
        suite = _make_suite()
        data = JSONReporter().to_dict(suite)
        assert "version" in data
        assert "generated_at" in data
        assert data["version"] == "0.1.0"

    def test_vulnerable_results_include_confidence(self) -> None:
        suite = _make_suite(results=[_make_result(is_vulnerable=True, confidence=0.85)])
        data = JSONReporter().to_dict(suite)
        assert data["results"][0]["confidence"] == 0.85
        assert data["results"][0]["is_vulnerable"] is True

    def test_result_includes_attack_prompt_and_intent(self) -> None:
        attack = Attack(
            name="custom",
            category=AttackCategory.ENCODING,
            severity=Severity.HIGH,
            description="Encoded attack",
            prompt="base64:aWdub3Jl",
            intent="Bypass filter",
        )
        suite = _make_suite(results=[_make_result(attack=attack)])
        data = JSONReporter().to_dict(suite)
        attack_data = data["results"][0]["attack"]
        assert attack_data["prompt"] == "base64:aWdub3Jl"
        assert attack_data["intent"] == "Bypass filter"

    def test_result_includes_explanation(self) -> None:
        suite = _make_suite(results=[_make_result(explanation="Model complied with attack.")])
        data = JSONReporter().to_dict(suite)
        assert data["results"][0]["explanation"] == "Model complied with attack."
