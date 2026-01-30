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
    schedules: Scheduled report management
    quick_metrics: Expression parser for calculated metrics
    activity: Activity logging for agent actions on dashboards
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
    QueryError,
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
    ConflictError,
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
    duplicate_dashboard,
    share_dashboard,
    set_dashboard_controls,
    create_page,
    create_section,
)

# Context exports
from .context import (
    UserPreferences,
    get_user_preferences,
    update_user_preferences,
    add_note,
    add_favorite,
    remove_favorite,
    remove_note,
)

# Export exports
from .export import (
    ExportResult,
    export_query_data,
    export_dashboard_data,
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

# Schedule exports
from .schedules import (
    Schedule,
    ScheduleSummary,
    ScheduleFrequency,
    DashboardReport,
    QueryReport,
    create_schedule,
    list_schedules,
    get_schedule,
    update_schedule,
    delete_schedule,
    update_run_status,
    get_schedules_due,
    get_schedules_for_dashboard,
)

# Quick Metrics exports
from .quick_metrics import (
    ParsedExpression,
    ExpressionError,
    QuickMetric,
    QuickMetricSummary,
    parse_expression,
    evaluate_expression,
    validate_metrics_exist,
    list_quick_metrics,
    get_quick_metric,
    get_quick_metric_by_name,
    create_quick_metric,
    update_quick_metric,
    delete_quick_metric,
)

# Activity exports
from .activity import (
    Activity,
    ActorType,
    ActionType,
    log_activity,
    get_recent_activity,
    get_activity_by_actor,
    get_activity_by_action,
    delete_activity,
    clear_activity,
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
    "QueryError",
    "VisualizationSuggestion",
    "query_metrics",
    "list_metrics",
    "list_dimensions",
    "explain_metric",
    "suggest_visualization",
    # Dashboard exports
    "DashboardSummary",
    "DashboardList",
    "ConflictError",
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
    "duplicate_dashboard",
    "share_dashboard",
    "set_dashboard_controls",
    "create_page",
    "create_section",
    # Context exports
    "UserPreferences",
    "get_user_preferences",
    "update_user_preferences",
    "add_note",
    "add_favorite",
    "remove_favorite",
    "remove_note",
    # Export exports
    "ExportResult",
    "export_query_data",
    "export_dashboard_data",
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
    # Schedule exports
    "Schedule",
    "ScheduleSummary",
    "ScheduleFrequency",
    "DashboardReport",
    "QueryReport",
    "create_schedule",
    "list_schedules",
    "get_schedule",
    "update_schedule",
    "delete_schedule",
    "update_run_status",
    "get_schedules_due",
    "get_schedules_for_dashboard",
    # Quick Metrics exports
    "ParsedExpression",
    "ExpressionError",
    "QuickMetric",
    "QuickMetricSummary",
    "parse_expression",
    "evaluate_expression",
    "validate_metrics_exist",
    "list_quick_metrics",
    "get_quick_metric",
    "get_quick_metric_by_name",
    "create_quick_metric",
    "update_quick_metric",
    "delete_quick_metric",
    # Activity exports
    "Activity",
    "ActorType",
    "ActionType",
    "log_activity",
    "get_recent_activity",
    "get_activity_by_actor",
    "get_activity_by_action",
    "delete_activity",
    "clear_activity",
]
