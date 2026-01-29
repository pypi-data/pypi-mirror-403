"""
China convertible bond data module.

This module provides functions to fetch convertible bond data including
bond lists, daily prices, and basic information.

Example:
    >>> import finvista as fv
    >>> df = fv.list_cn_convertible_symbols()
    >>> print(df.head())
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from finvista._core.exceptions import ValidationError
from finvista._core.types import DateLike
from finvista._fetchers.cache import cached
from finvista._fetchers.source_manager import source_manager


@cached(ttl=300)
def list_cn_convertible_symbols(
    source: str | None = None,
) -> pd.DataFrame:
    """
    Get list of all convertible bonds.

    Args:
        source: Specific data source to use.

    Returns:
        DataFrame with columns:
        - symbol: Bond symbol
        - name: Bond name
        - price: Current price
        - change_pct: Price change percentage
        - open: Opening price
        - high: Highest price
        - low: Lowest price
        - pre_close: Previous close
        - volume: Trading volume
        - amount: Trading amount

    Example:
        >>> import finvista as fv
        >>> df = fv.list_cn_convertible_symbols()
        >>> print(df.head())
    """
    from finvista._fetchers.adapters.registry import register_all_sources

    register_all_sources()

    if source:
        from finvista._fetchers.adapters.eastmoney import eastmoney_adapter

        df = eastmoney_adapter.fetch_convertible_list()
        df.attrs["source"] = source
    else:
        df, _ = source_manager.fetch_with_fallback(
            data_type="cn_convertible_list",
        )

    return df


@cached(ttl=60)
def get_cn_convertible_daily(
    symbol: str,
    start_date: DateLike | None = None,
    end_date: DateLike | None = None,
    source: str | None = None,
) -> pd.DataFrame:
    """
    Get daily convertible bond data.

    Args:
        symbol: Convertible bond symbol (e.g., "113008", "123456").
        start_date: Start date (YYYY-MM-DD format or date object).
        end_date: End date (YYYY-MM-DD format or date object).
        source: Specific data source to use.

    Returns:
        DataFrame with columns:
        - date: Trading date
        - open: Opening price
        - high: Highest price
        - low: Lowest price
        - close: Closing price
        - volume: Trading volume
        - amount: Trading amount

    Example:
        >>> import finvista as fv
        >>> df = fv.get_cn_convertible_daily("113008", start_date="2024-01-01")
        >>> print(df.head())
    """
    if not symbol:
        raise ValidationError("Symbol cannot be empty", param_name="symbol")

    from finvista._fetchers.adapters.registry import register_all_sources

    register_all_sources()

    if source:
        from finvista._fetchers.adapters.eastmoney import eastmoney_adapter

        df = eastmoney_adapter.fetch_convertible_daily(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
        )
        df.attrs["source"] = source
    else:
        df, _ = source_manager.fetch_with_fallback(
            data_type="cn_convertible_daily",
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
        )

    return df


@cached(ttl=3600)
def get_cn_convertible_info(
    symbol: str,
    source: str | None = None,
) -> dict[str, Any]:
    """
    Get convertible bond basic information.

    Args:
        symbol: Convertible bond symbol or underlying stock symbol.
        source: Specific data source to use.

    Returns:
        Dictionary with:
        - bond_code: Bond symbol
        - bond_name: Bond name
        - stock_code: Underlying stock symbol
        - stock_name: Underlying stock name
        - convert_price: Conversion price
        - convert_value: Conversion value
        - premium_rate: Premium rate
        - bond_price: Current bond price
        - issue_date: Issue date
        - maturity_date: Maturity date

    Example:
        >>> import finvista as fv
        >>> info = fv.get_cn_convertible_info("113008")
        >>> print(info)
    """
    if not symbol:
        raise ValidationError("Symbol cannot be empty", param_name="symbol")

    from finvista._fetchers.adapters.eastmoney import eastmoney_adapter

    return eastmoney_adapter.fetch_convertible_info(symbol=symbol)
