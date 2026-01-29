"""
China market industry data module.

This module provides Shenwan (申万) industry index data.
Data is sourced from Shenwan Research (申万宏源研究).

Example:
    >>> import finvista as fv
    >>> df = fv.get_sw_index_daily("801030")  # 基础化工
    >>> df = fv.get_sw_index_analysis("一级行业", "20240101", "20240115")
"""

from __future__ import annotations

import pandas as pd


def get_sw_index_daily(
    symbol: str = "801030",
    period: str = "day",
) -> pd.DataFrame:
    """
    Get Shenwan industry index historical data.

    Args:
        symbol: Shenwan index code (e.g., "801030" for 基础化工).
        period: Data period, options:
            - "day": Daily data (default)
            - "week": Weekly data
            - "month": Monthly data

    Returns:
        DataFrame with columns: 代码, 日期, 收盘, 开盘, 最高, 最低, 成交量, 成交额

    Example:
        >>> import finvista as fv
        >>> df = fv.get_sw_index_daily("801030")
        >>> print(df.tail())
    """
    from finvista._fetchers.adapters.shenwan import shenwan_adapter

    return shenwan_adapter.fetch_index_hist(symbol=symbol, period=period)


def get_sw_index_realtime(symbol: str = "一级行业") -> pd.DataFrame:
    """
    Get Shenwan industry index realtime data.

    Args:
        symbol: Index type, options:
            - "市场表征": Market indicators
            - "一级行业": Level 1 industries (default)
            - "二级行业": Level 2 industries
            - "风格指数": Style indices

    Returns:
        DataFrame with columns: 指数代码, 指数名称, 昨收盘, 今开盘, 最新价,
                               成交额, 成交量, 最高价, 最低价

    Example:
        >>> import finvista as fv
        >>> df = fv.get_sw_index_realtime("一级行业")
        >>> print(df)
    """
    from finvista._fetchers.adapters.shenwan import shenwan_adapter

    return shenwan_adapter.fetch_index_realtime(symbol=symbol)


def get_sw_index_analysis(
    symbol: str = "一级行业",
    start_date: str = "20240101",
    end_date: str = "20240115",
) -> pd.DataFrame:
    """
    Get Shenwan industry index daily analysis data.

    This provides detailed analysis including PE, PB, dividend yield, etc.

    Args:
        symbol: Index type, options:
            - "市场表征": Market indicators
            - "一级行业": Level 1 industries (default)
            - "二级行业": Level 2 industries
            - "风格指数": Style indices
        start_date: Start date in YYYYMMDD format.
        end_date: End date in YYYYMMDD format.

    Returns:
        DataFrame with columns: 指数代码, 指数名称, 发布日期, 收盘指数,
                               成交量, 涨跌幅, 换手率, 市盈率, 市净率,
                               均价, 成交额占比, 流通市值, 平均流通市值, 股息率

    Example:
        >>> import finvista as fv
        >>> df = fv.get_sw_index_analysis("一级行业", "20240101", "20240115")
        >>> print(df.head())
    """
    from finvista._fetchers.adapters.shenwan import shenwan_adapter

    return shenwan_adapter.fetch_index_analysis_daily(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
    )
