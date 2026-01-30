"""Metricly MCP Server - Remote MCP server with Google OAuth authentication.

This server exposes Metricly's metric query and dashboard capabilities
via the Model Context Protocol (MCP), allowing Claude.ai and other
MCP-compatible clients to interact with your business metrics.

Usage:
    # Run the MCP server
    python mcp_server.py

    # Or with uvicorn for production
    uvicorn mcp_server:app --host 0.0.0.0 --port 8080

Configuration:
    Environment variables:
    - MCP_OAUTH_CLIENT_ID: Google OAuth Client ID
    - MCP_OAUTH_CLIENT_SECRET: Google OAuth Client Secret
    - MCP_SERVER_BASE_URL: Base URL for the MCP server

Claude.ai Integration:
    1. Deploy this server (e.g., to Cloud Run)
    2. In Claude.ai, go to Settings → Integrations → Add MCP Server
    3. Enter the server URL: https://your-server.com/mcp
    4. OAuth will authenticate you via Google
    5. Start asking questions about your metrics!
"""

import asyncio
import base64
import logging
import os
from datetime import datetime
from typing import Literal

from fastmcp import FastMCP, Context
from fastmcp.server.dependencies import CurrentContext
from fastmcp.server.middleware import Middleware, MiddlewareContext, CallNext
from fastmcp.server.auth.providers.google import GoogleProvider
from fastmcp.exceptions import ToolError
from pydantic import BaseModel, Field

from auth import _init_firebase
from settings import get_settings
from services.auth import UserContext, get_user_by_email
import services.dashboards as dashboard_service
import services.queries as query_service
import services.context as context_service
import services.export as export_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)




# ============================================================================
# Authentication Middleware
# ============================================================================

# Global user for stdio mode (set by mcp_stdio.py before importing tools)
_stdio_user: UserContext | None = None


def set_stdio_user(user: UserContext):
    """Set user for stdio mode (bypasses OAuth)."""
    global _stdio_user
    _stdio_user = user


async def get_user_from_context(ctx: "Context") -> UserContext:
    """Get UserContext from MCP context, handling dict serialization."""
    # Note: get_state is synchronous, not async
    user_data = ctx.get_state("user")
    if user_data is None:
        raise ToolError("Authentication required: no user context")
    if isinstance(user_data, dict):
        return UserContext(**user_data)
    return user_data


class OrgContextMiddleware(Middleware):
    """Middleware to look up org context for authenticated OAuth user."""

    async def on_call_tool(
        self,
        context: MiddlewareContext,
        call_next: CallNext,
    ):
        """Look up user's org context and inject into tool context."""
        # Check for stdio mode user (pre-authenticated via CLI)
        if _stdio_user is not None:
            # Note: set_state is synchronous, not async
            context.fastmcp_context.set_state("user", _stdio_user)
            return await call_next(context)

        # Get authenticated user info from OAuth (provided by GoogleProvider)
        if not context.fastmcp_context:
            raise ToolError("Authentication required: no MCP context")

        # Get user info from OAuth authentication state
        # GoogleProvider stores access token info with claims from Google
        try:
            from fastmcp.server.dependencies import get_access_token
            access_token = get_access_token()
            logger.info(f"OrgContextMiddleware: got access_token type={type(access_token)}")
        except LookupError as e:
            logger.error(f"OrgContextMiddleware: LookupError getting access token: {e}")
            raise ToolError("Authentication required: please authenticate via OAuth")

        if not access_token:
            logger.error("OrgContextMiddleware: access_token is None/falsy")
            raise ToolError("Authentication required: no access token")

        # Log all available attributes on the token for debugging
        token_attrs = {attr: getattr(access_token, attr, None) for attr in dir(access_token) if not attr.startswith('_')}
        logger.info(f"OrgContextMiddleware: token attributes: {list(token_attrs.keys())}")

        # Get email from token claims (populated by GoogleProvider/FastMCP)
        # The claims include user info from Google's tokeninfo/userinfo APIs
        email = None
        if hasattr(access_token, 'claims') and access_token.claims:
            logger.info(f"OrgContextMiddleware: claims={access_token.claims}")
            email = access_token.claims.get("email")
            logger.info(f"OrgContextMiddleware: got email from claims: {email}")

        if not email:
            # Fallback: try to get email from resource_owner if available
            if hasattr(access_token, 'resource_owner') and access_token.resource_owner:
                email = access_token.resource_owner
                logger.info(f"OrgContextMiddleware: got email from resource_owner: {email}")

        if not email:
            # Log everything we know about the token
            logger.error(f"OrgContextMiddleware: No email found in token!")
            logger.error(f"  claims: {getattr(access_token, 'claims', 'N/A')}")
            logger.error(f"  resource_owner: {getattr(access_token, 'resource_owner', 'N/A')}")
            logger.error(f"  token: {getattr(access_token, 'token', 'N/A')}")
            logger.error(f"  scopes: {getattr(access_token, 'scopes', 'N/A')}")
            raise ToolError("OAuth authentication missing email - please re-authenticate")

        try:
            user = get_user_by_email(email)
        except ValueError as e:
            raise ToolError(f"Access denied: {e}")

        # Store user context in state for tools to access
        # Note: set_state is synchronous, not async
        context.fastmcp_context.set_state("user", user)

        return await call_next(context)




# ============================================================================
# MCP Server Setup
# ============================================================================

# Initialize Firebase before creating the server
_init_firebase()

# Get OAuth settings
settings = get_settings()

# Configure Google OAuth for Claude.ai integration
# OAuth is optional - if not configured, server runs without auth (dev mode)
auth_provider = None
if settings.mcp_oauth_client_id and settings.mcp_oauth_client_secret:
    from pydantic import AnyHttpUrl

    # base_url must include /mcp because OAuth routes (consent, authorize, token)
    # are created at app root, and this app is mounted at /api/mcp in main.py
    # So consent_url = base_url + "/consent" = "https://metricly.xyz/api/mcp/consent"
    base_url = f"{settings.mcp_server_base_url}/mcp"
    logger.info(f"Configuring Google OAuth for MCP server with base_url={base_url}")
    # Persistent JWT signing key is critical for production:
    # Without it, tokens become invalid when Cloud Run instances restart/scale
    if not settings.mcp_jwt_signing_key:
        logger.warning(
            "MCP_JWT_SIGNING_KEY not set! Tokens will be invalidated on server restart. "
            "Generate with: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
        )

    auth_provider = GoogleProvider(
        client_id=settings.mcp_oauth_client_id,
        client_secret=settings.mcp_oauth_client_secret,
        base_url=base_url,
        # Required scopes for user identification
        required_scopes=[
            "openid",
            "https://www.googleapis.com/auth/userinfo.email",
        ],
        # Allow Claude.ai's callback URL
        allowed_client_redirect_uris=[
            "https://claude.ai/api/mcp/auth_callback",
        ],
        # Persistent JWT signing key - critical for production
        # Without this, tokens become invalid when server restarts
        jwt_signing_key=settings.mcp_jwt_signing_key,
        # Skip FastMCP's consent screen - Google's consent is sufficient
        require_authorization_consent=False,
    )

    # Fix resource_url computation: FastMCP's _get_resource_url("/") adds trailing slash
    # but Claude.ai sends resource without trailing slash. Override to return base_url exactly.
    _original_get_resource_url = auth_provider._get_resource_url

    def _fixed_get_resource_url(path: str | None = None) -> AnyHttpUrl | None:
        # When path is "/" (root), return base_url without trailing slash
        if path == "/":
            return auth_provider.base_url
        return _original_get_resource_url(path)

    auth_provider._get_resource_url = _fixed_get_resource_url

    logger.info(f"OAuth base_url set to: {auth_provider.base_url}")
else:
    logger.warning("MCP OAuth not configured - running without authentication")

from mcp.types import Icon

from icon_data import METRICLY_ICON_DATA_URI

