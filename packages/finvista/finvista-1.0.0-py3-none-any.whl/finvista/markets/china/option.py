"""
China option data module.

This module provides functions to fetch option data including
contract lists, quotes, and daily prices.

Example:
    >>> import finvista as fv
    >>> df = fv.list_cn_option_contracts()
    >>> print(df.head())
"""

from __future__ import annotations

import pandas as pd

from finvista._core.exceptions import ValidationError
from finvista._core.types import DateLike
from finvista._fetchers.cache import cached
from finvista._fetchers.source_manager import source_manager


@cached(ttl=60)
def list_cn_option_contracts(
    underlying: str = "510050",
    source: str | None = None,
) -> pd.DataFrame:
    """
    Get list of option contracts.

    Args:
        underlying: Underlying asset code (e.g., "510050" for 50ETF).
        source: Specific data source to use.

    Returns:
        DataFrame with columns:
        - symbol: Option contract symbol
        - name: Contract name
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
        >>> df = fv.list_cn_option_contracts("510050")
        >>> print(df.head())
    """
    from finvista._fetchers.adapters.registry import register_all_sources

    register_all_sources()

    if source:
        from finvista._fetchers.adapters.eastmoney import eastmoney_adapter

        df = eastmoney_adapter.fetch_option_list(underlying=underlying)
        df.attrs["source"] = source
    else:
        df, _ = source_manager.fetch_with_fallback(
            data_type="cn_option_list",
            underlying=underlying,
        )

    return df


@cached(ttl=10)
def get_cn_option_quote(
    symbol: str,
    source: str | None = None,
) -> pd.DataFrame:
    """
    Get real-time option quote.

    Args:
        symbol: Option contract symbol.
        source: Specific data source to use.

    Returns:
        DataFrame with real-time quote data.

    Example:
        >>> import finvista as fv
        >>> df = fv.get_cn_option_quote("10004456")
        >>> print(df)
    """
    if not symbol:
        raise ValidationError("Symbol cannot be empty", param_name="symbol")

    from finvista._fetchers.adapters.eastmoney import eastmoney_adapter

    df = eastmoney_adapter.fetch_option_list()
    df = df[df["symbol"] == symbol]

    if df.empty:
        from finvista._core.exceptions import DataNotFoundError
        raise DataNotFoundError(f"No option data found for {symbol}")

    return df


@cached(ttl=60)
def get_cn_option_daily(
    symbol: str,
    start_date: DateLike | None = None,
    end_date: DateLike | None = None,
    source: str | None = None,
) -> pd.DataFrame:
    """
    Get daily option data.

    Args:
        symbol: Option contract symbol.
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
        >>> df = fv.get_cn_option_daily("10004456", start_date="2024-01-01")
        >>> print(df.head())
    """
    if not symbol:
        raise ValidationError("Symbol cannot be empty", param_name="symbol")

    from finvista._fetchers.adapters.registry import register_all_sources

    register_all_sources()

    if source:
        from finvista._fetchers.adapters.eastmoney import eastmoney_adapter

        df = eastmoney_adapter.fetch_option_daily(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
        )
        df.attrs["source"] = source
    else:
        df, _ = source_manager.fetch_with_fallback(
            data_type="cn_option_daily",
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
        )

    return df
