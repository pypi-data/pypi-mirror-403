"""Metricly API Backend - uses MetricFlow SDK directly for metric queries."""

import asyncio
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Literal
from dateutil.relativedelta import relativedelta

from fastapi import FastAPI, HTTPException, Depends, Response, Request, Query, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from chat import get_agent, ChatDependencies, ChatRequest, ChatResponse
from auth import get_current_user, get_current_user_flexible, require_org_role, AuthenticatedUser
from warehouse import get_org_warehouse, QueryClient
from mcp_server import app as mcp_app
from mf_engine import load_manifest_from_dict, create_engine
import storage
from cache import (
    get_cache_coordinator,
    get_cached_response,
    cache_response,
    build_cdn_headers,
    build_no_cache_headers,
)
from services.render import (
    render_dashboard,
    render_widget,
    validate_render_token,
    RenderError,
    ChromeConnectionError,
    RenderTimeoutError,
)

logger = logging.getLogger(__name__)

# Heavy imports placed after logger init for startup time optimization
from dbt_semantic_interfaces.implementations.semantic_manifest import PydanticSemanticManifest  # noqa: E402
from metricflow.engine.metricflow_engine import (  # noqa: E402
    MetricFlowEngine,
    MetricFlowQueryRequest,
    MetricFlowRequestId,
    MetricFlowQueryType,
    SqlOptimizationLevel,
)
from metricflow_semantics.random_id import random_id  # noqa: E402

# Thread pool for running blocking operations concurrently
# Sized to handle multiple widgets with comparison queries (2 queries per widget)
query_executor = ThreadPoolExecutor(max_workers=20)


def build_llm_context(manifest: PydanticSemanticManifest, org_id: str) -> str:
    """Build LLM context from manifest and persistent storage.

    Uses the already-loaded manifest (from Firestore) and fetches
    business context from Firestore.
    """
    # Extract metrics info from manifest
    metrics = []
    for metric in manifest.metrics:
        metric_type = getattr(metric.type, "__class__", type(metric.type)).__name__
        metrics.append({
            "name": metric.name,
            "description": metric.description or "",
            "type": metric_type,
        })

    # Extract dimensions from semantic models
    dimensions = {}
    for model in manifest.semantic_models:
        for dim in model.dimensions:
            if dim.name not in dimensions:
                dimensions[dim.name] = {
                    "name": dim.name,
                    "description": dim.description or "",
                    "type": dim.type.value if hasattr(dim.type, "value") else str(dim.type),
                }

    # Get business context from Firestore (persistent storage)
    business_context = storage.get_business_context(org_id) or ""

    # Build condensed metrics section
    metrics_section = "## Available Metrics\n\n"
    for m in sorted(metrics, key=lambda x: x["name"]):
        desc = m["description"][:100] + "..." if len(m["description"]) > 100 else m["description"]
        metrics_section += f"- **{m['name']}**: {desc}\n"

    # Build condensed dimensions section
    dims_section = "\n## Available Dimensions\n\n"
    dims_list = list(dimensions.values())
    time_dims = [d for d in dims_list if d["type"] == "time"]
    cat_dims = [d for d in dims_list if d["type"] != "time"]

    dims_section += "### Time Dimensions (support day/week/month/quarter/year grain)\n"
    for d in sorted(time_dims, key=lambda x: x["name"]):
        dims_section += f"- {d['name']}\n"

    dims_section += "\n### Categorical Dimensions\n"
    for d in sorted(cat_dims, key=lambda x: x["name"])[:50]:
        desc = d.get("description") or ""
        if len(desc) > 60:
            desc = desc[:60] + "..."
        dims_section += f"- {d['name']}: {desc}\n" if desc else f"- {d['name']}\n"

    return f"""# Semantic Layer Context

{metrics_section}
{dims_section}

## Business Context

{business_context}
"""


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize application resources at startup."""
    print("Metricly API starting...")
    print("  Per-org warehouse connections initialized on-demand")

    # Run MCP server lifespan alongside main app
    async with mcp_app.lifespan(mcp_app):
        yield

    # Cleanup
    query_executor.shutdown(wait=False)
    get_org_warehouse().clear_all()


app = FastAPI(title="Metricly API", version="0.3.0", lifespan=lifespan)

# Handle proxy headers from Firebase Hosting / Cloud Run
# This ensures redirects use the correct external host (metricly.xyz) instead of internal Cloud Run URL
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=["*"])

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:5050",
        "http://127.0.0.1:5050",
        "http://host.docker.internal:5173",  # For headless Chrome rendering
        "https://metricly-dev.web.app",
        "https://metricly-dev.firebaseapp.com",
        "https://metricly.xyz",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redirect /api/mcp (no trailing slash) to /api/mcp/ with correct external URL
# This MUST be defined BEFORE the mount to take precedence
# It prevents Starlette's internal redirect which uses the wrong (internal Cloud Run) host
from starlette.responses import RedirectResponse


@app.api_route("/api/mcp", methods=["GET", "POST", "DELETE"])
async def mcp_add_trailing_slash():
    """Redirect to /api/mcp/ using the external URL."""
    return RedirectResponse(url="https://metricly.xyz/api/mcp/", status_code=307)


# Mount MCP server at /api/mcp for Claude.ai integration
# Firebase Hosting rewrites /api/* to Cloud Run, passing the full path
# Mount MCP app - OAuth routes will be at /api/mcp/authorize, /api/mcp/token, etc.
app.mount("/api/mcp", mcp_app)


# Serve static frontend assets for render pages (eliminates 60s Firebase Hosting latency)
# Chrome in this container loads render pages from localhost instead of going through internet
import os
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(STATIC_DIR):
    # Mount static assets (JS, CSS, images)
    app.mount("/assets", StaticFiles(directory=os.path.join(STATIC_DIR, "assets")), name="static-assets")

    # Serve SPA index.html for all render routes
    @app.get("/render/{path:path}")
    async def serve_render_spa(path: str):
        """Serve the SPA for render routes (dashboard/widget rendering)."""
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))


# RFC 9728: OAuth well-known endpoints for MCP
# Claude.ai checks these root-level paths during OAuth discovery
@app.get("/.well-known/oauth-protected-resource/api/mcp")
@app.get("/.well-known/oauth-protected-resource/api/mcp/")
async def oauth_protected_resource_metadata_api():
    """Serve OAuth protected resource metadata for /api/mcp endpoint."""
    return JSONResponse({
        "resource": "https://metricly.xyz/api/mcp",
        "authorization_servers": ["https://metricly.xyz/api/mcp"],
        "scopes_supported": ["openid", "https://www.googleapis.com/auth/userinfo.email"],
        "bearer_methods_supported": ["header"],
    })


@app.get("/.well-known/oauth-protected-resource")
@app.get("/.well-known/oauth-protected-resource/")
async def oauth_protected_resource_metadata_root():
    """Serve OAuth protected resource metadata at root (redirects to /api/mcp)."""
    return JSONResponse({
        "resource": "https://metricly.xyz/api/mcp",
        "authorization_servers": ["https://metricly.xyz/api/mcp"],
        "scopes_supported": ["openid", "https://www.googleapis.com/auth/userinfo.email"],
        "bearer_methods_supported": ["header"],
    })


@app.get("/.well-known/oauth-authorization-server")
@app.get("/.well-known/oauth-authorization-server/")
@app.get("/.well-known/oauth-authorization-server/api/mcp")
@app.get("/.well-known/oauth-authorization-server/api/mcp/")
async def oauth_authorization_server_metadata():
    """Serve OAuth authorization server metadata."""
    return JSONResponse({
        "issuer": "https://metricly.xyz/api/mcp",
        "authorization_endpoint": "https://metricly.xyz/api/mcp/authorize",
        "token_endpoint": "https://metricly.xyz/api/mcp/token",
        "registration_endpoint": "https://metricly.xyz/api/mcp/register",
        "scopes_supported": ["openid", "https://www.googleapis.com/auth/userinfo.email"],
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "token_endpoint_auth_methods_supported": ["client_secret_post", "client_secret_basic"],
        "code_challenge_methods_supported": ["S256"],
    })


# OpenID Connect discovery endpoints (Claude.ai checks these too)
@app.get("/.well-known/openid-configuration")
@app.get("/.well-known/openid-configuration/")
@app.get("/.well-known/openid-configuration/api/mcp")
@app.get("/.well-known/openid-configuration/api/mcp/")
@app.get("/api/mcp/.well-known/openid-configuration")
@app.get("/api/mcp/.well-known/openid-configuration/")
async def openid_configuration():
    """Serve OpenID Connect discovery document."""
    return JSONResponse({
        "issuer": "https://metricly.xyz/api/mcp",
        "authorization_endpoint": "https://metricly.xyz/api/mcp/authorize",
        "token_endpoint": "https://metricly.xyz/api/mcp/token",
        "registration_endpoint": "https://metricly.xyz/api/mcp/register",
        "jwks_uri": "https://metricly.xyz/api/mcp/.well-known/jwks.json",
        "scopes_supported": ["openid", "https://www.googleapis.com/auth/userinfo.email"],
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "subject_types_supported": ["public"],
        "id_token_signing_alg_values_supported": ["RS256"],
        "token_endpoint_auth_methods_supported": ["client_secret_post", "client_secret_basic"],
        "code_challenge_methods_supported": ["S256"],
    })


class QueryRequest(BaseModel):
    metrics: list[str]
    dimensions: list[str] | None = None
    grain: str | None = None
    filters: list[dict] | None = None
    order_by: str | None = None
    limit: int | None = None
    start_date: str | None = None  # ISO date string (YYYY-MM-DD)
    end_date: str | None = None    # ISO date string (YYYY-MM-DD)
    comparison: Literal["none", "previous_period", "same_period_last_year"] | None = None


class QueryResponse(BaseModel):
    data: list[dict]
    columns: list[str]
    comparison_data: list[dict] | None = None
    comparison_range: dict | None = None  # {start_date, end_date} for display


def compute_comparison_dates(
    start_date: str | None,
    end_date: str | None,
    comparison: str
) -> tuple[datetime | None, datetime | None]:
    """Compute the comparison period date range."""
    if not start_date or not end_date:
        return None, None

    start = datetime.fromisoformat(start_date)
    end = datetime.fromisoformat(end_date)

    if comparison == "same_period_last_year":
        # Shift both dates back by 1 year
        comp_start = start - relativedelta(years=1)
        comp_end = end - relativedelta(years=1)
    elif comparison == "previous_period":
        # Calculate period length and shift back by that amount
        period_days = (end - start).days + 1
        comp_end = start - timedelta(days=1)
        comp_start = comp_end - timedelta(days=period_days - 1)
    else:
        return None, None

    return comp_start, comp_end


@app.get("/health")
async def health():
    return {"status": "ok", "engine": "per_org_on_demand"}


# ============================================================================
# Waitlist Endpoint (public, no auth required)
# ============================================================================

class WaitlistRequest(BaseModel):
    email: str

@app.post("/api/waitlist")
async def join_waitlist(request: WaitlistRequest):
    """Add email to the waitlist."""
    import re

    # Basic email validation
    email = request.email.strip()
    if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
        raise HTTPException(status_code=400, detail="Invalid email address")

    try:
        storage.add_to_waitlist(email)
        return {"status": "ok", "message": "Successfully joined waitlist"}
    except ValueError:
        # Already on waitlist - return success anyway (don't expose this)
        return {"status": "ok", "message": "Successfully joined waitlist"}
    except Exception as e:
        logger.error(f"Waitlist error: {e}")
        raise HTTPException(status_code=500, detail="Failed to join waitlist")


@app.get("/api/cache/stats")
async def cache_stats(user: AuthenticatedUser = Depends(require_org_role("owner", "admin"))):
    """Get cache statistics. Requires admin role."""
    coordinator = get_cache_coordinator()
    return JSONResponse(content=coordinator.stats(), headers=build_no_cache_headers())


@app.post("/api/cache/invalidate")
async def invalidate_cache(user: AuthenticatedUser = Depends(require_org_role("owner", "admin"))):
    """Invalidate all cached queries for this organization. Requires admin role."""
    coordinator = get_cache_coordinator()
    l1_count, l2_count = await coordinator.invalidate_org(user.org_id)
    logger.info(f"Manual cache invalidation for org {user.org_id}: L1={l1_count}, L2={l2_count}")
    return {
        "status": "ok",
        "invalidated": {
            "l1_entries": l1_count,
            "l2_entries": l2_count,
        }
    }


@app.get("/metrics")
async def list_metrics(user: AuthenticatedUser = Depends(get_current_user)):
    """List all available metrics from MetricFlow."""
    try:
        engine, _ = get_org_warehouse().get_engine(user.org_id)
        metrics = engine.list_metrics()
        return {"metrics": [m.name for m in metrics]}
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))


# ============================================================================
# Dashboard Endpoints
# ============================================================================


@app.get("/api/manifest")
async def get_manifest_status_endpoint(user: AuthenticatedUser = Depends(get_current_user)):
    """Get current manifest status for an organization."""
    try:
        data = storage.get_manifest_status(user.org_id)
        return JSONResponse(content=data, headers=build_no_cache_headers())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read manifest: {e}")


@app.put("/api/manifest")
async def upload_manifest(
    manifest: dict,
    user: AuthenticatedUser = Depends(require_org_role("owner", "admin")),
):
    """Upload/update semantic manifest for an organization. Requires admin role.

    Also imports semantic models and metrics into Firestore for editing.
    Merge logic: user-modified items are kept, unmodified imports are replaced.
    """
    # Validate it's a semantic manifest
    if not manifest.get("metrics") or not isinstance(manifest.get("metrics"), list):
        raise HTTPException(status_code=400, detail="Invalid manifest: missing 'metrics' array")

    if not manifest.get("semantic_models") or not isinstance(manifest.get("semantic_models"), list):
        raise HTTPException(status_code=400, detail="Invalid manifest: missing 'semantic_models' array")

    try:
        # Import into Firestore (merges with user modifications)
        import_result = storage.import_manifest(user.org_id, manifest)
        logger.info(f"Imported manifest for org {user.org_id}: {import_result}")

        # Get status info from the manifest
        status = storage.save_manifest(user.org_id, manifest)

        # Invalidate cached engine for this org
        get_org_warehouse().invalidate(user.org_id)
        # Invalidate query cache for this org (manifest change affects queries)
        cache_coordinator = get_cache_coordinator()
        await cache_coordinator.invalidate_org(user.org_id)
        logger.info(f"Invalidated cache for org {user.org_id} after manifest update")

        return {**status, "import": import_result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save manifest: {e}")


# ============================================================================
# Semantic Layer Endpoints (Firestore-native)
# ============================================================================


@app.post("/api/semantic-layer/import")
async def import_manifest_endpoint(
    manifest: dict,
    user: AuthenticatedUser = Depends(require_org_role("owner", "admin")),
):
    """Import semantic models and metrics from a manifest into Firestore.

    This parses the manifest and stores semantic models and metrics in Firestore,
    enabling editing and CRUD operations. Merge logic:
    - New items: imported with provenance tracking
    - Unmodified imports: replaced with new version
    - User-modified items: kept as-is, flagged as conflicts
    - Orphaned items: reported (not deleted)

    Requires admin role.
    """
    # Validate manifest structure
    if not manifest.get("semantic_models") or not isinstance(manifest.get("semantic_models"), list):
        raise HTTPException(status_code=400, detail="Invalid manifest: missing 'semantic_models' array")

    if not manifest.get("metrics") or not isinstance(manifest.get("metrics"), list):
        raise HTTPException(status_code=400, detail="Invalid manifest: missing 'metrics' array")

    try:
        result = storage.import_manifest(user.org_id, manifest)
        # Invalidate caches
        get_org_warehouse().invalidate(user.org_id)
        cache_coordinator = get_cache_coordinator()
        await cache_coordinator.invalidate_org(user.org_id)
        logger.info(f"Imported manifest for org {user.org_id}: {result}")
        return result
    except Exception as e:
        logger.error(f"Failed to import manifest: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to import manifest: {e}")


@app.post("/api/semantic-layer/validate")
async def validate_manifest_endpoint(
    manifest: dict,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Validate a semantic manifest without saving.

    Returns validation errors and warnings. Use this to check changes before
    saving semantic models or metrics.
    """
    try:
        result = storage.validate_manifest(manifest)
        return result
    except Exception as e:
        logger.error(f"Failed to validate manifest: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to validate manifest: {e}")


