"""
Multi-source data manager for FinVista.

This module provides automatic failover between multiple data sources.
When a primary source fails, it automatically switches to backup sources
while tracking health and implementing circuit breaker patterns.

Example:
    >>> from finvista._fetchers.source_manager import source_manager
    >>> source_manager.register("cn_stock_daily", "eastmoney", fetcher_func, priority=0)
    >>> source_manager.register("cn_stock_daily", "sina", fetcher_func, priority=1)
    >>> data, source = source_manager.fetch_with_fallback("cn_stock_daily", symbol="000001")
"""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from finvista._core.config import config
from finvista._core.exceptions import (
    AllSourcesFailedError,
    AllSourcesUnavailableError,
)
from finvista._core.types import SourceStatus
from finvista._fetchers.circuit_breaker import circuit_registry
from finvista._fetchers.rate_limiter import rate_limiter

logger = logging.getLogger(__name__)


@dataclass
class SourceHealth:
    """
    Health information for a data source.

    Attributes:
        status: Current health status.
        failure_count: Consecutive failure count.
        success_count: Consecutive success count.
        last_failure_time: Timestamp of last failure.
        last_success_time: Timestamp of last success.
        avg_response_time: Average response time in seconds.
        circuit_open_until: When circuit will attempt to close.
    """

    status: SourceStatus = SourceStatus.HEALTHY
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: float | None = None
    last_success_time: float | None = None
    avg_response_time: float = 0.0
    circuit_open_until: float | None = None


@dataclass
class DataSource:
    """
    Data source definition.

    Attributes:
        name: Unique name identifying this source.
        fetcher: Function to fetch data from this source.
        priority: Priority level (lower = higher priority).
        enabled: Whether this source is enabled.
        health: Health information for this source.
    """

    name: str
    fetcher: Callable[..., pd.DataFrame]
    priority: int = 0
    enabled: bool = True
    health: SourceHealth = field(default_factory=SourceHealth)


