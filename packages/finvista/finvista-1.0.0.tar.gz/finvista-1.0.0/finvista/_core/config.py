"""
Configuration management for FinVista.

This module provides a centralized, thread-safe configuration system
for managing library settings including HTTP options, caching, logging,
and failover behavior.

Example:
    >>> import finvista as fv
    >>> fv.set_timeout(60)
    >>> fv.set_proxies({"http": "http://127.0.0.1:7890"})
    >>> fv.set_cache(enabled=True, ttl=300)
"""

from __future__ import annotations

import threading
from collections.abc import Generator
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any

from finvista._core.exceptions import ConfigError


@dataclass
class CacheConfig:
    """
    Cache configuration settings.

    Attributes:
        enabled: Whether caching is enabled.
        backend: Cache backend type ('memory', 'redis', 'disk').
        ttl: Default time-to-live in seconds.
        max_size: Maximum number of cached items (for memory backend).
    """

    enabled: bool = True
    backend: str = "memory"
    ttl: int = 300
    max_size: int = 1000

    def validate(self) -> None:
        """Validate cache configuration."""
        if self.ttl < 0:
            raise ConfigError("Cache TTL must be non-negative", config_key="cache.ttl")
        if self.max_size < 1:
            raise ConfigError(
                "Cache max_size must be positive", config_key="cache.max_size"
            )
        if self.backend not in ("memory", "redis", "disk"):
            raise ConfigError(
                f"Invalid cache backend: {self.backend}", config_key="cache.backend"
            )


@dataclass
class HttpConfig:
    """
    HTTP client configuration settings.

    Attributes:
        timeout: Request timeout in seconds.
        max_retries: Maximum number of retry attempts.
        retry_delay: Initial delay between retries in seconds.
        retry_backoff: Backoff multiplier for retry delays.
        proxies: Proxy configuration dictionary.
        verify_ssl: Whether to verify SSL certificates.
        user_agent: User-Agent header value.
    """

    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    retry_backoff: float = 2.0
    proxies: dict[str, str] | None = None
    verify_ssl: bool = True
    user_agent: str = "FinVista/0.1.0 (https://github.com/finvista/finvista)"

    def validate(self) -> None:
        """Validate HTTP configuration."""
        if self.timeout < 1:
            raise ConfigError(
                "Timeout must be a positive integer", config_key="http.timeout"
            )
        if self.max_retries < 0:
            raise ConfigError(
                "max_retries must be non-negative", config_key="http.max_retries"
            )
        if self.retry_delay < 0:
            raise ConfigError(
                "retry_delay must be non-negative", config_key="http.retry_delay"
            )
        if self.retry_backoff < 1:
            raise ConfigError(
                "retry_backoff must be >= 1", config_key="http.retry_backoff"
            )


@dataclass
class LogConfig:
    """
    Logging configuration settings.

    Attributes:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        format: Log message format string.
        file: Optional file path for log output.
    """

    level: str = "WARNING"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: str | None = None

    def validate(self) -> None:
        """Validate logging configuration."""
        valid_levels = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
        if self.level.upper() not in valid_levels:
            raise ConfigError(
                f"Invalid log level: {self.level}. Must be one of {valid_levels}",
                config_key="log.level",
            )


@dataclass
class FailoverConfig:
    """
    Data source failover configuration settings.

    Attributes:
        enabled: Whether automatic failover is enabled.
        failure_threshold: Consecutive failures before circuit opens.
        circuit_timeout: Seconds before circuit attempts to close.
        success_threshold: Consecutive successes to close circuit.
        max_retries_per_source: Max retries for each source before switching.
    """

    enabled: bool = True
    failure_threshold: int = 5
    circuit_timeout: float = 60.0
    success_threshold: int = 3
    max_retries_per_source: int = 2

    def validate(self) -> None:
        """Validate failover configuration."""
        if self.failure_threshold < 1:
            raise ConfigError(
                "failure_threshold must be positive",
                config_key="failover.failure_threshold",
            )
        if self.circuit_timeout < 1:
            raise ConfigError(
                "circuit_timeout must be positive",
                config_key="failover.circuit_timeout",
            )
        if self.success_threshold < 1:
            raise ConfigError(
                "success_threshold must be positive",
                config_key="failover.success_threshold",
            )