@app.get("/api/semantic-layer/models")
async def list_semantic_models_endpoint(user: AuthenticatedUser = Depends(get_current_user)):
    """List all semantic models for the organization."""
    try:
        models = storage.list_semantic_models(user.org_id)
        return {"semantic_models": models}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list semantic models: {e}")


@app.get("/api/semantic-layer/models/{name}")
async def get_semantic_model_endpoint(
    name: str,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Get a specific semantic model by name."""
    try:
        model = storage.get_semantic_model(user.org_id, name)
        if not model:
            raise HTTPException(status_code=404, detail=f"Semantic model '{name}' not found")
        return model
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get semantic model: {e}")


@app.post("/api/semantic-layer/models")
async def create_semantic_model_endpoint(
    model: dict,
    user: AuthenticatedUser = Depends(require_org_role("owner", "admin")),
):
    """Create a new semantic model. Requires admin role."""
    try:
        # Check if model already exists
        existing = storage.get_semantic_model(user.org_id, model.get("name", ""))
        if existing:
            raise HTTPException(status_code=400, detail=f"Semantic model '{model.get('name')}' already exists")

        # Validate the model before saving
        current_manifest = storage.generate_manifest(user.org_id)
        test_manifest = {
            "semantic_models": current_manifest.get("semantic_models", []) + [model],
            "metrics": current_manifest.get("metrics", []),
        }
        validation = storage.validate_manifest(test_manifest)
        if not validation["valid"]:
            raise HTTPException(status_code=400, detail=f"Validation failed: {'; '.join(validation['errors'])}")

        result = storage.save_semantic_model(user.org_id, model, user_id=user.uid)

        # Record history
        storage.add_history_entry(
            org_id=user.org_id,
            collection_type="semantic_models",
            item_name=model.get("name"),
            action="created",
            user_id=user.uid,
            user_email=user.email or "",
            changes={},
        )

        await _regenerate_manifest(user.org_id)
        return result
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create semantic model: {e}")


@app.put("/api/semantic-layer/models/{name}")
async def update_semantic_model_endpoint(
    name: str,
    updates: dict,
    user: AuthenticatedUser = Depends(require_org_role("owner", "admin")),
):
    """Update an existing semantic model. Requires admin role."""
    try:
        existing = storage.get_semantic_model(user.org_id, name)
        if not existing:
            raise HTTPException(status_code=404, detail=f"Semantic model '{name}' not found")
        # Merge updates with existing, preserving the name
        updated_model = {**existing, **updates, "name": name}

        # Validate the updated model before saving
        current_manifest = storage.generate_manifest(user.org_id)
        # Replace the old model with the updated one
        updated_models = [m for m in current_manifest.get("semantic_models", []) if m.get("name") != name]
        updated_models.append(updated_model)
        test_manifest = {
            "semantic_models": updated_models,
            "metrics": current_manifest.get("metrics", []),
        }
        validation = storage.validate_manifest(test_manifest)
        if not validation["valid"]:
            raise HTTPException(status_code=400, detail=f"Validation failed: {'; '.join(validation['errors'])}")

        result = storage.save_semantic_model(user.org_id, updated_model, user_id=user.uid)

        # Record history with changes
        changes = storage.compute_changes(existing, updated_model)
        if changes:
            storage.add_history_entry(
                org_id=user.org_id,
                collection_type="semantic_models",
                item_name=name,
                action="updated",
                user_id=user.uid,
                user_email=user.email or "",
                changes=changes,
            )

        await _regenerate_manifest(user.org_id)
        return result
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update semantic model: {e}")


@app.delete("/api/semantic-layer/models/{name}")
async def delete_semantic_model_endpoint(
    name: str,
    user: AuthenticatedUser = Depends(require_org_role("owner", "admin")),
):
    """Delete a semantic model. Requires admin role."""
    try:
        success = storage.delete_semantic_model(user.org_id, name)
        if not success:
            raise HTTPException(status_code=404, detail=f"Semantic model '{name}' not found")

        # Record history
        storage.add_history_entry(
            org_id=user.org_id,
            collection_type="semantic_models",
            item_name=name,
            action="deleted",
            user_id=user.uid,
            user_email=user.email or "",
            changes={},
        )

        await _regenerate_manifest(user.org_id)
        return {"status": "ok"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete semantic model: {e}")


@app.get("/api/semantic-layer/metrics")
async def list_metrics_endpoint(user: AuthenticatedUser = Depends(get_current_user)):
    """List all metrics for the organization."""
    try:
        metrics = storage.list_metrics(user.org_id)
        return {"metrics": metrics}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list metrics: {e}")


@app.get("/api/semantic-layer/metrics/{name}")
async def get_metric_endpoint(
    name: str,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Get a specific metric by name."""
    try:
        metric = storage.get_metric(user.org_id, name)
        if not metric:
            raise HTTPException(status_code=404, detail=f"Metric '{name}' not found")
        return metric
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metric: {e}")


@app.post("/api/semantic-layer/metrics")
async def create_metric_endpoint(
    metric: dict,
    user: AuthenticatedUser = Depends(require_org_role("owner", "admin")),
):
    """Create a new metric. Requires admin role."""
    try:
        # Validate the metric before saving
        current_manifest = storage.generate_manifest(user.org_id)
        test_manifest = {
            "semantic_models": current_manifest.get("semantic_models", []),
            "metrics": current_manifest.get("metrics", []) + [metric],
        }
        validation = storage.validate_manifest(test_manifest)
        if not validation["valid"]:
            raise HTTPException(status_code=400, detail=f"Validation failed: {'; '.join(validation['errors'])}")

        result = storage.create_metric(user.org_id, metric, user.uid)

        # Record history
        storage.add_history_entry(
            org_id=user.org_id,
            collection_type="metrics",
            item_name=metric.get("name"),
            action="created",
            user_id=user.uid,
            user_email=user.email or "",
            changes={},
        )

        # Regenerate manifest for MetricFlow
        await _regenerate_manifest(user.org_id)
        return result
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create metric: {e}")


class MetricPreviewRequest(BaseModel):
    """Request body for metric preview."""
    metric: dict
    days: int = 7  # Number of days to query
    limit: int = 10  # Row limit for preview


class MetricPreviewResponse(BaseModel):
    """Response for metric preview."""
    valid: bool
    errors: list[str] = []
    warnings: list[str] = []
    data: list[dict] = []
    columns: list[str] = []
    sql: str | None = None


def _normalize_metric_for_metricflow(metric: dict) -> dict:
    """Normalize a metric definition for MetricFlow compatibility.

    MetricFlow requires `input_measures` to be populated in type_params.
    When metrics are created via UI, only `measure` is provided.
    This function derives `input_measures` from `measure` for simple metrics.
    """
    metric = dict(metric)  # Don't mutate original
    type_params = metric.get("type_params", {})

    if not type_params:
        return metric

    type_params = dict(type_params)
    metric["type_params"] = type_params

    # For simple metrics, derive input_measures from measure
    metric_type = metric.get("type", "").lower()
    if metric_type == "simple" and "measure" in type_params:
        measure = type_params["measure"]
        if "input_measures" not in type_params or not type_params["input_measures"]:
            # Create input_measures from measure
            if isinstance(measure, dict):
                type_params["input_measures"] = [measure]
            elif isinstance(measure, str):
                type_params["input_measures"] = [{"name": measure}]

    return metric


@app.post("/api/semantic-layer/metrics/preview", response_model=MetricPreviewResponse)
async def preview_metric_endpoint(
    request: MetricPreviewRequest,
    user: AuthenticatedUser = Depends(require_org_role("owner", "admin")),
):
    """Preview a metric definition without saving.

    Validates the metric, then executes a sample query to show what data
    the metric would return. Useful for testing metrics before saving.
    """
    # Normalize the metric for MetricFlow compatibility
    metric = _normalize_metric_for_metricflow(request.metric)
    metric_name = metric.get("name")

    if not metric_name:
        return MetricPreviewResponse(
            valid=False,
            errors=["Metric name is required"],
        )

    try:
        # Step 1: Validate the metric against current manifest
        current_manifest = storage.generate_manifest(user.org_id)

        # Check if this is a new metric or editing an existing one
        existing_metrics = current_manifest.get("metrics", [])
        is_edit = any(m.get("name") == metric_name for m in existing_metrics)

        if is_edit:
            # Replace existing metric for validation
            test_metrics = [m for m in existing_metrics if m.get("name") != metric_name]
            test_metrics.append(metric)
        else:
            # Add new metric
            test_metrics = existing_metrics + [metric]

        test_manifest = {
            "semantic_models": current_manifest.get("semantic_models", []),
            "metrics": test_metrics,
            "project_configuration": current_manifest.get("project_configuration", {"time_spines": []}),
        }

        validation = storage.validate_manifest(test_manifest)
        if not validation["valid"]:
            return MetricPreviewResponse(
                valid=False,
                errors=validation["errors"],
                warnings=validation.get("warnings", []),
            )

        # Step 2: Create a temporary MetricFlow engine with the test manifest
        # Get warehouse config to determine SQL dialect
        warehouse_config = storage.get_warehouse_config(user.org_id)
        if not warehouse_config:
            return MetricPreviewResponse(
                valid=True,
                errors=[],
                warnings=["No warehouse configured - cannot execute preview query"],
            )

        warehouse_type = warehouse_config.get("type", "bigquery")

        # Check if time_spines are configured (required by MetricFlow)
        project_config = test_manifest.get("project_configuration", {})
        time_spines = project_config.get("time_spines", [])
        if not time_spines:
            return MetricPreviewResponse(
                valid=False,
                errors=[
                    "No time spine configured. MetricFlow requires a time spine table for time-based queries. "
                    "Please import a dbt semantic manifest that includes project_configuration with time_spines, "
                    "or configure a time spine table in your dbt project's schema.yml."
                ],
            )

        # Load test manifest into MetricFlow
        try:
            pydantic_manifest = load_manifest_from_dict(test_manifest)
            temp_engine = create_engine(pydantic_manifest, warehouse_type=warehouse_type)
        except Exception as e:
            logger.error(f"Failed to create preview engine: {e}")
            return MetricPreviewResponse(
                valid=False,
                errors=[f"Failed to compile metric: {str(e)}"],
            )

        # Step 3: Build and execute a sample query
        time_end = datetime.now()
        time_start = time_end - timedelta(days=request.days)

        mf_request = build_mf_request(
            metrics=[metric_name],
            group_by=None,
            order_by_specs=None,
            limit=request.limit,
            time_start=time_start,
            time_end=time_end,
            where_constraint=None,
        )

        # Generate SQL
        try:
            explain_result = temp_engine.explain(mf_request)
            sql = explain_result.sql_statement.sql
        except Exception as e:
            logger.error(f"Failed to generate SQL for preview: {e}")
            return MetricPreviewResponse(
                valid=False,
                errors=[f"Failed to generate query: {str(e)}"],
            )

        # Step 4: Execute the query
        try:
            org_warehouse = get_org_warehouse()
            client = org_warehouse.get_client(user.org_id)
            data = client.query(sql)
            columns = list(data[0].keys()) if data else []
        except Exception as e:
            logger.warning(f"Preview query execution failed: {e}")
            # Still return valid since the metric compiled - just couldn't run
            return MetricPreviewResponse(
                valid=True,
                errors=[],
                warnings=[f"Query execution failed: {str(e)}"],
                sql=sql,
            )

        return MetricPreviewResponse(
            valid=True,
            errors=[],
            warnings=validation.get("warnings", []),
            data=data,
            columns=columns,
            sql=sql,
        )

    except Exception as e:
        logger.error(f"Preview failed: {e}")
        raise HTTPException(status_code=500, detail=f"Preview failed: {e}")


@app.put("/api/semantic-layer/metrics/{name}")
async def update_metric_endpoint(
    name: str,
    updates: dict,
    user: AuthenticatedUser = Depends(require_org_role("owner", "admin")),
):
    """Update an existing metric. Requires admin role."""
    try:
        # Get existing metric to merge with updates
        existing = storage.get_metric(user.org_id, name)
        if not existing:
            raise HTTPException(status_code=404, detail=f"Metric '{name}' not found")

        # Merge updates with existing
        updated_metric = {**existing, **updates, "name": name}

        # Validate the updated metric before saving
        current_manifest = storage.generate_manifest(user.org_id)
        # Replace the old metric with the updated one
        updated_metrics = [m for m in current_manifest.get("metrics", []) if m.get("name") != name]
        updated_metrics.append(updated_metric)
        test_manifest = {
            "semantic_models": current_manifest.get("semantic_models", []),
            "metrics": updated_metrics,
        }
        validation = storage.validate_manifest(test_manifest)
        if not validation["valid"]:
            raise HTTPException(status_code=400, detail=f"Validation failed: {'; '.join(validation['errors'])}")

        result = storage.update_metric(user.org_id, name, updates, user.uid)
        if not result:
            raise HTTPException(status_code=404, detail=f"Metric '{name}' not found")

        # Record history with changes
        changes = storage.compute_changes(existing, updated_metric)
        if changes:
            storage.add_history_entry(
                org_id=user.org_id,
                collection_type="metrics",
                item_name=name,
                action="updated",
                user_id=user.uid,
                user_email=user.email or "",
                changes=changes,
            )

        # Regenerate manifest for MetricFlow
        await _regenerate_manifest(user.org_id)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update metric: {e}")


@app.delete("/api/semantic-layer/metrics/{name}")
async def delete_metric_endpoint(
    name: str,
    user: AuthenticatedUser = Depends(require_org_role("owner", "admin")),
):
    """Delete a metric. Requires admin role."""
    try:
        success = storage.delete_metric(user.org_id, name)
        if not success:
            raise HTTPException(status_code=404, detail=f"Metric '{name}' not found")

        # Record history
        storage.add_history_entry(
            org_id=user.org_id,
            collection_type="metrics",
            item_name=name,
            action="deleted",
            user_id=user.uid,
            user_email=user.email or "",
            changes={},
        )

        # Regenerate manifest for MetricFlow
        await _regenerate_manifest(user.org_id)
        return {"status": "ok"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete metric: {e}")


# -----------------------------------------------------------------------------
# History Endpoints
# -----------------------------------------------------------------------------


@app.get("/api/semantic-layer/models/{name}/history")
async def get_semantic_model_history_endpoint(
    name: str,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Get change history for a semantic model."""
    try:
        # Verify model exists
        model = storage.get_semantic_model(user.org_id, name)
        if not model:
            raise HTTPException(status_code=404, detail=f"Semantic model '{name}' not found")
        history = storage.get_history(user.org_id, "semantic_models", name)
        return {"history": history}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get history: {e}")


@app.get("/api/semantic-layer/metrics/{name}/history")
async def get_metric_history_endpoint(
    name: str,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Get change history for a metric."""
    try:
        # Verify metric exists
        metric = storage.get_metric(user.org_id, name)
        if not metric:
            raise HTTPException(status_code=404, detail=f"Metric '{name}' not found")
        history = storage.get_history(user.org_id, "metrics", name)
        return {"history": history}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get history: {e}")


async def _regenerate_manifest(org_id: str):
    """Invalidate caches after semantic layer changes.

    Note: Manifest is now generated dynamically from Firestore, so we only
    need to invalidate caches. No GCS save is needed.
    """
    # Invalidate engine cache (forces re-read of manifest from Firestore)
    get_org_warehouse().invalidate(org_id)
    # Invalidate query cache
    cache_coordinator = get_cache_coordinator()
    await cache_coordinator.invalidate_org(org_id)
    logger.info(f"Invalidated caches for org {org_id} after semantic layer change")


# -----------------------------------------------------------------------------
# Export Endpoints
# -----------------------------------------------------------------------------


@app.get("/api/semantic-layer/export")
async def export_yaml_endpoint(user: AuthenticatedUser = Depends(get_current_user)):
    """Export semantic layer to dbt-compatible YAML files.

    Returns a JSON object with {filename: yaml_content} for each file.
    """
    try:
        files = storage.export_to_yaml(user.org_id)
        return {"files": files}
    except Exception as e:
        logger.error(f"Failed to export YAML: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to export: {e}")


@app.get("/api/semantic-layer/export/zip")
async def export_zip_endpoint(user: AuthenticatedUser = Depends(get_current_user)):
    """Export semantic layer to a ZIP file containing dbt-compatible YAML.

    Returns the ZIP file as a downloadable attachment.
    """
    try:
        zip_bytes = storage.export_to_zip(user.org_id)
        return Response(
            content=zip_bytes,
            media_type="application/zip",
            headers={
                "Content-Disposition": "attachment; filename=semantic_layer.zip"
            }
        )
    except Exception as e:
        logger.error(f"Failed to export ZIP: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to export: {e}")


@app.get("/api/context")
async def get_context_endpoint(user: AuthenticatedUser = Depends(get_current_user)):
    """Get business context for an organization."""
    try:
        content = storage.get_business_context(user.org_id)
        return JSONResponse(content={"content": content or ""}, headers=build_no_cache_headers())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load context: {e}")


@app.put("/api/context")
async def save_context_endpoint(
    body: dict,
    user: AuthenticatedUser = Depends(require_org_role("owner", "admin")),
):
    """Save business context for an organization. Requires admin role."""
    content = body.get("content", "")
    try:
        return storage.save_business_context(user.org_id, content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save context: {e}")


@app.get("/api/warehouse")
async def get_warehouse_config_endpoint(
    user: AuthenticatedUser = Depends(require_org_role("owner", "admin")),
):
    """Get warehouse configuration for an organization. Requires admin role."""
    try:
        config = storage.get_warehouse_config(user.org_id)
        data = config if config else {"status": "not_configured"}
        return JSONResponse(content=data, headers=build_no_cache_headers())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load warehouse config: {e}")


@app.put("/api/warehouse")
async def save_warehouse_config_endpoint(
    config: dict,
    user: AuthenticatedUser = Depends(require_org_role("owner", "admin")),
):
    """Save warehouse configuration for an organization. Requires admin role."""
    try:
        result = storage.save_warehouse_config(user.org_id, config)
        # Invalidate cached client for this org
        get_org_warehouse().invalidate(user.org_id)
        # Invalidate query cache for this org (warehouse change affects queries)
        cache_coordinator = get_cache_coordinator()
        await cache_coordinator.invalidate_org(user.org_id)
        logger.info(f"Invalidated cache for org {user.org_id} after warehouse config update")
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save warehouse config: {e}")


@app.delete("/api/warehouse")
async def delete_warehouse_config_endpoint(
    user: AuthenticatedUser = Depends(require_org_role("owner")),
):
    """Delete warehouse configuration for an organization. Requires owner role."""
    try:
        result = storage.delete_warehouse_config(user.org_id)
        # Invalidate cached client for this org
        get_org_warehouse().invalidate(user.org_id)
        # Invalidate query cache for this org
        cache_coordinator = get_cache_coordinator()
        await cache_coordinator.invalidate_org(user.org_id)
        logger.info(f"Invalidated cache for org {user.org_id} after warehouse config delete")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete warehouse config: {e}")


@app.post("/api/warehouse/test")
async def test_warehouse_connection_endpoint(
    config: dict,
    user: AuthenticatedUser = Depends(require_org_role("owner", "admin")),
):
    """Test warehouse connection without saving. Requires admin role."""
    from google.cloud import bigquery
    from google.oauth2 import service_account

    warehouse_type = config.get("type")
    if not warehouse_type:
        raise HTTPException(status_code=400, detail="Missing warehouse type")

    try:
        if warehouse_type == "bigquery":
            bq_config = config.get("bigquery", {})
            project_id = bq_config.get("project_id")
            credentials_json = bq_config.get("credentials")

            if not project_id:
                raise HTTPException(status_code=400, detail="Missing project_id")

            # Create BigQuery client with provided credentials
            if credentials_json:
                credentials = service_account.Credentials.from_service_account_info(
                    credentials_json,
                    scopes=["https://www.googleapis.com/auth/bigquery.readonly"],
                )
                client = bigquery.Client(project=project_id, credentials=credentials)
            else:
                # Use application default credentials
                client = bigquery.Client(project=project_id)

            # Test by listing datasets (limited to 5)
            datasets = list(client.list_datasets(max_results=5))
            dataset_names = [ds.dataset_id for ds in datasets]

            return {
                "status": "success",
                "message": f"Connected to {project_id}",
                "datasets": dataset_names,
            }

        elif warehouse_type == "duckdb":
            import tempfile
            import os
            from google.cloud import storage as gcs_storage
            import duckdb

            duckdb_config = config.get("duckdb", {})
            path = duckdb_config.get("path")
            token = duckdb_config.get("token")
            if not path:
                raise HTTPException(
                    status_code=400, detail="DuckDB requires path"
                )

            temp_file = None
            actual_path = path
            conn = None

            try:
                if path.startswith("md:"):
                    # MotherDuck connection
                    if token:
                        # Build connection string with token
                        if "?" in path:
                            actual_path = f"{path}&motherduck_token={token}"
                        else:
                            actual_path = f"{path}?motherduck_token={token}"
                    # If no token provided, duckdb will use MOTHERDUCK_TOKEN env var
                    conn = duckdb.connect(actual_path)
                    # List databases for MotherDuck
                    result = conn.execute("SHOW DATABASES")
                    databases = [row[0] for row in result.fetchall()]
                    conn.close()
                    return {
                        "status": "success",
                        "message": "Connected to MotherDuck",
                        "datasets": databases,
                    }

                elif path.startswith("gs://"):
                    # Download from GCS to temp file
                    path_without_prefix = path[5:]  # Remove "gs://"
                    parts = path_without_prefix.split("/", 1)
                    if len(parts) != 2:
                        raise ValueError(f"Invalid GCS path: {path}")

                    bucket_name, blob_name = parts

                    # Create temp file
                    fd, temp_file = tempfile.mkstemp(suffix=".duckdb")
                    os.close(fd)

                    # Download from GCS
                    gcs_client = gcs_storage.Client()
                    bucket = gcs_client.bucket(bucket_name)
                    blob = bucket.blob(blob_name)

                    if not blob.exists():
                        raise ValueError(f"File not found in GCS: {path}")

                    blob.download_to_filename(temp_file)
                    actual_path = temp_file

                else:
                    # Local file path
                    if not os.path.exists(path):
                        raise ValueError(f"DuckDB file not found: {path}")

                # Connect to local/GCS DuckDB and list tables
                conn = duckdb.connect(actual_path, read_only=True)
                result = conn.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'main' LIMIT 10")
                tables = [row[0] for row in result.fetchall()]
                conn.close()

                return {
                    "status": "success",
                    "message": f"Connected to DuckDB at {path}",
                    "datasets": tables,
                }
            finally:
                # Clean up connection
                if conn:
                    try:
                        conn.close()
                    except Exception:
                        pass
                # Clean up temp file
                if temp_file and os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                    except OSError:
                        pass

        else:
            raise HTTPException(
                status_code=400, detail=f"Unknown warehouse type: {warehouse_type}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Warehouse connection test failed: {e}")
        return {
            "status": "error",
            "message": str(e),
        }


@app.get("/api/dashboards")
async def list_dashboards_endpoint(user: AuthenticatedUser = Depends(get_current_user)):
    """List all dashboards visible to user, split into personal and team sections."""
    try:
        data = storage.list_dashboards(user.org_id, user.uid)
        return JSONResponse(content=data, headers=build_no_cache_headers())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list dashboards: {e}")


@app.get("/api/dashboards/{dashboard_id}")
async def get_dashboard_endpoint(
    dashboard_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Get a specific dashboard by ID."""
    try:
        dashboard = storage.get_dashboard(user.org_id, dashboard_id, user.uid)
        if not dashboard:
            raise HTTPException(status_code=404, detail="Dashboard not found")
        return JSONResponse(content=dashboard, headers=build_no_cache_headers())
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load dashboard: {e}")


@app.post("/api/dashboards")
async def create_dashboard_endpoint(
    dashboard: dict,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Create a new dashboard owned by the current user."""
    try:
        return storage.create_dashboard(user.org_id, user.uid, dashboard)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create dashboard: {e}")


@app.put("/api/dashboards/{dashboard_id}")
async def update_dashboard_endpoint(
    dashboard_id: str,
    updates: dict,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Update a dashboard. Only owner can update.

    Supports optimistic locking: pass expected_version in updates to detect conflicts.
    If version mismatch occurs, returns 409 Conflict with current/expected versions.
    """
    from services.dashboards import ConflictError

    try:
        # Extract expected_version if provided (for optimistic locking)
        expected_version = updates.pop("expected_version", None)

        result = storage.update_dashboard(
            user.org_id, dashboard_id, user.uid, updates, expected_version
        )
        if not result:
            raise HTTPException(status_code=403, detail="Not authorized to update this dashboard")
        return result
    except ConflictError as e:
        # Return a specific conflict response for frontend to handle
        return JSONResponse(
            status_code=409,
            content={
                "error": "conflict",
                "detail": str(e),
                "current_version": e.current_version,
                "expected_version": e.expected_version,
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update dashboard: {e}")


@app.delete("/api/dashboards/{dashboard_id}")
async def delete_dashboard_endpoint(
    dashboard_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Delete a dashboard. Only owner can delete."""
    try:
        success = storage.delete_dashboard(user.org_id, dashboard_id, user.uid)
        if not success:
            raise HTTPException(status_code=403, detail="Not authorized to delete this dashboard")
        return {"status": "ok"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete dashboard: {e}")


class DashboardOrderUpdate(BaseModel):
    personal_order: list[str] | None = None
    team_order: list[str] | None = None


@app.put("/api/dashboards/order")
async def update_dashboard_order_endpoint(
    body: DashboardOrderUpdate,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Update user's dashboard order preferences."""
    try:
        return storage.update_dashboard_order(
            user.org_id, user.uid, body.personal_order, body.team_order
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update order: {e}")


def build_mf_request(
    metrics: list[str],
    group_by: list[str] | None,
    order_by_specs: list[str] | None,
    limit: int | None,
    time_start: datetime | None,
    time_end: datetime | None,
    where_constraint: str | None,
) -> MetricFlowQueryRequest:
    """Build a MetricFlowQueryRequest with the given parameters."""
    return MetricFlowQueryRequest(
        request_id=MetricFlowRequestId(f"metricly__{random_id()}"),
        saved_query_name=None,
        metric_names=metrics,
        metrics=None,
        group_by_names=group_by if group_by else None,
        group_by=None,
        limit=limit,
        time_constraint_start=time_start,
        time_constraint_end=time_end,
        where_constraints=[where_constraint] if where_constraint else None,
        order_by_names=order_by_specs if order_by_specs else None,
        order_by=None,
        min_max_only=False,
        apply_group_by=True,
        sql_optimization_level=SqlOptimizationLevel.O4,
        dataflow_plan_optimizations=frozenset(),
        query_type=MetricFlowQueryType.METRIC,
        order_output_columns_by_input_order=False,
    )


def execute_query(
    mf_request: MetricFlowQueryRequest,
    engine: MetricFlowEngine,
    client: QueryClient,
) -> tuple[list[dict], list[str]]:
    """Generate SQL via MetricFlow and execute via query client.

    Returns (data, columns) where data is list of row dicts.
    """
    # Generate SQL
    explain_result = engine.explain(mf_request)
    sql = explain_result.sql_statement.sql

    # Execute via query client (BigQuery or DuckDB)
    data = client.query(sql)

    # Extract column names from first row (if any)
    columns = list(data[0].keys()) if data else []

    return data, columns


@app.post("/query", response_model=QueryResponse)
async def query_metrics(
    request: QueryRequest,
    response: Response,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Execute a MetricFlow query and return results."""
    # Get org-specific engine and client
    try:
        org_warehouse = get_org_warehouse()
        engine, _ = org_warehouse.get_engine(user.org_id)
        client = org_warehouse.get_client(user.org_id)
    except ValueError as e:
        # Add no-cache headers on error
        for key, value in build_no_cache_headers().items():
            response.headers[key] = value
        raise HTTPException(status_code=503, detail=str(e))

    # Get cache coordinator and warehouse info for freshness checking
    cache_coordinator = get_cache_coordinator()
    warehouse_info = org_warehouse.get_warehouse_info(user.org_id) or {}

    # Check cache first
    cached = await get_cached_response(
        coordinator=cache_coordinator,
        org_id=user.org_id,
        metrics=request.metrics,
        dimensions=request.dimensions,
        grain=request.grain,
        start_date=request.start_date,
        end_date=request.end_date,
        filters=request.filters,
        comparison=request.comparison,
        order_by=request.order_by,
        limit=request.limit,
        warehouse_type=warehouse_info.get("warehouse_type"),
        client=warehouse_info.get("client"),
        project_id=warehouse_info.get("project_id"),
        dataset_ids=warehouse_info.get("dataset_ids"),
        db_path=warehouse_info.get("db_path"),
    )

    if cached:
        logger.info(f"Cache HIT for query: metrics={request.metrics}")
        # Add CDN headers and cache status
        has_comparison = request.comparison and request.comparison != "none"
        for key, value in build_cdn_headers(
            has_comparison=has_comparison,
            end_date=request.end_date,
        ).items():
            response.headers[key] = value
        response.headers["X-Cache"] = "HIT"

        return QueryResponse(
            data=cached["data"],
            columns=cached["columns"],
            comparison_data=cached.get("comparison_data"),
            comparison_range=cached.get("comparison_range"),
        )

    # Build group_by list
    group_by = list(request.dimensions) if request.dimensions else []

    # Add time grain if specified
    if request.grain:
        grain_dim = f"metric_time__{request.grain}"
        if grain_dim not in group_by:
            group_by.append(grain_dim)

    # Build order_by list
    order_by_specs = []
    if request.order_by:
        # MetricFlow uses -column for descending
        order = request.order_by
        if order.endswith(" desc"):
            order_by_specs.append("-" + order.replace(" desc", ""))
        elif order.endswith(" asc"):
            order_by_specs.append(order.replace(" asc", ""))
        else:
            order_by_specs.append(order)
    elif group_by and any("metric_time" in g for g in group_by):
        # Default: order by time
        time_dim = next((g for g in group_by if "metric_time" in g), None)
        if time_dim:
            order_by_specs.append(time_dim)

    # Build where clause from filters
    where_constraint = None
    if request.filters:
        where_clauses = []
        for f in request.filters:
            dim = f.get("dimension", "")
            op = f.get("operator", "equals")
            val = f.get("value")

            if op == "equals":
                where_clauses.append(f"{{{{ Dimension('{dim}') }}}} = '{val}'")
            elif op == "not_equals":
                where_clauses.append(f"{{{{ Dimension('{dim}') }}}} != '{val}'")
            elif op == "in":
                vals = ", ".join([f"'{v}'" for v in val])
                where_clauses.append(f"{{{{ Dimension('{dim}') }}}} IN ({vals})")
            elif op == "gte":
                where_clauses.append(f"{{{{ Dimension('{dim}') }}}} >= '{val}'")
            elif op == "lte":
                where_clauses.append(f"{{{{ Dimension('{dim}') }}}} <= '{val}'")
            elif op == "gt":
                where_clauses.append(f"{{{{ Dimension('{dim}') }}}} > '{val}'")
            elif op == "lt":
                where_clauses.append(f"{{{{ Dimension('{dim}') }}}} < '{val}'")

        if where_clauses:
            where_constraint = " AND ".join(where_clauses)

    try:
        import time
        query_start = time.time()

        # Parse date constraints
        time_start = datetime.fromisoformat(request.start_date) if request.start_date else None
        time_end = datetime.fromisoformat(request.end_date) if request.end_date else None

        print(f"\n{'='*60}")
        print(f"[QUERY START] metrics={request.metrics}")
        print(f"  group_by={group_by or None}")
        print(f"  filters={request.filters or None}")
        print(f"  where_constraint={where_constraint}")
        print(f"  dates={request.start_date} to {request.end_date}")
        print(f"  limit={request.limit}")

        # Build main query
        mf_request = build_mf_request(
            metrics=request.metrics,
            group_by=group_by if group_by else None,
            order_by_specs=order_by_specs if order_by_specs else None,
            limit=request.limit,
            time_start=time_start,
            time_end=time_end,
            where_constraint=where_constraint,
        )

        # Execute query in thread pool (query client is blocking)
        exec_start = time.time()
        loop = asyncio.get_event_loop()
        data, columns = await loop.run_in_executor(
            query_executor, execute_query, mf_request, engine, client
        )
        exec_time = time.time() - exec_start

        print(f"[QUERY RESULT] rows={len(data)}, columns={columns}")
        print(f"  execution_time={exec_time:.2f}s")
        if data:
            print(f"  sample_row={data[0]}")

        # Handle comparison query if requested
        comparison_data = None
        comparison_range = None

        if request.comparison and request.comparison != "none":
            comp_start, comp_end = compute_comparison_dates(
                request.start_date, request.end_date, request.comparison
            )

            if comp_start and comp_end:
                print(f"Comparison query: {request.comparison}, dates={comp_start.date()} to {comp_end.date()}")

                comp_request = build_mf_request(
                    metrics=request.metrics,
                    group_by=group_by if group_by else None,
                    order_by_specs=order_by_specs if order_by_specs else None,
                    limit=request.limit,
                    time_start=comp_start,
                    time_end=comp_end,
                    where_constraint=where_constraint,
                )

                # Comparison query can fail gracefully (e.g., no data for that period)
                try:
                    comparison_data, _ = await loop.run_in_executor(
                        query_executor, execute_query, comp_request, engine, client
                    )
                    comparison_range = {
                        "start_date": comp_start.date().isoformat(),
                        "end_date": comp_end.date().isoformat(),
                    }
                except Exception as comp_error:
                    print(f"[COMPARISON ERROR] {type(comp_error).__name__}: {comp_error}")
                    print("  Continuing without comparison data")
                    # Leave comparison_data as None - main query still succeeds

        total_time = time.time() - query_start
        print(f"[QUERY COMPLETE] total_time={total_time:.2f}s, returning {len(data)} rows")
        print(f"{'='*60}\n")

        # Cache the result
        await cache_response(
            coordinator=cache_coordinator,
            org_id=user.org_id,
            metrics=request.metrics,
            dimensions=request.dimensions,
            grain=request.grain,
            start_date=request.start_date,
            end_date=request.end_date,
            data=data,
            columns=columns,
            comparison_data=comparison_data,
            comparison_range=comparison_range,
            filters=request.filters,
            comparison=request.comparison,
            order_by=request.order_by,
            limit=request.limit,
        )

        # Add CDN headers and cache status
        has_comparison = request.comparison and request.comparison != "none"
        for key, value in build_cdn_headers(
            has_comparison=has_comparison,
            end_date=request.end_date,
        ).items():
            response.headers[key] = value
        response.headers["X-Cache"] = "MISS"

        return QueryResponse(
            data=data,
            columns=columns,
            comparison_data=comparison_data,
            comparison_range=comparison_range,
        )

    except Exception as e:
        print(f"\n[QUERY ERROR] {type(e).__name__}: {e}")
        print(f"  metrics={request.metrics}")
        print(f"  group_by={group_by or None}")
        print(f"  filters={request.filters}")
        print(f"{'='*60}\n")
        # Add no-cache headers on error
        for key, value in build_no_cache_headers().items():
            response.headers[key] = value
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Chat Endpoint
# ============================================================================

@app.post("/api/chat")
async def chat_endpoint(
    request: ChatRequest,
    req: Request,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Stream chat responses with status updates as tools are called."""
    from pydantic_ai.messages import ModelRequest, ModelResponse, UserPromptPart, TextPart
    from chat import validate_dashboard_update, fix_dashboard_immutable_fields

    # Get org-specific engine, manifest, and client
    try:
        org_warehouse = get_org_warehouse()
        engine, manifest = org_warehouse.get_engine(user.org_id)
        client = org_warehouse.get_client(user.org_id)
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))

    # Build org-specific LLM context
    llm_context = build_llm_context(manifest, user.org_id)

    # Load user preferences for personalization
    from services.context import get_user_preferences
    try:
        user_prefs = await get_user_preferences(user.uid)
        user_prefs_dict = user_prefs.model_dump(exclude_none=True) if user_prefs else None
    except Exception:
        user_prefs_dict = None  # Don't block chat if preferences fail to load

    # Queue for streaming status updates (cleaner than polling a list)
    queue: asyncio.Queue[dict] = asyncio.Queue(maxsize=100)

    async def emit_status(message: str) -> None:
        """Called by tools to emit status updates via queue."""
        await queue.put({"type": "status", "message": message})

    # Create dependencies for the agent with status callback
    deps = ChatDependencies(
        mf_engine=engine,
        bq_client=client,
        semantic_manifest=manifest,
        tenant_context=llm_context,
        query_executor=query_executor,
        org_id=user.org_id,
        user_id=user.uid,
        user_email=user.email or "",
        user_role=user.org_role,
        widget_context=request.widget_context.widget if request.widget_context else None,
        widget_dashboard_controls=request.widget_context.dashboard_controls if request.widget_context else None,
        widget_rendered_data=request.widget_context.rendered_data if request.widget_context else None,
        dashboard_context=request.dashboard_context,
        full_dashboard=request.full_dashboard,
        status_callback=emit_status,
        user_preferences=user_prefs_dict,
    )

    # Convert message history to pydantic-ai ModelMessage format
    message_history = []
    if request.history:
        for msg in request.history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "user":
                message_history.append(ModelRequest(parts=[UserPromptPart(content=content)]))
            else:
                message_history.append(ModelResponse(parts=[TextPart(content=content)]))

    async def run_agent():
        """Run the agent and push result/error to queue."""
        MAX_RETRIES = 2
        try:
            # Initial status - shown while LLM processes the question
            await queue.put({"type": "status", "message": "Analyzing your question..."})

            chat_agent = get_agent()
            current_message = request.message
            current_history = message_history if message_history else None

            for attempt in range(MAX_RETRIES + 1):
                print(f"[CHAT] Attempt {attempt + 1}/{MAX_RETRIES + 1}")
                result = await chat_agent.run(
                    current_message,
                    deps=deps,
                    message_history=current_history,
                )

                # Validate dashboard_update if present
                output = result.output.model_dump(exclude_none=True)
                if output.get('dashboard_update') and request.full_dashboard:

                    # Log both dashboards for debugging
                    import os
                    debug_dir = "/tmp/metricly-debug"
                    os.makedirs(debug_dir, exist_ok=True)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    with open(f"{debug_dir}/dashboard_original_{timestamp}.json", "w") as f:
                        json.dump(request.full_dashboard, f, indent=2, default=str)
                    with open(f"{debug_dir}/dashboard_updated_{timestamp}.json", "w") as f:
                        json.dump(output['dashboard_update'], f, indent=2, default=str)
                    print(f"[CHAT] Logged dashboards to {debug_dir}/dashboard_*_{timestamp}.json")

                    print(f"[CHAT] Got dashboard_update, fixing immutable fields...")
                    # Fix immutable fields (id, owner, created_at, created_by, visibility, version)
                    output['dashboard_update'] = fix_dashboard_immutable_fields(
                        output['dashboard_update'],
                        request.full_dashboard
                    )
                    print(f"[CHAT] Validating dashboard_update...")
                    validation_errors = validate_dashboard_update(
                        output['dashboard_update'],
                        request.full_dashboard
                    )
                    if validation_errors:
                        print(f"[CHAT] Validation errors: {validation_errors}")
                        if attempt < MAX_RETRIES:
                            # Retry with error feedback
                            await queue.put({
                                "type": "status",
                                "message": f"Fixing dashboard structure (attempt {attempt + 2}/{MAX_RETRIES + 1})..."
                            })
                            error_feedback = (
                                f"Your dashboard_update response failed validation with these errors:\n"
                                f"{chr(10).join('- ' + e for e in validation_errors)}\n\n"
                                f"Please fix these issues and return the corrected dashboard_update. "
                                f"Remember to copy ALL required fields from the original dashboard."
                            )
                            # Build history with previous attempt
                            from pydantic_ai.messages import ModelRequest, ModelResponse, UserPromptPart, TextPart
                            if current_history is None:
                                current_history = []
                            current_history.append(ModelRequest(parts=[UserPromptPart(content=current_message)]))
                            current_history.append(ModelResponse(parts=[TextPart(content=output.get('answer', ''))]))
                            current_message = error_feedback
                            continue
                        else:
                            # Max retries reached, return error
                            print(f"[CHAT] Max retries reached, returning error")
                            await queue.put({
                                "type": "error",
                                "message": f"Failed to generate valid dashboard after {MAX_RETRIES + 1} attempts: {', '.join(validation_errors[:3])}"
                            })
                            return
                    else:
                        print(f"[CHAT] Validation passed!")

                # Validation passed or no dashboard_update
                break

            # Final status before returning result
            await queue.put({"type": "status", "message": "Preparing response..."})
            # Return the fixed output (with corrected immutable fields)
            await queue.put({"type": "result", "data": output})
        except Exception as e:
            print(f"[CHAT] Exception: {e}")
            await queue.put({"type": "error", "message": str(e)})

    async def generate():
        """Stream SSE events from queue."""
        task = asyncio.create_task(run_agent())
        try:
            while True:
                # Check for client disconnect
                if await req.is_disconnected():
                    task.cancel()
                    break
                try:
                    # Wait for next item with timeout (sends keepalive on timeout)
                    item = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield f"data: {json.dumps(item)}\n\n"
                    # Exit loop on terminal events
                    if item["type"] in {"result", "error"}:
                        break
                except asyncio.TimeoutError:
                    # Send keepalive comment to prevent connection timeout
                    yield ": ping\n\n"
        finally:
            if not task.done():
                task.cancel()
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
            "Transfer-Encoding": "chunked",
        },
    )


@app.post("/api/chat/sync", response_model=ChatResponse)
async def chat_sync_endpoint(
    request: ChatRequest,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Non-streaming chat endpoint for simpler testing."""
    from pydantic_ai.messages import ModelRequest, ModelResponse, UserPromptPart, TextPart

    # Get org-specific engine, manifest, and client
    try:
        org_warehouse = get_org_warehouse()
        engine, manifest = org_warehouse.get_engine(user.org_id)
        client = org_warehouse.get_client(user.org_id)
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))

    # Build org-specific LLM context
    llm_context = build_llm_context(manifest, user.org_id)

    # Load user preferences for personalization
    from services.context import get_user_preferences
    try:
        user_prefs = await get_user_preferences(user.uid)
        user_prefs_dict = user_prefs.model_dump(exclude_none=True) if user_prefs else None
    except Exception:
        user_prefs_dict = None  # Don't block chat if preferences fail to load

    # No-op status callback for sync endpoint (status not streamed, but keeps tool behavior consistent)
    async def noop_status(message: str) -> None:
        pass

    deps = ChatDependencies(
        mf_engine=engine,
        bq_client=client,
        semantic_manifest=manifest,
        tenant_context=llm_context,
        query_executor=query_executor,
        org_id=user.org_id,
        user_id=user.uid,
        user_email=user.email or "",
        user_role=user.org_role,
        widget_context=request.widget_context.widget if request.widget_context else None,
        widget_dashboard_controls=request.widget_context.dashboard_controls if request.widget_context else None,
        widget_rendered_data=request.widget_context.rendered_data if request.widget_context else None,
        dashboard_context=request.dashboard_context,
        status_callback=noop_status,
        user_preferences=user_prefs_dict,
    )

    # Convert message history to pydantic-ai ModelMessage format
    message_history = []
    if request.history:
        for msg in request.history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "user":
                message_history.append(ModelRequest(parts=[UserPromptPart(content=content)]))
            else:
                message_history.append(ModelResponse(parts=[TextPart(content=content)]))

    try:
        chat_agent = get_agent()
        result = await chat_agent.run(
            request.message,
            deps=deps,
            message_history=message_history if message_history else None,
        )
        return result.output
    except Exception as e:
        print(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Render Endpoints
# ============================================================================


class DashboardRenderRequest(BaseModel):
    """Request body for dashboard rendering."""

    format: Literal["pdf", "png"] = "pdf"
    page_id: str | None = None  # Optional: render specific page only
    width: int = 1200
    height: int = 800


class WidgetRenderRequest(BaseModel):
    """Request body for widget rendering."""

    width: int = 600
    height: int = 400


class TokenValidationResponse(BaseModel):
    """Response for token validation."""

    valid: bool
    org_id: str | None = None
    # Include resource data so render pages don't need to make additional authenticated calls
    dashboard: dict | None = None  # Full dashboard data for dashboard renders
    widget: dict | None = None  # Single widget data for widget renders
    controls: dict | None = None  # Dashboard controls (for widget renders)


@app.post("/api/render/dashboard/{dashboard_id}")
async def render_dashboard_endpoint(
    dashboard_id: str,
    request: DashboardRenderRequest,
    user: AuthenticatedUser = Depends(get_current_user_flexible),
):
    """Render a dashboard to PDF or PNG.

    Supports both Firebase ID tokens (web) and Google OAuth tokens (CLI).
    Returns binary file data.
    """
    # Verify user has access to the dashboard
    try:
        dashboard = storage.get_dashboard(user.org_id, dashboard_id, user.uid)
        if not dashboard:
            raise HTTPException(status_code=404, detail="Dashboard not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load dashboard: {e}")

    # Render the dashboard in a thread pool to avoid blocking the event loop
    # This is critical: Chrome loads pages from the same server, which would deadlock
    # if the render call blocked the main event loop
    try:
        result = await asyncio.to_thread(
            render_dashboard,
            org_id=user.org_id,
            dashboard_id=dashboard_id,
            page_id=request.page_id,
            format=request.format,
            width=request.width,
            height=request.height,
        )

        media_type = "application/pdf" if request.format == "pdf" else "image/png"
        # Include page title in filename if rendering specific page
        base_title = dashboard.get('title', 'dashboard')
        if request.page_id:
            page_title = next(
                (p.get('title', request.page_id) for p in dashboard.get('pages', []) if p.get('id') == request.page_id),
                request.page_id
            )
            filename = f"{base_title} - {page_title}.{request.format}"
        else:
            filename = f"{base_title}.{request.format}"

        return Response(
            content=result.data,
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
            },
        )
    except ChromeConnectionError as e:
        logger.error(f"Chrome connection error: {e}")
        raise HTTPException(
            status_code=503,
            detail="Rendering service unavailable. Please try again later.",
        )
    except RenderTimeoutError as e:
        logger.error(f"Render timeout: {e}")
        raise HTTPException(
            status_code=504,
            detail="Rendering timed out. The dashboard may be too complex.",
        )
    except RenderError as e:
        logger.error(f"Render error: {e}")
        raise HTTPException(status_code=500, detail=f"Rendering failed: {e}")


@app.post("/api/render/widget/{dashboard_id}/{widget_id}")
async def render_widget_endpoint(
    dashboard_id: str,
    widget_id: str,
    request: WidgetRenderRequest,
    user: AuthenticatedUser = Depends(get_current_user_flexible),
):
    """Render a single widget to PNG.

    Supports both Firebase ID tokens (web) and Google OAuth tokens (CLI).
    Returns PNG image.
    """
    # Verify user has access to the dashboard
    try:
        dashboard = storage.get_dashboard(user.org_id, dashboard_id, user.uid)
        if not dashboard:
            raise HTTPException(status_code=404, detail="Dashboard not found")

        # Verify widget exists in dashboard
        widget_found = False
        for page in dashboard.get("pages", []):
            for section in page.get("sections", []):
                for widget in section.get("widgets", []):
                    if widget.get("id") == widget_id:
                        widget_found = True
                        break
                if widget_found:
                    break
            if widget_found:
                break

        if not widget_found:
            raise HTTPException(status_code=404, detail="Widget not found")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load dashboard: {e}")

    # Render the widget in a thread pool to avoid blocking the event loop
    # This is critical: Chrome loads pages from the same server, which would deadlock
    # if the render call blocked the main event loop
    try:
        result = await asyncio.to_thread(
            render_widget,
            org_id=user.org_id,
            dashboard_id=dashboard_id,
            widget_id=widget_id,
            width=request.width,
            height=request.height,
        )

        return Response(
            content=result.data,
            media_type="image/png",
            headers={
                "Content-Disposition": f'attachment; filename="widget-{widget_id}.png"',
            },
        )
    except ChromeConnectionError as e:
        logger.error(f"Chrome connection error: {e}")
        raise HTTPException(
            status_code=503,
            detail="Rendering service unavailable. Please try again later.",
        )
    except RenderTimeoutError as e:
        logger.error(f"Render timeout: {e}")
        raise HTTPException(
            status_code=504,
            detail="Rendering timed out.",
        )
    except RenderError as e:
        logger.error(f"Render error: {e}")
        raise HTTPException(status_code=500, detail=f"Rendering failed: {e}")


@app.get("/api/render/token/validate", response_model=TokenValidationResponse)
async def validate_render_token_endpoint(
    token: str,
    resource_type: Literal["dashboard", "widget"],
    resource_id: str,
):
    """Validate a one-time render token and return resource data.

    Used by frontend render routes to validate access and get data for rendering.
    This endpoint is unauthenticated - the token itself provides auth.

    The endpoint returns the full dashboard/widget data so render pages
    don't need to make additional authenticated API calls.

    Returns:
        TokenValidationResponse with valid=true, org_id, and resource data if valid,
        or 401 error if invalid/expired.
    """
    logger.info(f"Token validation request: type={resource_type}, id={resource_id}, token={token[:20]}...")
    org_id = validate_render_token(token, resource_type, resource_id)
    logger.info(f"Token validation result: org_id={org_id}")

    if not org_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    # Fetch the resource data (using internal function to bypass user access checks,
    # since the render token already grants access to the specific resource)
    try:
        if resource_type == "dashboard":
            dashboard_data = storage.get_dashboard_internal(org_id, resource_id)
            if not dashboard_data:
                raise HTTPException(status_code=404, detail="Dashboard not found")
            return TokenValidationResponse(
                valid=True,
                org_id=org_id,
                dashboard=dashboard_data,
            )
        else:  # widget
            # resource_id is "dashboard_id/widget_id"
            parts = resource_id.split("/")
            if len(parts) != 2:
                raise HTTPException(status_code=400, detail="Invalid widget resource_id format")
            dashboard_id, widget_id = parts

            dashboard_data = storage.get_dashboard_internal(org_id, dashboard_id)
            if not dashboard_data:
                raise HTTPException(status_code=404, detail="Dashboard not found")

            # Find the widget in the dashboard
            widget_data = None
            for page in dashboard_data.get("pages", []):
                for section in page.get("sections", []):
                    for widget in section.get("widgets", []):
                        if widget.get("id") == widget_id:
                            widget_data = widget
                            break
                    if widget_data:
                        break
                if widget_data:
                    break

            if not widget_data:
                raise HTTPException(status_code=404, detail="Widget not found in dashboard")

            return TokenValidationResponse(
                valid=True,
                org_id=org_id,
                widget=widget_data,
                controls=dashboard_data.get("controls"),
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching resource for render: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch resource data")


@app.post("/api/render/query")
async def render_query_endpoint(
    request: QueryRequest,
    response: Response,
    token: str = Query(..., description="Render token for authentication"),
):
    """Execute a MetricFlow query using a render token for authentication.

    This endpoint is used by frontend render pages to query metric data
    without requiring Firebase authentication. The render token must have
    been previously validated via /api/render/token/validate.
    """
    from services.render import validate_render_token_for_query

    try:
        # Validate token and get org_id
        org_id = validate_render_token_for_query(token)
        if not org_id:
            raise HTTPException(status_code=401, detail="Invalid or expired render token")

        logger.info(f"Render query: token validated for org {org_id}")

        # Get warehouse
        org_warehouse = get_org_warehouse()
        engine, _ = org_warehouse.get_engine(org_id)
        client = org_warehouse.get_client(org_id)
        logger.info(f"Render query: got engine and client")

        # Build group_by from dimensions and grain
        group_by = []
        if request.dimensions:
            group_by.extend(request.dimensions)
        if request.grain:
            group_by.append(f"metric_time__{request.grain}")

        # Parse dates
        time_start = datetime.fromisoformat(request.start_date) if request.start_date else None
        time_end = datetime.fromisoformat(request.end_date) if request.end_date else None

        # Build the MetricFlow request
        mf_request = build_mf_request(
            metrics=request.metrics,
            group_by=group_by if group_by else None,
            order_by_specs=[request.order_by] if request.order_by else None,
            limit=request.limit,
            time_start=time_start,
            time_end=time_end,
            where_constraint=None,
        )

        # Execute query
        data, columns = execute_query(mf_request, engine, client)
        logger.info(f"Render query: executed, got {len(data)} rows")

        # Build response
        result = QueryResponse(columns=columns, data=data)

        # No-cache headers for render queries
        for key, value in build_no_cache_headers().items():
            response.headers[key] = value

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Render query endpoint failed: {e}")
        raise HTTPException(status_code=500, detail=f"Query failed: {e}")


# ============================================================================
# Schedule Execution Endpoint (Internal - Called by Cloud Function)
# ============================================================================


class ScheduleExecuteResponse(BaseModel):
    """Response from schedule execution."""

    status: Literal["success", "failed"]
    schedule_id: str
    report_type: str
    error: str | None = None


@app.post("/api/schedules/{schedule_id}/execute", response_model=ScheduleExecuteResponse)
async def execute_schedule_endpoint(
    schedule_id: str,
    x_org_id: str = Header(..., alias="X-Org-Id"),
    x_internal_secret: str = Header(..., alias="X-Internal-Secret"),
):
    """Execute a scheduled report (internal endpoint for Cloud Function).

    This endpoint is called by the Cloud Function scheduler to execute
    scheduled reports. It renders dashboards or exports queries, then
    sends the results via email.

    Security:
        Requires X-Internal-Secret header matching the configured secret.
        This is NOT a user-facing endpoint.

    Args:
        schedule_id: The schedule to execute
        x_org_id: Organization ID (from Cloud Function)
        x_internal_secret: Internal secret for authentication

    Returns:
        ScheduleExecuteResponse with execution status
    """
    from settings import get_settings
    from services.schedules import (
        Schedule,
        DashboardReport,
        QueryReport,
        update_run_status,
    )
    from services.export import export_query_data
    from services.queries import QueryParams

    settings = get_settings()

    # Verify internal secret
    if not settings.internal_secret:
        logger.error("INTERNAL_SECRET not configured")
        raise HTTPException(status_code=500, detail="Server misconfigured")

    if x_internal_secret != settings.internal_secret:
        logger.warning(f"Invalid internal secret for schedule execution: {schedule_id}")
        raise HTTPException(status_code=401, detail="Unauthorized")

    logger.info(f"Executing schedule {schedule_id} for org {x_org_id}")

    try:
        # Load schedule from Firestore
        db = storage.get_firestore_client()
        schedule_ref = db.collection("organizations").document(x_org_id).collection("schedules").document(schedule_id)
        schedule_doc = schedule_ref.get()

        if not schedule_doc.exists:
            raise HTTPException(status_code=404, detail=f"Schedule {schedule_id} not found")

        schedule_data = schedule_doc.to_dict()

        # Determine report type
        report_data = schedule_data.get("report", {})
        is_dashboard_report = "dashboard_id" in report_data
        report_type = "dashboard" if is_dashboard_report else "query"

        # Execute based on report type
        if is_dashboard_report:
            # Dashboard PDF/PNG rendering
            dashboard_id = report_data.get("dashboard_id")
            format_type = report_data.get("format", "pdf")

            logger.info(f"Rendering dashboard {dashboard_id} as {format_type}")

            try:
                # Render the dashboard
                result = await asyncio.to_thread(
                    render_dashboard,
                    org_id=x_org_id,
                    dashboard_id=dashboard_id,
                    format=format_type,
                )

                # TODO: Send email with attachment
                # For now, we log success and the Cloud Function can extend this
                logger.info(f"Dashboard rendered successfully: {len(result.data)} bytes")

                # Update run status
                await update_run_status(x_org_id, schedule_id, "success")

                return ScheduleExecuteResponse(
                    status="success",
                    schedule_id=schedule_id,
                    report_type=report_type,
                )

            except Exception as e:
                logger.error(f"Dashboard rendering failed: {e}")
                await update_run_status(x_org_id, schedule_id, "failed")
                return ScheduleExecuteResponse(
                    status="failed",
                    schedule_id=schedule_id,
                    report_type=report_type,
                    error=str(e),
                )

        else:
            # Query CSV/JSON export
            metrics = report_data.get("metrics", [])
            dimensions = report_data.get("dimensions", [])
            filters = report_data.get("filters", {})
            format_type = report_data.get("format", "csv")

            logger.info(f"Exporting query: metrics={metrics}, format={format_type}")

            try:
                # Create a minimal user context for the export
                from services.auth import UserContext
                user_context = UserContext(
                    uid="scheduler",
                    email="scheduler@metricly.xyz",
                    org_id=x_org_id,
                    role="admin",  # Scheduler has admin access
                )

                # Build query params
                params = QueryParams(
                    metrics=metrics,
                    dimensions=dimensions if dimensions else None,
                    # Note: filters are dict format here, would need conversion
                    # for full filter support
                )

                # Export query data
                export_result = await export_query_data(
                    user=user_context,
                    params=params,
                    format=format_type,
                )

                # TODO: Send email with attachment
                logger.info(f"Query exported successfully: {export_result.row_count} rows")

                # Update run status
                await update_run_status(x_org_id, schedule_id, "success")

                return ScheduleExecuteResponse(
                    status="success",
                    schedule_id=schedule_id,
                    report_type=report_type,
                )

            except Exception as e:
                logger.error(f"Query export failed: {e}")
                await update_run_status(x_org_id, schedule_id, "failed")
                return ScheduleExecuteResponse(
                    status="failed",
                    schedule_id=schedule_id,
                    report_type=report_type,
                    error=str(e),
                )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Schedule execution failed: {e}")
        raise HTTPException(status_code=500, detail=f"Execution failed: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