mcp = FastMCP(
    "Metricly",
    website_url="https://metricly.xyz",
    icons=[
        Icon(
            src=METRICLY_ICON_DATA_URI,
            mimeType="image/svg+xml",
        ),
    ],
    instructions="""You have access to Metricly, a business intelligence platform.

Use these tools to:
- Query business metrics (revenue, users, churn, etc.)
- List available metrics and dimensions
- View and manage dashboard configurations
- Export data to CSV or JSON
- Schedule recurring reports via email
- Create and query quick metrics (calculated metrics using expressions)
- Manage the semantic layer (admins only)

IMPORTANT: Use get_context at the start of conversations to load user preferences.
When you learn user preferences (currency, grain, etc.), use update_context to save them.

When answering questions about metrics:
1. First use list_metrics to see what's available
2. Use query_metrics to fetch actual data
3. Provide insights based on the results

For dashboard management:
- Use list_dashboards/get_dashboard to view dashboards
- Use create_dashboard/update_dashboard/delete_dashboard to manage dashboards
- Use add_widget/update_widget/remove_widget to manage widgets within dashboards
- Use reorder_widgets to change widget order in a section
- Use duplicate_dashboard to create a copy of an existing dashboard
- Use share_dashboard to toggle visibility (private/org)
- Use set_dashboard_controls to update date range, grain, or comparison mode

Widget width (10-column grid):
- width=2: kpi default (5 per row)
- width=3: donut default (3 per row)
- width=5: heatmap default (2 per row)
- width=10: charts/tables default (full width)
If width not specified, type-appropriate default is applied automatically.

Widget time_scope (for non-time-series widgets):
- "range": Full dashboard date range (default)
- "latest": Current period only (may be incomplete)
- "latest_complete": Last complete period
Use latest_complete for KPIs showing "last month's revenue" alongside trend charts.

For dashboard structural changes, prefer ATOMIC OPERATIONS:

Widget Operations:
- move_widget(dashboard_id, widget_id, target_page_id, target_section_index, position?) - Move widget to new location
- copy_widget(dashboard_id, widget_id, target_page_id, target_section_index, new_title?) - Copy widget
- swap_widgets(dashboard_id, widget_id_1, widget_id_2) - Swap two widgets

Section Operations:
- create_section(dashboard_id, page_id, title?, position?) - Create new section
- delete_section(dashboard_id, page_id, section_index, cascade?) - Delete section
- rename_section(dashboard_id, page_id, section_index, title) - Rename section
- move_section(dashboard_id, source_page_id, section_index, target_page_id, position?) - Move section

Page Operations:
- create_page(dashboard_id, title, position?) - Create new page
- delete_page(dashboard_id, page_id, cascade?) - Delete page
- rename_page(dashboard_id, page_id, title) - Rename page
- reorder_pages(dashboard_id, page_ids) - Reorder pages

IMPORTANT: Use atomic operations for structural changes instead of update_dashboard.
Only use update_dashboard for bulk operations affecting 5+ elements simultaneously

For data export:
- Use export_data to export query results or dashboard data
- Supports CSV and JSON formats
- Can save to file with output_path parameter

For scheduled reports:
- Use create_scheduled_report to set up recurring email reports
- Supports dashboard reports (PDF/PNG) or query reports (CSV/JSON)
- Frequency options: daily, weekly (specify day_of_week 0-6), monthly (specify day_of_month 1-28)
- Use list_scheduled_reports to see all schedules
- Use get_scheduled_report to view schedule details
- Use update_scheduled_report to modify settings or pause (enabled=False)
- Use delete_scheduled_report to remove a schedule

For user context (memory across sessions):
- Use get_context to load saved preferences, favorites, and notes
- Use update_context when you learn user preferences
- Use add_note to record insights about metrics or data

For quick metrics (user-defined calculated metrics):
- Use create_quick_metric to define derived metrics using arithmetic expressions
  Example: create_quick_metric("revenue_per_order", "total_revenue / order_count")
- Use list_quick_metrics to see all quick metrics in your organization
- Use get_quick_metric to view a quick metric's definition
- Use update_quick_metric to modify name, expression, or description
- Use delete_quick_metric to remove a quick metric
- Query quick metrics with the qm: prefix: query_metrics(metrics=["qm:revenue_per_order"], ...)
- Expressions support: +, -, *, /, parentheses, and numeric constants
- All referenced metrics in expressions must exist in the manifest

For semantic layer management (requires admin role):
- Use list_semantic_models/get_semantic_model to explore models
- Use create/update/delete_semantic_model to manage models
- Use create/update/delete_metric to manage metrics
- Use preview_metric to test a metric before saving
- Use import_manifest to bulk import from dbt
- Use export_manifest to backup your semantic layer

Always specify date ranges when querying to get relevant data.""",
    auth=auth_provider,
)

# Add org context middleware (after OAuth authentication)
mcp.add_middleware(OrgContextMiddleware())


# ============================================================================
# Tool Parameter Models
# ============================================================================

class MCPQueryParams(BaseModel):
    """Parameters for querying metrics (MCP-compatible with string dates)."""
    metrics: list[str] = Field(description="List of metric names to query (e.g., ['total_revenue', 'order_count'])")
    dimensions: list[str] | None = Field(default=None, description="Dimensions to group by. Use qualified names from list_dimensions (e.g., ['customer__segment', 'order__region'])")
    grain: str | None = Field(default=None, description="Time granularity: 'day', 'week', 'month', 'quarter', or 'year'")
    start_date: str | None = Field(default=None, description="Start date in YYYY-MM-DD format")
    end_date: str | None = Field(default=None, description="End date in YYYY-MM-DD format")
    limit: int | None = Field(default=None, description="Maximum number of rows to return")
    order_by: str | None = Field(default=None, description="Column to sort by, append ' desc' for descending (e.g., 'total_revenue desc')")


# ============================================================================
# MCP Tools
# ============================================================================

@mcp.tool()
async def list_metrics(ctx: Context = CurrentContext()) -> list[dict]:
    """List all available metrics in the organization.

    Returns metrics with their names, types, descriptions, and definitions.
    Use this to discover what metrics are available before querying.
    """
    user = await get_user_from_context(ctx)

    try:
        return await query_service.list_metrics(user.org_id)
    except ValueError as e:
        return [{"error": f"Failed to load metrics: {e}"}]


@mcp.tool()
async def list_dimensions(ctx: Context = CurrentContext()) -> list[dict]:
    """List all available dimensions that can be used for grouping.

    Dimensions are attributes you can group metrics by. Use the qualified names
    returned here when querying (e.g., customer__region, order__product_category).
    The prefix before __ is the entity name the dimension belongs to.
    """
    user = await get_user_from_context(ctx)

    try:
        return await query_service.list_dimensions(user.org_id)
    except ValueError as e:
        return [{"error": f"Failed to load dimensions: {e}"}]


@mcp.tool()
async def query_metrics(
    params: MCPQueryParams,
    suggest_visualization: bool = False,
    ctx: Context = CurrentContext(),
) -> dict:
    """Execute a metric query and return the results.

    Use this to fetch actual data for one or more metrics. You can optionally:
    - Group by dimensions
    - Filter by time range
    - Limit results
    - Sort by a column
    - Get a visualization suggestion

    Example queries:
    - Monthly revenue: metrics=['total_revenue'], grain='month', start_date='2024-01-01'
    - Revenue by region: metrics=['total_revenue'], dimensions=['region']
    - Top 10 customers: metrics=['total_revenue'], dimensions=['customer_name'], order_by='total_revenue desc', limit=10

    Args:
        params: Query parameters (metrics, dimensions, grain, dates, etc.)
        suggest_visualization: If True, include a visualization recommendation
    """
    user = await get_user_from_context(ctx)

    try:
        # Parse string dates to date objects for the service layer
        start_date = None
        end_date = None
        if params.start_date:
            start_date = datetime.strptime(params.start_date, "%Y-%m-%d").date()
        if params.end_date:
            end_date = datetime.strptime(params.end_date, "%Y-%m-%d").date()

        # Create service layer QueryParams
        service_params = query_service.QueryParams(
            metrics=params.metrics,
            dimensions=params.dimensions,
            grain=params.grain,
            start_date=start_date,
            end_date=end_date,
            limit=params.limit,
            order_by=params.order_by,
        )

        # Execute query via service layer
        result = await query_service.query_metrics(
            org_id=user.org_id,
            params=service_params,
            include_visualization=suggest_visualization,
        )

        # Build response in same format as before
        response = {
            "success": True,
            "row_count": result.row_count,
            "columns": result.columns,
            "data": result.data,
        }

        # Include visualization suggestion if requested
        if result.visualization:
            response["visualization"] = {
                "widget_type": result.visualization.widget_type,
                "orientation": result.visualization.orientation,
                "format": result.visualization.format,
                "rationale": result.visualization.rationale,
            }

        return response

    except query_service.QueryError as e:
        # Return user-friendly error with hint
        error_response = {"error": e.message}
        if e.hint:
            error_response["hint"] = e.hint
        return error_response
    except ValueError as e:
        return {"error": f"Failed to initialize query engine: {e}"}
    except Exception as e:
        logger.error(f"Query failed: {e}")
        return {"error": str(e)}


@mcp.tool()
async def list_dashboards(ctx: Context = CurrentContext()) -> list[dict]:
    """List all dashboards accessible to the user.

    Returns dashboard titles, descriptions, and visibility (private or shared with org).
    """
    user = await get_user_from_context(ctx)

    try:
        result = await dashboard_service.list_dashboards(user)
        dashboards = []

        for d in result.personal:
            dashboards.append({
                "id": d.id,
                "title": d.title,
                "description": d.description,
                "visibility": "private",
                "owner": d.owner,
            })

        for d in result.team:
            dashboards.append({
                "id": d.id,
                "title": d.title,
                "description": d.description,
                "visibility": "org",
                "owner": d.owner,
            })

        return dashboards
    except Exception as e:
        return [{"error": f"Failed to list dashboards: {e}"}]