@dataclass
class FinVistaConfig:
    """
    Main configuration container for FinVista.

    This class holds all configuration settings organized into
    logical groups (cache, http, log, failover).

    Attributes:
        cache: Cache-related settings.
        http: HTTP client settings.
        log: Logging settings.
        failover: Data source failover settings.
        data_source_priority: Default priority order for data sources.
        return_format: Default return format ('dataframe', 'dict', 'json').
        show_progress: Whether to show progress bars for long operations.
    """

    cache: CacheConfig = field(default_factory=CacheConfig)
    http: HttpConfig = field(default_factory=HttpConfig)
    log: LogConfig = field(default_factory=LogConfig)
    failover: FailoverConfig = field(default_factory=FailoverConfig)

    data_source_priority: list[str] = field(
        default_factory=lambda: ["eastmoney", "sina", "tencent"]
    )
    return_format: str = "dataframe"
    show_progress: bool = True

    def validate(self) -> None:
        """Validate all configuration settings."""
        self.cache.validate()
        self.http.validate()
        self.log.validate()
        self.failover.validate()

        if self.return_format not in ("dataframe", "dict", "json"):
            raise ConfigError(
                f"Invalid return_format: {self.return_format}",
                config_key="return_format",
            )


class ConfigManager:
    """
    Thread-safe configuration manager (singleton pattern).

    This class manages the global configuration state and provides
    methods for updating settings. It supports thread-local configuration
    overrides through context managers.

    Example:
        >>> from finvista._core.config import config
        >>> config.set(http={"timeout": 60})
        >>> with config.context(http={"timeout": 10}):
        ...     # Uses timeout=10 in this block
        ...     pass
        >>> # Back to timeout=60

    Note:
        This class implements the singleton pattern. Use the global
        `config` instance instead of creating new instances.
    """

    _instance: ConfigManager | None = None
    _lock = threading.Lock()
    _config: FinVistaConfig
    _local: threading.local
    _source_priorities: dict[str, list[str]]

    def __new__(cls) -> ConfigManager:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    instance = super().__new__(cls)
                    instance._config = FinVistaConfig()
                    instance._local = threading.local()
                    instance._source_priorities = {}
                    cls._instance = instance
        return cls._instance

    @property
    def config(self) -> FinVistaConfig:
        """
        Get the current configuration.

        Returns thread-local config if set, otherwise global config.
        """
        return getattr(self._local, "config", self._config)

    # Convenience properties for direct access
    @property
    def cache(self) -> CacheConfig:
        """Get cache configuration."""
        return self.config.cache

    @property
    def http(self) -> HttpConfig:
        """Get HTTP configuration."""
        return self.config.http

    @property
    def log(self) -> LogConfig:
        """Get log configuration."""
        return self.config.log

    @property
    def failover(self) -> FailoverConfig:
        """Get failover configuration."""
        return self.config.failover

    def set(self, **kwargs: Any) -> None:
        """
        Update configuration settings.

        Args:
            **kwargs: Configuration values to update. Can be nested
                     dictionaries for sub-configurations.

        Example:
            >>> config.set(http={"timeout": 60, "max_retries": 5})
        """
        for key, value in kwargs.items():
            if hasattr(self._config, key):
                current = getattr(self._config, key)
                if isinstance(value, dict) and hasattr(current, "__dataclass_fields__"):
                    # Update nested dataclass
                    for k, v in value.items():
                        if hasattr(current, k):
                            setattr(current, k, v)
                        else:
                            raise ConfigError(
                                f"Unknown config option: {key}.{k}",
                                config_key=f"{key}.{k}",
                            )
                else:
                    setattr(self._config, key, value)
            else:
                raise ConfigError(f"Unknown config option: {key}", config_key=key)

        # Validate after update
        self._config.validate()

    def reset(self) -> None:
        """Reset all configuration to defaults."""
        self._config = FinVistaConfig()
        self._source_priorities = {}

    @contextmanager
    def context(self, **kwargs: Any) -> Generator[FinVistaConfig, None, None]:
        """
        Create a temporary configuration context.

        Configuration changes made within this context are thread-local
        and automatically reverted when the context exits.

        Args:
            **kwargs: Configuration overrides for this context.

        Yields:
            The temporary configuration object.

        Example:
            >>> with config.context(http={"timeout": 10}):
            ...     # Uses timeout=10 here
            ...     data = fetch_data()
            >>> # Timeout reverts to original value
        """
        # Create a deep copy of current config
        self._local.config = deepcopy(self.config)

        try:
            # Apply overrides
            for key, value in kwargs.items():
                current = getattr(self._local.config, key, None)
                if current is None:
                    raise ConfigError(f"Unknown config option: {key}")
                if isinstance(value, dict) and hasattr(current, "__dataclass_fields__"):
                    for k, v in value.items():
                        setattr(current, k, v)
                else:
                    setattr(self._local.config, key, value)

            self._local.config.validate()
            yield self._local.config
        finally:
            # Remove thread-local override
            if hasattr(self._local, "config"):
                del self._local.config

    def get_source_priority(self, data_type: str) -> list[str]:
        """
        Get the data source priority for a specific data type.

        Args:
            data_type: The data type (e.g., 'cn_stock_daily').

        Returns:
            Ordered list of data source names.
        """
        return self._source_priorities.get(
            data_type, self.config.data_source_priority.copy()
        )

    def set_source_priority(self, data_type: str, sources: list[str]) -> None:
        """
        Set the data source priority for a specific data type.

        Args:
            data_type: The data type (e.g., 'cn_stock_daily').
            sources: Ordered list of data source names.
        """
        self._source_priorities[data_type] = sources.copy()


