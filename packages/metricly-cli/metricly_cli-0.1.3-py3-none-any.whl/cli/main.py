"""Metricly CLI - Main entry point.

Command-line interface for querying metrics, managing dashboards,
and interacting with the Metricly platform.
"""

import asyncio
import json
from datetime import date
from pathlib import Path
from typing import Annotated, Optional

import typer
import yaml

from cli.auth import CLIAuthManager, AuthenticationError
from cli.output import (
    console,
    format_output,
    print_error,
    print_info,
    print_success,
    print_warning,
    print_user_context,
    print_visualization_suggestion,
    OutputFormat,
)


# Initialize auth manager
auth = CLIAuthManager()

# Initialize main app
app = typer.Typer(
    name="metricly",
    help="Metricly CLI - Query metrics and manage dashboards from the terminal.",
    no_args_is_help=True,
)

# Sub-command groups
metrics_app = typer.Typer(help="Metric operations")
dimensions_app = typer.Typer(help="Dimension operations")
org_app = typer.Typer(help="Organization operations")
dashboards_app = typer.Typer(help="Dashboard operations")
manifest_app = typer.Typer(help="Manifest operations")
models_app = typer.Typer(help="Semantic model operations")

# Register sub-command groups
app.add_typer(metrics_app, name="metrics")
app.add_typer(dimensions_app, name="dimensions")
app.add_typer(org_app, name="org")
app.add_typer(dashboards_app, name="dashboards")
app.add_typer(manifest_app, name="manifest")
app.add_typer(models_app, name="models")


# ============================================================================
# Helpers
# ============================================================================


def run_async(coro):
    """Run an async function synchronously."""
    return asyncio.run(coro)


def require_auth():
    """Get authenticated user or exit with error.

    Returns:
        UserContext for authenticated user

    Raises:
        typer.Exit: If not authenticated
    """
    try:
        return run_async(auth.get_user())
    except AuthenticationError as e:
        print_error(str(e), hint="Run 'metricly login' to authenticate")
        raise typer.Exit(1)


# ============================================================================
# Top-level commands
# ============================================================================


@app.command()
def version():
    """Show CLI version."""
    from importlib.metadata import version as get_version
    try:
        v = get_version("metricly-cli")
    except Exception:
        v = "unknown"
    console.print(f"[bold]Metricly CLI[/] v{v}")


@app.command()
def login():
    """Login via Google OAuth.

    Opens a browser window to authenticate with Google.
    Your credentials are stored locally in ~/.metricly/credentials.json.
    """
    if auth.is_logged_in():
        email = auth.get_stored_email()
        print_info(f"Already logged in as {email}")
        print_info("Run 'metricly logout' first to switch accounts")
        return

    try:
        user = run_async(auth.login())
        print_success(f"Logged in as {user.email}")
        print_info(f"Organization: {user.org_id} ({user.role})")
    except AuthenticationError as e:
        print_error(str(e))
        raise typer.Exit(1)
    except Exception as e:
        print_error(f"Login failed: {e}")
        raise typer.Exit(1)


@app.command()
def logout():
    """Logout and clear stored credentials."""
    if not auth.is_logged_in():
        print_info("Not logged in")
        return

    email = auth.get_stored_email()
    run_async(auth.logout())
    print_success(f"Logged out {email}")


@app.command()
def whoami():
    """Show current user and organization."""
    user = require_auth()
    print_user_context(
        email=user.email,
        org_id=user.org_id,
        role=user.role,
        org_name=user.org_name,
    )