@mcp.tool()
async def get_dashboard(dashboard_id: str, ctx: Context = CurrentContext()) -> dict:
    """Get detailed information about a specific dashboard.

    Returns the full dashboard configuration including pages, sections, and widgets.
    """
    user = await get_user_from_context(ctx)

    try:
        dashboard = await dashboard_service.get_dashboard(user, dashboard_id)
        return dashboard.model_dump()
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to get dashboard: {e}"}


@mcp.tool()
async def explain_metric(metric_name: str, ctx: Context = CurrentContext()) -> dict:
    """Get detailed information about how a specific metric is calculated.

    Returns the metric definition including its type, formula, and underlying measures.
    """
    user = await get_user_from_context(ctx)

    try:
        return await query_service.explain_metric(user.org_id, metric_name)
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to load metric: {e}"}


@mcp.tool()
async def create_dashboard(
    title: str,
    description: str | None = None,
    visibility: str = "private",
    ctx: Context = CurrentContext(),
) -> dict:
    """Create a new dashboard.

    Args:
        title: Dashboard title
        description: Optional description
        visibility: "private" (only you) or "org" (shared with organization)

    Returns the created dashboard with its generated ID.
    """
    user = await get_user_from_context(ctx)

    if visibility not in ("private", "org"):
        return {"error": f"Invalid visibility: {visibility}. Must be 'private' or 'org'"}

    try:
        dashboard = await dashboard_service.create_dashboard(
            user,
            title=title,
            description=description,
            visibility=visibility,
        )
        return {
            "success": True,
            "dashboard": dashboard.model_dump(),
        }
    except Exception as e:
        return {"error": f"Failed to create dashboard: {e}"}


@mcp.tool()
async def update_dashboard(
    dashboard_id: str,
    title: str | None = None,
    description: str | None = None,
    visibility: str | None = None,
    expected_version: int | None = None,
    ctx: Context = CurrentContext(),
) -> dict:
    """Update an existing dashboard.

    Args:
        dashboard_id: ID of the dashboard to update
        title: New title (optional)
        description: New description (optional)
        visibility: New visibility - "private" or "org" (optional)
        expected_version: For optimistic locking - if provided, update will fail
            if the current version doesn't match. Use the version from get_dashboard
            to prevent overwriting concurrent changes.

    Only fields that are provided will be updated.
    You must be the owner of the dashboard to update it.

    Returns a conflict error if expected_version is provided but doesn't match
    the current version. In that case, re-fetch the dashboard to get the latest
    version and retry your changes.
    """
    user = await get_user_from_context(ctx)

    updates = {}
    if title is not None:
        updates["title"] = title
    if description is not None:
        updates["description"] = description
    if visibility is not None:
        if visibility not in ("private", "org"):
            return {"error": f"Invalid visibility: {visibility}. Must be 'private' or 'org'"}
        updates["visibility"] = visibility

    if not updates:
        return {"error": "No updates provided"}

    try:
        dashboard = await dashboard_service.update_dashboard(
            user, dashboard_id, updates, expected_version
        )
        return {
            "success": True,
            "dashboard": dashboard.model_dump(),
        }
    except dashboard_service.ConflictError as e:
        return {
            "error": "conflict",
            "message": str(e),
            "current_version": e.current_version,
            "expected_version": e.expected_version,
        }
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to update dashboard: {e}"}


@mcp.tool()
async def delete_dashboard(dashboard_id: str, ctx: Context = CurrentContext()) -> dict:
    """Delete a dashboard.

    Args:
        dashboard_id: ID of the dashboard to delete

    You must be the owner of the dashboard to delete it.
    This action cannot be undone.
    """
    user = await get_user_from_context(ctx)

    try:
        await dashboard_service.delete_dashboard(user, dashboard_id)
        return {"success": True, "message": f"Dashboard '{dashboard_id}' deleted"}
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to delete dashboard: {e}"}


@mcp.tool()
async def add_widget(
    dashboard_id: str,
    widget: dict,
    page_index: int = 0,
    section_index: int = 0,
    expected_version: int | None = None,
    ctx: Context = CurrentContext(),
) -> dict:
    """Add a widget to a dashboard.

    Args:
        dashboard_id: ID of the dashboard
        widget: Widget definition with type, title, query, etc.
        page_index: Index of the page to add to (default: 0)
        section_index: Index of the section within the page (default: 0)
        expected_version: For optimistic locking - if provided, update will fail
            if the current version doesn't match.

    Widget definition should include:
    - type: Widget type (kpi, area_chart, bar_chart, line_chart, table, donut, heatmap)
    - title: Widget title
    - query: Query configuration with metrics, dimensions, etc.
    - format: Optional formatting options
    - width: Optional column span (1-10). If not specified, uses type defaults:
        - kpi: 2 (5 per row)
        - donut: 3 (3 per row)
        - heatmap: 5 (2 per row)
        - area_chart, line_chart, bar_chart, table: 10 (full width)
    - time_scope: Date scope for non-time-series widgets:
        - "range" (default): Use full dashboard date range
        - "latest": Current period only (may be incomplete)
        - "latest_complete": Last complete period (use for KPIs in monthly reports)

    You must be the owner of the dashboard to add widgets.
    """
    user = await get_user_from_context(ctx)

    try:
        dashboard = await dashboard_service.add_widget(
            user,
            dashboard_id,
            widget,
            page_index=page_index,
            section_index=section_index,
            expected_version=expected_version,
        )
        return {
            "success": True,
            "message": f"Widget added to page {page_index}, section {section_index}",
            "dashboard": dashboard.model_dump(),
        }
    except dashboard_service.ConflictError as e:
        return {
            "error": "conflict",
            "message": str(e),
            "current_version": e.current_version,
            "expected_version": e.expected_version,
        }
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to add widget: {e}"}


@mcp.tool()
async def remove_widget(
    dashboard_id: str,
    page_index: int,
    section_index: int,
    widget_index: int,
    expected_version: int | None = None,
    ctx: Context = CurrentContext(),
) -> dict:
    """Remove a widget from a dashboard.

    Args:
        dashboard_id: ID of the dashboard
        page_index: Index of the page containing the widget
        section_index: Index of the section containing the widget
        widget_index: Index of the widget to remove
        expected_version: For optimistic locking - if provided, update will fail
            if the current version doesn't match.

    You must be the owner of the dashboard to remove widgets.
    This action cannot be undone.
    """
    user = await get_user_from_context(ctx)

    try:
        dashboard = await dashboard_service.remove_widget(
            user,
            dashboard_id,
            page_index=page_index,
            section_index=section_index,
            widget_index=widget_index,
            expected_version=expected_version,
        )
        return {
            "success": True,
            "message": f"Widget removed from page {page_index}, section {section_index}",
            "dashboard": dashboard.model_dump(),
        }
    except dashboard_service.ConflictError as e:
        return {
            "error": "conflict",
            "message": str(e),
            "current_version": e.current_version,
            "expected_version": e.expected_version,
        }
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to remove widget: {e}"}


@mcp.tool()
async def update_widget(
    dashboard_id: str,
    page_index: int,
    section_index: int,
    widget_index: int,
    updates: dict,
    expected_version: int | None = None,
    ctx: Context = CurrentContext(),
) -> dict:
    """Update a specific widget in a dashboard.

    Args:
        dashboard_id: ID of the dashboard
        page_index: Index of the page containing the widget
        section_index: Index of the section containing the widget
        widget_index: Index of the widget to update
        updates: Fields to update (title, query, format, type, etc.)
        expected_version: For optimistic locking - if provided, update will fail
            if the current version doesn't match.

    Only provided fields will be updated; other fields remain unchanged.
    You must be the owner of the dashboard to update widgets.
    """
    user = await get_user_from_context(ctx)

    try:
        dashboard = await dashboard_service.update_widget(
            user,
            dashboard_id,
            page_index=page_index,
            section_index=section_index,
            widget_index=widget_index,
            updates=updates,
            expected_version=expected_version,
        )
        return {
            "success": True,
            "message": f"Widget updated at page {page_index}, section {section_index}, widget {widget_index}",
            "dashboard": dashboard.model_dump(),
        }
    except dashboard_service.ConflictError as e:
        return {
            "error": "conflict",
            "message": str(e),
            "current_version": e.current_version,
            "expected_version": e.expected_version,
        }
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to update widget: {e}"}


