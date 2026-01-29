"""
Macroeconomic data module.

This module provides access to macroeconomic data from various countries
including GDP, CPI, PPI, PMI, and other economic indicators.
"""

from finvista.macro.china import (
    get_cn_macro_cpi,
    get_cn_macro_gdp,
    get_cn_macro_money_supply,
    get_cn_macro_pmi,
    get_cn_macro_ppi,
    get_cn_macro_social_financing,
)

__all__ = [
    # China Macro
    "get_cn_macro_gdp",
    "get_cn_macro_cpi",
    "get_cn_macro_ppi",
    "get_cn_macro_pmi",
    "get_cn_macro_money_supply",
    "get_cn_macro_social_financing",
]