@app.command()
def query(
    metrics: Annotated[
        list[str],
        typer.Option("-m", "--metrics", help="Metric names to query"),
    ],
    dimensions: Annotated[
        Optional[list[str]],
        typer.Option("-d", "--dimensions", help="Dimensions to group by"),
    ] = None,
    grain: Annotated[
        Optional[str],
        typer.Option("-g", "--grain", help="Time grain: day, week, month, quarter, year"),
    ] = None,
    start_date: Annotated[
        Optional[str],
        typer.Option("--start", help="Start date (YYYY-MM-DD)"),
    ] = None,
    end_date: Annotated[
        Optional[str],
        typer.Option("--end", help="End date (YYYY-MM-DD)"),
    ] = None,
    limit: Annotated[
        Optional[int],
        typer.Option("--limit", help="Maximum rows to return"),
    ] = None,
    order_by: Annotated[
        Optional[str],
        typer.Option("--order-by", help="Column to sort by (append ' desc' for descending)"),
    ] = None,
    suggest_viz: Annotated[
        bool,
        typer.Option("--suggest-viz", help="Suggest a visualization type"),
    ] = False,
    format: Annotated[
        OutputFormat,
        typer.Option("--format", "-f", help="Output format"),
    ] = "table",
):
    """Query metrics from your data warehouse.

    Examples:
        metricly query -m total_revenue -g month
        metricly query -m revenue -d region --limit 10
        metricly query -m revenue -m orders --start 2024-01-01 --end 2024-12-31
    """
    user = require_auth()

    # Import services (deferred to avoid import issues)
    from services.queries import QueryParams, query_metrics

    # Parse dates
    parsed_start = None
    parsed_end = None
    if start_date:
        try:
            parsed_start = date.fromisoformat(start_date)
        except ValueError:
            print_error(f"Invalid start date: {start_date}", hint="Use YYYY-MM-DD format")
            raise typer.Exit(1)
    if end_date:
        try:
            parsed_end = date.fromisoformat(end_date)
        except ValueError:
            print_error(f"Invalid end date: {end_date}", hint="Use YYYY-MM-DD format")
            raise typer.Exit(1)

    # Build query params
    params = QueryParams(
        metrics=metrics,
        dimensions=dimensions,
        grain=grain,
        start_date=parsed_start,
        end_date=parsed_end,
        limit=limit,
        order_by=order_by,
    )

    try:
        result = run_async(
            query_metrics(
                org_id=user.org_id,
                params=params,
                include_visualization=suggest_viz,
            )
        )

        # Format output
        format_output(
            result.data,
            format=format,
            columns=result.columns,
            title=f"Query Results ({result.row_count} rows)",
        )

        # Show visualization suggestion if requested
        if suggest_viz and result.visualization:
            print_visualization_suggestion(
                result.visualization.widget_type,
                result.visualization.rationale,
            )

    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)
    except Exception as e:
        print_error(f"Query failed: {e}")
        raise typer.Exit(1)


# ============================================================================
# Metrics sub-commands
# ============================================================================


@metrics_app.command("list")
def metrics_list(
    format: Annotated[
        OutputFormat,
        typer.Option("--format", "-f", help="Output format"),
    ] = "table",
):
    """List available metrics."""
    user = require_auth()

    from services.queries import list_metrics

    try:
        metrics = run_async(list_metrics(user.org_id))
        format_output(
            metrics,
            format=format,
            columns=["name", "type", "description"],
            title="Available Metrics",
        )
    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)


@metrics_app.command("show")
def metrics_show(
    name: Annotated[str, typer.Argument(help="Metric name")],
    format: Annotated[
        OutputFormat,
        typer.Option("--format", "-f", help="Output format"),
    ] = "table",
):
    """Show details for a specific metric."""
    user = require_auth()

    from services.queries import explain_metric

    try:
        metric = run_async(explain_metric(user.org_id, name))
        format_output(metric, format=format, title=f"Metric: {name}")
    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)


@metrics_app.command("create")
def metrics_create(
    file: Annotated[Path, typer.Argument(help="Path to YAML or JSON file with metric definition")],
    format: Annotated[
        OutputFormat,
        typer.Option("--format", "-f", help="Output format"),
    ] = "table",
):
    """Create a new metric from a YAML or JSON file.

    The file should contain a metric definition with at least:
    - name: Unique metric name
    - type: Metric type (simple, derived, cumulative)
    - type_params: Type-specific parameters

    Examples:
        metricly metrics create metric.yaml
        metricly metrics create metric.json --format json
    """
    user = require_auth()

    from services.manifest import create_metric

    metric_data = load_definition_file(file)

    try:
        metric = run_async(create_metric(user, metric_data))
        print_success(f"Created metric: {metric.get('name')}")
        format_output(metric, format=format, title="New Metric")
    except PermissionError as e:
        print_error(str(e), hint="You need admin role to create metrics")
        raise typer.Exit(1)
    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)


@metrics_app.command("update")
def metrics_update(
    name: Annotated[str, typer.Argument(help="Name of the metric to update")],
    file: Annotated[Path, typer.Argument(help="Path to YAML or JSON file with updates")],
    format: Annotated[
        OutputFormat,
        typer.Option("--format", "-f", help="Output format"),
    ] = "table",
):
    """Update an existing metric from a YAML or JSON file.

    The file should contain the fields to update. The metric name
    cannot be changed.

    Examples:
        metricly metrics update total_revenue updates.yaml
        metricly metrics update total_revenue updates.json --format json
    """
    user = require_auth()

    from services.manifest import update_metric

    updates = load_definition_file(file)

    try:
        metric = run_async(update_metric(user, name, updates))
        print_success(f"Updated metric: {name}")
        format_output(metric, format=format, title="Updated Metric")
    except PermissionError as e:
        print_error(str(e), hint="You need admin role to update metrics")
        raise typer.Exit(1)
    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)


