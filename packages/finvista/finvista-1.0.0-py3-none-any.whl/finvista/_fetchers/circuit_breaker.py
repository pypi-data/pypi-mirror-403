"""
Circuit breaker pattern implementation for FinVista.

This module implements the circuit breaker pattern to prevent cascading
failures when data sources become unavailable. It automatically disables
failing sources and periodically tests them for recovery.

Circuit States:
    CLOSED: Normal operation, requests pass through
    OPEN: Circuit tripped, requests fail immediately
    HALF_OPEN: Testing recovery, limited requests allowed

Example:
    >>> from finvista._fetchers.circuit_breaker import CircuitBreaker
    >>> breaker = CircuitBreaker("eastmoney")
    >>> if breaker.allow_request():
    ...     try:
    ...         result = make_request()
    ...         breaker.record_success()
    ...     except Exception as e:
    ...         breaker.record_failure(e)
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from finvista._core.config import config

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Circuit tripped, failing fast
    HALF_OPEN = "half_open"  # Testing for recovery


@dataclass
class CircuitStats:
    """
    Statistics for a circuit breaker.

    Attributes:
        failure_count: Consecutive failures.
        success_count: Consecutive successes (in half-open state).
        total_failures: Total failures since last reset.
        total_successes: Total successes since last reset.
        last_failure_time: Timestamp of last failure.
        last_success_time: Timestamp of last success.
        last_state_change: Timestamp of last state change.
        avg_response_time: Exponential moving average of response times.
    """

    failure_count: int = 0
    success_count: int = 0
    total_failures: int = 0
    total_successes: int = 0
    last_failure_time: float | None = None
    last_success_time: float | None = None
    last_state_change: float = field(default_factory=time.time)
    avg_response_time: float = 0.0


class CircuitBreaker:
    """
    Circuit breaker implementation for a single data source.

    The circuit breaker monitors failures and automatically "trips"
    (opens) when failures exceed a threshold. After a timeout period,
    it enters a half-open state to test if the source has recovered.

    Attributes:
        name: Name of the data source.
        state: Current circuit state.
        stats: Circuit statistics.

    Example:
        >>> breaker = CircuitBreaker("eastmoney")
        >>> if breaker.allow_request():
        ...     try:
        ...         data = fetch_from_source()
        ...         breaker.record_success(response_time=0.5)
        ...     except Exception as e:
        ...         breaker.record_failure(e)
        ... else:
        ...     print("Circuit is open, skipping source")
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int | None = None,
        success_threshold: int | None = None,
        timeout: float | None = None,
    ) -> None:
        """
        Initialize the circuit breaker.

        Args:
            name: Name of the data source.
            failure_threshold: Failures before opening circuit.
            success_threshold: Successes to close circuit from half-open.
            timeout: Seconds before attempting recovery.
        """
        self.name = name
        self._state = CircuitState.CLOSED
        self._stats = CircuitStats()
        self._lock = threading.Lock()
        self._open_until: float | None = None

        # Use provided values or fall back to config
        self._failure_threshold = failure_threshold
        self._success_threshold = success_threshold
        self._timeout = timeout

    @property
    def failure_threshold(self) -> int:
        """Get the failure threshold."""
        if self._failure_threshold is not None:
            return self._failure_threshold
        return config.failover.failure_threshold

    @property
    def success_threshold(self) -> int:
        """Get the success threshold for recovery."""
        if self._success_threshold is not None:
            return self._success_threshold
        return config.failover.success_threshold

    @property
    def timeout(self) -> float:
        """Get the circuit timeout."""
        if self._timeout is not None:
            return self._timeout
        return config.failover.circuit_timeout

    @property
    def state(self) -> CircuitState:
        """Get the current circuit state."""
        with self._lock:
            self._check_state_transition()
            return self._state

    @property
    def stats(self) -> CircuitStats:
        """Get circuit statistics."""
        with self._lock:
            return CircuitStats(
                failure_count=self._stats.failure_count,
                success_count=self._stats.success_count,
                total_failures=self._stats.total_failures,
                total_successes=self._stats.total_successes,
                last_failure_time=self._stats.last_failure_time,
                last_success_time=self._stats.last_success_time,
                last_state_change=self._stats.last_state_change,
                avg_response_time=self._stats.avg_response_time,
            )

    def _check_state_transition(self) -> None:
        """Check and perform automatic state transitions."""
        if self._state == CircuitState.OPEN and self._open_until:
            if time.time() >= self._open_until:
                self._transition_to(CircuitState.HALF_OPEN)

    def _transition_to(self, new_state: CircuitState) -> None:
        """
        Transition to a new state.

        Args:
            new_state: The state to transition to.
        """
        old_state = self._state
        self._state = new_state
        self._stats.last_state_change = time.time()

        if new_state == CircuitState.OPEN:
            self._open_until = time.time() + self.timeout
        else:
            self._open_until = None

        if new_state == CircuitState.HALF_OPEN:
            self._stats.success_count = 0

        logger.info(f"Circuit '{self.name}' transitioned from {old_state.value} to {new_state.value}")

    def allow_request(self) -> bool:
        """
        Check if a request is allowed.

        Returns:
            True if the request should proceed, False otherwise.
        """
        with self._lock:
            self._check_state_transition()

            if self._state == CircuitState.CLOSED:
                return True
            elif self._state == CircuitState.HALF_OPEN:
                # Allow limited requests in half-open state
                return True
            else:
                # Circuit is open
                return False

    def record_success(self, response_time: float = 0.0) -> None:
        """
        Record a successful request.

        Args:
            response_time: Time taken for the request in seconds.
        """
        with self._lock:
            self._stats.success_count += 1
            self._stats.total_successes += 1
            self._stats.failure_count = 0
            self._stats.last_success_time = time.time()

            # Update exponential moving average of response time
            alpha = 0.2
            self._stats.avg_response_time = (
                alpha * response_time + (1 - alpha) * self._stats.avg_response_time
            )

            if self._state == CircuitState.HALF_OPEN:
                if self._stats.success_count >= self.success_threshold:
                    self._transition_to(CircuitState.CLOSED)
                    logger.info(f"Circuit '{self.name}' recovered and closed")

    def record_failure(self, error: Exception | None = None) -> None:
        """
        Record a failed request.

        Args:
            error: The exception that caused the failure.
        """
        with self._lock:
            self._stats.failure_count += 1
            self._stats.total_failures += 1
            self._stats.success_count = 0
            self._stats.last_failure_time = time.time()

            error_msg = str(error) if error else "Unknown error"
            logger.warning(
                f"Circuit '{self.name}' failure #{self._stats.failure_count}: {error_msg}"
            )

            if self._state == CircuitState.HALF_OPEN:
                # Immediately trip back to open on failure in half-open state
                self._transition_to(CircuitState.OPEN)
                logger.warning(f"Circuit '{self.name}' tripped back to open")
            elif self._state == CircuitState.CLOSED:
                if self._stats.failure_count >= self.failure_threshold:
                    self._transition_to(CircuitState.OPEN)
                    logger.error(
                        f"Circuit '{self.name}' opened after {self._stats.failure_count} failures"
                    )

    def reset(self) -> None:
        """Reset the circuit breaker to closed state."""
        with self._lock:
            self._state = CircuitState.CLOSED
            self._stats = CircuitStats()
            self._open_until = None
            logger.info(f"Circuit '{self.name}' reset to closed state")

    def get_status(self) -> dict[str, Any]:
        """
        Get the current status of the circuit breaker.

        Returns:
            Dictionary with status information.
        """
        with self._lock:
            self._check_state_transition()
            status: dict[str, Any] = {
                "name": self.name,
                "state": self._state.value,
                "failure_count": self._stats.failure_count,
                "success_count": self._stats.success_count,
                "total_failures": self._stats.total_failures,
                "total_successes": self._stats.total_successes,
                "avg_response_time": round(self._stats.avg_response_time, 3),
                "last_failure_time": self._stats.last_failure_time,
                "last_success_time": self._stats.last_success_time,
            }

            if self._state == CircuitState.OPEN and self._open_until:
                status["open_until"] = self._open_until
                status["time_until_half_open"] = max(0, self._open_until - time.time())

            return status