@mcp.tool()
async def reorder_widgets(
    dashboard_id: str,
    page_index: int,
    section_index: int,
    widget_ids: list[str],
    expected_version: int | None = None,
    ctx: Context = CurrentContext(),
) -> dict:
    """Reorder widgets within a section.

    Args:
        dashboard_id: ID of the dashboard
        page_index: Index of the page containing the section
        section_index: Index of the section to reorder
        widget_ids: List of widget IDs in the new desired order
        expected_version: For optimistic locking - if provided, update will fail
            if the current version doesn't match.

    All widget IDs in the section must be provided in the new order.
    You must be the owner of the dashboard to reorder widgets.
    """
    user = await get_user_from_context(ctx)

    try:
        dashboard = await dashboard_service.reorder_widgets(
            user,
            dashboard_id,
            page_index=page_index,
            section_index=section_index,
            widget_ids=widget_ids,
            expected_version=expected_version,
        )
        return {
            "success": True,
            "message": f"Widgets reordered in page {page_index}, section {section_index}",
            "dashboard": dashboard.model_dump(),
        }
    except dashboard_service.ConflictError as e:
        return {
            "error": "conflict",
            "message": str(e),
            "current_version": e.current_version,
            "expected_version": e.expected_version,
        }
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to reorder widgets: {e}"}


# ============================================================================
# Atomic Widget Operations
# ============================================================================


@mcp.tool()
async def move_widget(
    dashboard_id: str,
    widget_id: str,
    target_page_id: str,
    target_section_index: int,
    position: int | None = None,
    ctx: Context = CurrentContext(),
) -> dict:
    """Move a widget to a different location in the dashboard.

    Args:
        dashboard_id: ID of the dashboard
        widget_id: ID of the widget to move
        target_page_id: ID of the destination page
        target_section_index: Index of the destination section
        position: Position within section (None = append to end)

    Returns the updated dashboard.
    """
    user = await get_user_from_context(ctx)

    try:
        dashboard = await dashboard_service.move_widget(
            user,
            dashboard_id,
            widget_id,
            target_page_id,
            target_section_index,
            position,
        )
        return {
            "success": True,
            "message": f"Widget moved to page {target_page_id}, section {target_section_index}",
            "dashboard": dashboard.model_dump(),
        }
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to move widget: {e}"}


@mcp.tool()
async def copy_widget(
    dashboard_id: str,
    widget_id: str,
    target_page_id: str,
    target_section_index: int,
    new_title: str | None = None,
    ctx: Context = CurrentContext(),
) -> dict:
    """Copy a widget to a new location with a new ID.

    Args:
        dashboard_id: ID of the dashboard
        widget_id: ID of the widget to copy
        target_page_id: ID of the destination page
        target_section_index: Index of the destination section
        new_title: Title for the copy (default: "Copy of {original}")

    Returns the updated dashboard.
    """
    user = await get_user_from_context(ctx)

    try:
        dashboard = await dashboard_service.copy_widget(
            user,
            dashboard_id,
            widget_id,
            target_page_id,
            target_section_index,
            new_title,
        )
        return {
            "success": True,
            "message": f"Widget copied to page {target_page_id}, section {target_section_index}",
            "dashboard": dashboard.model_dump(),
        }
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to copy widget: {e}"}


@mcp.tool()
async def swap_widgets(
    dashboard_id: str,
    widget_id_1: str,
    widget_id_2: str,
    ctx: Context = CurrentContext(),
) -> dict:
    """Swap the positions of two widgets.

    Args:
        dashboard_id: ID of the dashboard
        widget_id_1: ID of first widget
        widget_id_2: ID of second widget

    Widgets can be in different sections or pages.
    Returns the updated dashboard.
    """
    user = await get_user_from_context(ctx)

    try:
        dashboard = await dashboard_service.swap_widgets(
            user,
            dashboard_id,
            widget_id_1,
            widget_id_2,
        )
        return {
            "success": True,
            "message": f"Widgets {widget_id_1} and {widget_id_2} swapped",
            "dashboard": dashboard.model_dump(),
        }
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to swap widgets: {e}"}


# ============================================================================
# Dashboard Parity Tools
# ============================================================================


@mcp.tool()
async def duplicate_dashboard(
    dashboard_id: str,
    new_title: str | None = None,
    ctx: Context = CurrentContext(),
) -> dict:
    """Duplicate a dashboard with all its pages, sections, and widgets.

    Creates a private copy owned by you. All widget and page IDs are
    regenerated to avoid conflicts.

    Args:
        dashboard_id: ID of the dashboard to duplicate
        new_title: Title for the new dashboard (default: "Copy of {original}")

    Returns the created dashboard.
    """
    user = await get_user_from_context(ctx)

    try:
        dashboard = await dashboard_service.duplicate_dashboard(
            user,
            dashboard_id,
            new_title=new_title,
        )
        return {
            "success": True,
            "dashboard": dashboard.model_dump(),
        }
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to duplicate dashboard: {e}"}


@mcp.tool()
async def share_dashboard(
    dashboard_id: str,
    visibility: str,
    ctx: Context = CurrentContext(),
) -> dict:
    """Toggle dashboard visibility between private and shared.

    Args:
        dashboard_id: ID of the dashboard
        visibility: "private" (only you) or "org" (shared with organization)

    You must be the owner of the dashboard to change its visibility.
    """
    user = await get_user_from_context(ctx)

    if visibility not in ("private", "org"):
        return {"error": f"Invalid visibility: {visibility}. Must be 'private' or 'org'"}

    try:
        dashboard = await dashboard_service.share_dashboard(
            user,
            dashboard_id,
            visibility=visibility,
        )
        return {
            "success": True,
            "dashboard": dashboard.model_dump(),
        }
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to share dashboard: {e}"}


@mcp.tool()
async def set_dashboard_controls(
    dashboard_id: str,
    date_range: dict | None = None,
    grain: str | None = None,
    comparison: str | None = None,
    ctx: Context = CurrentContext(),
) -> dict:
    """Update dashboard controls (date range, grain, comparison).

    Only provided fields are updated; others remain unchanged.

    Args:
        dashboard_id: ID of the dashboard
        date_range: Date range config with mode (relative/absolute) and settings.
                    For relative: {"mode": "relative", "preset": "last_30_days"}
                    For absolute: {"mode": "absolute", "start_date": "2024-01-01", "end_date": "2024-12-31"}
        grain: Time granularity: "day", "week", "month", "quarter", or "year"
        comparison: Comparison mode: "none", "previous_period", or "same_period_last_year"

    You must be the owner of the dashboard to update its controls.
    """
    user = await get_user_from_context(ctx)

    try:
        dashboard = await dashboard_service.set_dashboard_controls(
            user,
            dashboard_id,
            date_range=date_range,
            grain=grain,
            comparison=comparison,
        )
        return {
            "success": True,
            "dashboard": dashboard.model_dump(),
        }
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to update dashboard controls: {e}"}


# ============================================================================
# Atomic Page Operations
# ============================================================================


@mcp.tool()
async def create_page(
    dashboard_id: str,
    title: str,
    position: int | None = None,
    ctx: Context = CurrentContext(),
) -> dict:
    """Create a new page in a dashboard.

    Args:
        dashboard_id: ID of the dashboard
        title: Page title
        position: Position to insert (None = append to end)

    Returns the updated dashboard.
    """
    user = await get_user_from_context(ctx)

    try:
        dashboard = await dashboard_service.create_page(
            user,
            dashboard_id,
            title,
            position,
        )
        return {
            "success": True,
            "message": f"Page '{title}' created",
            "dashboard": dashboard.model_dump(),
        }
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to create page: {e}"}


@mcp.tool()
async def delete_page(
    dashboard_id: str,
    page_id: str,
    cascade: bool = False,
    ctx: Context = CurrentContext(),
) -> dict:
    """Delete a page from a dashboard.

    Args:
        dashboard_id: ID of the dashboard
        page_id: ID of page to delete
        cascade: If True, delete even if page has widgets

    Cannot delete the last page.
    Returns the updated dashboard.
    """
    user = await get_user_from_context(ctx)

    try:
        dashboard = await dashboard_service.delete_page(
            user,
            dashboard_id,
            page_id,
            cascade,
        )
        return {
            "success": True,
            "message": f"Page {page_id} deleted",
            "dashboard": dashboard.model_dump(),
        }
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to delete page: {e}"}


@mcp.tool()
async def rename_page(
    dashboard_id: str,
    page_id: str,
    title: str,
    ctx: Context = CurrentContext(),
) -> dict:
    """Rename a page.

    Args:
        dashboard_id: ID of the dashboard
        page_id: ID of page to rename
        title: New title

    Returns the updated dashboard.
    """
    user = await get_user_from_context(ctx)

    try:
        dashboard = await dashboard_service.rename_page(
            user,
            dashboard_id,
            page_id,
            title,
        )
        return {
            "success": True,
            "message": f"Page renamed to '{title}'",
            "dashboard": dashboard.model_dump(),
        }
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to rename page: {e}"}


