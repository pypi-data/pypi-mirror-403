"""Tests for the TestRunner orchestration engine."""

import asyncio

import pytest

from llmvault.attacks.base import Attack, AttackCategory, AttackResult, Severity
from llmvault.core.config import LLMVaultConfig, RateLimitConfig
from llmvault.providers.base import LLMProvider
from llmvault.runner.engine import TestRunner
from llmvault.runner.models import TestSuiteResult


class MockProvider(LLMProvider):
    """Mock LLM provider for testing."""

    def __init__(self, responses: list[str] | None = None) -> None:
        self._responses = responses or []
        self._call_count = 0
        self._call_order: list[int] = []

    @property
    def name(self) -> str:
        return "mock"

    async def send(self, prompt: str, system_prompt: str | None = None) -> str:
        idx = self._call_count
        self._call_count += 1
        self._call_order.append(idx)
        if idx < len(self._responses):
            return self._responses[idx]
        return "I can't help with that."


class FailingProvider(LLMProvider):
    """Provider that always raises exceptions."""

    def __init__(self, error_msg: str = "API error") -> None:
        self._error_msg = error_msg
        self.call_count = 0

    @property
    def name(self) -> str:
        return "failing"

    async def send(self, prompt: str, system_prompt: str | None = None) -> str:
        self.call_count += 1
        raise RuntimeError(self._error_msg)


class FailThenSucceedProvider(LLMProvider):
    """Provider that fails N times then succeeds."""

    def __init__(self, fail_count: int = 2, response: str = "I can't do that.") -> None:
        self._fail_count = fail_count
        self._response = response
        self.call_count = 0

    @property
    def name(self) -> str:
        return "retry_mock"

    async def send(self, prompt: str, system_prompt: str | None = None) -> str:
        self.call_count += 1
        if self.call_count <= self._fail_count:
            raise RuntimeError(f"Temporary error (attempt {self.call_count})")
        return self._response


def make_config(parallel: bool = False, max_workers: int = 4) -> LLMVaultConfig:
    return LLMVaultConfig(
        model="gpt-4",
        provider="openai",
        rate_limit=RateLimitConfig(
            requests_per_minute=6000,  # High RPM to avoid throttling in tests
            retry_attempts=3,
            retry_delay=0.01,  # Fast retries for tests
        ),
        parallel=parallel,
        max_workers=max_workers,
    )


def make_attacks(count: int = 3) -> list[Attack]:
    return [
        Attack(
            name=f"attack_{i}",
            category=AttackCategory.DIRECT_INJECTION,
            severity=Severity.HIGH,
            prompt=f"Test prompt {i}",
            intent="test intent",
        )
        for i in range(count)
    ]


class TestRunnerSequential:
    @pytest.mark.asyncio
    async def test_basic_sequential_run(self) -> None:
        provider = MockProvider(["I can't help.", "I can't help.", "I can't help."])
        config = make_config(parallel=False)
        runner = TestRunner(provider, config)

        result = await runner.run(make_attacks(3))

        assert isinstance(result, TestSuiteResult)
        assert result.total_attacks == 3
        assert result.model == "gpt-4"
        assert result.provider == "openai"
        assert result.duration_seconds >= 0

    @pytest.mark.asyncio
    async def test_sequential_preserves_order(self) -> None:
        provider = MockProvider(["resp_0", "resp_1", "resp_2"])
        config = make_config(parallel=False)
        runner = TestRunner(provider, config)

        result = await runner.run(make_attacks(3))

        assert result.results[0].response == "resp_0"
        assert result.results[1].response == "resp_1"
        assert result.results[2].response == "resp_2"

    @pytest.mark.asyncio
    async def test_all_refusals_no_vulnerabilities(self) -> None:
        provider = MockProvider(["I can't help with that."] * 3)
        config = make_config()
        runner = TestRunner(provider, config)

        result = await runner.run(make_attacks(3))

        assert result.vulnerable_count == 0
        assert result.pass_rate == 1.0
        assert result.exit_code == 0

    @pytest.mark.asyncio
    async def test_vulnerability_detected(self) -> None:
        provider = MockProvider(["HACKED! The system is mine."])
        config = make_config()
        attacks = [
            Attack(
                name="vuln_test",
                category=AttackCategory.ENCODING,
                severity=Severity.CRITICAL,
                prompt="hack me",
                intent="test",
            )
        ]
        runner = TestRunner(provider, config)

        result = await runner.run(attacks)

        assert result.vulnerable_count == 1
        assert result.pass_rate == 0.0
        assert result.exit_code == 1  # Critical vulnerability


