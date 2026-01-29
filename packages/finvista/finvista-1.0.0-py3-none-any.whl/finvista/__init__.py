"""
FinVista - A powerful Python library for global financial data.

FinVista provides easy access to financial market data from multiple
sources with automatic failover, caching, and rate limiting.

Quick Start:
    >>> import finvista as fv
    >>>
    >>> # Get A-share daily data
    >>> df = fv.get_cn_stock_daily("000001", start_date="2024-01-01")
    >>>
    >>> # Get real-time quotes
    >>> df = fv.get_cn_stock_quote(["000001", "600519"])
    >>>
    >>> # List all stocks
    >>> df = fv.list_cn_stock_symbols(market="main")

Configuration:
    >>> # Set proxy
    >>> fv.set_proxies({"http": "http://127.0.0.1:7890"})
    >>>
    >>> # Set timeout
    >>> fv.set_timeout(60)
    >>>
    >>> # Configure cache
    >>> fv.set_cache(enabled=True, ttl=300)
    >>>
    >>> # Check data source health
    >>> health = fv.get_source_health()

For more information, visit: https://github.com/finvista/finvista
"""

# =============================================================================
# Configuration Functions
# =============================================================================
from finvista._core.config import (
    config,
    get_source_health,
    reset_source_circuit,
    set_cache,
    set_proxies,
    set_source_priority,
    set_timeout,
)

# =============================================================================
# Exceptions
# =============================================================================
from finvista._core.exceptions import (
    AllSourcesFailedError,
    AllSourcesUnavailableError,
    APIError,
    ConfigError,
    DataError,
    DataNotFoundError,
    DataParsingError,
    DateRangeError,
    FinVistaError,
    NetworkError,
    RateLimitError,
    SourceError,
    SymbolNotFoundError,
    ValidationError,
)

# =============================================================================
# Register data sources on import
# =============================================================================
from finvista._fetchers.adapters.registry import (
    register_all_sources as _register_sources,
)
from finvista._version import __version__

# =============================================================================
# Macroeconomic Data - China
# =============================================================================
from finvista.macro.china import (
    get_cn_macro_cpi,
    get_cn_macro_gdp,
    get_cn_macro_money_supply,
    get_cn_macro_pmi,
    get_cn_macro_ppi,
    get_cn_macro_social_financing,
)

# =============================================================================
# China Market - Convertible Bonds
# =============================================================================
from finvista.markets.china.convertible import (
    get_cn_convertible_daily,
    get_cn_convertible_info,
    list_cn_convertible_symbols,
)

# =============================================================================
# China Market - ETF
# =============================================================================
from finvista.markets.china.etf import (
    get_cn_etf_premium_discount,
    get_cn_etf_share_change,
)

# =============================================================================
# China Market - Financial Data
# =============================================================================
from finvista.markets.china.financial import (
    get_cn_balance_sheet,
    get_cn_cash_flow,
    get_cn_dividend_history,
    get_cn_income_statement,
    get_cn_performance_forecast,
)

# =============================================================================
# China Market - Funds
# =============================================================================
from finvista.markets.china.fund import (
    get_cn_fund_info,
    get_cn_fund_nav,
    get_cn_fund_quote,
    list_cn_fund_symbols,
    search_cn_fund,
)

# =============================================================================
# China Market - Futures
# =============================================================================
from finvista.markets.china.futures import (
    get_cn_futures_daily,
    get_cn_futures_positions,
    list_cn_futures_symbols,
)

# =============================================================================
# China Market - Indices
# =============================================================================
from finvista.markets.china.index import (
    get_cn_index_constituents,
    get_cn_index_daily,
    get_cn_index_quote,
    get_cn_index_weights,
    list_cn_major_indices,
)

# =============================================================================
# China Market - Industry (Shenwan)
# =============================================================================
from finvista.markets.china.industry import (
    get_sw_index_analysis,
    get_sw_index_daily,
    get_sw_index_realtime,
)

# =============================================================================
# China Market - Dragon Tiger List (龙虎榜)
# =============================================================================
from finvista.markets.china.lhb import (
    get_cn_lhb_detail,
    get_cn_lhb_institution,
    get_cn_lhb_list,
)

# =============================================================================
# China Market - Minute Data
# =============================================================================
from finvista.markets.china.minute import (
    get_cn_stock_minute,
)

# =============================================================================
# China Market - Money Flow
# =============================================================================
from finvista.markets.china.moneyflow import (
    get_cn_industry_moneyflow,
    get_cn_stock_moneyflow,
    get_cn_stock_moneyflow_realtime,
)

