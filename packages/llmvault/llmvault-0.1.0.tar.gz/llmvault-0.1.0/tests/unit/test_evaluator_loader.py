"""Tests for custom evaluator plugin loading."""

import sys
from pathlib import Path

import pytest

from llmvault.attacks.base import Attack, AttackCategory, Severity
from llmvault.runner.evaluator import EvalResult
from llmvault.runner.evaluator_loader import EvaluatorPlugin, load_evaluator

# Ensure fixtures directory is importable
_FIXTURES_DIR = str(Path(__file__).parent / "fixtures")
if _FIXTURES_DIR not in sys.path:
    sys.path.insert(0, _FIXTURES_DIR)


def _make_attack() -> Attack:
    return Attack(
        name="test",
        category=AttackCategory.JAILBREAK,
        severity=Severity.HIGH,
        prompt="test prompt",
    )


class TestEvaluatorPlugin:
    """Tests for EvaluatorPlugin adapter."""

    def test_delegates_to_fn(self) -> None:
        def my_eval(attack: Attack, response: str) -> EvalResult:
            return EvalResult(is_vulnerable=True, confidence=0.99, explanation="custom")

        plugin = EvaluatorPlugin(my_eval)
        result = plugin.evaluate(_make_attack(), "some response")
        assert result.is_vulnerable is True
        assert result.confidence == 0.99
        assert result.explanation == "custom"

    def test_passes_attack_and_response(self) -> None:
        received: list[tuple[Attack, str]] = []

        def capture_eval(attack: Attack, response: str) -> EvalResult:
            received.append((attack, response))
            return EvalResult(is_vulnerable=False, confidence=0.5, explanation="ok")

        plugin = EvaluatorPlugin(capture_eval)
        attack = _make_attack()
        plugin.evaluate(attack, "hello world")
        assert len(received) == 1
        assert received[0][0] is attack
        assert received[0][1] == "hello world"


class TestLoadEvaluator:
    """Tests for load_evaluator function."""

    def test_load_class_with_evaluate(self) -> None:
        evaluator = load_evaluator("custom_evaluator:AlwaysVulnerableEvaluator")
        result = evaluator.evaluate(_make_attack(), "response")
        assert result.is_vulnerable is True
        assert result.confidence == 1.0

    def test_load_function(self) -> None:
        evaluator = load_evaluator("custom_evaluator:always_safe")
        result = evaluator.evaluate(_make_attack(), "response")
        assert result.is_vulnerable is False
        assert result.confidence == 1.0

    def test_loaded_function_is_wrapped(self) -> None:
        evaluator = load_evaluator("custom_evaluator:always_safe")
        assert isinstance(evaluator, EvaluatorPlugin)

    def test_invalid_spec_no_colon(self) -> None:
        with pytest.raises(ValueError, match="Invalid evaluator spec"):
            load_evaluator("custom_evaluator.AlwaysVulnerableEvaluator")

    def test_missing_module(self) -> None:
        with pytest.raises(ModuleNotFoundError):
            load_evaluator("nonexistent_module:SomeClass")

    def test_missing_attribute(self) -> None:
        with pytest.raises(AttributeError):
            load_evaluator("custom_evaluator:NonExistentClass")

    def test_class_without_evaluate(self) -> None:
        with pytest.raises(ValueError, match="no 'evaluate' method"):
            load_evaluator("custom_evaluator:NoEvaluateMethod")

    def test_non_callable_attribute(self) -> None:
        with pytest.raises(ValueError, match="not callable"):
            load_evaluator("custom_evaluator:NOT_CALLABLE")

    def test_loaded_evaluator_is_evaluator_interface(self) -> None:
        evaluator = load_evaluator("custom_evaluator:AlwaysVulnerableEvaluator")
        # Must have evaluate method
        assert hasattr(evaluator, "evaluate")
        assert callable(evaluator.evaluate)
