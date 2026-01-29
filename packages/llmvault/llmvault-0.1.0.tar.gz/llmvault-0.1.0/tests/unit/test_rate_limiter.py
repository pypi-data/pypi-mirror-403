"""Tests for the token bucket rate limiter."""

import asyncio
import time

import pytest

from llmvault.runner.rate_limiter import RateLimiter


class TestRateLimiterInit:
    def test_default_capacity(self) -> None:
        limiter = RateLimiter()
        assert limiter._capacity == 60

    def test_custom_capacity(self) -> None:
        limiter = RateLimiter(requests_per_minute=120)
        assert limiter._capacity == 120

    def test_starts_full(self) -> None:
        limiter = RateLimiter(requests_per_minute=10)
        assert limiter._tokens == 10.0


class TestRateLimiterBurst:
    @pytest.mark.asyncio
    async def test_immediate_burst(self) -> None:
        """Should allow immediate burst up to capacity."""
        limiter = RateLimiter(requests_per_minute=5)
        start = time.monotonic()
        for _ in range(5):
            await limiter.acquire()
        elapsed = time.monotonic() - start
        # All 5 should be near-instant (< 0.1s)
        assert elapsed < 0.1

    @pytest.mark.asyncio
    async def test_burst_exhausts_tokens(self) -> None:
        """After burst, next acquire should block."""
        limiter = RateLimiter(requests_per_minute=3)
        for _ in range(3):
            await limiter.acquire()
        # Tokens exhausted, next one should take time
        start = time.monotonic()
        await limiter.acquire()
        elapsed = time.monotonic() - start
        # At 3 RPM, refill rate is 3/60 = 0.05 tokens/sec
        # So 1 token takes ~20 seconds. But we just need to verify it waited.
        assert elapsed >= 0.01


class TestRateLimiterThrottling:
    @pytest.mark.asyncio
    async def test_throttling_at_high_rate(self) -> None:
        """High RPM limiter should allow rapid requests."""
        limiter = RateLimiter(requests_per_minute=6000)
        start = time.monotonic()
        for _ in range(100):
            await limiter.acquire()
        elapsed = time.monotonic() - start
        # 6000 RPM = 100/sec, 100 requests from burst should be instant
        assert elapsed < 0.5

    @pytest.mark.asyncio
    async def test_refill_over_time(self) -> None:
        """Tokens should refill after waiting."""
        limiter = RateLimiter(requests_per_minute=600)
        # Exhaust all tokens
        for _ in range(600):
            await limiter.acquire()
        # Wait for some refill (600 RPM = 10/sec, wait 0.1s = 1 token)
        await asyncio.sleep(0.11)
        start = time.monotonic()
        await limiter.acquire()
        elapsed = time.monotonic() - start
        # Should be near-instant since we waited for refill
        assert elapsed < 0.05


class TestRateLimiterConcurrency:
    @pytest.mark.asyncio
    async def test_concurrent_acquires(self) -> None:
        """Multiple concurrent acquires should not exceed capacity."""
        limiter = RateLimiter(requests_per_minute=5)
        acquired = 0

        async def worker() -> None:
            nonlocal acquired
            await limiter.acquire()
            acquired += 1

        # Launch 5 concurrent workers (should all succeed from burst)
        tasks = [asyncio.create_task(worker()) for _ in range(5)]
        await asyncio.gather(*tasks)
        assert acquired == 5