@mcp.tool()
async def reorder_pages(
    dashboard_id: str,
    page_ids: list[str],
    ctx: Context = CurrentContext(),
) -> dict:
    """Reorder pages in a dashboard.

    Args:
        dashboard_id: ID of the dashboard
        page_ids: List of all page IDs in new order

    All existing page IDs must be provided.
    Returns the updated dashboard.
    """
    user = await get_user_from_context(ctx)

    try:
        dashboard = await dashboard_service.reorder_pages(
            user,
            dashboard_id,
            page_ids,
        )
        return {
            "success": True,
            "message": "Pages reordered",
            "dashboard": dashboard.model_dump(),
        }
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to reorder pages: {e}"}


# ============================================================================
# Atomic Section Operations
# ============================================================================


@mcp.tool()
async def create_section(
    dashboard_id: str,
    page_id: str,
    title: str | None = None,
    position: int | None = None,
    ctx: Context = CurrentContext(),
) -> dict:
    """Create a new section in a page.

    Args:
        dashboard_id: ID of the dashboard
        page_id: ID of the page to add section to
        title: Optional section title
        position: Position to insert (None = append to end)

    Returns the updated dashboard.
    """
    user = await get_user_from_context(ctx)

    try:
        dashboard = await dashboard_service.create_section(
            user,
            dashboard_id,
            page_id,
            title,
            position,
        )
        return {
            "success": True,
            "message": f"Section created in page {page_id}",
            "dashboard": dashboard.model_dump(),
        }
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to create section: {e}"}


@mcp.tool()
async def delete_section(
    dashboard_id: str,
    page_id: str,
    section_index: int,
    cascade: bool = False,
    ctx: Context = CurrentContext(),
) -> dict:
    """Delete a section from a page.

    Args:
        dashboard_id: ID of the dashboard
        page_id: ID of the page containing section
        section_index: Index of section to delete
        cascade: If True, delete even if section has widgets

    Returns the updated dashboard.
    """
    user = await get_user_from_context(ctx)

    try:
        dashboard = await dashboard_service.delete_section(
            user,
            dashboard_id,
            page_id,
            section_index,
            cascade,
        )
        return {
            "success": True,
            "message": f"Section {section_index} deleted from page {page_id}",
            "dashboard": dashboard.model_dump(),
        }
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to delete section: {e}"}


@mcp.tool()
async def rename_section(
    dashboard_id: str,
    page_id: str,
    section_index: int,
    title: str | None,
    ctx: Context = CurrentContext(),
) -> dict:
    """Rename a section.

    Args:
        dashboard_id: ID of the dashboard
        page_id: ID of the page containing section
        section_index: Index of section to rename
        title: New title (None to remove title)

    Returns the updated dashboard.
    """
    user = await get_user_from_context(ctx)

    try:
        dashboard = await dashboard_service.rename_section(
            user,
            dashboard_id,
            page_id,
            section_index,
            title,
        )
        return {
            "success": True,
            "message": f"Section {section_index} renamed",
            "dashboard": dashboard.model_dump(),
        }
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to rename section: {e}"}


@mcp.tool()
async def move_section(
    dashboard_id: str,
    source_page_id: str,
    section_index: int,
    target_page_id: str,
    target_position: int | None = None,
    ctx: Context = CurrentContext(),
) -> dict:
    """Move a section to a different page or position.

    Args:
        dashboard_id: ID of the dashboard
        source_page_id: ID of page containing section
        section_index: Index of section to move
        target_page_id: ID of destination page
        target_position: Position in target page (None = append)

    Returns the updated dashboard.
    """
    user = await get_user_from_context(ctx)

    try:
        dashboard = await dashboard_service.move_section(
            user,
            dashboard_id,
            source_page_id,
            section_index,
            target_page_id,
            target_position,
        )
        return {
            "success": True,
            "message": f"Section moved to page {target_page_id}",
            "dashboard": dashboard.model_dump(),
        }
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to move section: {e}"}


# ============================================================================
# Export Tools
# ============================================================================


@mcp.tool()
async def export_data(
    format: str = "csv",
    metrics: list[str] | None = None,
    dimensions: list[str] | None = None,
    grain: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    dashboard_id: str | None = None,
    output_path: str | None = None,
    ctx: Context = CurrentContext(),
) -> dict:
    """Export query results or dashboard data to CSV or JSON.

    You can either:
    - Export query results by specifying metrics, dimensions, etc.
    - Export all data from a dashboard by specifying dashboard_id

    Args:
        format: Output format - "csv" or "json" (default: csv)
        metrics: List of metric names to query (for query export)
        dimensions: Dimensions to group by (for query export)
        grain: Time granularity (for query export)
        start_date: Start date YYYY-MM-DD (for query export)
        end_date: End date YYYY-MM-DD (for query export)
        dashboard_id: Dashboard ID (for dashboard export, overrides query params)
        output_path: If provided, save to this file path

    Returns the data content (CSV or JSON) or file path if saved.
    """
    user = await get_user_from_context(ctx)

    if format not in ("csv", "json"):
        return {"error": f"Invalid format: {format}. Must be 'csv' or 'json'"}

    try:
        # Dashboard export takes precedence
        if dashboard_id:
            result = await export_service.export_dashboard_data(
                user,
                dashboard_id,
                format=format,
                output_path=output_path,
            )
        else:
            # Query export requires at least metrics
            if not metrics:
                return {"error": "Either dashboard_id or metrics must be provided"}

            # Parse dates
            parsed_start = None
            parsed_end = None
            if start_date:
                parsed_start = datetime.strptime(start_date, "%Y-%m-%d").date()
            if end_date:
                parsed_end = datetime.strptime(end_date, "%Y-%m-%d").date()

            params = query_service.QueryParams(
                metrics=metrics,
                dimensions=dimensions,
                grain=grain,
                start_date=parsed_start,
                end_date=parsed_end,
            )

            result = await export_service.export_query_data(
                user,
                params,
                format=format,
                output_path=output_path,
            )

        response = {
            "success": True,
            "format": result.format,
            "row_count": result.row_count,
            "columns": result.columns,
        }

        if result.saved_to:
            response["saved_to"] = result.saved_to
        else:
            response["content"] = result.content

        return response

    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to export data: {e}"}


# ============================================================================
# Context Tools (User Preferences)
# ============================================================================


@mcp.tool()
async def get_context(ctx: Context = CurrentContext()) -> dict:
    """Get accumulated user context including preferences, favorites, and notes.

    This context persists across sessions and helps personalize interactions.
    Returns:
    - Format preferences (currency, grain, decimal places)
    - Favorite metrics
    - Notes about metrics/topics
    - Custom instructions
    """
    user = await get_user_from_context(ctx)

    try:
        prefs = await context_service.get_user_preferences(user.uid)
        return {
            "default_currency": prefs.default_currency,
            "default_grain": prefs.default_grain,
            "decimal_places": prefs.decimal_places,
            "preferred_chart_type": prefs.preferred_chart_type,
            "favorite_metrics": prefs.favorite_metrics,
            "notes": prefs.notes,
            "custom_instructions": prefs.custom_instructions,
            "updated_at": prefs.updated_at,
        }
    except Exception as e:
        return {"error": f"Failed to get context: {e}"}


@mcp.tool()
async def update_context(
    updates: dict,
    ctx: Context = CurrentContext(),
) -> dict:
    """Update user preferences (merge, not replace).

    Use this when you learn user preferences during conversation.
    Only provided fields are updated; others remain unchanged.

    Args:
        updates: Fields to update. Supported fields:
            - default_currency: Preferred currency (e.g., "USD", "EUR")
            - default_grain: Preferred time grain (e.g., "month", "week")
            - decimal_places: Number of decimal places for values
            - preferred_chart_type: Preferred visualization type
            - favorite_metrics: List of favorite metric names
            - custom_instructions: User's custom instructions

    Example: update_context({"default_currency": "EUR", "default_grain": "month"})
    """
    user = await get_user_from_context(ctx)

    try:
        prefs = await context_service.update_user_preferences(user.uid, updates)
        return {
            "success": True,
            "context": {
                "default_currency": prefs.default_currency,
                "default_grain": prefs.default_grain,
                "decimal_places": prefs.decimal_places,
                "preferred_chart_type": prefs.preferred_chart_type,
                "favorite_metrics": prefs.favorite_metrics,
                "notes": prefs.notes,
                "custom_instructions": prefs.custom_instructions,
                "updated_at": prefs.updated_at,
            },
        }
    except Exception as e:
        return {"error": f"Failed to update context: {e}"}


@mcp.tool()
async def add_note(
    subject: str,
    note: str,
    ctx: Context = CurrentContext(),
) -> dict:
    """Add a note about a metric, dashboard, or topic.

    Use this to record insights, caveats, or context about data.
    Notes persist across sessions and help with future analysis.

    Args:
        subject: Subject of the note (e.g., metric name, "data quality", "business context")
        note: The note content

    Notes are keyed by subject; adding a note with an existing subject replaces it.
    """
    user = await get_user_from_context(ctx)

    try:
        prefs = await context_service.add_note(user.uid, subject, note)
        return {
            "success": True,
            "notes": prefs.notes,
        }
    except Exception as e:
        return {"error": f"Failed to add note: {e}"}