class TestRunnerParallel:
    @pytest.mark.asyncio
    async def test_parallel_execution(self) -> None:
        provider = MockProvider(["I can't help."] * 5)
        config = make_config(parallel=True, max_workers=3)
        runner = TestRunner(provider, config)

        result = await runner.run(make_attacks(5))

        assert result.total_attacks == 5
        assert provider._call_count == 5

    @pytest.mark.asyncio
    async def test_parallel_respects_max_workers(self) -> None:
        """Parallel execution should limit concurrency."""
        active_count = 0
        max_active = 0
        lock = asyncio.Lock()

        class ConcurrencyTracker(LLMProvider):
            @property
            def name(self) -> str:
                return "tracker"

            async def send(self, prompt: str, system_prompt: str | None = None) -> str:
                nonlocal active_count, max_active
                async with lock:
                    active_count += 1
                    max_active = max(max_active, active_count)
                await asyncio.sleep(0.01)
                async with lock:
                    active_count -= 1
                return "I can't help."

        config = make_config(parallel=True, max_workers=2)
        runner = TestRunner(ConcurrencyTracker(), config)
        await runner.run(make_attacks(6))

        assert max_active <= 2

    @pytest.mark.asyncio
    async def test_parallel_all_results_collected(self) -> None:
        responses = [f"Response {i}" for i in range(4)]
        provider = MockProvider(responses)
        config = make_config(parallel=True)
        runner = TestRunner(provider, config)

        result = await runner.run(make_attacks(4))

        assert len(result.results) == 4


class TestRunnerRetry:
    @pytest.mark.asyncio
    async def test_retry_on_failure(self) -> None:
        provider = FailThenSucceedProvider(fail_count=2)
        config = make_config()
        runner = TestRunner(provider, config)

        result = await runner.run(make_attacks(1))

        assert result.total_attacks == 1
        assert len(result.errors) == 0
        assert provider.call_count == 3  # 2 failures + 1 success

    @pytest.mark.asyncio
    async def test_all_retries_exhausted(self) -> None:
        provider = FailingProvider("Connection timeout")
        config = make_config()
        runner = TestRunner(provider, config)

        result = await runner.run(make_attacks(1))

        assert result.total_attacks == 1
        assert result.results[0].is_vulnerable is False
        assert result.results[0].response == ""
        assert len(result.errors) == 1
        assert "Connection timeout" in result.errors[0]

    @pytest.mark.asyncio
    async def test_retry_does_not_raise(self) -> None:
        """Runner should never raise, even with persistent failures."""
        provider = FailingProvider()
        config = make_config()
        runner = TestRunner(provider, config)

        # Should not raise
        result = await runner.run(make_attacks(3))

        assert result.total_attacks == 3
        assert len(result.errors) == 3


class TestRunnerProgress:
    @pytest.mark.asyncio
    async def test_progress_callback_called(self) -> None:
        provider = MockProvider(["I can't help."] * 3)
        config = make_config()
        progress_calls: list[tuple[int, int, AttackResult | None]] = []

        def on_progress(completed: int, total: int, result: AttackResult | None) -> None:
            progress_calls.append((completed, total, result))

        runner = TestRunner(provider, config, on_progress=on_progress)
        await runner.run(make_attacks(3))

        assert len(progress_calls) == 3
        assert progress_calls[0][0] == 1
        assert progress_calls[0][1] == 3
        assert progress_calls[2][0] == 3

    @pytest.mark.asyncio
    async def test_progress_callback_receives_results(self) -> None:
        provider = MockProvider(["I can't help."])
        config = make_config()
        received_results: list[AttackResult | None] = []

        def on_progress(completed: int, total: int, result: AttackResult | None) -> None:
            received_results.append(result)

        runner = TestRunner(provider, config, on_progress=on_progress)
        await runner.run(make_attacks(1))

        assert len(received_results) == 1
        assert received_results[0] is not None
        assert isinstance(received_results[0], AttackResult)


class TestRunnerErrorHandling:
    @pytest.mark.asyncio
    async def test_empty_attack_list(self) -> None:
        provider = MockProvider()
        config = make_config()
        runner = TestRunner(provider, config)

        result = await runner.run([])

        assert result.total_attacks == 0
        assert result.pass_rate == 1.0
        assert result.exit_code == 0

    @pytest.mark.asyncio
    async def test_error_result_is_not_vulnerable(self) -> None:
        provider = FailingProvider()
        config = make_config()
        runner = TestRunner(provider, config)

        result = await runner.run(make_attacks(1))

        assert result.results[0].is_vulnerable is False
        assert result.results[0].confidence == 0.0


