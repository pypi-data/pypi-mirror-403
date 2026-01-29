"""
China futures data module.

This module provides functions to fetch futures data including
contract lists, daily prices, and position rankings.

Example:
    >>> import finvista as fv
    >>> df = fv.list_cn_futures_symbols()
    >>> print(df.head())
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

import pandas as pd

from finvista._core.exceptions import ValidationError
from finvista._core.types import DateLike
from finvista._fetchers.cache import cached
from finvista._fetchers.source_manager import source_manager


@cached(ttl=300)
def list_cn_futures_symbols(
    exchange: Literal["all", "SHFE", "DCE", "CZCE", "CFFEX", "INE"] = "all",
    source: str | None = None,
) -> pd.DataFrame:
    """
    Get list of all futures contracts.

    Args:
        exchange: Exchange filter:
            - "all": All exchanges
            - "SHFE": Shanghai Futures Exchange (上海期货交易所)
            - "DCE": Dalian Commodity Exchange (大连商品交易所)
            - "CZCE": Zhengzhou Commodity Exchange (郑州商品交易所)
            - "CFFEX": China Financial Futures Exchange (中国金融期货交易所)
            - "INE": Shanghai International Energy Exchange (上海国际能源交易中心)
        source: Specific data source to use.

    Returns:
        DataFrame with columns:
        - symbol: Contract symbol
        - name: Contract name
        - exchange: Exchange code
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
        >>> # Get all futures contracts
        >>> df = fv.list_cn_futures_symbols()
        >>> print(df.head())

        >>> # Get CFFEX contracts only
        >>> df = fv.list_cn_futures_symbols(exchange="CFFEX")
    """
    from finvista._fetchers.adapters.registry import register_all_sources

    register_all_sources()

    if source:
        from finvista._fetchers.adapters.eastmoney import eastmoney_adapter

        df = eastmoney_adapter.fetch_futures_list(exchange=exchange)
        df.attrs["source"] = source
    else:
        df, _ = source_manager.fetch_with_fallback(
            data_type="cn_futures_list",
            exchange=exchange,
        )

    return df


@cached(ttl=60)
def get_cn_futures_daily(
    symbol: str,
    start_date: DateLike | None = None,
    end_date: DateLike | None = None,
    source: str | None = None,
) -> pd.DataFrame:
    """
    Get daily futures data.

    Args:
        symbol: Futures contract symbol (e.g., "IF2401", "AU2406").
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
        - open_interest: Open interest

    Example:
        >>> import finvista as fv
        >>> df = fv.get_cn_futures_daily("IF2401", start_date="2024-01-01")
        >>> print(df.head())
    """
    if not symbol:
        raise ValidationError("Symbol cannot be empty", param_name="symbol")

    from finvista._fetchers.adapters.registry import register_all_sources

    register_all_sources()

    if source:
        from finvista._fetchers.adapters.eastmoney import eastmoney_adapter

        df = eastmoney_adapter.fetch_futures_daily(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
        )
        df.attrs["source"] = source
    else:
        df, _ = source_manager.fetch_with_fallback(
            data_type="cn_futures_daily",
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
        )

    return df


@cached(ttl=300)
def get_cn_futures_positions(
    symbol: str,
    date: DateLike | None = None,
    source: str | None = None,
) -> pd.DataFrame:
    """
    Get futures position ranking data.

    Args:
        symbol: Futures contract base symbol (e.g., "IF", "AU").
        date: Date to query (YYYY-MM-DD).
        source: Specific data source to use.

    Returns:
        DataFrame with columns:
        - date: Trading date
        - contract: Contract code
        - rank: Ranking
        - member_name: Member name
        - long_volume: Long position volume
        - long_change: Long position change
        - short_volume: Short position volume
        - short_change: Short position change

    Example:
        >>> import finvista as fv
        >>> df = fv.get_cn_futures_positions("IF", date="2024-01-15")
        >>> print(df.head())
    """
    if not symbol:
        raise ValidationError("Symbol cannot be empty", param_name="symbol")

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

        df = eastmoney_adapter.fetch_futures_positions(symbol=symbol, date=date_str)
        df.attrs["source"] = source
    else:
        df, _ = source_manager.fetch_with_fallback(
            data_type="cn_futures_positions",
            symbol=symbol,
            date=date_str,
        )

    return df