@metrics_app.command("delete")
def metrics_delete(
    name: Annotated[str, typer.Argument(help="Name of the metric to delete")],
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Skip confirmation prompt"),
    ] = False,
):
    """Delete a metric.

    Requires confirmation unless --yes is passed.
    You need admin role to delete metrics.

    Examples:
        metricly metrics delete total_revenue
        metricly metrics delete total_revenue --yes
    """
    user = require_auth()

    from services.manifest import delete_metric, get_metric

    try:
        # First get the metric to confirm it exists
        metric = run_async(get_metric(user, name))

        # Confirm deletion
        if not yes:
            metric_type = metric.get("type", "unknown")
            confirm = typer.confirm(
                f"Delete metric '{name}' (type: {metric_type})?"
            )
            if not confirm:
                print_info("Cancelled")
                raise typer.Exit(0)

        # Delete it
        run_async(delete_metric(user, name))
        print_success(f"Deleted metric: {name}")

    except PermissionError as e:
        print_error(str(e), hint="You need admin role to delete metrics")
        raise typer.Exit(1)
    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)


@metrics_app.command("preview")
def metrics_preview(
    file: Annotated[Path, typer.Argument(help="Path to YAML or JSON file with metric definition")],
    limit: Annotated[
        int,
        typer.Option("--limit", "-l", help="Maximum rows to return"),
    ] = 5,
    grain: Annotated[
        Optional[str],
        typer.Option("--grain", "-g", help="Time grain: day, week, month"),
    ] = "day",
    format: Annotated[
        OutputFormat,
        typer.Option("--format", "-f", help="Output format"),
    ] = "table",
):
    """Preview a metric's query results before saving.

    Runs a sample query using the metric definition from the file
    without persisting the metric. Useful for validating that the
    metric definition is correct before creating it.

    Examples:
        metricly metrics preview metric.yaml
        metricly metrics preview metric.json --limit 10 --grain week
    """
    user = require_auth()

    from services.manifest import preview_metric

    metric_data = load_definition_file(file)
    metric_name = metric_data.get("name", "unknown")
    print_info(f"Previewing metric: {metric_name}")

    try:
        sample_query = {"grain": grain, "limit": limit}
        result = run_async(preview_metric(user, metric_data, sample_query))

        if "error" in result:
            print_error(f"Preview failed: {result['error']}")
            raise typer.Exit(1)

        # Format output like the query command
        format_output(
            result["data"],
            format=format,
            columns=result.get("columns"),
            title=f"Preview Results ({result.get('row_count', 0)} rows)",
        )

        print_success("Metric definition is valid")

    except Exception as e:
        print_error(f"Preview failed: {e}")
        raise typer.Exit(1)


# ============================================================================
# Dimensions sub-commands
# ============================================================================


@dimensions_app.command("list")
def dimensions_list(
    format: Annotated[
        OutputFormat,
        typer.Option("--format", "-f", help="Output format"),
    ] = "table",
):
    """List available dimensions."""
    user = require_auth()

    from services.queries import list_dimensions

    try:
        dimensions = run_async(list_dimensions(user.org_id))
        format_output(
            dimensions,
            format=format,
            columns=["name"],
            title="Available Dimensions",
        )
    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)


# ============================================================================
# Org sub-commands
# ============================================================================


@org_app.command("list")
def org_list(
    format: Annotated[
        OutputFormat,
        typer.Option("--format", "-f", help="Output format"),
    ] = "table",
):
    """List organizations you belong to."""
    # Need email but not full auth for this
    if not auth.is_logged_in():
        print_error("Not logged in", hint="Run 'metricly login' first")
        raise typer.Exit(1)

    email = auth.get_stored_email()
    if not email:
        print_error("No stored email", hint="Run 'metricly login' again")
        raise typer.Exit(1)

    from services.auth import get_user_orgs

    try:
        orgs = get_user_orgs(email)
        format_output(
            orgs,
            format=format,
            columns=["id", "name", "role", "current"],
            title="Your Organizations",
        )
    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)


@org_app.command("switch")
def org_switch(
    org_id: Annotated[str, typer.Argument(help="Organization ID to switch to")],
):
    """Switch to a different organization."""
    if not auth.is_logged_in():
        print_error("Not logged in", hint="Run 'metricly login' first")
        raise typer.Exit(1)

    email = auth.get_stored_email()
    if not email:
        print_error("No stored email", hint="Run 'metricly login' again")
        raise typer.Exit(1)

    from services.auth import switch_org

    try:
        user = switch_org(email, org_id)
        print_success(f"Switched to organization: {org_id}")
        print_info(f"Role: {user.role}")
    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)


# ============================================================================
# Dashboards sub-commands
# ============================================================================


