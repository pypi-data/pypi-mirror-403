"""Cache configuration settings."""

from pydantic_settings import BaseSettings


class CacheSettings(BaseSettings):
    """Configuration for the caching layer.

    Invalidation strategy: Freshness check is the primary invalidation mechanism.
    TTLs are long (safety net) since freshness check detects warehouse changes.
    """

    # L1: In-memory cache (per-instance, bounded by memory)
    memory_max_size_mb: int = 100
    memory_ttl_seconds: int = 3600  # 1 hour

    # L2: Firestore cache (distributed, freshness check invalidates)
    firestore_ttl_seconds: int = 86400  # 24 hours (safety net TTL)
    firestore_max_doc_size_kb: int = 900  # Leave headroom under 1MB limit

    # Freshness checking (primary invalidation mechanism)
    freshness_check_interval_seconds: int = 60  # Check warehouse every 1 min

    # CDN headers
    cdn_max_age_seconds: int = 60
    cdn_stale_while_revalidate_seconds: int = 300

    model_config = {"env_prefix": "CACHE_"}


# Singleton instance
cache_settings = CacheSettings()


def compute_query_ttl(end_date: str | None) -> int:
    """
    Compute TTL for cached query results.

    Since freshness check is the primary invalidation mechanism,
    we use a long TTL as a safety net. The freshness check will
    invalidate the cache when warehouse data changes.

    Args:
        end_date: End date of the query in ISO format (YYYY-MM-DD)
                  (kept for API compatibility, not used for TTL calculation)

    Returns:
        TTL in seconds (default Firestore TTL)
    """
    return cache_settings.firestore_ttl_seconds
