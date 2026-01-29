"""
China fund data module.

This module provides functions to fetch Chinese fund data
including NAV history, fund information, and real-time estimates.

Example:
    >>> import finvista as fv
    >>> df = fv.get_cn_fund_nav("000001", start_date="2024-01-01")
    >>> print(df.head())
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

import pandas as pd

from finvista._core.exceptions import ValidationError
from finvista._core.types import DateLike
from finvista._fetchers.cache import cached
from finvista._fetchers.source_manager import source_manager

# Fund types
FUND_TYPES = {
    "all": "All funds",
    "stock": "Stock funds (股票型)",
    "mixed": "Mixed funds (混合型)",
    "bond": "Bond funds (债券型)",
    "index": "Index funds (指数型)",
    "qdii": "QDII funds",
    "money": "Money market funds (货币型)",
    "etf": "ETF funds",
}


def _validate_fund_symbol(symbol: str) -> str:
    """
    Validate and normalize a fund symbol.

    Args:
        symbol: Fund symbol to validate.

    Returns:
        Normalized symbol string.

    Raises:
        ValidationError: If symbol is invalid.
    """
    if not symbol:
        raise ValidationError("Symbol cannot be empty", param_name="symbol")

    symbol = symbol.strip()

    # Validate format (6 digits)
    if not symbol.isdigit() or len(symbol) != 6:
        raise ValidationError(
            f"Invalid fund symbol format: {symbol}. Expected 6 digits.",
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
    """
    start_str: str | None = None
    end_str: str | None = None

    if start_date is not None:
        if isinstance(start_date, str):
            start_str = start_date
        elif isinstance(start_date, (date, datetime)):
            start_str = start_date.strftime("%Y-%m-%d")

    if end_date is not None:
        if isinstance(end_date, str):
            end_str = end_date
        elif isinstance(end_date, (date, datetime)):
            end_str = end_date.strftime("%Y-%m-%d")

    return start_str, end_str


@cached(ttl=60)
def get_cn_fund_nav(
    symbol: str,
    start_date: DateLike | None = None,
    end_date: DateLike | None = None,
    source: str | None = None,
) -> pd.DataFrame:
    """
    Get NAV (Net Asset Value) history for a China fund.

    Args:
        symbol: Fund symbol (e.g., "000001" for Huaxia Growth).
        start_date: Start date (YYYY-MM-DD format or date object).
        end_date: End date (YYYY-MM-DD format or date object).
        source: Specific data source to use.

    Returns:
        DataFrame with columns:
        - date: Trading date
        - nav: Unit NAV (单位净值)
        - acc_nav: Accumulated NAV (累计净值)
        - daily_return: Daily return percentage

    Raises:
        ValidationError: If the symbol format is invalid.
        DataNotFoundError: If no data is found.
        AllSourcesFailedError: If all data sources fail.

    Example:
        >>> import finvista as fv
        >>> df = fv.get_cn_fund_nav("000001", start_date="2024-01-01")
        >>> print(df.head())
                 date    nav  acc_nav  daily_return
        0  2024-01-02  1.234    3.456          0.15
        1  2024-01-03  1.245    3.467          0.89
    """
    # Validate inputs
    symbol = _validate_fund_symbol(symbol)
    start_date_str, end_date_str = _validate_date_range(start_date, end_date)

    # Ensure sources are registered
    from finvista._fetchers.adapters.registry import register_all_sources

    register_all_sources()

    # Fetch data
    if source:
        from finvista._fetchers.adapters.tiantian import tiantian_adapter

        adapters = {"tiantian": tiantian_adapter}
        if source not in adapters:
            raise ValidationError(f"Unknown source: {source}", param_name="source")

        df = adapters[source].fetch_fund_nav(
            symbol=symbol,
            start_date=start_date_str,
            end_date=end_date_str,
        )
        df.attrs["source"] = source
    else:
        df, used_source = source_manager.fetch_with_fallback(
            data_type="cn_fund_nav",
            symbol=symbol,
            start_date=start_date_str,
            end_date=end_date_str,
        )

    return df


