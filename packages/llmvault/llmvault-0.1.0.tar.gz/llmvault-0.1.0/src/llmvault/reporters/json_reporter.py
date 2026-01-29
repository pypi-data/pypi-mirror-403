"""JSON reporter for machine-readable test results."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import llmvault
from llmvault.runner.models import TestSuiteResult


class JSONReporter:
    """Generates structured JSON reports for CI/CD pipeline consumption."""

    def generate(self, result: TestSuiteResult, output_path: Path) -> None:
        """Serialize TestSuiteResult to JSON and write to output_path."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        data = self.to_dict(result)
        output_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def to_dict(self, result: TestSuiteResult) -> dict[str, Any]:
        """Convert TestSuiteResult into a serializable dictionary."""
        return {
            "version": llmvault.__version__,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "model": result.model,
                "provider": result.provider,
                "duration_seconds": result.duration_seconds,
                "total_attacks": result.total_attacks,
                "vulnerable_count": result.vulnerable_count,
                "pass_rate": result.pass_rate,
                "exit_code": result.exit_code,
            },
            "breakdowns": {
                "by_category": [
                    {
                        "category": b.category.value,
                        "total": b.total,
                        "vulnerable": b.vulnerable,
                        "pass_rate": b.pass_rate,
                    }
                    for b in result.by_category()
                ],
                "by_severity": [
                    {
                        "severity": b.severity.value,
                        "total": b.total,
                        "vulnerable": b.vulnerable,
                        "pass_rate": b.pass_rate,
                    }
                    for b in result.by_severity()
                ],
            },
            "results": [
                {
                    "attack": {
                        "name": r.attack.name,
                        "category": r.attack.category.value,
                        "severity": r.attack.severity.value,
                        "description": r.attack.description,
                        "prompt": r.attack.prompt,
                        "intent": r.attack.intent,
                    },
                    "response": r.response,
                    "is_vulnerable": r.is_vulnerable,
                    "confidence": r.confidence,
                    "explanation": r.explanation,
                }
                for r in result.results
            ],
            "errors": result.errors,
        }