# ============================================================================
# Render Tools
# ============================================================================

from services import render_dashboard as render_dashboard_service
from services import render_widget as render_widget_service
from services import RenderError


@mcp.tool()
async def render_dashboard(
    dashboard_id: str,
    format: Literal["pdf", "png"] = "pdf",
    page_id: str | None = None,
    width: int = 1200,
    height: int = 800,
    output_path: str | None = None,
    ctx: Context = CurrentContext(),
) -> dict:
    """Render a dashboard to PDF or PNG image.

    Args:
        dashboard_id: ID of the dashboard to render
        format: Output format - "pdf" or "png"
        page_id: Optional page ID to render (if None, renders all pages)
        width: Viewport width in pixels (for PNG, default: 1200)
        height: Viewport height in pixels (for PNG, default: 800)
        output_path: If provided, save to this file path instead of returning base64.
                     This is more efficient for large renders.

    Returns base64-encoded data with content type, or file path if output_path is set.
    Requires headless Chrome to be running for rendering.
    """
    user = await get_user_from_context(ctx)

    try:
        # Run in thread pool to avoid blocking event loop
        # Chrome loads pages from the same server, which could deadlock otherwise
        result = await asyncio.to_thread(
            render_dashboard_service,
            org_id=user.org_id,
            dashboard_id=dashboard_id,
            page_id=page_id,
            format=format,
            width=width,
            height=height,
        )

        content_type = "application/pdf" if result.format == "pdf" else "image/png"

        # Save to file if output_path is provided
        if output_path:
            with open(output_path, "wb") as f:
                f.write(result.data)
            return {
                "success": True,
                "format": result.format,
                "content_type": content_type,
                "width": result.width,
                "height": result.height,
                "saved_to": output_path,
                "size_bytes": len(result.data),
            }

        return {
            "success": True,
            "format": result.format,
            "content_type": content_type,
            "width": result.width,
            "height": result.height,
            "data_base64": base64.b64encode(result.data).decode("utf-8"),
        }
    except RenderError as e:
        return {"error": str(e)}
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Dashboard render failed: {e}")
        return {"error": f"Failed to render dashboard: {e}"}


@mcp.tool()
async def render_widget(
    dashboard_id: str,
    widget_id: str,
    width: int = 600,
    height: int = 400,
    output_path: str | None = None,
    ctx: Context = CurrentContext(),
) -> dict:
    """Render a single widget to PNG image.

    Args:
        dashboard_id: ID of the dashboard containing the widget
        widget_id: ID of the widget to render
        width: Viewport width in pixels (default: 600)
        height: Viewport height in pixels (default: 400)
        output_path: If provided, save to this file path instead of returning base64.
                     This is more efficient for large renders.

    Returns base64-encoded PNG data, or file path if output_path is set.
    Requires headless Chrome to be running for rendering.
    """
    user = await get_user_from_context(ctx)

    try:
        # Run in thread pool to avoid blocking event loop
        # Chrome loads pages from the same server, which could deadlock otherwise
        result = await asyncio.to_thread(
            render_widget_service,
            org_id=user.org_id,
            dashboard_id=dashboard_id,
            widget_id=widget_id,
            width=width,
            height=height,
        )

        # Save to file if output_path is provided
        if output_path:
            with open(output_path, "wb") as f:
                f.write(result.data)
            return {
                "success": True,
                "format": "png",
                "content_type": "image/png",
                "width": result.width,
                "height": result.height,
                "saved_to": output_path,
                "size_bytes": len(result.data),
            }

        return {
            "success": True,
            "format": "png",
            "content_type": "image/png",
            "width": result.width,
            "height": result.height,
            "data_base64": base64.b64encode(result.data).decode("utf-8"),
        }
    except RenderError as e:
        return {"error": str(e)}
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Widget render failed: {e}")
        return {"error": f"Failed to render widget: {e}"}


# ============================================================================
# Manifest Tools
# ============================================================================

import services.manifest as manifest_service
import services.schedules as schedule_service
import services.quick_metrics as quick_metrics_service


@mcp.tool()
async def get_manifest_status(ctx: Context = CurrentContext()) -> dict:
    """Get status information about the organization's semantic manifest.

    Returns manifest metadata including metric/model/dimension counts.
    """
    user = await get_user_from_context(ctx)

    try:
        status = await manifest_service.get_manifest_status(user)
        return {
            "org_id": status.org_id,
            "project_name": status.project_name,
            "metric_count": status.metric_count,
            "model_count": status.model_count,
            "dimension_count": status.dimension_count,
            "last_updated": status.last_updated,
        }
    except Exception as e:
        return {"error": f"Failed to get manifest status: {e}"}


@mcp.tool()
async def list_semantic_models(ctx: Context = CurrentContext()) -> list[dict]:
    """List all semantic models in the organization.

    Returns models with their names, descriptions, measures, and dimensions.
    """
    user = await get_user_from_context(ctx)

    try:
        return await manifest_service.list_semantic_models(user)
    except Exception as e:
        return [{"error": f"Failed to list semantic models: {e}"}]


@mcp.tool()
async def get_semantic_model(name: str, ctx: Context = CurrentContext()) -> dict:
    """Get detailed information about a semantic model.

    Args:
        name: Name of the semantic model
    """
    user = await get_user_from_context(ctx)

    try:
        return await manifest_service.get_semantic_model(user, name)
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to get semantic model: {e}"}


@mcp.tool()
async def create_semantic_model(model_data: dict, ctx: Context = CurrentContext()) -> dict:
    """Create a new semantic model.

    Args:
        model_data: Semantic model definition with name, measures, dimensions

    Requires admin or owner role.
    """
    user = await get_user_from_context(ctx)

    try:
        result = await manifest_service.create_semantic_model(user, model_data)
        return {"success": True, "model": result}
    except PermissionError as e:
        return {"error": str(e)}
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to create semantic model: {e}"}


@mcp.tool()
async def update_semantic_model(
    name: str,
    updates: dict,
    ctx: Context = CurrentContext(),
) -> dict:
    """Update an existing semantic model.

    Args:
        name: Name of the model to update
        updates: Fields to update

    Requires admin or owner role.
    """
    user = await get_user_from_context(ctx)

    try:
        result = await manifest_service.update_semantic_model(user, name, updates)
        return {"success": True, "model": result}
    except PermissionError as e:
        return {"error": str(e)}
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to update semantic model: {e}"}


@mcp.tool()
async def delete_semantic_model(name: str, ctx: Context = CurrentContext()) -> dict:
    """Delete a semantic model.

    Args:
        name: Name of the model to delete

    Requires admin or owner role. This action cannot be undone.
    """
    user = await get_user_from_context(ctx)

    try:
        await manifest_service.delete_semantic_model(user, name)
        return {"success": True, "message": f"Semantic model '{name}' deleted"}
    except PermissionError as e:
        return {"error": str(e)}
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to delete semantic model: {e}"}


@mcp.tool()
async def create_metric(metric_data: dict, ctx: Context = CurrentContext()) -> dict:
    """Create a new metric.

    Args:
        metric_data: Metric definition with name, type, type_params

    Requires admin or owner role.
    """
    user = await get_user_from_context(ctx)

    try:
        result = await manifest_service.create_metric(user, metric_data)
        return {"success": True, "metric": result}
    except PermissionError as e:
        return {"error": str(e)}
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to create metric: {e}"}


@mcp.tool()
async def update_metric(
    name: str,
    updates: dict,
    ctx: Context = CurrentContext(),
) -> dict:
    """Update an existing metric.

    Args:
        name: Name of the metric to update
        updates: Fields to update

    Requires admin or owner role.
    """
    user = await get_user_from_context(ctx)

    try:
        result = await manifest_service.update_metric(user, name, updates)
        return {"success": True, "metric": result}
    except PermissionError as e:
        return {"error": str(e)}
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to update metric: {e}"}


@mcp.tool()
async def delete_metric(name: str, ctx: Context = CurrentContext()) -> dict:
    """Delete a metric.

    Args:
        name: Name of the metric to delete

    Requires admin or owner role. This action cannot be undone.
    """
    user = await get_user_from_context(ctx)

    try:
        await manifest_service.delete_metric(user, name)
        return {"success": True, "message": f"Metric '{name}' deleted"}
    except PermissionError as e:
        return {"error": str(e)}
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to delete metric: {e}"}