class SourceManager:
    """
    Multi-source data manager with automatic failover.

    This class manages multiple data sources for each data type,
    automatically switching to backup sources when the primary fails.
    It integrates with circuit breakers and rate limiters to ensure
    robust data fetching.

    Attributes:
        sources: Registered data sources by data type.

    Example:
        >>> manager = SourceManager()
        >>> manager.register("cn_stock_daily", "eastmoney", fetch_eastmoney, priority=0)
        >>> manager.register("cn_stock_daily", "sina", fetch_sina, priority=1)
        >>> data, source_name = manager.fetch_with_fallback("cn_stock_daily", symbol="000001")
        >>> print(f"Data fetched from: {source_name}")
    """

    def __init__(self) -> None:
        """Initialize the source manager."""
        self._sources: dict[str, dict[str, DataSource]] = {}
        self._priority_order: dict[str, list[str]] = {}
        self._lock = threading.Lock()

    def register(
        self,
        data_type: str,
        name: str,
        fetcher: Callable[..., pd.DataFrame],
        priority: int = 0,
        enabled: bool = True,
    ) -> None:
        """
        Register a data source.

        Args:
            data_type: Type of data (e.g., 'cn_stock_daily').
            name: Unique name for this source.
            fetcher: Function to fetch data.
            priority: Priority level (lower = higher priority).
            enabled: Whether the source is enabled.

        Example:
            >>> def fetch_eastmoney(symbol: str, **kwargs) -> pd.DataFrame:
            ...     # Fetch implementation
            ...     pass
            >>> manager.register("cn_stock_daily", "eastmoney", fetch_eastmoney, priority=0)
        """
        with self._lock:
            if data_type not in self._sources:
                self._sources[data_type] = {}
                self._priority_order[data_type] = []

            self._sources[data_type][name] = DataSource(
                name=name,
                fetcher=fetcher,
                priority=priority,
                enabled=enabled,
            )

            # Update priority order
            self._update_priority_order(data_type)

            logger.info(f"Registered source '{name}' for '{data_type}' with priority {priority}")

    def _update_priority_order(self, data_type: str) -> None:
        """Update the priority order for a data type."""
        sources = self._sources.get(data_type, {})

        # Check for custom priority from config
        custom_priority = config.get_source_priority(data_type)

        if custom_priority:
            # Use custom order, but only include registered sources
            self._priority_order[data_type] = [
                name for name in custom_priority if name in sources
            ]
            # Add any registered sources not in custom priority
            for name in sources:
                if name not in self._priority_order[data_type]:
                    self._priority_order[data_type].append(name)
        else:
            # Sort by priority value
            self._priority_order[data_type] = sorted(
                sources.keys(), key=lambda x: sources[x].priority
            )

    def unregister(self, data_type: str, name: str) -> None:
        """
        Unregister a data source.

        Args:
            data_type: Type of data.
            name: Name of the source to unregister.
        """
        with self._lock:
            if data_type in self._sources and name in self._sources[data_type]:
                del self._sources[data_type][name]
                self._update_priority_order(data_type)
                logger.info(f"Unregistered source '{name}' for '{data_type}'")

    def set_enabled(self, data_type: str, name: str, enabled: bool) -> None:
        """
        Enable or disable a data source.

        Args:
            data_type: Type of data.
            name: Name of the source.
            enabled: Whether to enable the source.
        """
        with self._lock:
            if data_type in self._sources and name in self._sources[data_type]:
                self._sources[data_type][name].enabled = enabled
                logger.info(f"Source '{name}' for '{data_type}' {'enabled' if enabled else 'disabled'}")

    def get_available_sources(self, data_type: str) -> list[DataSource]:
        """
        Get list of available sources for a data type.

        This returns sources that are:
        - Registered and enabled
        - Not in circuit-open state

        Args:
            data_type: Type of data to fetch.

        Returns:
            List of available DataSource objects in priority order.
        """
        with self._lock:
            if data_type not in self._sources:
                return []

            available = []
            for name in self._priority_order.get(data_type, []):
                source = self._sources[data_type].get(name)
                if source is None or not source.enabled:
                    continue

                # Check circuit breaker
                breaker = circuit_registry.get(data_type, name)
                if breaker.allow_request():
                    available.append(source)
                else:
                    logger.debug(f"Source '{name}' for '{data_type}' skipped (circuit open)")

            return available

    def fetch_with_fallback(
        self,
        data_type: str,
        **kwargs: Any,
    ) -> tuple[pd.DataFrame, str]:
        """
        Fetch data with automatic failover to backup sources.

        This method tries each available source in priority order,
        automatically falling back to the next source if one fails.

        Args:
            data_type: Type of data to fetch.
            **kwargs: Parameters passed to the fetcher function.

        Returns:
            Tuple of (DataFrame, source_name) where source_name indicates
            which data source was actually used.

        Raises:
            AllSourcesUnavailableError: When no sources are available.
            AllSourcesFailedError: When all sources fail.

        Example:
            >>> df, source = manager.fetch_with_fallback(
            ...     "cn_stock_daily",
            ...     symbol="000001",
            ...     start_date="2024-01-01"
            ... )
            >>> print(f"Fetched from: {source}")
        """
        available_sources = self.get_available_sources(data_type)

        if not available_sources:
            raise AllSourcesUnavailableError(
                f"No available sources for data type: {data_type}",
                data_type=data_type,
            )

        last_error: Exception | None = None
        attempted_sources: list[str] = []

        for source in available_sources:
            attempted_sources.append(source.name)
            breaker = circuit_registry.get(data_type, source.name)

            try:
                # Acquire rate limit
                rate_limiter.acquire(source.name)

                # Fetch data
                start_time = time.time()
                data = source.fetcher(**kwargs)
                elapsed = time.time() - start_time

                # Record success
                breaker.record_success(response_time=elapsed)
                self._update_health(data_type, source.name, success=True, response_time=elapsed)

                logger.debug(f"Successfully fetched from '{source.name}' in {elapsed:.2f}s")

                # Add source metadata to DataFrame
                if isinstance(data, pd.DataFrame):
                    data.attrs["source"] = source.name
                    data.attrs["fetch_time"] = elapsed

                return data, source.name

            except Exception as e:
                # Record failure
                breaker.record_failure(e)
                self._update_health(data_type, source.name, success=False, error=e)

                logger.warning(f"Source '{source.name}' failed: {e}, trying next...")
                last_error = e
                continue

        raise AllSourcesFailedError(
            f"All sources failed for data type: {data_type}",
            data_type=data_type,
            last_error=last_error,
            attempted_sources=attempted_sources,
        )

    def _update_health(
        self,
        data_type: str,
        source_name: str,
        success: bool,
        response_time: float = 0.0,
        error: Exception | None = None,
    ) -> None:
        """Update health information for a source."""
        with self._lock:
            if data_type not in self._sources or source_name not in self._sources[data_type]:
                return

            health = self._sources[data_type][source_name].health
            now = time.time()

            if success:
                health.success_count += 1
                health.failure_count = 0
                health.last_success_time = now
                health.status = SourceStatus.HEALTHY

                # Update average response time (exponential moving average)
                alpha = 0.2
                health.avg_response_time = alpha * response_time + (1 - alpha) * health.avg_response_time
            else:
                health.failure_count += 1
                health.success_count = 0
                health.last_failure_time = now

                # Update status based on failure count
                if health.failure_count >= config.failover.failure_threshold:
                    health.status = SourceStatus.CIRCUIT_OPEN
                    health.circuit_open_until = now + config.failover.circuit_timeout
                elif health.failure_count >= 2:
                    health.status = SourceStatus.UNHEALTHY
                else:
                    health.status = SourceStatus.DEGRADED

    def reset_circuit(self, data_type: str, source_name: str) -> None:
        """
        Reset the circuit breaker for a source.

        Args:
            data_type: Type of data.
            source_name: Name of the source.
        """
        circuit_registry.reset(data_type, source_name)

        with self._lock:
            if data_type in self._sources and source_name in self._sources[data_type]:
                health = self._sources[data_type][source_name].health
                health.status = SourceStatus.HEALTHY
                health.failure_count = 0
                health.circuit_open_until = None

        logger.info(f"Circuit reset for '{source_name}' ({data_type})")

    def get_health_report(self) -> dict[str, dict[str, dict[str, Any]]]:
        """
        Get health report for all sources.

        Returns:
            Nested dictionary: data_type -> source_name -> health_info
        """
        with self._lock:
            report: dict[str, dict[str, dict[str, Any]]] = {}

            for data_type, sources in self._sources.items():
                report[data_type] = {}

                for name, source in sources.items():
                    health = source.health
                    breaker = circuit_registry.get(data_type, name)
                    breaker_status = breaker.get_status()

                    report[data_type][name] = {
                        "status": health.status.value,
                        "enabled": source.enabled,
                        "priority": source.priority,
                        "failure_count": health.failure_count,
                        "success_count": health.success_count,
                        "avg_response_time": round(health.avg_response_time, 3),
                        "last_success_time": health.last_success_time,
                        "last_failure_time": health.last_failure_time,
                        "circuit_state": breaker_status["state"],
                    }

                    if health.circuit_open_until:
                        report[data_type][name]["circuit_open_until"] = health.circuit_open_until
                        report[data_type][name]["time_until_recovery"] = max(
                            0, health.circuit_open_until - time.time()
                        )

            return report

    def get_sources(self, data_type: str) -> list[str]:
        """
        Get list of registered source names for a data type.

        Args:
            data_type: Type of data.

        Returns:
            List of source names in priority order.
        """
        with self._lock:
            return self._priority_order.get(data_type, []).copy()

    def set_priority(self, data_type: str, sources: list[str]) -> None:
        """
        Set custom priority order for sources.

        Args:
            data_type: Type of data.
            sources: Ordered list of source names.
        """
        config.set_source_priority(data_type, sources)
        with self._lock:
            self._update_priority_order(data_type)
        logger.info(f"Priority updated for '{data_type}': {sources}")


# Global source manager instance
source_manager = SourceManager()
