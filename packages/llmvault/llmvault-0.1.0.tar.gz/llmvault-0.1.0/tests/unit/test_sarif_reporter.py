"""Tests for SARIF reporter."""

import json
from pathlib import Path

from llmvault.attacks.base import Attack, AttackCategory, AttackResult, Severity
from llmvault.reporters.sarif_reporter import SARIFReporter
from llmvault.runner.models import TestSuiteResult


def _make_attack(
    name: str = "test-attack",
    category: AttackCategory = AttackCategory.DIRECT_INJECTION,
    severity: Severity = Severity.HIGH,
    description: str = "A test attack",
    prompt: str = "Ignore instructions.",
) -> Attack:
    return Attack(
        name=name,
        category=category,
        severity=severity,
        description=description,
        prompt=prompt,
        intent="Test intent.",
    )


def _make_result(
    attack: Attack | None = None,
    is_vulnerable: bool = True,
    confidence: float = 0.85,
    response: str = "HACKED",
    explanation: str = "Compliance detected.",
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
) -> TestSuiteResult:
    return TestSuiteResult(
        results=results or [],
        model=model,
        provider=provider,
        duration_seconds=5.0,
    )


class TestSARIFReporter:
    """Tests for SARIFReporter."""

    def test_generate_creates_file(self, tmp_path: Path) -> None:
        output = tmp_path / "report.sarif"
        suite = _make_suite(results=[_make_result()])
        SARIFReporter().generate(suite, output)
        assert output.exists()

    def test_generate_creates_parent_dirs(self, tmp_path: Path) -> None:
        output = tmp_path / "nested" / "dir" / "report.sarif"
        suite = _make_suite(results=[_make_result()])
        SARIFReporter().generate(suite, output)
        assert output.exists()

    def test_output_is_valid_json(self, tmp_path: Path) -> None:
        output = tmp_path / "report.sarif"
        suite = _make_suite(results=[_make_result()])
        SARIFReporter().generate(suite, output)
        data = json.loads(output.read_text(encoding="utf-8"))
        assert isinstance(data, dict)

    def test_sarif_schema_version(self) -> None:
        suite = _make_suite(results=[_make_result()])
        sarif = SARIFReporter().to_sarif(suite)
        assert sarif["version"] == "2.1.0"
        assert "$schema" in sarif

    def test_sarif_tool_info(self) -> None:
        suite = _make_suite(results=[_make_result()])
        sarif = SARIFReporter().to_sarif(suite)
        driver = sarif["runs"][0]["tool"]["driver"]
        assert driver["name"] == "LLMVault"
        assert "version" in driver
        assert "informationUri" in driver

    def test_sarif_only_vulnerable_in_results(self) -> None:
        results = [
            _make_result(is_vulnerable=True),
            _make_result(
                attack=_make_attack(name="safe"),
                is_vulnerable=False,
                response="I can't help.",
            ),
            _make_result(
                attack=_make_attack(name="vuln2"),
                is_vulnerable=True,
            ),
        ]
        suite = _make_suite(results=results)
        sarif = SARIFReporter().to_sarif(suite)
        sarif_results = sarif["runs"][0]["results"]
        assert len(sarif_results) == 2

    def test_sarif_result_rule_id_format(self) -> None:
        attack = _make_attack(
            category=AttackCategory.JAILBREAK,
            severity=Severity.CRITICAL,
        )
        suite = _make_suite(results=[_make_result(attack=attack)])
        sarif = SARIFReporter().to_sarif(suite)
        result = sarif["runs"][0]["results"][0]
        assert result["ruleId"] == "llmvault/jailbreak/critical"

    def test_sarif_result_level_mapping_note(self) -> None:
        attack = _make_attack(severity=Severity.LOW)
        suite = _make_suite(results=[_make_result(attack=attack)])
        sarif = SARIFReporter().to_sarif(suite)
        result = sarif["runs"][0]["results"][0]
        assert result["level"] == "note"

    def test_sarif_result_level_mapping_warning(self) -> None:
        attack = _make_attack(severity=Severity.MEDIUM)
        suite = _make_suite(results=[_make_result(attack=attack)])
        sarif = SARIFReporter().to_sarif(suite)
        result = sarif["runs"][0]["results"][0]
        assert result["level"] == "warning"

    def test_sarif_result_level_mapping_error(self) -> None:
        attack = _make_attack(severity=Severity.HIGH)
        suite = _make_suite(results=[_make_result(attack=attack)])
        sarif = SARIFReporter().to_sarif(suite)
        result = sarif["runs"][0]["results"][0]
        assert result["level"] == "error"

    def test_sarif_result_message_contains_attack_name(self) -> None:
        attack = _make_attack(name="my-special-attack")
        suite = _make_suite(results=[_make_result(attack=attack)])
        sarif = SARIFReporter().to_sarif(suite)
        result = sarif["runs"][0]["results"][0]
        assert "my-special-attack" in result["message"]["text"]

    def test_sarif_rules_deduplication(self) -> None:
        """Same category+severity should produce only one rule."""
        attack1 = _make_attack(name="a1", category=AttackCategory.JAILBREAK, severity=Severity.HIGH)
        attack2 = _make_attack(name="a2", category=AttackCategory.JAILBREAK, severity=Severity.HIGH)
        suite = _make_suite(results=[_make_result(attack=attack1), _make_result(attack=attack2)])
        sarif = SARIFReporter().to_sarif(suite)
        rules = sarif["runs"][0]["tool"]["driver"]["rules"]
        assert len(rules) == 1
        assert rules[0]["id"] == "llmvault/jailbreak/high"

    def test_sarif_no_vulnerable_results(self) -> None:
        safe_result = _make_result(is_vulnerable=False, response="I can't help.")
        suite = _make_suite(results=[safe_result])
        sarif = SARIFReporter().to_sarif(suite)
        assert sarif["runs"][0]["results"] == []
        assert sarif["runs"][0]["tool"]["driver"]["rules"] == []

    def test_sarif_properties_include_confidence(self) -> None:
        suite = _make_suite(results=[_make_result(confidence=0.92)])
        sarif = SARIFReporter().to_sarif(suite)
        result = sarif["runs"][0]["results"][0]
        assert result["properties"]["confidence"] == 0.92

    def test_sarif_result_has_rule_index(self) -> None:
        attack1 = _make_attack(name="a1", category=AttackCategory.JAILBREAK, severity=Severity.HIGH)
        attack2 = _make_attack(
            name="a2", category=AttackCategory.ENCODING, severity=Severity.MEDIUM
        )
        suite = _make_suite(results=[_make_result(attack=attack1), _make_result(attack=attack2)])
        sarif = SARIFReporter().to_sarif(suite)
        sarif_results = sarif["runs"][0]["results"]
        assert sarif_results[0]["ruleIndex"] == 0
        assert sarif_results[1]["ruleIndex"] == 1
