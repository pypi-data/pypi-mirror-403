"""Token bucket rate limiter for async LLM API calls."""

import asyncio
import time


class RateLimiter:
    """Async-compatible token bucket rate limiter.

    Starts full (allows initial burst up to capacity), then refills
    at a steady rate of requests_per_minute tokens per minute.
    """

    def __init__(self, requests_per_minute: int = 60) -> None:
        self._capacity = requests_per_minute
        self._tokens = float(requests_per_minute)
        self._refill_rate = requests_per_minute / 60.0  # tokens per second
        self._last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(self._capacity, self._tokens + elapsed * self._refill_rate)
        self._last_refill = now

    async def acquire(self) -> None:
        """Acquire a token, blocking until one is available."""
        while True:
            async with self._lock:
                self._refill()
                if self._tokens >= 1.0:
                    self._tokens -= 1.0
                    return
                # Calculate wait time for next token
                wait_time = (1.0 - self._tokens) / self._refill_rate
            await asyncio.sleep(wait_time)
