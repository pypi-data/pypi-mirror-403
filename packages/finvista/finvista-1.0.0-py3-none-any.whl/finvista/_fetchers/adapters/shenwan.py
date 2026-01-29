#!/usr/bin/env python
"""
Shenwan (申万宏源研究) data adapter.

This module provides data fetching from Shenwan Research for industry index data.
https://www.swsresearch.com/
"""

from __future__ import annotations

import logging
import math

import pandas as pd
import requests
from tqdm import tqdm

from finvista._fetchers.adapters.base import BaseAdapter

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}


class ShenwanAdapter(BaseAdapter):
    """
    Adapter for Shenwan Research (申万宏源研究) data source.

    Provides access to:
    - Shenwan industry index data
    - Index historical data
    - Index analysis reports
    """

    name = "shenwan"
    base_url = "https://www.swsresearch.com"

    def is_available(self) -> bool:
        """Check if Shenwan Research API is available."""
        try:
            r = requests.get(
                f"{self.base_url}/institute-sw/api/index_publish/current/",
                params={"page": "1", "page_size": "1", "indextype": "一级行业"},
                headers=_HEADERS,
                timeout=10,
                verify=False,
            )
            return bool(r.status_code == 200)
        except Exception:
            return False

    def fetch_index_hist(
        self,
        symbol: str = "801030",
        period: str = "day",
    ) -> pd.DataFrame:
        """
        Fetch Shenwan index historical data.

        Args:
            symbol: Index code (e.g., "801030" for 基础化工)
            period: Data period, one of {"day", "week", "month"}

        Returns:
            DataFrame with historical index data.
        """
        period_map = {"day": "DAY", "week": "WEEK", "month": "MONTH"}
        url = f"{self.base_url}/institute-sw/api/index_publish/trend/"
        params = {"swindexcode": symbol, "period": period_map[period]}

        r = requests.get(url, params=params, headers=_HEADERS, verify=False)
        data_json = r.json()
        temp_df = pd.DataFrame(data_json["data"])
        temp_df.rename(
            columns={
                "swindexcode": "代码",
                "bargaindate": "日期",
                "openindex": "开盘",
                "maxindex": "最高",
                "minindex": "最低",
                "closeindex": "收盘",
                "bargainamount": "成交量",
                "bargainsum": "成交额",
            },
            inplace=True,
        )
        temp_df = temp_df[
            ["代码", "日期", "收盘", "开盘", "最高", "最低", "成交量", "成交额"]
        ]
        temp_df["日期"] = pd.to_datetime(temp_df["日期"], errors="coerce").dt.date
        temp_df["收盘"] = pd.to_numeric(temp_df["收盘"], errors="coerce")
        temp_df["最高"] = pd.to_numeric(temp_df["最高"], errors="coerce")
        temp_df["最低"] = pd.to_numeric(temp_df["最低"], errors="coerce")
        temp_df["成交量"] = pd.to_numeric(temp_df["成交量"], errors="coerce")
        temp_df["成交额"] = pd.to_numeric(temp_df["成交额"], errors="coerce")
        return temp_df

    def fetch_index_realtime(self, symbol: str = "一级行业") -> pd.DataFrame:
        """
        Fetch Shenwan index realtime data.

        Args:
            symbol: Index type, one of:
                {"市场表征", "一级行业", "二级行业", "风格指数"}

        Returns:
            DataFrame with realtime index data.
        """
        url = f"{self.base_url}/institute-sw/api/index_publish/current/"
        params = {"page": "1", "page_size": "50", "indextype": symbol}

        r = requests.get(url, params=params, headers=_HEADERS, verify=False)
        data_json = r.json()
        total_num = data_json["data"]["count"]
        total_page = math.ceil(total_num / 50)

        big_df = pd.DataFrame()
        for page in range(1, total_page + 1):
            params.update({"page": str(page)})
            r = requests.get(url, params=params, headers=_HEADERS, verify=False)
            data_json = r.json()
            temp_df = pd.DataFrame(data_json["data"]["results"])
            big_df = pd.concat(objs=[big_df, temp_df], ignore_index=True)

        big_df.columns = [
            "指数代码", "指数名称", "昨收盘", "今开盘", "成交额",
            "最高价", "最低价", "最新价", "成交量",
        ]
        big_df = big_df[
            ["指数代码", "指数名称", "昨收盘", "今开盘", "最新价",
             "成交额", "成交量", "最高价", "最低价"]
        ]
        for col in ["昨收盘", "今开盘", "最新价", "成交额", "成交量", "最高价", "最低价"]:
            big_df[col] = pd.to_numeric(big_df[col], errors="coerce")
        return big_df

    def fetch_index_analysis_daily(
        self,
        symbol: str = "一级行业",
        start_date: str = "20221103",
        end_date: str = "20221103",
    ) -> pd.DataFrame:
        """
        Fetch Shenwan index daily analysis data.

        Args:
            symbol: Index type, one of:
                {"市场表征", "一级行业", "二级行业", "风格指数"}
            start_date: Start date in YYYYMMDD format
            end_date: End date in YYYYMMDD format

        Returns:
            DataFrame with daily analysis data including PE, PB, etc.
        """
        url = f"{self.base_url}/institute-sw/api/index_analysis/index_analysis_report/"
        params = {
            "page": "1",
            "page_size": "50",
            "index_type": symbol,
            "start_date": f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]}",
            "end_date": f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:]}",
            "type": "DAY",
            "swindexcode": "all",
        }

        r = requests.get(url, params=params, headers=_HEADERS, verify=False)
        data_json = r.json()
        total_num = data_json["data"]["count"]
        total_page = math.ceil(total_num / 50)

        big_df = pd.DataFrame()
        for page in tqdm(range(1, total_page + 1), leave=False):
            params.update({"page": str(page)})
            r = requests.get(url, params=params, headers=_HEADERS, verify=False)
            data_json = r.json()
            temp_df = pd.DataFrame(data_json["data"]["results"])
            big_df = pd.concat(objs=[big_df, temp_df], ignore_index=True)

        big_df.rename(
            columns={
                "swindexcode": "指数代码",
                "swindexname": "指数名称",
                "bargaindate": "发布日期",
                "closeindex": "收盘指数",
                "bargainamount": "成交量",
                "markup": "涨跌幅",
                "turnoverrate": "换手率",
                "pe": "市盈率",
                "pb": "市净率",
                "meanprice": "均价",
                "bargainsumrate": "成交额占比",
                "negotiablessharesum1": "流通市值",
                "negotiablessharesum2": "平均流通市值",
                "dp": "股息率",
            },
            inplace=True,
        )
        big_df["发布日期"] = pd.to_datetime(big_df["发布日期"], errors="coerce").dt.date
        for col in ["收盘指数", "成交量", "涨跌幅", "换手率", "市盈率", "市净率",
                    "均价", "成交额占比", "流通市值", "平均流通市值", "股息率"]:
            if col in big_df.columns:
                big_df[col] = pd.to_numeric(big_df[col], errors="coerce")
        big_df.sort_values(by=["发布日期"], inplace=True, ignore_index=True)
        return big_df


# Module-level instance
shenwan_adapter = ShenwanAdapter()
