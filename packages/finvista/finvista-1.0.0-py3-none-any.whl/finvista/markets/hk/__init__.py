"""
Hong Kong market data module.

This module provides access to Hong Kong financial market data including:
- Hang Seng Index
- Hang Seng Tech Index
- HK stocks
"""

from finvista.markets.hk.index import get_hk_index_daily

__all__ = [
    "get_hk_index_daily",
]
