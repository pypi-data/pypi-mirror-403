"""
Rate limiting for FinVista.

This module provides rate limiting functionality to prevent API abuse
and avoid being blocked by data sources. It supports per-source limits
and uses a token bucket algorithm for smooth rate limiting.

Example:
    >>> from finvista._fetchers.rate_limiter import rate_limiter
    >>> rate_limiter.set_limit("eastmoney", requests_per_second=5)
    >>> rate_limiter.acquire("eastmoney")  # Blocks if rate limit exceeded
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """
    Rate limit configuration for a data source.

    Attributes:
        requests_per_second: Maximum requests per second.
        requests_per_minute: Maximum requests per minute.
        burst_size: Maximum burst size (tokens in bucket).
    """

    requests_per_second: float = 5.0
    requests_per_minute: float | None = None
    burst_size: int = 10


class TokenBucket:
    """
    Token bucket rate limiter implementation.

    This implementation allows for bursting up to a configured limit
    while maintaining a steady-state rate limit over time.

    Attributes:
        rate: Tokens added per second.
        capacity: Maximum tokens in the bucket.

    Example:
        >>> bucket = TokenBucket(rate=5.0, capacity=10)
        >>> bucket.acquire()  # Returns immediately if tokens available
        >>> bucket.acquire(block=True)  # Blocks until token available
    """

    def __init__(self, rate: float, capacity: int) -> None:
        """
        Initialize the token bucket.

        Args:
            rate: Tokens added per second.
            capacity: Maximum tokens in the bucket.
        """
        self.rate = rate
        self.capacity = capacity
        self._tokens = float(capacity)
        self._last_update = time.monotonic()
        self._lock = threading.Lock()

    def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.monotonic()
        elapsed = now - self._last_update
        self._tokens = min(self.capacity, self._tokens + elapsed * self.rate)
        self._last_update = now

    def acquire(self, tokens: int = 1, block: bool = True, timeout: float | None = None) -> bool:
        """
        Acquire tokens from the bucket.

        Args:
            tokens: Number of tokens to acquire.
            block: Whether to block until tokens are available.
            timeout: Maximum time to wait (None for no timeout).

        Returns:
            True if tokens were acquired, False otherwise.
        """
        deadline = time.monotonic() + timeout if timeout else None

        with self._lock:
            while True:
                self._refill()

                if self._tokens >= tokens:
                    self._tokens -= tokens
                    return True

                if not block:
                    return False

                # Calculate wait time
                needed = tokens - self._tokens
                wait_time = needed / self.rate

                if deadline is not None:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        return False
                    wait_time = min(wait_time, remaining)

                # Release lock while waiting
                self._lock.release()
                try:
                    time.sleep(wait_time)
                finally:
                    self._lock.acquire()

    @property
    def available(self) -> float:
        """Get the number of available tokens."""
        with self._lock:
            self._refill()
            return self._tokens


class RateLimiter:
    """
    Multi-source rate limiter.

    This class manages rate limits for multiple data sources,
    ensuring that each source's rate limit is respected.

    Example:
        >>> limiter = RateLimiter()
        >>> limiter.set_limit("eastmoney", requests_per_second=5)
        >>> limiter.acquire("eastmoney")
    """

    def __init__(self) -> None:
        """Initialize the rate limiter."""
        self._buckets: dict[str, TokenBucket] = {}
        self._configs: dict[str, RateLimitConfig] = {}
        self._lock = threading.Lock()

        # Default rate limits for known sources
        self._default_limits: dict[str, RateLimitConfig] = {
            "eastmoney": RateLimitConfig(requests_per_second=5.0, burst_size=10),
            "sina": RateLimitConfig(requests_per_second=3.0, burst_size=5),
            "tencent": RateLimitConfig(requests_per_second=5.0, burst_size=10),
            "yahoo": RateLimitConfig(requests_per_second=2.0, burst_size=5),
            "fred": RateLimitConfig(requests_per_second=1.0, burst_size=3),
        }

    def _get_bucket(self, source: str) -> TokenBucket:
        """
        Get or create a token bucket for a source.

        Args:
            source: The data source name.

        Returns:
            The token bucket for the source.
        """
        with self._lock:
            if source not in self._buckets:
                config = self._configs.get(source) or self._default_limits.get(
                    source, RateLimitConfig()
                )
                self._buckets[source] = TokenBucket(
                    rate=config.requests_per_second,
                    capacity=config.burst_size,
                )
            return self._buckets[source]

    def set_limit(
        self,
        source: str,
        requests_per_second: float | None = None,
        requests_per_minute: float | None = None,
        burst_size: int | None = None,
    ) -> None:
        """
        Set rate limit for a data source.

        Args:
            source: The data source name.
            requests_per_second: Maximum requests per second.
            requests_per_minute: Maximum requests per minute (converted to per-second).
            burst_size: Maximum burst size.
        """
        with self._lock:
            # Get existing config or create new
            config = self._configs.get(source, RateLimitConfig())

            if requests_per_second is not None:
                config.requests_per_second = requests_per_second
            elif requests_per_minute is not None:
                config.requests_per_second = requests_per_minute / 60.0

            if burst_size is not None:
                config.burst_size = burst_size

            self._configs[source] = config

            # Recreate bucket with new config
            if source in self._buckets:
                del self._buckets[source]

        logger.info(
            f"Rate limit set for {source}: {config.requests_per_second} req/s, "
            f"burst={config.burst_size}"
        )

    def acquire(
        self,
        source: str,
        tokens: int = 1,
        block: bool = True,
        timeout: float | None = None,
    ) -> bool:
        """
        Acquire permission to make a request.

        This method should be called before making a request to a data source.
        It will block (if configured) until the rate limit allows the request.

        Args:
            source: The data source name.
            tokens: Number of tokens to acquire (usually 1).
            block: Whether to block until tokens are available.
            timeout: Maximum time to wait.

        Returns:
            True if permission was granted, False if timed out or non-blocking.
        """
        bucket = self._get_bucket(source)
        result = bucket.acquire(tokens, block, timeout)

        if result:
            logger.debug(f"Rate limit acquired for {source}")
        else:
            logger.warning(f"Rate limit not acquired for {source} (timeout/non-blocking)")

        return result

    def get_available(self, source: str) -> float:
        """
        Get the number of available tokens for a source.

        Args:
            source: The data source name.

        Returns:
            Number of available tokens.
        """
        bucket = self._get_bucket(source)
        return bucket.available

    def get_limits(self) -> dict[str, dict[str, Any]]:
        """
        Get all configured rate limits.

        Returns:
            Dictionary mapping source names to their rate limit configs.
        """
        with self._lock:
            result = {}
            for source, config in self._configs.items():
                result[source] = {
                    "requests_per_second": config.requests_per_second,
                    "burst_size": config.burst_size,
                }
            # Include defaults for sources not explicitly configured
            for source, config in self._default_limits.items():
                if source not in result:
                    result[source] = {
                        "requests_per_second": config.requests_per_second,
                        "burst_size": config.burst_size,
                        "default": True,
                    }
            return result

    def reset(self, source: str | None = None) -> None:
        """
        Reset rate limit state.

        Args:
            source: Source to reset, or None to reset all.
        """
        with self._lock:
            if source:
                if source in self._buckets:
                    del self._buckets[source]
            else:
                self._buckets.clear()


# Global rate limiter instance
rate_limiter = RateLimiter()
