"""
Foreign exchange (Forex) data module.

This module provides functions to fetch exchange rate data including
real-time rates and historical data.

Example:
    >>> import finvista as fv
    >>> df = fv.get_exchange_rate("USD", "CNY")
    >>> print(df)
"""

from __future__ import annotations

import pandas as pd

from finvista._core.exceptions import ValidationError
from finvista._core.types import DateLike
from finvista._fetchers.cache import cached
from finvista._fetchers.source_manager import source_manager


@cached(ttl=60)
def get_exchange_rate(
    base: str = "USD",
    target: str = "CNY",
    source: str | None = None,
) -> pd.DataFrame:
    """
    Get current exchange rate.

    Args:
        base: Base currency code (e.g., "USD", "EUR", "GBP", "JPY", "HKD").
        target: Target currency code (currently only "CNY" is supported).
        source: Specific data source to use.

    Returns:
        DataFrame with columns:
        - base: Base currency
        - target: Target currency
        - rate: Current exchange rate
        - open: Opening rate
        - high: Highest rate
        - low: Lowest rate
        - pre_close: Previous close rate
        - change_pct: Change percentage

    Example:
        >>> import finvista as fv
        >>> df = fv.get_exchange_rate("USD", "CNY")
        >>> print(df)
    """
    if not base or not target:
        raise ValidationError("Base and target currencies are required")

    from finvista._fetchers.adapters.registry import register_all_sources

    register_all_sources()

    if source:
        from finvista._fetchers.adapters.eastmoney import eastmoney_adapter

        df = eastmoney_adapter.fetch_exchange_rate(base=base, target=target)
        df.attrs["source"] = source
    else:
        df, _ = source_manager.fetch_with_fallback(
            data_type="forex_rate",
            base=base,
            target=target,
        )

    return df


@cached(ttl=300)
def get_exchange_rate_history(
    base: str,
    target: str,
    start_date: DateLike | None = None,
    end_date: DateLike | None = None,
    source: str | None = None,
) -> pd.DataFrame:
    """
    Get historical exchange rate data.

    Args:
        base: Base currency code (e.g., "USD", "EUR", "GBP", "JPY", "HKD").
        target: Target currency code (currently only "CNY" is supported).
        start_date: Start date (YYYY-MM-DD format or date object).
        end_date: End date (YYYY-MM-DD format or date object).
        source: Specific data source to use.

    Returns:
        DataFrame with columns:
        - date: Trading date
        - base: Base currency
        - target: Target currency
        - open: Opening rate
        - high: Highest rate
        - low: Lowest rate
        - close: Closing rate

    Example:
        >>> import finvista as fv
        >>> df = fv.get_exchange_rate_history("USD", "CNY", start_date="2024-01-01")
        >>> print(df.head())
    """
    if not base or not target:
        raise ValidationError("Base and target currencies are required")

    from finvista._fetchers.adapters.registry import register_all_sources

    register_all_sources()

    if source:
        from finvista._fetchers.adapters.eastmoney import eastmoney_adapter

        df = eastmoney_adapter.fetch_exchange_rate_history(
            base=base,
            target=target,
            start_date=start_date,
            end_date=end_date,
        )
        df.attrs["source"] = source
    else:
        df, _ = source_manager.fetch_with_fallback(
            data_type="forex_rate_history",
            base=base,
            target=target,
            start_date=start_date,
            end_date=end_date,
        )

    return df
