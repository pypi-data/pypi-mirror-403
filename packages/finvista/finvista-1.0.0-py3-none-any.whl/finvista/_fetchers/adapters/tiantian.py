"""
Tiantian Fund (天天基金) data adapter.

This module provides data fetching from Tiantian Fund, the most popular
fund data platform in China, operated by East Money.
"""

from __future__ import annotations

import logging
import re
from datetime import date, datetime
from typing import Any

import pandas as pd

from finvista._core.exceptions import DataNotFoundError, DataParsingError
from finvista._fetchers.adapters.base import BaseAdapter

logger = logging.getLogger(__name__)


class TiantianAdapter(BaseAdapter):
    """
    Adapter for Tiantian Fund (天天基金) data source.

    This adapter provides access to:
    - Fund NAV (net asset value) data
    - Fund list
    - Fund information

    Example:
        >>> adapter = TiantianAdapter()
        >>> df = adapter.fetch_fund_nav("000001", start_date="2024-01-01")
    """

    name = "tiantian"
    base_url = "https://fund.eastmoney.com"

    def is_available(self) -> bool:
        """Check if Tiantian Fund API is available."""
        try:
            response = self._get_text(
                "https://fund.eastmoney.com/js/fundcode_search.js"
            )
            return "var r = [" in response
        except Exception:
            return False

    def fetch_fund_nav(
        self,
        symbol: str,
        start_date: str | date | None = None,
        end_date: str | date | None = None,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """
        Fetch fund NAV (net asset value) history.

        Args:
            symbol: Fund symbol (e.g., "000001").
            start_date: Start date.
            end_date: End date.

        Returns:
            DataFrame with NAV history.
        """
        # Format dates
        if start_date is None:
            start_str = "2000-01-01"
        elif isinstance(start_date, (date, datetime)):
            start_str = start_date.strftime("%Y-%m-%d")
        else:
            start_str = start_date

        if end_date is None:
            end_str = datetime.now().strftime("%Y-%m-%d")
        elif isinstance(end_date, (date, datetime)):
            end_str = end_date.strftime("%Y-%m-%d")
        else:
            end_str = end_date

        # Fetch data from API
        # Note: API has a pageSize limit around 100-500
        url = "https://api.fund.eastmoney.com/f10/lsjz"
        params = {
            "fundCode": symbol,
            "pageIndex": 1,
            "pageSize": 100,
            "startDate": start_str,
            "endDate": end_str,
        }
        headers = {
            "Referer": f"https://fundf10.eastmoney.com/jjjz_{symbol}.html",
        }

        try:
            data = self._get_json(url, params=params, headers=headers)
        except Exception as e:
            logger.warning(f"Failed to fetch fund NAV from API: {e}")
            # Fallback to web scraping
            return self._fetch_fund_nav_fallback(symbol, start_str, end_str)

        if not data.get("Data") or not data["Data"].get("LSJZList"):
            raise DataNotFoundError(f"No NAV data found for fund {symbol}")

        records = []
        for item in data["Data"]["LSJZList"]:
            try:
                nav = float(item.get("DWJZ", 0)) if item.get("DWJZ") else None
                acc_nav = float(item.get("LJJZ", 0)) if item.get("LJJZ") else None
                daily_return = item.get("JZZZL", "")
                daily_return = float(daily_return) if daily_return and daily_return != "" else None

                records.append({
                    "date": item.get("FSRQ"),
                    "nav": nav,  # Unit NAV (单位净值)
                    "acc_nav": acc_nav,  # Accumulated NAV (累计净值)
                    "daily_return": daily_return,  # Daily return %
                })
            except (ValueError, TypeError) as e:
                logger.warning(f"Failed to parse NAV record: {e}")
                continue

        if not records:
            raise DataNotFoundError(f"No NAV data found for fund {symbol}")

        df = pd.DataFrame(records)
        df["date"] = pd.to_datetime(df["date"]).dt.date
        df = df.sort_values("date").reset_index(drop=True)

        return df

    def _fetch_fund_nav_fallback(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
    ) -> pd.DataFrame:
        """Fallback method to fetch NAV by scraping."""
        # Use the alternative endpoint
        url = "https://fund.eastmoney.com/f10/F10DataApi.aspx"
        params = {
            "type": "lsjz",
            "code": symbol,
            "page": 1,
            "per": 10000,
            "sdate": start_date,
            "edate": end_date,
        }

        response = self._get_text(url, params=params, encoding="utf-8")

        # Parse the HTML table
        records = []
        pattern = r'<td[^>]*>([^<]*)</td>'
        matches = re.findall(pattern, response)

        # Data comes in groups of 7 columns
        # Date, NAV, Acc NAV, Daily Return, Buy Status, Sell Status, Dividend
        for i in range(0, len(matches) - 6, 7):
            try:
                date_str = matches[i].strip()
                nav = float(matches[i + 1]) if matches[i + 1] else None
                acc_nav = float(matches[i + 2]) if matches[i + 2] else None
                daily_return_str = matches[i + 3].replace("%", "").strip()
                daily_return = float(daily_return_str) if daily_return_str else None

                records.append({
                    "date": date_str,
                    "nav": nav,
                    "acc_nav": acc_nav,
                    "daily_return": daily_return,
                })
            except (ValueError, IndexError):
                continue

        if not records:
            raise DataNotFoundError(f"No NAV data found for fund {symbol}")

        df = pd.DataFrame(records)
        df["date"] = pd.to_datetime(df["date"]).dt.date
        df = df.sort_values("date").reset_index(drop=True)

        return df

    def fetch_fund_info(
        self,
        symbol: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Fetch fund basic information.

        Args:
            symbol: Fund symbol.

        Returns:
            Dictionary with fund information.
        """
        url = f"https://fundf10.eastmoney.com/jbgk_{symbol}.html"

        try:
            response = self._get_text(url, encoding="utf-8")
        except Exception as e:
            raise DataNotFoundError(f"Failed to fetch fund info: {e}") from e

        info = {"symbol": symbol}

        # Parse fund name
        name_match = re.search(r'<span class="title-text">([^<]+)</span>', response)
        if name_match:
            info["name"] = name_match.group(1).strip()

        # Parse table data
        patterns = {
            "type": r'基金类型[^<]*</th>\s*<td[^>]*>([^<]+)',
            "inception_date": r'成立日期/规模[^<]*</th>\s*<td[^>]*>([^/]+)',
            "manager": r'基金经理[^<]*</th>\s*<td[^>]*><a[^>]*>([^<]+)',
            "company": r'基金管理人[^<]*</th>\s*<td[^>]*><a[^>]*>([^<]+)',
            "benchmark": r'业绩比较基准[^<]*</th>\s*<td[^>]*>([^<]+)',
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, response)
            if match:
                info[key] = match.group(1).strip()

        return info

    def fetch_fund_list(
        self,
        fund_type: str = "all",
        **kwargs: Any,
    ) -> pd.DataFrame:
        """
        Fetch list of funds.

        Args:
            fund_type: Fund type filter:
                - "all": All funds
                - "stock": Stock funds (股票型)
                - "mixed": Mixed funds (混合型)
                - "bond": Bond funds (债券型)
                - "index": Index funds (指数型)
                - "qdii": QDII funds
                - "money": Money market funds (货币型)
                - "etf": ETF funds

        Returns:
            DataFrame with fund information.
        """
        # Fetch fund list from JS file
        url = "https://fund.eastmoney.com/js/fundcode_search.js"

        response = self._get_text(url)

        # Parse the JavaScript array
        match = re.search(r'var r = (\[.*\])', response, re.DOTALL)
        if not match:
            raise DataNotFoundError("Failed to parse fund list")

        import json
        try:
            # The data is a JS array of arrays
            data_str = match.group(1)
            # Fix JS array format for JSON
            data_str = data_str.replace("'", '"')
            funds = json.loads(data_str)
        except json.JSONDecodeError as e:
            raise DataParsingError(f"Failed to parse fund list JSON: {e}") from e

        # Type mapping
        type_map = {
            "股票型": "stock",
            "混合型": "mixed",
            "债券型": "bond",
            "指数型": "index",
            "QDII": "qdii",
            "货币型": "money",
            "ETF-场内": "etf",
            "联接基金": "linked",
            "FOF": "fof",
        }

        records = []
        for fund in funds:
            if len(fund) >= 5:
                fund_type_cn = fund[3]
                fund_type_en = type_map.get(fund_type_cn, "other")

                records.append({
                    "symbol": fund[0],
                    "abbr": fund[1],  # Pinyin abbreviation
                    "name": fund[2],
                    "type_cn": fund_type_cn,
                    "type": fund_type_en,
                })

        df = pd.DataFrame(records)

        # Filter by type if specified
        if fund_type != "all":
            df = df[df["type"] == fund_type]

        return df.reset_index(drop=True)

    def fetch_fund_quote(
        self,
        symbols: list[str] | str,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """
        Fetch real-time fund NAV estimates.

        Args:
            symbols: Single symbol or list of symbols.

        Returns:
            DataFrame with estimated NAV data.
        """
        if isinstance(symbols, str):
            symbols = [symbols]

        records = []
        for symbol in symbols:
            try:
                url = f"https://fundgz.1234567.com.cn/js/{symbol}.js"
                response = self._get_text(url)

                # Parse JSONP response
                match = re.search(r'jsonpgz\((.*)\)', response)
                if not match:
                    continue

                import json
                data = json.loads(match.group(1))

                records.append({
                    "symbol": data.get("fundcode", symbol),
                    "name": data.get("name", ""),
                    "nav": float(data.get("dwjz", 0)) if data.get("dwjz") else None,
                    "estimated_nav": float(data.get("gsz", 0)) if data.get("gsz") else None,
                    "estimated_return": float(data.get("gszzl", 0)) if data.get("gszzl") else None,
                    "update_time": data.get("gztime", ""),
                })
            except Exception as e:
                logger.warning(f"Failed to fetch quote for fund {symbol}: {e}")
                continue

        if not records:
            raise DataNotFoundError(f"No quote data found for funds: {symbols}")

        return pd.DataFrame(records)


# Global adapter instance
tiantian_adapter = TiantianAdapter()
