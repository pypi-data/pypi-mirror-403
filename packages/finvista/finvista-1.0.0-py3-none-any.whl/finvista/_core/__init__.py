"""Core infrastructure for FinVista."""

from finvista._core.config import config, set_cache, set_proxies, set_timeout
from finvista._core.exceptions import (
    AllSourcesFailedError,
    AllSourcesUnavailableError,
    APIError,
    ConfigError,
    DataError,
    DataNotFoundError,
    DataParsingError,
    DateRangeError,
    FinVistaError,
    NetworkError,
    RateLimitError,
    SourceError,
    SymbolNotFoundError,
    ValidationError,
)

__all__ = [
    # Config
    "config",
    "set_proxies",
    "set_timeout",
    "set_cache",
    # Exceptions
    "FinVistaError",
    "ConfigError",
    "NetworkError",
    "APIError",
    "RateLimitError",
    "DataError",
    "DataNotFoundError",
    "DataParsingError",
    "ValidationError",
    "SymbolNotFoundError",
    "DateRangeError",
    "SourceError",
    "AllSourcesUnavailableError",
    "AllSourcesFailedError",
]
