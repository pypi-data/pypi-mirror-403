"""
Data source registration for FinVista.

This module registers all available data sources with the source manager,
setting up the failover chain for each data type.
"""

from __future__ import annotations

import logging

from finvista._fetchers.source_manager import source_manager

logger = logging.getLogger(__name__)

_registered = False


def register_all_sources() -> None:
    """
    Register all data sources with the source manager.

    This function is called automatically when the library is imported.
    It sets up the failover chain for each data type.
    """
    global _registered

    if _registered:
        return

    logger.debug("Registering data sources...")

    # Import adapters
    from finvista._fetchers.adapters.eastmoney import eastmoney_adapter
    from finvista._fetchers.adapters.sina import sina_adapter
    from finvista._fetchers.adapters.tencent import tencent_adapter
    from finvista._fetchers.adapters.tiantian import tiantian_adapter
    from finvista._fetchers.adapters.yahoo import yahoo_adapter

    # =========================================================================
    # China Stock Daily - with failover chain
    # =========================================================================
    source_manager.register(
        data_type="cn_stock_daily",
        name="eastmoney",
        fetcher=eastmoney_adapter.fetch_stock_daily,
        priority=0,
    )
    source_manager.register(
        data_type="cn_stock_daily",
        name="sina",
        fetcher=sina_adapter.fetch_stock_daily,
        priority=1,
    )
    source_manager.register(
        data_type="cn_stock_daily",
        name="tencent",
        fetcher=tencent_adapter.fetch_stock_daily,
        priority=2,
    )

    # =========================================================================
    # China Stock Quote (Real-time) - Sina is faster for quotes
    # =========================================================================
    source_manager.register(
        data_type="cn_stock_quote",
        name="sina",
        fetcher=sina_adapter.fetch_stock_quote,
        priority=0,
    )
    source_manager.register(
        data_type="cn_stock_quote",
        name="tencent",
        fetcher=tencent_adapter.fetch_stock_quote,
        priority=1,
    )
    source_manager.register(
        data_type="cn_stock_quote",
        name="eastmoney",
        fetcher=eastmoney_adapter.fetch_stock_quote,
        priority=2,
    )

    # =========================================================================
    # China Stock List
    # =========================================================================
    source_manager.register(
        data_type="cn_stock_list",
        name="eastmoney",
        fetcher=eastmoney_adapter.fetch_stock_list,
        priority=0,
    )
    source_manager.register(
        data_type="cn_stock_list",
        name="tencent",
        fetcher=tencent_adapter.fetch_stock_list,
        priority=1,
    )

    # =========================================================================
    # China Index Daily
    # =========================================================================
    source_manager.register(
        data_type="cn_index_daily",
        name="eastmoney",
        fetcher=eastmoney_adapter.fetch_index_daily,
        priority=0,
    )

    # =========================================================================
    # China Index Quote (Real-time)
    # =========================================================================
    source_manager.register(
        data_type="cn_index_quote",
        name="sina",
        fetcher=sina_adapter.fetch_index_quote,
        priority=0,
    )

    # =========================================================================
    # China Fund NAV
    # =========================================================================
    source_manager.register(
        data_type="cn_fund_nav",
        name="tiantian",
        fetcher=tiantian_adapter.fetch_fund_nav,
        priority=0,
    )

    # =========================================================================
    # China Fund List
    # =========================================================================
    source_manager.register(
        data_type="cn_fund_list",
        name="tiantian",
        fetcher=tiantian_adapter.fetch_fund_list,
        priority=0,
    )

    # =========================================================================
    # China Fund Quote (Real-time estimate)
    # =========================================================================
    source_manager.register(
        data_type="cn_fund_quote",
        name="tiantian",
        fetcher=tiantian_adapter.fetch_fund_quote,
        priority=0,
    )

    # =========================================================================
    # US Stock Daily
    # =========================================================================
    source_manager.register(
        data_type="us_stock_daily",
        name="yahoo",
        fetcher=yahoo_adapter.fetch_stock_daily,
        priority=0,
    )

    # =========================================================================
    # US Stock Quote (Real-time)
    # =========================================================================
    source_manager.register(
        data_type="us_stock_quote",
        name="yahoo",
        fetcher=yahoo_adapter.fetch_stock_quote,
        priority=0,
    )

    # =========================================================================
    # Financial Data - Income Statement, Balance Sheet, Cash Flow
    # =========================================================================
    source_manager.register(
        data_type="cn_income_statement",
        name="eastmoney",
        fetcher=eastmoney_adapter.fetch_income_statement,
        priority=0,
    )
    source_manager.register(
        data_type="cn_balance_sheet",
        name="eastmoney",
        fetcher=eastmoney_adapter.fetch_balance_sheet,
        priority=0,
    )
    source_manager.register(
        data_type="cn_cash_flow",
        name="eastmoney",
        fetcher=eastmoney_adapter.fetch_cash_flow,
        priority=0,
    )
    source_manager.register(
        data_type="cn_performance_forecast",
        name="eastmoney",
        fetcher=eastmoney_adapter.fetch_performance_forecast,
        priority=0,
    )
    source_manager.register(
        data_type="cn_dividend_history",
        name="eastmoney",
        fetcher=eastmoney_adapter.fetch_dividend_history,
        priority=0,
    )

    # =========================================================================
    # Money Flow Data
    # =========================================================================
    source_manager.register(
        data_type="cn_stock_moneyflow",
        name="eastmoney",
        fetcher=eastmoney_adapter.fetch_stock_moneyflow,
        priority=0,
    )
    source_manager.register(
        data_type="cn_stock_moneyflow_realtime",
        name="eastmoney",
        fetcher=eastmoney_adapter.fetch_stock_moneyflow_realtime,
        priority=0,
    )
    source_manager.register(
        data_type="cn_industry_moneyflow",
        name="eastmoney",
        fetcher=eastmoney_adapter.fetch_industry_moneyflow,
        priority=0,
    )

    # =========================================================================
    # Minute Data
    # =========================================================================
    source_manager.register(
        data_type="cn_stock_minute",
        name="eastmoney",
        fetcher=eastmoney_adapter.fetch_stock_minute,
        priority=0,
    )

    # =========================================================================
    # Futures Data
    # =========================================================================
    source_manager.register(
        data_type="cn_futures_list",
        name="eastmoney",
        fetcher=eastmoney_adapter.fetch_futures_list,
        priority=0,
    )
    source_manager.register(
        data_type="cn_futures_daily",
        name="eastmoney",
        fetcher=eastmoney_adapter.fetch_futures_daily,
        priority=0,
    )
    source_manager.register(
        data_type="cn_futures_positions",
        name="eastmoney",
        fetcher=eastmoney_adapter.fetch_futures_positions,
        priority=0,
    )

    # =========================================================================
    # Convertible Bond Data
    # =========================================================================
    source_manager.register(
        data_type="cn_convertible_list",
        name="eastmoney",
        fetcher=eastmoney_adapter.fetch_convertible_list,
        priority=0,
    )
    source_manager.register(
        data_type="cn_convertible_daily",
        name="eastmoney",
        fetcher=eastmoney_adapter.fetch_convertible_daily,
        priority=0,
    )

    # =========================================================================
    # Dragon Tiger List (龙虎榜)
    # =========================================================================
    source_manager.register(
        data_type="cn_lhb_list",
        name="eastmoney",
        fetcher=eastmoney_adapter.fetch_lhb_list,
        priority=0,
    )
    source_manager.register(
        data_type="cn_lhb_detail",
        name="eastmoney",
        fetcher=eastmoney_adapter.fetch_lhb_detail,
        priority=0,
    )
    source_manager.register(
        data_type="cn_lhb_institution",
        name="eastmoney",
        fetcher=eastmoney_adapter.fetch_lhb_institution,
        priority=0,
    )

    # =========================================================================
    # Option Data
    # =========================================================================
    source_manager.register(
        data_type="cn_option_list",
        name="eastmoney",
        fetcher=eastmoney_adapter.fetch_option_list,
        priority=0,
    )
    source_manager.register(
        data_type="cn_option_daily",
        name="eastmoney",
        fetcher=eastmoney_adapter.fetch_option_daily,
        priority=0,
    )

    # =========================================================================
    # Shareholder Data
    # =========================================================================
    source_manager.register(
        data_type="cn_top_shareholders",
        name="eastmoney",
        fetcher=eastmoney_adapter.fetch_top_shareholders,
        priority=0,
    )
    source_manager.register(
        data_type="cn_stock_pledge",
        name="eastmoney",
        fetcher=eastmoney_adapter.fetch_stock_pledge,
        priority=0,
    )
    source_manager.register(
        data_type="cn_stock_unlock",
        name="eastmoney",
        fetcher=eastmoney_adapter.fetch_stock_unlock,
        priority=0,
    )

    # =========================================================================
    # Index Constituents and Weights
    # =========================================================================
    source_manager.register(
        data_type="cn_index_constituents",
        name="eastmoney",
        fetcher=eastmoney_adapter.fetch_index_constituents,
        priority=0,
    )
    source_manager.register(
        data_type="cn_index_weights",
        name="eastmoney",
        fetcher=eastmoney_adapter.fetch_index_weights,
        priority=0,
    )

    # =========================================================================
    # ETF Data
    # =========================================================================
    source_manager.register(
        data_type="cn_etf_share_change",
        name="eastmoney",
        fetcher=eastmoney_adapter.fetch_etf_share_change,
        priority=0,
    )
    source_manager.register(
        data_type="cn_etf_premium_discount",
        name="eastmoney",
        fetcher=eastmoney_adapter.fetch_etf_premium_discount,
        priority=0,
    )

    # =========================================================================
    # Forex Data
    # =========================================================================
    source_manager.register(
        data_type="forex_rate",
        name="eastmoney",
        fetcher=eastmoney_adapter.fetch_exchange_rate,
        priority=0,
    )
    source_manager.register(
        data_type="forex_rate_history",
        name="eastmoney",
        fetcher=eastmoney_adapter.fetch_exchange_rate_history,
        priority=0,
    )

    _registered = True
    logger.debug("Data source registration complete")


def get_registered_sources() -> dict[str, list[str]]:
    """
    Get all registered data sources.

    Returns:
        Dictionary mapping data types to lists of source names.
    """
    # Ensure sources are registered
    register_all_sources()

    result = {}
    for data_type in [
        "cn_stock_daily",
        "cn_stock_quote",
        "cn_stock_list",
        "cn_index_daily",
        "cn_index_quote",
        "cn_fund_nav",
        "cn_fund_list",
        "cn_fund_quote",
        "us_stock_daily",
        "us_stock_quote",
    ]:
        result[data_type] = source_manager.get_sources(data_type)

    return result
