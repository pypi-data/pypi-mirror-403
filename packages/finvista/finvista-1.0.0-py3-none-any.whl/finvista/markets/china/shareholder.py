"""
China A-share shareholder data module.

This module provides functions to fetch shareholder data including
top shareholders, stock pledges, and unlock schedules.

Example:
    >>> import finvista as fv
    >>> df = fv.get_cn_top_shareholders("000001")
    >>> print(df.head())
"""

from __future__ import annotations

from datetime import datetime

import pandas as pd

from finvista._core.exceptions import ValidationError
from finvista._core.types import DateLike
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


@cached(ttl=3600)
def get_cn_top_shareholders(
    symbol: str,
    period: DateLike | None = None,
    source: str | None = None,
) -> pd.DataFrame:
    """
    Get top 10 shareholders data.

    Args:
        symbol: Stock symbol (e.g., "000001").
        period: Report period (YYYY-MM-DD). If None, returns all periods.
        source: Specific data source to use.

    Returns:
        DataFrame with columns:
        - report_date: Report date
        - rank: Shareholder rank
        - holder_name: Shareholder name
        - holder_type: Shareholder type
        - shares: Number of shares held
        - shares_pct: Percentage of shares held
        - change: Change in shares
        - change_pct: Change percentage

    Example:
        >>> import finvista as fv
        >>> df = fv.get_cn_top_shareholders("000001")
        >>> print(df.head())
    """
    symbol = _validate_symbol(symbol)

    period_str = None
    if period is not None:
        if isinstance(period, str):
            period_str = period
        elif isinstance(period, (datetime,)):
            period_str = period.strftime("%Y-%m-%d")

    from finvista._fetchers.adapters.registry import register_all_sources

    register_all_sources()

    if source:
        from finvista._fetchers.adapters.eastmoney import eastmoney_adapter

        df = eastmoney_adapter.fetch_top_shareholders(symbol=symbol, period=period_str)
        df.attrs["source"] = source
    else:
        df, _ = source_manager.fetch_with_fallback(
            data_type="cn_top_shareholders",
            symbol=symbol,
            period=period_str,
        )

    return df


@cached(ttl=3600)
def get_cn_stock_pledge(
    symbol: str,
    source: str | None = None,
) -> pd.DataFrame:
    """
    Get stock pledge data.

    Args:
        symbol: Stock symbol (e.g., "000001").
        source: Specific data source to use.

    Returns:
        DataFrame with columns:
        - symbol: Stock symbol
        - pledge_date: Pledge date
        - holder_name: Pledgor name
        - pledgee: Pledgee name
        - shares: Number of shares pledged
        - shares_pct: Percentage of shares pledged
        - start_date: Pledge start date
        - end_date: Pledge end date

    Example:
        >>> import finvista as fv
        >>> df = fv.get_cn_stock_pledge("000001")
        >>> print(df.head())
    """
    symbol = _validate_symbol(symbol)

    from finvista._fetchers.adapters.registry import register_all_sources

    register_all_sources()

    if source:
        from finvista._fetchers.adapters.eastmoney import eastmoney_adapter

        df = eastmoney_adapter.fetch_stock_pledge(symbol=symbol)
        df.attrs["source"] = source
    else:
        df, _ = source_manager.fetch_with_fallback(
            data_type="cn_stock_pledge",
            symbol=symbol,
        )

    return df


@cached(ttl=3600)
def get_cn_stock_unlock_schedule(
    start_date: str,
    end_date: str,
    source: str | None = None,
) -> pd.DataFrame:
    """
    Get stock unlock schedule.

    Args:
        start_date: Start date (YYYY-MM-DD).
        end_date: End date (YYYY-MM-DD).
        source: Specific data source to use.

    Returns:
        DataFrame with columns:
        - unlock_date: Unlock date
        - symbol: Stock symbol
        - name: Stock name
        - unlock_shares: Number of shares to be unlocked
        - unlock_ratio: Unlock ratio
        - unlock_value: Unlock market value
        - lock_type: Type of lock-up

    Example:
        >>> import finvista as fv
        >>> df = fv.get_cn_stock_unlock_schedule("2024-01-01", "2024-01-31")
        >>> print(df.head())
    """
    if not start_date or not end_date:
        raise ValidationError("start_date and end_date are required")

    from finvista._fetchers.adapters.registry import register_all_sources

    register_all_sources()

    if source:
        from finvista._fetchers.adapters.eastmoney import eastmoney_adapter

        df = eastmoney_adapter.fetch_stock_unlock(start_date=start_date, end_date=end_date)
        df.attrs["source"] = source
    else:
        df, _ = source_manager.fetch_with_fallback(
            data_type="cn_stock_unlock",
            start_date=start_date,
            end_date=end_date,
        )

    return df