# =============================================================================
# China Market - Options
# =============================================================================
from finvista.markets.china.option import (
    get_cn_option_daily,
    get_cn_option_quote,
    list_cn_option_contracts,
)

# =============================================================================
# China Market - Shareholders
# =============================================================================
from finvista.markets.china.shareholder import (
    get_cn_stock_pledge,
    get_cn_stock_unlock_schedule,
    get_cn_top_shareholders,
)

# =============================================================================
# China Market - Stocks
# =============================================================================
from finvista.markets.china.stock import (
    get_cn_stock_daily,
    get_cn_stock_quote,
    list_cn_stock_symbols,
    search_cn_stock,
)

# =============================================================================
# China Market - Valuation
# =============================================================================
from finvista.markets.china.valuation import (
    get_all_a_pb,
    get_index_pb,
    get_index_pe,
)

# =============================================================================
# Global Market - Forex
# =============================================================================
from finvista.markets.global_.forex import (
    get_exchange_rate,
    get_exchange_rate_history,
)

# =============================================================================
# Hong Kong Market - Indices
# =============================================================================
from finvista.markets.hk.index import get_hk_index_daily

# =============================================================================
# US Market - Indices
# =============================================================================
from finvista.markets.us.index import get_us_index_daily

# =============================================================================
# US Market - Stocks
# =============================================================================
from finvista.markets.us.stock import (
    get_us_stock_daily,
    get_us_stock_info,
    get_us_stock_quote,
    search_us_stock,
)

_register_sources()

# =============================================================================
# Public API
# =============================================================================
__all__ = [
    # Version
    "__version__",
    # Configuration
    "config",
    "set_proxies",
    "set_timeout",
    "set_cache",
    "set_source_priority",
    "get_source_health",
    "reset_source_circuit",
    # Exceptions
    "FinVistaError",
    "ConfigError",
    "NetworkError",
    "APIError",
    "RateLimitError",
    "DataError",
    "DataNotFoundError",
    "DataParsingError",
    "ValidationError",
    "SymbolNotFoundError",
    "DateRangeError",
    "SourceError",
    "AllSourcesUnavailableError",
    "AllSourcesFailedError",
    # China Stocks
    "get_cn_stock_daily",
    "get_cn_stock_quote",
    "list_cn_stock_symbols",
    "search_cn_stock",
    # China Indices
    "get_cn_index_daily",
    "get_cn_index_quote",
    "list_cn_major_indices",
    "get_cn_index_constituents",
    "get_cn_index_weights",
    # China Funds
    "get_cn_fund_nav",
    "get_cn_fund_quote",
    "list_cn_fund_symbols",
    "search_cn_fund",
    "get_cn_fund_info",
    # US Stocks
    "get_us_stock_daily",
    "get_us_stock_quote",
    "get_us_stock_info",
    "search_us_stock",
    # US Indices
    "get_us_index_daily",
    # HK Indices
    "get_hk_index_daily",
    # China Valuation
    "get_index_pe",
    "get_index_pb",
    "get_all_a_pb",
    # China Industry (Shenwan)
    "get_sw_index_daily",
    "get_sw_index_realtime",
    "get_sw_index_analysis",
    # China Financial Data
    "get_cn_income_statement",
    "get_cn_balance_sheet",
    "get_cn_cash_flow",
    "get_cn_performance_forecast",
    "get_cn_dividend_history",
    # China Money Flow
    "get_cn_stock_moneyflow",
    "get_cn_stock_moneyflow_realtime",
    "get_cn_industry_moneyflow",
    # China Minute Data
    "get_cn_stock_minute",
    # China Futures
    "list_cn_futures_symbols",
    "get_cn_futures_daily",
    "get_cn_futures_positions",
    # China Convertible Bonds
    "list_cn_convertible_symbols",
    "get_cn_convertible_daily",
    "get_cn_convertible_info",
    # China Dragon Tiger List
    "get_cn_lhb_list",
    "get_cn_lhb_detail",
    "get_cn_lhb_institution",
    # China Options
    "list_cn_option_contracts",
    "get_cn_option_quote",
    "get_cn_option_daily",
    # China Shareholders
    "get_cn_top_shareholders",
    "get_cn_stock_pledge",
    "get_cn_stock_unlock_schedule",
    # China ETF
    "get_cn_etf_share_change",
    "get_cn_etf_premium_discount",
    # Global Forex
    "get_exchange_rate",
    "get_exchange_rate_history",
    # China Macroeconomic
    "get_cn_macro_gdp",
    "get_cn_macro_cpi",
    "get_cn_macro_ppi",
    "get_cn_macro_pmi",
    "get_cn_macro_money_supply",
    "get_cn_macro_social_financing",
]