@dashboards_app.command("list")
def dashboards_list(
    format: Annotated[
        OutputFormat,
        typer.Option("--format", "-f", help="Output format"),
    ] = "table",
):
    """List your dashboards (personal and team).

    Shows dashboards you own (personal) and dashboards shared with
    your organization (team).
    """
    user = require_auth()

    from services.dashboards import list_dashboards

    try:
        result = run_async(list_dashboards(user))

        # Combine personal and team dashboards for output
        all_dashboards = []

        for d in result.personal:
            all_dashboards.append({
                "id": d.id,
                "title": d.title,
                "visibility": d.visibility,
                "owner": "you",
                "updated_at": d.updated_at,
            })

        for d in result.team:
            all_dashboards.append({
                "id": d.id,
                "title": d.title,
                "visibility": d.visibility,
                "owner": d.owner,
                "updated_at": d.updated_at,
            })

        if not all_dashboards:
            print_info("No dashboards found")
            print_info("Create one with: metricly dashboards create 'My Dashboard'")
            return

        format_output(
            all_dashboards,
            format=format,
            columns=["id", "title", "visibility", "owner", "updated_at"],
            title="Dashboards",
        )
    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)


@dashboards_app.command("show")
def dashboards_show(
    dashboard_id: Annotated[str, typer.Argument(help="Dashboard ID")],
    format: Annotated[
        OutputFormat,
        typer.Option("--format", "-f", help="Output format"),
    ] = "table",
):
    """Show details for a specific dashboard.

    Displays dashboard metadata and page/widget structure.
    """
    user = require_auth()

    from services.dashboards import get_dashboard

    try:
        dashboard = run_async(get_dashboard(user, dashboard_id))

        if format == "json":
            format_output(dashboard.model_dump(), format=format)
        else:
            # Build summary for table format
            summary = {
                "id": dashboard.id,
                "title": dashboard.title,
                "description": dashboard.description or "-",
                "visibility": dashboard.visibility,
                "owner": dashboard.owner,
                "created_at": dashboard.created_at,
                "updated_at": dashboard.updated_at,
                "pages": len(dashboard.pages),
            }

            # Count total widgets
            widget_count = 0
            for page in dashboard.pages:
                for section in page.sections:
                    widget_count += len(section.widgets)
            summary["widgets"] = widget_count

            format_output(summary, format=format, title=f"Dashboard: {dashboard.title}")

            # Show page structure in table format
            if dashboard.pages:
                console.print()
                pages_data = []
                for i, page in enumerate(dashboard.pages):
                    section_count = len(page.sections)
                    widget_count = sum(len(s.widgets) for s in page.sections)
                    pages_data.append({
                        "index": i,
                        "title": page.title,
                        "sections": section_count,
                        "widgets": widget_count,
                    })
                format_output(
                    pages_data,
                    format="table",
                    columns=["index", "title", "sections", "widgets"],
                    title="Pages",
                )

    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)


@dashboards_app.command("create")
def dashboards_create(
    title: Annotated[str, typer.Argument(help="Dashboard title")],
    description: Annotated[
        Optional[str],
        typer.Option("--description", "-d", help="Dashboard description"),
    ] = None,
    visibility: Annotated[
        str,
        typer.Option(
            "--visibility",
            "-v",
            help="Visibility: 'private' (only you) or 'org' (team)",
        ),
    ] = "private",
    format: Annotated[
        OutputFormat,
        typer.Option("--format", "-f", help="Output format"),
    ] = "table",
):
    """Create a new dashboard.

    Examples:
        metricly dashboards create "Sales Overview"
        metricly dashboards create "Team Metrics" -v org -d "Shared team dashboard"
    """
    user = require_auth()

    # Validate visibility
    if visibility not in ("private", "org"):
        print_error(
            f"Invalid visibility: {visibility}",
            hint="Use 'private' or 'org'",
        )
        raise typer.Exit(1)

    from services.dashboards import create_dashboard

    try:
        dashboard = run_async(
            create_dashboard(
                user,
                title=title,
                description=description,
                visibility=visibility,  # type: ignore
            )
        )

        print_success(f"Created dashboard: {dashboard.title}")

        summary = {
            "id": dashboard.id,
            "title": dashboard.title,
            "description": dashboard.description or "-",
            "visibility": dashboard.visibility,
        }
        format_output(summary, format=format, title="New Dashboard")

    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)


@dashboards_app.command("delete")
def dashboards_delete(
    dashboard_id: Annotated[str, typer.Argument(help="Dashboard ID to delete")],
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Skip confirmation prompt"),
    ] = False,
):
    """Delete a dashboard.

    Requires confirmation unless --yes is passed.
    You can only delete dashboards you own.
    """
    user = require_auth()

    from services.dashboards import get_dashboard, delete_dashboard

    try:
        # First get the dashboard to show its title
        dashboard = run_async(get_dashboard(user, dashboard_id))

        # Confirm deletion
        if not yes:
            confirm = typer.confirm(
                f"Delete dashboard '{dashboard.title}' ({dashboard_id})?"
            )
            if not confirm:
                print_info("Cancelled")
                raise typer.Exit(0)

        # Delete it
        run_async(delete_dashboard(user, dashboard_id))
        print_success(f"Deleted dashboard: {dashboard.title}")

    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)


