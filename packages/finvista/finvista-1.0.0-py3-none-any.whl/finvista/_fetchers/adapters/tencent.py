"""
Tencent Finance (腾讯财经) data adapter.

This module provides data fetching from Tencent Finance,
known for reliable real-time quote data.
"""

from __future__ import annotations

import logging
import re
from datetime import date, datetime
from typing import Any

import pandas as pd

from finvista._core.exceptions import DataNotFoundError
from finvista._fetchers.adapters.base import BaseAdapter

logger = logging.getLogger(__name__)


class TencentAdapter(BaseAdapter):
    """
    Adapter for Tencent Finance (腾讯财经) data source.

    This adapter provides access to:
    - A-share real-time quotes
    - A-share historical data
    - Index data

    Example:
        >>> adapter = TencentAdapter()
        >>> df = adapter.fetch_stock_quote(["000001", "600519"])
    """

    name = "tencent"
    base_url = "https://qt.gtimg.cn"

    def is_available(self) -> bool:
        """Check if Tencent API is available."""
        try:
            response = self._get_text("https://qt.gtimg.cn/q=sh000001")
            return "v_sh000001" in response
        except Exception:
            return False

    def _get_tencent_symbol(self, symbol: str) -> str:
        """
        Convert symbol to Tencent format.

        Args:
            symbol: Stock symbol.

        Returns:
            Tencent-formatted symbol (e.g., 'sz000001').
        """
        if symbol.startswith(("6", "9")):
            return f"sh{symbol}"
        else:
            return f"sz{symbol}"

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

        Raises:
            DataNotFoundError: When no data is found.
        """
        if isinstance(symbols, str):
            symbols = [symbols]

        tencent_symbols = [self._get_tencent_symbol(s) for s in symbols]
        symbols_str = ",".join(tencent_symbols)

        response = self._get_text(
            f"https://qt.gtimg.cn/q={symbols_str}",
            encoding="gbk",
        )

        records = []
        pattern = r'v_(\w+)="([^"]*)"'

        for match in re.finditer(pattern, response):
            tencent_symbol = match.group(1)
            data_str = match.group(2)

            if not data_str:
                continue

            parts = data_str.split("~")
            if len(parts) < 45:
                continue

            symbol = parts[2] if len(parts) > 2 else tencent_symbol[2:]

            try:
                records.append({
                    "symbol": symbol,
                    "name": parts[1],
                    "price": float(parts[3]) if parts[3] else None,
                    "pre_close": float(parts[4]) if parts[4] else None,
                    "open": float(parts[5]) if parts[5] else None,
                    "volume": int(float(parts[6]) * 100) if parts[6] else 0,  # In lots
                    "amount": float(parts[37]) * 10000 if len(parts) > 37 and parts[37] else 0,
                    "high": float(parts[33]) if len(parts) > 33 and parts[33] else None,
                    "low": float(parts[34]) if len(parts) > 34 and parts[34] else None,
                    "change": float(parts[31]) if len(parts) > 31 and parts[31] else None,
                    "change_pct": float(parts[32]) if len(parts) > 32 and parts[32] else None,
                    "turnover": float(parts[38]) if len(parts) > 38 and parts[38] else None,
                    "pe": float(parts[39]) if len(parts) > 39 and parts[39] else None,
                    "pb": float(parts[46]) if len(parts) > 46 and parts[46] else None,
                    "market_cap": float(parts[45]) if len(parts) > 45 and parts[45] else None,
                    "time": parts[30] if len(parts) > 30 else None,
                })
            except (ValueError, IndexError) as e:
                logger.warning(f"Failed to parse quote for {symbol}: {e}")
                continue

        if not records:
            raise DataNotFoundError(f"No quote data found for symbols: {symbols}")

        return pd.DataFrame(records)

    def fetch_stock_daily(
        self,
        symbol: str,
        start_date: str | date | None = None,
        end_date: str | date | None = None,
        adjust: str = "none",
        **kwargs: Any,
    ) -> pd.DataFrame:
        """
        Fetch daily stock data from Tencent.

        Args:
            symbol: Stock symbol.
            start_date: Start date.
            end_date: End date.
            adjust: Adjustment type (only 'none' supported).

        Returns:
            DataFrame with daily OHLCV data.
        """
        tencent_symbol = self._get_tencent_symbol(symbol)

        # Calculate number of years to fetch
        if start_date:
            if isinstance(start_date, str):
                start_dt = datetime.strptime(start_date.replace("-", ""), "%Y%m%d")
            else:
                start_dt = datetime.combine(start_date, datetime.min.time())
            years = (datetime.now() - start_dt).days // 365 + 1
        else:
            years = 10

        # Tencent provides data in yearly chunks
        all_records = []

        for year_offset in range(years):
            year = datetime.now().year - year_offset
            url = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
            params = {
                "_var": f"kline_dayqfq{year}",
                "param": f"{tencent_symbol},day,{year}-01-01,{year}-12-31,640,qfq",
            }

            try:
                response = self._get_text(url, params=params)

                # Parse JSONP response
                import json
                match = re.search(r'=(\{.*\})', response)
                if not match:
                    continue

                data = json.loads(match.group(1))

                # Extract kline data
                stock_data = data.get("data", {}).get(tencent_symbol, {})
                klines = stock_data.get("day", []) or stock_data.get("qfqday", [])

                for item in klines:
                    if len(item) >= 6:
                        all_records.append({
                            "date": item[0],
                            "open": float(item[1]),
                            "close": float(item[2]),
                            "high": float(item[3]),
                            "low": float(item[4]),
                            "volume": int(float(item[5])),
                        })
            except Exception as e:
                logger.warning(f"Failed to fetch data for year {year}: {e}")
                continue

        if not all_records:
            raise DataNotFoundError(f"No data found for {symbol}")

        df = pd.DataFrame(all_records)
        df["date"] = pd.to_datetime(df["date"]).dt.date

        # Filter by date range
        if start_date:
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date.replace("-", ""), "%Y%m%d").date()
            df = df[df["date"] >= start_date]

        if end_date:
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date.replace("-", ""), "%Y%m%d").date()
            df = df[df["date"] <= end_date]

        return df.drop_duplicates("date").sort_values("date").reset_index(drop=True)

    def fetch_stock_list(
        self,
        market: str = "all",
        **kwargs: Any,
    ) -> pd.DataFrame:
        """
        Fetch list of A-share stocks.

        Note: Tencent doesn't provide a simple stock list API,
        so this method fetches from an alternative endpoint.

        Args:
            market: Market filter ('all', 'sh', 'sz').

        Returns:
            DataFrame with stock information.
        """
        records = []

        # Fetch from different markets
        markets_to_fetch = []
        if market in ("all", "sh"):
            markets_to_fetch.append(("sh", "1"))
        if market in ("all", "sz"):
            markets_to_fetch.append(("sz", "2"))

        for market_name, market_id in markets_to_fetch:
            try:
                url = "https://stock.gtimg.cn/data/index.php"
                params = {
                    "appn": "rank",
                    "t": f"rank{market_name}/chr",
                    "p": "1",
                    "o": "0",
                    "l": "1000",
                    "v": "list_data",
                }

                response = self._get_text(url, params=params, encoding="gbk")

                # Parse the response
                match = re.search(r'"([^"]+)"', response)
                if match:
                    data_str = match.group(1)
                    items = data_str.split("^")

                    for item in items:
                        parts = item.split("~")
                        if len(parts) >= 3:
                            records.append({
                                "symbol": parts[1],
                                "name": parts[2],
                                "market": market_name,
                                "price": float(parts[3]) if len(parts) > 3 and parts[3] else None,
                            })
            except Exception as e:
                logger.warning(f"Failed to fetch {market_name} stocks: {e}")
                continue

        if not records:
            raise DataNotFoundError("No stock list found")

        df = pd.DataFrame(records)
        df = df[df["symbol"].str.len() == 6]

        return df


# Global adapter instance
tencent_adapter = TencentAdapter()
