"""
China A-share stock data module.

This module provides functions to fetch Chinese A-share stock data
including historical prices, real-time quotes, and stock information.

Example:
    >>> import finvista as fv
    >>> df = fv.get_cn_stock_daily("000001", start_date="2024-01-01")
    >>> print(df.head())
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

import pandas as pd

from finvista._core.exceptions import (
    DateRangeError,
    ValidationError,
)
from finvista._core.types import AdjustType, DateLike
from finvista._fetchers.cache import cached
from finvista._fetchers.source_manager import source_manager


def _validate_symbol(symbol: str) -> str:
    """
    Validate and normalize a stock symbol.

    Args:
        symbol: Stock symbol to validate.

    Returns:
        Normalized symbol string.

    Raises:
        ValidationError: If symbol is invalid.
    """
    if not symbol:
        raise ValidationError("Symbol cannot be empty", param_name="symbol")

    # Remove any exchange prefix
    symbol = symbol.upper().strip()
    for prefix in ["SH", "SZ", "BJ", "."]:
        if symbol.startswith(prefix):
            symbol = symbol[len(prefix) :]

    # Validate format
    if not symbol.isdigit() or len(symbol) != 6:
        raise ValidationError(
            f"Invalid symbol format: {symbol}. Expected 6 digits.",
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
            start_str = start_date.strftime("%Y-%m-%d")

    if end_date is not None:
        if isinstance(end_date, str):
            end_str = end_date.replace("-", "").replace("/", "")
        elif isinstance(end_date, (date, datetime)):
            end_str = end_date.strftime("%Y-%m-%d")

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
def get_cn_stock_daily(
    symbol: str,
    start_date: DateLike | None = None,
    end_date: DateLike | None = None,
    adjust: AdjustType = "none",
    source: str | None = None,
) -> pd.DataFrame:
    """
    Get daily historical data for a China A-share stock.

    Args:
        symbol: Stock symbol (e.g., "000001" for Ping An Bank).
        start_date: Start date (YYYY-MM-DD format or date object).
                   Defaults to 1 year ago.
        end_date: End date (YYYY-MM-DD format or date object).
                 Defaults to today.
        adjust: Price adjustment type:
               - "none": No adjustment (raw prices)
               - "qfq": Forward adjusted (前复权)
               - "hfq": Backward adjusted (后复权)
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
        - amount: Trading amount
        - change: Price change
        - change_pct: Price change percentage
        - turnover: Turnover rate

    Raises:
        SymbolNotFoundError: If the symbol does not exist.
        DateRangeError: If the date range is invalid.
        AllSourcesFailedError: If all data sources fail.

    Example:
        >>> import finvista as fv
        >>> # Get daily data with forward adjustment
        >>> df = fv.get_cn_stock_daily(
        ...     "000001",
        ...     start_date="2024-01-01",
        ...     end_date="2024-06-30",
        ...     adjust="qfq"
        ... )
        >>> print(df.head())
                 date   open   high    low  close    volume        amount
        0  2024-01-02   9.82   9.85   9.72   9.73   1234567   12345678.90
        1  2024-01-03   9.74   9.80   9.70   9.78   1345678   13456789.01

        >>> # Check which source was used
        >>> print(f"Data source: {df.attrs.get('source')}")
        Data source: eastmoney
    """
    # Validate inputs
    symbol = _validate_symbol(symbol)
    start_date_str, end_date_str = _validate_date_range(start_date, end_date)

    if adjust not in ("none", "qfq", "hfq"):
        raise ValidationError(
            f"Invalid adjust type: {adjust}. Must be 'none', 'qfq', or 'hfq'.",
            param_name="adjust",
            param_value=adjust,
        )

    # Ensure sources are registered
    from finvista._fetchers.adapters.registry import register_all_sources

    register_all_sources()

    # Fetch data
    if source:
        # Use specific source
        from finvista._fetchers.adapters.eastmoney import eastmoney_adapter

        adapters = {"eastmoney": eastmoney_adapter}
        if source not in adapters:
            raise ValidationError(f"Unknown source: {source}", param_name="source")

        df = adapters[source].fetch_stock_daily(
            symbol=symbol,
            start_date=start_date_str,
            end_date=end_date_str,
            adjust=adjust,
        )
        df.attrs["source"] = source
    else:
        # Use source manager with failover
        df, used_source = source_manager.fetch_with_fallback(
            data_type="cn_stock_daily",
            symbol=symbol,
            start_date=start_date_str,
            end_date=end_date_str,
            adjust=adjust,
        )

    return df


@cached(ttl=10)
def get_cn_stock_quote(
    symbol: str | list[str],
    source: str | None = None,
) -> pd.DataFrame:
    """
    Get real-time quotes for China A-share stocks.

    Args:
        symbol: Single symbol or list of symbols.
        source: Specific data source to use.

    Returns:
        DataFrame with real-time quote data including:
        - symbol: Stock symbol
        - name: Stock name
        - price: Current price
        - change: Price change
        - change_pct: Price change percentage
        - open: Opening price
        - high: Highest price
        - low: Lowest price
        - pre_close: Previous close price
        - volume: Trading volume
        - amount: Trading amount

    Example:
        >>> import finvista as fv
        >>> df = fv.get_cn_stock_quote(["000001", "600519"])
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
        from finvista._fetchers.adapters.eastmoney import eastmoney_adapter

        df = eastmoney_adapter.fetch_stock_quote(symbols)
        df.attrs["source"] = source
    else:
        df, _ = source_manager.fetch_with_fallback(
            data_type="cn_stock_quote",
            symbols=symbols,
        )

    return df


