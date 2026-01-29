"""
China A-share money flow data module.

This module provides functions to fetch money flow data including
individual stock money flow, industry money flow, and real-time data.

Example:
    >>> import finvista as fv
    >>> df = fv.get_cn_stock_moneyflow("000001")
    >>> print(df.head())
"""

from __future__ import annotations

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


@cached(ttl=60)
def get_cn_stock_moneyflow(
    symbol: str,
    days: int = 30,
    source: str | None = None,
) -> pd.DataFrame:
    """
    Get historical money flow data for a China A-share stock.

    Args:
        symbol: Stock symbol (e.g., "000001" for Ping An Bank).
        days: Number of days of data to fetch.
        source: Specific data source to use.

    Returns:
        DataFrame with columns:
        - date: Trading date
        - main_net_inflow: Main force net inflow (大单净流入)
        - small_net_inflow: Small order net inflow (小单净流入)
        - medium_net_inflow: Medium order net inflow (中单净流入)
        - large_net_inflow: Large order net inflow (大单净流入)
        - super_large_net_inflow: Super large order net inflow (超大单净流入)
        - main_net_inflow_pct: Main force net inflow percentage
        - close: Closing price
        - change_pct: Price change percentage

    Example:
        >>> import finvista as fv
        >>> df = fv.get_cn_stock_moneyflow("000001", days=30)
        >>> print(df.head())
    """
    symbol = _validate_symbol(symbol)

    from finvista._fetchers.adapters.registry import register_all_sources

    register_all_sources()

    if source:
        from finvista._fetchers.adapters.eastmoney import eastmoney_adapter

        df = eastmoney_adapter.fetch_stock_moneyflow(symbol=symbol, days=days)
        df.attrs["source"] = source
    else:
        df, _ = source_manager.fetch_with_fallback(
            data_type="cn_stock_moneyflow",
            symbol=symbol,
            days=days,
        )

    return df


@cached(ttl=10)
def get_cn_stock_moneyflow_realtime(
    symbol: str,
    source: str | None = None,
) -> pd.DataFrame:
    """
    Get real-time money flow data for a China A-share stock.

    Args:
        symbol: Stock symbol (e.g., "000001" for Ping An Bank).
        source: Specific data source to use.

    Returns:
        DataFrame with columns:
        - symbol: Stock symbol
        - main_net_inflow: Main force net inflow
        - main_net_inflow_pct: Main force net inflow percentage
        - super_large_inflow: Super large order inflow
        - super_large_outflow: Super large order outflow
        - super_large_net_inflow: Super large order net inflow
        - large_inflow: Large order inflow
        - large_outflow: Large order outflow
        - large_net_inflow: Large order net inflow
        - medium_inflow: Medium order inflow
        - medium_outflow: Medium order outflow
        - medium_net_inflow: Medium order net inflow
        - small_inflow: Small order inflow
        - small_outflow: Small order outflow
        - small_net_inflow: Small order net inflow

    Example:
        >>> import finvista as fv
        >>> df = fv.get_cn_stock_moneyflow_realtime("000001")
        >>> print(df)
    """
    symbol = _validate_symbol(symbol)

    from finvista._fetchers.adapters.registry import register_all_sources

    register_all_sources()

    if source:
        from finvista._fetchers.adapters.eastmoney import eastmoney_adapter

        df = eastmoney_adapter.fetch_stock_moneyflow_realtime(symbol=symbol)
        df.attrs["source"] = source
    else:
        df, _ = source_manager.fetch_with_fallback(
            data_type="cn_stock_moneyflow_realtime",
            symbol=symbol,
        )

    return df


@cached(ttl=60)
def get_cn_industry_moneyflow(
    date: DateLike | None = None,
    source: str | None = None,
) -> pd.DataFrame:
    """
    Get industry money flow data.

    Args:
        date: Date to filter (not used, always returns latest).
        source: Specific data source to use.

    Returns:
        DataFrame with columns:
        - code: Industry code
        - name: Industry name
        - price: Industry index price
        - change_pct: Price change percentage
        - main_net_inflow: Main force net inflow
        - main_net_inflow_pct: Main force net inflow percentage
        - super_large_net_inflow: Super large order net inflow
        - large_net_inflow: Large order net inflow
        - medium_net_inflow: Medium order net inflow
        - small_net_inflow: Small order net inflow

    Example:
        >>> import finvista as fv
        >>> df = fv.get_cn_industry_moneyflow()
        >>> print(df.head())
    """
    from finvista._fetchers.adapters.registry import register_all_sources

    register_all_sources()

    if source:
        from finvista._fetchers.adapters.eastmoney import eastmoney_adapter

        df = eastmoney_adapter.fetch_industry_moneyflow()
        df.attrs["source"] = source
    else:
        df, _ = source_manager.fetch_with_fallback(
            data_type="cn_industry_moneyflow",
        )

    return df
