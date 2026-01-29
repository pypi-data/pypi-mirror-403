"""
Global market data module.

This module provides access to global financial market data including:
- Foreign exchange rates
"""

from finvista.markets.global_.forex import (
    get_exchange_rate,
    get_exchange_rate_history,
)

__all__ = [
    # Forex
    "get_exchange_rate",
    "get_exchange_rate_history",
]
