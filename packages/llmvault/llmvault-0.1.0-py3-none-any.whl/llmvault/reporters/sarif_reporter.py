"""SARIF v2.1.0 reporter for static analysis tool integration."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import llmvault
from llmvault.attacks.base import AttackResult, Severity
from llmvault.runner.models import TestSuiteResult

_SARIF_SCHEMA = (
    "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/"
    "main/sarif-2.1/schema/sarif-schema-2.1.0.json"
)

_SEVERITY_TO_SARIF_LEVEL: dict[Severity, str] = {
    Severity.LOW: "note",
    Severity.MEDIUM: "warning",
    Severity.HIGH: "error",
    Severity.CRITICAL: "error",
}


class SARIFReporter:
    """Generates SARIF v2.1.0 reports for CI/CD tool integration.

    Compatible with GitHub Code Scanning (upload-sarif action),
    VS Code SARIF Viewer, and Azure DevOps.
    """

    def generate(self, result: TestSuiteResult, output_path: Path) -> None:
        """Render SARIF report and write to output_path."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        sarif = self.to_sarif(result)
        output_path.write_text(
            json.dumps(sarif, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def to_sarif(self, result: TestSuiteResult) -> dict[str, Any]:
        """Convert TestSuiteResult to SARIF v2.1.0 structure."""
        vulnerable_results = [r for r in result.results if r.is_vulnerable]
        rules = self._make_rules(vulnerable_results)
        rule_id_to_index = {r["id"]: i for i, r in enumerate(rules)}

        sarif_results = []
        for ar in vulnerable_results:
            rule_id = self._rule_id(ar)
            sarif_results.append(self._make_result(ar, rule_id_to_index[rule_id]))

        return {
            "$schema": _SARIF_SCHEMA,
            "version": "2.1.0",
            "runs": [
                {
                    "tool": {
                        "driver": {
                            "name": "LLMVault",
                            "version": llmvault.__version__,
                            "informationUri": "https://github.com/sharkfabri/LLMVault",
                            "rules": rules,
                        }
                    },
                    "results": sarif_results,
                    "invocations": [
                        {
                            "executionSuccessful": True,
                            "startTimeUtc": datetime.now(timezone.utc).isoformat(),
                        }
                    ],
                }
            ],
        }

    def _rule_id(self, attack_result: AttackResult) -> str:
        """Generate a rule ID from category and severity."""
        return (
            f"llmvault/{attack_result.attack.category.value}/{attack_result.attack.severity.value}"
        )

    def _make_rules(self, vulnerable_results: list[AttackResult]) -> list[dict[str, Any]]:
        """Generate deduplicated SARIF rule definitions."""
        seen: dict[str, dict[str, Any]] = {}
        for ar in vulnerable_results:
            rule_id = self._rule_id(ar)
            if rule_id in seen:
                continue
            seen[rule_id] = {
                "id": rule_id,
                "name": f"{ar.attack.category.value}_{ar.attack.severity.value}",
                "shortDescription": {
                    "text": (
                        f"LLM {ar.attack.category.value} vulnerability "
                        f"({ar.attack.severity.value} severity)"
                    ),
                },
                "defaultConfiguration": {
                    "level": _SEVERITY_TO_SARIF_LEVEL[ar.attack.severity],
                },
                "properties": {
                    "tags": ["security", "llm", ar.attack.category.value],
                },
            }
        return list(seen.values())

    def _make_result(self, attack_result: AttackResult, rule_index: int) -> dict[str, Any]:
        """Convert a single vulnerable AttackResult to a SARIF result."""
        rule_id = self._rule_id(attack_result)
        message_parts = [attack_result.attack.name]
        if attack_result.attack.description:
            message_parts.append(attack_result.attack.description)
        if attack_result.explanation:
            message_parts.append(attack_result.explanation)

        response_excerpt = attack_result.response[:200]
        if len(attack_result.response) > 200:
            response_excerpt += "..."

        return {
            "ruleId": rule_id,
            "ruleIndex": rule_index,
            "level": _SEVERITY_TO_SARIF_LEVEL[attack_result.attack.severity],
            "message": {"text": " - ".join(message_parts)},
            "properties": {
                "confidence": attack_result.confidence,
                "model": "",  # Filled by caller context if needed
                "response": response_excerpt,
                "prompt": attack_result.attack.prompt[:300],
            },
        }
