"""Per-org warehouse connections (MetricFlow engines and query clients).

Provides cached, per-org MetricFlow engines and BigQuery/DuckDB clients.
Engines are created lazily on first access and cached with TTL.
"""

import json
import os
import tempfile
import time
from dataclasses import dataclass
from threading import Lock
from typing import Optional, Protocol

import duckdb
from google.cloud import bigquery, secretmanager, storage as gcs_storage
from google.oauth2 import service_account
from dbt_semantic_interfaces.implementations.semantic_manifest import PydanticSemanticManifest
from metricflow.engine.metricflow_engine import MetricFlowEngine

import storage
from cache.manifest import extract_datasets_from_manifest
from mf_engine import load_manifest_from_dict, create_engine


# Cache TTL in seconds (1 hour)
CACHE_TTL = 3600

# Secret Manager client (lazy init)
_secret_client: Optional[secretmanager.SecretManagerServiceClient] = None
_secret_lock = Lock()


def _get_secret_client() -> secretmanager.SecretManagerServiceClient:
    """Get or create Secret Manager client."""
    global _secret_client
    if _secret_client is None:
        with _secret_lock:
            if _secret_client is None:
                _secret_client = secretmanager.SecretManagerServiceClient()
    return _secret_client


def _get_secret(secret_path: str) -> str:
    """Fetch secret value from Secret Manager.

    Args:
        secret_path: Full resource name like
            "projects/metricly-dev/secrets/org-xxx-bq-key/versions/latest"

    Returns:
        Secret value as string
    """
    client = _get_secret_client()
    response = client.access_secret_version(request={"name": secret_path})
    return response.payload.data.decode("UTF-8")


class QueryClient(Protocol):
    """Protocol for query execution clients."""

    def query(self, sql: str) -> list[dict]:
        """Execute SQL and return results as list of dicts."""
        ...

    def close(self) -> None:
        """Close the client connection."""
        ...


@dataclass
class BigQueryClient:
    """BigQuery client wrapper."""

    client: bigquery.Client
    project_id: str

    def query(self, sql: str) -> list[dict]:
        """Execute SQL and return results as list of dicts."""
        rows = self.client.query(sql).result()
        return [dict(row) for row in rows]

    def close(self) -> None:
        self.client.close()


@dataclass
class DuckDBClient:
    """DuckDB client wrapper for file-based databases."""

    conn: duckdb.DuckDBPyConnection
    path: str
    _temp_file: Optional[str] = None  # For GCS downloads

    def query(self, sql: str) -> list[dict]:
        """Execute SQL and return results as list of dicts."""
        result = self.conn.execute(sql)
        columns = [desc[0] for desc in result.description]
        return [dict(zip(columns, row)) for row in result.fetchall()]

    def close(self) -> None:
        """Close connection and clean up temp files."""
        self.conn.close()
        if self._temp_file and os.path.exists(self._temp_file):
            try:
                os.remove(self._temp_file)
            except OSError:
                pass


@dataclass
class CachedEngine:
    """Cached MetricFlow engine with metadata."""
    engine: MetricFlowEngine
    manifest: PydanticSemanticManifest
    created_at: float

    def is_expired(self) -> bool:
        return time.time() - self.created_at > CACHE_TTL


@dataclass
class CachedClient:
    """Cached query client with metadata."""
    client: QueryClient
    created_at: float
    warehouse_type: str

    def is_expired(self) -> bool:
        return time.time() - self.created_at > CACHE_TTL


