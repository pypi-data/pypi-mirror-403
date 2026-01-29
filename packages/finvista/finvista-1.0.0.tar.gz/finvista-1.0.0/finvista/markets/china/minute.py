"""
China A-share minute-level data module.

This module provides functions to fetch minute-level stock data
including 1-minute, 5-minute, 15-minute, 30-minute, and 60-minute intervals.

Example:
    >>> import finvista as fv
    >>> df = fv.get_cn_stock_minute("000001", period="5")
    >>> print(df.head())
"""

from __future__ import annotations

from typing import Literal

import pandas as pd

from finvista._core.exceptions import ValidationError
from finvista._fetchers.cache import cached
from finvista._fetchers.source_manager import source_manager


def _validate_symbol(symbol: str) -> str:
    """Validate and normalize a stock symbol."""
    if not symbol:
        raise ValidationError("Symbol cannot be empty", param_name="symbol")

    symbol = symbol.upper().strip()
    for prefix in ["SH", "SZ", "BJ", "."]:
        if symbol.startswith(prefix):
            symbol = symbol[len(prefix):]

    if not symbol.isdigit() or len(symbol) != 6:
        raise ValidationError(
            f"Invalid symbol format: {symbol}. Expected 6 digits.",
            param_name="symbol",
            param_value=symbol,
        )

    return symbol


@cached(ttl=60)
def get_cn_stock_minute(
    symbol: str,
    period: Literal["1", "5", "15", "30", "60"] = "5",
    days: int = 5,
    source: str | None = None,
) -> pd.DataFrame:
    """
    Get minute-level stock data for a China A-share stock.

    Args:
        symbol: Stock symbol (e.g., "000001" for Ping An Bank).
        period: Minute interval ('1', '5', '15', '30', '60').
        days: Number of days of data to fetch.
        source: Specific data source to use.

    Returns:
        DataFrame with columns:
        - datetime: Timestamp
        - open: Opening price
        - high: Highest price
        - low: Lowest price
        - close: Closing price
        - volume: Trading volume
        - amount: Trading amount

    Example:
        >>> import finvista as fv
        >>> # Get 5-minute data for last 5 days
        >>> df = fv.get_cn_stock_minute("000001", period="5", days=5)
        >>> print(df.head())

        >>> # Get 1-minute data
        >>> df = fv.get_cn_stock_minute("000001", period="1", days=1)
    """
    symbol = _validate_symbol(symbol)

    if period not in ("1", "5", "15", "30", "60"):
        raise ValidationError(
            f"Invalid period: {period}. Must be '1', '5', '15', '30', or '60'.",
            param_name="period",
            param_value=period,
        )

    from finvista._fetchers.adapters.registry import register_all_sources

    register_all_sources()

    if source:
        from finvista._fetchers.adapters.eastmoney import eastmoney_adapter

        df = eastmoney_adapter.fetch_stock_minute(symbol=symbol, period=period, days=days)
        df.attrs["source"] = source
    else:
        df, _ = source_manager.fetch_with_fallback(
            data_type="cn_stock_minute",
            symbol=symbol,
            period=period,
            days=days,
        )

    return df
