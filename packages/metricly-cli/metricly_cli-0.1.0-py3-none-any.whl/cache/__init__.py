"""Query caching layer for Metricly."""

from cache.config import cache_settings, compute_query_ttl
from cache.keys import query_cache_key, normalize_filters
from cache.memory import MemoryCache, memory_cache
from cache.firestore import FirestoreCache, QueryCacheEntry
from cache.freshness import FreshnessChecker, FreshnessState, freshness_checker
from cache.coordinator import TieredCacheCoordinator
from cache.integration import (
    get_cache_coordinator,
    build_cdn_headers,
    build_no_cache_headers,
    get_cached_response,
    cache_response,
)

__all__ = [
    # Config
    "cache_settings",
    "compute_query_ttl",
    # Keys
    "query_cache_key",
    "normalize_filters",
    # L1 Memory cache
    "MemoryCache",
    "memory_cache",
    # L2 Firestore cache
    "FirestoreCache",
    "QueryCacheEntry",
    # Freshness checker
    "FreshnessChecker",
    "FreshnessState",
    "freshness_checker",
    # Coordinator
    "TieredCacheCoordinator",
    # Integration helpers
    "get_cache_coordinator",
    "build_cdn_headers",
    "build_no_cache_headers",
    "get_cached_response",
    "cache_response",
]
