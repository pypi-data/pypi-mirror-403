"""
China ETF enhanced data module.

This module provides functions to fetch ETF-specific data including
share changes and premium/discount data.

Example:
    >>> import finvista as fv
    >>> df = fv.get_cn_etf_share_change("510050")
    >>> print(df.head())
"""

from __future__ import annotations

import pandas as pd

from finvista._core.exceptions import ValidationError
from finvista._fetchers.cache import cached
from finvista._fetchers.source_manager import source_manager


def _validate_symbol(symbol: str) -> str:
    """Validate and normalize an ETF symbol."""
    if not symbol:
        raise ValidationError("Symbol cannot be empty", param_name="symbol")

    symbol = symbol.upper().strip()
    for prefix in ["SH", "SZ", "."]:
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
def get_cn_etf_share_change(
    symbol: str,
    days: int = 30,
    source: str | None = None,
) -> pd.DataFrame:
    """
    Get ETF share change data.

    Args:
        symbol: ETF symbol (e.g., "510050" for 50ETF).
        days: Number of days of data.
        source: Specific data source to use.

    Returns:
        DataFrame with columns:
        - date: Trading date
        - symbol: ETF symbol
        - shares: Total shares
        - shares_change: Share change
        - shares_change_pct: Share change percentage

    Example:
        >>> import finvista as fv
        >>> df = fv.get_cn_etf_share_change("510050", days=30)
        >>> print(df.head())
    """
    symbol = _validate_symbol(symbol)

    from finvista._fetchers.adapters.registry import register_all_sources

    register_all_sources()

    if source:
        from finvista._fetchers.adapters.eastmoney import eastmoney_adapter

        df = eastmoney_adapter.fetch_etf_share_change(symbol=symbol, days=days)
        df.attrs["source"] = source
    else:
        df, _ = source_manager.fetch_with_fallback(
            data_type="cn_etf_share_change",
            symbol=symbol,
            days=days,
        )

    return df


@cached(ttl=300)
def get_cn_etf_premium_discount(
    symbol: str,
    source: str | None = None,
) -> pd.DataFrame:
    """
    Get ETF premium/discount data.

    Args:
        symbol: ETF symbol (e.g., "510050" for 50ETF).
        source: Specific data source to use.

    Returns:
        DataFrame with columns:
        - date: Trading date
        - symbol: ETF symbol
        - price: Market price
        - nav: Net asset value
        - premium_rate: Premium/discount rate

    Example:
        >>> import finvista as fv
        >>> df = fv.get_cn_etf_premium_discount("510050")
        >>> print(df.head())
    """
    symbol = _validate_symbol(symbol)

    from finvista._fetchers.adapters.registry import register_all_sources

    register_all_sources()

    if source:
        from finvista._fetchers.adapters.eastmoney import eastmoney_adapter

        df = eastmoney_adapter.fetch_etf_premium_discount(symbol=symbol)
        df.attrs["source"] = source
    else:
        df, _ = source_manager.fetch_with_fallback(
            data_type="cn_etf_premium_discount",
            symbol=symbol,
        )

    return df
