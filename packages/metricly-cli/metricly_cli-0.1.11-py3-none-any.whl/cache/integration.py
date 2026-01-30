"""Cache integration helpers for the API layer.

Provides a simple interface for caching query results with
CDN headers and freshness checking.
"""

import logging
from typing import Any

from cache.config import cache_settings, compute_query_ttl
from cache.keys import query_cache_key
from cache.memory import memory_cache
from cache.firestore import FirestoreCache
from cache.freshness import freshness_checker
from cache.coordinator import TieredCacheCoordinator

logger = logging.getLogger(__name__)

# Global coordinator instance
_coordinator: TieredCacheCoordinator | None = None


def get_cache_coordinator(firestore_db: Any = None) -> TieredCacheCoordinator:
    """
    Get or create the cache coordinator singleton.

    Args:
        firestore_db: Optional Firestore async client for L2 cache.
                     If None, only L1 (memory) cache is used.

    Returns:
        TieredCacheCoordinator instance
    """
    global _coordinator
    if _coordinator is None:
        firestore_cache = FirestoreCache(db=firestore_db) if firestore_db else None
        _coordinator = TieredCacheCoordinator(
            memory_cache=memory_cache,
            firestore_cache=firestore_cache,
            freshness_checker=freshness_checker,
        )
    return _coordinator


def build_cdn_headers(
    has_comparison: bool = False,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict[str, str]:
    """
    Build Cache-Control headers for CDN caching.

    Uses stale-while-revalidate pattern to serve stale content
    while fetching fresh data in the background.

    Args:
        has_comparison: Whether response includes comparison data
        start_date: Query start date (affects TTL)
        end_date: Query end date (affects TTL)

    Returns:
        Dict of HTTP headers
    """
    # Compute TTL based on data recency
    ttl = compute_query_ttl(end_date)

    # Comparison queries have more complex data, shorter TTL
    if has_comparison:
        ttl = min(ttl, cache_settings.cdn_max_age_seconds * 2)

    max_age = cache_settings.cdn_max_age_seconds
    stale_while_revalidate = cache_settings.cdn_stale_while_revalidate_seconds

    return {
        "Cache-Control": f"public, max-age={max_age}, stale-while-revalidate={stale_while_revalidate}",
        "Vary": "Authorization",
    }


def build_no_cache_headers() -> dict[str, str]:
    """
    Build headers that prevent caching.

    Use for error responses or when cache is disabled.

    Returns:
        Dict of HTTP headers
    """
    return {
        "Cache-Control": "no-store, no-cache, must-revalidate",
        "Pragma": "no-cache",
    }


async def get_cached_response(
    coordinator: TieredCacheCoordinator,
    org_id: str,
    metrics: list[str],
    dimensions: list[str] | None,
    grain: str | None,
    start_date: str | None,
    end_date: str | None,
    filters: list[dict] | None = None,
    comparison: str | None = None,
    order_by: str | None = None,
    limit: int | None = None,
    warehouse_type: str | None = None,
    client: Any = None,
    project_id: str | None = None,
    dataset_ids: list[str] | None = None,
    db_path: str | None = None,
) -> dict | None:
    """
    Check cache for query result.

    Generates cache key and checks tiered cache with optional
    freshness verification.

    Args:
        coordinator: Cache coordinator instance
        org_id: Organization ID
        metrics: List of metric names
        dimensions: List of dimension names
        grain: Time grain (day, week, month, etc.)
        start_date: Query start date
        end_date: Query end date
        filters: Query filters
        comparison: Comparison type (none, previous_period, same_period_last_year)
        order_by: Order by clause
        limit: Result limit
        warehouse_type: "bigquery" or "duckdb"
        client: Warehouse client (for freshness check)
        project_id: GCP project ID (for BigQuery freshness check)
        dataset_ids: List of dataset IDs - auto-extracted from manifest (for BigQuery)
        db_path: DuckDB path (for DuckDB freshness check)

    Returns:
        Cached response dict or None if cache miss
    """
    cache_key = query_cache_key(
        org_id=org_id,
        metrics=metrics,
        dimensions=dimensions,
        grain=grain,
        start_date=start_date,
        end_date=end_date,
        filters=filters,
        comparison=comparison,
        order_by=order_by,
        limit=limit,
    )

    return await coordinator.get(
        org_id=org_id,
        cache_key=cache_key,
        warehouse_type=warehouse_type,
        client=client,
        project_id=project_id,
        dataset_ids=dataset_ids,
        db_path=db_path,
    )


async def cache_response(
    coordinator: TieredCacheCoordinator,
    org_id: str,
    metrics: list[str],
    dimensions: list[str] | None,
    grain: str | None,
    start_date: str | None,
    end_date: str | None,
    data: list[dict],
    columns: list[str],
    comparison_data: list[dict] | None = None,
    comparison_range: dict | None = None,
    filters: list[dict] | None = None,
    comparison: str | None = None,
    order_by: str | None = None,
    limit: int | None = None,
) -> bool:
    """
    Store query result in cache.

    Generates cache key and stores in tiered cache.

    Args:
        coordinator: Cache coordinator instance
        org_id: Organization ID
        metrics: List of metric names
        dimensions: List of dimension names
        grain: Time grain
        start_date: Query start date
        end_date: Query end date
        data: Query result rows
        columns: Column names
        comparison_data: Comparison query results
        comparison_range: Comparison date range
        filters: Query filters
        comparison: Comparison type
        order_by: Order by clause
        limit: Result limit

    Returns:
        True if cached successfully
    """
    cache_key = query_cache_key(
        org_id=org_id,
        metrics=metrics,
        dimensions=dimensions,
        grain=grain,
        start_date=start_date,
        end_date=end_date,
        filters=filters,
        comparison=comparison,
        order_by=order_by,
        limit=limit,
    )

    ttl = compute_query_ttl(end_date)

    return await coordinator.set(
        org_id=org_id,
        cache_key=cache_key,
        data=data,
        columns=columns,
        comparison_data=comparison_data,
        comparison_range=comparison_range,
        ttl_seconds=ttl,
    )
