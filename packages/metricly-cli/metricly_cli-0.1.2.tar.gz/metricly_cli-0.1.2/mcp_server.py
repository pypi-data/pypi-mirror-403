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
    user_data = await ctx.get_state("user")
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
            await context.fastmcp_context.set_state("user", _stdio_user)
            return await call_next(context)

        # Get authenticated user info from OAuth (provided by GoogleProvider)
        if not context.fastmcp_context:
            raise ToolError("Authentication required: no MCP context")

        # Get user info from OAuth authentication state
        # GoogleProvider stores access token info in request state
        try:
            from fastmcp.server.dependencies import get_access_token
            access_token = get_access_token()
        except LookupError:
            raise ToolError("Authentication required: please authenticate via OAuth")

        if not access_token:
            raise ToolError("Authentication required: no access token")

        # Get user email from Google's userinfo endpoint
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            if resp.status_code != 200:
                raise ToolError(f"Failed to get user info from Google: {resp.text}")
            user_info = resp.json()

        email = user_info.get("email")
        if not email:
            raise ToolError("OAuth authentication missing email scope")

        try:
            user = get_user_by_email(email)
        except ValueError as e:
            raise ToolError(f"Access denied: {e}")

        # Store user context in state for tools to access (async in FastMCP 3.0)
        await context.fastmcp_context.set_state("user", user)

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
    logger.info("Configuring Google OAuth for MCP server")
    auth_provider = GoogleProvider(
        client_id=settings.mcp_oauth_client_id,
        client_secret=settings.mcp_oauth_client_secret,
        base_url=f"{settings.mcp_server_base_url}/mcp",
        # Required scopes for user identification
        required_scopes=[
            "openid",
            "https://www.googleapis.com/auth/userinfo.email",
        ],
        # Allow Claude.ai's callback URL
        allowed_client_redirect_uris=[
            "https://claude.ai/api/mcp/auth_callback",
        ],
    )
else:
    logger.warning("MCP OAuth not configured - running without authentication")

mcp = FastMCP(
    "Metricly",
    icon="https://metricly.xyz/logo.svg",
    instructions="""You have access to Metricly, a business intelligence platform.

Use these tools to:
- Query business metrics (revenue, users, churn, etc.)
- List available metrics and dimensions
- View and manage dashboard configurations
- Manage the semantic layer (admins only)

When answering questions about metrics:
1. First use list_metrics to see what's available
2. Use query_metrics to fetch actual data
3. Provide insights based on the results

For dashboard management:
- Use list_dashboards/get_dashboard to view dashboards
- Use create_dashboard/update_dashboard/delete_dashboard to manage dashboards
- Use add_widget/update_widget/remove_widget to manage widgets within dashboards
- Use reorder_widgets to change widget order in a section

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
    dimensions: list[str] | None = Field(default=None, description="Dimensions to group by (e.g., ['customer_segment', 'region'])")
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

    Dimensions are attributes you can group metrics by (e.g., customer_segment, region, product_category).
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
    ctx: Context = CurrentContext(),
) -> dict:
    """Update an existing dashboard.

    Args:
        dashboard_id: ID of the dashboard to update
        title: New title (optional)
        description: New description (optional)
        visibility: New visibility - "private" or "org" (optional)

    Only fields that are provided will be updated.
    You must be the owner of the dashboard to update it.
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
        dashboard = await dashboard_service.update_dashboard(user, dashboard_id, updates)
        return {
            "success": True,
            "dashboard": dashboard.model_dump(),
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
    ctx: Context = CurrentContext(),
) -> dict:
    """Add a widget to a dashboard.

    Args:
        dashboard_id: ID of the dashboard
        widget: Widget definition with type, title, query, etc.
        page_index: Index of the page to add to (default: 0)
        section_index: Index of the section within the page (default: 0)

    Widget definition should include:
    - type: Widget type (kpi, area_chart, bar_chart, line_chart, table, donut)
    - title: Widget title
    - query: Query configuration with metrics, dimensions, etc.
    - format: Optional formatting options

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
        )
        return {
            "success": True,
            "message": f"Widget added to page {page_index}, section {section_index}",
            "dashboard": dashboard.model_dump(),
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
    ctx: Context = CurrentContext(),
) -> dict:
    """Remove a widget from a dashboard.

    Args:
        dashboard_id: ID of the dashboard
        page_index: Index of the page containing the widget
        section_index: Index of the section containing the widget
        widget_index: Index of the widget to remove

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
        )
        return {
            "success": True,
            "message": f"Widget removed from page {page_index}, section {section_index}",
            "dashboard": dashboard.model_dump(),
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
    ctx: Context = CurrentContext(),
) -> dict:
    """Update a specific widget in a dashboard.

    Args:
        dashboard_id: ID of the dashboard
        page_index: Index of the page containing the widget
        section_index: Index of the section containing the widget
        widget_index: Index of the widget to update
        updates: Fields to update (title, query, format, type, etc.)

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
        )
        return {
            "success": True,
            "message": f"Widget updated at page {page_index}, section {section_index}, widget {widget_index}",
            "dashboard": dashboard.model_dump(),
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
    ctx: Context = CurrentContext(),
) -> dict:
    """Reorder widgets within a section.

    Args:
        dashboard_id: ID of the dashboard
        page_index: Index of the page containing the section
        section_index: Index of the section to reorder
        widget_ids: List of widget IDs in the new desired order

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
        )
        return {
            "success": True,
            "message": f"Widgets reordered in page {page_index}, section {section_index}",
            "dashboard": dashboard.model_dump(),
        }
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to reorder widgets: {e}"}


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
        result = render_dashboard_service(
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
        result = render_widget_service(
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
# Server Entry Point
# ============================================================================

# Create the ASGI app for deployment
# Use path="/" since we mount this under /mcp in main.py
app = mcp.http_app(path="/")

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Starting Metricly MCP Server on port {port}")

    # Run with HTTP transport for remote connections
    uvicorn.run(app, host="0.0.0.0", port=port)
