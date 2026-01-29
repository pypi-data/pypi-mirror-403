"""L2: Firestore distributed cache with TTL."""

import json
from dataclasses import dataclass
from datetime import datetime, timedelta

from cache.config import cache_settings


@dataclass
class QueryCacheEntry:
    """Cached query result entry."""

    data: list[dict]
    columns: list[str]
    comparison_data: list[dict] | None
    comparison_range: dict | None
    created_at: datetime
    expires_at: datetime

    @classmethod
    def from_query_response(
        cls,
        data: list[dict],
        columns: list[str],
        comparison_data: list[dict] | None,
        comparison_range: dict | None,
        ttl_seconds: int,
    ) -> "QueryCacheEntry":
        """Create entry from query response data."""
        now = datetime.now()
        return cls(
            data=data,
            columns=columns,
            comparison_data=comparison_data,
            comparison_range=comparison_range,
            created_at=now,
            expires_at=now + timedelta(seconds=ttl_seconds),
        )

    def is_expired(self) -> bool:
        """Check if entry has expired."""
        return datetime.now() > self.expires_at

    def to_dict(self) -> dict:
        """Convert to dict for Firestore storage."""
        return {
            "data": self.data,
            "columns": self.columns,
            "comparison_data": self.comparison_data,
            "comparison_range": self.comparison_range,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "QueryCacheEntry":
        """Create from Firestore document dict."""
        return cls(
            data=d["data"],
            columns=d["columns"],
            comparison_data=d.get("comparison_data"),
            comparison_range=d.get("comparison_range"),
            created_at=d["created_at"],
            expires_at=d["expires_at"],
        )


class FirestoreCache:
    """
    L2: Distributed Firestore cache with TTL.

    Stores query results in a subcollection under each org document.
    Uses Firestore TTL policy for automatic cleanup of expired entries.

    Schema:
        /orgs/{org_id}/query_cache/{hash}
            - data: list[dict]
            - columns: list[str]
            - comparison_data: list[dict] | None
            - comparison_range: dict | None
            - created_at: Timestamp
            - expires_at: Timestamp (TTL field)
    """

    def __init__(self, db):
        """
        Initialize Firestore cache.

        Args:
            db: Firestore async client instance
        """
        self._db = db

    async def get(self, org_id: str, cache_key: str) -> dict | None:
        """
        Get cached query result.

        Args:
            org_id: Organization ID
            cache_key: Cache key (org_id:hash format)

        Returns:
            Dict with data, columns, comparison_data, comparison_range
            or None if not found/expired
        """
        doc_ref = self._doc_ref(org_id, cache_key)
        doc = await doc_ref.get()

        if not doc.exists:
            return None

        data = doc.to_dict()

        # Check expiration (belt + suspenders with TTL policy)
        entry = QueryCacheEntry.from_dict(data)
        if entry.is_expired():
            return None

        return {
            "data": entry.data,
            "columns": entry.columns,
            "comparison_data": entry.comparison_data,
            "comparison_range": entry.comparison_range,
        }

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
        Store query result in cache.

        Args:
            org_id: Organization ID
            cache_key: Cache key
            data: Query result rows
            columns: Column names
            comparison_data: Comparison query results
            comparison_range: Comparison date range
            ttl_seconds: TTL override (defaults to config)

        Returns:
            True if stored, False if too large
        """
        ttl = ttl_seconds or cache_settings.firestore_ttl_seconds

        entry = QueryCacheEntry.from_query_response(
            data=data,
            columns=columns,
            comparison_data=comparison_data,
            comparison_range=comparison_range,
            ttl_seconds=ttl,
        )

        doc_data = entry.to_dict()

        # Check size (Firestore 1MB limit, leave headroom)
        size_kb = len(json.dumps(doc_data, default=str).encode()) / 1024
        if size_kb > cache_settings.firestore_max_doc_size_kb:
            return False

        doc_ref = self._doc_ref(org_id, cache_key)
        await doc_ref.set(doc_data)
        return True

    async def delete(self, org_id: str, cache_key: str) -> None:
        """
        Delete a cached entry.

        Args:
            org_id: Organization ID
            cache_key: Cache key
        """
        doc_ref = self._doc_ref(org_id, cache_key)
        await doc_ref.delete()

    async def invalidate_org(self, org_id: str) -> int:
        """
        Delete all cached entries for an organization.

        Args:
            org_id: Organization ID

        Returns:
            Number of entries deleted
        """
        collection_ref = (
            self._db.collection("orgs")
            .document(org_id)
            .collection("query_cache")
        )

        count = 0
        async for doc in collection_ref.stream():
            await doc.reference.delete()
            count += 1

        return count

    def _doc_ref(self, org_id: str, cache_key: str):
        """Get document reference for a cache key."""
        # Extract hash part from key (org_id:hash)
        doc_id = cache_key.split(":")[-1]
        return (
            self._db.collection("orgs")
            .document(org_id)
            .collection("query_cache")
            .document(doc_id)
        )
