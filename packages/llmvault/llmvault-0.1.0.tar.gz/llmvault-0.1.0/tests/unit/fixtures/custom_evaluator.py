"""Test fixture evaluators for evaluator_loader tests."""

from llmvault.attacks.base import Attack
from llmvault.runner.evaluator import EvalResult


class AlwaysVulnerableEvaluator:
    """Evaluator that always reports vulnerable."""

    def evaluate(self, attack: Attack, response: str) -> EvalResult:
        return EvalResult(
            is_vulnerable=True,
            confidence=1.0,
            explanation="Always vulnerable (test fixture).",
        )


class NoEvaluateMethod:
    """Class without evaluate method (for negative tests)."""

    def analyze(self, attack: Attack, response: str) -> str:
        return "analyzed"


def always_safe(attack: Attack, response: str) -> EvalResult:
    """Function evaluator that always reports safe."""
    return EvalResult(
        is_vulnerable=False,
        confidence=1.0,
        explanation="Always safe (test fixture).",
    )


NOT_CALLABLE = "just a string"
