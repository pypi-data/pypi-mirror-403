"""
China index data module.

This module provides functions to fetch Chinese market index data
including historical prices and real-time quotes.

Example:
    >>> import finvista as fv
    >>> df = fv.get_cn_index_daily("000001", start_date="2024-01-01")
    >>> print(df.head())
"""

from __future__ import annotations

from datetime import date, datetime

import pandas as pd

from finvista._core.exceptions import DateRangeError, ValidationError
from finvista._core.types import DateLike
from finvista._fetchers.cache import cached
from finvista._fetchers.source_manager import source_manager

# Common China indices
MAJOR_INDICES = {
    "000001": "SSE Composite (上证综指)",
    "000300": "CSI 300 (沪深300)",
    "000016": "SSE 50 (上证50)",
    "000905": "CSI 500 (中证500)",
    "000852": "CSI 1000 (中证1000)",
    "399001": "SZSE Component (深证成指)",
    "399006": "ChiNext (创业板指)",
    "399005": "SME Board (中小板指)",
    "399673": "ChiNext 50 (创业板50)",
}


def _validate_index_symbol(symbol: str) -> str:
    """
    Validate and normalize an index symbol.

    Args:
        symbol: Index symbol to validate.

    Returns:
        Normalized symbol string.

    Raises:
        ValidationError: If symbol is invalid.
    """
    if not symbol:
        raise ValidationError("Symbol cannot be empty", param_name="symbol")

    # Remove any exchange prefix
    symbol = symbol.upper().strip()
    for prefix in ["SH", "SZ", "."]:
        if symbol.startswith(prefix):
            symbol = symbol[len(prefix):]

    # Validate format
    if not symbol.isdigit() or len(symbol) != 6:
        raise ValidationError(
            f"Invalid index symbol format: {symbol}. Expected 6 digits.",
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
def get_cn_index_daily(
    symbol: str,
    start_date: DateLike | None = None,
    end_date: DateLike | None = None,
    source: str | None = None,
) -> pd.DataFrame:
    """
    Get daily historical data for a China market index.

    Args:
        symbol: Index symbol (e.g., "000001" for SSE Composite).
                Common indices:
                - "000001": SSE Composite (上证综指)
                - "000300": CSI 300 (沪深300)
                - "000016": SSE 50 (上证50)
                - "399001": SZSE Component (深证成指)
                - "399006": ChiNext (创业板指)
        start_date: Start date (YYYY-MM-DD format or date object).
                   Defaults to 1 year ago.
        end_date: End date (YYYY-MM-DD format or date object).
                 Defaults to today.
        source: Specific data source to use. If None, uses automatic
               failover between available sources.

    Returns:
        DataFrame with columns:
        - date: Trading date
        - open: Opening value
        - high: Highest value
        - low: Lowest value
        - close: Closing value
        - volume: Trading volume
        - amount: Trading amount

    Raises:
        ValidationError: If the symbol format is invalid.
        DateRangeError: If the date range is invalid.
        AllSourcesFailedError: If all data sources fail.

    Example:
        >>> import finvista as fv
        >>> # Get SSE Composite Index data
        >>> df = fv.get_cn_index_daily("000001", start_date="2024-01-01")
        >>> print(df.head())
                 date     open     high      low    close      volume         amount
        0  2024-01-02  2974.93  2987.64  2962.16  2974.93  318624531  3.816247e+11

        >>> # Check which source was used
        >>> print(f"Data source: {df.attrs.get('source')}")
        Data source: eastmoney
    """
    # Validate inputs
    symbol = _validate_index_symbol(symbol)
    start_date_str, end_date_str = _validate_date_range(start_date, end_date)

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

        df = adapters[source].fetch_index_daily(
            symbol=symbol,
            start_date=start_date_str,
            end_date=end_date_str,
        )
        df.attrs["source"] = source
    else:
        # Use source manager with failover
        df, used_source = source_manager.fetch_with_fallback(
            data_type="cn_index_daily",
            symbol=symbol,
            start_date=start_date_str,
            end_date=end_date_str,
        )

    return df


@cached(ttl=10)
def get_cn_index_quote(
    symbol: str | list[str],
    source: str | None = None,
) -> pd.DataFrame:
    """
    Get real-time quotes for China market indices.

    Args:
        symbol: Single symbol or list of symbols.
        source: Specific data source to use.

    Returns:
        DataFrame with real-time index data including:
        - symbol: Index symbol
        - name: Index name
        - price: Current value
        - change: Value change
        - change_pct: Change percentage
        - volume: Trading volume
        - amount: Trading amount

    Example:
        >>> import finvista as fv
        >>> df = fv.get_cn_index_quote(["000001", "399001"])
        >>> print(df)
    """
    # Normalize to list
    if isinstance(symbol, str):
        symbols = [_validate_index_symbol(symbol)]
    else:
        symbols = [_validate_index_symbol(s) for s in symbol]

    # Ensure sources are registered
    from finvista._fetchers.adapters.registry import register_all_sources

    register_all_sources()

    if source:
        from finvista._fetchers.adapters.sina import sina_adapter

        df = sina_adapter.fetch_index_quote(symbols)
        df.attrs["source"] = source
    else:
        df, _ = source_manager.fetch_with_fallback(
            data_type="cn_index_quote",
            symbols=symbols,
        )

    return df


def list_cn_major_indices() -> pd.DataFrame:
    """
    Get list of major China market indices.

    Returns:
        DataFrame with index information:
        - symbol: Index symbol
        - name: Index name (English and Chinese)

    Example:
        >>> import finvista as fv
        >>> df = fv.list_cn_major_indices()
        >>> print(df)
           symbol                       name
        0  000001    SSE Composite (上证综指)
        1  000300         CSI 300 (沪深300)
        2  000016          SSE 50 (上证50)
        3  399001  SZSE Component (深证成指)
        4  399006       ChiNext (创业板指)
    """
    records = [
        {"symbol": symbol, "name": name}
        for symbol, name in MAJOR_INDICES.items()
    ]
    return pd.DataFrame(records)


@cached(ttl=3600)
def get_cn_index_constituents(
    symbol: str,
    source: str | None = None,
) -> pd.DataFrame:
    """
    Get index constituent stocks.

    Args:
        symbol: Index symbol (e.g., "000300" for CSI 300).
        source: Specific data source to use.

    Returns:
        DataFrame with columns:
        - index_code: Index symbol
        - symbol: Stock symbol
        - name: Stock name
        - close: Closing price
        - change_pct: Price change percentage

    Example:
        >>> import finvista as fv
        >>> df = fv.get_cn_index_constituents("000300")
        >>> print(df.head())
    """
    symbol = _validate_index_symbol(symbol)

    from finvista._fetchers.adapters.registry import register_all_sources

    register_all_sources()

    if source:
        from finvista._fetchers.adapters.eastmoney import eastmoney_adapter

        df = eastmoney_adapter.fetch_index_constituents(symbol=symbol)
        df.attrs["source"] = source
    else:
        df, _ = source_manager.fetch_with_fallback(
            data_type="cn_index_constituents",
            symbol=symbol,
        )

    return df


@cached(ttl=3600)
def get_cn_index_weights(
    symbol: str,
    source: str | None = None,
) -> pd.DataFrame:
    """
    Get index constituent weights.

    Args:
        symbol: Index symbol (e.g., "000300" for CSI 300).
        source: Specific data source to use.

    Returns:
        DataFrame with columns:
        - index_code: Index symbol
        - symbol: Stock symbol
        - name: Stock name
        - weight: Stock weight in index

    Example:
        >>> import finvista as fv
        >>> df = fv.get_cn_index_weights("000300")
        >>> print(df.head())
    """
    symbol = _validate_index_symbol(symbol)

    from finvista._fetchers.adapters.registry import register_all_sources

    register_all_sources()

    if source:
        from finvista._fetchers.adapters.eastmoney import eastmoney_adapter

        df = eastmoney_adapter.fetch_index_weights(symbol=symbol)
        df.attrs["source"] = source
    else:
        df, _ = source_manager.fetch_with_fallback(
            data_type="cn_index_weights",
            symbol=symbol,
        )

    return df
