"""Async test runner engine for executing attacks against LLM providers."""

import asyncio
import time
from collections.abc import Callable

from llmvault.attacks.base import Attack, AttackResult
from llmvault.core.config import LLMVaultConfig
from llmvault.providers.base import LLMProvider
from llmvault.runner.evaluator import Evaluator
from llmvault.runner.models import TestSuiteResult
from llmvault.runner.rate_limiter import RateLimiter

ProgressCallback = Callable[[int, int, AttackResult | None], None]


class TestRunner:
    """Async orchestrator for running attacks against an LLM provider.

    Supports sequential and parallel execution, rate limiting,
    exponential backoff retry, and progress reporting.
    """

    def __init__(
        self,
        provider: LLMProvider,
        config: LLMVaultConfig,
        evaluator: Evaluator | None = None,
        on_progress: ProgressCallback | None = None,
    ) -> None:
        self._provider = provider
        self._config = config
        self._evaluator = evaluator or Evaluator()
        self._on_progress = on_progress
        self._rate_limiter = RateLimiter(config.rate_limit.requests_per_minute)

    async def run(self, attacks: list[Attack]) -> TestSuiteResult:
        """Execute all attacks and return aggregated results.

        Never raises - errors are captured in the result.
        """
        start_time = time.monotonic()
        errors: list[str] = []
        results: list[AttackResult] = []

        if self._config.parallel:
            results, errors = await self._run_parallel(attacks)
        else:
            results, errors = await self._run_sequential(attacks)

        duration = time.monotonic() - start_time
        return TestSuiteResult(
            results=results,
            model=self._config.model,
            provider=self._config.provider or "",
            duration_seconds=duration,
            errors=errors,
        )

    async def _run_sequential(self, attacks: list[Attack]) -> tuple[list[AttackResult], list[str]]:
        """Run attacks one at a time."""
        results: list[AttackResult] = []
        errors: list[str] = []
        total = len(attacks)

        for i, attack in enumerate(attacks):
            result, error = await self._execute_single(attack)
            results.append(result)
            if error:
                errors.append(error)
            if self._on_progress:
                self._on_progress(i + 1, total, result)

        return results, errors

    async def _run_parallel(self, attacks: list[Attack]) -> tuple[list[AttackResult], list[str]]:
        """Run attacks concurrently with semaphore-based concurrency control."""
        semaphore = asyncio.Semaphore(self._config.max_workers)
        results: list[AttackResult | None] = [None] * len(attacks)
        errors: list[str] = []
        completed = 0
        total = len(attacks)
        lock = asyncio.Lock()

        async def worker(index: int, attack: Attack) -> None:
            nonlocal completed
            async with semaphore:
                result, error = await self._execute_single(attack)
                async with lock:
                    results[index] = result
                    if error:
                        errors.append(error)
                    completed += 1
                    if self._on_progress:
                        self._on_progress(completed, total, result)

        tasks = [asyncio.create_task(worker(i, attack)) for i, attack in enumerate(attacks)]
        await asyncio.gather(*tasks)

        return [r for r in results if r is not None], errors

    async def _execute_single(self, attack: Attack) -> tuple[AttackResult, str | None]:
        """Execute a single attack with retry and rate limiting.

        Returns (result, error_message). Never raises.
        """
        retry_attempts = self._config.rate_limit.retry_attempts
        retry_delay = self._config.rate_limit.retry_delay
        last_error: str | None = None

        for attempt in range(retry_attempts):
            try:
                await self._rate_limiter.acquire()
                response = await self._provider.send(
                    prompt=attack.prompt,
                    system_prompt=attack.system_prompt,
                )
                eval_result = self._evaluator.evaluate(attack, response)
                return (
                    AttackResult(
                        attack=attack,
                        response=response,
                        is_vulnerable=eval_result.is_vulnerable,
                        confidence=eval_result.confidence,
                        explanation=eval_result.explanation,
                    ),
                    None,
                )
            except Exception as exc:  # noqa: BLE001
                last_error = f"{attack.name}: {exc}"
                if attempt < retry_attempts - 1:
                    await asyncio.sleep(retry_delay * (2**attempt))

        # All retries exhausted - return non-vulnerable result with error
        return (
            AttackResult(
                attack=attack,
                response="",
                is_vulnerable=False,
                confidence=0.0,
                explanation=f"Error after {retry_attempts} attempts: {last_error}",
            ),
            last_error,
        )
