"""
Hong Kong market index data module.

This module provides Hong Kong market index data.

Example:
    >>> import finvista as fv
    >>> df = fv.get_hk_index_daily("HSI")  # Hang Seng Index
"""

from __future__ import annotations

import pandas as pd

from finvista._core.types import DateLike


def get_hk_index_daily(
    symbol: str = "HSI",
    start_date: DateLike | None = None,
    end_date: DateLike | None = None,
) -> pd.DataFrame:
    """
    Get Hong Kong index historical data.

    Args:
        symbol: Index symbol, options:
            - "HSI": Hang Seng Index (恒生指数)
            - "HSTECH": Hang Seng Tech Index (恒生科技指数)
            - "HSCEI": Hang Seng China Enterprises Index (恒生国企指数)
        start_date: Start date (YYYY-MM-DD format or date object).
        end_date: End date (YYYY-MM-DD format or date object).

    Returns:
        DataFrame with columns: date, open, high, low, close, volume, amount

    Raises:
        ValidationError: If symbol is invalid.

    Example:
        >>> import finvista as fv
        >>> df = fv.get_hk_index_daily("HSI", start_date="2024-01-01")
        >>> print(df.tail())
    """
    from finvista._fetchers.adapters.eastmoney import eastmoney_adapter

    return eastmoney_adapter.fetch_hk_index_daily(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
    )