@dashboards_app.command("render")
def dashboards_render(
    dashboard_id: Annotated[str, typer.Argument(help="Dashboard ID to render")],
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="Output file path"),
    ],
    page: Annotated[
        str | None,
        typer.Option("--page", "-p", help="Page ID to render (default: all pages)"),
    ] = None,
    format: Annotated[
        str,
        typer.Option("--format", "-f", help="Output format: pdf or png"),
    ] = "pdf",
    width: Annotated[
        int,
        typer.Option("--width", "-w", help="Render width in pixels"),
    ] = 1200,
    height: Annotated[
        int,
        typer.Option("--height", "-h", help="Render height in pixels"),
    ] = 800,
):
    """Render a dashboard to PDF or PNG.

    Exports a dashboard as a static file for sharing or archiving.

    Examples:
        metricly dashboards render abc123 --output sales.pdf
        metricly dashboards render abc123 --output sales.png --format png
        metricly dashboards render abc123 --page overview -o overview.pdf
        metricly dashboards render abc123 -o report.pdf --width 1400 --height 900
    """
    import httpx
    from settings import get_settings

    # Validate format
    format_lower = format.lower()
    if format_lower not in ("pdf", "png"):
        print_error(
            f"Invalid format: {format}",
            hint="Use 'pdf' or 'png'",
        )
        raise typer.Exit(1)

    # Ensure output has correct extension
    output_path = output
    expected_ext = f".{format_lower}"
    if output_path.suffix.lower() != expected_ext:
        output_path = output_path.with_suffix(expected_ext)
        print_warning(f"Output file extension adjusted to {output_path.name}")

    # Get access token
    try:
        token = auth.get_access_token()
    except Exception as e:
        print_error(str(e), hint="Run 'metricly login' to authenticate")
        raise typer.Exit(1)

    # Get API base URL from settings
    settings = get_settings()
    api_base = settings.mcp_server_base_url

    # Build request URL
    url = f"{api_base}/api/render/dashboard/{dashboard_id}"

    if page:
        print_info(f"Rendering page '{page}' from dashboard {dashboard_id}...")
    else:
        print_info(f"Rendering dashboard {dashboard_id} (all pages)...")

    try:
        # Make authenticated API call
        with httpx.Client(timeout=120.0) as client:
            request_body = {
                "format": format_lower,
                "width": width,
                "height": height,
            }
            if page:
                request_body["page_id"] = page

            response = client.post(
                url,
                headers={"Authorization": f"Bearer {token}"},
                json=request_body,
            )

            if response.status_code == 401:
                print_error("Authentication failed", hint="Run 'metricly login' to re-authenticate")
                raise typer.Exit(1)
            elif response.status_code == 403:
                print_error("Access denied", hint="You don't have permission to render this dashboard")
                raise typer.Exit(1)
            elif response.status_code == 404:
                print_error(f"Dashboard not found: {dashboard_id}")
                raise typer.Exit(1)
            elif response.status_code != 200:
                error_detail = response.text
                try:
                    error_json = response.json()
                    error_detail = error_json.get("detail", error_detail)
                except Exception:
                    pass
                print_error(f"Render failed: {error_detail}")
                raise typer.Exit(1)

            # Save binary response to file
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(response.content)

            # Calculate file size for display
            file_size = len(response.content)
            if file_size >= 1024 * 1024:
                size_str = f"{file_size / (1024 * 1024):.1f} MB"
            elif file_size >= 1024:
                size_str = f"{file_size / 1024:.1f} KB"
            else:
                size_str = f"{file_size} bytes"

            print_success(f"Saved {format_lower.upper()} to {output_path}")
            print_info(f"File size: {size_str}")

    except httpx.TimeoutException:
        print_error("Request timed out", hint="The dashboard may be too large. Try increasing timeout.")
        raise typer.Exit(1)
    except httpx.RequestError as e:
        print_error(f"Network error: {e}")
        raise typer.Exit(1)


