"""Storage utilities for Firestore (manifests, dashboards, config)."""

import hashlib
import json
import os
from datetime import datetime, UTC
from pathlib import Path
from typing import Optional

from google.cloud import firestore
from google.cloud.firestore_v1._helpers import DatetimeWithNanoseconds
from google.cloud.firestore_v1.base_query import FieldFilter

# Initialize client lazily
_firestore_client: Optional[firestore.Client] = None

PROJECT_ID = "metricly-dev"

# Development mode - use local files for manifest bootstrap
IS_DEV = os.environ.get("ENV") == "development"

# Local manifest paths for development bootstrap (relative to backend directory)
# These are only used when Firestore has no data - run seed script to import
LOCAL_MANIFEST_PATHS = {
    "local-dev": "../examples/demo-dbt-project/semantic_manifest.json",
}


def get_firestore_client() -> firestore.Client:
    """Get or create Firestore client."""
    global _firestore_client
    if _firestore_client is None:
        _firestore_client = firestore.Client(project=PROJECT_ID)
    return _firestore_client


def _serialize_firestore_doc(data: dict) -> dict:
    """Convert Firestore document to JSON-serializable dict.

    Converts DatetimeWithNanoseconds to ISO format strings.
    """
    result = {}
    for key, value in data.items():
        if isinstance(value, DatetimeWithNanoseconds):
            result[key] = value.isoformat()
        elif isinstance(value, datetime):
            result[key] = value.isoformat()
        elif isinstance(value, dict):
            result[key] = _serialize_firestore_doc(value)
        elif isinstance(value, list):
            result[key] = [
                _serialize_firestore_doc(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            result[key] = value
    return result


# =============================================================================
# Manifest Storage (Firestore with local dev fallback for bootstrap)
# =============================================================================

def get_manifest(org_id: str) -> Optional[dict]:
    """Get semantic manifest from Firestore, or local file in dev mode for bootstrap.

    Priority:
    1. Generate from Firestore (semantic_models + metrics collections)
    2. Fall back to local file in dev mode (for bootstrap before import)
    """
    # Try generating from Firestore first
    manifest = generate_manifest(org_id)

    # Check if we have any data in Firestore
    if manifest.get("semantic_models") or manifest.get("metrics"):
        return manifest

    # No Firestore data - try local file in dev mode for bootstrap
    if IS_DEV and org_id in LOCAL_MANIFEST_PATHS:
        local_path = Path(__file__).parent / LOCAL_MANIFEST_PATHS[org_id]
        if local_path.exists():
            content = local_path.read_text()
            return json.loads(content)

    return None


def get_manifest_status(org_id: str) -> dict:
    """Get manifest status (metadata without full content).

    Uses Firestore as primary source, with local file fallback for dev bootstrap.
    """
    db = get_firestore_client()

    # Try generating from Firestore first
    manifest = generate_manifest(org_id)

    # Check if we have any data in Firestore
    if manifest.get("semantic_models") or manifest.get("metrics"):
        # Get upload timestamp from project_configuration if available
        config_ref = db.collection("organizations").document(org_id).collection("config").document("project_configuration")
        config_doc = config_ref.get()
        updated_at = None
        if config_doc.exists:
            config_data = config_doc.to_dict()
            updated_at = config_data.get("_imported_at")
        return _extract_manifest_status(manifest, updated_at)

    # No Firestore data - try local file in dev mode for bootstrap
    if IS_DEV and org_id in LOCAL_MANIFEST_PATHS:
        local_path = Path(__file__).parent / LOCAL_MANIFEST_PATHS[org_id]
        if local_path.exists():
            content = local_path.read_text()
            local_manifest = json.loads(content)
            return _extract_manifest_status(local_manifest, local_path.stat().st_mtime)

    return {"status": "not_configured"}


# Re-export from cache.manifest for backward compatibility


def _extract_manifest_status(manifest: dict, updated_at) -> dict:
    """Extract status info from a manifest."""
    metrics = manifest.get("metrics", [])
    semantic_models = manifest.get("semantic_models", [])

    # Count unique dimensions
    all_dimensions = set()
    for model in semantic_models:
        for dim in model.get("dimensions", []):
            all_dimensions.add(dim.get("name", ""))

    project_name = manifest.get("project_configuration", {}).get("name")

    # Handle datetime, float (mtime), string (ISO format), and None for updated_at
    if isinstance(updated_at, float):
        uploaded_at = datetime.fromtimestamp(updated_at).isoformat()
    elif isinstance(updated_at, str):
        uploaded_at = updated_at  # Already ISO format
    elif updated_at:
        uploaded_at = updated_at.isoformat()
    else:
        uploaded_at = None

    return {
        "status": "configured",
        "metrics": len(metrics),
        "dimensions": len(all_dimensions),
        "semantic_models": len(semantic_models),
        "project_name": project_name,
        "uploaded_at": uploaded_at,
    }


def save_manifest(org_id: str, manifest: dict) -> dict:
    """Save semantic manifest. (DEPRECATED: Now uses Firestore via import_manifest)

    This function is kept for backward compatibility but no longer saves to GCS.
    Use import_manifest() directly for new code.
    """
    # Return status info only - actual saving happens via import_manifest
    metrics = manifest.get("metrics", [])
    semantic_models = manifest.get("semantic_models", [])

    all_dimensions = set()
    for model in semantic_models:
        for dim in model.get("dimensions", []):
            all_dimensions.add(dim.get("name", ""))

    project_name = manifest.get("project_configuration", {}).get("name")

    return {
        "status": "ok",
        "metrics": len(metrics),
        "dimensions": len(all_dimensions),
        "semantic_models": len(semantic_models),
        "project_name": project_name,
    }


# =============================================================================
# Dashboard Storage (Firestore) - Multi-dashboard with Personal/Team sections
# =============================================================================

def list_dashboards(org_id: str, user_id: str) -> dict:
    """List dashboards visible to user, split into personal and shared sections.

    Returns:
        {
            "personal": [...],  # Private dashboards owned by user
            "team": [...],      # All shared dashboards (visibility=org), including user's own
        }
    """
    db = get_firestore_client()
    dashboards_ref = db.collection("organizations").document(org_id).collection("dashboards")

    # Get all dashboards in org
    all_docs = dashboards_ref.stream()

    personal = []
    team = []

    for doc in all_docs:
        data = _serialize_firestore_doc(doc.to_dict())
        data["id"] = doc.id

        is_owner = data.get("owner") == user_id
        is_shared = data.get("visibility") == "org"

        if is_shared:
            # All shared dashboards go to team section (including user's own)
            team.append(data)
        elif is_owner:
            # User's private dashboards go to personal
            personal.append(data)
        # Skip private dashboards owned by others

    # Get user's dashboard order preferences
    member_ref = db.collection("organizations").document(org_id).collection("members").document(user_id)
    member_doc = member_ref.get()
    personal_order = []
    team_order = []

    if member_doc.exists:
        member_data = member_doc.to_dict()
        personal_order = member_data.get("personalDashboardOrder", [])
        team_order = member_data.get("teamDashboardOrder", [])

    # Sort by user's order preference, unordered items at end
    def sort_by_order(items: list, order: list) -> list:
        order_map = {id: idx for idx, id in enumerate(order)}
        return sorted(items, key=lambda x: order_map.get(x["id"], len(order)))

    return {
        "personal": sort_by_order(personal, personal_order),
        "team": sort_by_order(team, team_order),
    }


def get_dashboard(org_id: str, dashboard_id: str, user_id: str) -> Optional[dict]:
    """Get a specific dashboard if user has access."""
    db = get_firestore_client()
    doc_ref = db.collection("organizations").document(org_id).collection("dashboards").document(dashboard_id)
    doc = doc_ref.get()

    if not doc.exists:
        return None

    data = _serialize_firestore_doc(doc.to_dict())
    data["id"] = doc.id

    # Check access: owner can always access, others only if visibility=org
    if data.get("owner") != user_id and data.get("visibility") != "org":
        return None

    return data


def get_dashboard_internal(org_id: str, dashboard_id: str) -> Optional[dict]:
    """Get a dashboard by ID without user access checks.

    This is for internal/server-side use only, such as render token validation
    where the token already grants access to the resource.
    """
    db = get_firestore_client()
    doc_ref = db.collection("organizations").document(org_id).collection("dashboards").document(dashboard_id)
    doc = doc_ref.get()

    if not doc.exists:
        return None

    data = _serialize_firestore_doc(doc.to_dict())
    data["id"] = doc.id
    return data


def create_dashboard(org_id: str, user_id: str, dashboard: dict) -> dict:
    """Create a new dashboard owned by user."""
    db = get_firestore_client()
    dashboards_ref = db.collection("organizations").document(org_id).collection("dashboards")

    now = datetime.now(UTC).isoformat() + "Z"
    dashboard["owner"] = user_id
    dashboard["visibility"] = dashboard.get("visibility", "private")
    dashboard["created_at"] = now
    dashboard["updated_at"] = now
    dashboard["created_by"] = user_id
    dashboard["version"] = 1  # Initialize version for optimistic locking

    # Create with auto-generated ID
    doc_ref = dashboards_ref.document()
    dashboard["id"] = doc_ref.id
    doc_ref.set(dashboard)

    # Add to user's personal order
    member_ref = db.collection("organizations").document(org_id).collection("members").document(user_id)
    member_doc = member_ref.get()
    if member_doc.exists:
        personal_order = member_doc.to_dict().get("personalDashboardOrder", [])
        personal_order.append(doc_ref.id)
        member_ref.update({"personalDashboardOrder": personal_order})

    return dashboard


def update_dashboard(
    org_id: str,
    dashboard_id: str,
    user_id: str,
    updates: dict,
    expected_version: Optional[int] = None,
) -> Optional[dict]:
    """Update a dashboard with optional optimistic locking.

    Args:
        org_id: Organization ID
        dashboard_id: Dashboard ID
        user_id: User ID (must be owner)
        updates: Fields to update
        expected_version: If provided, reject if current version doesn't match

    Returns:
        Updated dashboard dict or None if not found/not owner

    Raises:
        ConflictError: If version mismatch detected (imported from services.dashboards)
    """
    # Import here to avoid circular import
    from services.dashboards import ConflictError

    db = get_firestore_client()
    doc_ref = db.collection("organizations").document(org_id).collection("dashboards").document(dashboard_id)
    doc = doc_ref.get()

    if not doc.exists:
        return None

    data = doc.to_dict()

    # Only owner can update
    if data.get("owner") != user_id:
        return None

    # Check version for optimistic locking
    current_version = data.get("version", 1)
    if expected_version is not None:
        if current_version != expected_version:
            raise ConflictError(
                f"Dashboard was modified (version {current_version}, expected {expected_version})",
                current_version=current_version,
                expected_version=expected_version,
            )

    # Don't allow changing owner
    updates.pop("owner", None)
    updates.pop("id", None)
    updates.pop("created_at", None)
    updates.pop("created_by", None)
    updates.pop("version", None)  # Don't allow manual version changes

    updates["updated_at"] = datetime.now(UTC).isoformat() + "Z"
    # Increment version on every update
    updates["version"] = current_version + 1

    doc_ref.update(updates)

    # Return updated document
    updated = _serialize_firestore_doc(doc_ref.get().to_dict())
    updated["id"] = dashboard_id
    return updated


def delete_dashboard(org_id: str, dashboard_id: str, user_id: str) -> bool:
    """Delete a dashboard. Only owner can delete."""
    db = get_firestore_client()
    doc_ref = db.collection("organizations").document(org_id).collection("dashboards").document(dashboard_id)
    doc = doc_ref.get()

    if not doc.exists:
        return False

    data = doc.to_dict()

    # Only owner can delete
    if data.get("owner") != user_id:
        return False

    doc_ref.delete()

    # Remove from user's personal order
    member_ref = db.collection("organizations").document(org_id).collection("members").document(user_id)
    member_doc = member_ref.get()
    if member_doc.exists:
        personal_order = member_doc.to_dict().get("personalDashboardOrder", [])
        if dashboard_id in personal_order:
            personal_order.remove(dashboard_id)
            member_ref.update({"personalDashboardOrder": personal_order})

    return True


def update_dashboard_order(org_id: str, user_id: str, personal_order: Optional[list] = None, team_order: Optional[list] = None) -> dict:
    """Update user's dashboard order preferences."""
    db = get_firestore_client()
    member_ref = db.collection("organizations").document(org_id).collection("members").document(user_id)

    updates = {}
    if personal_order is not None:
        updates["personalDashboardOrder"] = personal_order
    if team_order is not None:
        updates["teamDashboardOrder"] = team_order

    if updates:
        member_ref.update(updates)

    return {"status": "ok"}


# =============================================================================
# Business Context Storage (Firestore)
# =============================================================================

def get_business_context(org_id: str) -> Optional[str]:
    """Get business context markdown from Firestore."""
    db = get_firestore_client()
    doc_ref = db.collection("organizations").document(org_id).collection("config").document("context")
    doc = doc_ref.get()

    if not doc.exists:
        return None

    data = doc.to_dict()
    return data.get("content")


def save_business_context(org_id: str, content: str) -> dict:
    """Save business context to Firestore."""
    db = get_firestore_client()
    doc_ref = db.collection("organizations").document(org_id).collection("config").document("context")

    doc_ref.set({
        "content": content,
        "updated_at": datetime.now(UTC).isoformat() + "Z",
    })

    return {"status": "ok"}


# =============================================================================
# User Preferences Storage (Firestore)
# =============================================================================

def get_user_preferences(user_id: str) -> Optional[dict]:
    """Get user preferences from Firestore.

    Path: users/{uid}/preferences/context

    Returns:
        User preferences dict or None if not found
    """
    db = get_firestore_client()
    doc_ref = db.collection("users").document(user_id).collection("preferences").document("context")
    doc = doc_ref.get()

    if not doc.exists:
        return None

    return _serialize_firestore_doc(doc.to_dict())


def save_user_preferences(user_id: str, preferences: dict) -> dict:
    """Save user preferences to Firestore (merge with existing).

    Path: users/{uid}/preferences/context

    Args:
        user_id: User's UID
        preferences: Preferences dict to merge

    Returns:
        Updated preferences dict
    """
    db = get_firestore_client()
    doc_ref = db.collection("users").document(user_id).collection("preferences").document("context")

    # Add timestamp
    preferences["updated_at"] = datetime.now(UTC).isoformat() + "Z"

    # Merge with existing (set with merge=True)
    doc_ref.set(preferences, merge=True)

    return _serialize_firestore_doc(doc_ref.get().to_dict())


# =============================================================================
# Warehouse Config Storage (Firestore)
# =============================================================================

# Warehouse config schema:
# {
#   "type": "bigquery" | "duckdb",
#   "bigquery": {  # if type == "bigquery"
#     "project_id": "customer-warehouse",
#     "dataset": "analytics",
#     "service_account_secret": "projects/metricly-dev/secrets/org-xxx-bq-key/versions/latest"
#   },
#   "duckdb": {  # if type == "duckdb"
#     "motherduck_token_secret": "projects/metricly-dev/secrets/org-xxx-md-token/versions/latest",
#     "database": "md:my_database"
#     # OR for local/GCS file:
#     "path": "gs://bucket/org/warehouse.duckdb"
#   }
# }


def get_warehouse_config(org_id: str) -> Optional[dict]:
    """Get warehouse configuration for an organization."""
    db = get_firestore_client()
    doc_ref = db.collection("organizations").document(org_id).collection("config").document("warehouse")
    doc = doc_ref.get()

    if not doc.exists:
        return None

    return doc.to_dict()


def save_warehouse_config(org_id: str, config: dict) -> dict:
    """Save warehouse configuration for an organization.

    Args:
        org_id: Organization ID
        config: Warehouse config with 'type' and type-specific settings

    Returns:
        Status dict with saved config summary
    """
    db = get_firestore_client()
    doc_ref = db.collection("organizations").document(org_id).collection("config").document("warehouse")

    # Validate required fields
    warehouse_type = config.get("type")
    if warehouse_type not in ("bigquery", "duckdb"):
        raise ValueError(f"Invalid warehouse type: {warehouse_type}. Must be 'bigquery' or 'duckdb'")

    if warehouse_type == "bigquery":
        bq_config = config.get("bigquery", {})
        if not bq_config.get("project_id"):
            raise ValueError("BigQuery config requires 'project_id'")
    elif warehouse_type == "duckdb":
        duck_config = config.get("duckdb", {})
        if not duck_config.get("database") and not duck_config.get("path"):
            raise ValueError("DuckDB config requires 'database' or 'path'")

    config["updated_at"] = datetime.now(UTC).isoformat() + "Z"
    doc_ref.set(config)

    return {
        "status": "ok",
        "type": warehouse_type,
    }


def delete_warehouse_config(org_id: str) -> dict:
    """Delete warehouse configuration for an organization."""
    db = get_firestore_client()
    doc_ref = db.collection("organizations").document(org_id).collection("config").document("warehouse")
    doc_ref.delete()
    return {"status": "ok"}


# =============================================================================
# Semantic Layer Storage (Firestore)
# =============================================================================
#
# Collections:
#   organizations/{orgId}/semantic_models/{name} - Semantic model definitions
#   organizations/{orgId}/metrics/{name} - Metric definitions
#
# Provenance fields:
#   _origin: "imported" | "metricly" - where the definition came from
#   _imported_at: ISO timestamp of when it was imported from manifest
#   _imported_hash: hash of the original imported JSON for conflict detection
#   _modified_at: ISO timestamp of last modification in Metricly
#   _modified_by: user ID who made the modification


def _compute_hash(data: dict) -> str:
    """Compute stable hash of a dictionary for conflict detection."""
    # Remove provenance fields before hashing
    clean = {k: v for k, v in data.items() if not k.startswith("_")}
    json_str = json.dumps(clean, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(json_str.encode()).hexdigest()[:16]


# -----------------------------------------------------------------------------
# Semantic Models
# -----------------------------------------------------------------------------

def list_semantic_models(org_id: str) -> list[dict]:
    """List all semantic models for an organization."""
    db = get_firestore_client()
    models_ref = db.collection("organizations").document(org_id).collection("semantic_models")

    models = []
    for doc in models_ref.stream():
        data = doc.to_dict()
        data["name"] = doc.id
        models.append(data)

    return models


def get_semantic_model(org_id: str, name: str) -> Optional[dict]:
    """Get a specific semantic model by name."""
    db = get_firestore_client()
    doc_ref = db.collection("organizations").document(org_id).collection("semantic_models").document(name)
    doc = doc_ref.get()

    if not doc.exists:
        return None

    data = doc.to_dict()
    data["name"] = doc.id
    return data


def save_semantic_model(org_id: str, model: dict, user_id: Optional[str] = None) -> dict:
    """Save a semantic model. Used for both import and updates.

    Args:
        org_id: Organization ID
        model: Semantic model data (must include 'name')
        user_id: User making the change (None for imports)

    Returns:
        Saved model with provenance fields
    """
    db = get_firestore_client()
    name = model.get("name")
    if not name:
        raise ValueError("Semantic model must have a 'name' field")

    doc_ref = db.collection("organizations").document(org_id).collection("semantic_models").document(name)

    now = datetime.now(UTC).isoformat() + "Z"

    # Check if exists
    existing = doc_ref.get()
    if existing.exists:
        # Update existing
        model["_modified_at"] = now
        if user_id:
            model["_modified_by"] = user_id
    else:
        # New model - set imported timestamp if not present
        if "_imported_at" not in model:
            model["_imported_at"] = now

    doc_ref.set(model)

    data = doc_ref.get().to_dict()
    data["name"] = name
    return data


def create_semantic_model(org_id: str, model: dict, user_id: str) -> dict:
    """Create a new semantic model. Only for Metricly-created models.

    Args:
        org_id: Organization ID
        model: Semantic model data (must include 'name')
        user_id: User creating the model

    Returns:
        Created model with provenance fields
    """
    db = get_firestore_client()
    name = model.get("name")
    if not name:
        raise ValueError("Semantic model must have a 'name' field")

    doc_ref = db.collection("organizations").document(org_id).collection("semantic_models").document(name)

    # Check if already exists
    if doc_ref.get().exists:
        raise ValueError(f"Semantic model '{name}' already exists")

    now = datetime.now(UTC).isoformat() + "Z"
    model["_origin"] = "metricly"
    model["_modified_at"] = now
    model["_modified_by"] = user_id

    doc_ref.set(model)

    data = doc_ref.get().to_dict()
    data["name"] = name
    return data


def update_semantic_model(org_id: str, name: str, updates: dict, user_id: str) -> Optional[dict]:
    """Update an existing semantic model.

    Args:
        org_id: Organization ID
        name: Semantic model name
        updates: Fields to update
        user_id: User making the change

    Returns:
        Updated model or None if not found
    """
    db = get_firestore_client()
    doc_ref = db.collection("organizations").document(org_id).collection("semantic_models").document(name)
    doc = doc_ref.get()

    if not doc.exists:
        return None

    # Don't allow changing name or origin
    updates.pop("name", None)
    updates.pop("_origin", None)
    updates.pop("_imported_at", None)
    updates.pop("_imported_hash", None)

    now = datetime.now(UTC).isoformat() + "Z"
    updates["_modified_at"] = now
    updates["_modified_by"] = user_id

    doc_ref.update(updates)

    data = doc_ref.get().to_dict()
    data["name"] = name
    return data


def delete_semantic_model(org_id: str, name: str) -> bool:
    """Delete a semantic model by name."""
    db = get_firestore_client()
    doc_ref = db.collection("organizations").document(org_id).collection("semantic_models").document(name)
    doc = doc_ref.get()

    if not doc.exists:
        return False

    doc_ref.delete()
    return True


# -----------------------------------------------------------------------------
# Metrics
# -----------------------------------------------------------------------------

def list_metrics(org_id: str) -> list[dict]:
    """List all metrics for an organization."""
    db = get_firestore_client()
    metrics_ref = db.collection("organizations").document(org_id).collection("metrics")

    metrics = []
    for doc in metrics_ref.stream():
        data = doc.to_dict()
        data["name"] = doc.id
        metrics.append(data)

    return metrics


def get_metric(org_id: str, name: str) -> Optional[dict]:
    """Get a specific metric by name."""
    db = get_firestore_client()
    doc_ref = db.collection("organizations").document(org_id).collection("metrics").document(name)
    doc = doc_ref.get()

    if not doc.exists:
        return None

    data = doc.to_dict()
    data["name"] = doc.id
    return data


def create_metric(org_id: str, metric: dict, user_id: str) -> dict:
    """Create a new metric. Only for Metricly-created metrics.

    Args:
        org_id: Organization ID
        metric: Metric data (must include 'name')
        user_id: User creating the metric

    Returns:
        Created metric with provenance fields
    """
    db = get_firestore_client()
    name = metric.get("name")
    if not name:
        raise ValueError("Metric must have a 'name' field")

    doc_ref = db.collection("organizations").document(org_id).collection("metrics").document(name)

    # Check if already exists
    if doc_ref.get().exists:
        raise ValueError(f"Metric '{name}' already exists")

    now = datetime.now(UTC).isoformat() + "Z"
    metric["_origin"] = "metricly"
    metric["_modified_at"] = now
    metric["_modified_by"] = user_id

    doc_ref.set(metric)

    data = doc_ref.get().to_dict()
    data["name"] = name
    return data


def update_metric(org_id: str, name: str, updates: dict, user_id: str) -> Optional[dict]:
    """Update an existing metric.

    Args:
        org_id: Organization ID
        name: Metric name
        updates: Fields to update
        user_id: User making the change

    Returns:
        Updated metric or None if not found
    """
    db = get_firestore_client()
    doc_ref = db.collection("organizations").document(org_id).collection("metrics").document(name)
    doc = doc_ref.get()

    if not doc.exists:
        return None

    # Don't allow changing name or origin
    updates.pop("name", None)
    updates.pop("_origin", None)
    updates.pop("_imported_at", None)
    updates.pop("_imported_hash", None)

    now = datetime.now(UTC).isoformat() + "Z"
    updates["_modified_at"] = now
    updates["_modified_by"] = user_id

    doc_ref.update(updates)

    data = doc_ref.get().to_dict()
    data["name"] = name
    return data


def delete_metric(org_id: str, name: str) -> bool:
    """Delete a metric by name."""
    db = get_firestore_client()
    doc_ref = db.collection("organizations").document(org_id).collection("metrics").document(name)
    doc = doc_ref.get()

    if not doc.exists:
        return False

    doc_ref.delete()
    return True


# -----------------------------------------------------------------------------
# Manifest Import
# -----------------------------------------------------------------------------

def import_manifest(org_id: str, manifest: dict) -> dict:
    """Import semantic models and metrics from a manifest into Firestore.

    Merge logic:
    - New items: imported as-is with provenance
    - Unmodified imports: replaced with new version
    - User-modified items: kept as-is, flagged for review
    - Items no longer in manifest: marked as orphaned

    Args:
        org_id: Organization ID
        manifest: Full semantic manifest dict

    Returns:
        Import summary with counts and conflicts
    """
    db = get_firestore_client()
    now = datetime.now(UTC).isoformat() + "Z"

    # Get existing data
    existing_models = {m["name"]: m for m in list_semantic_models(org_id)}
    existing_metrics = {m["name"]: m for m in list_metrics(org_id)}

    # Track results
    result = {
        "semantic_models": {"imported": 0, "updated": 0, "skipped": 0, "conflicts": []},
        "metrics": {"imported": 0, "updated": 0, "skipped": 0, "conflicts": []},
    }

    # Import semantic models
    for model in manifest.get("semantic_models", []):
        name = model.get("name")
        if not name:
            continue

        new_hash = _compute_hash(model)
        model["_imported_at"] = now
        model["_imported_hash"] = new_hash

        if name in existing_models:
            existing = existing_models[name]
            old_hash = existing.get("_imported_hash")

            # Check if user modified it
            if existing.get("_modified_at") and old_hash and old_hash != _compute_hash({k: v for k, v in existing.items() if not k.startswith("_")}):
                # User modified - skip and flag conflict
                result["semantic_models"]["conflicts"].append(name)
                result["semantic_models"]["skipped"] += 1
                continue

            # Unmodified import - safe to replace
            result["semantic_models"]["updated"] += 1
        else:
            result["semantic_models"]["imported"] += 1

        save_semantic_model(org_id, model)

    # Import metrics
    for metric in manifest.get("metrics", []):
        name = metric.get("name")
        if not name:
            continue

        new_hash = _compute_hash(metric)
        metric["_origin"] = "imported"
        metric["_imported_at"] = now
        metric["_imported_hash"] = new_hash

        if name in existing_metrics:
            existing = existing_metrics[name]

            # Never overwrite Metricly-created metrics
            if existing.get("_origin") == "metricly":
                result["metrics"]["conflicts"].append(name)
                result["metrics"]["skipped"] += 1
                continue

            old_hash = existing.get("_imported_hash")

            # Check if user modified it
            if existing.get("_modified_at") and old_hash:
                current_hash = _compute_hash({k: v for k, v in existing.items() if not k.startswith("_")})
                if old_hash != current_hash:
                    # User modified - skip and flag conflict
                    result["metrics"]["conflicts"].append(name)
                    result["metrics"]["skipped"] += 1
                    continue

            # Unmodified import - safe to replace
            result["metrics"]["updated"] += 1
        else:
            result["metrics"]["imported"] += 1

        # Save directly (bypass create_metric which sets _origin to metricly)
        doc_ref = db.collection("organizations").document(org_id).collection("metrics").document(name)
        doc_ref.set(metric)

    # Find orphaned items (in Firestore but not in manifest)
    manifest_model_names = {m.get("name") for m in manifest.get("semantic_models", [])}
    manifest_metric_names = {m.get("name") for m in manifest.get("metrics", [])}

    orphaned_models = [n for n in existing_models if n not in manifest_model_names and existing_models[n].get("_origin") != "metricly"]
    orphaned_metrics = [n for n in existing_metrics if n not in manifest_metric_names and existing_metrics[n].get("_origin") == "imported"]

    result["orphaned"] = {
        "semantic_models": orphaned_models,
        "metrics": orphaned_metrics,
    }

    # Store project_configuration if present
    project_config = manifest.get("project_configuration")
    if project_config:
        config_ref = db.collection("organizations").document(org_id).collection("config").document("project_configuration")
        config_ref.set({
            "data": project_config,
            "_imported_at": now,
        })

    return result


def generate_manifest(org_id: str) -> dict:
    """Generate a semantic manifest from Firestore data.

    This creates a manifest that can be used by MetricFlow.
    Provenance fields (starting with _) are stripped.
    Aggregation type aliases are normalized (e.g., 'avg' -> 'average').

    Args:
        org_id: Organization ID

    Returns:
        Semantic manifest dict ready for MetricFlow
    """
    db = get_firestore_client()

    # Normalize aggregation types to MetricFlow's expected values
    # MetricFlow accepts: sum, min, max, count_distinct, sum_boolean, average, percentile, median, count
    agg_type_aliases = {"avg": "average", "mean": "average"}

    def normalize_measure(measure: dict) -> dict:
        """Normalize measure aggregation types."""
        result = dict(measure)
        if "agg" in result:
            agg_lower = result["agg"].lower()
            result["agg"] = agg_type_aliases.get(agg_lower, agg_lower)
        return result

    semantic_models = []
    for model in list_semantic_models(org_id):
        # Strip provenance fields
        clean_model = {k: v for k, v in model.items() if not k.startswith("_")}
        # Normalize measure aggregation types
        if "measures" in clean_model:
            clean_model["measures"] = [normalize_measure(m) for m in clean_model["measures"]]
        semantic_models.append(clean_model)

    metrics = []
    for metric in list_metrics(org_id):
        # Strip provenance fields
        clean_metric = {k: v for k, v in metric.items() if not k.startswith("_")}
        metrics.append(clean_metric)

    result = {
        "semantic_models": semantic_models,
        "metrics": metrics,
    }

    # Include project_configuration (required by MetricFlow)
    config_ref = db.collection("organizations").document(org_id).collection("config").document("project_configuration")
    config_doc = config_ref.get()
    if config_doc.exists:
        config_data = config_doc.to_dict()
        if config_data and "data" in config_data:
            result["project_configuration"] = config_data["data"]

    # Ensure project_configuration exists with at least time_spines (required by MetricFlow)
    if "project_configuration" not in result:
        result["project_configuration"] = {
            "time_spines": []
        }

    return result


# -----------------------------------------------------------------------------
# Version History
# -----------------------------------------------------------------------------

def add_history_entry(
    org_id: str,
    collection_type: str,  # "semantic_models" or "metrics"
    item_name: str,
    action: str,  # "created", "updated", "deleted"
    user_id: str,
    user_email: str,
    changes: dict,
) -> None:
    """Add a history entry for a semantic model or metric change.

    Args:
        org_id: Organization ID
        collection_type: "semantic_models" or "metrics"
        item_name: Name of the item
        action: "created", "updated", or "deleted"
        user_id: User who made the change
        user_email: Email of the user
        changes: Dict of {field: {old, new}} for updates
    """
    db = get_firestore_client()
    now = datetime.now(UTC).isoformat() + "Z"

    history_ref = (
        db.collection("organizations")
        .document(org_id)
        .collection(collection_type)
        .document(item_name)
        .collection("history")
    )

    history_ref.add({
        "user_id": user_id,
        "user_email": user_email,
        "action": action,
        "changes": changes,
        "timestamp": now,
    })


def get_history(
    org_id: str,
    collection_type: str,  # "semantic_models" or "metrics"
    item_name: str,
    limit: int = 50,
) -> list[dict]:
    """Get history entries for a semantic model or metric.

    Args:
        org_id: Organization ID
        collection_type: "semantic_models" or "metrics"
        item_name: Name of the item
        limit: Maximum number of entries to return

    Returns:
        List of history entries, oldest first
    """
    db = get_firestore_client()

    history_ref = (
        db.collection("organizations")
        .document(org_id)
        .collection(collection_type)
        .document(item_name)
        .collection("history")
    )

    entries = []
    for doc in history_ref.order_by("timestamp").stream():
        entries.append(doc.to_dict())

    return entries[:limit]


def compute_changes(old_data: dict, new_data: dict) -> dict:
    """Compute the changes between two versions of an item.

    Args:
        old_data: Previous version
        new_data: New version

    Returns:
        Dict of {field: {old, new}} for changed fields
    """
    changes = {}

    # Get all keys from both dicts, excluding provenance fields
    all_keys = set(k for k in old_data.keys() if not k.startswith("_"))
    all_keys.update(k for k in new_data.keys() if not k.startswith("_"))

    for key in all_keys:
        old_val = old_data.get(key)
        new_val = new_data.get(key)

        if old_val != new_val:
            changes[key] = {"old": old_val, "new": new_val}

    return changes


def validate_manifest(manifest: dict) -> dict:
    """Validate a semantic manifest using MetricFlow's validators.

    Performs two levels of validation:
    1. Schema validation (required fields, types)
    2. Semantic validation (references, consistency)

    Args:
        manifest: Semantic manifest dict

    Returns:
        {
            "valid": bool,
            "errors": list[str],
            "warnings": list[str]
        }
    """
    errors = []
    warnings = []

    semantic_models = manifest.get("semantic_models", [])
    metrics = manifest.get("metrics", [])

    # Track all measures for reference validation
    all_measures = set()
    # MetricFlow valid aggregation types
    valid_agg_types = {"sum", "count", "count_distinct", "average", "min", "max", "sum_boolean", "median", "percentile"}
    # Common aliases that should be accepted during validation
    agg_type_aliases = {"avg": "average", "mean": "average"}

    # Validate semantic models
    for i, model in enumerate(semantic_models):
        model_name = model.get("name")

        # Check required name field
        if not model_name:
            errors.append(f"Semantic model at index {i} is missing required 'name' field")
            continue

        # Validate measures
        for measure in model.get("measures", []):
            measure_name = measure.get("name")
            if not measure_name:
                errors.append(f"Measure in model '{model_name}' is missing required 'name' field")
                continue

            all_measures.add(measure_name)

            # Validate aggregation type (normalize aliases)
            agg = measure.get("agg")
            if agg:
                agg_lower = agg.lower()
                # Normalize common aliases
                agg_normalized = agg_type_aliases.get(agg_lower, agg_lower)
                if agg_normalized not in valid_agg_types:
                    errors.append(f"Measure '{measure_name}' in model '{model_name}' has invalid aggregation type '{agg}'")

        # Validate dimensions
        for dim in model.get("dimensions", []):
            dim_name = dim.get("name")
            if not dim_name:
                errors.append(f"Dimension in model '{model_name}' is missing required 'name' field")

    # Validate metrics
    for i, metric in enumerate(metrics):
        metric_name = metric.get("name")

        # Check required name field
        if not metric_name:
            errors.append(f"Metric at index {i} is missing required 'name' field")
            continue

        # Validate type
        metric_type = metric.get("type")
        if metric_type not in {"simple", "ratio", "derived", "cumulative", "conversion"}:
            if metric_type:
                errors.append(f"Metric '{metric_name}' has invalid type '{metric_type}'")

        # Validate measure references
        type_params = metric.get("type_params", {})

        if metric_type == "simple":
            measure_ref = type_params.get("measure")
            if measure_ref:
                measure_name = measure_ref.get("name") if isinstance(measure_ref, dict) else measure_ref
                if measure_name and measure_name not in all_measures:
                    errors.append(f"Metric '{metric_name}' references undefined measure '{measure_name}'")

        elif metric_type == "ratio":
            for field in ["numerator", "denominator"]:
                ref = type_params.get(field)
                if ref:
                    measure_name = ref.get("name") if isinstance(ref, dict) else ref
                    if measure_name and measure_name not in all_measures:
                        errors.append(f"Metric '{metric_name}' {field} references undefined measure '{measure_name}'")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
    }


# -----------------------------------------------------------------------------
# Export to dbt YAML
# -----------------------------------------------------------------------------

def _yaml_representer_str(dumper, data: str):
    """Custom YAML representer for multi-line strings."""
    if "\n" in data:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


def _clean_for_yaml(data: dict) -> dict:
    """Clean data for YAML export by removing provenance fields and nulls."""
    result = {}
    for key, value in data.items():
        # Skip provenance fields
        if key.startswith("_"):
            continue
        # Skip None values
        if value is None:
            continue
        # Recursively clean nested dicts
        if isinstance(value, dict):
            cleaned = _clean_for_yaml(value)
            if cleaned:  # Only include non-empty dicts
                result[key] = cleaned
        # Recursively clean lists
        elif isinstance(value, list):
            cleaned_list = []
            for item in value:
                if isinstance(item, dict):
                    cleaned_item = _clean_for_yaml(item)
                    if cleaned_item:
                        cleaned_list.append(cleaned_item)
                elif item is not None:
                    cleaned_list.append(item)
            if cleaned_list:
                result[key] = cleaned_list
        else:
            result[key] = value
    return result


def export_to_yaml(org_id: str) -> dict[str, str]:
    """Export semantic layer to dbt-compatible YAML files.

    Generates two YAML files:
    - semantic_models.yml: All semantic models
    - metrics.yml: All metrics

    Args:
        org_id: Organization ID

    Returns:
        Dict of {filename: yaml_content}
    """
    import yaml

    # Register custom string representer for multi-line strings
    yaml.add_representer(str, _yaml_representer_str)

    files = {}

    # Export semantic models
    models = list_semantic_models(org_id)
    if models:
        clean_models = [_clean_for_yaml(m) for m in models]
        models_yaml = yaml.dump(
            {"semantic_models": clean_models},
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
            width=120,
        )
        files["semantic_models.yml"] = models_yaml

    # Export metrics
    metrics = list_metrics(org_id)
    if metrics:
        clean_metrics = [_clean_for_yaml(m) for m in metrics]
        metrics_yaml = yaml.dump(
            {"metrics": clean_metrics},
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
            width=120,
        )
        files["metrics.yml"] = metrics_yaml

    return files


def export_to_zip(org_id: str) -> bytes:
    """Export semantic layer to a ZIP file containing dbt-compatible YAML.

    Args:
        org_id: Organization ID

    Returns:
        ZIP file as bytes
    """
    import io
    import zipfile

    files = export_to_yaml(org_id)

    # Create in-memory ZIP file
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for filename, content in files.items():
            zf.writestr(filename, content)

    return zip_buffer.getvalue()


# =============================================================================
# Waitlist
# =============================================================================

def add_to_waitlist(email: str, source: str = "website") -> dict:
    """Add an email to the waitlist.

    Args:
        email: Email address to add
        source: Where the signup came from (default: "website")

    Returns:
        Waitlist entry dict

    Raises:
        ValueError: If email is already on the waitlist
    """
    db = get_firestore_client()
    now = datetime.now(UTC).isoformat() + "Z"

    # Check if email already exists
    waitlist_ref = db.collection("waitlist")
    existing = waitlist_ref.where(filter=FieldFilter("email", "==", email.lower())).limit(1).get()

    if len(list(existing)) > 0:
        raise ValueError("Email already on waitlist")

    # Add to waitlist
    doc_ref = waitlist_ref.document()
    entry = {
        "email": email.lower(),
        "source": source,
        "created_at": now,
    }
    doc_ref.set(entry)
    entry["id"] = doc_ref.id

    return entry
