"""Custom evaluator plugin loading utilities."""

import importlib
from collections.abc import Callable
from typing import cast

from llmvault.attacks.base import Attack
from llmvault.runner.evaluator import EvalResult, Evaluator


class EvaluatorPlugin(Evaluator):
    """Adapter that wraps a user-provided callable as an Evaluator.

    The callable must accept (Attack, str) and return EvalResult.
    """

    def __init__(self, evaluator_fn: Callable[[Attack, str], EvalResult]) -> None:
        self._fn = evaluator_fn

    def evaluate(self, attack: Attack, response: str) -> EvalResult:
        """Delegate evaluation to the wrapped callable."""
        return self._fn(attack, response)


def load_evaluator(spec: str) -> Evaluator:
    """Load an evaluator from a module:attribute specification.

    Format: 'path.to.module:ClassName' or 'path.to.module:function_name'

    If the loaded attribute is a class, it is instantiated (no-arg constructor).
    If the instance has an ``evaluate`` method, it is used directly.
    If the attribute is a bare callable (function), it is wrapped in EvaluatorPlugin.

    Raises:
        ValueError: If the spec format is invalid or the attribute is not usable.
        ImportError: If the module cannot be imported.
        AttributeError: If the attribute is not found in the module.
    """
    if ":" not in spec:
        msg = (
            f"Invalid evaluator spec '{spec}'. "
            f"Expected format: 'module.path:ClassName' or 'module.path:function'"
        )
        raise ValueError(msg)

    module_path, attr_name = spec.rsplit(":", 1)
    module = importlib.import_module(module_path)
    attr = getattr(module, attr_name)

    # If it's a class, instantiate it
    if isinstance(attr, type):
        instance = attr()
        if hasattr(instance, "evaluate") and callable(instance.evaluate):
            return cast(Evaluator, instance)
        msg = f"Class '{attr_name}' has no 'evaluate' method."
        raise ValueError(msg)

    # If it's a callable (function), wrap it
    if callable(attr):
        return EvaluatorPlugin(attr)

    msg = f"Attribute '{attr_name}' in '{module_path}' is not callable."
    raise ValueError(msg)