@dashboards_app.command("render-widget")
def dashboards_render_widget(
    dashboard_id: Annotated[str, typer.Argument(help="Dashboard ID containing the widget")],
    widget_id: Annotated[str, typer.Argument(help="Widget ID to render")],
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="Output file path"),
    ],
    width: Annotated[
        int,
        typer.Option("--width", "-w", help="Render width in pixels"),
    ] = 600,
    height: Annotated[
        int,
        typer.Option("--height", "-h", help="Render height in pixels"),
    ] = 400,
):
    """Render a single widget to PNG.

    Exports a widget as a standalone PNG image.

    Examples:
        metricly dashboards render-widget abc123 kpi-revenue --output revenue.png
        metricly dashboards render-widget abc123 chart-1 -o chart.png --width 800 --height 600
    """
    import httpx
    from settings import get_settings

    # Ensure output has .png extension
    output_path = output
    if output_path.suffix.lower() != ".png":
        output_path = output_path.with_suffix(".png")
        print_warning(f"Output file extension adjusted to {output_path.name}")

    # Get access token
    try:
        token = auth.get_access_token()
    except Exception as e:
        print_error(str(e), hint="Run 'metricly login' to authenticate")
        raise typer.Exit(1)

    # Get API base URL from settings
    settings = get_settings()
    api_base = settings.mcp_server_base_url

    # Build request URL
    url = f"{api_base}/api/render/widget/{dashboard_id}/{widget_id}"

    print_info(f"Rendering widget {widget_id}...")

    try:
        # Make authenticated API call
        with httpx.Client(timeout=120.0) as client:
            response = client.post(
                url,
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "width": width,
                    "height": height,
                },
            )

            if response.status_code == 401:
                print_error("Authentication failed", hint="Run 'metricly login' to re-authenticate")
                raise typer.Exit(1)
            elif response.status_code == 403:
                print_error("Access denied", hint="You don't have permission to render this widget")
                raise typer.Exit(1)
            elif response.status_code == 404:
                print_error(f"Dashboard or widget not found: {dashboard_id}/{widget_id}")
                raise typer.Exit(1)
            elif response.status_code != 200:
                error_detail = response.text
                try:
                    error_json = response.json()
                    error_detail = error_json.get("detail", error_detail)
                except Exception:
                    pass
                print_error(f"Render failed: {error_detail}")
                raise typer.Exit(1)

            # Save binary response to file
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(response.content)

            # Calculate file size for display
            file_size = len(response.content)
            if file_size >= 1024 * 1024:
                size_str = f"{file_size / (1024 * 1024):.1f} MB"
            elif file_size >= 1024:
                size_str = f"{file_size / 1024:.1f} KB"
            else:
                size_str = f"{file_size} bytes"

            print_success(f"Saved PNG to {output_path}")
            print_info(f"File size: {size_str}")

    except httpx.TimeoutException:
        print_error("Request timed out", hint="The widget may be too complex. Try increasing timeout.")
        raise typer.Exit(1)
    except httpx.RequestError as e:
        print_error(f"Network error: {e}")
        raise typer.Exit(1)


# ============================================================================
# Manifest sub-commands
# ============================================================================


@manifest_app.command("status")
def manifest_status(
    format: Annotated[
        OutputFormat,
        typer.Option("--format", "-f", help="Output format"),
    ] = "table",
):
    """Show manifest status (project name, counts).

    Displays information about the organization's semantic layer manifest
    including project name, metric count, model count, and dimension count.
    """
    user = require_auth()

    from services.manifest import get_manifest_status

    try:
        status = run_async(get_manifest_status(user))

        summary = {
            "organization": status.org_id,
            "project": status.project_name or "-",
            "metrics": status.metric_count,
            "models": status.model_count,
            "dimensions": status.dimension_count,
            "last_updated": status.last_updated or "-",
        }

        format_output(summary, format=format, title="Manifest Status")

    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)