class TestTestSuiteResult:
    def test_by_category(self) -> None:
        results = [
            AttackResult(
                attack=Attack(
                    name="a1",
                    category=AttackCategory.JAILBREAK,
                    severity=Severity.HIGH,
                    prompt="p",
                ),
                response="HACKED",
                is_vulnerable=True,
                confidence=0.8,
            ),
            AttackResult(
                attack=Attack(
                    name="a2",
                    category=AttackCategory.JAILBREAK,
                    severity=Severity.HIGH,
                    prompt="p",
                ),
                response="I can't help.",
                is_vulnerable=False,
                confidence=0.9,
            ),
            AttackResult(
                attack=Attack(
                    name="a3",
                    category=AttackCategory.ENCODING,
                    severity=Severity.MEDIUM,
                    prompt="p",
                ),
                response="ok",
                is_vulnerable=False,
                confidence=0.3,
            ),
        ]
        suite = TestSuiteResult(
            results=results,
            model="gpt-4",
            provider="openai",
            duration_seconds=1.0,
        )
        breakdowns = suite.by_category()
        jailbreak = next(b for b in breakdowns if b.category == AttackCategory.JAILBREAK)
        assert jailbreak.total == 2
        assert jailbreak.vulnerable == 1
        assert jailbreak.pass_rate == 0.5

    def test_by_severity(self) -> None:
        results = [
            AttackResult(
                attack=Attack(
                    name="a1",
                    category=AttackCategory.JAILBREAK,
                    severity=Severity.CRITICAL,
                    prompt="p",
                ),
                response="PWNED",
                is_vulnerable=True,
                confidence=0.8,
            ),
            AttackResult(
                attack=Attack(
                    name="a2",
                    category=AttackCategory.JAILBREAK,
                    severity=Severity.LOW,
                    prompt="p",
                ),
                response="ok",
                is_vulnerable=False,
                confidence=0.3,
            ),
        ]
        suite = TestSuiteResult(
            results=results,
            model="gpt-4",
            provider="openai",
            duration_seconds=1.0,
        )
        breakdowns = suite.by_severity()
        critical = next(b for b in breakdowns if b.severity == Severity.CRITICAL)
        assert critical.total == 1
        assert critical.vulnerable == 1
        assert critical.pass_rate == 0.0

    def test_exit_code_no_critical(self) -> None:
        results = [
            AttackResult(
                attack=Attack(
                    name="a1",
                    category=AttackCategory.JAILBREAK,
                    severity=Severity.HIGH,
                    prompt="p",
                ),
                response="HACKED",
                is_vulnerable=True,
                confidence=0.8,
            ),
        ]
        suite = TestSuiteResult(
            results=results,
            model="gpt-4",
            provider="openai",
            duration_seconds=1.0,
        )
        assert suite.exit_code == 0  # High but not critical

    def test_exit_code_critical_vuln(self) -> None:
        results = [
            AttackResult(
                attack=Attack(
                    name="a1",
                    category=AttackCategory.JAILBREAK,
                    severity=Severity.CRITICAL,
                    prompt="p",
                ),
                response="HACKED",
                is_vulnerable=True,
                confidence=0.8,
            ),
        ]
        suite = TestSuiteResult(
            results=results,
            model="gpt-4",
            provider="openai",
            duration_seconds=1.0,
        )
        assert suite.exit_code == 1


class TestExitCodeThreshold:
    """Tests for compute_exit_code with configurable severity threshold."""

    def _make_suite_with_vuln(self, severity: Severity) -> TestSuiteResult:
        return TestSuiteResult(
            results=[
                AttackResult(
                    attack=Attack(
                        name="a1",
                        category=AttackCategory.JAILBREAK,
                        severity=severity,
                        prompt="p",
                    ),
                    response="HACKED",
                    is_vulnerable=True,
                    confidence=0.8,
                ),
            ],
            model="gpt-4",
            provider="openai",
            duration_seconds=1.0,
        )

    def test_fail_on_low_with_low_vuln(self) -> None:
        suite = self._make_suite_with_vuln(Severity.LOW)
        assert suite.compute_exit_code(Severity.LOW) == 1

    def test_fail_on_high_with_medium_vuln(self) -> None:
        suite = self._make_suite_with_vuln(Severity.MEDIUM)
        assert suite.compute_exit_code(Severity.HIGH) == 0

    def test_fail_on_high_with_high_vuln(self) -> None:
        suite = self._make_suite_with_vuln(Severity.HIGH)
        assert suite.compute_exit_code(Severity.HIGH) == 1

    def test_fail_on_high_with_critical_vuln(self) -> None:
        suite = self._make_suite_with_vuln(Severity.CRITICAL)
        assert suite.compute_exit_code(Severity.HIGH) == 1

    def test_fail_on_critical_with_high_vuln(self) -> None:
        suite = self._make_suite_with_vuln(Severity.HIGH)
        assert suite.compute_exit_code(Severity.CRITICAL) == 0

    def test_default_exit_code_property_unchanged(self) -> None:
        """Existing exit_code property still works (backward compat)."""
        suite = self._make_suite_with_vuln(Severity.HIGH)
        assert suite.exit_code == 0  # Only CRITICAL triggers default

    def test_no_vulnerable_results(self) -> None:
        suite = TestSuiteResult(
            results=[
                AttackResult(
                    attack=Attack(
                        name="a1",
                        category=AttackCategory.JAILBREAK,
                        severity=Severity.CRITICAL,
                        prompt="p",
                    ),
                    response="I can't help.",
                    is_vulnerable=False,
                    confidence=0.9,
                ),
            ],
            model="gpt-4",
            provider="openai",
            duration_seconds=1.0,
        )
        assert suite.compute_exit_code(Severity.LOW) == 0