class CircuitBreakerRegistry:
    """
    Registry for managing multiple circuit breakers.

    This class provides a centralized way to manage circuit breakers
    for different data sources and data types.

    Example:
        >>> registry = CircuitBreakerRegistry()
        >>> breaker = registry.get("cn_stock_daily", "eastmoney")
        >>> if breaker.allow_request():
        ...     # Make request
    """

    def __init__(self) -> None:
        """Initialize the registry."""
        self._breakers: dict[str, dict[str, CircuitBreaker]] = {}
        self._lock = threading.Lock()

    def get(self, data_type: str, source_name: str) -> CircuitBreaker:
        """
        Get or create a circuit breaker.

        Args:
            data_type: The data type (e.g., 'cn_stock_daily').
            source_name: The data source name.

        Returns:
            The circuit breaker for the specified source.
        """
        with self._lock:
            if data_type not in self._breakers:
                self._breakers[data_type] = {}

            if source_name not in self._breakers[data_type]:
                self._breakers[data_type][source_name] = CircuitBreaker(
                    name=f"{data_type}:{source_name}"
                )

            return self._breakers[data_type][source_name]

    def reset(self, data_type: str | None = None, source_name: str | None = None) -> None:
        """
        Reset circuit breakers.

        Args:
            data_type: Data type to reset, or None for all.
            source_name: Source to reset, or None for all sources of data_type.
        """
        with self._lock:
            if data_type is None:
                # Reset all
                for dt in self._breakers.values():
                    for breaker in dt.values():
                        breaker.reset()
            elif source_name is None:
                # Reset all sources for a data type
                if data_type in self._breakers:
                    for breaker in self._breakers[data_type].values():
                        breaker.reset()
            else:
                # Reset specific breaker
                if data_type in self._breakers and source_name in self._breakers[data_type]:
                    self._breakers[data_type][source_name].reset()

    def get_all_status(self) -> dict[str, dict[str, dict[str, Any]]]:
        """
        Get status of all circuit breakers.

        Returns:
            Nested dictionary of data_type -> source -> status.
        """
        with self._lock:
            result: dict[str, dict[str, dict[str, Any]]] = {}
            for data_type, sources in self._breakers.items():
                result[data_type] = {}
                for source_name, breaker in sources.items():
                    result[data_type][source_name] = breaker.get_status()
            return result


# Global circuit breaker registry
circuit_registry = CircuitBreakerRegistry()
