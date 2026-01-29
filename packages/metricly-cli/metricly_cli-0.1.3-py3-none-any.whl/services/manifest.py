"""Manifest services - semantic layer management for admins.

Provides typed manifest operations for MCP, CLI, and chat consumers.
Wraps storage.py with Pydantic validation, permission checks, and fork detection.
"""

from dataclasses import dataclass, field
from typing import Literal

from services.auth import UserContext, require_role

import storage


# ============================================================================
# Types
# ============================================================================


@dataclass
class ManifestStatus:
    """Status information about an organization's manifest."""

    org_id: str
    project_name: str | None
    metric_count: int
    model_count: int
    dimension_count: int
    last_updated: str | None


@dataclass
class ConflictItem:
    """A conflict detected during manifest import."""

    name: str
    type: Literal["metric", "model"]
    reason: str  # "modified_since_import" or "origin_metricly"


@dataclass
class ManifestImportResult:
    """Result of a manifest import operation."""

    imported_metrics: int
    imported_models: int
    skipped_metrics: int
    skipped_models: int
    conflicts: list[ConflictItem] = field(default_factory=list)
    orphaned: list[str] = field(default_factory=list)


# ============================================================================
# Read Operations
# ============================================================================


async def get_manifest_status(user: UserContext) -> ManifestStatus:
    """Get status information about the organization's manifest.

    Args:
        user: Authenticated user context

    Returns:
        ManifestStatus with counts and metadata
    """
    manifest = storage.get_manifest(user.org_id)

    if not manifest:
        return ManifestStatus(
            org_id=user.org_id,
            project_name=None,
            metric_count=0,
            model_count=0,
            dimension_count=0,
            last_updated=None,
        )

    # Count dimensions across all semantic models
    dimension_count = 0
    models = manifest.get("semantic_models", [])
    for model in models:
        dimension_count += len(model.get("dimensions", []))

    # Get project name from configuration
    project_config = manifest.get("project_configuration", {})
    project_name = project_config.get("name")

    # Get last updated timestamp from any metric/model
    last_updated = None
    metrics = manifest.get("metrics", [])
    for metric in metrics:
        modified = metric.get("_modified_at") or metric.get("_imported_at")
        if modified and (not last_updated or modified > last_updated):
            last_updated = modified

    return ManifestStatus(
        org_id=user.org_id,
        project_name=project_name,
        metric_count=len(metrics),
        model_count=len(models),
        dimension_count=dimension_count,
        last_updated=last_updated,
    )


async def list_semantic_models(user: UserContext) -> list[dict]:
    """List all semantic models in the organization.

    Args:
        user: Authenticated user context

    Returns:
        List of semantic model dicts with name, description, measures, dimensions
    """
    models = storage.list_semantic_models(user.org_id)
    return models


async def get_semantic_model(user: UserContext, name: str) -> dict:
    """Get a semantic model by name.

    Args:
        user: Authenticated user context
        name: Model name

    Returns:
        Semantic model dict

    Raises:
        ValueError: If model not found
    """
    model = storage.get_semantic_model(user.org_id, name)

    if not model:
        raise ValueError(f"Semantic model '{name}' not found")

    return model


async def list_metrics(user: UserContext) -> list[dict]:
    """List all metrics in the organization.

    Args:
        user: Authenticated user context

    Returns:
        List of metric dicts with name, type, description
    """
    metrics = storage.list_metrics(user.org_id)
    return metrics


async def get_metric(user: UserContext, name: str) -> dict:
    """Get a metric by name.

    Args:
        user: Authenticated user context
        name: Metric name

    Returns:
        Metric dict

    Raises:
        ValueError: If metric not found
    """
    metric = storage.get_metric(user.org_id, name)

    if not metric:
        raise ValueError(f"Metric '{name}' not found")

    return metric


# ============================================================================
# Model CRUD Operations
# ============================================================================


async def create_semantic_model(user: UserContext, model_data: dict) -> dict:
    """Create a new semantic model.

    Args:
        user: Authenticated user context (must be admin or owner)
        model_data: Semantic model definition

    Returns:
        Created semantic model dict

    Raises:
        PermissionError: If user lacks admin role
        ValueError: If model already exists or validation fails
    """
    require_role(user, "admin")

    name = model_data.get("name")
    if not name:
        raise ValueError("Semantic model must have a name")

    # Check if model already exists
    existing = storage.get_semantic_model(user.org_id, name)
    if existing:
        raise ValueError(f"Semantic model '{name}' already exists")

    # Set provenance
    model_data["_origin"] = "metricly"

    result = storage.save_semantic_model(user.org_id, model_data, user.uid)

    # Invalidate cache
    from warehouse import get_org_warehouse
    get_org_warehouse().invalidate(user.org_id)

    return result


