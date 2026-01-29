"""
Type definitions for FinVista.

This module defines type aliases, TypedDicts, and Protocol classes
used throughout the library for type safety and documentation.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date, datetime
from enum import Enum
from typing import (
    Any,
    Literal,
    Protocol,
    TypedDict,
    TypeVar,
    Union,
)

import pandas as pd

# =============================================================================
# Type Variables
# =============================================================================

T = TypeVar("T")
DataFrameT = TypeVar("DataFrameT", bound=pd.DataFrame)

# =============================================================================
# Basic Type Aliases
# =============================================================================

# Date types that can be accepted as input
DateLike = Union[str, date, datetime]

# JSON-serializable types
JsonValue = Union[str, int, float, bool, None, list["JsonValue"], dict[str, "JsonValue"]]
JsonDict = dict[str, JsonValue]

# =============================================================================
# Literal Types for Parameters
# =============================================================================

# Market codes
MarketCode = Literal["cn", "us", "hk", "eu", "jp", "global"]

# Asset types
AssetType = Literal[
    "stock", "fund", "bond", "futures", "option", "forex", "crypto", "index", "etf"
]

# Price adjustment types
AdjustType = Literal["none", "qfq", "hfq"]  # none/forward/backward

# Data frequency
Frequency = Literal[
    "1m", "5m", "15m", "30m", "60m", "daily", "weekly", "monthly", "quarterly", "yearly"
]

# Data source names
SourceName = Literal["eastmoney", "sina", "tencent", "yahoo", "fred", "alphavantage"]

# Return format types
ReturnFormat = Literal["dataframe", "dict", "json"]


# =============================================================================
# Enums
# =============================================================================


class SourceStatus(Enum):
    """Data source health status."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CIRCUIT_OPEN = "circuit_open"


class MarketType(Enum):
    """Market type enumeration."""

    MAIN = "main"  # Main board
    STAR = "star"  # STAR Market (科创板)
    GEM = "gem"  # ChiNext (创业板)
    BSE = "bse"  # Beijing Stock Exchange
    ALL = "all"


# =============================================================================
# TypedDict Definitions
# =============================================================================


class StockQuote(TypedDict):
    """Real-time stock quote data structure."""

    symbol: str
    name: str
    price: float
    change: float
    change_pct: float
    open: float
    high: float
    low: float
    pre_close: float
    volume: int
    amount: float
    timestamp: datetime


class OHLCV(TypedDict):
    """OHLCV (candlestick) data structure."""

    date: date
    open: float
    high: float
    low: float
    close: float
    volume: int
    amount: float | None


class StockInfo(TypedDict):
    """Basic stock information."""

    symbol: str
    name: str
    market: str
    industry: str | None
    list_date: date | None
    total_shares: int | None
    float_shares: int | None


class FundInfo(TypedDict):
    """Fund information structure."""

    symbol: str
    name: str
    fund_type: str
    manager: str | None
    custodian: str | None
    inception_date: date | None
    nav: float | None
    nav_date: date | None


class MacroIndicator(TypedDict):
    """Macroeconomic indicator data structure."""

    date: date
    actual: float | None
    forecast: float | None
    previous: float | None


class SourceHealth(TypedDict):
    """Data source health information."""

    status: str
    failure_count: int
    success_count: int
    avg_response_time: float
    last_success_time: float | None
    last_failure_time: float | None
    circuit_open_until: float | None


class HealthReport(TypedDict):
    """Health report for a data type."""

    sources: dict[str, SourceHealth]


# =============================================================================
# Protocol Definitions
# =============================================================================


class DataFetcher(Protocol):
    """
    Protocol for data fetcher functions.

    All data fetcher implementations should conform to this protocol
    to ensure consistent behavior across different data sources.
    """

    def __call__(self, **kwargs: Any) -> pd.DataFrame:
        """
        Fetch data from the source.

        Args:
            **kwargs: Fetcher-specific parameters.

        Returns:
            DataFrame containing the fetched data.
        """
        ...


class DataAdapter(Protocol):
    """
    Protocol for data source adapters.

    Adapters handle the specifics of fetching data from a particular
    source and normalizing it to a standard format.
    """

    @property
    def name(self) -> str:
        """Unique name identifying this adapter."""
        ...

    @property
    def base_url(self) -> str:
        """Base URL for API requests."""
        ...

    def fetch(self, endpoint: str, **kwargs: Any) -> pd.DataFrame:
        """
        Fetch data from a specific endpoint.

        Args:
            endpoint: API endpoint to fetch from.
            **kwargs: Endpoint-specific parameters.

        Returns:
            DataFrame containing the fetched data.
        """
        ...

    def is_available(self) -> bool:
        """
        Check if this adapter is currently available.

        Returns:
            True if the adapter can be used, False otherwise.
        """
        ...


class CacheBackend(Protocol):
    """
    Protocol for cache backend implementations.

    Cache backends provide storage and retrieval of cached data
    with optional TTL (time-to-live) support.
    """

    def get(self, key: str) -> Any | None:
        """
        Retrieve a value from the cache.

        Args:
            key: Cache key.

        Returns:
            Cached value or None if not found/expired.
        """
        ...

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """
        Store a value in the cache.

        Args:
            key: Cache key.
            value: Value to cache.
            ttl: Time-to-live in seconds (None for default).
        """
        ...

    def delete(self, key: str) -> None:
        """
        Remove a value from the cache.

        Args:
            key: Cache key.
        """
        ...

    def clear(self) -> None:
        """Clear all cached values."""
        ...


# =============================================================================
# Callback Type Aliases
# =============================================================================

# Fetcher function type
FetcherFunc = Callable[..., pd.DataFrame]

# Progress callback type
ProgressCallback = Callable[[int, int, str], None]  # current, total, message

# Error callback type
ErrorCallback = Callable[[Exception, str], None]  # error, source_name


# =============================================================================
# Result Types
# =============================================================================


class FetchResult(TypedDict):
    """Result of a data fetch operation."""

    data: pd.DataFrame
    source: str
    elapsed_time: float
    from_cache: bool


class ValidationResult(TypedDict):
    """Result of parameter validation."""

    valid: bool
    errors: list[str]
    warnings: list[str]
    normalized_params: dict[str, Any]