# Global configuration instance
config = ConfigManager()


# =============================================================================
# Convenience functions
# =============================================================================


def set_proxies(proxies: dict[str, str] | None) -> None:
    """
    Set HTTP proxy configuration.

    Args:
        proxies: Proxy configuration dictionary, e.g.,
                {"http": "http://127.0.0.1:7890", "https": "http://127.0.0.1:7890"}
                Pass None to disable proxies.

    Example:
        >>> import finvista as fv
        >>> fv.set_proxies({"http": "http://127.0.0.1:7890"})
    """
    config.config.http.proxies = proxies


def set_timeout(timeout: int) -> None:
    """
    Set HTTP request timeout.

    Args:
        timeout: Timeout in seconds (must be positive).

    Example:
        >>> import finvista as fv
        >>> fv.set_timeout(60)
    """
    if timeout < 1:
        raise ConfigError("Timeout must be a positive integer", config_key="timeout")
    config.config.http.timeout = timeout


def set_cache(
    enabled: bool = True,
    ttl: int | None = None,
    backend: str | None = None,
    max_size: int | None = None,
) -> None:
    """
    Configure caching behavior.

    Args:
        enabled: Whether to enable caching.
        ttl: Cache time-to-live in seconds.
        backend: Cache backend ('memory', 'redis', 'disk').
        max_size: Maximum cached items (for memory backend).

    Example:
        >>> import finvista as fv
        >>> fv.set_cache(enabled=True, ttl=600)
    """
    config.config.cache.enabled = enabled
    if ttl is not None:
        config.config.cache.ttl = ttl
    if backend is not None:
        config.config.cache.backend = backend
    if max_size is not None:
        config.config.cache.max_size = max_size

    config.config.cache.validate()


def get_source_health() -> dict[str, dict[str, Any]]:
    """
    Get health status of all data sources.

    This function is implemented in the source_manager module
    and re-exported here for convenience.

    Returns:
        Dictionary mapping data types to source health information.
    """
    # Import here to avoid circular imports
    from finvista._fetchers.source_manager import source_manager

    return source_manager.get_health_report()


def reset_source_circuit(data_type: str, source_name: str) -> None:
    """
    Reset the circuit breaker for a specific data source.

    Args:
        data_type: The data type (e.g., 'cn_stock_daily').
        source_name: The name of the data source.
    """
    # Import here to avoid circular imports
    from finvista._fetchers.source_manager import source_manager

    source_manager.reset_circuit(data_type, source_name)


def set_source_priority(data_type: str, sources: list[str]) -> None:
    """
    Set the priority order for data sources.

    Args:
        data_type: The data type (e.g., 'cn_stock_daily').
        sources: Ordered list of source names (first = highest priority).

    Example:
        >>> import finvista as fv
        >>> fv.set_source_priority("cn_stock_daily", ["sina", "eastmoney", "tencent"])
    """
    config.set_source_priority(data_type, sources)
