"""
China A-share Dragon Tiger List (龙虎榜) data module.

This module provides functions to fetch dragon tiger list data including
daily rankings, trading details, and institution trading data.

Example:
    >>> import finvista as fv
    >>> df = fv.get_cn_lhb_list()
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


@cached(ttl=300)
def get_cn_lhb_list(
    date: DateLike | None = None,
    source: str | None = None,
) -> pd.DataFrame:
    """
    Get dragon tiger list data.

    Args:
        date: Date to query (YYYY-MM-DD). If None, returns latest data.
        source: Specific data source to use.

    Returns:
        DataFrame with columns:
        - date: Trading date
        - symbol: Stock symbol
        - name: Stock name
        - close: Closing price
        - change_pct: Price change percentage
        - turnover_rate: Turnover rate
        - reason: Reason for appearing on the list
        - buy_amount: Total buy amount
        - sell_amount: Total sell amount
        - net_amount: Net amount

    Example:
        >>> import finvista as fv
        >>> # Get latest dragon tiger list
        >>> df = fv.get_cn_lhb_list()
        >>> print(df.head())

        >>> # Get data for specific date
        >>> df = fv.get_cn_lhb_list(date="2024-01-15")
    """
    date_str = None
    if date is not None:
        if isinstance(date, str):
            date_str = date
        elif isinstance(date, (datetime,)):
            date_str = date.strftime("%Y-%m-%d")

    from finvista._fetchers.adapters.registry import register_all_sources

    register_all_sources()

    if source:
        from finvista._fetchers.adapters.eastmoney import eastmoney_adapter

        df = eastmoney_adapter.fetch_lhb_list(date=date_str)
        df.attrs["source"] = source
    else:
        df, _ = source_manager.fetch_with_fallback(
            data_type="cn_lhb_list",
            date=date_str,
        )

    return df


@cached(ttl=300)
def get_cn_lhb_detail(
    symbol: str,
    date: str,
    source: str | None = None,
) -> pd.DataFrame:
    """
    Get dragon tiger list trading details.

    Args:
        symbol: Stock symbol.
        date: Trading date (YYYY-MM-DD).
        source: Specific data source to use.

    Returns:
        DataFrame with columns:
        - date: Trading date
        - symbol: Stock symbol
        - rank: Trading rank
        - trader_name: Trader/institution name
        - buy_amount: Buy amount
        - sell_amount: Sell amount
        - net_amount: Net amount
        - buy_pct: Buy percentage
        - sell_pct: Sell percentage

    Example:
        >>> import finvista as fv
        >>> df = fv.get_cn_lhb_detail("000001", "2024-01-15")
        >>> print(df.head())
    """
    symbol = _validate_symbol(symbol)

    from finvista._fetchers.adapters.registry import register_all_sources

    register_all_sources()

    if source:
        from finvista._fetchers.adapters.eastmoney import eastmoney_adapter

        df = eastmoney_adapter.fetch_lhb_detail(symbol=symbol, date=date)
        df.attrs["source"] = source
    else:
        df, _ = source_manager.fetch_with_fallback(
            data_type="cn_lhb_detail",
            symbol=symbol,
            date=date,
        )

    return df


@cached(ttl=300)
def get_cn_lhb_institution(
    date: DateLike | None = None,
    source: str | None = None,
) -> pd.DataFrame:
    """
    Get institution trading data from dragon tiger list.

    Args:
        date: Date to query (YYYY-MM-DD). If None, returns recent data.
        source: Specific data source to use.

    Returns:
        DataFrame with columns:
        - date: Trading date
        - symbol: Stock symbol
        - name: Stock name
        - close: Closing price
        - change_pct: Price change percentage
        - institution_buy: Institution buy amount
        - institution_sell: Institution sell amount
        - institution_net: Institution net amount
        - reason: Reason for appearing on the list

    Example:
        >>> import finvista as fv
        >>> df = fv.get_cn_lhb_institution()
        >>> print(df.head())
    """
    date_str = None
    if date is not None:
        if isinstance(date, str):
            date_str = date
        elif isinstance(date, (datetime,)):
            date_str = date.strftime("%Y-%m-%d")

    from finvista._fetchers.adapters.registry import register_all_sources

    register_all_sources()

    if source:
        from finvista._fetchers.adapters.eastmoney import eastmoney_adapter

        df = eastmoney_adapter.fetch_lhb_institution(date=date_str)
        df.attrs["source"] = source
    else:
        df, _ = source_manager.fetch_with_fallback(
            data_type="cn_lhb_institution",
            date=date_str,
        )

    return df
