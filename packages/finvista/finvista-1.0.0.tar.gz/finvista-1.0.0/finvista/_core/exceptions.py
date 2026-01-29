"""
Exception hierarchy for FinVista.

This module defines a comprehensive exception hierarchy for handling
various error conditions in the library.

Exception Hierarchy:
    FinVistaError
    ├── ConfigError
    ├── NetworkError
    ├── APIError
    │   └── RateLimitError
    ├── DataError
    │   ├── DataNotFoundError
    │   └── DataParsingError
    ├── ValidationError
    │   ├── SymbolNotFoundError
    │   └── DateRangeError
    └── SourceError
        ├── AllSourcesUnavailableError
        └── AllSourcesFailedError
"""

from __future__ import annotations

from typing import Any


class FinVistaError(Exception):
    """
    Base exception class for all FinVista errors.

    All exceptions raised by FinVista inherit from this class,
    making it easy to catch all library-specific errors.

    Attributes:
        message: Human-readable error description.
        code: Optional error code for programmatic handling.
        details: Optional dictionary with additional error context.

    Example:
        >>> try:
        ...     data = fv.get_cn_stock_daily("invalid")
        ... except FinVistaError as e:
        ...     print(f"Error: {e.message}, Code: {e.code}")
    """

    def __init__(
        self,
        message: str,
        code: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.code:
            return f"[{self.code}] {self.message}"
        return self.message

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(message={self.message!r}, code={self.code!r})"


# =============================================================================
# Configuration Errors
# =============================================================================


class ConfigError(FinVistaError):
    """
    Raised when there is a configuration-related error.

    This includes invalid configuration values, missing required
    configuration, or configuration file parsing errors.

    Example:
        >>> fv.set_timeout(-1)
        ConfigError: Timeout must be a positive integer
    """

    def __init__(self, message: str, config_key: str | None = None) -> None:
        self.config_key = config_key
        super().__init__(message, code="CONFIG_ERROR")


# =============================================================================
# Network Errors
# =============================================================================


class NetworkError(FinVistaError):
    """
    Raised when a network-related error occurs.

    This includes connection timeouts, DNS resolution failures,
    SSL/TLS errors, and other transport-level issues.

    Attributes:
        url: The URL that was being accessed when the error occurred.
        original_error: The underlying exception that caused this error.

    Example:
        >>> fv.get_cn_stock_daily("000001")
        NetworkError: Connection timeout while accessing https://...
    """

    def __init__(
        self,
        message: str,
        url: str | None = None,
        original_error: Exception | None = None,
    ) -> None:
        self.url = url
        self.original_error = original_error
        details = {}
        if url:
            details["url"] = url
        if original_error:
            details["original_error"] = str(original_error)
        super().__init__(message, code="NETWORK_ERROR", details=details)


class APIError(FinVistaError):
    """
    Raised when an API returns an error response.

    This includes HTTP errors (4xx, 5xx), API-specific error responses,
    and authentication/authorization failures.

    Attributes:
        status_code: HTTP status code if applicable.
        response_body: Raw response body if available.

    Example:
        >>> fv.get_cn_stock_daily("000001")
        APIError: [HTTP_500] Internal server error from data source
    """

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_body: str | None = None,
    ) -> None:
        self.status_code = status_code
        self.response_body = response_body
        code = f"HTTP_{status_code}" if status_code else "API_ERROR"
        details: dict[str, Any] = {}
        if status_code:
            details["status_code"] = status_code
        if response_body:
            details["response_body"] = response_body[:500]  # Truncate long responses
        super().__init__(message, code=code, details=details)


class RateLimitError(APIError):
    """
    Raised when an API rate limit is exceeded.

    This is a specific type of API error that indicates the client
    has made too many requests in a given time period.

    Attributes:
        retry_after: Suggested wait time in seconds before retrying.

    Example:
        >>> fv.get_cn_stock_daily("000001")
        RateLimitError: Rate limit exceeded, retry after 60 seconds
    """

    def __init__(
        self,
        message: str,
        retry_after: int | None = None,
    ) -> None:
        self.retry_after = retry_after
        super().__init__(message, status_code=429)
        self.code = "RATE_LIMIT"
        if retry_after:
            self.details["retry_after"] = retry_after


# =============================================================================
# Data Errors
# =============================================================================


class DataError(FinVistaError):
    """
    Base class for data-related errors.

    This includes errors during data fetching, parsing, transformation,
    or validation of the returned data.
    """

    def __init__(self, message: str, code: str = "DATA_ERROR") -> None:
        super().__init__(message, code=code)


class DataNotFoundError(DataError):
    """
    Raised when requested data is not found.

    This occurs when a query returns no results, such as requesting
    data for a date range with no trading days or a delisted stock.

    Attributes:
        query_params: Parameters used in the failed query.

    Example:
        >>> fv.get_cn_stock_daily("000001", start_date="2099-01-01")
        DataNotFoundError: No data found for the specified date range
    """

    def __init__(
        self,
        message: str,
        query_params: dict[str, Any] | None = None,
    ) -> None:
        self.query_params = query_params
        super().__init__(message, code="DATA_NOT_FOUND")
        if query_params:
            self.details["query_params"] = query_params