async def update_semantic_model(
    user: UserContext, name: str, updates: dict
) -> dict:
    """Update an existing semantic model.

    Args:
        user: Authenticated user context (must be admin or owner)
        name: Model name to update
        updates: Fields to update

    Returns:
        Updated semantic model dict

    Raises:
        PermissionError: If user lacks admin role
        ValueError: If model not found
    """
    require_role(user, "admin")

    existing = storage.get_semantic_model(user.org_id, name)
    if not existing:
        raise ValueError(f"Semantic model '{name}' not found")

    # Merge updates
    updated = {**existing, **updates}
    updated["name"] = name  # Prevent name change

    result = storage.save_semantic_model(user.org_id, updated, user.uid)

    # Invalidate cache
    from warehouse import get_org_warehouse
    get_org_warehouse().invalidate(user.org_id)

    return result


async def delete_semantic_model(user: UserContext, name: str) -> bool:
    """Delete a semantic model.

    Args:
        user: Authenticated user context (must be admin or owner)
        name: Model name to delete

    Returns:
        True if deleted

    Raises:
        PermissionError: If user lacks admin role
        ValueError: If model not found
    """
    require_role(user, "admin")

    existing = storage.get_semantic_model(user.org_id, name)
    if not existing:
        raise ValueError(f"Semantic model '{name}' not found")

    storage.delete_semantic_model(user.org_id, name)

    # Invalidate cache
    from warehouse import get_org_warehouse
    get_org_warehouse().invalidate(user.org_id)

    return True


# ============================================================================
# Metric CRUD Operations
# ============================================================================


async def create_metric(user: UserContext, metric_data: dict) -> dict:
    """Create a new metric.

    Args:
        user: Authenticated user context (must be admin or owner)
        metric_data: Metric definition

    Returns:
        Created metric dict

    Raises:
        PermissionError: If user lacks admin role
        ValueError: If metric already exists or validation fails
    """
    require_role(user, "admin")

    name = metric_data.get("name")
    if not name:
        raise ValueError("Metric must have a name")

    # Check if metric already exists
    existing = storage.get_metric(user.org_id, name)
    if existing:
        raise ValueError(f"Metric '{name}' already exists")

    # Set provenance for user-created metrics
    metric_data["_origin"] = "metricly"

    result = storage.create_metric(user.org_id, metric_data, user.uid)

    # Invalidate cache
    from warehouse import get_org_warehouse
    get_org_warehouse().invalidate(user.org_id)

    return result


async def update_metric(user: UserContext, name: str, updates: dict) -> dict:
    """Update an existing metric.

    Args:
        user: Authenticated user context (must be admin or owner)
        name: Metric name to update
        updates: Fields to update

    Returns:
        Updated metric dict

    Raises:
        PermissionError: If user lacks admin role
        ValueError: If metric not found
    """
    require_role(user, "admin")

    existing = storage.get_metric(user.org_id, name)
    if not existing:
        raise ValueError(f"Metric '{name}' not found")

    result = storage.update_metric(user.org_id, name, updates, user.uid)

    # Invalidate cache
    from warehouse import get_org_warehouse
    get_org_warehouse().invalidate(user.org_id)

    return result


async def delete_metric(user: UserContext, name: str) -> bool:
    """Delete a metric.

    Args:
        user: Authenticated user context (must be admin or owner)
        name: Metric name to delete

    Returns:
        True if deleted

    Raises:
        PermissionError: If user lacks admin role
        ValueError: If metric not found
    """
    require_role(user, "admin")

    existing = storage.get_metric(user.org_id, name)
    if not existing:
        raise ValueError(f"Metric '{name}' not found")

    storage.delete_metric(user.org_id, name)

    # Invalidate cache
    from warehouse import get_org_warehouse
    get_org_warehouse().invalidate(user.org_id)

    return True


# ============================================================================
# Manifest Import/Export
# ============================================================================


