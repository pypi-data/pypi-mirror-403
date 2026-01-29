"""
China macroeconomic data module.

This module provides functions to fetch Chinese macroeconomic data
including GDP, CPI, PMI, and other economic indicators.

Example:
    >>> import finvista as fv
    >>> df = fv.get_cn_macro_gdp()
    >>> print(df.head())
"""

from __future__ import annotations

import logging
from typing import Any, Literal

import pandas as pd

from finvista._core.exceptions import DataNotFoundError
from finvista._fetchers.adapters.base import BaseAdapter
from finvista._fetchers.cache import cached

logger = logging.getLogger(__name__)


class ChinaMacroAdapter(BaseAdapter):
    """
    Adapter for China macroeconomic data.

    Sources:
    - National Bureau of Statistics (NBS)
    - East Money macro data API
    """

    name = "china_macro"
    base_url = "https://datacenter-web.eastmoney.com"

    def is_available(self) -> bool:
        """Check if the data source is available."""
        try:
            self._get_json(
                "https://datacenter-web.eastmoney.com/api/data/v1/get",
                params={"reportName": "RPT_ECONOMY_GDP"},
            )
            return True
        except Exception:
            return False

    def fetch_gdp(
        self,
        frequency: str = "quarterly",
        **kwargs: Any,
    ) -> pd.DataFrame:
        """
        Fetch China GDP data.

        Args:
            frequency: Data frequency ('quarterly', 'annual').

        Returns:
            DataFrame with GDP data.
        """
        params = {
            "reportName": "RPT_ECONOMY_GDP",
            "columns": "ALL",
            "pageNumber": 1,
            "pageSize": 500,
            "sortColumns": "REPORT_DATE",
            "sortTypes": -1,
        }

        data = self._get_json(
            "https://datacenter-web.eastmoney.com/api/data/v1/get",
            params=params,
        )

        if not data.get("result") or not data["result"].get("data"):
            raise DataNotFoundError("No GDP data found")

        records = []
        for item in data["result"]["data"]:
            records.append({
                "date": item.get("REPORT_DATE", "")[:10],
                "gdp": item.get("GDP"),  # GDP in billions
                "gdp_yoy": item.get("GDP_SAME"),  # YoY growth %
                "primary_industry": item.get("FIRST_INDUSTRY"),
                "secondary_industry": item.get("SECOND_INDUSTRY"),
                "tertiary_industry": item.get("THIRD_INDUSTRY"),
            })

        df = pd.DataFrame(records)
        df["date"] = pd.to_datetime(df["date"]).dt.date

        return df.sort_values("date").reset_index(drop=True)

    def fetch_cpi(
        self,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """
        Fetch China CPI (Consumer Price Index) data.

        Returns:
            DataFrame with CPI data.
        """
        params = {
            "reportName": "RPT_ECONOMY_CPI",
            "columns": "ALL",
            "pageNumber": 1,
            "pageSize": 500,
            "sortColumns": "REPORT_DATE",
            "sortTypes": -1,
        }

        data = self._get_json(
            "https://datacenter-web.eastmoney.com/api/data/v1/get",
            params=params,
        )

        if not data.get("result") or not data["result"].get("data"):
            raise DataNotFoundError("No CPI data found")

        records = []
        for item in data["result"]["data"]:
            records.append({
                "date": item.get("REPORT_DATE", "")[:10],
                "cpi": item.get("NATIONAL_SAME"),  # YoY %
                "cpi_mom": item.get("NATIONAL_BASE"),  # MoM %
                "cpi_urban": item.get("CITY_SAME"),
                "cpi_rural": item.get("RURAL_SAME"),
                "food": item.get("FOOD_SAME"),
                "non_food": item.get("NOT_FOOD_SAME"),
            })

        df = pd.DataFrame(records)
        df["date"] = pd.to_datetime(df["date"]).dt.date

        return df.sort_values("date").reset_index(drop=True)

    def fetch_ppi(
        self,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """
        Fetch China PPI (Producer Price Index) data.

        Returns:
            DataFrame with PPI data.
        """
        params = {
            "reportName": "RPT_ECONOMY_PPI",
            "columns": "ALL",
            "pageNumber": 1,
            "pageSize": 500,
            "sortColumns": "REPORT_DATE",
            "sortTypes": -1,
        }

        data = self._get_json(
            "https://datacenter-web.eastmoney.com/api/data/v1/get",
            params=params,
        )

        if not data.get("result") or not data["result"].get("data"):
            raise DataNotFoundError("No PPI data found")

        records = []
        for item in data["result"]["data"]:
            records.append({
                "date": item.get("REPORT_DATE", "")[:10],
                "ppi": item.get("BASE"),  # YoY %
                "ppi_mom": item.get("BASE_SAME"),  # MoM %
                "mining": item.get("CYJY_BASE"),
                "raw_materials": item.get("YLGY_BASE"),
                "processing": item.get("JGGY_BASE"),
            })

        df = pd.DataFrame(records)
        df["date"] = pd.to_datetime(df["date"]).dt.date

        return df.sort_values("date").reset_index(drop=True)

    def fetch_pmi(
        self,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """
        Fetch China PMI (Purchasing Managers' Index) data.

        Returns:
            DataFrame with PMI data.
        """
        params = {
            "reportName": "RPT_ECONOMY_PMI",
            "columns": "ALL",
            "pageNumber": 1,
            "pageSize": 500,
            "sortColumns": "REPORT_DATE",
            "sortTypes": -1,
        }

        data = self._get_json(
            "https://datacenter-web.eastmoney.com/api/data/v1/get",
            params=params,
        )

        if not data.get("result") or not data["result"].get("data"):
            raise DataNotFoundError("No PMI data found")

        records = []
        for item in data["result"]["data"]:
            records.append({
                "date": item.get("REPORT_DATE", "")[:10],
                "pmi_manufacturing": item.get("MAKE_INDEX"),
                "pmi_non_manufacturing": item.get("NMAKE_INDEX"),
                "pmi_composite": item.get("COMPOSITE_INDEX"),
            })

        df = pd.DataFrame(records)
        df["date"] = pd.to_datetime(df["date"]).dt.date

        return df.sort_values("date").reset_index(drop=True)

    def fetch_money_supply(
        self,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """
        Fetch China money supply (M0, M1, M2) data.

        Returns:
            DataFrame with money supply data.
        """
        params = {
            "reportName": "RPT_ECONOMY_CURRENCY",
            "columns": "ALL",
            "pageNumber": 1,
            "pageSize": 500,
            "sortColumns": "REPORT_DATE",
            "sortTypes": -1,
        }

        data = self._get_json(
            "https://datacenter-web.eastmoney.com/api/data/v1/get",
            params=params,
        )

        if not data.get("result") or not data["result"].get("data"):
            raise DataNotFoundError("No money supply data found")

        records = []
        for item in data["result"]["data"]:
            records.append({
                "date": item.get("REPORT_DATE", "")[:10],
                "m0": item.get("BASIC_CURRENCY"),  # M0 in billions
                "m0_yoy": item.get("BASIC_CURRENCY_SAME"),  # YoY %
                "m1": item.get("CURRENCY"),  # M1 in billions
                "m1_yoy": item.get("CURRENCY_SAME"),  # YoY %
                "m2": item.get("CURRENCY_QUASI"),  # M2 in billions
                "m2_yoy": item.get("CURRENCY_QUASI_SAME"),  # YoY %
            })

        df = pd.DataFrame(records)
        df["date"] = pd.to_datetime(df["date"]).dt.date

        return df.sort_values("date").reset_index(drop=True)

    def fetch_social_financing(
        self,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """
        Fetch China social financing (社会融资规模) data.

        Returns:
            DataFrame with social financing data.
        """
        params = {
            "reportName": "RPT_ECONOMY_SOCFIN",
            "columns": "ALL",
            "pageNumber": 1,
            "pageSize": 500,
            "sortColumns": "REPORT_DATE",
            "sortTypes": -1,
        }

        data = self._get_json(
            "https://datacenter-web.eastmoney.com/api/data/v1/get",
            params=params,
        )

        if not data.get("result") or not data["result"].get("data"):
            raise DataNotFoundError("No social financing data found")

        records = []
        for item in data["result"]["data"]:
            records.append({
                "date": item.get("REPORT_DATE", "")[:10],
                "total": item.get("TOTAL_FINANCE"),  # Total in billions
                "total_yoy": item.get("TOTAL_FINANCE_SAME"),  # YoY growth
                "rmb_loans": item.get("RMB_LOAN"),
                "foreign_currency_loans": item.get("FOREIGN_LOAN"),
                "trust_loans": item.get("TRUST_LOAN"),
                "corporate_bonds": item.get("ENTERPRISE_BINDTO"),
                "equity_financing": item.get("CAPITAL_MARKET"),
            })

        df = pd.DataFrame(records)
        df["date"] = pd.to_datetime(df["date"]).dt.date

        return df.sort_values("date").reset_index(drop=True)


# Global adapter instance
china_macro_adapter = ChinaMacroAdapter()


# =============================================================================
# Public API Functions
# =============================================================================


@cached(ttl=3600)
def get_cn_macro_gdp(
    frequency: Literal["quarterly", "annual"] = "quarterly",
) -> pd.DataFrame:
    """
    Get China GDP (Gross Domestic Product) data.

    Args:
        frequency: Data frequency ('quarterly' or 'annual').

    Returns:
        DataFrame with columns:
        - date: Report date
        - gdp: GDP in billions RMB
        - gdp_yoy: Year-over-year growth rate (%)
        - primary_industry: Primary industry GDP
        - secondary_industry: Secondary industry GDP
        - tertiary_industry: Tertiary industry GDP

    Example:
        >>> import finvista as fv
        >>> df = fv.get_cn_macro_gdp()
        >>> print(df.tail())
    """
    return china_macro_adapter.fetch_gdp(frequency=frequency)


@cached(ttl=3600)
def get_cn_macro_cpi() -> pd.DataFrame:
    """
    Get China CPI (Consumer Price Index) data.

    Returns:
        DataFrame with columns:
        - date: Report date
        - cpi: CPI year-over-year change (%)
        - cpi_mom: CPI month-over-month change (%)
        - cpi_urban: Urban CPI YoY (%)
        - cpi_rural: Rural CPI YoY (%)
        - food: Food CPI YoY (%)
        - non_food: Non-food CPI YoY (%)

    Example:
        >>> import finvista as fv
        >>> df = fv.get_cn_macro_cpi()
        >>> print(df.tail())
    """
    return china_macro_adapter.fetch_cpi()


@cached(ttl=3600)
def get_cn_macro_ppi() -> pd.DataFrame:
    """
    Get China PPI (Producer Price Index) data.

    Returns:
        DataFrame with columns:
        - date: Report date
        - ppi: PPI year-over-year change (%)
        - ppi_mom: PPI month-over-month change (%)
        - mining: Mining industry PPI
        - raw_materials: Raw materials PPI
        - processing: Processing industry PPI

    Example:
        >>> import finvista as fv
        >>> df = fv.get_cn_macro_ppi()
        >>> print(df.tail())
    """
    return china_macro_adapter.fetch_ppi()


@cached(ttl=3600)
def get_cn_macro_pmi() -> pd.DataFrame:
    """
    Get China PMI (Purchasing Managers' Index) data.

    Returns:
        DataFrame with columns:
        - date: Report date
        - pmi_manufacturing: Manufacturing PMI (>50 expansion, <50 contraction)
        - pmi_non_manufacturing: Non-manufacturing PMI
        - pmi_composite: Composite PMI

    Example:
        >>> import finvista as fv
        >>> df = fv.get_cn_macro_pmi()
        >>> print(df.tail())
    """
    return china_macro_adapter.fetch_pmi()


@cached(ttl=3600)
def get_cn_macro_money_supply() -> pd.DataFrame:
    """
    Get China money supply (M0, M1, M2) data.

    Returns:
        DataFrame with columns:
        - date: Report date
        - m0: M0 (currency in circulation) in billions RMB
        - m0_yoy: M0 year-over-year growth (%)
        - m1: M1 (narrow money) in billions RMB
        - m1_yoy: M1 year-over-year growth (%)
        - m2: M2 (broad money) in billions RMB
        - m2_yoy: M2 year-over-year growth (%)

    Example:
        >>> import finvista as fv
        >>> df = fv.get_cn_macro_money_supply()
        >>> print(df.tail())
    """
    return china_macro_adapter.fetch_money_supply()


@cached(ttl=3600)
def get_cn_macro_social_financing() -> pd.DataFrame:
    """
    Get China social financing (社会融资规模) data.

    Returns:
        DataFrame with columns:
        - date: Report date
        - total: Total social financing in billions RMB
        - total_yoy: Year-over-year growth
        - rmb_loans: RMB loans
        - foreign_currency_loans: Foreign currency loans
        - trust_loans: Trust loans
        - corporate_bonds: Corporate bond financing
        - equity_financing: Equity financing

    Example:
        >>> import finvista as fv
        >>> df = fv.get_cn_macro_social_financing()
        >>> print(df.tail())
    """
    return china_macro_adapter.fetch_social_financing()
