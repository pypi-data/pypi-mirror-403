"""L1: In-memory LRU cache with TTL."""

from threading import Lock
from typing import Any

from cachetools import TTLCache

from cache.config import cache_settings


class MemoryCache:
    """
    Per-instance in-memory LRU cache with TTL.

    This cache is local to each Cloud Run instance. Items are evicted
    either when TTL expires or when the cache reaches its size limit
    (LRU eviction).

    Thread-safe for concurrent access.
    """

    def __init__(
        self,
        max_size_mb: int | None = None,
        ttl_seconds: int | None = None,
    ):
        """
        Initialize the memory cache.

        Args:
            max_size_mb: Maximum cache size in MB. Defaults to config value.
            ttl_seconds: TTL for cached items in seconds. Defaults to config value.
        """
        max_size = max_size_mb if max_size_mb is not None else cache_settings.memory_max_size_mb
        ttl = ttl_seconds if ttl_seconds is not None else cache_settings.memory_ttl_seconds

        # Estimate ~10KB per cached query result
        max_items = max(1, (max_size * 1024) // 10)

        self._cache: TTLCache = TTLCache(maxsize=max_items, ttl=ttl)
        self._lock = Lock()

    def get(self, key: str) -> Any | None:
        """
        Get a value from the cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        with self._lock:
            return self._cache.get(key)

    def set(self, key: str, value: Any) -> None:
        """
        Store a value in the cache.

        Args:
            key: Cache key
            value: Value to cache
        """
        with self._lock:
            self._cache[key] = value

    def delete(self, key: str) -> None:
        """
        Delete a key from the cache.

        Args:
            key: Cache key to delete
        """
        with self._lock:
            self._cache.pop(key, None)

    def invalidate_org(self, org_id: str) -> int:
        """
        Remove all cached entries for an organization.

        Args:
            org_id: Organization ID prefix

        Returns:
            Number of entries removed
        """
        prefix = f"{org_id}:"
        count = 0

        with self._lock:
            keys_to_delete = [k for k in self._cache if k.startswith(prefix)]
            for key in keys_to_delete:
                del self._cache[key]
                count += 1

        return count

    def clear(self) -> None:
        """Clear all cached entries."""
        with self._lock:
            self._cache.clear()

    def stats(self) -> dict:
        """
        Get cache statistics.

        Returns:
            Dict with size, maxsize, and currsize info
        """
        with self._lock:
            return {
                "size": len(self._cache),
                "maxsize": self._cache.maxsize,
                "currsize": self._cache.currsize,
            }


# Singleton instance for use across the application
memory_cache = MemoryCache()
