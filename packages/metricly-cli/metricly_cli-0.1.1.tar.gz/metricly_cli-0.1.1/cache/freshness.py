"""Cache freshness checker for detecting warehouse data changes."""

import logging
import os
from dataclasses import dataclass
from datetime import datetime
from threading import Lock
from typing import Any, Callable, Awaitable

from cache.config import cache_settings

logger = logging.getLogger(__name__)


@dataclass
class FreshnessState:
    """Tracks freshness state for an organization's warehouse data."""

    org_id: str
    last_check: datetime | None
    last_modified: datetime | None

    def is_stale(self, interval_seconds: int) -> bool:
        """Check if freshness state needs to be refreshed.

        Args:
            interval_seconds: How often to check freshness

        Returns:
            True if we should check warehouse freshness
        """
        if self.last_check is None:
            return True

        elapsed = datetime.now() - self.last_check
        return elapsed.total_seconds() > interval_seconds

    def has_changed(self, new_modified: datetime | None) -> bool:
        """Check if warehouse data has changed.

        Args:
            new_modified: New modification timestamp from warehouse

        Returns:
            True if data has changed since last check
        """
        if self.last_modified is None:
            return True
        if new_modified is None:
            return False
        return new_modified > self.last_modified


class FreshnessChecker:
    """
    Checks warehouse data freshness to trigger cache invalidation.

    Uses BigQuery __TABLES__ metadata (free) or DuckDB file mtime
    to detect when underlying data has changed.

    This is request-driven - checks only happen when queries come in,
    allowing Cloud Run to scale to zero when idle.
    """

    def __init__(self, check_interval_seconds: int | None = None):
        """
        Initialize the freshness checker.

        Args:
            check_interval_seconds: How often to check freshness per org.
                                   Defaults to config value.
        """
        self._interval = (
            check_interval_seconds
            if check_interval_seconds is not None
            else cache_settings.freshness_check_interval_seconds
        )
        self._states: dict[str, FreshnessState] = {}
        self._lock = Lock()

    def get_state(self, org_id: str) -> FreshnessState | None:
        """
        Get freshness state for an organization.

        Args:
            org_id: Organization ID

        Returns:
            FreshnessState or None if not tracked
        """
        with self._lock:
            return self._states.get(org_id)

    def update_state(self, org_id: str, last_modified: datetime | None) -> None:
        """
        Update freshness state for an organization.

        Args:
            org_id: Organization ID
            last_modified: Latest modification timestamp from warehouse
        """
        with self._lock:
            self._states[org_id] = FreshnessState(
                org_id=org_id,
                last_check=datetime.now(),
                last_modified=last_modified,
            )

    def needs_check(self, org_id: str) -> bool:
        """
        Check if org needs a freshness check.

        Args:
            org_id: Organization ID

        Returns:
            True if freshness should be checked
        """
        state = self.get_state(org_id)
        if state is None:
            return True
        return state.is_stale(self._interval)

    async def check_bigquery_freshness(
        self,
        client: Any,
        project_id: str,
        dataset_ids: list[str],
    ) -> datetime | None:
        """
        Check BigQuery dataset freshness via __TABLES__ metadata.

        This query is free (no data scanned) and returns the latest
        modification time across all tables in all specified datasets.

        Metrics can span multiple datasets (semantic models), so we
        check all of them and return the most recent modification time.

        Args:
            client: BigQuery client instance
            project_id: GCP project ID
            dataset_ids: List of BigQuery dataset IDs to check

        Returns:
            Latest modification datetime across all datasets, or None if empty/error
        """
        if not dataset_ids:
            return None

        try:
            # Build UNION ALL query across all datasets
            union_parts = []
            for dataset_id in dataset_ids:
                union_parts.append(
                    f"SELECT last_modified_time FROM `{project_id}.{dataset_id}.__TABLES__`"
                )

            query = f"""
                SELECT MAX(last_modified_time) as last_modified_time
                FROM ({' UNION ALL '.join(union_parts)})
            """
            job = client.query(query)
            results = list(job.result())

            if not results or results[0].last_modified_time is None:
                return None

            return results[0].last_modified_time
        except Exception as e:
            logger.warning(f"Error checking BigQuery freshness: {e}")
            return None

    def check_duckdb_freshness(self, db_path: str) -> datetime | None:
        """
        Check DuckDB file freshness via file modification time.

        Args:
            db_path: Path to DuckDB database file

        Returns:
            File modification datetime or None if file doesn't exist
        """
        try:
            if not os.path.exists(db_path):
                return None

            mtime = os.path.getmtime(db_path)
            return datetime.fromtimestamp(mtime)
        except Exception as e:
            logger.warning(f"Error checking DuckDB freshness: {e}")
            return None

    async def check_and_invalidate(
        self,
        org_id: str,
        warehouse_type: str,
        invalidate_callback: Callable[[str], Awaitable[None]],
        client: Any = None,
        project_id: str | None = None,
        dataset_ids: list[str] | None = None,
        db_path: str | None = None,
    ) -> bool:
        """
        Check freshness and invalidate cache if data changed.

        This is the main entry point called on each query request.
        It throttles checks to avoid hammering the warehouse.

        Args:
            org_id: Organization ID
            warehouse_type: "bigquery" or "duckdb"
            invalidate_callback: Async function to call when invalidation needed
            client: BigQuery client (for BigQuery)
            project_id: GCP project ID (for BigQuery)
            dataset_ids: List of dataset IDs (for BigQuery) - extracted from manifest
            db_path: Path to DuckDB file (for DuckDB)

        Returns:
            True if cache was invalidated, False otherwise
        """
        # Skip check if recently checked
        if not self.needs_check(org_id):
            return False

        # Get current freshness from warehouse
        new_modified: datetime | None = None

        if warehouse_type == "bigquery" and client and project_id and dataset_ids:
            new_modified = await self.check_bigquery_freshness(
                client, project_id, dataset_ids
            )
        elif warehouse_type == "duckdb" and db_path:
            new_modified = self.check_duckdb_freshness(db_path)

        # Check if data changed
        state = self.get_state(org_id)
        changed = state is None or state.has_changed(new_modified)

        # Update state with new check time
        self.update_state(org_id, new_modified)

        # Invalidate if changed
        if changed and state is not None:
            logger.info(f"Warehouse data changed for org {org_id}, invalidating cache")
            await invalidate_callback(org_id)
            return True

        return False

    def clear_state(self, org_id: str) -> None:
        """
        Clear freshness state for an organization.

        Args:
            org_id: Organization ID
        """
        with self._lock:
            self._states.pop(org_id, None)

    def clear_all_states(self) -> None:
        """Clear all freshness states."""
        with self._lock:
            self._states.clear()


# Singleton instance
freshness_checker = FreshnessChecker()