class DataParsingError(DataError):
    """
    Raised when data cannot be parsed or transformed.

    This occurs when the response format is unexpected, data types
    cannot be converted, or required fields are missing.

    Attributes:
        raw_data: Sample of the data that failed to parse.
        parse_location: Location in the data where parsing failed.

    Example:
        >>> fv.get_cn_stock_daily("000001")
        DataParsingError: Failed to parse date field: invalid format
    """

    def __init__(
        self,
        message: str,
        raw_data: str | None = None,
        parse_location: str | None = None,
    ) -> None:
        self.raw_data = raw_data
        self.parse_location = parse_location
        super().__init__(message, code="DATA_PARSING_ERROR")
        if raw_data:
            self.details["raw_data"] = raw_data[:200]  # Truncate
        if parse_location:
            self.details["parse_location"] = parse_location


# =============================================================================
# Validation Errors
# =============================================================================


class ValidationError(FinVistaError):
    """
    Base class for input validation errors.

    This includes invalid parameter values, incorrect types,
    or constraint violations in user-provided input.

    Attributes:
        param_name: Name of the parameter that failed validation.
        param_value: The invalid value that was provided.

    Example:
        >>> fv.get_cn_stock_daily("000001", adjust="invalid")
        ValidationError: Invalid value for 'adjust': must be one of ['none', 'qfq', 'hfq']
    """

    def __init__(
        self,
        message: str,
        param_name: str | None = None,
        param_value: Any = None,
    ) -> None:
        self.param_name = param_name
        self.param_value = param_value
        super().__init__(message, code="VALIDATION_ERROR")
        if param_name:
            self.details["param_name"] = param_name
        if param_value is not None:
            self.details["param_value"] = str(param_value)


class SymbolNotFoundError(ValidationError):
    """
    Raised when a stock/fund/futures symbol is not found.

    This occurs when the provided symbol does not exist in the
    target market or has been delisted.

    Attributes:
        symbol: The symbol that was not found.
        market: The market where the symbol was searched.

    Example:
        >>> fv.get_cn_stock_daily("999999")
        SymbolNotFoundError: Symbol '999999' not found in China market
    """

    def __init__(
        self,
        message: str,
        symbol: str | None = None,
        market: str | None = None,
    ) -> None:
        self.symbol = symbol
        self.market = market
        super().__init__(message, param_name="symbol", param_value=symbol)
        self.code = "SYMBOL_NOT_FOUND"
        if market:
            self.details["market"] = market


class DateRangeError(ValidationError):
    """
    Raised when a date range is invalid.

    This occurs when start_date is after end_date, dates are in
    the future, or date format is incorrect.

    Attributes:
        start_date: The start date that was provided.
        end_date: The end date that was provided.

    Example:
        >>> fv.get_cn_stock_daily("000001", start_date="2024-12-31", end_date="2024-01-01")
        DateRangeError: start_date cannot be after end_date
    """

    def __init__(
        self,
        message: str,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> None:
        self.start_date = start_date
        self.end_date = end_date
        super().__init__(message, param_name="date_range")
        self.code = "DATE_RANGE_ERROR"
        if start_date:
            self.details["start_date"] = start_date
        if end_date:
            self.details["end_date"] = end_date


# =============================================================================
# Source Errors
# =============================================================================


class SourceError(FinVistaError):
    """
    Base class for data source errors.

    This includes errors related to data source availability,
    failover, and circuit breaker states.

    Attributes:
        source_name: Name of the data source involved.
        data_type: Type of data being fetched.
    """

    def __init__(
        self,
        message: str,
        source_name: str | None = None,
        data_type: str | None = None,
    ) -> None:
        self.source_name = source_name
        self.data_type = data_type
        super().__init__(message, code="SOURCE_ERROR")
        if source_name:
            self.details["source_name"] = source_name
        if data_type:
            self.details["data_type"] = data_type


class AllSourcesUnavailableError(SourceError):
    """
    Raised when all data sources are unavailable.

    This occurs when all registered data sources for a data type
    are in a circuit-open state (temporarily disabled due to failures).

    Example:
        >>> fv.get_cn_stock_daily("000001")
        AllSourcesUnavailableError: All sources for 'cn_stock_daily' are currently unavailable
    """

    def __init__(self, message: str, data_type: str | None = None) -> None:
        super().__init__(message, data_type=data_type)
        self.code = "ALL_SOURCES_UNAVAILABLE"


class AllSourcesFailedError(SourceError):
    """
    Raised when all data sources fail to return data.

    This occurs when the library has tried all available data sources
    and all of them returned errors.

    Attributes:
        last_error: The last exception that was raised.
        attempted_sources: List of sources that were attempted.

    Example:
        >>> fv.get_cn_stock_daily("000001")
        AllSourcesFailedError: All sources failed for 'cn_stock_daily'
    """

    def __init__(
        self,
        message: str,
        data_type: str | None = None,
        last_error: Exception | None = None,
        attempted_sources: list[str] | None = None,
    ) -> None:
        self.last_error = last_error
        self.attempted_sources = attempted_sources or []
        super().__init__(message, data_type=data_type)
        self.code = "ALL_SOURCES_FAILED"
        if last_error:
            self.details["last_error"] = str(last_error)
        if attempted_sources:
            self.details["attempted_sources"] = attempted_sources
