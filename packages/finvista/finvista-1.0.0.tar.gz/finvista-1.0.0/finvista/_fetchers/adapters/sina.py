"""
Sina Finance (新浪财经) data adapter.

This module provides data fetching from Sina Finance, a popular
financial data source in China with good real-time quote support.
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


class SinaAdapter(BaseAdapter):
    """
    Adapter for Sina Finance (新浪财经) data source.

    This adapter provides access to:
    - A-share real-time quotes (fast updates)
    - A-share historical data
    - Index data

    Example:
        >>> adapter = SinaAdapter()
        >>> df = adapter.fetch_stock_quote(["000001", "600519"])
    """

    name = "sina"
    base_url = "https://hq.sinajs.cn"

    # Market prefix mapping
    MARKET_PREFIX = {
        "sh": "sh",  # Shanghai
        "sz": "sz",  # Shenzhen
    }

    def is_available(self) -> bool:
        """Check if Sina API is available."""
        try:
            response = self._get_text(
                "https://hq.sinajs.cn/list=sh000001",
                headers={"Referer": "https://finance.sina.com.cn"},
            )
            return "var hq_str" in response
        except Exception:
            return False

    def _get_market_prefix(self, symbol: str) -> str:
        """
        Get market prefix for a symbol.

        Args:
            symbol: Stock symbol (e.g., '000001', '600519').

        Returns:
            Market prefix ('sh' or 'sz').
        """
        if symbol.startswith(("6", "9")):
            return "sh"
        else:
            return "sz"

    def _get_sina_symbol(self, symbol: str) -> str:
        """
        Convert symbol to Sina format.

        Args:
            symbol: Stock symbol.

        Returns:
            Sina-formatted symbol (e.g., 'sz000001').
        """
        prefix = self._get_market_prefix(symbol)
        return f"{prefix}{symbol}"

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
            DataParsingError: When data cannot be parsed.
        """
        if isinstance(symbols, str):
            symbols = [symbols]

        sina_symbols = [self._get_sina_symbol(s) for s in symbols]
        symbols_str = ",".join(sina_symbols)

        response = self._get_text(
            f"https://hq.sinajs.cn/list={symbols_str}",
            headers={"Referer": "https://finance.sina.com.cn"},
            encoding="gbk",
        )

        records = []
        pattern = r'var hq_str_(\w+)="([^"]*)"'

        for match in re.finditer(pattern, response):
            sina_symbol = match.group(1)
            data_str = match.group(2)

            if not data_str:
                continue

            parts = data_str.split(",")
            if len(parts) < 32:
                continue

            # Extract symbol without prefix
            symbol = sina_symbol[2:]

            try:
                records.append({
                    "symbol": symbol,
                    "name": parts[0],
                    "open": float(parts[1]) if parts[1] else None,
                    "pre_close": float(parts[2]) if parts[2] else None,
                    "price": float(parts[3]) if parts[3] else None,
                    "high": float(parts[4]) if parts[4] else None,
                    "low": float(parts[5]) if parts[5] else None,
                    "volume": int(float(parts[8])) if parts[8] else 0,
                    "amount": float(parts[9]) if parts[9] else 0,
                    "change": float(parts[3]) - float(parts[2]) if parts[3] and parts[2] else None,
                    "change_pct": round(
                        (float(parts[3]) - float(parts[2])) / float(parts[2]) * 100, 2
                    ) if parts[3] and parts[2] and float(parts[2]) != 0 else None,
                    "date": parts[30] if len(parts) > 30 else None,
                    "time": parts[31] if len(parts) > 31 else None,
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
        Fetch daily stock data from Sina.

        Args:
            symbol: Stock symbol.
            start_date: Start date.
            end_date: End date.
            adjust: Adjustment type ('none', 'qfq', 'hfq').

        Returns:
            DataFrame with daily OHLCV data.
        """
        sina_symbol = self._get_sina_symbol(symbol)

        # Use the historical data API
        url = f"https://quotes.sina.cn/cn/api/jsonp.php/var%20_{sina_symbol}=/CN_MarketDataService.getKLineData"
        params = {
            "symbol": sina_symbol,
            "scale": "240",  # Daily
            "ma": "no",
            "datalen": "1000",
        }

        response = self._get_text(url, params=params)

        # Parse JSONP response
        match = re.search(r'\[.*\]', response)
        if not match:
            raise DataNotFoundError(f"No data found for {symbol}")

        import json
        try:
            data = json.loads(match.group())
        except json.JSONDecodeError as e:
            raise DataParsingError(f"Failed to parse JSON: {e}") from e

        if not data:
            raise DataNotFoundError(f"No data found for {symbol}")

        records = []
        for item in data:
            try:
                records.append({
                    "date": item.get("day"),
                    "open": float(item.get("open", 0)),
                    "high": float(item.get("high", 0)),
                    "low": float(item.get("low", 0)),
                    "close": float(item.get("close", 0)),
                    "volume": int(float(item.get("volume", 0))),
                })
            except (ValueError, TypeError) as e:
                logger.warning(f"Failed to parse record: {e}")
                continue

        df = pd.DataFrame(records)
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

        return df.sort_values("date").reset_index(drop=True)

    def fetch_index_quote(
        self,
        symbols: list[str] | str,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """
        Fetch real-time index quotes.

        Args:
            symbols: Single symbol or list of symbols.
                    Use '000001' for SSE Composite, '399001' for SZSE Component.

        Returns:
            DataFrame with index quote data.
        """
        if isinstance(symbols, str):
            symbols = [symbols]

        # Convert to Sina index format
        sina_symbols = []
        for s in symbols:
            if s.startswith("0"):
                sina_symbols.append(f"sh{s}")  # Shanghai index
            elif s.startswith("3"):
                sina_symbols.append(f"sz{s}")  # Shenzhen index
            else:
                sina_symbols.append(f"sh{s}")

        symbols_str = ",".join(sina_symbols)

        response = self._get_text(
            f"https://hq.sinajs.cn/list={symbols_str}",
            headers={"Referer": "https://finance.sina.com.cn"},
            encoding="gbk",
        )

        records = []
        pattern = r'var hq_str_(\w+)="([^"]*)"'

        for match in re.finditer(pattern, response):
            sina_symbol = match.group(1)
            data_str = match.group(2)

            if not data_str:
                continue

            parts = data_str.split(",")
            if len(parts) < 9:
                continue

            symbol = sina_symbol[2:]

            try:
                records.append({
                    "symbol": symbol,
                    "name": parts[0],
                    "price": float(parts[1]) if parts[1] else None,
                    "change": float(parts[2]) if parts[2] else None,
                    "change_pct": float(parts[3]) if parts[3] else None,
                    "volume": int(float(parts[4])) if parts[4] else 0,
                    "amount": float(parts[5]) if parts[5] else 0,
                })
            except (ValueError, IndexError) as e:
                logger.warning(f"Failed to parse index {symbol}: {e}")
                continue

        if not records:
            raise DataNotFoundError("No index data found")

        return pd.DataFrame(records)


    def fetch_us_index_daily(
        self,
        symbol: str = ".DJI",
        start_date: str | date | None = None,
        end_date: str | date | None = None,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """
        Fetch US index daily data from Sina.

        Args:
            symbol: Index symbol, options:
                - ".DJI": Dow Jones Industrial Average
                - ".IXIC": NASDAQ Composite
                - ".INX": S&P 500
            start_date: Start date.
            end_date: End date.

        Returns:
            DataFrame with columns: date, open, high, low, close, volume
        """
        import json

        # Sina symbol format for US indices
        sina_symbol = f"gb_{symbol.replace('.', '$')}"

        # Use the historical data API
        full_url = f"https://stock.finance.sina.com.cn/usstock/api/jsonp.php/var%20temp=/US_MinKService.getDailyK?symbol={sina_symbol}&type=daily"
        response = self._get_text(full_url)

        # Parse JSONP response
        match = re.search(r'\[.*\]', response)
        if not match:
            raise DataNotFoundError(f"No data found for US index {symbol}")

        try:
            data = json.loads(match.group())
        except json.JSONDecodeError as e:
            raise DataParsingError(f"Failed to parse JSON: {e}") from e

        if not data:
            raise DataNotFoundError(f"No data found for US index {symbol}")

        records = []
        for item in data:
            try:
                records.append({
                    "date": item.get("d"),
                    "open": float(item.get("o", 0)),
                    "high": float(item.get("h", 0)),
                    "low": float(item.get("l", 0)),
                    "close": float(item.get("c", 0)),
                    "volume": int(float(item.get("v", 0))) if item.get("v") else 0,
                })
            except (ValueError, TypeError) as e:
                logger.warning(f"Failed to parse record: {e}")
                continue

        df = pd.DataFrame(records)
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

        return df.sort_values("date").reset_index(drop=True)


# Global adapter instance
sina_adapter = SinaAdapter()
