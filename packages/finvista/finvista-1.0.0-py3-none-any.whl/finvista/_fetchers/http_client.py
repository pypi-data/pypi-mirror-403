"""
HTTP client for FinVista.

This module provides a robust HTTP client with automatic retries,
proxy support, and proper error handling.

Example:
    >>> from finvista._fetchers.http_client import http_client
    >>> response = http_client.get("https://api.example.com/data")
    >>> data = http_client.get_json("https://api.example.com/data.json")
"""

from __future__ import annotations

import logging
import time
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from finvista._core.config import config
from finvista._core.exceptions import (
    APIError,
    DataParsingError,
    NetworkError,
    RateLimitError,
)

logger = logging.getLogger(__name__)


class HttpClient:
    """
    HTTP client with retry logic, proxy support, and error handling.

    This client wraps the requests library and adds:
    - Automatic retry with exponential backoff
    - Proxy configuration from global config
    - Proper error classification and handling
    - Session reuse for connection pooling

    Attributes:
        session: The underlying requests Session object.

    Example:
        >>> client = HttpClient()
        >>> response = client.get("https://api.example.com/data")
        >>> data = client.get_json("https://api.example.com/data.json")
    """

    def __init__(self) -> None:
        """Initialize the HTTP client."""
        self._session: requests.Session | None = None

    @property
    def session(self) -> requests.Session:
        """
        Get or create the requests session.

        The session is lazily initialized and configured with retry
        logic based on the current configuration.
        """
        if self._session is None:
            self._session = self._create_session()
        return self._session

    def _create_session(self) -> requests.Session:
        """
        Create and configure a new requests session.

        Returns:
            Configured Session object with retry adapter.
        """
        http_config = config.http

        session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=http_config.max_retries,
            backoff_factor=http_config.retry_backoff,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["GET", "POST", "HEAD", "OPTIONS"],
            raise_on_status=False,
        )

        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=20,
        )
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # Set default headers
        session.headers.update(
            {
                "User-Agent": http_config.user_agent,
                "Accept": "application/json, text/html, text/plain, */*",
                "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
            }
        )

        return session

    def reset_session(self) -> None:
        """
        Reset the session to apply new configuration.

        Call this after changing HTTP configuration to ensure
        the new settings take effect.
        """
        if self._session is not None:
            self._session.close()
            self._session = None

    def get(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: int | None = None,
        **kwargs: Any,
    ) -> requests.Response:
        """
        Send a GET request.

        Args:
            url: The URL to request.
            params: Optional query parameters.
            headers: Optional additional headers.
            timeout: Optional timeout override.
            **kwargs: Additional arguments passed to requests.

        Returns:
            The Response object.

        Raises:
            NetworkError: On connection or timeout errors.
            RateLimitError: When rate limited (HTTP 429).
            APIError: On HTTP errors.
        """
        return self._request("GET", url, params=params, headers=headers, timeout=timeout, **kwargs)

    def post(
        self,
        url: str,
        data: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: int | None = None,
        **kwargs: Any,
    ) -> requests.Response:
        """
        Send a POST request.

        Args:
            url: The URL to request.
            data: Optional form data.
            json: Optional JSON body.
            headers: Optional additional headers.
            timeout: Optional timeout override.
            **kwargs: Additional arguments passed to requests.

        Returns:
            The Response object.

        Raises:
            NetworkError: On connection or timeout errors.
            RateLimitError: When rate limited (HTTP 429).
            APIError: On HTTP errors.
        """
        return self._request(
            "POST", url, data=data, json=json, headers=headers, timeout=timeout, **kwargs
        )

    def _request(
        self,
        method: str,
        url: str,
        timeout: int | None = None,
        **kwargs: Any,
    ) -> requests.Response:
        """
        Send an HTTP request with error handling.

        Args:
            method: HTTP method (GET, POST, etc.).
            url: The URL to request.
            timeout: Optional timeout override.
            **kwargs: Additional arguments passed to requests.

        Returns:
            The Response object.

        Raises:
            NetworkError: On connection or timeout errors.
            RateLimitError: When rate limited (HTTP 429).
            APIError: On HTTP errors.
        """
        http_config = config.http

        # Apply configuration
        kwargs.setdefault("timeout", timeout or http_config.timeout)
        kwargs.setdefault("verify", http_config.verify_ssl)

        if http_config.proxies:
            kwargs.setdefault("proxies", http_config.proxies)

        # Merge headers
        if "headers" in kwargs and kwargs["headers"]:
            merged_headers = dict(self.session.headers)
            merged_headers.update(kwargs["headers"])
            kwargs["headers"] = merged_headers

        start_time = time.time()
        try:
            response = self.session.request(method, url, **kwargs)
            elapsed = time.time() - start_time

            logger.debug(
                f"{method} {url} completed in {elapsed:.2f}s with status {response.status_code}"
            )

            # Handle rate limiting
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                retry_seconds = int(retry_after) if retry_after else None
                raise RateLimitError(
                    f"Rate limit exceeded for {url}",
                    retry_after=retry_seconds,
                )

            # Handle other errors
            if response.status_code >= 400:
                raise APIError(
                    f"HTTP {response.status_code} error from {url}",
                    status_code=response.status_code,
                    response_body=response.text[:500] if response.text else None,
                )

            return response

        except requests.exceptions.Timeout as e:
            logger.warning(f"Request timeout for {url}: {e}")
            raise NetworkError(
                f"Request timeout after {kwargs.get('timeout')}s",
                url=url,
                original_error=e,
            ) from e

        except requests.exceptions.ConnectionError as e:
            logger.warning(f"Connection error for {url}: {e}")
            raise NetworkError(
                f"Connection error: {e}",
                url=url,
                original_error=e,
            ) from e

        except requests.exceptions.RequestException as e:
            logger.warning(f"Request error for {url}: {e}")
            raise NetworkError(
                f"Request failed: {e}",
                url=url,
                original_error=e,
            ) from e

    def get_json(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Send a GET request and parse JSON response.

        Args:
            url: The URL to request.
            params: Optional query parameters.
            headers: Optional additional headers.
            **kwargs: Additional arguments passed to requests.

        Returns:
            Parsed JSON as a dictionary.

        Raises:
            DataParsingError: When JSON parsing fails.
        """
        response = self.get(url, params=params, headers=headers, **kwargs)
        try:
            return response.json()  # type: ignore[no-any-return]
        except ValueError as e:
            raise DataParsingError(
                f"Failed to parse JSON from {url}",
                raw_data=response.text[:200] if response.text else None,
            ) from e

    def get_text(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        encoding: str | None = None,
        **kwargs: Any,
    ) -> str:
        """
        Send a GET request and return text response.

        Args:
            url: The URL to request.
            params: Optional query parameters.
            headers: Optional additional headers.
            encoding: Optional encoding override.
            **kwargs: Additional arguments passed to requests.

        Returns:
            Response text content.
        """
        response = self.get(url, params=params, headers=headers, **kwargs)
        if encoding:
            response.encoding = encoding
        return str(response.text)

    def get_content(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> bytes:
        """
        Send a GET request and return raw bytes.

        Args:
            url: The URL to request.
            params: Optional query parameters.
            headers: Optional additional headers.
            **kwargs: Additional arguments passed to requests.

        Returns:
            Response content as bytes.
        """
        response = self.get(url, params=params, headers=headers, **kwargs)
        return bytes(response.content)

    def close(self) -> None:
        """Close the HTTP session."""
        if self._session is not None:
            self._session.close()
            self._session = None

    def __enter__(self) -> HttpClient:
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.close()


# Global HTTP client instance
http_client = HttpClient()
