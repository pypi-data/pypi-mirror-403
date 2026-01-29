"""
Yahoo Finance data adapter.

This module provides data fetching from Yahoo Finance,
a global financial data source supporting stocks, ETFs, and more.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Any

import pandas as pd

from finvista._core.exceptions import DataNotFoundError
from finvista._fetchers.adapters.base import BaseAdapter

logger = logging.getLogger(__name__)


class YahooAdapter(BaseAdapter):
    """
    Adapter for Yahoo Finance data source.

    This adapter provides access to:
    - US stock historical data
    - US stock quotes
    - Global stock data
    - ETF data

    Example:
        >>> adapter = YahooAdapter()
        >>> df = adapter.fetch_stock_daily("AAPL", start_date="2024-01-01")
    """

    name = "yahoo"
    base_url = "https://query1.finance.yahoo.com"

    def is_available(self) -> bool:
        """Check if Yahoo Finance API is available."""
        try:
            # Test with a known symbol
            response = self._get_text(
                "https://query1.finance.yahoo.com/v8/finance/chart/AAPL",
                params={"interval": "1d", "range": "1d"},
            )
            return '"chart"' in response
        except Exception:
            return False

    def _get_crumb_and_cookies(self) -> tuple[str, dict[str, str]]:
        """
        Get crumb and cookies required for Yahoo Finance API.

        Returns:
            Tuple of (crumb, cookies).

        Note:
            This method is reserved for future use when Yahoo Finance
            requires authentication for certain endpoints.
        """
        # Currently not implemented - Yahoo Finance public API doesn't require crumb
        return "", {}

    def fetch_stock_daily(
        self,
        symbol: str,
        start_date: str | date | None = None,
        end_date: str | date | None = None,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """
        Fetch daily stock data from Yahoo Finance.

        Args:
            symbol: Stock symbol (e.g., "AAPL", "MSFT").
            start_date: Start date.
            end_date: End date.

        Returns:
            DataFrame with daily OHLCV data.
        """
        # Format dates to timestamps
        if start_date is None:
            start_ts = int((datetime.now() - timedelta(days=365)).timestamp())
        elif isinstance(start_date, str):
            start_dt = datetime.strptime(start_date.replace("-", ""), "%Y%m%d")
            start_ts = int(start_dt.timestamp())
        else:
            start_ts = int(datetime.combine(start_date, datetime.min.time()).timestamp())

        if end_date is None:
            end_ts = int(datetime.now().timestamp())
        elif isinstance(end_date, str):
            end_dt = datetime.strptime(end_date.replace("-", ""), "%Y%m%d")
            end_ts = int(end_dt.timestamp())
        else:
            end_ts = int(datetime.combine(end_date, datetime.min.time()).timestamp())

        # Use the chart API endpoint
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        params = {
            "period1": start_ts,
            "period2": end_ts,
            "interval": "1d",
            "events": "history",
        }

        try:
            data = self._get_json(url, params=params)
        except Exception as e:
            raise DataNotFoundError(f"Failed to fetch data for {symbol}: {e}") from e

        if not data.get("chart") or not data["chart"].get("result"):
            raise DataNotFoundError(f"No data found for symbol {symbol}")

        result = data["chart"]["result"][0]
        timestamps = result.get("timestamp", [])
        indicators = result.get("indicators", {})
        quote = indicators.get("quote", [{}])[0]
        adjclose = indicators.get("adjclose", [{}])

        if not timestamps:
            raise DataNotFoundError(f"No data found for symbol {symbol}")

        records = []
        for i, ts in enumerate(timestamps):
            try:
                dt = datetime.fromtimestamp(ts)
                records.append({
                    "date": dt.date(),
                    "open": quote.get("open", [None])[i],
                    "high": quote.get("high", [None])[i],
                    "low": quote.get("low", [None])[i],
                    "close": quote.get("close", [None])[i],
                    "volume": quote.get("volume", [None])[i],
                    "adj_close": adjclose[0].get("adjclose", [None])[i] if adjclose else None,
                })
            except (IndexError, TypeError):
                continue

        if not records:
            raise DataNotFoundError(f"No data found for symbol {symbol}")

        df = pd.DataFrame(records)
        df = df.dropna(subset=["close"])

        return df.sort_values("date").reset_index(drop=True)

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

        symbols_str = ",".join(symbols)

        url = "https://query1.finance.yahoo.com/v7/finance/quote"
        params = {
            "symbols": symbols_str,
        }

        try:
            data = self._get_json(url, params=params)
        except Exception as e:
            raise DataNotFoundError(f"Failed to fetch quotes: {e}") from e

        if not data.get("quoteResponse") or not data["quoteResponse"].get("result"):
            raise DataNotFoundError(f"No quote data found for symbols: {symbols}")

        records = []
        for item in data["quoteResponse"]["result"]:
            records.append({
                "symbol": item.get("symbol", ""),
                "name": item.get("shortName", ""),
                "price": item.get("regularMarketPrice"),
                "change": item.get("regularMarketChange"),
                "change_pct": item.get("regularMarketChangePercent"),
                "open": item.get("regularMarketOpen"),
                "high": item.get("regularMarketDayHigh"),
                "low": item.get("regularMarketDayLow"),
                "pre_close": item.get("regularMarketPreviousClose"),
                "volume": item.get("regularMarketVolume"),
                "market_cap": item.get("marketCap"),
                "pe": item.get("trailingPE"),
                "eps": item.get("epsTrailingTwelveMonths"),
                "dividend_yield": item.get("dividendYield"),
                "market_state": item.get("marketState"),
            })

        return pd.DataFrame(records)

    def fetch_stock_info(
        self,
        symbol: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Fetch detailed stock information.

        Args:
            symbol: Stock symbol.

        Returns:
            Dictionary with stock information.
        """
        url = f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{symbol}"
        params = {
            "modules": "assetProfile,summaryProfile,summaryDetail,defaultKeyStatistics",
        }

        try:
            data = self._get_json(url, params=params)
        except Exception as e:
            raise DataNotFoundError(f"Failed to fetch info for {symbol}: {e}") from e

        if not data.get("quoteSummary") or not data["quoteSummary"].get("result"):
            raise DataNotFoundError(f"No info found for symbol {symbol}")

        result = data["quoteSummary"]["result"][0]
        info = {"symbol": symbol}

        # Asset profile
        asset_profile = result.get("assetProfile", {})
        info.update({
            "industry": asset_profile.get("industry"),
            "sector": asset_profile.get("sector"),
            "country": asset_profile.get("country"),
            "website": asset_profile.get("website"),
            "employees": asset_profile.get("fullTimeEmployees"),
            "description": asset_profile.get("longBusinessSummary"),
        })

        # Summary detail
        summary = result.get("summaryDetail", {})
        info.update({
            "market_cap": self._get_raw_value(summary, "marketCap"),
            "pe_trailing": self._get_raw_value(summary, "trailingPE"),
            "pe_forward": self._get_raw_value(summary, "forwardPE"),
            "dividend_yield": self._get_raw_value(summary, "dividendYield"),
            "beta": self._get_raw_value(summary, "beta"),
            "52_week_high": self._get_raw_value(summary, "fiftyTwoWeekHigh"),
            "52_week_low": self._get_raw_value(summary, "fiftyTwoWeekLow"),
        })

        # Key statistics
        stats = result.get("defaultKeyStatistics", {})
        info.update({
            "shares_outstanding": self._get_raw_value(stats, "sharesOutstanding"),
            "float_shares": self._get_raw_value(stats, "floatShares"),
            "book_value": self._get_raw_value(stats, "bookValue"),
            "price_to_book": self._get_raw_value(stats, "priceToBook"),
        })

        return info

    def _get_raw_value(self, data: dict[str, Any], key: str) -> Any:
        """Extract raw value from Yahoo Finance data structure."""
        if key not in data:
            return None
        value = data[key]
        if isinstance(value, dict):
            return value.get("raw")
        return value

    def search_stocks(
        self,
        query: str,
        limit: int = 10,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """
        Search for stocks by keyword.

        Args:
            query: Search query.
            limit: Maximum number of results.

        Returns:
            DataFrame with search results.
        """
        url = "https://query1.finance.yahoo.com/v1/finance/search"
        params = {
            "q": query,
            "quotesCount": limit,
            "newsCount": 0,
            "enableFuzzyQuery": True,
            "quotesQueryId": "tss_match_phrase_query",
        }

        try:
            data = self._get_json(url, params=params)
        except Exception as e:
            raise DataNotFoundError(f"Search failed: {e}") from e

        quotes = data.get("quotes", [])
        if not quotes:
            return pd.DataFrame()

        records = []
        for item in quotes:
            records.append({
                "symbol": item.get("symbol", ""),
                "name": item.get("shortname", "") or item.get("longname", ""),
                "type": item.get("typeDisp", ""),
                "exchange": item.get("exchange", ""),
            })

        return pd.DataFrame(records)


# Global adapter instance
yahoo_adapter = YahooAdapter()
