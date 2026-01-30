"""Manifest-only MetricFlow engine setup.

Loads semantic manifest from JSON and creates a MetricFlow engine that generates SQL
without requiring a dbt project or database credentials at initialization time.

See docs/metricflow-python-guide.md for details.
"""

import json
from datetime import datetime
from pathlib import Path

from dbt_semantic_interfaces.implementations.semantic_manifest import PydanticSemanticManifest
from metricflow_semantics.model.semantic_manifest_lookup import SemanticManifestLookup
from metricflow_semantics.time.time_source import TimeSource
from metricflow.engine.metricflow_engine import MetricFlowEngine
from metricflow.protocols.sql_client import SqlEngine
from metricflow.sql.render.big_query import BigQuerySqlPlanRenderer
from metricflow.sql.render.duckdb_renderer import DuckDbSqlPlanRenderer


class SimpleTimeSource(TimeSource):
    """Simple time source that returns current time."""

    def get_time(self) -> datetime:
        return datetime.now()


class SqlGeneratorClient:
    """Mock SQL client for SQL generation only - no query execution.

    MetricFlow requires a SQL client, but for SQL generation via explain()
    we only need the renderer. This client raises errors if anyone tries
    to actually execute queries through it.
    """

    def __init__(self, sql_engine: SqlEngine, renderer):
        self._sql_engine_type = sql_engine
        self._renderer = renderer

    @property
    def sql_engine_type(self) -> SqlEngine:
        return self._sql_engine_type

    @property
    def sql_plan_renderer(self):
        return self._renderer

    def query(self, *args, **kwargs):
        raise NotImplementedError("Use explain() for SQL generation, then execute with BigQuery client")

    def execute(self, *args, **kwargs):
        raise NotImplementedError("Use explain() for SQL generation, then execute with BigQuery client")

    def dry_run(self, *args, **kwargs):
        raise NotImplementedError("Use explain() for SQL generation, then execute with BigQuery client")

    def close(self):
        pass

    def render_bind_parameter_key(self, bind_parameter_name: str) -> str:
        return f"@{bind_parameter_name}"


def load_manifest(manifest_path: Path) -> PydanticSemanticManifest:
    """Load semantic manifest from JSON file."""
    with open(manifest_path) as f:
        manifest_dict = json.load(f)
    return PydanticSemanticManifest.parse_obj(manifest_dict)


def load_manifest_from_dict(manifest_dict: dict) -> PydanticSemanticManifest:
    """Load semantic manifest from a dictionary (e.g., from Firestore)."""
    return PydanticSemanticManifest.parse_obj(manifest_dict)


def create_engine(manifest: PydanticSemanticManifest, warehouse_type: str = "bigquery") -> MetricFlowEngine:
    """Create a MetricFlow engine for SQL generation.

    The engine can generate SQL via explain() but cannot execute queries.
    Use a separate warehouse client for query execution.

    Args:
        manifest: The semantic manifest
        warehouse_type: "bigquery" or "duckdb"
    """
    lookup = SemanticManifestLookup(manifest)

    if warehouse_type == "duckdb":
        sql_engine = SqlEngine.DUCKDB
        renderer = DuckDbSqlPlanRenderer()
    else:
        sql_engine = SqlEngine.BIGQUERY
        renderer = BigQuerySqlPlanRenderer()

    sql_client = SqlGeneratorClient(sql_engine, renderer)
    return MetricFlowEngine(
        semantic_manifest_lookup=lookup,
        sql_client=sql_client,
        time_source=SimpleTimeSource(),
    )
