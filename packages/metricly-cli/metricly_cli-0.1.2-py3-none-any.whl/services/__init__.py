"""Metricly Service Layer.

This module provides the core business logic for Metricly, extracted from
MCP server and chat agent implementations. Services are consumed by:
- MCP Server (FastMCP tools)
- CLI Tool (Typer commands)
- Chat Agent (Pydantic AI tools)

Services are pure business logic with:
- Typed inputs/outputs (Pydantic models)
- Async support for concurrent operations
- No knowledge of transport layer (MCP, HTTP, CLI)

Modules:
    auth: User context, role hierarchy, permission checks
    queries: Metric queries, visualization suggestions
    dashboards: Dashboard CRUD and widget operations
    manifest: Semantic layer management for admins
"""

# Auth exports
from .auth import (
    UserContext,
    require_role,
    get_user_by_email,
    get_user_orgs,
    switch_org,
    ROLE_HIERARCHY,
)

# Query exports
from .queries import (
    QueryParams,
    QueryResult,
    VisualizationSuggestion,
    query_metrics,
    list_metrics,
    list_dimensions,
    explain_metric,
    suggest_visualization,
)

# Dashboard exports
from .dashboards import (
    DashboardSummary,
    DashboardList,
    list_dashboards,
    get_dashboard,
    create_dashboard,
    create_dashboard_from_definition,
    update_dashboard,
    delete_dashboard,
    add_widget,
    remove_widget,
    update_widget,
    reorder_widgets,
)

# Manifest exports
from .manifest import (
    ManifestStatus,
    ConflictItem,
    ManifestImportResult,
    get_manifest_status,
    list_semantic_models,
    get_semantic_model,
    list_metrics as list_manifest_metrics,  # Alias to avoid conflict with queries.list_metrics
    get_metric,
    create_semantic_model,
    update_semantic_model,
    delete_semantic_model,
    create_metric,
    update_metric,
    delete_metric,
    import_manifest,
    export_manifest,
    preview_metric,
)

# Render exports
from .render import (
    RenderResult,
    RenderError,
    ChromeConnectionError,
    RenderTimeoutError,
    create_render_token,
    validate_render_token,
    validate_render_token_for_query,
    render_dashboard,
    render_widget,
    render_url_to_png,
    render_url_to_pdf,
)

__all__ = [
    # Auth exports
    "UserContext",
    "ROLE_HIERARCHY",
    "require_role",
    "get_user_by_email",
    "get_user_orgs",
    "switch_org",
    # Query exports
    "QueryParams",
    "QueryResult",
    "VisualizationSuggestion",
    "query_metrics",
    "list_metrics",
    "list_dimensions",
    "explain_metric",
    "suggest_visualization",
    # Dashboard exports
    "DashboardSummary",
    "DashboardList",
    "list_dashboards",
    "get_dashboard",
    "create_dashboard",
    "create_dashboard_from_definition",
    "update_dashboard",
    "delete_dashboard",
    "add_widget",
    "remove_widget",
    "update_widget",
    "reorder_widgets",
    # Manifest exports
    "ManifestStatus",
    "ConflictItem",
    "ManifestImportResult",
    "get_manifest_status",
    "list_semantic_models",
    "get_semantic_model",
    "list_manifest_metrics",
    "get_metric",
    "create_semantic_model",
    "update_semantic_model",
    "delete_semantic_model",
    "create_metric",
    "update_metric",
    "delete_metric",
    "import_manifest",
    "export_manifest",
    "preview_metric",
    # Render exports
    "RenderResult",
    "RenderError",
    "ChromeConnectionError",
    "RenderTimeoutError",
    "create_render_token",
    "validate_render_token",
    "validate_render_token_for_query",
    "render_dashboard",
    "render_widget",
    "render_url_to_png",
    "render_url_to_pdf",
]
