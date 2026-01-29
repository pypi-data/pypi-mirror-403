"""
China market valuation data module.

This module provides valuation metrics (PE, PB, etc.) for Chinese market indices.
Data is sourced from Legugle (乐咕乐股).

Example:
    >>> import finvista as fv
    >>> df = fv.get_index_pe("000300")  # CSI 300 PE
    >>> df = fv.get_all_a_pb()  # All A-share PB
"""

from __future__ import annotations

import pandas as pd


def get_index_pe(
    symbol: str = "000300",
    indicator: str = "pe_ttm",
) -> pd.DataFrame:
    """
    Get index PE (Price-to-Earnings) historical data.

    Args:
        symbol: Index symbol, options:
            - "000300": CSI 300 (沪深300)
            - "000016": SSE 50 (上证50)
            - "000905": CSI 500 (中证500)
            - "000852": CSI 1000 (中证1000)
            - "399006": ChiNext (创业板指)
        indicator: PE indicator type, options:
            - "pe_ttm": PE TTM (default)
            - "pe_ttm_nonfinancial": PE TTM excluding financials
            - "pe_lyr": PE LYR

    Returns:
        DataFrame with columns: date, pe, index, quantile

    Raises:
        ValidationError: If symbol or indicator is invalid.

    Example:
        >>> import finvista as fv
        >>> df = fv.get_index_pe("000300")
        >>> print(df.tail())
    """
    from finvista._fetchers.adapters.legulegu import legulegu_adapter

    # Note: indicator parameter is reserved for future use
    _ = indicator  # Currently unused
    return legulegu_adapter.fetch_index_pe(symbol=symbol)


def get_index_pb(symbol: str = "000300") -> pd.DataFrame:
    """
    Get index PB (Price-to-Book) historical data.

    Args:
        symbol: Index symbol, options:
            - "000300": CSI 300 (沪深300)
            - "000016": SSE 50 (上证50)
            - "000905": CSI 500 (中证500)
            - "000852": CSI 1000 (中证1000)
            - "399006": ChiNext (创业板指)

    Returns:
        DataFrame with columns: date, pb, index, quantile

    Raises:
        ValidationError: If symbol is invalid.

    Example:
        >>> import finvista as fv
        >>> df = fv.get_index_pb("000300")
        >>> print(df.tail())
    """
    from finvista._fetchers.adapters.legulegu import legulegu_adapter

    return legulegu_adapter.fetch_index_pb(symbol=symbol)


def get_all_a_pb() -> pd.DataFrame:
    """
    Get all A-share market PB (Price-to-Book) historical data.

    This provides the overall PB level of the entire A-share market,
    useful for assessing market valuation.

    Returns:
        DataFrame with columns: date, pb, index

    Example:
        >>> import finvista as fv
        >>> df = fv.get_all_a_pb()
        >>> print(df.tail())
    """
    from finvista._fetchers.adapters.legulegu import legulegu_adapter

    return legulegu_adapter.fetch_all_a_pb()
