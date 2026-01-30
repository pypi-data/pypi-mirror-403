"""Tiered cache coordinator for L1 + L2 caching."""

import logging
from typing import Any

from cache.memory import MemoryCache
from cache.firestore import FirestoreCache
from cache.freshness import FreshnessChecker

logger = logging.getLogger(__name__)


class TieredCacheCoordinator:
    """
    Coordinates L1 (memory) and L2 (Firestore) caches.

    Flow on read:
    1. Check freshness (if warehouse info provided, throttled to 1x/min)
    2. Try L1 (memory) - fast, local to instance
    3. Try L2 (Firestore) - distributed, shared across instances
    4. On L2 hit, populate L1 for next request
    5. Return None if both miss (caller should query warehouse)

    Flow on write:
    1. Store in L1 (memory)
    2. Store in L2 (Firestore) - may fail for large documents
    """

    def __init__(
        self,
        memory_cache: MemoryCache,
        firestore_cache: FirestoreCache | None,
        freshness_checker: FreshnessChecker,
    ):
        """
        Initialize the tiered cache coordinator.

        Args:
            memory_cache: L1 in-memory cache instance
            firestore_cache: L2 Firestore cache instance (can be None for local dev)
            freshness_checker: Freshness checker instance
        """
        self._memory_cache = memory_cache
        self._firestore_cache = firestore_cache
        self._freshness_checker = freshness_checker

    async def get(
        self,
        org_id: str,
        cache_key: str,
        warehouse_type: str | None = None,
        client: Any = None,
        project_id: str | None = None,
        dataset_ids: list[str] | None = None,
        db_path: str | None = None,
    ) -> dict | None:
        """
        Get cached query result from tiered cache.

        Checks L1 first, then L2. Populates L1 from L2 on L2 hit.
        Optionally checks warehouse freshness before returning.

        Args:
            org_id: Organization ID
            cache_key: Cache key (org_id:hash format)
            warehouse_type: "bigquery" or "duckdb" (for freshness check)
            client: BigQuery client (for freshness check)
            project_id: GCP project ID (for freshness check)
            dataset_ids: List of dataset IDs (for freshness check) - auto-extracted from manifest
            db_path: DuckDB path (for freshness check)

        Returns:
            Dict with data, columns, comparison_data, comparison_range
            or None if not found/expired
        """
        # Check freshness if warehouse info provided
        if warehouse_type:
            invalidated = await self._check_freshness(
                org_id=org_id,
                warehouse_type=warehouse_type,
                client=client,
                project_id=project_id,
                dataset_ids=dataset_ids,
                db_path=db_path,
            )
            if invalidated:
                # Cache was invalidated, return miss
                return None

        # Try L1 (memory)
        result = self._memory_cache.get(cache_key)
        if result is not None:
            logger.debug(f"L1 cache hit for {cache_key}")
            return result

        # Try L2 (Firestore)
        if self._firestore_cache is not None:
            result = await self._firestore_cache.get(org_id, cache_key)
            if result is not None:
                logger.debug(f"L2 cache hit for {cache_key}, populating L1")
                # Populate L1 for next request
                self._memory_cache.set(cache_key, result)
                return result

        logger.debug(f"Cache miss for {cache_key}")
        return None

    async def set(
        self,
        org_id: str,
        cache_key: str,
        data: list[dict],
        columns: list[str],
        comparison_data: list[dict] | None,
        comparison_range: dict | None,
        ttl_seconds: int | None = None,
    ) -> bool:
        """
        Store query result in tiered cache.

        Stores in both L1 and L2. L2 may fail for large documents.

        Args:
            org_id: Organization ID
            cache_key: Cache key
            data: Query result rows
            columns: Column names
            comparison_data: Comparison query results
            comparison_range: Comparison date range
            ttl_seconds: TTL override (defaults to config)

        Returns:
            True if stored in L2 (or no L2), False if L2 store failed
        """
        cache_entry = {
            "data": data,
            "columns": columns,
            "comparison_data": comparison_data,
            "comparison_range": comparison_range,
        }

        # Store in L1 (memory)
        self._memory_cache.set(cache_key, cache_entry)

        # Store in L2 (Firestore)
        if self._firestore_cache is not None:
            success = await self._firestore_cache.set(
                org_id=org_id,
                cache_key=cache_key,
                data=data,
                columns=columns,
                comparison_data=comparison_data,
                comparison_range=comparison_range,
                ttl_seconds=ttl_seconds,
            )
            return success

        return True

    async def invalidate_org(self, org_id: str) -> tuple[int, int]:
        """
        Invalidate all cached entries for an organization.

        Args:
            org_id: Organization ID

        Returns:
            Tuple of (L1 count, L2 count) invalidated
        """
        l1_count = self._memory_cache.invalidate_org(org_id)

        l2_count = 0
        if self._firestore_cache is not None:
            l2_count = await self._firestore_cache.invalidate_org(org_id)

        # Also clear freshness state
        self._freshness_checker.clear_state(org_id)

        logger.info(f"Invalidated {l1_count} L1 + {l2_count} L2 entries for org {org_id}")
        return l1_count, l2_count

    async def _check_freshness(
        self,
        org_id: str,
        warehouse_type: str,
        client: Any = None,
        project_id: str | None = None,
        dataset_ids: list[str] | None = None,
        db_path: str | None = None,
    ) -> bool:
        """
        Check warehouse freshness and invalidate if changed.

        Returns:
            True if cache was invalidated, False otherwise
        """
        return await self._freshness_checker.check_and_invalidate(
            org_id=org_id,
            warehouse_type=warehouse_type,
            client=client,
            project_id=project_id,
            dataset_ids=dataset_ids,
            db_path=db_path,
            invalidate_callback=self._invalidate_callback,
        )

    async def _invalidate_callback(self, org_id: str) -> None:
        """Callback for freshness checker to invalidate cache."""
        await self.invalidate_org(org_id)

    def stats(self) -> dict:
        """
        Get cache statistics.

        Returns:
            Dict with L1 and L2 stats
        """
        return {
            "l1": self._memory_cache.stats(),
            "l2": {"available": self._firestore_cache is not None},
        }