@cached(ttl=10)
def get_cn_fund_quote(
    symbol: str | list[str],
    source: str | None = None,
) -> pd.DataFrame:
    """
    Get real-time NAV estimates for China funds.

    The estimated NAV is calculated based on the fund's holdings
    and real-time market prices.

    Args:
        symbol: Single symbol or list of symbols.
        source: Specific data source to use.

    Returns:
        DataFrame with columns:
        - symbol: Fund symbol
        - name: Fund name
        - nav: Previous NAV
        - estimated_nav: Estimated current NAV
        - estimated_return: Estimated daily return %
        - update_time: Last update time

    Example:
        >>> import finvista as fv
        >>> df = fv.get_cn_fund_quote(["000001", "110011"])
        >>> print(df)
    """
    # Normalize to list
    if isinstance(symbol, str):
        symbols = [_validate_fund_symbol(symbol)]
    else:
        symbols = [_validate_fund_symbol(s) for s in symbol]

    # Ensure sources are registered
    from finvista._fetchers.adapters.registry import register_all_sources

    register_all_sources()

    if source:
        from finvista._fetchers.adapters.tiantian import tiantian_adapter

        df = tiantian_adapter.fetch_fund_quote(symbols)
        df.attrs["source"] = source
    else:
        df, _ = source_manager.fetch_with_fallback(
            data_type="cn_fund_quote",
            symbols=symbols,
        )

    return df


@cached(ttl=3600)
def list_cn_fund_symbols(
    fund_type: Literal["all", "stock", "mixed", "bond", "index", "qdii", "money", "etf"] = "all",
    source: str | None = None,
) -> pd.DataFrame:
    """
    Get list of all China fund symbols.

    Args:
        fund_type: Fund type filter:
            - "all": All funds
            - "stock": Stock funds (股票型)
            - "mixed": Mixed funds (混合型)
            - "bond": Bond funds (债券型)
            - "index": Index funds (指数型)
            - "qdii": QDII funds
            - "money": Money market funds (货币型)
            - "etf": ETF funds
        source: Specific data source to use.

    Returns:
        DataFrame with fund information:
        - symbol: Fund symbol
        - name: Fund name
        - abbr: Pinyin abbreviation
        - type: Fund type (English)
        - type_cn: Fund type (Chinese)

    Example:
        >>> import finvista as fv
        >>> # Get all ETF funds
        >>> df = fv.list_cn_fund_symbols(fund_type="etf")
        >>> print(f"Found {len(df)} ETF funds")
    """
    # Ensure sources are registered
    from finvista._fetchers.adapters.registry import register_all_sources

    register_all_sources()

    if source:
        from finvista._fetchers.adapters.tiantian import tiantian_adapter

        df = tiantian_adapter.fetch_fund_list(fund_type=fund_type)
        df.attrs["source"] = source
    else:
        df, _ = source_manager.fetch_with_fallback(
            data_type="cn_fund_list",
            fund_type=fund_type,
        )

    return df


def search_cn_fund(
    keyword: str,
    limit: int = 20,
) -> pd.DataFrame:
    """
    Search for funds by keyword.

    Args:
        keyword: Search keyword (symbol, name, or pinyin abbreviation).
        limit: Maximum number of results to return.

    Returns:
        DataFrame with matching funds.

    Example:
        >>> import finvista as fv
        >>> df = fv.search_cn_fund("沪深300")
        >>> print(df.head())
    """
    if not keyword:
        raise ValidationError("Keyword cannot be empty", param_name="keyword")

    # Get all funds and filter
    df = list_cn_fund_symbols()

    if len(df) == 0:
        return df

    # Search in symbol, name, and abbreviation
    mask = (
        df["symbol"].str.contains(keyword, case=False, na=False) |
        df["name"].str.contains(keyword, case=False, na=False) |
        df["abbr"].str.contains(keyword, case=False, na=False)
    )

    result = df[mask].head(limit).reset_index(drop=True)

    return result


def get_cn_fund_info(
    symbol: str,
) -> dict[str, Any]:
    """
    Get basic information for a fund.

    Args:
        symbol: Fund symbol.

    Returns:
        Dictionary with fund information:
        - symbol: Fund symbol
        - name: Fund name
        - type: Fund type
        - inception_date: Fund inception date
        - manager: Fund manager
        - company: Fund management company
        - benchmark: Performance benchmark

    Example:
        >>> import finvista as fv
        >>> info = fv.get_cn_fund_info("000001")
        >>> print(info["name"])
    """
    symbol = _validate_fund_symbol(symbol)

    from finvista._fetchers.adapters.tiantian import tiantian_adapter

    return tiantian_adapter.fetch_fund_info(symbol)