async def import_manifest(
    user: UserContext,
    manifest_data: dict,
    force: bool = False,
) -> ManifestImportResult:
    """Import a manifest with conflict detection.

    Args:
        user: Authenticated user context (must be admin or owner)
        manifest_data: Full manifest dict with metrics and semantic_models
        force: If True, overwrite forked metrics. If False, raise on conflicts.

    Returns:
        ManifestImportResult with import statistics

    Raises:
        PermissionError: If user lacks admin role
        ValueError: If conflicts detected and force=False
    """
    require_role(user, "admin")

    # Validate manifest structure
    if "metrics" not in manifest_data and "semantic_models" not in manifest_data:
        raise ValueError("Manifest must contain 'metrics' or 'semantic_models'")

    # Call storage import which handles merge logic
    result = storage.import_manifest(user.org_id, manifest_data)

    # Extract counts from nested structure
    models_result = result.get("semantic_models", {})
    metrics_result = result.get("metrics", {})

    # Build conflict list from storage result
    conflicts = []
    for name in models_result.get("conflicts", []):
        conflicts.append(ConflictItem(
            name=name,
            type="model",
            reason="modified_since_import",
        ))
    for name in metrics_result.get("conflicts", []):
        conflicts.append(ConflictItem(
            name=name,
            type="metric",
            reason="modified_since_import",
        ))

    # If conflicts and not force, raise error
    if conflicts and not force:
        conflict_names = [c.name for c in conflicts]
        raise ValueError(
            f"Import blocked: {len(conflicts)} forked items would be overwritten. "
            f"Items: {', '.join(conflict_names)}. "
            f"Use --force to overwrite."
        )

    # Invalidate cache
    from warehouse import get_org_warehouse
    get_org_warehouse().invalidate(user.org_id)

    # Build orphaned list from nested structure
    orphaned_result = result.get("orphaned", {})
    orphaned = orphaned_result.get("semantic_models", []) + orphaned_result.get("metrics", [])

    return ManifestImportResult(
        imported_metrics=metrics_result.get("imported", 0) + metrics_result.get("updated", 0),
        imported_models=models_result.get("imported", 0) + models_result.get("updated", 0),
        skipped_metrics=metrics_result.get("skipped", 0),
        skipped_models=models_result.get("skipped", 0),
        conflicts=conflicts,
        orphaned=orphaned,
    )


async def export_manifest(user: UserContext) -> dict:
    """Export the organization's manifest.

    Args:
        user: Authenticated user context

    Returns:
        Full manifest dict with metrics, semantic_models, project_configuration
    """
    manifest = storage.get_manifest(user.org_id)

    if not manifest:
        return {
            "metrics": [],
            "semantic_models": [],
            "project_configuration": {},
        }

    # Strip internal provenance fields for export
    def strip_provenance(item: dict) -> dict:
        return {k: v for k, v in item.items() if not k.startswith("_")}

    return {
        "metrics": [strip_provenance(m) for m in manifest.get("metrics", [])],
        "semantic_models": [strip_provenance(m) for m in manifest.get("semantic_models", [])],
        "project_configuration": manifest.get("project_configuration", {}),
    }


# ============================================================================
# Preview Operations
# ============================================================================


async def preview_metric(
    user: UserContext,
    metric_data: dict,
    sample_query: dict | None = None,
) -> dict:
    """Preview a metric's query results before saving.

    Args:
        user: Authenticated user context
        metric_data: Metric definition to preview
        sample_query: Optional query params (defaults to last 7 days, limit 5)

    Returns:
        Dict with 'data' (query results) or 'error' (validation/query error)
    """
    from datetime import datetime, timedelta
    from concurrent.futures import ThreadPoolExecutor

    from warehouse import get_org_warehouse

    metric_name = metric_data.get("name")
    if not metric_name:
        return {"error": "Metric must have a name"}

    try:
        # Get current manifest and add/replace metric
        manifest = storage.get_manifest(user.org_id)
        if not manifest:
            return {"error": "No manifest found for organization"}

        # Create temporary manifest with the preview metric
        temp_manifest = {
            "semantic_models": manifest.get("semantic_models", []),
            "metrics": [m for m in manifest.get("metrics", []) if m.get("name") != metric_name],
            "project_configuration": manifest.get("project_configuration", {}),
        }
        temp_manifest["metrics"].append(metric_data)

        # Build temporary engine
        org_warehouse = get_org_warehouse()
        engine = org_warehouse.build_temp_engine(user.org_id, temp_manifest)

        # Build query
        from metricflow.engine.metricflow_engine import MetricFlowQueryRequest

        if sample_query:
            start_date = sample_query.get("start_date")
            end_date = sample_query.get("end_date")
            grain = sample_query.get("grain")
            limit = sample_query.get("limit", 5)
        else:
            # Default: last 7 days
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=7)
            grain = "day"
            limit = 5

        group_by = []
        if grain:
            group_by.append(f"metric_time__{grain}")

        request = MetricFlowQueryRequest.create_with_random_request_id(
            metric_names=[metric_name],
            group_by_names=group_by if group_by else None,
            limit=limit,
            time_constraint_start=start_date,
            time_constraint_end=end_date,
        )

        # Execute query in thread pool
        with ThreadPoolExecutor(max_workers=1) as executor:
            def run_query():
                result = engine.query(request)
                if result.exception:
                    raise result.exception
                return result.df

            df = executor.submit(run_query).result(timeout=30)

        return {
            "success": True,
            "data": df.to_dict(orient="records"),
            "columns": list(df.columns),
            "row_count": len(df),
        }

    except Exception as e:
        return {"error": str(e)}
