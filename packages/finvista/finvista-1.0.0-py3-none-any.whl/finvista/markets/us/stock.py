"""
US stock data module.

This module provides functions to fetch US stock market data
including historical prices, real-time quotes, and stock information.

Example:
    >>> import finvista as fv
    >>> df = fv.get_us_stock_daily("AAPL", start_date="2024-01-01")
    >>> print(df.head())
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

import pandas as pd

from finvista._core.exceptions import DateRangeError, ValidationError
from finvista._core.types import DateLike
from finvista._fetchers.cache import cached
from finvista._fetchers.source_manager import source_manager


def _validate_symbol(symbol: str) -> str:
    """
    Validate and normalize a US stock symbol.

    Args:
        symbol: Stock symbol to validate.

    Returns:
        Normalized symbol string.

    Raises:
        ValidationError: If symbol is invalid.
    """
    if not symbol:
        raise ValidationError("Symbol cannot be empty", param_name="symbol")

    # Normalize symbol
    symbol = symbol.upper().strip()

    # Basic validation - US symbols are 1-5 characters
    if len(symbol) > 10:
        raise ValidationError(
            f"Invalid symbol format: {symbol}",
            param_name="symbol",
            param_value=symbol,
        )

    return symbol


def _validate_date_range(
    start_date: DateLike | None,
    end_date: DateLike | None,
) -> tuple[str | None, str | None]:
    """
    Validate and normalize date range.

    Args:
        start_date: Start date.
        end_date: End date.

    Returns:
        Tuple of (start_date, end_date) as strings or None.

    Raises:
        DateRangeError: If date range is invalid.
    """
    start_str: str | None = None
    end_str: str | None = None

    if start_date is not None:
        if isinstance(start_date, str):
            start_str = start_date.replace("-", "").replace("/", "")
        elif isinstance(start_date, (date, datetime)):
            start_str = start_date.strftime("%Y%m%d")

    if end_date is not None:
        if isinstance(end_date, str):
            end_str = end_date.replace("-", "").replace("/", "")
        elif isinstance(end_date, (date, datetime)):
            end_str = end_date.strftime("%Y%m%d")

    # Validate range
    if start_str and end_str:
        if start_str > end_str:
            raise DateRangeError(
                "start_date cannot be after end_date",
                start_date=start_str,
                end_date=end_str,
            )

    return start_str, end_str


@cached(ttl=60)
def get_us_stock_daily(
    symbol: str,
    start_date: DateLike | None = None,
    end_date: DateLike | None = None,
    source: str | None = None,
) -> pd.DataFrame:
    """
    Get daily historical data for a US stock.

    Args:
        symbol: Stock symbol (e.g., "AAPL", "MSFT", "GOOGL").
        start_date: Start date (YYYY-MM-DD format or date object).
                   Defaults to 1 year ago.
        end_date: End date (YYYY-MM-DD format or date object).
                 Defaults to today.
        source: Specific data source to use. If None, uses automatic
               failover between available sources.

    Returns:
        DataFrame with columns:
        - date: Trading date
        - open: Opening price
        - high: Highest price
        - low: Lowest price
        - close: Closing price
        - volume: Trading volume
        - adj_close: Adjusted closing price

    Raises:
        ValidationError: If the symbol format is invalid.
        DateRangeError: If the date range is invalid.
        AllSourcesFailedError: If all data sources fail.

    Example:
        >>> import finvista as fv
        >>> df = fv.get_us_stock_daily("AAPL", start_date="2024-01-01")
        >>> print(df.head())
                 date    open    high     low   close    volume  adj_close
        0  2024-01-02  187.15  188.44  183.89  185.64  82488700     185.29
        1  2024-01-03  184.22  185.88  183.43  184.25  58414500     183.90

        >>> # Check which source was used
        >>> print(f"Data source: {df.attrs.get('source')}")
        Data source: yahoo
    """
    # Validate inputs
    symbol = _validate_symbol(symbol)
    start_date_str, end_date_str = _validate_date_range(start_date, end_date)

    # Ensure sources are registered
    from finvista._fetchers.adapters.registry import register_all_sources

    register_all_sources()

    # Fetch data
    if source:
        from finvista._fetchers.adapters.yahoo import yahoo_adapter

        adapters = {"yahoo": yahoo_adapter}
        if source not in adapters:
            raise ValidationError(f"Unknown source: {source}", param_name="source")

        df = adapters[source].fetch_stock_daily(
            symbol=symbol,
            start_date=start_date_str,
            end_date=end_date_str,
        )
        df.attrs["source"] = source
    else:
        df, used_source = source_manager.fetch_with_fallback(
            data_type="us_stock_daily",
            symbol=symbol,
            start_date=start_date_str,
            end_date=end_date_str,
        )

    return df


@cached(ttl=10)
def get_us_stock_quote(
    symbol: str | list[str],
    source: str | None = None,
) -> pd.DataFrame:
    """
    Get real-time quotes for US stocks.

    Args:
        symbol: Single symbol or list of symbols.
        source: Specific data source to use.

    Returns:
        DataFrame with real-time quote data including:
        - symbol: Stock symbol
        - name: Company name
        - price: Current price
        - change: Price change
        - change_pct: Price change percentage
        - open: Opening price
        - high: Day high
        - low: Day low
        - pre_close: Previous close
        - volume: Trading volume
        - market_cap: Market capitalization
        - pe: P/E ratio
        - market_state: Market state (PRE, REGULAR, POST, CLOSED)

    Example:
        >>> import finvista as fv
        >>> df = fv.get_us_stock_quote(["AAPL", "MSFT", "GOOGL"])
        >>> print(df)
    """
    # Normalize to list
    if isinstance(symbol, str):
        symbols = [_validate_symbol(symbol)]
    else:
        symbols = [_validate_symbol(s) for s in symbol]

    # Ensure sources are registered
    from finvista._fetchers.adapters.registry import register_all_sources

    register_all_sources()

    if source:
        from finvista._fetchers.adapters.yahoo import yahoo_adapter

        df = yahoo_adapter.fetch_stock_quote(symbols)
        df.attrs["source"] = source
    else:
        df, _ = source_manager.fetch_with_fallback(
            data_type="us_stock_quote",
            symbols=symbols,
        )

    return df


@cached(ttl=3600)
def get_us_stock_info(
    symbol: str,
) -> dict[str, Any]:
    """
    Get detailed information for a US stock.

    Args:
        symbol: Stock symbol.

    Returns:
        Dictionary with stock information:
        - symbol: Stock symbol
        - industry: Industry
        - sector: Sector
        - country: Country
        - website: Company website
        - employees: Number of employees
        - description: Company description
        - market_cap: Market capitalization
        - pe_trailing: Trailing P/E ratio
        - pe_forward: Forward P/E ratio
        - dividend_yield: Dividend yield
        - beta: Beta
        - 52_week_high: 52-week high
        - 52_week_low: 52-week low

    Example:
        >>> import finvista as fv
        >>> info = fv.get_us_stock_info("AAPL")
        >>> print(f"Sector: {info['sector']}")
        Sector: Technology
    """
    symbol = _validate_symbol(symbol)

    from finvista._fetchers.adapters.yahoo import yahoo_adapter

    return yahoo_adapter.fetch_stock_info(symbol)


def search_us_stock(
    keyword: str,
    limit: int = 10,
) -> pd.DataFrame:
    """
    Search for US stocks by keyword.

    Args:
        keyword: Search keyword (symbol, company name).
        limit: Maximum number of results to return.

    Returns:
        DataFrame with matching stocks:
        - symbol: Stock symbol
        - name: Company name
        - type: Security type
        - exchange: Exchange

    Example:
        >>> import finvista as fv
        >>> df = fv.search_us_stock("Apple")
        >>> print(df.head())
    """
    if not keyword:
        raise ValidationError("Keyword cannot be empty", param_name="keyword")

    from finvista._fetchers.adapters.yahoo import yahoo_adapter

    return yahoo_adapter.search_stocks(keyword, limit=limit)
