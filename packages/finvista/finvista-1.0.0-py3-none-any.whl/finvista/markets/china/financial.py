"""
China A-share financial data module.

This module provides functions to fetch financial statement data
including income statements, balance sheets, cash flow statements,
performance forecasts, and dividend history.

Example:
    >>> import finvista as fv
    >>> df = fv.get_cn_income_statement("000001")
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
def get_cn_income_statement(
    symbol: str,
    period: Literal["yearly", "quarterly"] = "yearly",
    source: str | None = None,
) -> pd.DataFrame:
    """
    Get income statement data for a China A-share stock.

    Args:
        symbol: Stock symbol (e.g., "000001" for Ping An Bank).
        period: Report period ('yearly' or 'quarterly').
        source: Specific data source to use.

    Returns:
        DataFrame with columns:
        - report_date: Report date
        - revenue: Total operating revenue
        - operating_cost: Total operating cost
        - operating_profit: Operating profit
        - total_profit: Total profit
        - net_profit: Net profit
        - net_profit_excl_nr: Net profit excluding non-recurring items
        - eps: Basic earnings per share
        - eps_diluted: Diluted earnings per share

    Example:
        >>> import finvista as fv
        >>> df = fv.get_cn_income_statement("000001", period="yearly")
        >>> print(df.head())
    """
    symbol = _validate_symbol(symbol)

    from finvista._fetchers.adapters.registry import register_all_sources

    register_all_sources()

    if source:
        from finvista._fetchers.adapters.eastmoney import eastmoney_adapter

        df = eastmoney_adapter.fetch_income_statement(symbol=symbol, period=period)
        df.attrs["source"] = source
    else:
        df, _ = source_manager.fetch_with_fallback(
            data_type="cn_income_statement",
            symbol=symbol,
            period=period,
        )

    return df


@cached(ttl=3600)
def get_cn_balance_sheet(
    symbol: str,
    period: Literal["yearly", "quarterly"] = "yearly",
    source: str | None = None,
) -> pd.DataFrame:
    """
    Get balance sheet data for a China A-share stock.

    Args:
        symbol: Stock symbol (e.g., "000001" for Ping An Bank).
        period: Report period ('yearly' or 'quarterly').
        source: Specific data source to use.

    Returns:
        DataFrame with columns:
        - report_date: Report date
        - total_assets: Total assets
        - total_liab: Total liabilities
        - total_equity: Total equity
        - total_current_assets: Total current assets
        - total_noncurrent_assets: Total non-current assets
        - total_current_liab: Total current liabilities
        - total_noncurrent_liab: Total non-current liabilities
        - cash: Cash and cash equivalents
        - accounts_recv: Accounts receivable
        - inventory: Inventory
        - fixed_assets: Fixed assets

    Example:
        >>> import finvista as fv
        >>> df = fv.get_cn_balance_sheet("000001")
        >>> print(df.head())
    """
    symbol = _validate_symbol(symbol)

    from finvista._fetchers.adapters.registry import register_all_sources

    register_all_sources()

    if source:
        from finvista._fetchers.adapters.eastmoney import eastmoney_adapter

        df = eastmoney_adapter.fetch_balance_sheet(symbol=symbol, period=period)
        df.attrs["source"] = source
    else:
        df, _ = source_manager.fetch_with_fallback(
            data_type="cn_balance_sheet",
            symbol=symbol,
            period=period,
        )

    return df


@cached(ttl=3600)
def get_cn_cash_flow(
    symbol: str,
    period: Literal["yearly", "quarterly"] = "yearly",
    source: str | None = None,
) -> pd.DataFrame:
    """
    Get cash flow statement data for a China A-share stock.

    Args:
        symbol: Stock symbol (e.g., "000001" for Ping An Bank).
        period: Report period ('yearly' or 'quarterly').
        source: Specific data source to use.

    Returns:
        DataFrame with columns:
        - report_date: Report date
        - operating_cashflow: Net cash flow from operating activities
        - investing_cashflow: Net cash flow from investing activities
        - financing_cashflow: Net cash flow from financing activities
        - net_cash_change: Net increase in cash
        - cash_end: Cash at end of period

    Example:
        >>> import finvista as fv
        >>> df = fv.get_cn_cash_flow("000001")
        >>> print(df.head())
    """
    symbol = _validate_symbol(symbol)

    from finvista._fetchers.adapters.registry import register_all_sources

    register_all_sources()

    if source:
        from finvista._fetchers.adapters.eastmoney import eastmoney_adapter

        df = eastmoney_adapter.fetch_cash_flow(symbol=symbol, period=period)
        df.attrs["source"] = source
    else:
        df, _ = source_manager.fetch_with_fallback(
            data_type="cn_cash_flow",
            symbol=symbol,
            period=period,
        )

    return df


@cached(ttl=300)
def get_cn_performance_forecast(
    date: DateLike | None = None,
    source: str | None = None,
) -> pd.DataFrame:
    """
    Get performance forecast data for China A-share stocks.

    Args:
        date: Date to filter (YYYY-MM-DD). If None, returns latest forecasts.
        source: Specific data source to use.

    Returns:
        DataFrame with columns:
        - symbol: Stock symbol
        - name: Stock name
        - notice_date: Announcement date
        - report_date: Report period
        - forecast_type: Forecast type
        - net_profit_min: Minimum net profit forecast
        - net_profit_max: Maximum net profit forecast
        - change_pct_min: Minimum change percentage
        - change_pct_max: Maximum change percentage
        - forecast_content: Forecast description

    Example:
        >>> import finvista as fv
        >>> df = fv.get_cn_performance_forecast()
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

        df = eastmoney_adapter.fetch_performance_forecast(date=date_str)
        df.attrs["source"] = source
    else:
        df, _ = source_manager.fetch_with_fallback(
            data_type="cn_performance_forecast",
            date=date_str,
        )

    return df


@cached(ttl=3600)
def get_cn_dividend_history(
    symbol: str,
    source: str | None = None,
) -> pd.DataFrame:
    """
    Get dividend history for a China A-share stock.

    Args:
        symbol: Stock symbol (e.g., "000001" for Ping An Bank).
        source: Specific data source to use.

    Returns:
        DataFrame with columns:
        - symbol: Stock symbol
        - report_date: Report period
        - plan: Dividend plan description
        - dividend_per_share: Cash dividend per share
        - bonus_shares_ratio: Bonus shares ratio
        - ex_dividend_date: Ex-dividend date
        - record_date: Record date
        - pay_date: Payment date

    Example:
        >>> import finvista as fv
        >>> df = fv.get_cn_dividend_history("000001")
        >>> print(df.head())
    """
    symbol = _validate_symbol(symbol)

    from finvista._fetchers.adapters.registry import register_all_sources

    register_all_sources()

    if source:
        from finvista._fetchers.adapters.eastmoney import eastmoney_adapter

        df = eastmoney_adapter.fetch_dividend_history(symbol=symbol)
        df.attrs["source"] = source
    else:
        df, _ = source_manager.fetch_with_fallback(
            data_type="cn_dividend_history",
            symbol=symbol,
        )

    return df
