"""
Cache management for FinVista.

This module provides caching functionality to reduce redundant API calls
and improve performance. It supports multiple backends (memory, disk, redis)
and includes a decorator for easy function caching.

Example:
    >>> from finvista._fetchers.cache import cached
    >>> @cached(ttl=60)
    ... def fetch_data(symbol: str) -> pd.DataFrame:
    ...     return expensive_api_call(symbol)
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from collections import OrderedDict
from collections.abc import Callable
from functools import wraps
from typing import Any, ParamSpec, TypeVar

from finvista._core.config import config
from finvista._core.types import CacheBackend

logger = logging.getLogger(__name__)

P = ParamSpec("P")
T = TypeVar("T")


class MemoryCache:
    """
    In-memory LRU cache implementation.

    This cache stores values in memory with optional TTL (time-to-live)
    and automatically evicts least recently used items when full.

    Attributes:
        max_size: Maximum number of items to cache.

    Example:
        >>> cache = MemoryCache(max_size=100)
        >>> cache.set("key", "value", ttl=60)
        >>> cache.get("key")
        'value'
    """

    def __init__(self, max_size: int = 1000) -> None:
        """
        Initialize the memory cache.

        Args:
            max_size: Maximum number of items to store.
        """
        self._cache: OrderedDict[str, tuple[Any, float | None]] = OrderedDict()
        self._max_size = max_size

    def get(self, key: str) -> Any | None:
        """
        Retrieve a value from the cache.

        Args:
            key: The cache key.

        Returns:
            The cached value, or None if not found or expired.
        """
        if key not in self._cache:
            return None

        value, expire_at = self._cache[key]

        # Check expiration
        if expire_at is not None and time.time() > expire_at:
            del self._cache[key]
            logger.debug(f"Cache key expired: {key}")
            return None

        # Move to end (most recently used)
        self._cache.move_to_end(key)
        logger.debug(f"Cache hit: {key}")
        return value

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """
        Store a value in the cache.

        Args:
            key: The cache key.
            value: The value to cache.
            ttl: Time-to-live in seconds (None for no expiration).
        """
        expire_at = time.time() + ttl if ttl else None

        # Evict oldest items if at capacity
        while len(self._cache) >= self._max_size:
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
            logger.debug(f"Cache evicted: {oldest_key}")

        self._cache[key] = (value, expire_at)
        self._cache.move_to_end(key)
        logger.debug(f"Cache set: {key} (ttl={ttl}s)")

    def delete(self, key: str) -> None:
        """
        Remove a value from the cache.

        Args:
            key: The cache key.
        """
        if key in self._cache:
            del self._cache[key]
            logger.debug(f"Cache deleted: {key}")

    def clear(self) -> None:
        """Clear all cached values."""
        self._cache.clear()
        logger.debug("Cache cleared")

    def __len__(self) -> int:
        """Return the number of cached items."""
        return len(self._cache)

    def __contains__(self, key: str) -> bool:
        """Check if a key exists and is not expired."""
        return self.get(key) is not None

    def stats(self) -> dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics.
        """
        # Count non-expired items
        current_time = time.time()
        valid_count = sum(
            1
            for _, (__, expire_at) in self._cache.items()
            if expire_at is None or current_time <= expire_at
        )

        return {
            "size": len(self._cache),
            "valid_items": valid_count,
            "max_size": self._max_size,
        }


class CacheManager:
    """
    Cache manager supporting multiple backends.

    This class provides a unified interface for caching with support
    for different backends (memory, disk, redis) based on configuration.

    Example:
        >>> manager = CacheManager()
        >>> manager.set("key", "value", ttl=60)
        >>> manager.get("key")
        'value'
    """

    def __init__(self) -> None:
        """Initialize the cache manager."""
        self._backends: dict[str, CacheBackend] = {
            "memory": MemoryCache(max_size=config.cache.max_size),
        }

    @property
    def backend(self) -> CacheBackend:
        """
        Get the current cache backend.

        Returns:
            The configured cache backend.
        """
        backend_name = config.cache.backend
        if backend_name not in self._backends:
            logger.warning(f"Unknown cache backend: {backend_name}, using memory")
            backend_name = "memory"
        return self._backends[backend_name]

    def get(self, key: str) -> Any | None:
        """
        Retrieve a value from the cache.

        Args:
            key: The cache key.

        Returns:
            The cached value, or None if not found.
        """
        if not config.cache.enabled:
            return None
        return self.backend.get(key)

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """
        Store a value in the cache.

        Args:
            key: The cache key.
            value: The value to cache.
            ttl: Time-to-live in seconds.
        """
        if not config.cache.enabled:
            return
        cache_ttl = ttl if ttl is not None else config.cache.ttl
        self.backend.set(key, value, cache_ttl)

    def delete(self, key: str) -> None:
        """
        Remove a value from the cache.

        Args:
            key: The cache key.
        """
        self.backend.delete(key)

    def clear(self) -> None:
        """Clear all cached values."""
        self.backend.clear()

    def _make_key(self, func_name: str, args: tuple[Any, ...], kwargs: dict[str, Any]) -> str:
        """
        Generate a cache key from function name and arguments.

        Args:
            func_name: The function name.
            args: Positional arguments.
            kwargs: Keyword arguments.

        Returns:
            A unique cache key string.
        """
        key_data = {
            "func": func_name,
            "args": [self._serialize_arg(arg) for arg in args],
            "kwargs": {k: self._serialize_arg(v) for k, v in sorted(kwargs.items())},
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_str.encode()).hexdigest()

    def _serialize_arg(self, arg: Any) -> Any:
        """
        Serialize an argument for cache key generation.

        Args:
            arg: The argument to serialize.

        Returns:
            A JSON-serializable representation.
        """
        if hasattr(arg, "to_dict"):
            return arg.to_dict()
        if hasattr(arg, "__dict__"):
            return str(arg)
        return arg

    def cached(
        self,
        ttl: int | None = None,
        key_prefix: str = "",
    ) -> Callable[[Callable[P, T]], Callable[P, T]]:
        """
        Decorator for caching function results.

        Args:
            ttl: Cache time-to-live in seconds.
            key_prefix: Optional prefix for cache keys.

        Returns:
            A decorator function.

        Example:
            >>> @cache_manager.cached(ttl=60)
            ... def fetch_data(symbol: str) -> pd.DataFrame:
            ...     return api.get(symbol)
        """

        def decorator(func: Callable[P, T]) -> Callable[P, T]:
            @wraps(func)
            def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
                # Check if caching is enabled
                if not config.cache.enabled:
                    return func(*args, **kwargs)

                # Generate cache key
                cache_key = key_prefix + self._make_key(func.__name__, args, kwargs)

                # Try to get from cache
                cached_value = self.get(cache_key)
                if cached_value is not None:
                    logger.debug(f"Cache hit for {func.__name__}")
                    return cached_value  # type: ignore[no-any-return]

                # Execute function and cache result
                result = func(*args, **kwargs)
                cache_ttl = ttl if ttl is not None else config.cache.ttl
                self.set(cache_key, result, cache_ttl)
                logger.debug(f"Cached result for {func.__name__} (ttl={cache_ttl}s)")

                return result

            return wrapper

        return decorator


# Global cache manager instance
cache_manager = CacheManager()

# Convenience decorator
cached = cache_manager.cached
