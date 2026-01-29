"""
Data source adapters for FinVista.

This module contains adapters for various financial data sources.
Each adapter handles the specifics of fetching and parsing data
from a particular source.
"""

from finvista._fetchers.adapters.base import BaseAdapter
from finvista._fetchers.adapters.registry import register_all_sources

__all__ = [
    "BaseAdapter",
    "register_all_sources",
]
