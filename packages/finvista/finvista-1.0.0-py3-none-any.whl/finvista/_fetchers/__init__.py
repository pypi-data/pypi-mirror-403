"""
Data fetching layer for FinVista.

This module provides the infrastructure for fetching data from various
sources, including HTTP clients, caching, rate limiting, and automatic
failover between data sources.
"""

from finvista._fetchers.cache import MemoryCache, cache_manager, cached
from finvista._fetchers.http_client import HttpClient, http_client
from finvista._fetchers.rate_limiter import RateLimiter, rate_limiter
from finvista._fetchers.source_manager import SourceManager, source_manager

__all__ = [
    # HTTP Client
    "HttpClient",
    "http_client",
    # Cache
    "MemoryCache",
    "cached",
    "cache_manager",
    # Rate Limiter
    "RateLimiter",
    "rate_limiter",
    # Source Manager
    "SourceManager",
    "source_manager",
]
