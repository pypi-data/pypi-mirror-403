"""
Base adapter class for data sources.

This module provides the abstract base class that all data source
adapters should inherit from.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

import pandas as pd

from finvista._fetchers.http_client import http_client

logger = logging.getLogger(__name__)


class BaseAdapter(ABC):
    """
    Abstract base class for data source adapters.

    All data source adapters should inherit from this class and
    implement the required methods.

    Attributes:
        name: Unique identifier for this adapter.
        base_url: Base URL for API requests.

    Example:
        >>> class MyAdapter(BaseAdapter):
        ...     name = "my_source"
        ...     base_url = "https://api.example.com"
        ...
        ...     def fetch_stock_daily(self, symbol: str, **kwargs) -> pd.DataFrame:
        ...         # Implementation
        ...         pass
    """

    name: str = ""
    base_url: str = ""

    def __init__(self) -> None:
        """Initialize the adapter."""
        self._http = http_client

    @property
    def http(self) -> Any:
        """Get the HTTP client."""
        return self._http

    def _build_url(self, endpoint: str) -> str:
        """
        Build full URL from endpoint.

        Args:
            endpoint: API endpoint path.

        Returns:
            Full URL.
        """
        if endpoint.startswith("http"):
            return endpoint
        base = self.base_url.rstrip("/")
        endpoint = endpoint.lstrip("/")
        return f"{base}/{endpoint}"

    def _get(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> Any:
        """
        Make a GET request.

        Args:
            endpoint: API endpoint.
            params: Query parameters.
            headers: Additional headers.
            **kwargs: Additional request options.

        Returns:
            Response data.
        """
        url = self._build_url(endpoint)
        return self._http.get(url, params=params, headers=headers, **kwargs)

    def _get_json(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Make a GET request and parse JSON response.

        Args:
            endpoint: API endpoint.
            params: Query parameters.
            headers: Additional headers.
            **kwargs: Additional request options.

        Returns:
            Parsed JSON data.
        """
        url = self._build_url(endpoint)
        return self._http.get_json(url, params=params, headers=headers, **kwargs)

    def _get_text(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        encoding: str | None = None,
        **kwargs: Any,
    ) -> str:
        """
        Make a GET request and return text response.

        Args:
            endpoint: API endpoint.
            params: Query parameters.
            headers: Additional headers.
            encoding: Response encoding.
            **kwargs: Additional request options.

        Returns:
            Response text.
        """
        url = self._build_url(endpoint)
        return self._http.get_text(url, params=params, headers=headers, encoding=encoding, **kwargs)

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if this adapter is currently available.

        Returns:
            True if available, False otherwise.
        """
        pass

    def _to_dataframe(self, data: list[dict[str, Any]], columns: list[str] | None = None) -> pd.DataFrame:
        """
        Convert data to DataFrame with optional column selection.

        Args:
            data: List of dictionaries.
            columns: Optional list of columns to include.

        Returns:
            DataFrame.
        """
        df = pd.DataFrame(data)
        if columns and len(df) > 0:
            # Only include columns that exist
            existing_cols = [c for c in columns if c in df.columns]
            df = df[existing_cols]
        return df