@cached(ttl=3600)
def list_cn_stock_symbols(
    market: Literal["all", "sh", "sz", "main", "gem", "star"] = "all",
    source: str | None = None,
) -> pd.DataFrame:
    """
    Get list of all China A-share stock symbols.

    Args:
        market: Market filter:
               - "all": All markets
               - "sh": Shanghai Stock Exchange
               - "sz": Shenzhen Stock Exchange
               - "main": Main board (Shanghai + Shenzhen)
               - "gem": ChiNext (创业板)
               - "star": STAR Market (科创板)
        source: Specific data source to use.

    Returns:
        DataFrame with stock information:
        - symbol: Stock symbol
        - name: Stock name
        - market: Market (sh/sz)

    Example:
        >>> import finvista as fv
        >>> # Get all STAR Market stocks
        >>> df = fv.list_cn_stock_symbols(market="star")
        >>> print(f"Found {len(df)} STAR Market stocks")
    """
    # Ensure sources are registered
    from finvista._fetchers.adapters.registry import register_all_sources

    register_all_sources()

    if source:
        from finvista._fetchers.adapters.eastmoney import eastmoney_adapter

        df = eastmoney_adapter.fetch_stock_list(market=market)
        df.attrs["source"] = source
    else:
        df, _ = source_manager.fetch_with_fallback(
            data_type="cn_stock_list",
            market=market,
        )

    return df


def search_cn_stock(
    keyword: str,
    limit: int = 20,
) -> pd.DataFrame:
    """
    Search for stocks by keyword.

    Args:
        keyword: Search keyword (symbol, name, or pinyin abbreviation).
        limit: Maximum number of results to return.

    Returns:
        DataFrame with matching stocks.

    Example:
        >>> import finvista as fv
        >>> df = fv.search_cn_stock("银行")
        >>> print(df.head())
    """
    if not keyword:
        raise ValidationError("Keyword cannot be empty", param_name="keyword")

    # Get all stocks and filter
    df = list_cn_stock_symbols()

    if len(df) == 0:
        return df

    # Search in symbol and name
    mask = df["symbol"].str.contains(keyword, case=False, na=False) | df["name"].str.contains(
        keyword, case=False, na=False
    )

    result = df[mask].head(limit).reset_index(drop=True)

    return result
