"""
China market data module.

This module provides access to Chinese financial market data including:
- A-share stocks (Shanghai, Shenzhen, Beijing exchanges)
- Funds (mutual funds, ETFs)
- Futures
- Bonds
- Indices
- Financial statements
- Money flow
- Dragon tiger list
"""

from finvista.markets.china.convertible import (
    get_cn_convertible_daily,
    get_cn_convertible_info,
    list_cn_convertible_symbols,
)
from finvista.markets.china.etf import (
    get_cn_etf_premium_discount,
    get_cn_etf_share_change,
)
from finvista.markets.china.financial import (
    get_cn_balance_sheet,
    get_cn_cash_flow,
    get_cn_dividend_history,
    get_cn_income_statement,
    get_cn_performance_forecast,
)
from finvista.markets.china.fund import (
    get_cn_fund_info,
    get_cn_fund_nav,
    get_cn_fund_quote,
    list_cn_fund_symbols,
    search_cn_fund,
)
from finvista.markets.china.futures import (
    get_cn_futures_daily,
    get_cn_futures_positions,
    list_cn_futures_symbols,
)
from finvista.markets.china.index import (
    get_cn_index_constituents,
    get_cn_index_daily,
    get_cn_index_quote,
    get_cn_index_weights,
    list_cn_major_indices,
)
from finvista.markets.china.industry import (
    get_sw_index_analysis,
    get_sw_index_daily,
    get_sw_index_realtime,
)
from finvista.markets.china.lhb import (
    get_cn_lhb_detail,
    get_cn_lhb_institution,
    get_cn_lhb_list,
)
from finvista.markets.china.minute import (
    get_cn_stock_minute,
)
from finvista.markets.china.moneyflow import (
    get_cn_industry_moneyflow,
    get_cn_stock_moneyflow,
    get_cn_stock_moneyflow_realtime,
)
from finvista.markets.china.option import (
    get_cn_option_daily,
    get_cn_option_quote,
    list_cn_option_contracts,
)
from finvista.markets.china.shareholder import (
    get_cn_stock_pledge,
    get_cn_stock_unlock_schedule,
    get_cn_top_shareholders,
)
from finvista.markets.china.stock import (
    get_cn_stock_daily,
    get_cn_stock_quote,
    list_cn_stock_symbols,
    search_cn_stock,
)
from finvista.markets.china.valuation import (
    get_all_a_pb,
    get_index_pb,
    get_index_pe,
)

__all__ = [
    # Stock
    "get_cn_stock_daily",
    "get_cn_stock_quote",
    "list_cn_stock_symbols",
    "search_cn_stock",
    # Index
    "get_cn_index_daily",
    "get_cn_index_quote",
    "list_cn_major_indices",
    "get_cn_index_constituents",
    "get_cn_index_weights",
    # Fund
    "get_cn_fund_nav",
    "get_cn_fund_quote",
    "list_cn_fund_symbols",
    "search_cn_fund",
    "get_cn_fund_info",
    # Valuation
    "get_index_pe",
    "get_index_pb",
    "get_all_a_pb",
    # Industry
    "get_sw_index_daily",
    "get_sw_index_realtime",
    "get_sw_index_analysis",
    # Financial
    "get_cn_income_statement",
    "get_cn_balance_sheet",
    "get_cn_cash_flow",
    "get_cn_performance_forecast",
    "get_cn_dividend_history",
    # Money Flow
    "get_cn_stock_moneyflow",
    "get_cn_stock_moneyflow_realtime",
    "get_cn_industry_moneyflow",
    # Minute
    "get_cn_stock_minute",
    # Futures
    "list_cn_futures_symbols",
    "get_cn_futures_daily",
    "get_cn_futures_positions",
    # Convertible Bond
    "list_cn_convertible_symbols",
    "get_cn_convertible_daily",
    "get_cn_convertible_info",
    # Dragon Tiger List
    "get_cn_lhb_list",
    "get_cn_lhb_detail",
    "get_cn_lhb_institution",
    # Option
    "list_cn_option_contracts",
    "get_cn_option_quote",
    "get_cn_option_daily",
    # Shareholder
    "get_cn_top_shareholders",
    "get_cn_stock_pledge",
    "get_cn_stock_unlock_schedule",
    # ETF
    "get_cn_etf_share_change",
    "get_cn_etf_premium_discount",
]