@manifest_app.command("upload")
def manifest_upload(
    file: Annotated[
        str,
        typer.Argument(help="Path to manifest file (YAML or JSON)"),
    ],
    force: Annotated[
        bool,
        typer.Option("--force", help="Overwrite forked items without confirmation"),
    ] = False,
    format: Annotated[
        OutputFormat,
        typer.Option("--format", "-f", help="Output format"),
    ] = "table",
):
    """Upload a manifest file (YAML or JSON).

    Imports metrics and semantic models from a manifest file into the
    organization's semantic layer. Supports both YAML and JSON formats.

    Fork detection: If any metrics or models have been modified since
    their last import, they are considered "forked". Without --force,
    the upload will fail listing the conflicting items. With --force,
    forked items will be overwritten.

    Examples:
        metricly manifest upload manifest.yaml
        metricly manifest upload manifest.json --force
    """
    user = require_auth()

    from services.manifest import import_manifest

    # Validate file exists
    file_path = Path(file)
    if not file_path.exists():
        print_error(f"File not found: {file}")
        raise typer.Exit(1)

    # Determine format from extension
    ext = file_path.suffix.lower()
    if ext in (".yaml", ".yml"):
        try:
            with open(file_path) as f:
                manifest_data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            print_error(f"Invalid YAML: {e}")
            raise typer.Exit(1)
    elif ext == ".json":
        try:
            with open(file_path) as f:
                manifest_data = json.load(f)
        except json.JSONDecodeError as e:
            print_error(f"Invalid JSON: {e}")
            raise typer.Exit(1)
    else:
        print_error(
            f"Unsupported file format: {ext}",
            hint="Use .yaml, .yml, or .json",
        )
        raise typer.Exit(1)

    try:
        result = run_async(import_manifest(user, manifest_data, force=force))

        # Show conflicts if any (with --force they were overwritten)
        if result.conflicts:
            if force:
                print_warning(f"Overwrote {len(result.conflicts)} forked items:")
                for conflict in result.conflicts:
                    console.print(f"  - {conflict.name} ({conflict.type})")
            # Without force, import_manifest raises ValueError

        # Show orphaned items if any
        if result.orphaned:
            print_warning(f"{len(result.orphaned)} items no longer in manifest:")
            for name in result.orphaned:
                console.print(f"  - {name}")

        # Show summary
        summary = {
            "imported_metrics": result.imported_metrics,
            "imported_models": result.imported_models,
            "skipped_metrics": result.skipped_metrics,
            "skipped_models": result.skipped_models,
            "conflicts": len(result.conflicts),
        }

        print_success(f"Manifest uploaded from {file}")
        format_output(summary, format=format, title="Import Summary")

    except PermissionError as e:
        print_error(str(e), hint="You need admin or owner role")
        raise typer.Exit(1)
    except ValueError as e:
        # Conflict error - show details
        error_msg = str(e)
        if "forked items" in error_msg:
            print_error("Upload blocked due to forked items")
            print_info("The following items have been modified since their last import:")
            # Parse conflict names from error message
            if "Items:" in error_msg:
                items_part = error_msg.split("Items:")[1].split(".")[0].strip()
                for item in items_part.split(","):
                    console.print(f"  - {item.strip()}")
            print_info("Use --force to overwrite these items")
        else:
            print_error(error_msg)
        raise typer.Exit(1)


@manifest_app.command("export")
def manifest_export(
    output: Annotated[
        str,
        typer.Option("--output", "-o", help="Output file path (YAML or JSON)"),
    ],
):
    """Export manifest to a file.

    Exports the organization's semantic layer manifest to a YAML or JSON
    file. The format is determined by the file extension.

    Examples:
        metricly manifest export -o manifest.yaml
        metricly manifest export --output backup.json
    """
    user = require_auth()

    from services.manifest import export_manifest

    # Determine format from extension
    output_path = Path(output)
    ext = output_path.suffix.lower()

    if ext not in (".yaml", ".yml", ".json"):
        print_error(
            f"Unsupported file format: {ext}",
            hint="Use .yaml, .yml, or .json",
        )
        raise typer.Exit(1)

    try:
        manifest = run_async(export_manifest(user))

        # Check if manifest is empty
        if not manifest.get("metrics") and not manifest.get("semantic_models"):
            print_warning("Manifest is empty (no metrics or models)")

        # Write to file
        if ext in (".yaml", ".yml"):
            with open(output_path, "w") as f:
                yaml.dump(manifest, f, default_flow_style=False, sort_keys=False)
        else:
            with open(output_path, "w") as f:
                json.dump(manifest, f, indent=2)

        # Count items
        metric_count = len(manifest.get("metrics", []))
        model_count = len(manifest.get("semantic_models", []))

        print_success(f"Exported manifest to {output}")
        print_info(f"  Metrics: {metric_count}")
        print_info(f"  Models: {model_count}")

    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)


# ============================================================================
# Models sub-commands
# ============================================================================


def load_definition_file(file: Path) -> dict:
    """Load a model definition from YAML or JSON file.

    Args:
        file: Path to the definition file

    Returns:
        Parsed definition dictionary

    Raises:
        typer.Exit: If file not found or parsing fails
    """
    if not file.exists():
        print_error(f"File not found: {file}")
        raise typer.Exit(1)

    try:
        content = file.read_text()
        if file.suffix in (".yaml", ".yml"):
            return yaml.safe_load(content)
        return json.loads(content)
    except yaml.YAMLError as e:
        print_error(f"Invalid YAML: {e}")
        raise typer.Exit(1)
    except json.JSONDecodeError as e:
        print_error(f"Invalid JSON: {e}")
        raise typer.Exit(1)


@models_app.command("list")
def models_list(
    format: Annotated[
        OutputFormat,
        typer.Option("--format", "-f", help="Output format"),
    ] = "table",
):
    """List semantic models.

    Shows all semantic models with their name, description,
    measure count, and dimension count.
    """
    user = require_auth()

    from services.manifest import list_semantic_models

    try:
        models = run_async(list_semantic_models(user))

        if not models:
            print_info("No semantic models found")
            return

        # Build summary data for display
        model_data = []
        for model in models:
            model_data.append({
                "name": model.get("name", "-"),
                "description": model.get("description", "-") or "-",
                "measures": len(model.get("measures", [])),
                "dimensions": len(model.get("dimensions", [])),
            })

        format_output(
            model_data,
            format=format,
            columns=["name", "description", "measures", "dimensions"],
            title="Semantic Models",
        )
    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)