@mcp.tool()
async def import_manifest(
    manifest_data: dict,
    force: bool = False,
    ctx: Context = CurrentContext(),
) -> dict:
    """Import a semantic manifest with fork detection.

    Args:
        manifest_data: Full manifest with metrics and semantic_models
        force: If True, overwrite forked (modified) metrics. If False, fail on conflicts.

    Requires admin or owner role.

    Forked metrics are ones that were imported and then modified by users.
    Without --force, import will fail listing the conflicting items.
    """
    user = await get_user_from_context(ctx)

    try:
        result = await manifest_service.import_manifest(user, manifest_data, force=force)
        return {
            "success": True,
            "imported_metrics": result.imported_metrics,
            "imported_models": result.imported_models,
            "skipped_metrics": result.skipped_metrics,
            "skipped_models": result.skipped_models,
            "conflicts": [
                {"name": c.name, "type": c.type, "reason": c.reason}
                for c in result.conflicts
            ],
            "orphaned": result.orphaned,
        }
    except PermissionError as e:
        return {"error": str(e)}
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to import manifest: {e}"}


@mcp.tool()
async def preview_metric(
    metric_data: dict,
    sample_query: dict | None = None,
    ctx: Context = CurrentContext(),
) -> dict:
    """Preview a metric's query results before saving.

    Args:
        metric_data: Metric definition to preview
        sample_query: Optional query params (start_date, end_date, grain, limit).
                      Defaults to last 7 days, daily grain, limit 5.

    Returns sample query results or validation error.
    """
    user = await get_user_from_context(ctx)

    try:
        return await manifest_service.preview_metric(user, metric_data, sample_query)
    except Exception as e:
        return {"error": f"Failed to preview metric: {e}"}


@mcp.tool()
async def export_manifest(ctx: Context = CurrentContext()) -> dict:
    """Export the organization's semantic manifest.

    Returns the full manifest with metrics, semantic models, and project configuration.
    Internal provenance fields (prefixed with _) are stripped for clean export.

    This is useful for:
    - Backing up your semantic layer configuration
    - Migrating metrics to another organization
    - Version control of your semantic layer
    """
    user = await get_user_from_context(ctx)

    try:
        return await manifest_service.export_manifest(user)
    except Exception as e:
        return {"error": f"Failed to export manifest: {e}"}


# ============================================================================
# Quick Metrics Tools
# ============================================================================


@mcp.tool()
async def create_quick_metric(
    name: str,
    expression: str,
    description: str | None = None,
    ctx: Context = CurrentContext(),
) -> dict:
    """Create a user-defined derived metric from existing metrics.

    Quick metrics let you create calculated metrics using arithmetic expressions.
    They can be queried like regular metrics using the qm: prefix.

    Args:
        name: Metric name (e.g., "revenue_per_order")
        expression: Arithmetic expression using existing metrics
                   (e.g., "total_revenue / order_count")
        description: Optional description

    Examples:
    - Revenue per order: create_quick_metric("revenue_per_order", "total_revenue / order_count")
    - Gross margin %: create_quick_metric("gross_margin_pct", "(total_revenue - cogs) / total_revenue * 100")
    - Average order value: create_quick_metric("aov", "total_revenue / order_count", "Average order value in dollars")

    Once created, query with: query_metrics(metrics=["qm:revenue_per_order"], ...)
    """
    user = await get_user_from_context(ctx)

    try:
        metric = await quick_metrics_service.create_quick_metric(
            user,
            name=name,
            expression=expression,
            description=description,
        )
        return {
            "success": True,
            "quick_metric": {
                "id": metric.id,
                "name": metric.name,
                "expression": metric.expression,
                "description": metric.description,
                "base_metrics": metric.base_metrics,
                "created_at": metric.created_at.isoformat(),
            },
            "usage_hint": f"Query this metric with: qm:{metric.name}",
        }
    except quick_metrics_service.ExpressionError as e:
        return {"error": f"Invalid expression: {e.message}"}
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Failed to create quick metric: {e}")
        return {"error": f"Failed to create quick metric: {e}"}


@mcp.tool()
async def list_quick_metrics(
    ctx: Context = CurrentContext(),
) -> list[dict]:
    """List all quick metrics for your organization.

    Returns quick metrics with their expressions and base metrics.
    Use the qm: prefix when querying (e.g., "qm:revenue_per_order").
    """
    user = await get_user_from_context(ctx)

    try:
        metrics = await quick_metrics_service.list_quick_metrics(user)
        return [
            {
                "id": m.id,
                "name": m.name,
                "description": m.description,
                "expression": m.expression,
                "query_name": f"qm:{m.name}",
            }
            for m in metrics
        ]
    except Exception as e:
        return [{"error": f"Failed to list quick metrics: {e}"}]


@mcp.tool()
async def get_quick_metric(
    metric_id: str,
    ctx: Context = CurrentContext(),
) -> dict:
    """Get details of a quick metric by ID."""
    user = await get_user_from_context(ctx)

    try:
        metric = await quick_metrics_service.get_quick_metric(user, metric_id)
        return {
            "id": metric.id,
            "name": metric.name,
            "description": metric.description,
            "expression": metric.expression,
            "base_metrics": metric.base_metrics,
            "query_name": f"qm:{metric.name}",
            "created_by": metric.created_by,
            "created_at": metric.created_at.isoformat(),
            "updated_at": metric.updated_at.isoformat(),
        }
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to get quick metric: {e}"}


@mcp.tool()
async def update_quick_metric(
    metric_id: str,
    name: str | None = None,
    expression: str | None = None,
    description: str | None = None,
    ctx: Context = CurrentContext(),
) -> dict:
    """Update a quick metric's definition.

    Only provided fields are updated.

    Args:
        metric_id: ID of the quick metric to update
        name: New name (optional)
        expression: New expression (optional)
        description: New description (optional, use empty string to clear)
    """
    user = await get_user_from_context(ctx)

    try:
        metric = await quick_metrics_service.update_quick_metric(
            user,
            metric_id,
            name=name,
            expression=expression,
            description=description,
        )
        return {
            "success": True,
            "quick_metric": {
                "id": metric.id,
                "name": metric.name,
                "expression": metric.expression,
                "description": metric.description,
                "base_metrics": metric.base_metrics,
                "query_name": f"qm:{metric.name}",
                "updated_at": metric.updated_at.isoformat(),
            },
        }
    except quick_metrics_service.ExpressionError as e:
        return {"error": f"Invalid expression: {e.message}"}
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Failed to update quick metric: {e}")
        return {"error": f"Failed to update quick metric: {e}"}


@mcp.tool()
async def delete_quick_metric(
    metric_id: str,
    ctx: Context = CurrentContext(),
) -> dict:
    """Delete a quick metric.

    Args:
        metric_id: ID of the quick metric to delete

    This action cannot be undone.
    """
    user = await get_user_from_context(ctx)

    try:
        await quick_metrics_service.delete_quick_metric(user, metric_id)
        return {"success": True, "message": f"Quick metric '{metric_id}' deleted"}
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Failed to delete quick metric: {e}")
        return {"error": f"Failed to delete quick metric: {e}"}


# ============================================================================
# Schedule Tools (Recurring Reports)
# ============================================================================


@mcp.tool()
async def create_scheduled_report(
    name: str,
    frequency_type: Literal["daily", "weekly", "monthly"],
    time: str,
    recipients: list[str],
    dashboard_id: str | None = None,
    metrics: list[str] | None = None,
    dimensions: list[str] | None = None,
    format: str = "pdf",
    day_of_week: int | None = None,
    day_of_month: int | None = None,
    ctx: Context = CurrentContext(),
) -> dict:
    """Schedule a recurring report to be delivered via email.

    Create either a dashboard report (PDF/PNG) or a query report (CSV/JSON).

    Args:
        name: Schedule name (e.g., "Weekly Sales Report")
        frequency_type: How often to run - "daily", "weekly", or "monthly"
        time: Time to run in HH:MM format (UTC, 24-hour)
        recipients: List of email addresses to send to
        dashboard_id: Dashboard ID for dashboard reports (PDF/PNG)
        metrics: List of metric names for query reports (CSV/JSON)
        dimensions: Dimensions to group by for query reports
        format: Output format - "pdf" or "png" for dashboards, "csv" or "json" for queries
        day_of_week: Day for weekly schedules (0=Monday through 6=Sunday)
        day_of_month: Day for monthly schedules (1-28)

    Examples:
    - Weekly sales dashboard every Monday at 9am:
      create_scheduled_report(name="Weekly Sales", frequency_type="weekly",
                              time="09:00", day_of_week=0, dashboard_id="abc123",
                              recipients=["team@company.com"])

    - Daily revenue metrics CSV:
      create_scheduled_report(name="Daily Revenue", frequency_type="daily",
                              time="08:00", metrics=["total_revenue", "order_count"],
                              format="csv", recipients=["ceo@company.com"])
    """
    from settings import get_settings
    if not get_settings().schedules_enabled:
        return {"error": "Scheduled reports coming soon. This feature is not yet enabled."}

    user = await get_user_from_context(ctx)

    # Validate that either dashboard_id or metrics is provided
    if not dashboard_id and not metrics:
        return {"error": "Either dashboard_id or metrics must be provided"}
    if dashboard_id and metrics:
        return {"error": "Provide either dashboard_id or metrics, not both"}

    try:
        # Build frequency object
        frequency = schedule_service.ScheduleFrequency(
            type=frequency_type,
            time=time,
            day_of_week=day_of_week,
            day_of_month=day_of_month,
        )

        # Build report object
        if dashboard_id:
            if format not in ("pdf", "png"):
                return {"error": f"Invalid format for dashboard report: {format}. Must be 'pdf' or 'png'"}
            report = schedule_service.DashboardReport(
                dashboard_id=dashboard_id,
                format=format,
            )
        else:
            if format not in ("csv", "json"):
                return {"error": f"Invalid format for query report: {format}. Must be 'csv' or 'json'"}
            report = schedule_service.QueryReport(
                metrics=metrics,
                dimensions=dimensions or [],
                format=format,
            )

        # Create schedule
        schedule = await schedule_service.create_schedule(
            user=user,
            name=name,
            frequency=frequency,
            report=report,
            recipients=recipients,
        )

        return {
            "success": True,
            "schedule": {
                "id": schedule.id,
                "name": schedule.name,
                "frequency": schedule.frequency.model_dump(),
                "report": schedule.report.model_dump(),
                "recipients": schedule.recipients,
                "enabled": schedule.enabled,
                "created_at": schedule.created_at.isoformat(),
            },
        }
    except PermissionError as e:
        return {"error": str(e)}
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Failed to create scheduled report: {e}")
        return {"error": f"Failed to create scheduled report: {e}"}