class OrgWarehouse:
    """Per-org warehouse connection manager.

    Provides cached MetricFlow engines and query clients for each org.
    Thread-safe with per-org locking.
    """

    def __init__(self):
        self._engines: dict[str, CachedEngine] = {}
        self._clients: dict[str, CachedClient] = {}
        self._engine_locks: dict[str, Lock] = {}
        self._client_locks: dict[str, Lock] = {}
        self._global_lock = Lock()

    def _get_engine_lock(self, org_id: str) -> Lock:
        """Get or create lock for org's engine."""
        with self._global_lock:
            if org_id not in self._engine_locks:
                self._engine_locks[org_id] = Lock()
            return self._engine_locks[org_id]

    def _get_client_lock(self, org_id: str) -> Lock:
        """Get or create lock for org's client."""
        with self._global_lock:
            if org_id not in self._client_locks:
                self._client_locks[org_id] = Lock()
            return self._client_locks[org_id]

    def get_engine(self, org_id: str) -> tuple[MetricFlowEngine, PydanticSemanticManifest]:
        """Get MetricFlow engine for org, creating if needed.

        Returns:
            Tuple of (engine, manifest)

        Raises:
            ValueError: If no manifest configured for org
        """
        # Check cache first (no lock needed for read)
        cached = self._engines.get(org_id)
        if cached and not cached.is_expired():
            return cached.engine, cached.manifest

        # Need to create/refresh - acquire lock
        lock = self._get_engine_lock(org_id)
        with lock:
            # Double-check after acquiring lock
            cached = self._engines.get(org_id)
            if cached and not cached.is_expired():
                return cached.engine, cached.manifest

            # Load manifest from Firestore
            manifest_dict = storage.get_manifest(org_id)
            if not manifest_dict:
                raise ValueError(f"No manifest configured for org: {org_id}")

            # Get warehouse type to configure correct SQL renderer
            warehouse_config = storage.get_warehouse_config(org_id)
            warehouse_type = warehouse_config.get("type", "bigquery") if warehouse_config else "bigquery"

            # Create engine with appropriate SQL dialect
            manifest = load_manifest_from_dict(manifest_dict)
            engine = create_engine(manifest, warehouse_type=warehouse_type)

            # Cache it
            self._engines[org_id] = CachedEngine(
                engine=engine,
                manifest=manifest,
                created_at=time.time(),
            )

            return engine, manifest

    def get_client(self, org_id: str) -> QueryClient:
        """Get query client for org, creating if needed.

        Returns:
            Query client (BigQuery or DuckDB)

        Raises:
            ValueError: If no warehouse configured for org
        """
        # Check cache first
        cached = self._clients.get(org_id)
        if cached and not cached.is_expired():
            return cached.client

        # Need to create/refresh - acquire lock
        lock = self._get_client_lock(org_id)
        with lock:
            # Double-check after acquiring lock
            cached = self._clients.get(org_id)
            if cached and not cached.is_expired():
                return cached.client

            # Close old client if exists
            if cached:
                try:
                    cached.client.close()
                except Exception:
                    pass

            # Load warehouse config from Firestore
            config = storage.get_warehouse_config(org_id)
            if not config:
                raise ValueError(f"No warehouse configured for org: {org_id}")

            warehouse_type = config.get("type")

            if warehouse_type == "bigquery":
                client = self._create_bigquery_client(config)
            elif warehouse_type == "duckdb":
                client = self._create_duckdb_client(config)
            else:
                raise ValueError(f"Unknown warehouse type: {warehouse_type}")

            # Cache it
            self._clients[org_id] = CachedClient(
                client=client,
                created_at=time.time(),
                warehouse_type=warehouse_type,
            )

            return client

    def _create_bigquery_client(self, config: dict) -> BigQueryClient:
        """Create BigQuery client from warehouse config."""
        bq_config = config.get("bigquery", {})
        project_id = bq_config.get("project_id")

        if not project_id:
            raise ValueError("BigQuery config missing project_id")

        # Check for service account credentials
        secret_path = bq_config.get("service_account_secret")
        if secret_path:
            # Load credentials from Secret Manager
            secret_value = _get_secret(secret_path)
            credentials_info = json.loads(secret_value)
            credentials = service_account.Credentials.from_service_account_info(
                credentials_info
            )
            client = bigquery.Client(project=project_id, credentials=credentials)
        else:
            # Use default credentials (ADC)
            client = bigquery.Client(project=project_id)

        return BigQueryClient(client=client, project_id=project_id)

    def _create_duckdb_client(self, config: dict) -> DuckDBClient:
        """Create DuckDB client from warehouse config.

        Supports:
        - Local file paths
        - GCS paths (gs://bucket/path/file.duckdb)
        - MotherDuck (md:database)
        """
        duckdb_config = config.get("duckdb", {})
        path = duckdb_config.get("path")
        token = duckdb_config.get("token")

        if not path:
            raise ValueError("DuckDB config missing path")

        temp_file = None
        actual_path = path

        if path.startswith("md:"):
            # MotherDuck connection
            if token:
                # Build connection string with token
                if "?" in path:
                    actual_path = f"{path}&motherduck_token={token}"
                else:
                    actual_path = f"{path}?motherduck_token={token}"
            # Connect directly to MotherDuck (no ATTACH needed)
            conn = duckdb.connect(actual_path)
            return DuckDBClient(conn=conn, path=path, _temp_file=None)

        elif path.startswith("gs://"):
            # Download from GCS to temp file
            temp_file = self._download_gcs_file(path)
            actual_path = temp_file
        else:
            # Local file path - try as-is first, then relative to project root
            if not os.path.exists(path):
                # Try relative to project root (parent of backend directory)
                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                alt_path = os.path.join(project_root, path)
                if os.path.exists(alt_path):
                    actual_path = alt_path
                else:
                    raise ValueError(f"DuckDB file not found: {path}")

        # Connect to in-memory and attach the file as "data" catalog
        # This matches the dbt manifest which references tables as data.schema.table
        conn = duckdb.connect(":memory:")
        conn.execute(f"ATTACH '{actual_path}' AS data (READ_ONLY)")

        return DuckDBClient(conn=conn, path=path, _temp_file=temp_file)

    def _download_gcs_file(self, gcs_path: str) -> str:
        """Download a file from GCS to a temp location.

        Args:
            gcs_path: GCS URI like gs://bucket/path/file.duckdb

        Returns:
            Path to downloaded temp file
        """
        # Parse gs://bucket/path/to/file
        if not gcs_path.startswith("gs://"):
            raise ValueError(f"Invalid GCS path: {gcs_path}")

        path_without_prefix = gcs_path[5:]  # Remove "gs://"
        parts = path_without_prefix.split("/", 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid GCS path: {gcs_path}")

        bucket_name, blob_name = parts

        # Create temp file
        fd, temp_path = tempfile.mkstemp(suffix=".duckdb")
        os.close(fd)

        # Download from GCS
        client = gcs_storage.Client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        blob.download_to_filename(temp_path)

        return temp_path

    def invalidate(self, org_id: str) -> None:
        """Invalidate cached engine and client for org.

        Call this when org's manifest or warehouse config changes.
        """
        with self._global_lock:
            if org_id in self._engines:
                del self._engines[org_id]

            cached_client = self._clients.pop(org_id, None)
            if cached_client:
                try:
                    cached_client.client.close()
                except Exception:
                    pass

    def clear_all(self) -> None:
        """Clear all cached engines and clients."""
        with self._global_lock:
            self._engines.clear()
            for cached in self._clients.values():
                try:
                    cached.client.close()
                except Exception:
                    pass
            self._clients.clear()

    def get_warehouse_info(self, org_id: str) -> dict | None:
        """Get warehouse info for cache freshness checking.

        Returns info needed by the cache layer to check data freshness:
        - For BigQuery: warehouse_type, client, project_id, dataset_ids
        - For DuckDB: warehouse_type, db_path

        Dataset IDs are automatically extracted from the semantic manifest's
        node_relation.schema_name values, so no manual configuration needed.

        Returns:
            Dict with warehouse info or None if not configured
        """
        cached = self._clients.get(org_id)
        if not cached:
            return None

        config = storage.get_warehouse_config(org_id)
        if not config:
            return None

        warehouse_type = cached.warehouse_type

        if warehouse_type == "bigquery":
            bq_config = config.get("bigquery", {})
            client_wrapper = cached.client
            # Get the underlying bigquery.Client for freshness queries
            bq_client = getattr(client_wrapper, "client", None)

            # Extract dataset IDs from manifest (no manual config needed)
            manifest_dict = storage.get_manifest(org_id)
            dataset_ids = extract_datasets_from_manifest(manifest_dict) if manifest_dict else []

            return {
                "warehouse_type": "bigquery",
                "client": bq_client,
                "project_id": bq_config.get("project_id"),
                "dataset_ids": dataset_ids,
                "db_path": None,
            }
        elif warehouse_type == "duckdb":
            duckdb_config = config.get("duckdb", {})
            client_wrapper = cached.client
            db_path = getattr(client_wrapper, "path", duckdb_config.get("path"))
            return {
                "warehouse_type": "duckdb",
                "client": None,
                "project_id": None,
                "dataset_ids": [],
                "db_path": db_path,
            }

        return None


# Singleton instance
_warehouse: Optional[OrgWarehouse] = None
_warehouse_lock = Lock()


def get_org_warehouse() -> OrgWarehouse:
    """Get the singleton OrgWarehouse instance."""
    global _warehouse
    if _warehouse is None:
        with _warehouse_lock:
            if _warehouse is None:
                _warehouse = OrgWarehouse()
    return _warehouse
