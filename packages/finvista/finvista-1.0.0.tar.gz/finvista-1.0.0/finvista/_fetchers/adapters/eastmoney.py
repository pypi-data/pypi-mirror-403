"""
East Money (东方财富) data adapter.

This module provides data fetching from East Money, one of the most
popular financial data sources in China.
"""

from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Any

import pandas as pd

from finvista._core.exceptions import DataNotFoundError
from finvista._fetchers.adapters.base import BaseAdapter

logger = logging.getLogger(__name__)


class EastMoneyAdapter(BaseAdapter):
    """
    Adapter for East Money (东方财富) data source.

    This adapter provides access to:
    - A-share stock data (daily, real-time quotes)
    - Fund data
    - Index data
    - Basic financial information

    Example:
        >>> adapter = EastMoneyAdapter()
        >>> df = adapter.fetch_stock_daily("000001", start_date="2024-01-01")
    """

    name = "eastmoney"
    base_url = "https://push2his.eastmoney.com"

    # Market code mapping
    MARKET_CODES = {
        "sh": "1",  # Shanghai
        "sz": "0",  # Shenzhen
        "bj": "0",  # Beijing (uses Shenzhen code)
    }

    # Adjust type mapping
    ADJUST_MAP = {
        "none": "0",
        "qfq": "1",  # Forward adjust
        "hfq": "2",  # Backward adjust
    }

    def is_available(self) -> bool:
        """Check if East Money API is available."""
        try:
            self._get_json(
                "https://push2.eastmoney.com/api/qt/clist/get",
                params={"pn": 1, "pz": 1, "fs": "m:0+t:6"},
            )
            return True
        except Exception:
            return False

    def _get_market_code(self, symbol: str) -> str:
        """
        Get market code for a symbol.

        Args:
            symbol: Stock symbol (e.g., '000001', '600519').

        Returns:
            Market code ('0' for Shenzhen, '1' for Shanghai).
        """
        if symbol.startswith(("6", "9")):
            return "1"  # Shanghai
        elif symbol.startswith(("0", "2", "3")):
            return "0"  # Shenzhen
        elif symbol.startswith(("4", "8")):
            return "0"  # Beijing/New Third Board
        return "0"

    def _get_secid(self, symbol: str) -> str:
        """
        Get secid for a symbol.

        Args:
            symbol: Stock symbol.

        Returns:
            Security ID in format 'market.symbol'.
        """
        market = self._get_market_code(symbol)
        return f"{market}.{symbol}"

    def fetch_stock_daily(
        self,
        symbol: str,
        start_date: str | date | None = None,
        end_date: str | date | None = None,
        adjust: str = "none",
        **kwargs: Any,
    ) -> pd.DataFrame:
        """
        Fetch daily stock data.

        Args:
            symbol: Stock symbol (e.g., '000001').
            start_date: Start date (YYYY-MM-DD or date object).
            end_date: End date (YYYY-MM-DD or date object).
            adjust: Adjustment type ('none', 'qfq', 'hfq').

        Returns:
            DataFrame with columns: date, open, high, low, close, volume,
            amount, change, change_pct, turnover.

        Raises:
            DataNotFoundError: When no data is found.
            DataParsingError: When data cannot be parsed.
        """
        # Format dates
        if start_date is None:
            start_date = "19900101"
        elif isinstance(start_date, (date, datetime)):
            start_date = start_date.strftime("%Y%m%d")
        else:
            start_date = start_date.replace("-", "")

        if end_date is None:
            end_date = datetime.now().strftime("%Y%m%d")
        elif isinstance(end_date, (date, datetime)):
            end_date = end_date.strftime("%Y%m%d")
        else:
            end_date = end_date.replace("-", "")

        secid = self._get_secid(symbol)
        fqt = self.ADJUST_MAP.get(adjust, "0")

        params = {
            "secid": secid,
            "fields1": "f1,f2,f3,f4,f5,f6",
            "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
            "klt": "101",  # Daily
            "fqt": fqt,
            "beg": start_date,
            "end": end_date,
        }

        data = self._get_json(
            "https://push2his.eastmoney.com/api/qt/stock/kline/get",
            params=params,
        )

        if not data.get("data") or not data["data"].get("klines"):
            raise DataNotFoundError(
                f"No data found for symbol {symbol}",
                query_params={"symbol": symbol, "start_date": start_date, "end_date": end_date},
            )

        klines = data["data"]["klines"]
        records = []

        for line in klines:
            parts = line.split(",")
            if len(parts) >= 11:
                records.append(
                    {
                        "date": parts[0],
                        "open": float(parts[1]),
                        "close": float(parts[2]),
                        "high": float(parts[3]),
                        "low": float(parts[4]),
                        "volume": int(float(parts[5])),
                        "amount": float(parts[6]),
                        "amplitude": float(parts[7]) if parts[7] != "-" else None,
                        "change_pct": float(parts[8]) if parts[8] != "-" else None,
                        "change": float(parts[9]) if parts[9] != "-" else None,
                        "turnover": float(parts[10]) if parts[10] != "-" else None,
                    }
                )

        df = pd.DataFrame(records)
        df["date"] = pd.to_datetime(df["date"]).dt.date

        return df

    def fetch_stock_quote(
        self,
        symbols: list[str] | str,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """
        Fetch real-time stock quotes.

        Args:
            symbols: Single symbol or list of symbols.

        Returns:
            DataFrame with real-time quote data.
        """
        if isinstance(symbols, str):
            symbols = [symbols]

        secids = [self._get_secid(s) for s in symbols]
        secids_str = ",".join(secids)

        params = {
            "secids": secids_str,
            "fields": "f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18",
        }

        data = self._get_json(
            "https://push2.eastmoney.com/api/qt/ulist/get",
            params=params,
        )

        if not data.get("data") or not data["data"].get("diff"):
            raise DataNotFoundError(f"No quote data found for symbols: {symbols}")

        records = []
        for item in data["data"]["diff"]:
            records.append(
                {
                    "symbol": item.get("f12", ""),
                    "name": item.get("f14", ""),
                    "price": item.get("f2", 0) / 100 if item.get("f2") else None,
                    "change": item.get("f4", 0) / 100 if item.get("f4") else None,
                    "change_pct": item.get("f3", 0) / 100 if item.get("f3") else None,
                    "open": item.get("f17", 0) / 100 if item.get("f17") else None,
                    "high": item.get("f15", 0) / 100 if item.get("f15") else None,
                    "low": item.get("f16", 0) / 100 if item.get("f16") else None,
                    "pre_close": item.get("f18", 0) / 100 if item.get("f18") else None,
                    "volume": item.get("f5", 0),
                    "amount": item.get("f6", 0),
                }
            )

        return pd.DataFrame(records)

    def fetch_stock_list(
        self,
        market: str = "all",
        **kwargs: Any,
    ) -> pd.DataFrame:
        """
        Fetch list of all A-share stocks.

        Args:
            market: Market filter ('all', 'sh', 'sz', 'bj').

        Returns:
            DataFrame with stock information.
        """
        # Market filter string
        market_filter = {
            "all": "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23",
            "sh": "m:1+t:2,m:1+t:23",
            "sz": "m:0+t:6,m:0+t:80",
            "main": "m:0+t:6,m:1+t:2",
            "gem": "m:0+t:80",  # ChiNext
            "star": "m:1+t:23",  # STAR Market
        }.get(market, "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23")

        params = {
            "pn": 1,
            "pz": 10000,
            "fs": market_filter,
            "fields": "f1,f2,f3,f4,f12,f13,f14",
        }

        data = self._get_json(
            "https://push2.eastmoney.com/api/qt/clist/get",
            params=params,
        )

        if not data.get("data") or not data["data"].get("diff"):
            return pd.DataFrame()

        # diff can be a dict with numeric keys or a list
        diff_data = data["data"]["diff"]
        if isinstance(diff_data, dict):
            items = diff_data.values()
        else:
            items = diff_data

        records = []
        for item in items:
            market_code = item.get("f13", 0)
            records.append(
                {
                    "symbol": item.get("f12", ""),
                    "name": item.get("f14", ""),
                    "market": "sh" if market_code == 1 else "sz",
                    "price": item.get("f2", 0) / 100 if item.get("f2") else None,
                    "change_pct": item.get("f3", 0) / 100 if item.get("f3") else None,
                }
            )

        df = pd.DataFrame(records)
        df = df[df["symbol"].str.len() == 6]  # Filter valid symbols

        return df

    def fetch_index_daily(
        self,
        symbol: str,
        start_date: str | date | None = None,
        end_date: str | date | None = None,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """
        Fetch daily index data.

        Args:
            symbol: Index symbol (e.g., '000001' for SSE Composite).
            start_date: Start date.
            end_date: End date.

        Returns:
            DataFrame with index daily data.
        """
        # Index market codes are different
        if symbol.startswith("0"):
            secid = f"1.{symbol}"  # Shanghai index
        elif symbol.startswith("3"):
            secid = f"0.{symbol}"  # Shenzhen index
        else:
            secid = f"1.{symbol}"

        # Format dates
        if start_date is None:
            start_date = "19900101"
        elif isinstance(start_date, (date, datetime)):
            start_date = start_date.strftime("%Y%m%d")
        else:
            start_date = start_date.replace("-", "")

        if end_date is None:
            end_date = datetime.now().strftime("%Y%m%d")
        elif isinstance(end_date, (date, datetime)):
            end_date = end_date.strftime("%Y%m%d")
        else:
            end_date = end_date.replace("-", "")

        params = {
            "secid": secid,
            "fields1": "f1,f2,f3,f4,f5,f6",
            "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
            "klt": "101",
            "fqt": "1",
            "beg": start_date,
            "end": end_date,
        }

        data = self._get_json(
            "https://push2his.eastmoney.com/api/qt/stock/kline/get",
            params=params,
        )

        if not data.get("data") or not data["data"].get("klines"):
            raise DataNotFoundError(f"No index data found for {symbol}")

        klines = data["data"]["klines"]
        records = []

        for line in klines:
            parts = line.split(",")
            if len(parts) >= 7:
                records.append(
                    {
                        "date": parts[0],
                        "open": float(parts[1]),
                        "close": float(parts[2]),
                        "high": float(parts[3]),
                        "low": float(parts[4]),
                        "volume": int(float(parts[5])),
                        "amount": float(parts[6]),
                    }
                )

        df = pd.DataFrame(records)
        df["date"] = pd.to_datetime(df["date"]).dt.date

        return df


    def fetch_hk_index_daily(
        self,
        symbol: str = "HSI",
        start_date: str | date | None = None,
        end_date: str | date | None = None,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """
        Fetch Hong Kong index daily data.

        Args:
            symbol: Index symbol, options:
                - "HSI": Hang Seng Index (恒生指数)
                - "HSTECH": Hang Seng Tech Index (恒生科技指数)
                - "HSCEI": Hang Seng China Enterprises Index
            start_date: Start date.
            end_date: End date.

        Returns:
            DataFrame with columns: date, open, high, low, close, volume
        """
        # HK index symbol mapping
        hk_index_map = {
            "HSI": "100.HSI",       # 恒生指数
            "HSTECH": "100.HSTECH", # 恒生科技指数
            "HSCEI": "100.HSCEI",   # 恒生中国企业指数
        }

        secid = hk_index_map.get(symbol.upper())
        if not secid:
            raise DataNotFoundError(f"Unknown HK index symbol: {symbol}")

        # Format dates
        if start_date is None:
            start_date = "19900101"
        elif isinstance(start_date, (date, datetime)):
            start_date = start_date.strftime("%Y%m%d")
        else:
            start_date = start_date.replace("-", "")

        if end_date is None:
            end_date = datetime.now().strftime("%Y%m%d")
        elif isinstance(end_date, (date, datetime)):
            end_date = end_date.strftime("%Y%m%d")
        else:
            end_date = end_date.replace("-", "")

        params = {
            "secid": secid,
            "fields1": "f1,f2,f3,f4,f5,f6",
            "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
            "klt": "101",  # Daily
            "fqt": "1",
            "beg": start_date,
            "end": end_date,
        }

        data = self._get_json(
            "https://push2his.eastmoney.com/api/qt/stock/kline/get",
            params=params,
        )

        if not data.get("data") or not data["data"].get("klines"):
            raise DataNotFoundError(f"No HK index data found for {symbol}")

        klines = data["data"]["klines"]
        records = []

        for line in klines:
            parts = line.split(",")
            if len(parts) >= 7:
                records.append(
                    {
                        "date": parts[0],
                        "open": float(parts[1]),
                        "close": float(parts[2]),
                        "high": float(parts[3]),
                        "low": float(parts[4]),
                        "volume": int(float(parts[5])) if parts[5] != "-" else 0,
                        "amount": float(parts[6]) if parts[6] != "-" else 0,
                    }
                )

        df = pd.DataFrame(records)
        df["date"] = pd.to_datetime(df["date"]).dt.date

        return df


    # =========================================================================
    # Financial Data Methods
    # =========================================================================

    def fetch_income_statement(
        self,
        symbol: str,
        period: str = "yearly",
        **kwargs: Any,
    ) -> pd.DataFrame:
        """
        Fetch income statement data.

        Args:
            symbol: Stock symbol (e.g., '000001').
            period: Report period ('yearly' or 'quarterly').

        Returns:
            DataFrame with income statement data.
        """
        market = self._get_market_code(symbol)

        params = {
            "sortColumns": "REPORT_DATE",
            "sortTypes": "-1",
            "pageSize": "50",
            "pageNumber": "1",
            "reportName": "RPT_DMSK_FN_INCOME",
            "columns": "ALL",
            "filter": f'(SECUCODE="{symbol}.{"SH" if market == "1" else "SZ"}")',
        }

        data = self._get_json(
            "https://datacenter-web.eastmoney.com/api/data/v1/get",
            params=params,
        )

        if not data.get("result") or not data["result"].get("data"):
            raise DataNotFoundError(f"No income statement data found for {symbol}")

        records = []
        for item in data["result"]["data"]:
            records.append({
                "report_date": item.get("REPORT_DATE", "")[:10],
                "revenue": item.get("TOTAL_OPERATE_INCOME"),
                "operating_cost": item.get("TOTAL_OPERATE_COST"),
                "operating_profit": item.get("OPERATE_PROFIT"),
                "total_profit": item.get("TOTAL_PROFIT"),
                "net_profit": item.get("NETPROFIT"),
                "net_profit_excl_nr": item.get("DEDUCT_PARENT_NETPROFIT"),
                "eps": item.get("BASIC_EPS"),
                "eps_diluted": item.get("DILUTED_EPS"),
            })

        df = pd.DataFrame(records)
        if not df.empty:
            df["report_date"] = pd.to_datetime(df["report_date"]).dt.date
        return df

    def fetch_balance_sheet(
        self,
        symbol: str,
        period: str = "yearly",
        **kwargs: Any,
    ) -> pd.DataFrame:
        """
        Fetch balance sheet data.

        Args:
            symbol: Stock symbol.
            period: Report period ('yearly' or 'quarterly').

        Returns:
            DataFrame with balance sheet data.
        """
        market = self._get_market_code(symbol)

        params = {
            "sortColumns": "REPORT_DATE",
            "sortTypes": "-1",
            "pageSize": "50",
            "pageNumber": "1",
            "reportName": "RPT_DMSK_FN_BALANCE",
            "columns": "ALL",
            "filter": f'(SECUCODE="{symbol}.{"SH" if market == "1" else "SZ"}")',
        }

        data = self._get_json(
            "https://datacenter-web.eastmoney.com/api/data/v1/get",
            params=params,
        )

        if not data.get("result") or not data["result"].get("data"):
            raise DataNotFoundError(f"No balance sheet data found for {symbol}")

        records = []
        for item in data["result"]["data"]:
            records.append({
                "report_date": item.get("REPORT_DATE", "")[:10],
                "total_assets": item.get("TOTAL_ASSETS"),
                "total_liab": item.get("TOTAL_LIABILITIES"),
                "total_equity": item.get("TOTAL_EQUITY"),
                "total_current_assets": item.get("TOTAL_CURRENT_ASSETS"),
                "total_noncurrent_assets": item.get("TOTAL_NONCURRENT_ASSETS"),
                "total_current_liab": item.get("TOTAL_CURRENT_LIAB"),
                "total_noncurrent_liab": item.get("TOTAL_NONCURRENT_LIAB"),
                "cash": item.get("MONETARYFUNDS"),
                "accounts_recv": item.get("ACCOUNTS_RECE"),
                "inventory": item.get("INVENTORY"),
                "fixed_assets": item.get("FIXED_ASSET"),
            })

        df = pd.DataFrame(records)
        if not df.empty:
            df["report_date"] = pd.to_datetime(df["report_date"]).dt.date
        return df

    def fetch_cash_flow(
        self,
        symbol: str,
        period: str = "yearly",
        **kwargs: Any,
    ) -> pd.DataFrame:
        """
        Fetch cash flow statement data.

        Args:
            symbol: Stock symbol.
            period: Report period ('yearly' or 'quarterly').

        Returns:
            DataFrame with cash flow data.
        """
        market = self._get_market_code(symbol)

        params = {
            "sortColumns": "REPORT_DATE",
            "sortTypes": "-1",
            "pageSize": "50",
            "pageNumber": "1",
            "reportName": "RPT_DMSK_FN_CASHFLOW",
            "columns": "ALL",
            "filter": f'(SECUCODE="{symbol}.{"SH" if market == "1" else "SZ"}")',
        }

        data = self._get_json(
            "https://datacenter-web.eastmoney.com/api/data/v1/get",
            params=params,
        )

        if not data.get("result") or not data["result"].get("data"):
            raise DataNotFoundError(f"No cash flow data found for {symbol}")

        records = []
        for item in data["result"]["data"]:
            records.append({
                "report_date": item.get("REPORT_DATE", "")[:10],
                "operating_cashflow": item.get("NETCASH_OPERATE"),
                "investing_cashflow": item.get("NETCASH_INVEST"),
                "financing_cashflow": item.get("NETCASH_FINANCE"),
                "net_cash_change": item.get("CASH_EQUIVALENT_INCREASE"),
                "cash_end": item.get("END_CASH_EQUIVALENT"),
            })

        df = pd.DataFrame(records)
        if not df.empty:
            df["report_date"] = pd.to_datetime(df["report_date"]).dt.date
        return df

    def fetch_performance_forecast(
        self,
        date: str | None = None,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """
        Fetch performance forecast data.

        Args:
            date: Date to filter (YYYY-MM-DD). If None, get latest.

        Returns:
            DataFrame with performance forecast data.
        """
        params = {
            "sortColumns": "NOTICE_DATE",
            "sortTypes": "-1",
            "pageSize": "500",
            "pageNumber": "1",
            "reportName": "RPT_PUBLIC_OP_NEWPREDICT",
            "columns": "ALL",
        }

        if date:
            params["filter"] = f'(NOTICE_DATE>=\'{date}\')'

        data = self._get_json(
            "https://datacenter-web.eastmoney.com/api/data/v1/get",
            params=params,
        )

        if not data.get("result") or not data["result"].get("data"):
            return pd.DataFrame()

        records = []
        for item in data["result"]["data"]:
            records.append({
                "symbol": item.get("SECURITY_CODE", ""),
                "name": item.get("SECURITY_NAME_ABBR", ""),
                "notice_date": item.get("NOTICE_DATE", "")[:10],
                "report_date": item.get("REPORT_DATE", "")[:10] if item.get("REPORT_DATE") else "",
                "forecast_type": item.get("PREDICT_FINANCE_CODE", ""),
                "net_profit_min": item.get("PREDICT_NETPROFIT_MIN"),
                "net_profit_max": item.get("PREDICT_NETPROFIT_MAX"),
                "change_pct_min": item.get("ADD_AMP_MIN"),
                "change_pct_max": item.get("ADD_AMP_MAX"),
                "forecast_content": item.get("PREDICT_CONTENT", ""),
            })

        df = pd.DataFrame(records)
        if not df.empty and "notice_date" in df.columns:
            df["notice_date"] = pd.to_datetime(df["notice_date"]).dt.date
        return df

    def fetch_dividend_history(
        self,
        symbol: str,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """
        Fetch dividend history data.

        Args:
            symbol: Stock symbol.

        Returns:
            DataFrame with dividend history.
        """
        market = self._get_market_code(symbol)

        params = {
            "sortColumns": "EX_DIVIDEND_DATE",
            "sortTypes": "-1",
            "pageSize": "100",
            "pageNumber": "1",
            "reportName": "RPT_SHAREBONUS_DET",
            "columns": "ALL",
            "filter": f'(SECUCODE="{symbol}.{"SH" if market == "1" else "SZ"}")',
        }

        data = self._get_json(
            "https://datacenter-web.eastmoney.com/api/data/v1/get",
            params=params,
        )

        if not data.get("result") or not data["result"].get("data"):
            return pd.DataFrame()

        records = []
        for item in data["result"]["data"]:
            ex_date = item.get("EX_DIVIDEND_DATE")
            records.append({
                "symbol": symbol,
                "report_date": item.get("REPORT_DATE", "")[:10] if item.get("REPORT_DATE") else "",
                "plan": item.get("IMPL_PLAN_PROFILE", ""),
                "dividend_per_share": item.get("BONUS_IT_RATIO"),
                "bonus_shares_ratio": item.get("TRANS_IT_RATIO"),
                "ex_dividend_date": ex_date[:10] if ex_date else "",
                "record_date": item.get("EQUITY_RECORD_DATE", "")[:10] if item.get("EQUITY_RECORD_DATE") else "",
                "pay_date": item.get("PAY_CASH_DATE", "")[:10] if item.get("PAY_CASH_DATE") else "",
            })

        df = pd.DataFrame(records)
        return df

    # =========================================================================
    # Money Flow Methods
    # =========================================================================

    def fetch_stock_moneyflow(
        self,
        symbol: str,
        days: int = 30,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """
        Fetch historical money flow data for a stock.

        Args:
            symbol: Stock symbol.
            days: Number of days to fetch.

        Returns:
            DataFrame with money flow data.
        """
        secid = self._get_secid(symbol)

        params = {
            "lmt": str(days),
            "klt": "101",
            "secid": secid,
            "fields1": "f1,f2,f3,f7",
            "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63,f64,f65",
        }

        data = self._get_json(
            "https://push2his.eastmoney.com/api/qt/stock/fflow/daykline/get",
            params=params,
        )

        if not data.get("data") or not data["data"].get("klines"):
            raise DataNotFoundError(f"No money flow data found for {symbol}")

        records = []
        for line in data["data"]["klines"]:
            parts = line.split(",")
            if len(parts) >= 13:
                records.append({
                    "date": parts[0],
                    "main_net_inflow": float(parts[1]) if parts[1] != "-" else 0,
                    "small_net_inflow": float(parts[2]) if parts[2] != "-" else 0,
                    "medium_net_inflow": float(parts[3]) if parts[3] != "-" else 0,
                    "large_net_inflow": float(parts[4]) if parts[4] != "-" else 0,
                    "super_large_net_inflow": float(parts[5]) if parts[5] != "-" else 0,
                    "main_net_inflow_pct": float(parts[6]) if parts[6] != "-" else 0,
                    "small_net_inflow_pct": float(parts[7]) if parts[7] != "-" else 0,
                    "medium_net_inflow_pct": float(parts[8]) if parts[8] != "-" else 0,
                    "large_net_inflow_pct": float(parts[9]) if parts[9] != "-" else 0,
                    "super_large_net_inflow_pct": float(parts[10]) if parts[10] != "-" else 0,
                    "close": float(parts[11]) if parts[11] != "-" else 0,
                    "change_pct": float(parts[12]) if parts[12] != "-" else 0,
                })

        df = pd.DataFrame(records)
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"]).dt.date
        return df

    def fetch_stock_moneyflow_realtime(
        self,
        symbol: str,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """
        Fetch real-time money flow data for a stock.

        Args:
            symbol: Stock symbol.

        Returns:
            DataFrame with real-time money flow data.
        """
        secid = self._get_secid(symbol)

        params = {
            "secid": secid,
            "fields": "f62,f184,f66,f69,f72,f75,f78,f81,f84,f87,f64,f65,f70,f71,f76,f77,f82,f83,f88,f89",
        }

        data = self._get_json(
            "https://push2.eastmoney.com/api/qt/stock/get",
            params=params,
        )

        if not data.get("data"):
            raise DataNotFoundError(f"No real-time money flow data for {symbol}")

        item = data["data"]
        record = {
            "symbol": symbol,
            "main_net_inflow": item.get("f62"),
            "main_net_inflow_pct": item.get("f184"),
            "super_large_inflow": item.get("f66"),
            "super_large_outflow": item.get("f64"),
            "super_large_net_inflow": item.get("f69"),
            "large_inflow": item.get("f72"),
            "large_outflow": item.get("f70"),
            "large_net_inflow": item.get("f75"),
            "medium_inflow": item.get("f78"),
            "medium_outflow": item.get("f76"),
            "medium_net_inflow": item.get("f81"),
            "small_inflow": item.get("f84"),
            "small_outflow": item.get("f82"),
            "small_net_inflow": item.get("f87"),
        }

        return pd.DataFrame([record])

    def fetch_industry_moneyflow(
        self,
        date: str | None = None,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """
        Fetch industry money flow data.

        Args:
            date: Date to filter (not used, always returns latest).

        Returns:
            DataFrame with industry money flow data.
        """
        params = {
            "pn": "1",
            "pz": "100",
            "po": "1",
            "np": "1",
            "fltt": "2",
            "invt": "2",
            "fid": "f62",
            "fs": "m:90+t:2",
            "fields": "f12,f14,f2,f3,f62,f184,f66,f69,f72,f75,f78,f81,f84,f87",
        }

        data = self._get_json(
            "https://push2.eastmoney.com/api/qt/clist/get",
            params=params,
        )

        if not data.get("data") or not data["data"].get("diff"):
            return pd.DataFrame()

        records = []
        for item in data["data"]["diff"]:
            records.append({
                "code": item.get("f12", ""),
                "name": item.get("f14", ""),
                "price": item.get("f2"),
                "change_pct": item.get("f3"),
                "main_net_inflow": item.get("f62"),
                "main_net_inflow_pct": item.get("f184"),
                "super_large_net_inflow": item.get("f66"),
                "large_net_inflow": item.get("f72"),
                "medium_net_inflow": item.get("f78"),
                "small_net_inflow": item.get("f84"),
            })

        return pd.DataFrame(records)

    # =========================================================================
    # Minute Data Methods
    # =========================================================================

    def fetch_stock_minute(
        self,
        symbol: str,
        period: str = "5",
        days: int = 5,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """
        Fetch minute-level stock data.

        Args:
            symbol: Stock symbol.
            period: Minute period ('1', '5', '15', '30', '60').
            days: Number of days of data.

        Returns:
            DataFrame with minute data.
        """
        secid = self._get_secid(symbol)

        # Period mapping
        klt_map = {"1": "1", "5": "5", "15": "15", "30": "30", "60": "60"}
        klt = klt_map.get(period, "5")

        # Calculate limit based on days and period
        minutes_per_day = 240  # 4 hours * 60 minutes
        limit = (minutes_per_day // int(period)) * days

        params = {
            "secid": secid,
            "fields1": "f1,f2,f3,f4,f5,f6",
            "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
            "klt": klt,
            "fqt": "1",
            "lmt": str(limit),
        }

        data = self._get_json(
            "https://push2his.eastmoney.com/api/qt/stock/kline/get",
            params=params,
        )

        if not data.get("data") or not data["data"].get("klines"):
            raise DataNotFoundError(f"No minute data found for {symbol}")

        records = []
        for line in data["data"]["klines"]:
            parts = line.split(",")
            if len(parts) >= 7:
                records.append({
                    "datetime": parts[0],
                    "open": float(parts[1]),
                    "close": float(parts[2]),
                    "high": float(parts[3]),
                    "low": float(parts[4]),
                    "volume": int(float(parts[5])),
                    "amount": float(parts[6]),
                })

        df = pd.DataFrame(records)
        if not df.empty:
            df["datetime"] = pd.to_datetime(df["datetime"])
        return df

    # =========================================================================
    # Futures Data Methods
    # =========================================================================

    def fetch_futures_list(
        self,
        exchange: str = "all",
        **kwargs: Any,
    ) -> pd.DataFrame:
        """
        Fetch list of futures contracts.

        Args:
            exchange: Exchange filter ('all', 'SHFE', 'DCE', 'CZCE', 'CFFEX', 'INE').

        Returns:
            DataFrame with futures contract information.
        """
        # Futures market code
        market_filter = {
            "all": "m:113,m:114,m:115,m:8",
            "SHFE": "m:113",   # 上海期货交易所
            "DCE": "m:114",    # 大连商品交易所
            "CZCE": "m:115",   # 郑州商品交易所
            "CFFEX": "m:8",    # 中国金融期货交易所
            "INE": "m:142",    # 上海国际能源交易中心
        }.get(exchange.upper(), "m:113,m:114,m:115,m:8")

        params = {
            "pn": "1",
            "pz": "500",
            "po": "1",
            "np": "1",
            "fltt": "2",
            "invt": "2",
            "fid": "f3",
            "fs": market_filter,
            "fields": "f1,f2,f3,f4,f5,f6,f7,f12,f13,f14,f15,f16,f17,f18",
        }

        data = self._get_json(
            "https://push2.eastmoney.com/api/qt/clist/get",
            params=params,
        )

        if not data.get("data") or not data["data"].get("diff"):
            return pd.DataFrame()

        records = []
        for item in data["data"]["diff"]:
            market_code = item.get("f13", 0)
            exchange_name = {113: "SHFE", 114: "DCE", 115: "CZCE", 8: "CFFEX", 142: "INE"}.get(market_code, "")
            records.append({
                "symbol": item.get("f12", ""),
                "name": item.get("f14", ""),
                "exchange": exchange_name,
                "price": item.get("f2"),
                "change_pct": item.get("f3"),
                "open": item.get("f17"),
                "high": item.get("f15"),
                "low": item.get("f16"),
                "pre_close": item.get("f18"),
                "volume": item.get("f5"),
                "amount": item.get("f6"),
            })

        return pd.DataFrame(records)

    def fetch_futures_daily(
        self,
        symbol: str,
        start_date: str | date | None = None,
        end_date: str | date | None = None,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """
        Fetch daily futures data.

        Args:
            symbol: Futures contract symbol.
            start_date: Start date.
            end_date: End date.

        Returns:
            DataFrame with futures daily data.
        """
        # Format dates
        if start_date is None:
            start_date = "19900101"
        elif isinstance(start_date, (date, datetime)):
            start_date = start_date.strftime("%Y%m%d")
        else:
            start_date = start_date.replace("-", "")

        if end_date is None:
            end_date = datetime.now().strftime("%Y%m%d")
        elif isinstance(end_date, (date, datetime)):
            end_date = end_date.strftime("%Y%m%d")
        else:
            end_date = end_date.replace("-", "")

        # Determine exchange by symbol pattern
        symbol_upper = symbol.upper()
        if symbol_upper.startswith(("IF", "IC", "IH", "IM", "T", "TF", "TS")):
            market = "8"  # CFFEX
        elif symbol_upper.startswith(("SC", "NR", "LU", "BC")):
            market = "142"  # INE
        elif any(symbol_upper.startswith(x) for x in ["A", "B", "C", "I", "J", "JD", "JM", "L", "M", "P", "PP", "V", "Y", "EG", "EB", "PG", "RR", "LH"]):
            market = "114"  # DCE
        elif any(symbol_upper.startswith(x) for x in ["CF", "CY", "FG", "MA", "OI", "RM", "RS", "SF", "SM", "SR", "TA", "ZC", "AP", "CJ", "UR", "SA", "PF", "PK"]):
            market = "115"  # CZCE
        else:
            market = "113"  # SHFE

        secid = f"{market}.{symbol}"

        params = {
            "secid": secid,
            "fields1": "f1,f2,f3,f4,f5,f6",
            "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
            "klt": "101",
            "fqt": "1",
            "beg": start_date,
            "end": end_date,
        }

        data = self._get_json(
            "https://push2his.eastmoney.com/api/qt/stock/kline/get",
            params=params,
        )

        if not data.get("data") or not data["data"].get("klines"):
            raise DataNotFoundError(f"No futures data found for {symbol}")

        records = []
        for line in data["data"]["klines"]:
            parts = line.split(",")
            if len(parts) >= 7:
                records.append({
                    "date": parts[0],
                    "open": float(parts[1]),
                    "close": float(parts[2]),
                    "high": float(parts[3]),
                    "low": float(parts[4]),
                    "volume": int(float(parts[5])),
                    "amount": float(parts[6]),
                    "open_interest": float(parts[7]) if len(parts) > 7 and parts[7] != "-" else None,
                })

        df = pd.DataFrame(records)
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"]).dt.date
        return df

    def fetch_futures_positions(
        self,
        symbol: str,
        date: str | None = None,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """
        Fetch futures position ranking data.

        Args:
            symbol: Futures contract symbol (e.g., 'IF2401').
            date: Date to query (YYYY-MM-DD).

        Returns:
            DataFrame with position ranking data.
        """
        if date:
            date_filter = f"(TRADE_DATE='{date}')"
        else:
            date_filter = ""

        # Extract base symbol
        base_symbol = ''.join([c for c in symbol if c.isalpha()]).upper()

        params = {
            "sortColumns": "TRADE_DATE,RANK",
            "sortTypes": "-1,1",
            "pageSize": "200",
            "pageNumber": "1",
            "reportName": "RPT_FUTU_POSITION_DETAIL",
            "columns": "ALL",
            "filter": f'(TRADE_MARKET_CODE="main")(CONTRACT_CODE="{base_symbol}")' + date_filter,
        }

        data = self._get_json(
            "https://datacenter-web.eastmoney.com/api/data/v1/get",
            params=params,
        )

        if not data.get("result") or not data["result"].get("data"):
            return pd.DataFrame()

        records = []
        for item in data["result"]["data"]:
            records.append({
                "date": item.get("TRADE_DATE", "")[:10],
                "contract": item.get("CONTRACT_CODE", ""),
                "rank": item.get("RANK"),
                "member_name": item.get("PARTICIPATOR_NAME", ""),
                "long_volume": item.get("CJ_VOLUME"),
                "long_change": item.get("CJ_VOLUME_CHG"),
                "short_volume": item.get("CD_VOLUME"),
                "short_change": item.get("CD_VOLUME_CHG"),
            })

        df = pd.DataFrame(records)
        if not df.empty and "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"]).dt.date
        return df

    # =========================================================================
    # Convertible Bond Data Methods
    # =========================================================================

    def fetch_convertible_list(
        self,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """
        Fetch list of convertible bonds.

        Returns:
            DataFrame with convertible bond information.
        """
        params = {
            "pn": "1",
            "pz": "500",
            "po": "1",
            "np": "1",
            "fltt": "2",
            "invt": "2",
            "fid": "f3",
            "fs": "b:MK0354",
            "fields": "f1,f2,f3,f4,f5,f6,f12,f13,f14,f15,f16,f17,f18",
        }

        data = self._get_json(
            "https://push2.eastmoney.com/api/qt/clist/get",
            params=params,
        )

        if not data.get("data") or not data["data"].get("diff"):
            return pd.DataFrame()

        records = []
        for item in data["data"]["diff"]:
            records.append({
                "symbol": item.get("f12", ""),
                "name": item.get("f14", ""),
                "price": item.get("f2"),
                "change_pct": item.get("f3"),
                "open": item.get("f17"),
                "high": item.get("f15"),
                "low": item.get("f16"),
                "pre_close": item.get("f18"),
                "volume": item.get("f5"),
                "amount": item.get("f6"),
            })

        return pd.DataFrame(records)

    def fetch_convertible_daily(
        self,
        symbol: str,
        start_date: str | date | None = None,
        end_date: str | date | None = None,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """
        Fetch daily convertible bond data.

        Args:
            symbol: Convertible bond symbol.
            start_date: Start date.
            end_date: End date.

        Returns:
            DataFrame with daily data.
        """
        # Format dates
        if start_date is None:
            start_date = "19900101"
        elif isinstance(start_date, (date, datetime)):
            start_date = start_date.strftime("%Y%m%d")
        else:
            start_date = start_date.replace("-", "")

        if end_date is None:
            end_date = datetime.now().strftime("%Y%m%d")
        elif isinstance(end_date, (date, datetime)):
            end_date = end_date.strftime("%Y%m%d")
        else:
            end_date = end_date.replace("-", "")

        # Convertible bonds: 11/12xxxx -> SH, 123/127/128xxx -> SZ
        if symbol.startswith(("11", "12")) and not symbol.startswith(("123", "127", "128")):
            secid = f"1.{symbol}"
        else:
            secid = f"0.{symbol}"

        params = {
            "secid": secid,
            "fields1": "f1,f2,f3,f4,f5,f6",
            "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
            "klt": "101",
            "fqt": "1",
            "beg": start_date,
            "end": end_date,
        }

        data = self._get_json(
            "https://push2his.eastmoney.com/api/qt/stock/kline/get",
            params=params,
        )

        if not data.get("data") or not data["data"].get("klines"):
            raise DataNotFoundError(f"No convertible bond data found for {symbol}")

        records = []
        for line in data["data"]["klines"]:
            parts = line.split(",")
            if len(parts) >= 7:
                records.append({
                    "date": parts[0],
                    "open": float(parts[1]),
                    "close": float(parts[2]),
                    "high": float(parts[3]),
                    "low": float(parts[4]),
                    "volume": int(float(parts[5])),
                    "amount": float(parts[6]),
                })

        df = pd.DataFrame(records)
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"]).dt.date
        return df

    def fetch_convertible_info(
        self,
        symbol: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Fetch convertible bond basic information.

        Args:
            symbol: Convertible bond symbol.

        Returns:
            Dictionary with bond information.
        """
        params = {
            "sortColumns": "PUBLIC_START_DATE",
            "sortTypes": "-1",
            "pageSize": "500",
            "pageNumber": "1",
            "reportName": "RPT_BOND_CB_LIST",
            "columns": "ALL",
            "filter": f'(CONVERT_STOCK_CODE="{symbol}")',
        }

        data = self._get_json(
            "https://datacenter-web.eastmoney.com/api/data/v1/get",
            params=params,
        )

        # Try searching by bond code
        if not data.get("result") or not data["result"].get("data"):
            params["filter"] = f'(SECURITY_CODE="{symbol}")'
            data = self._get_json(
                "https://datacenter-web.eastmoney.com/api/data/v1/get",
                params=params,
            )

        if not data.get("result") or not data["result"].get("data"):
            raise DataNotFoundError(f"No convertible bond info found for {symbol}")

        item = data["result"]["data"][0]
        return {
            "bond_code": item.get("SECURITY_CODE", ""),
            "bond_name": item.get("SECURITY_NAME_ABBR", ""),
            "stock_code": item.get("CONVERT_STOCK_CODE", ""),
            "stock_name": item.get("SECURITY_SHORT_NAME", ""),
            "convert_price": item.get("CONVERT_PRICE"),
            "convert_value": item.get("CONVERT_VALUE"),
            "premium_rate": item.get("PREMIUM_RATE"),
            "bond_price": item.get("TRADE_PRICE"),
            "issue_date": item.get("PUBLIC_START_DATE", "")[:10] if item.get("PUBLIC_START_DATE") else "",
            "maturity_date": item.get("CEASE_DATE", "")[:10] if item.get("CEASE_DATE") else "",
        }

    # =========================================================================
    # Dragon Tiger List (龙虎榜) Methods
    # =========================================================================

    def fetch_lhb_list(
        self,
        date: str | None = None,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """
        Fetch dragon tiger list data.

        Args:
            date: Date to query (YYYY-MM-DD). If None, get latest.

        Returns:
            DataFrame with dragon tiger list data.
        """
        params = {
            "sortColumns": "TRADE_DATE,SECURITY_CODE",
            "sortTypes": "-1,-1",
            "pageSize": "500",
            "pageNumber": "1",
            "reportName": "RPT_DAILYBILLBOARD_DETAILSNEW",
            "columns": "ALL",
        }

        if date:
            params["filter"] = f"(TRADE_DATE='{date}')"

        data = self._get_json(
            "https://datacenter-web.eastmoney.com/api/data/v1/get",
            params=params,
        )

        if not data.get("result") or not data["result"].get("data"):
            return pd.DataFrame()

        records = []
        for item in data["result"]["data"]:
            records.append({
                "date": item.get("TRADE_DATE", "")[:10],
                "symbol": item.get("SECURITY_CODE", ""),
                "name": item.get("SECURITY_NAME_ABBR", ""),
                "close": item.get("CLOSE_PRICE"),
                "change_pct": item.get("CHANGE_RATE"),
                "turnover_rate": item.get("TURNOVERRATE"),
                "reason": item.get("EXPLANATION", ""),
                "buy_amount": item.get("BUY_TOTAL_AMT"),
                "sell_amount": item.get("SELL_TOTAL_AMT"),
                "net_amount": item.get("NET_BUY_AMT"),
            })

        df = pd.DataFrame(records)
        if not df.empty and "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"]).dt.date
        return df

    def fetch_lhb_detail(
        self,
        symbol: str,
        date: str,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """
        Fetch dragon tiger list trading details.

        Args:
            symbol: Stock symbol.
            date: Trading date (YYYY-MM-DD).

        Returns:
            DataFrame with trading details.
        """
        params = {
            "sortColumns": "BUY_AMT,RANK",
            "sortTypes": "-1,1",
            "pageSize": "100",
            "pageNumber": "1",
            "reportName": "RPT_BILLBOARD_DAILYDETAILSBUY",
            "columns": "ALL",
            "filter": f"(TRADE_DATE='{date}')(SECURITY_CODE=\"{symbol}\")",
        }

        data = self._get_json(
            "https://datacenter-web.eastmoney.com/api/data/v1/get",
            params=params,
        )

        if not data.get("result") or not data["result"].get("data"):
            return pd.DataFrame()

        records = []
        for item in data["result"]["data"]:
            records.append({
                "date": item.get("TRADE_DATE", "")[:10],
                "symbol": item.get("SECURITY_CODE", ""),
                "rank": item.get("RANK"),
                "trader_name": item.get("OPERATEDEPT_NAME", ""),
                "buy_amount": item.get("BUY_AMT"),
                "sell_amount": item.get("SELL_AMT"),
                "net_amount": item.get("NET_AMT"),
                "buy_pct": item.get("BUY_RATE"),
                "sell_pct": item.get("SELL_RATE"),
            })

        df = pd.DataFrame(records)
        return df

    def fetch_lhb_institution(
        self,
        date: str | None = None,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """
        Fetch institution trading data from dragon tiger list.

        Args:
            date: Date to query (YYYY-MM-DD).

        Returns:
            DataFrame with institution trading data.
        """
        params = {
            "sortColumns": "TRADE_DATE,NET_BUY_AMT",
            "sortTypes": "-1,-1",
            "pageSize": "500",
            "pageNumber": "1",
            "reportName": "RPT_ORGANIZATION_HOLD_DETAILS",
            "columns": "ALL",
        }

        if date:
            params["filter"] = f"(TRADE_DATE>='{date}')"

        data = self._get_json(
            "https://datacenter-web.eastmoney.com/api/data/v1/get",
            params=params,
        )

        if not data.get("result") or not data["result"].get("data"):
            return pd.DataFrame()

        records = []
        for item in data["result"]["data"]:
            records.append({
                "date": item.get("TRADE_DATE", "")[:10],
                "symbol": item.get("SECURITY_CODE", ""),
                "name": item.get("SECURITY_NAME_ABBR", ""),
                "close": item.get("CLOSE_PRICE"),
                "change_pct": item.get("CHANGE_RATE"),
                "institution_buy": item.get("BUY_AMT"),
                "institution_sell": item.get("SELL_AMT"),
                "institution_net": item.get("NET_BUY_AMT"),
                "reason": item.get("EXPLANATION", ""),
            })

        df = pd.DataFrame(records)
        if not df.empty and "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"]).dt.date
        return df

    # =========================================================================
    # Option Data Methods
    # =========================================================================

    def fetch_option_list(
        self,
        underlying: str = "510050",
        **kwargs: Any,
    ) -> pd.DataFrame:
        """
        Fetch list of option contracts.

        Args:
            underlying: Underlying asset code.

        Returns:
            DataFrame with option contract information.
        """
        params = {
            "pn": "1",
            "pz": "500",
            "po": "1",
            "np": "1",
            "fltt": "2",
            "invt": "2",
            "fid": "f3",
            "fs": "m:10+t:8",
            "fields": "f1,f2,f3,f4,f5,f6,f12,f13,f14,f15,f16,f17,f18,f152",
        }

        data = self._get_json(
            "https://push2.eastmoney.com/api/qt/clist/get",
            params=params,
        )

        if not data.get("data") or not data["data"].get("diff"):
            return pd.DataFrame()

        records = []
        for item in data["data"]["diff"]:
            records.append({
                "symbol": item.get("f12", ""),
                "name": item.get("f14", ""),
                "price": item.get("f2"),
                "change_pct": item.get("f3"),
                "open": item.get("f17"),
                "high": item.get("f15"),
                "low": item.get("f16"),
                "pre_close": item.get("f18"),
                "volume": item.get("f5"),
                "amount": item.get("f6"),
            })

        return pd.DataFrame(records)

    def fetch_option_daily(
        self,
        symbol: str,
        start_date: str | date | None = None,
        end_date: str | date | None = None,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """
        Fetch daily option data.

        Args:
            symbol: Option contract symbol.
            start_date: Start date.
            end_date: End date.

        Returns:
            DataFrame with option daily data.
        """
        # Format dates
        if start_date is None:
            start_date = "19900101"
        elif isinstance(start_date, (date, datetime)):
            start_date = start_date.strftime("%Y%m%d")
        else:
            start_date = start_date.replace("-", "")

        if end_date is None:
            end_date = datetime.now().strftime("%Y%m%d")
        elif isinstance(end_date, (date, datetime)):
            end_date = end_date.strftime("%Y%m%d")
        else:
            end_date = end_date.replace("-", "")

        secid = f"10.{symbol}"

        params = {
            "secid": secid,
            "fields1": "f1,f2,f3,f4,f5,f6",
            "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
            "klt": "101",
            "fqt": "1",
            "beg": start_date,
            "end": end_date,
        }

        data = self._get_json(
            "https://push2his.eastmoney.com/api/qt/stock/kline/get",
            params=params,
        )

        if not data.get("data") or not data["data"].get("klines"):
            raise DataNotFoundError(f"No option data found for {symbol}")

        records = []
        for line in data["data"]["klines"]:
            parts = line.split(",")
            if len(parts) >= 7:
                records.append({
                    "date": parts[0],
                    "open": float(parts[1]),
                    "close": float(parts[2]),
                    "high": float(parts[3]),
                    "low": float(parts[4]),
                    "volume": int(float(parts[5])),
                    "amount": float(parts[6]),
                })

        df = pd.DataFrame(records)
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"]).dt.date
        return df

    # =========================================================================
    # Shareholder Data Methods
    # =========================================================================

    def fetch_top_shareholders(
        self,
        symbol: str,
        period: str | None = None,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """
        Fetch top 10 shareholders data.

        Args:
            symbol: Stock symbol.
            period: Report period (YYYY-MM-DD).

        Returns:
            DataFrame with shareholder data.
        """
        market = self._get_market_code(symbol)

        params = {
            "sortColumns": "HOLD_DATE,RANK",
            "sortTypes": "-1,1",
            "pageSize": "50",
            "pageNumber": "1",
            "reportName": "RPT_F10_EH_FREEHOLDERS",
            "columns": "ALL",
            "filter": f'(SECUCODE="{symbol}.{"SH" if market == "1" else "SZ"}")',
        }

        data = self._get_json(
            "https://datacenter-web.eastmoney.com/api/data/v1/get",
            params=params,
        )

        if not data.get("result") or not data["result"].get("data"):
            raise DataNotFoundError(f"No shareholder data found for {symbol}")

        records = []
        for item in data["result"]["data"]:
            records.append({
                "report_date": item.get("HOLD_DATE", "")[:10],
                "rank": item.get("RANK"),
                "holder_name": item.get("HOLDER_NAME", ""),
                "holder_type": item.get("HOLDER_TYPE", ""),
                "shares": item.get("HOLD_NUM"),
                "shares_pct": item.get("HOLD_RATIO"),
                "change": item.get("HOLD_NUM_CHANGE"),
                "change_pct": item.get("HOLD_RATIO_CHANGE"),
            })

        df = pd.DataFrame(records)
        if not df.empty and "report_date" in df.columns:
            df["report_date"] = pd.to_datetime(df["report_date"]).dt.date
        return df

    def fetch_stock_pledge(
        self,
        symbol: str,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """
        Fetch stock pledge data.

        Args:
            symbol: Stock symbol.

        Returns:
            DataFrame with pledge data.
        """
        params = {
            "sortColumns": "PLEDGE_DATE",
            "sortTypes": "-1",
            "pageSize": "100",
            "pageNumber": "1",
            "reportName": "RPT_SHAREHOLD_PLEGDGE_DETAIL",
            "columns": "ALL",
            "filter": f'(SECURITY_CODE="{symbol}")',
        }

        data = self._get_json(
            "https://datacenter-web.eastmoney.com/api/data/v1/get",
            params=params,
        )

        if not data.get("result") or not data["result"].get("data"):
            return pd.DataFrame()

        records = []
        for item in data["result"]["data"]:
            records.append({
                "symbol": symbol,
                "pledge_date": item.get("PLEDGE_DATE", "")[:10] if item.get("PLEDGE_DATE") else "",
                "holder_name": item.get("HOLDER_NAME", ""),
                "pledgee": item.get("PLEDGE_ORG", ""),
                "shares": item.get("PLEDGE_NUM"),
                "shares_pct": item.get("PLEDGE_RATIO"),
                "start_date": item.get("PLEDGE_START_DATE", "")[:10] if item.get("PLEDGE_START_DATE") else "",
                "end_date": item.get("PLEDGE_END_DATE", "")[:10] if item.get("PLEDGE_END_DATE") else "",
            })

        df = pd.DataFrame(records)
        return df

    def fetch_stock_unlock(
        self,
        start_date: str,
        end_date: str,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """
        Fetch stock unlock schedule.

        Args:
            start_date: Start date (YYYY-MM-DD).
            end_date: End date (YYYY-MM-DD).

        Returns:
            DataFrame with unlock schedule.
        """
        params = {
            "sortColumns": "FREE_DATE",
            "sortTypes": "1",
            "pageSize": "500",
            "pageNumber": "1",
            "reportName": "RPT_LIFT_STAGE",
            "columns": "ALL",
            "filter": f"(FREE_DATE>='{start_date}')(FREE_DATE<='{end_date}')",
        }

        data = self._get_json(
            "https://datacenter-web.eastmoney.com/api/data/v1/get",
            params=params,
        )

        if not data.get("result") or not data["result"].get("data"):
            return pd.DataFrame()

        records = []
        for item in data["result"]["data"]:
            records.append({
                "unlock_date": item.get("FREE_DATE", "")[:10],
                "symbol": item.get("SECURITY_CODE", ""),
                "name": item.get("SECURITY_NAME_ABBR", ""),
                "unlock_shares": item.get("LIFT_NUM"),
                "unlock_ratio": item.get("LIFT_RATIO"),
                "unlock_value": item.get("LIFT_MARKET_CAP"),
                "lock_type": item.get("LIMIT_SALE_TYPE", ""),
            })

        df = pd.DataFrame(records)
        if not df.empty and "unlock_date" in df.columns:
            df["unlock_date"] = pd.to_datetime(df["unlock_date"]).dt.date
        return df

    # =========================================================================
    # Index Enhanced Methods
    # =========================================================================

    def fetch_index_constituents(
        self,
        symbol: str,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """
        Fetch index constituent stocks.

        Args:
            symbol: Index symbol (e.g., '000300' for CSI 300).

        Returns:
            DataFrame with constituent stocks.
        """
        params = {
            "sortColumns": "SECURITY_CODE",
            "sortTypes": "1",
            "pageSize": "1000",
            "pageNumber": "1",
            "reportName": "RPT_INDEX_TS",
            "columns": "SECUCODE,SECURITY_CODE,SECURITY_NAME_ABBR,CLOSE_PRICE,CHANGE_RATE,INDEX_CODE",
            "filter": f'(INDEX_CODE="{symbol}")',
        }

        data = self._get_json(
            "https://datacenter-web.eastmoney.com/api/data/v1/get",
            params=params,
        )

        if not data.get("result") or not data["result"].get("data"):
            raise DataNotFoundError(f"No constituents found for index {symbol}")

        records = []
        for item in data["result"]["data"]:
            records.append({
                "index_code": symbol,
                "symbol": item.get("SECURITY_CODE", ""),
                "name": item.get("SECURITY_NAME_ABBR", ""),
                "close": item.get("CLOSE_PRICE"),
                "change_pct": item.get("CHANGE_RATE"),
            })

        return pd.DataFrame(records)

    def fetch_index_weights(
        self,
        symbol: str,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """
        Fetch index constituent weights.

        Args:
            symbol: Index symbol.

        Returns:
            DataFrame with constituent weights.
        """
        params = {
            "sortColumns": "WEIGHT",
            "sortTypes": "-1",
            "pageSize": "1000",
            "pageNumber": "1",
            "reportName": "RPT_INDEX_TS",
            "columns": "SECUCODE,SECURITY_CODE,SECURITY_NAME_ABBR,WEIGHT,INDEX_CODE",
            "filter": f'(INDEX_CODE="{symbol}")',
        }

        data = self._get_json(
            "https://datacenter-web.eastmoney.com/api/data/v1/get",
            params=params,
        )

        if not data.get("result") or not data["result"].get("data"):
            raise DataNotFoundError(f"No weight data found for index {symbol}")

        records = []
        for item in data["result"]["data"]:
            records.append({
                "index_code": symbol,
                "symbol": item.get("SECURITY_CODE", ""),
                "name": item.get("SECURITY_NAME_ABBR", ""),
                "weight": item.get("WEIGHT"),
            })

        return pd.DataFrame(records)

    # =========================================================================
    # ETF Enhanced Methods
    # =========================================================================

    def fetch_etf_share_change(
        self,
        symbol: str,
        days: int = 30,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """
        Fetch ETF share change data.

        Args:
            symbol: ETF symbol.
            days: Number of days.

        Returns:
            DataFrame with share change data.
        """
        params = {
            "sortColumns": "TRADE_DATE",
            "sortTypes": "-1",
            "pageSize": str(days),
            "pageNumber": "1",
            "reportName": "RPT_FUND_SHARES_CHANGE",
            "columns": "ALL",
            "filter": f'(FUND_CODE="{symbol}")',
        }

        data = self._get_json(
            "https://datacenter-web.eastmoney.com/api/data/v1/get",
            params=params,
        )

        if not data.get("result") or not data["result"].get("data"):
            return pd.DataFrame()

        records = []
        for item in data["result"]["data"]:
            records.append({
                "date": item.get("TRADE_DATE", "")[:10],
                "symbol": symbol,
                "shares": item.get("FUND_SHARE"),
                "shares_change": item.get("FUND_SHARE_CHANGE"),
                "shares_change_pct": item.get("FUND_SHARE_CHANGE_RATE"),
            })

        df = pd.DataFrame(records)
        if not df.empty and "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"]).dt.date
        return df

    def fetch_etf_premium_discount(
        self,
        symbol: str,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """
        Fetch ETF premium/discount data.

        Args:
            symbol: ETF symbol.

        Returns:
            DataFrame with premium/discount data.
        """
        params = {
            "sortColumns": "TRADE_DATE",
            "sortTypes": "-1",
            "pageSize": "100",
            "pageNumber": "1",
            "reportName": "RPT_ETF_JYGM",
            "columns": "ALL",
            "filter": f'(FUND_CODE="{symbol}")',
        }

        data = self._get_json(
            "https://datacenter-web.eastmoney.com/api/data/v1/get",
            params=params,
        )

        if not data.get("result") or not data["result"].get("data"):
            return pd.DataFrame()

        records = []
        for item in data["result"]["data"]:
            records.append({
                "date": item.get("TRADE_DATE", "")[:10],
                "symbol": symbol,
                "price": item.get("CLOSE_PRICE"),
                "nav": item.get("NAV"),
                "premium_rate": item.get("PREMIUM_RATE"),
            })

        df = pd.DataFrame(records)
        if not df.empty and "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"]).dt.date
        return df

    # =========================================================================
    # Forex Data Methods
    # =========================================================================

    def fetch_exchange_rate(
        self,
        base: str = "USD",
        target: str = "CNY",
        **kwargs: Any,
    ) -> pd.DataFrame:
        """
        Fetch current exchange rate.

        Args:
            base: Base currency code.
            target: Target currency code.

        Returns:
            DataFrame with exchange rate.
        """
        # Currency pair mapping
        pair_map = {
            ("USD", "CNY"): "133.USDCNH",
            ("EUR", "CNY"): "133.EURCNH",
            ("GBP", "CNY"): "133.GBPCNH",
            ("JPY", "CNY"): "133.JPYCNH",
            ("HKD", "CNY"): "133.HKDCNH",
        }

        secid = pair_map.get((base.upper(), target.upper()))
        if not secid:
            raise DataNotFoundError(f"Currency pair {base}/{target} not supported")

        params = {
            "secid": secid,
            "fields": "f43,f44,f45,f46,f60,f170",
        }

        data = self._get_json(
            "https://push2.eastmoney.com/api/qt/stock/get",
            params=params,
        )

        if not data.get("data"):
            raise DataNotFoundError(f"No exchange rate data for {base}/{target}")

        item = data["data"]
        record = {
            "base": base.upper(),
            "target": target.upper(),
            "rate": item.get("f43") / 10000 if item.get("f43") else None,
            "open": item.get("f46") / 10000 if item.get("f46") else None,
            "high": item.get("f44") / 10000 if item.get("f44") else None,
            "low": item.get("f45") / 10000 if item.get("f45") else None,
            "pre_close": item.get("f60") / 10000 if item.get("f60") else None,
            "change_pct": item.get("f170") / 100 if item.get("f170") else None,
        }

        return pd.DataFrame([record])

    def fetch_exchange_rate_history(
        self,
        base: str,
        target: str,
        start_date: str | date | None = None,
        end_date: str | date | None = None,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """
        Fetch historical exchange rate data.

        Args:
            base: Base currency code.
            target: Target currency code.
            start_date: Start date.
            end_date: End date.

        Returns:
            DataFrame with historical exchange rates.
        """
        # Currency pair mapping
        pair_map = {
            ("USD", "CNY"): "133.USDCNH",
            ("EUR", "CNY"): "133.EURCNH",
            ("GBP", "CNY"): "133.GBPCNH",
            ("JPY", "CNY"): "133.JPYCNH",
            ("HKD", "CNY"): "133.HKDCNH",
        }

        secid = pair_map.get((base.upper(), target.upper()))
        if not secid:
            raise DataNotFoundError(f"Currency pair {base}/{target} not supported")

        # Format dates
        if start_date is None:
            start_date = "19900101"
        elif isinstance(start_date, (date, datetime)):
            start_date = start_date.strftime("%Y%m%d")
        else:
            start_date = start_date.replace("-", "")

        if end_date is None:
            end_date = datetime.now().strftime("%Y%m%d")
        elif isinstance(end_date, (date, datetime)):
            end_date = end_date.strftime("%Y%m%d")
        else:
            end_date = end_date.replace("-", "")

        params = {
            "secid": secid,
            "fields1": "f1,f2,f3,f4,f5,f6",
            "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
            "klt": "101",
            "fqt": "1",
            "beg": start_date,
            "end": end_date,
        }

        data = self._get_json(
            "https://push2his.eastmoney.com/api/qt/stock/kline/get",
            params=params,
        )

        if not data.get("data") or not data["data"].get("klines"):
            raise DataNotFoundError(f"No historical exchange rate data for {base}/{target}")

        records = []
        for line in data["data"]["klines"]:
            parts = line.split(",")
            if len(parts) >= 5:
                records.append({
                    "date": parts[0],
                    "base": base.upper(),
                    "target": target.upper(),
                    "open": float(parts[1]),
                    "close": float(parts[2]),
                    "high": float(parts[3]),
                    "low": float(parts[4]),
                })

        df = pd.DataFrame(records)
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"]).dt.date
        return df


# Global adapter instance
eastmoney_adapter = EastMoneyAdapter()
