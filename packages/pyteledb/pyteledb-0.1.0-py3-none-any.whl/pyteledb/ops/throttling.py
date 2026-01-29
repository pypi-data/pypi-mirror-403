"""Rate limiting and throttling for Telegram API.

Implements backoff strategies and burst allowance.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

from pyteledb.utils.logging import get_logger
from pyteledb.utils.time import monotonic_timestamp

logger = get_logger(__name__)


@dataclass
class RateLimiterConfig:
    """Configuration for RateLimiter."""

    # Telegram limits: ~30 messages per second to same chat
    # ~20 messages per minute to same group
    # We use conservative defaults
    requests_per_second: float = 20.0
    burst_size: int = 5
    recovery_rate: float = 1.0  # Tokens per second to recover


class RateLimiter:
    """
    Token bucket rate limiter.

    Limits request rate while allowing short bursts.
    """

    def __init__(self, config: RateLimiterConfig | None = None) -> None:
        """
        Initialize the rate limiter.

        Args:
            config: Rate limiter configuration.
        """
        self.config = config or RateLimiterConfig()
        self._tokens = float(self.config.burst_size)
        self._last_update = monotonic_timestamp()
        self._lock = asyncio.Lock()

    async def acquire(self, tokens: float = 1.0) -> float:
        """
        Acquire tokens, waiting if necessary.

        Args:
            tokens: Number of tokens to acquire.

        Returns:
            Time waited in seconds.
        """
        async with self._lock:
            waited = 0.0

            while True:
                self._refill()

                if self._tokens >= tokens:
                    self._tokens -= tokens
                    return waited

                # Calculate wait time
                needed = tokens - self._tokens
                wait_time = needed / self.config.recovery_rate
                waited += wait_time
                await asyncio.sleep(wait_time)

    def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = monotonic_timestamp()
        elapsed = now - self._last_update
        self._last_update = now

        # Add tokens based on elapsed time
        self._tokens = min(
            self.config.burst_size,
            self._tokens + elapsed * self.config.recovery_rate,
        )

    async def try_acquire(self, tokens: float = 1.0) -> bool:
        """
        Try to acquire tokens without waiting.

        Args:
            tokens: Number of tokens to acquire.

        Returns:
            True if tokens were acquired, False otherwise.
        """
        async with self._lock:
            self._refill()
            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            return False

    @property
    def available_tokens(self) -> float:
        """Get currently available tokens."""
        return self._tokens


@dataclass
class ThrottlerConfig:
    """Configuration for Throttler."""

    min_delay: float = 0.05  # Minimum delay between requests
    max_delay: float = 60.0  # Maximum delay (for backoff)
    backoff_factor: float = 2.0  # Exponential backoff multiplier
    reset_after: float = 60.0  # Reset backoff after this many seconds of success


@dataclass
class ThrottlerState:
    """Internal state for Throttler."""

    current_delay: float = 0.05
    consecutive_errors: int = 0
    last_error_time: float = 0.0
    last_request_time: float = 0.0


class Throttler:
    """
    Adaptive throttler with exponential backoff.

    Adjusts request rate based on success/failure patterns.
    """

    def __init__(self, config: ThrottlerConfig | None = None) -> None:
        """
        Initialize the throttler.

        Args:
            config: Throttler configuration.
        """
        self.config = config or ThrottlerConfig()
        self._state = ThrottlerState(current_delay=config.min_delay if config else 0.05)
        self._lock = asyncio.Lock()

    async def wait(self) -> float:
        """
        Wait before making a request.

        Returns:
            Time waited in seconds.
        """
        async with self._lock:
            now = monotonic_timestamp()

            # Check if we should reset backoff
            if (
                self._state.consecutive_errors > 0
                and now - self._state.last_error_time > self.config.reset_after
            ):
                self._state.current_delay = self.config.min_delay
                self._state.consecutive_errors = 0

            # Calculate required wait time
            elapsed = now - self._state.last_request_time
            wait_time = max(0, self._state.current_delay - elapsed)

            if wait_time > 0:
                await asyncio.sleep(wait_time)

            self._state.last_request_time = monotonic_timestamp()
            return wait_time

    async def report_success(self) -> None:
        """Report a successful request."""
        async with self._lock:
            # Gradually reduce delay on success
            self._state.current_delay = max(
                self.config.min_delay,
                self._state.current_delay * 0.9,
            )
            self._state.consecutive_errors = 0

    async def report_error(self, retry_after: float | None = None) -> None:
        """
        Report a failed request.

        Args:
            retry_after: Explicit retry-after value (from rate limit).
        """
        async with self._lock:
            now = monotonic_timestamp()
            self._state.consecutive_errors += 1
            self._state.last_error_time = now

            if retry_after is not None:
                # Use server-provided retry-after
                self._state.current_delay = min(retry_after, self.config.max_delay)
            else:
                # Exponential backoff
                self._state.current_delay = min(
                    self._state.current_delay * self.config.backoff_factor,
                    self.config.max_delay,
                )

            logger.warning(
                f"Throttler backoff: delay={self._state.current_delay:.2f}s, "
                f"errors={self._state.consecutive_errors}"
            )

    @property
    def current_delay(self) -> float:
        """Get current delay value."""
        return self._state.current_delay

    @property
    def consecutive_errors(self) -> int:
        """Get consecutive error count."""
        return self._state.consecutive_errors

    def stats(self) -> dict[str, Any]:
        """Get throttler statistics."""
        return {
            "current_delay": self._state.current_delay,
            "consecutive_errors": self._state.consecutive_errors,
            "min_delay": self.config.min_delay,
            "max_delay": self.config.max_delay,
        }