@models_app.command("show")
def models_show(
    name: Annotated[str, typer.Argument(help="Model name")],
    format: Annotated[
        OutputFormat,
        typer.Option("--format", "-f", help="Output format"),
    ] = "table",
):
    """Show details for a semantic model.

    Displays full model definition including all measures and dimensions.
    """
    user = require_auth()

    from services.manifest import get_semantic_model

    try:
        model = run_async(get_semantic_model(user, name))

        if format == "json":
            format_output(model, format=format)
        elif format == "yaml":
            format_output(model, format=format)
        else:
            # Show model summary
            summary = {
                "name": model.get("name", "-"),
                "description": model.get("description", "-") or "-",
                "model_ref": model.get("model", "-"),
                "measures": len(model.get("measures", [])),
                "dimensions": len(model.get("dimensions", [])),
            }
            format_output(summary, format=format, title=f"Model: {name}")

            # Show measures
            measures = model.get("measures", [])
            if measures:
                console.print()
                measures_data = []
                for m in measures:
                    measures_data.append({
                        "name": m.get("name", "-"),
                        "type": m.get("type", "-"),
                        "expr": m.get("expr", "-"),
                    })
                format_output(
                    measures_data,
                    format="table",
                    columns=["name", "type", "expr"],
                    title="Measures",
                )

            # Show dimensions
            dimensions = model.get("dimensions", [])
            if dimensions:
                console.print()
                dims_data = []
                for d in dimensions:
                    dims_data.append({
                        "name": d.get("name", "-"),
                        "type": d.get("type", "-"),
                        "expr": d.get("expr", "-"),
                    })
                format_output(
                    dims_data,
                    format="table",
                    columns=["name", "type", "expr"],
                    title="Dimensions",
                )

    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)


@models_app.command("create")
def models_create(
    file: Annotated[Path, typer.Argument(help="YAML or JSON file with model definition")],
    format: Annotated[
        OutputFormat,
        typer.Option("--format", "-f", help="Output format"),
    ] = "table",
):
    """Create a semantic model from a file.

    Requires admin role. The file must be YAML or JSON with a valid
    semantic model definition.

    Examples:
        metricly models create orders.yaml
        metricly models create model.json
    """
    user = require_auth()

    from services.manifest import create_semantic_model

    model_data = load_definition_file(file)

    try:
        model = run_async(create_semantic_model(user, model_data))
        print_success(f"Created semantic model: {model.get('name')}")

        summary = {
            "name": model.get("name", "-"),
            "measures": len(model.get("measures", [])),
            "dimensions": len(model.get("dimensions", [])),
        }
        format_output(summary, format=format, title="New Model")

    except PermissionError as e:
        print_error(str(e), hint="Admin role required")
        raise typer.Exit(1)
    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)


@models_app.command("update")
def models_update(
    name: Annotated[str, typer.Argument(help="Model name to update")],
    file: Annotated[Path, typer.Argument(help="YAML or JSON file with updates")],
    format: Annotated[
        OutputFormat,
        typer.Option("--format", "-f", help="Output format"),
    ] = "table",
):
    """Update a semantic model from a file.

    Requires admin role. The file should contain the fields to update.
    The model name cannot be changed.

    Examples:
        metricly models update orders orders_updated.yaml
    """
    user = require_auth()

    from services.manifest import update_semantic_model

    updates = load_definition_file(file)

    try:
        model = run_async(update_semantic_model(user, name, updates))
        print_success(f"Updated semantic model: {name}")

        summary = {
            "name": model.get("name", "-"),
            "measures": len(model.get("measures", [])),
            "dimensions": len(model.get("dimensions", [])),
        }
        format_output(summary, format=format, title="Updated Model")

    except PermissionError as e:
        print_error(str(e), hint="Admin role required")
        raise typer.Exit(1)
    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)


@models_app.command("delete")
def models_delete(
    name: Annotated[str, typer.Argument(help="Model name to delete")],
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Skip confirmation prompt"),
    ] = False,
):
    """Delete a semantic model.

    Requires admin role. Requires confirmation unless --yes is passed.
    """
    user = require_auth()

    from services.manifest import get_semantic_model, delete_semantic_model

    try:
        # First get the model to show its name
        model = run_async(get_semantic_model(user, name))

        # Confirm deletion
        if not yes:
            confirm = typer.confirm(
                f"Delete semantic model '{name}'? This cannot be undone."
            )
            if not confirm:
                print_info("Cancelled")
                raise typer.Exit(0)

        # Delete it
        run_async(delete_semantic_model(user, name))
        print_success(f"Deleted semantic model: {name}")

    except PermissionError as e:
        print_error(str(e), hint="Admin role required")
        raise typer.Exit(1)
    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
