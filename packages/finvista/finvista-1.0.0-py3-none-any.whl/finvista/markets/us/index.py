"""
US market index data module.

This module provides US market index data.

Example:
    >>> import finvista as fv
    >>> df = fv.get_us_index_daily(".DJI")  # Dow Jones
"""

from __future__ import annotations

import pandas as pd

from finvista._core.types import DateLike


def get_us_index_daily(
    symbol: str = ".DJI",
    start_date: DateLike | None = None,
    end_date: DateLike | None = None,
) -> pd.DataFrame:
    """
    Get US index historical data.

    Args:
        symbol: Index symbol, options:
            - ".DJI": Dow Jones Industrial Average
            - ".IXIC": NASDAQ Composite
            - ".INX": S&P 500
        start_date: Start date (YYYY-MM-DD format or date object).
        end_date: End date (YYYY-MM-DD format or date object).

    Returns:
        DataFrame with columns: date, open, high, low, close, volume

    Raises:
        ValidationError: If symbol is invalid.

    Example:
        >>> import finvista as fv
        >>> df = fv.get_us_index_daily(".DJI", start_date="2024-01-01")
        >>> print(df.tail())
    """
    from finvista._fetchers.adapters.sina import sina_adapter

    return sina_adapter.fetch_us_index_daily(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
    )