@mcp.tool()
async def list_scheduled_reports(
    ctx: Context = CurrentContext(),
) -> list[dict]:
    """List all scheduled reports for your organization.

    Returns summary information for each schedule including:
    - Name and ID
    - Frequency and timing
    - Report type (dashboard or query)
    - Enabled status
    - Number of recipients
    - Last run status
    """
    from settings import get_settings
    if not get_settings().schedules_enabled:
        return [{"error": "Scheduled reports coming soon. This feature is not yet enabled."}]

    user = await get_user_from_context(ctx)

    try:
        summaries = await schedule_service.list_schedules(user)

        return [
            {
                "id": s.id,
                "name": s.name,
                "frequency_type": s.frequency_type,
                "frequency_time": s.frequency_time,
                "report_type": s.report_type,
                "enabled": s.enabled,
                "recipients_count": s.recipients_count,
                "last_run_at": s.last_run_at.isoformat() if s.last_run_at else None,
                "last_run_status": s.last_run_status,
            }
            for s in summaries
        ]
    except Exception as e:
        return [{"error": f"Failed to list scheduled reports: {e}"}]


@mcp.tool()
async def get_scheduled_report(
    schedule_id: str,
    ctx: Context = CurrentContext(),
) -> dict:
    """Get details of a scheduled report.

    Args:
        schedule_id: ID of the schedule to retrieve

    Returns full schedule details including:
    - Name, frequency, and timing
    - Report configuration (dashboard or query)
    - Recipients list
    - Enabled status
    - Creation and last run information
    """
    from settings import get_settings
    if not get_settings().schedules_enabled:
        return {"error": "Scheduled reports coming soon. This feature is not yet enabled."}

    user = await get_user_from_context(ctx)

    try:
        schedule = await schedule_service.get_schedule(user, schedule_id)

        return {
            "id": schedule.id,
            "name": schedule.name,
            "frequency": schedule.frequency.model_dump(),
            "report": schedule.report.model_dump(),
            "report_type": "dashboard" if isinstance(schedule.report, schedule_service.DashboardReport) else "query",
            "recipients": schedule.recipients,
            "enabled": schedule.enabled,
            "created_by": schedule.created_by,
            "created_at": schedule.created_at.isoformat(),
            "updated_at": schedule.updated_at.isoformat(),
            "last_run_at": schedule.last_run_at.isoformat() if schedule.last_run_at else None,
            "last_run_status": schedule.last_run_status,
        }
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to get scheduled report: {e}"}


@mcp.tool()
async def update_scheduled_report(
    schedule_id: str,
    name: str | None = None,
    enabled: bool | None = None,
    frequency_type: Literal["daily", "weekly", "monthly"] | None = None,
    time: str | None = None,
    day_of_week: int | None = None,
    day_of_month: int | None = None,
    recipients: list[str] | None = None,
    ctx: Context = CurrentContext(),
) -> dict:
    """Update a scheduled report's settings.

    Use enabled=False to pause a schedule without deleting it.

    Args:
        schedule_id: ID of the schedule to update
        name: New schedule name
        enabled: Enable/disable the schedule
        frequency_type: New frequency - "daily", "weekly", or "monthly"
        time: New run time in HH:MM format (UTC)
        day_of_week: Day for weekly schedules (0=Monday through 6=Sunday)
        day_of_month: Day for monthly schedules (1-28)
        recipients: New list of recipient email addresses

    Only provided fields are updated; others remain unchanged.
    You must be the creator or have admin role to update.
    """
    from settings import get_settings
    if not get_settings().schedules_enabled:
        return {"error": "Scheduled reports coming soon. This feature is not yet enabled."}

    user = await get_user_from_context(ctx)

    try:
        updates = {}

        if name is not None:
            updates["name"] = name

        if enabled is not None:
            updates["enabled"] = enabled

        if recipients is not None:
            updates["recipients"] = recipients

        # Build frequency update if any frequency field provided
        if frequency_type is not None or time is not None or day_of_week is not None or day_of_month is not None:
            # Get current schedule to fill in missing fields
            current = await schedule_service.get_schedule(user, schedule_id)
            current_freq = current.frequency

            updates["frequency"] = {
                "type": frequency_type if frequency_type is not None else current_freq.type,
                "time": time if time is not None else current_freq.time,
                "day_of_week": day_of_week if day_of_week is not None else current_freq.day_of_week,
                "day_of_month": day_of_month if day_of_month is not None else current_freq.day_of_month,
            }

        if not updates:
            return {"error": "No updates provided"}

        schedule = await schedule_service.update_schedule(user, schedule_id, updates)

        return {
            "success": True,
            "schedule": {
                "id": schedule.id,
                "name": schedule.name,
                "frequency": schedule.frequency.model_dump(),
                "report": schedule.report.model_dump(),
                "recipients": schedule.recipients,
                "enabled": schedule.enabled,
                "updated_at": schedule.updated_at.isoformat(),
            },
        }
    except PermissionError as e:
        return {"error": str(e)}
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Failed to update scheduled report: {e}")
        return {"error": f"Failed to update scheduled report: {e}"}


@mcp.tool()
async def delete_scheduled_report(
    schedule_id: str,
    ctx: Context = CurrentContext(),
) -> dict:
    """Delete a scheduled report.

    Args:
        schedule_id: ID of the schedule to delete

    You must be the creator or have admin role to delete.
    This action cannot be undone.
    """
    from settings import get_settings
    if not get_settings().schedules_enabled:
        return {"error": "Scheduled reports coming soon. This feature is not yet enabled."}

    user = await get_user_from_context(ctx)

    try:
        await schedule_service.delete_schedule(user, schedule_id)
        return {"success": True, "message": f"Schedule '{schedule_id}' deleted"}
    except PermissionError as e:
        return {"error": str(e)}
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Failed to delete scheduled report: {e}")
        return {"error": f"Failed to delete scheduled report: {e}"}


# ============================================================================
# Server Entry Point
# ============================================================================

# Create the ASGI app for deployment
# Use path="/" so MCP endpoint is at app root (becomes /api/mcp when mounted)
# The _get_resource_url override above ensures resource_url = base_url (no trailing slash)
app = mcp.http_app(path="/")

# Verify OAuth URLs are configured correctly
if auth_provider:
    expected_resource_url = f"{settings.mcp_server_base_url}/mcp"
    actual_resource_url = str(auth_provider._resource_url) if auth_provider._resource_url else None

    logger.info(f"OAuth URL verification:")
    logger.info(f"  base_url: {auth_provider.base_url}")
    logger.info(f"  resource_url: {actual_resource_url}")
    logger.info(f"  expected: {expected_resource_url}")

    if actual_resource_url != expected_resource_url:
        logger.error(
            f"RESOURCE URL MISMATCH! Expected '{expected_resource_url}' but got '{actual_resource_url}'. "
            "Claude.ai OAuth will fail!"
        )
    else:
        logger.info("OAuth URLs configured correctly for Claude.ai integration")


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Starting Metricly MCP Server on port {port}")

    # Run with HTTP transport for remote connections
    uvicorn.run(app, host="0.0.0.0", port=port)
