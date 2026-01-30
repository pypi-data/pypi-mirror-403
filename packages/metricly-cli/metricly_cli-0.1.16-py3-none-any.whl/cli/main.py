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
pages_app = typer.Typer(help="Dashboard page operations")
sections_app = typer.Typer(help="Dashboard section operations")
manifest_app = typer.Typer(help="Manifest operations")
models_app = typer.Typer(help="Semantic model operations")
schedules_app = typer.Typer(help="Scheduled report operations")
quick_metrics_app = typer.Typer(help="Quick metric operations (user-defined calculated metrics)")
context_app = typer.Typer(help="User context and preferences")

# Register sub-command groups
app.add_typer(metrics_app, name="metrics")
app.add_typer(dimensions_app, name="dimensions")
app.add_typer(org_app, name="org")
app.add_typer(dashboards_app, name="dashboards")
app.add_typer(pages_app, name="pages")
app.add_typer(sections_app, name="sections")
app.add_typer(manifest_app, name="manifest")
app.add_typer(models_app, name="models")
app.add_typer(schedules_app, name="schedules")
app.add_typer(quick_metrics_app, name="quick-metrics")
app.add_typer(context_app, name="context")


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
def docs(
    full: Annotated[
        bool,
        typer.Option("--full", help="Show full documentation (llms-full.txt)"),
    ] = False,
    raw: Annotated[
        bool,
        typer.Option("--raw", help="Output raw markdown without formatting"),
    ] = False,
):
    """Show Metricly documentation for LLMs.

    Fetches documentation from metricly.xyz designed for LLM consumption.
    Use this to understand Metricly's capabilities, API, and CLI commands.

    Examples:
        metricly docs              # Show navigation/summary
        metricly docs --full       # Show complete documentation
        metricly docs --full --raw # Raw markdown for piping
    """
    import httpx
    from rich.markdown import Markdown

    url = "https://metricly.xyz/llms-full.txt" if full else "https://metricly.xyz/llms.txt"

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(url)
            response.raise_for_status()
            content = response.text

        if raw:
            print(content)
        else:
            console.print(Markdown(content))

    except httpx.HTTPStatusError as e:
        print_error(f"Failed to fetch documentation: HTTP {e.response.status_code}")
        raise typer.Exit(1)
    except httpx.RequestError as e:
        print_error(f"Failed to fetch documentation: {e}")
        print_info("Check your internet connection or try again later")
        raise typer.Exit(1)


@app.command()
def query(
    metrics: Annotated[
        list[str],
        typer.Option("-m", "--metrics", help="Metric names to query"),
    ],
    dimensions: Annotated[
        Optional[list[str]],
        typer.Option("-d", "--dimensions", help="Dimensions to group by (use qualified names, e.g. customer__region)"),
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
    from services.queries import QueryParams, QueryError, query_metrics

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

    except QueryError as e:
        print_error(e.message, hint=e.hint)
        raise typer.Exit(1)
    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)
    except Exception as e:
        print_error(f"Query failed: {e}")
        raise typer.Exit(1)


@app.command()
def export(
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="Output file path (required)"),
    ],
    metrics: Annotated[
        Optional[list[str]],
        typer.Option("-m", "--metrics", help="Metric names to export"),
    ] = None,
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
    dashboard: Annotated[
        Optional[str],
        typer.Option("--dashboard", help="Dashboard ID to export (exports all widget data)"),
    ] = None,
    format: Annotated[
        str,
        typer.Option("--format", "-f", help="Output format: csv or json"),
    ] = "csv",
):
    """Export query results or dashboard data to CSV or JSON.

    You can either:
    - Export query results by specifying metrics
    - Export all data from a dashboard by specifying --dashboard

    Examples:
        metricly export -o revenue.csv -m total_revenue -g month
        metricly export -o sales.json -m revenue -m orders -f json
        metricly export -o dashboard.csv --dashboard abc123
        metricly export -o report.csv -m revenue -d region --start 2024-01-01
    """
    user = require_auth()

    # Validate format
    format_lower = format.lower()
    if format_lower not in ("csv", "json"):
        print_error(
            f"Invalid format: {format}",
            hint="Use 'csv' or 'json'",
        )
        raise typer.Exit(1)

    # Ensure output has correct extension
    output_path = output
    expected_ext = f".{format_lower}"
    if output_path.suffix.lower() != expected_ext:
        output_path = output_path.with_suffix(expected_ext)
        print_warning(f"Output file extension adjusted to {output_path.name}")

    # Must have either metrics or dashboard
    if not metrics and not dashboard:
        print_error(
            "Either --metrics or --dashboard must be provided",
            hint="Use -m metric_name or --dashboard dashboard_id",
        )
        raise typer.Exit(1)

    from services.export import export_query_data, export_dashboard_data
    from services.queries import QueryParams

    try:
        if dashboard:
            # Dashboard export
            print_info(f"Exporting data from dashboard {dashboard}...")
            result = run_async(
                export_dashboard_data(
                    user,
                    dashboard,
                    format=format_lower,
                    output_path=str(output_path),
                )
            )
        else:
            # Query export
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

            params = QueryParams(
                metrics=metrics,
                dimensions=dimensions,
                grain=grain,
                start_date=parsed_start,
                end_date=parsed_end,
            )

            print_info(f"Exporting metrics: {', '.join(metrics)}...")
            result = run_async(
                export_query_data(
                    user,
                    params,
                    format=format_lower,
                    output_path=str(output_path),
                )
            )

        print_success(f"Exported {result.row_count} rows to {result.saved_to}")
        print_info(f"Columns: {', '.join(result.columns)}")

    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)
    except Exception as e:
        print_error(f"Export failed: {e}")
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
                "owner": "you" if d.owner == user.uid else "team",
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


@dashboards_app.command("update")
def dashboards_update(
    dashboard_id: Annotated[str, typer.Argument(help="Dashboard ID to update")],
    file: Annotated[
        Optional[Path],
        typer.Argument(help="Path to YAML or JSON file with updates (optional)"),
    ] = None,
    title: Annotated[
        Optional[str],
        typer.Option("--title", "-t", help="New dashboard title"),
    ] = None,
    description: Annotated[
        Optional[str],
        typer.Option("--description", "-d", help="New dashboard description"),
    ] = None,
    visibility: Annotated[
        Optional[str],
        typer.Option(
            "--visibility",
            "-v",
            help="New visibility: 'private' (only you) or 'org' (team)",
        ),
    ] = None,
    format: Annotated[
        OutputFormat,
        typer.Option("--format", "-f", help="Output format"),
    ] = "table",
):
    """Update a dashboard's metadata.

    You can update using command-line options, a file, or both.
    Command-line options override values from the file.

    Examples:
        metricly dashboards update abc123 --title 'New Title'
        metricly dashboards update abc123 --description 'Updated description'
        metricly dashboards update abc123 --visibility org
        metricly dashboards update abc123 dashboard.yaml
        metricly dashboards update abc123 updates.yaml --title 'Override Title'
    """
    user = require_auth()

    from services.dashboards import update_dashboard, get_dashboard
    import uuid

    def ensure_ids(data: dict) -> dict:
        """Ensure all pages, sections, and widgets have IDs."""
        if "pages" in data:
            for page in data["pages"]:
                if not page.get("id"):  # Missing, None, or empty string
                    page["id"] = str(uuid.uuid4())
                for section in page.get("sections", []):
                    # Sections don't have IDs by default, but widgets do
                    for widget in section.get("widgets", []):
                        if not widget.get("id"):  # Missing, None, or empty string
                            widget["id"] = str(uuid.uuid4())
        return data

    # Build updates dict
    updates = {}

    # Load from file if provided
    if file:
        file_updates = load_definition_file(file)
        # Auto-generate IDs for widgets/pages that don't have them
        file_updates = ensure_ids(file_updates)
        updates.update(file_updates)

    # Override with command-line options
    if title is not None:
        updates["title"] = title
    if description is not None:
        updates["description"] = description
    if visibility is not None:
        # Validate visibility
        if visibility not in ("private", "org"):
            print_error(
                f"Invalid visibility: {visibility}",
                hint="Use 'private' or 'org'",
            )
            raise typer.Exit(1)
        updates["visibility"] = visibility

    # Check that we have something to update
    if not updates:
        print_error(
            "No updates provided",
            hint="Use --title, --description, --visibility, or provide a file",
        )
        raise typer.Exit(1)

    try:
        # First verify the dashboard exists and user has access
        dashboard = run_async(get_dashboard(user, dashboard_id))

        # Perform the update
        updated = run_async(update_dashboard(user, dashboard_id, updates))

        print_success(f"Updated dashboard: {updated.title}")

        summary = {
            "id": updated.id,
            "title": updated.title,
            "description": updated.description or "-",
            "visibility": updated.visibility,
        }
        format_output(summary, format=format, title="Updated Dashboard")

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


@dashboards_app.command("duplicate")
def dashboards_duplicate(
    dashboard_id: Annotated[str, typer.Argument(help="Dashboard ID to duplicate")],
    title: Annotated[
        Optional[str],
        typer.Option("--title", "-t", help="Title for the new dashboard"),
    ] = None,
    format: Annotated[
        OutputFormat,
        typer.Option("--format", "-f", help="Output format"),
    ] = "table",
):
    """Duplicate a dashboard with all its pages, sections, and widgets.

    Creates a private copy owned by you. All widget and page IDs are
    regenerated to avoid conflicts.

    Examples:
        metricly dashboards duplicate abc123
        metricly dashboards duplicate abc123 --title "My Copy"
    """
    user = require_auth()

    from services.dashboards import duplicate_dashboard

    try:
        dashboard = run_async(
            duplicate_dashboard(
                user,
                dashboard_id,
                new_title=title,
            )
        )

        print_success(f"Created copy: {dashboard.title}")

        summary = {
            "id": dashboard.id,
            "title": dashboard.title,
            "description": dashboard.description or "-",
            "visibility": dashboard.visibility,
            "source": dashboard_id,
        }
        format_output(summary, format=format, title="Duplicated Dashboard")

    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)


@dashboards_app.command("share")
def dashboards_share(
    dashboard_id: Annotated[str, typer.Argument(help="Dashboard ID to share")],
    private: Annotated[
        bool,
        typer.Option("--private", "-p", help="Make dashboard private (unshare)"),
    ] = False,
):
    """Share or unshare a dashboard with your organization.

    By default, makes the dashboard visible to your organization.
    Use --private to make it private again.

    Examples:
        metricly dashboards share abc123         # Share with org
        metricly dashboards share abc123 --private  # Make private
    """
    user = require_auth()

    from services.dashboards import share_dashboard, get_dashboard

    visibility = "private" if private else "org"

    try:
        # First get the dashboard to show its title
        dashboard = run_async(get_dashboard(user, dashboard_id))

        # Update visibility
        updated = run_async(
            share_dashboard(
                user,
                dashboard_id,
                visibility=visibility,
            )
        )

        if visibility == "org":
            print_success(f"Shared '{updated.title}' with organization")
        else:
            print_success(f"Made '{updated.title}' private")

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
    # Note: api_base already includes /api (e.g., https://metricly.xyz/api)
    url = f"{api_base}/render/dashboard/{dashboard_id}"

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
            elif response.status_code != 200:
                # Extract error detail from response body
                error_detail = response.text
                try:
                    error_json = response.json()
                    error_detail = error_json.get("detail", error_detail)
                except Exception:
                    pass

                # Provide appropriate error message based on status code
                if response.status_code == 404:
                    print_error(f"Dashboard not found: {dashboard_id}", hint=error_detail if error_detail != "Dashboard not found" else None)
                else:
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
    # Note: api_base already includes /api (e.g., https://metricly.xyz/api)
    url = f"{api_base}/render/widget/{dashboard_id}/{widget_id}"

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
            elif response.status_code != 200:
                # Extract error detail from response body
                error_detail = response.text
                try:
                    error_json = response.json()
                    error_detail = error_json.get("detail", error_detail)
                except Exception:
                    pass

                # Provide appropriate error message based on status code
                if response.status_code == 404:
                    default_msg = "Dashboard or widget not found"
                    print_error(f"{default_msg}: {dashboard_id}/{widget_id}", hint=error_detail if error_detail != default_msg else None)
                else:
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


@dashboards_app.command("move-widget")
def move_widget_cmd(
    dashboard_id: Annotated[str, typer.Argument(help="Dashboard ID")],
    widget_id: Annotated[str, typer.Argument(help="Widget ID to move")],
    to_page: Annotated[
        str,
        typer.Option("--to-page", help="Target page ID"),
    ],
    to_section: Annotated[
        int,
        typer.Option("--to-section", help="Target section index"),
    ],
    position: Annotated[
        Optional[int],
        typer.Option("--position", help="Position in section (default: append to end)"),
    ] = None,
    format: Annotated[
        OutputFormat,
        typer.Option("--format", "-f", help="Output format"),
    ] = "table",
):
    """Move a widget to a different location.

    Move a widget to a different page, section, or position within a dashboard.
    The widget is removed from its current location and inserted at the target.

    Examples:
        metricly dashboards move-widget abc123 widget-1 --to-page page-2 --to-section 0
        metricly dashboards move-widget abc123 widget-1 --to-page page-1 --to-section 1 --position 0
    """
    user = require_auth()

    from services.dashboards import move_widget

    try:
        dashboard = run_async(
            move_widget(
                user,
                dashboard_id,
                widget_id,
                to_page,
                to_section,
                position,
            )
        )

        print_success(f"Moved widget '{widget_id}' to page '{to_page}', section {to_section}")

        if format == "json":
            format_output(dashboard.model_dump(), format=format)
        else:
            summary = {
                "dashboard_id": dashboard.id,
                "dashboard_title": dashboard.title,
                "widget_id": widget_id,
                "target_page": to_page,
                "target_section": to_section,
                "position": position if position is not None else "end",
            }
            format_output(summary, format=format, title="Widget Moved")

    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)


@dashboards_app.command("copy-widget")
def copy_widget_cmd(
    dashboard_id: Annotated[str, typer.Argument(help="Dashboard ID")],
    widget_id: Annotated[str, typer.Argument(help="Widget ID to copy")],
    to_page: Annotated[
        str,
        typer.Option("--to-page", help="Target page ID"),
    ],
    to_section: Annotated[
        int,
        typer.Option("--to-section", help="Target section index"),
    ],
    title: Annotated[
        Optional[str],
        typer.Option("--title", help="Title for the copied widget (default: 'Copy of {original}')"),
    ] = None,
    format: Annotated[
        OutputFormat,
        typer.Option("--format", "-f", help="Output format"),
    ] = "table",
):
    """Copy a widget to a new location.

    Creates a duplicate of a widget with a new ID at the target location.
    The original widget remains unchanged.

    Examples:
        metricly dashboards copy-widget abc123 widget-1 --to-page page-2 --to-section 0
        metricly dashboards copy-widget abc123 widget-1 --to-page page-1 --to-section 1 --title "Q2 Revenue"
    """
    user = require_auth()

    from services.dashboards import copy_widget

    try:
        dashboard = run_async(
            copy_widget(
                user,
                dashboard_id,
                widget_id,
                to_page,
                to_section,
                title,
            )
        )

        print_success(f"Copied widget '{widget_id}' to page '{to_page}', section {to_section}")

        if format == "json":
            format_output(dashboard.model_dump(), format=format)
        else:
            summary = {
                "dashboard_id": dashboard.id,
                "dashboard_title": dashboard.title,
                "source_widget_id": widget_id,
                "target_page": to_page,
                "target_section": to_section,
                "new_title": title or f"Copy of {widget_id}",
            }
            format_output(summary, format=format, title="Widget Copied")

    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)


@dashboards_app.command("swap-widgets")
def swap_widgets_cmd(
    dashboard_id: Annotated[str, typer.Argument(help="Dashboard ID")],
    widget_id_1: Annotated[str, typer.Argument(help="First widget ID")],
    widget_id_2: Annotated[str, typer.Argument(help="Second widget ID")],
    format: Annotated[
        OutputFormat,
        typer.Option("--format", "-f", help="Output format"),
    ] = "table",
):
    """Swap the positions of two widgets.

    Exchange the positions of two widgets within a dashboard.
    Widgets can be in different pages or sections.

    Examples:
        metricly dashboards swap-widgets abc123 widget-1 widget-2
        metricly dashboards swap-widgets abc123 kpi-revenue kpi-orders --format json
    """
    user = require_auth()

    from services.dashboards import swap_widgets

    try:
        dashboard = run_async(
            swap_widgets(
                user,
                dashboard_id,
                widget_id_1,
                widget_id_2,
            )
        )

        print_success(f"Swapped widgets '{widget_id_1}' and '{widget_id_2}'")

        if format == "json":
            format_output(dashboard.model_dump(), format=format)
        else:
            summary = {
                "dashboard_id": dashboard.id,
                "dashboard_title": dashboard.title,
                "widget_1": widget_id_1,
                "widget_2": widget_id_2,
            }
            format_output(summary, format=format, title="Widgets Swapped")

    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)


@dashboards_app.command("add-widget")
def add_widget_cmd(
    dashboard_id: Annotated[str, typer.Argument(help="Dashboard ID")],
    widget_type: Annotated[
        str,
        typer.Option("--type", "-t", help="Widget type: kpi, line_chart, bar_chart, area_chart, donut, table, heatmap"),
    ],
    title: Annotated[str, typer.Option("--title", help="Widget title")],
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
        typer.Option("-g", "--grain", help="Time grain: day, week, month, quarter, year, or $grain for dashboard control"),
    ] = None,
    page: Annotated[
        int,
        typer.Option("--page", help="Page index (0-based)"),
    ] = 0,
    section: Annotated[
        int,
        typer.Option("--section", help="Section index (0-based)"),
    ] = 0,
    width: Annotated[
        Optional[int],
        typer.Option("--width", "-w", help="Widget width (1-10). Defaults: kpi=2, donut=3, heatmap=5, charts/tables=10"),
    ] = None,
    time_scope: Annotated[
        Optional[str],
        typer.Option("--time-scope", help="Date scope: range (full), latest (current period), latest_complete (last complete period)"),
    ] = None,
    format: Annotated[
        OutputFormat,
        typer.Option("--format", "-f", help="Output format"),
    ] = "table",
):
    """Add a new widget to a dashboard.

    Creates a new widget with the specified configuration and adds it
    to the specified page and section. Uses a 10-column grid layout.

    Default widths by type (if --width not specified):
        kpi: 2 columns (5 per row)
        donut: 3 columns (3 per row)
        heatmap: 5 columns (2 per row)
        area_chart, line_chart, bar_chart, table: 10 columns (full width)

    Time scope (for non-time-series widgets):
        range: Use full dashboard date range (default)
        latest: Current period only (may be incomplete)
        latest_complete: Last complete period

    Examples:
        metricly dashboards add-widget abc123 --type kpi --title "Revenue" -m total_revenue
        metricly dashboards add-widget abc123 -t line_chart --title "Trends" -m revenue -g month
        metricly dashboards add-widget abc123 -t kpi --title "Last Month" -m revenue --time-scope latest_complete
        metricly dashboards add-widget abc123 -t kpi --title "Custom" -m revenue --width 4
    """
    user = require_auth()

    from services.dashboards import add_widget

    # Build widget definition
    widget = {
        "type": widget_type,
        "title": title,
        "query": {
            "metrics": metrics,
        },
    }

    if dimensions:
        widget["query"]["dimensions"] = dimensions
    if grain:
        widget["query"]["grain"] = grain
    if width:
        widget["width"] = width
    if time_scope:
        if time_scope not in ("range", "latest", "latest_complete"):
            print_error(f"Invalid time_scope: {time_scope}. Must be: range, latest, latest_complete")
            raise typer.Exit(1)
        widget["time_scope"] = time_scope

    try:
        dashboard = run_async(
            add_widget(
                user,
                dashboard_id,
                widget,
                page_index=page,
                section_index=section,
            )
        )

        print_success(f"Added widget '{title}' to dashboard")

        if format == "json":
            format_output(dashboard.model_dump(), format=format)
        else:
            summary = {
                "dashboard_id": dashboard.id,
                "widget_title": title,
                "widget_type": widget_type,
                "page_index": page,
                "section_index": section,
            }
            format_output(summary, format=format, title="Widget Added")

    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)


@dashboards_app.command("remove-widget")
def remove_widget_cmd(
    dashboard_id: Annotated[str, typer.Argument(help="Dashboard ID")],
    widget_id: Annotated[str, typer.Argument(help="Widget ID to remove")],
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Skip confirmation"),
    ] = False,
    format: Annotated[
        OutputFormat,
        typer.Option("--format", "-f", help="Output format"),
    ] = "table",
):
    """Remove a widget from a dashboard.

    Permanently deletes a widget from the dashboard.

    Examples:
        metricly dashboards remove-widget abc123 widget-1
        metricly dashboards remove-widget abc123 widget-1 --yes
    """
    user = require_auth()

    from services.dashboards import remove_widget

    if not yes:
        confirm = typer.confirm(f"Remove widget '{widget_id}'?")
        if not confirm:
            print_info("Cancelled")
            return

    try:
        dashboard = run_async(
            remove_widget(user, dashboard_id, widget_id)
        )

        print_success(f"Removed widget '{widget_id}'")

        if format == "json":
            format_output(dashboard.model_dump(), format=format)
        else:
            summary = {
                "dashboard_id": dashboard.id,
                "removed_widget_id": widget_id,
            }
            format_output(summary, format=format, title="Widget Removed")

    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)


@dashboards_app.command("update-widget")
def update_widget_cmd(
    dashboard_id: Annotated[str, typer.Argument(help="Dashboard ID")],
    widget_id: Annotated[str, typer.Argument(help="Widget ID to update")],
    title: Annotated[
        Optional[str],
        typer.Option("--title", help="New widget title"),
    ] = None,
    metrics: Annotated[
        Optional[list[str]],
        typer.Option("-m", "--metrics", help="New metric names"),
    ] = None,
    dimensions: Annotated[
        Optional[list[str]],
        typer.Option("-d", "--dimensions", help="New dimensions"),
    ] = None,
    grain: Annotated[
        Optional[str],
        typer.Option("-g", "--grain", help="New time grain"),
    ] = None,
    width: Annotated[
        Optional[int],
        typer.Option("--width", "-w", help="New widget width (1-10)"),
    ] = None,
    format: Annotated[
        OutputFormat,
        typer.Option("--format", "-f", help="Output format"),
    ] = "table",
):
    """Update an existing widget.

    Modify the configuration of an existing widget. Only specified
    fields are updated; others remain unchanged.

    Examples:
        metricly dashboards update-widget abc123 widget-1 --title "New Title"
        metricly dashboards update-widget abc123 widget-1 -m revenue -m orders
        metricly dashboards update-widget abc123 widget-1 --width 6
    """
    user = require_auth()

    from services.dashboards import update_widget

    # Build updates dict
    updates = {}
    if title:
        updates["title"] = title
    if width:
        updates["width"] = width

    # Build query updates if any query fields provided
    query_updates = {}
    if metrics:
        query_updates["metrics"] = metrics
    if dimensions:
        query_updates["dimensions"] = dimensions
    if grain:
        query_updates["grain"] = grain

    if query_updates:
        updates["query"] = query_updates

    if not updates:
        print_error("No updates specified")
        raise typer.Exit(1)

    try:
        dashboard = run_async(
            update_widget(user, dashboard_id, widget_id, updates)
        )

        print_success(f"Updated widget '{widget_id}'")

        if format == "json":
            format_output(dashboard.model_dump(), format=format)
        else:
            summary = {
                "dashboard_id": dashboard.id,
                "widget_id": widget_id,
                "updated_fields": list(updates.keys()),
            }
            format_output(summary, format=format, title="Widget Updated")

    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)


@dashboards_app.command("reorder-widgets")
def reorder_widgets_cmd(
    dashboard_id: Annotated[str, typer.Argument(help="Dashboard ID")],
    page_id: Annotated[str, typer.Option("--page", help="Page ID")],
    section_index: Annotated[int, typer.Option("--section", help="Section index (0-based)")],
    widget_ids: Annotated[
        list[str],
        typer.Argument(help="Widget IDs in desired order"),
    ],
    format: Annotated[
        OutputFormat,
        typer.Option("--format", "-f", help="Output format"),
    ] = "table",
):
    """Reorder widgets within a section.

    Specify the widget IDs in the desired order. All widgets in the
    section must be included.

    Examples:
        metricly dashboards reorder-widgets abc123 --page page-1 --section 0 widget-3 widget-1 widget-2
    """
    user = require_auth()

    from services.dashboards import reorder_widgets

    try:
        dashboard = run_async(
            reorder_widgets(user, dashboard_id, page_id, section_index, widget_ids)
        )

        print_success(f"Reordered {len(widget_ids)} widgets")

        if format == "json":
            format_output(dashboard.model_dump(), format=format)
        else:
            summary = {
                "dashboard_id": dashboard.id,
                "page_id": page_id,
                "section_index": section_index,
                "new_order": widget_ids,
            }
            format_output(summary, format=format, title="Widgets Reordered")

    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)


@dashboards_app.command("set-controls")
def set_controls_cmd(
    dashboard_id: Annotated[str, typer.Argument(help="Dashboard ID")],
    start_date: Annotated[
        Optional[str],
        typer.Option("--start", help="Start date (YYYY-MM-DD)"),
    ] = None,
    end_date: Annotated[
        Optional[str],
        typer.Option("--end", help="End date (YYYY-MM-DD)"),
    ] = None,
    preset: Annotated[
        Optional[str],
        typer.Option("--preset", help="Date preset: last_7_days, last_30_days, mtd, qtd, ytd, etc."),
    ] = None,
    grain: Annotated[
        Optional[str],
        typer.Option("-g", "--grain", help="Time grain: day, week, month, quarter, year"),
    ] = None,
    comparison: Annotated[
        Optional[str],
        typer.Option("--comparison", help="Comparison mode: previous_period, previous_year, none"),
    ] = None,
    format: Annotated[
        OutputFormat,
        typer.Option("--format", "-f", help="Output format"),
    ] = "table",
):
    """Set dashboard control values.

    Update the date range, grain, or comparison mode for a dashboard.
    Use either --preset OR --start/--end for date range.

    Examples:
        metricly dashboards set-controls abc123 --preset last_30_days
        metricly dashboards set-controls abc123 --start 2024-01-01 --end 2024-12-31
        metricly dashboards set-controls abc123 --grain month --comparison previous_year
    """
    user = require_auth()

    from services.dashboards import set_dashboard_controls

    # Build controls dict
    controls = {}

    if preset:
        controls["date_range"] = {"preset": preset}
    elif start_date and end_date:
        controls["date_range"] = {"start": start_date, "end": end_date}
    elif start_date or end_date:
        print_error("Both --start and --end are required for custom date range")
        raise typer.Exit(1)

    if grain:
        controls["grain"] = grain
    if comparison:
        controls["comparison"] = comparison

    if not controls:
        print_error("No control values specified")
        raise typer.Exit(1)

    try:
        dashboard = run_async(
            set_dashboard_controls(user, dashboard_id, controls)
        )

        print_success(f"Updated dashboard controls")

        if format == "json":
            format_output(dashboard.model_dump(), format=format)
        else:
            summary = {
                "dashboard_id": dashboard.id,
                "updated_controls": list(controls.keys()),
            }
            if "date_range" in controls:
                summary["date_range"] = controls["date_range"]
            if "grain" in controls:
                summary["grain"] = controls["grain"]
            if "comparison" in controls:
                summary["comparison"] = controls["comparison"]
            format_output(summary, format=format, title="Controls Updated")

    except ValueError as e:
        print_error(str(e))
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
# Pages sub-commands
# ============================================================================


@pages_app.command("create")
def pages_create(
    dashboard_id: Annotated[str, typer.Argument(help="Dashboard ID")],
    title: Annotated[str, typer.Argument(help="Page title")],
    position: Annotated[
        Optional[int],
        typer.Option("--position", "-p", help="Position in dashboard (default: append to end)"),
    ] = None,
    format: Annotated[
        OutputFormat,
        typer.Option("--format", "-f", help="Output format"),
    ] = "table",
):
    """Create a new page in a dashboard.

    Examples:
        metricly pages create abc123 "Sales Overview"
        metricly pages create abc123 "Q1 Metrics" --position 0
    """
    user = require_auth()

    from services.dashboards import create_page, get_dashboard

    try:
        dashboard = run_async(create_page(user, dashboard_id, title, position))
        print_success(f"Created page: {title}")

        # Find the newly created page
        new_page = None
        for page in dashboard.pages:
            if page.title == title:
                new_page = page
                break

        if new_page:
            summary = {
                "page_id": new_page.id,
                "title": new_page.title,
                "dashboard_id": dashboard_id,
                "total_pages": len(dashboard.pages),
            }
            format_output(summary, format=format, title="New Page")

    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)


@pages_app.command("delete")
def pages_delete(
    dashboard_id: Annotated[str, typer.Argument(help="Dashboard ID")],
    page_id: Annotated[str, typer.Argument(help="Page ID to delete")],
    cascade: Annotated[
        bool,
        typer.Option("--cascade", help="Delete even if page has widgets"),
    ] = False,
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Skip confirmation prompt"),
    ] = False,
):
    """Delete a page from a dashboard.

    By default, refuses to delete pages with widgets. Use --cascade to force deletion.
    Cannot delete the last page in a dashboard.

    Examples:
        metricly pages delete abc123 page-id-123
        metricly pages delete abc123 page-id-123 --cascade --yes
    """
    user = require_auth()

    from services.dashboards import delete_page, get_dashboard

    try:
        # Get dashboard and find page
        dashboard = run_async(get_dashboard(user, dashboard_id))
        page = None
        for p in dashboard.pages:
            if p.id == page_id:
                page = p
                break

        if not page:
            print_error(f"Page '{page_id}' not found in dashboard")
            raise typer.Exit(1)

        # Count widgets
        widget_count = sum(len(s.widgets) for s in page.sections)

        # Confirm deletion
        if not yes:
            msg = f"Delete page '{page.title}'"
            if widget_count > 0:
                msg += f" ({widget_count} widgets)"
            msg += "?"
            confirm = typer.confirm(msg)
            if not confirm:
                print_info("Cancelled")
                raise typer.Exit(0)

        # Delete it
        updated = run_async(delete_page(user, dashboard_id, page_id, cascade))
        print_success(f"Deleted page: {page.title}")
        print_info(f"Dashboard now has {len(updated.pages)} page(s)")

    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)


@pages_app.command("rename")
def pages_rename(
    dashboard_id: Annotated[str, typer.Argument(help="Dashboard ID")],
    page_id: Annotated[str, typer.Argument(help="Page ID to rename")],
    title: Annotated[str, typer.Argument(help="New title")],
):
    """Rename a page.

    Examples:
        metricly pages rename abc123 page-id-123 "New Title"
    """
    user = require_auth()

    from services.dashboards import rename_page

    try:
        dashboard = run_async(rename_page(user, dashboard_id, page_id, title))
        print_success(f"Renamed page to: {title}")

        # Find the renamed page to show its info
        renamed_page = None
        for page in dashboard.pages:
            if page.id == page_id:
                renamed_page = page
                break

        if renamed_page:
            section_count = len(renamed_page.sections)
            widget_count = sum(len(s.widgets) for s in renamed_page.sections)
            print_info(f"Page has {section_count} section(s) and {widget_count} widget(s)")

    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)


@pages_app.command("reorder")
def pages_reorder(
    dashboard_id: Annotated[str, typer.Argument(help="Dashboard ID")],
    page_ids: Annotated[list[str], typer.Argument(help="Page IDs in new order")],
):
    """Reorder pages in a dashboard.

    Provide all page IDs in the desired order. All page IDs must be included.

    Examples:
        metricly pages reorder abc123 page-1 page-2 page-3
    """
    user = require_auth()

    from services.dashboards import reorder_pages, get_dashboard

    try:
        # First get the dashboard to show current order
        dashboard = run_async(get_dashboard(user, dashboard_id))

        # Reorder
        updated = run_async(reorder_pages(user, dashboard_id, page_ids))
        print_success(f"Reordered {len(page_ids)} page(s)")

        # Show new order
        console.print()
        pages_data = []
        for i, page in enumerate(updated.pages):
            section_count = len(page.sections)
            widget_count = sum(len(s.widgets) for s in page.sections)
            pages_data.append({
                "position": i + 1,
                "title": page.title,
                "sections": section_count,
                "widgets": widget_count,
            })

        format_output(
            pages_data,
            format="table",
            columns=["position", "title", "sections", "widgets"],
            title="New Page Order",
        )

    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)


# ============================================================================
# Sections sub-commands
# ============================================================================


@sections_app.command("create")
def sections_create(
    dashboard_id: Annotated[str, typer.Argument(help="Dashboard ID")],
    page_id: Annotated[str, typer.Argument(help="Page ID to add section to")],
    title: Annotated[
        Optional[str],
        typer.Option("--title", "-t", help="Section title (optional)"),
    ] = None,
    position: Annotated[
        Optional[int],
        typer.Option("--position", "-p", help="Position in page (default: append to end)"),
    ] = None,
    format: Annotated[
        OutputFormat,
        typer.Option("--format", "-f", help="Output format"),
    ] = "table",
):
    """Create a new section in a page.

    Creates an empty section at the specified position (or at the end if position not provided).
    The section will have no widgets initially.

    Examples:
        metricly sections create abc123 page-1
        metricly sections create abc123 page-1 --title "Revenue Metrics"
        metricly sections create abc123 page-1 --title "KPIs" --position 0
    """
    user = require_auth()

    from services.dashboards import create_section, get_dashboard

    try:
        dashboard = run_async(
            create_section(
                user,
                dashboard_id,
                page_id,
                title=title,
                position=position,
            )
        )

        print_success(f"Created section in page '{page_id}'")

        # Find the page to show section count
        page_idx = None
        for i, page in enumerate(dashboard.pages):
            if page.id == page_id:
                page_idx = i
                break

        if page_idx is not None:
            section_count = len(dashboard.pages[page_idx].sections)
            print_info(f"Page now has {section_count} section(s)")

    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)


@sections_app.command("delete")
def sections_delete(
    dashboard_id: Annotated[str, typer.Argument(help="Dashboard ID")],
    page_id: Annotated[str, typer.Argument(help="Page ID containing the section")],
    section_index: Annotated[int, typer.Argument(help="Section index (0-based)")],
    cascade: Annotated[
        bool,
        typer.Option("--cascade", help="Delete even if section has widgets"),
    ] = False,
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Skip confirmation prompt"),
    ] = False,
):
    """Delete a section from a page.

    By default, fails if the section contains widgets. Use --cascade to delete anyway.
    Requires confirmation unless --yes is passed.

    Examples:
        metricly sections delete abc123 page-1 0
        metricly sections delete abc123 page-1 0 --cascade --yes
    """
    user = require_auth()

    from services.dashboards import delete_section, get_dashboard

    try:
        # First get the dashboard to check the section
        dashboard = run_async(get_dashboard(user, dashboard_id))

        # Find page
        page_idx = None
        for i, page in enumerate(dashboard.pages):
            if page.id == page_id:
                page_idx = i
                break

        if page_idx is None:
            raise ValueError(f"Page '{page_id}' not found")

        sections = dashboard.pages[page_idx].sections
        if section_index < 0 or section_index >= len(sections):
            raise ValueError(f"Section index {section_index} out of range (0-{len(sections)-1})")

        section = sections[section_index]
        widget_count = len(section.widgets)
        section_title = section.title or f"Section {section_index}"

        # Confirm deletion
        if not yes:
            widget_msg = f" with {widget_count} widgets" if widget_count > 0 else " (empty)"
            confirm = typer.confirm(
                f"Delete section '{section_title}'{widget_msg}?"
            )
            if not confirm:
                print_info("Cancelled")
                raise typer.Exit(0)

        # Delete it
        run_async(
            delete_section(
                user,
                dashboard_id,
                page_id,
                section_index,
                cascade=cascade,
            )
        )
        print_success(f"Deleted section '{section_title}'")

    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)


@sections_app.command("rename")
def sections_rename(
    dashboard_id: Annotated[str, typer.Argument(help="Dashboard ID")],
    page_id: Annotated[str, typer.Argument(help="Page ID containing the section")],
    section_index: Annotated[int, typer.Argument(help="Section index (0-based)")],
    title: Annotated[
        str,
        typer.Option("--title", "-t", help="New section title (use empty string to remove title)"),
    ],
):
    """Rename a section.

    Updates the section title. Pass an empty string to remove the title.

    Examples:
        metricly sections rename abc123 page-1 0 --title "Revenue Overview"
        metricly sections rename abc123 page-1 0 --title ""  # Remove title
    """
    user = require_auth()

    from services.dashboards import rename_section

    try:
        # Use None for empty string to remove title
        new_title = title if title else None

        dashboard = run_async(
            rename_section(
                user,
                dashboard_id,
                page_id,
                section_index,
                new_title,
            )
        )

        if new_title:
            print_success(f"Renamed section to '{new_title}'")
        else:
            print_success("Removed section title")

    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)


@sections_app.command("move")
def sections_move(
    dashboard_id: Annotated[str, typer.Argument(help="Dashboard ID")],
    source_page_id: Annotated[str, typer.Argument(help="Source page ID")],
    section_index: Annotated[int, typer.Argument(help="Section index in source page (0-based)")],
    to_page: Annotated[
        str,
        typer.Option("--to-page", help="Target page ID"),
    ],
    position: Annotated[
        Optional[int],
        typer.Option("--position", "-p", help="Position in target page (default: append to end)"),
    ] = None,
):
    """Move a section to a different page.

    Moves the section and all its widgets from one page to another.
    Can also be used to reposition within the same page.

    Examples:
        metricly sections move abc123 page-1 0 --to-page page-2
        metricly sections move abc123 page-1 2 --to-page page-2 --position 0
        metricly sections move abc123 page-1 1 --to-page page-1 --position 0  # Reorder within same page
    """
    user = require_auth()

    from services.dashboards import move_section, get_dashboard

    try:
        # Get dashboard to show section info
        dashboard = run_async(get_dashboard(user, dashboard_id))

        # Find source page to get section title
        page_idx = None
        for i, page in enumerate(dashboard.pages):
            if page.id == source_page_id:
                page_idx = i
                break

        if page_idx is not None:
            sections = dashboard.pages[page_idx].sections
            if 0 <= section_index < len(sections):
                section = sections[section_index]
                section_title = section.title or f"Section {section_index}"
                widget_count = len(section.widgets)

        # Move the section
        updated_dashboard = run_async(
            move_section(
                user,
                dashboard_id,
                source_page_id,
                section_index,
                to_page,
                target_position=position,
            )
        )

        # Show result
        if source_page_id == to_page:
            print_success(f"Repositioned section '{section_title}' within page")
        else:
            print_success(f"Moved section '{section_title}' to page '{to_page}'")

        if 'widget_count' in locals():
            print_info(f"Moved {widget_count} widget(s)")

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


# ============================================================================
# Schedules sub-commands
# ============================================================================


@schedules_app.command("list")
def schedules_list(
    format: Annotated[
        OutputFormat,
        typer.Option("--format", "-f", help="Output format"),
    ] = "table",
):
    """List all scheduled reports.

    Shows all schedules in your organization with their status
    and configuration summary.

    Examples:
        metricly schedules list
        metricly schedules list --format json
    """
    from settings import get_settings
    if not get_settings().schedules_enabled:
        print_info("Scheduled reports coming soon. This feature is not yet enabled.")
        return

    user = require_auth()

    from services.schedules import list_schedules

    try:
        schedules = run_async(list_schedules(user))

        if not schedules:
            print_info("No scheduled reports found")
            print_info("Create one with: metricly schedules create 'My Report' ...")
            return

        # Build display data
        schedules_data = []
        for s in schedules:
            schedules_data.append({
                "id": s.id,
                "name": s.name,
                "frequency": s.frequency_type,
                "time": s.frequency_time,
                "type": s.report_type,
                "enabled": s.enabled,
                "recipients": s.recipients_count,
                "last_run": s.last_run_at.strftime("%Y-%m-%d %H:%M") if s.last_run_at else "-",
                "status": s.last_run_status or "-",
            })

        format_output(
            schedules_data,
            format=format,
            columns=["id", "name", "frequency", "time", "type", "enabled", "recipients", "last_run", "status"],
            title="Scheduled Reports",
        )
    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)


@schedules_app.command("show")
def schedules_show(
    schedule_id: Annotated[str, typer.Argument(help="Schedule ID")],
    format: Annotated[
        OutputFormat,
        typer.Option("--format", "-f", help="Output format"),
    ] = "table",
):
    """Show details of a scheduled report.

    Displays full schedule configuration including frequency,
    report type, and recipients.

    Examples:
        metricly schedules show abc123
        metricly schedules show abc123 --format json
    """
    from settings import get_settings
    if not get_settings().schedules_enabled:
        print_info("Scheduled reports coming soon. This feature is not yet enabled.")
        return

    user = require_auth()

    from services.schedules import get_schedule, DashboardReport, QueryReport

    try:
        schedule = run_async(get_schedule(user, schedule_id))

        if format == "json":
            format_output(schedule.model_dump(mode="json"), format=format)
        else:
            # Determine report type and details
            if isinstance(schedule.report, DashboardReport):
                report_type = "dashboard"
                report_details = f"Dashboard: {schedule.report.dashboard_id} ({schedule.report.format})"
            else:
                report_type = "query"
                metrics_str = ", ".join(schedule.report.metrics)
                dims_str = ", ".join(schedule.report.dimensions) if schedule.report.dimensions else "-"
                report_details = f"Metrics: {metrics_str}\nDimensions: {dims_str}\nFormat: {schedule.report.format}"

            # Build frequency description
            freq = schedule.frequency
            if freq.type == "daily":
                freq_desc = f"Daily at {freq.time} UTC"
            elif freq.type == "weekly":
                days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                day_name = days[freq.day_of_week] if freq.day_of_week is not None else "?"
                freq_desc = f"Weekly on {day_name} at {freq.time} UTC"
            else:  # monthly
                freq_desc = f"Monthly on day {freq.day_of_month} at {freq.time} UTC"

            summary = {
                "id": schedule.id,
                "name": schedule.name,
                "enabled": schedule.enabled,
                "frequency": freq_desc,
                "report_type": report_type,
                "report_details": report_details,
                "recipients": ", ".join(schedule.recipients),
                "created_by": schedule.created_by,
                "created_at": schedule.created_at.strftime("%Y-%m-%d %H:%M"),
                "updated_at": schedule.updated_at.strftime("%Y-%m-%d %H:%M"),
                "last_run": schedule.last_run_at.strftime("%Y-%m-%d %H:%M") if schedule.last_run_at else "-",
                "last_status": schedule.last_run_status or "-",
            }

            format_output(summary, format=format, title=f"Schedule: {schedule.name}")

    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)


@schedules_app.command("create")
def schedules_create(
    name: Annotated[str, typer.Argument(help="Schedule name")],
    frequency: Annotated[
        str,
        typer.Option("--frequency", help="Frequency: daily, weekly, or monthly"),
    ],
    recipients: Annotated[
        list[str],
        typer.Option("--to", help="Email recipients (can specify multiple)"),
    ],
    time: Annotated[
        str,
        typer.Option("--time", help="Time in HH:MM format (UTC)"),
    ] = "09:00",
    dashboard_id: Annotated[
        Optional[str],
        typer.Option("--dashboard", help="Dashboard ID for PDF/PNG report"),
    ] = None,
    metrics: Annotated[
        Optional[list[str]],
        typer.Option("-m", "--metric", help="Metrics for query report"),
    ] = None,
    dimensions: Annotated[
        Optional[list[str]],
        typer.Option("-d", "--dimension", help="Dimensions for query report"),
    ] = None,
    report_format: Annotated[
        str,
        typer.Option("--format", "-f", help="Output format: pdf, png, csv, json"),
    ] = "pdf",
    day_of_week: Annotated[
        Optional[int],
        typer.Option("--day-of-week", help="Day of week for weekly (0=Monday through 6=Sunday)"),
    ] = None,
    day_of_month: Annotated[
        Optional[int],
        typer.Option("--day-of-month", help="Day of month for monthly (1-28)"),
    ] = None,
):
    """Create a scheduled report.

    Create a recurring report that will be emailed to recipients.
    You can schedule either a dashboard export (PDF/PNG) or a
    metrics query export (CSV/JSON).

    For dashboard reports, use --dashboard with the dashboard ID.
    For query reports, use -m/--metric to specify metrics.

    Examples:
        # Weekly dashboard PDF every Monday at 9am UTC
        metricly schedules create "Weekly Sales" --frequency weekly --day-of-week 0 \\
            --dashboard abc123 --to team@company.com

        # Daily metrics CSV report
        metricly schedules create "Daily Revenue" --frequency daily \\
            -m total_revenue -m order_count --format csv --to ceo@company.com

        # Monthly report on the 1st at 8am
        metricly schedules create "Monthly Summary" --frequency monthly --day-of-month 1 \\
            --time 08:00 --dashboard abc123 --to reports@company.com --to cfo@company.com
    """
    from settings import get_settings
    if not get_settings().schedules_enabled:
        print_info("Scheduled reports coming soon. This feature is not yet enabled.")
        return

    user = require_auth()

    from services.schedules import (
        create_schedule,
        ScheduleFrequency,
        DashboardReport,
        QueryReport,
    )

    # Validate: must have either dashboard or metrics
    if not dashboard_id and not metrics:
        print_error(
            "Either --dashboard or -m/--metric must be provided",
            hint="Use --dashboard for PDF/PNG reports or -m for query reports",
        )
        raise typer.Exit(1)

    if dashboard_id and metrics:
        print_error(
            "Cannot specify both --dashboard and -m/--metric",
            hint="Choose either a dashboard report or a query report",
        )
        raise typer.Exit(1)

    # Validate frequency
    if frequency not in ("daily", "weekly", "monthly"):
        print_error(
            f"Invalid frequency: {frequency}",
            hint="Use 'daily', 'weekly', or 'monthly'",
        )
        raise typer.Exit(1)

    # Validate frequency-specific options
    if frequency == "weekly" and day_of_week is None:
        print_error(
            "Weekly schedules require --day-of-week",
            hint="Use 0=Monday through 6=Sunday",
        )
        raise typer.Exit(1)

    if frequency == "monthly" and day_of_month is None:
        print_error(
            "Monthly schedules require --day-of-month",
            hint="Use 1-28",
        )
        raise typer.Exit(1)

    # Validate format based on report type
    if dashboard_id:
        if report_format not in ("pdf", "png"):
            print_error(
                f"Invalid format for dashboard report: {report_format}",
                hint="Use 'pdf' or 'png' for dashboard reports",
            )
            raise typer.Exit(1)
    else:
        if report_format not in ("csv", "json"):
            print_error(
                f"Invalid format for query report: {report_format}",
                hint="Use 'csv' or 'json' for query reports",
            )
            raise typer.Exit(1)

    # Build frequency object
    freq = ScheduleFrequency(
        type=frequency,  # type: ignore
        time=time,
        day_of_week=day_of_week,
        day_of_month=day_of_month,
    )

    # Build report object
    if dashboard_id:
        report = DashboardReport(
            dashboard_id=dashboard_id,
            format=report_format,  # type: ignore
        )
    else:
        report = QueryReport(
            metrics=metrics,
            dimensions=dimensions or [],
            format=report_format,  # type: ignore
        )

    try:
        schedule = run_async(
            create_schedule(
                user,
                name=name,
                frequency=freq,
                report=report,
                recipients=recipients,
            )
        )

        print_success(f"Created scheduled report: {schedule.name}")

        # Show summary
        summary = {
            "id": schedule.id,
            "name": schedule.name,
            "frequency": frequency,
            "time": time,
            "recipients": ", ".join(recipients),
        }
        if dashboard_id:
            summary["dashboard"] = dashboard_id
            summary["format"] = report_format
        else:
            summary["metrics"] = ", ".join(metrics)
            summary["format"] = report_format

        format_output(summary, format="table", title="New Schedule")

    except PermissionError as e:
        print_error(str(e), hint="You need member role to create schedules")
        raise typer.Exit(1)
    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)


@schedules_app.command("update")
def schedules_update(
    schedule_id: Annotated[str, typer.Argument(help="Schedule ID to update")],
    name: Annotated[
        Optional[str],
        typer.Option("--name", help="New name"),
    ] = None,
    enabled: Annotated[
        Optional[bool],
        typer.Option("--enabled/--disabled", help="Enable or disable"),
    ] = None,
    time: Annotated[
        Optional[str],
        typer.Option("--time", help="New time in HH:MM (UTC)"),
    ] = None,
    recipients: Annotated[
        Optional[list[str]],
        typer.Option("--to", help="New recipients (replaces existing)"),
    ] = None,
    format: Annotated[
        OutputFormat,
        typer.Option("--format", "-f", help="Output format"),
    ] = "table",
):
    """Update a scheduled report.

    Update schedule properties like name, time, or recipients.
    Only the creator or admins can update a schedule.

    Examples:
        metricly schedules update abc123 --name "New Name"
        metricly schedules update abc123 --disabled  # Pause schedule
        metricly schedules update abc123 --enabled   # Resume schedule
        metricly schedules update abc123 --time 08:00
        metricly schedules update abc123 --to newemail@company.com
    """
    from settings import get_settings
    if not get_settings().schedules_enabled:
        print_info("Scheduled reports coming soon. This feature is not yet enabled.")
        return

    user = require_auth()

    from services.schedules import update_schedule, get_schedule

    # Build updates dict
    updates = {}
    if name is not None:
        updates["name"] = name
    if enabled is not None:
        updates["enabled"] = enabled
    if time is not None:
        # Validate time format
        try:
            parts = time.split(":")
            if len(parts) != 2:
                raise ValueError()
            hour, minute = int(parts[0]), int(parts[1])
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError()
        except (ValueError, AttributeError):
            print_error(
                f"Invalid time format: {time}",
                hint="Use HH:MM in 24-hour format (e.g., 09:00, 14:30)",
            )
            raise typer.Exit(1)

        # Get current schedule to build updated frequency
        current = run_async(get_schedule(user, schedule_id))
        updates["frequency"] = {
            "type": current.frequency.type,
            "time": time,
            "day_of_week": current.frequency.day_of_week,
            "day_of_month": current.frequency.day_of_month,
        }
    if recipients is not None:
        updates["recipients"] = recipients

    if not updates:
        print_error(
            "No updates provided",
            hint="Use --name, --enabled/--disabled, --time, or --to",
        )
        raise typer.Exit(1)

    try:
        schedule = run_async(update_schedule(user, schedule_id, updates))

        print_success(f"Updated schedule: {schedule.name}")

        summary = {
            "id": schedule.id,
            "name": schedule.name,
            "enabled": schedule.enabled,
            "time": schedule.frequency.time,
            "recipients": ", ".join(schedule.recipients),
        }
        format_output(summary, format=format, title="Updated Schedule")

    except PermissionError as e:
        print_error(str(e), hint="Only the creator or admins can update schedules")
        raise typer.Exit(1)
    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)


@schedules_app.command("delete")
def schedules_delete(
    schedule_id: Annotated[str, typer.Argument(help="Schedule ID to delete")],
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Skip confirmation prompt"),
    ] = False,
):
    """Delete a scheduled report.

    Permanently removes the schedule. Only the creator or admins
    can delete a schedule. Requires confirmation unless --yes is passed.

    Examples:
        metricly schedules delete abc123
        metricly schedules delete abc123 --yes
    """
    from settings import get_settings
    if not get_settings().schedules_enabled:
        print_info("Scheduled reports coming soon. This feature is not yet enabled.")
        return

    user = require_auth()

    from services.schedules import get_schedule, delete_schedule

    try:
        # First get the schedule to show its name
        schedule = run_async(get_schedule(user, schedule_id))

        # Confirm deletion
        if not yes:
            confirm = typer.confirm(
                f"Delete scheduled report '{schedule.name}' ({schedule_id})?"
            )
            if not confirm:
                print_info("Cancelled")
                raise typer.Exit(0)

        # Delete it
        run_async(delete_schedule(user, schedule_id))
        print_success(f"Deleted schedule: {schedule.name}")

    except PermissionError as e:
        print_error(str(e), hint="Only the creator or admins can delete schedules")
        raise typer.Exit(1)
    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)


# ============================================================================
# Quick Metrics sub-commands
# ============================================================================


@quick_metrics_app.command("list")
def quick_metrics_list(
    format: Annotated[
        OutputFormat,
        typer.Option("--format", "-f", help="Output format"),
    ] = "table",
):
    """List all quick metrics.

    Quick metrics are user-defined calculated metrics that combine
    base metrics with arithmetic expressions. Query them using the
    qm: prefix (e.g., qm:revenue_per_order).

    Examples:
        metricly quick-metrics list
        metricly quick-metrics list --format json
    """
    user = require_auth()

    from services.quick_metrics import list_quick_metrics

    try:
        metrics = run_async(list_quick_metrics(user))

        if not metrics:
            print_info("No quick metrics found")
            print_info("Create one with: metricly quick-metrics create revenue_per_order 'total_revenue / order_count'")
            return

        # Build display data with query name
        metrics_data = []
        for m in metrics:
            metrics_data.append({
                "id": m.id,
                "name": m.name,
                "expression": m.expression,
                "query_name": f"qm:{m.name}",
                "description": m.description or "-",
            })

        format_output(
            metrics_data,
            format=format,
            columns=["id", "name", "expression", "query_name", "description"],
            title="Quick Metrics",
        )
    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)


@quick_metrics_app.command("show")
def quick_metrics_show(
    metric_id: Annotated[str, typer.Argument(help="Quick metric ID")],
    format: Annotated[
        OutputFormat,
        typer.Option("--format", "-f", help="Output format"),
    ] = "table",
):
    """Show details of a quick metric.

    Displays the full configuration of a quick metric including
    its expression and the base metrics it references.

    Examples:
        metricly quick-metrics show abc123
        metricly quick-metrics show abc123 --format json
    """
    user = require_auth()

    from services.quick_metrics import get_quick_metric

    try:
        metric = run_async(get_quick_metric(user, metric_id))

        if format == "json":
            format_output(metric.model_dump(mode="json"), format=format)
        else:
            summary = {
                "id": metric.id,
                "name": metric.name,
                "query_name": f"qm:{metric.name}",
                "expression": metric.expression,
                "base_metrics": ", ".join(metric.base_metrics),
                "description": metric.description or "-",
                "created_by": metric.created_by,
                "created_at": metric.created_at.strftime("%Y-%m-%d %H:%M"),
                "updated_at": metric.updated_at.strftime("%Y-%m-%d %H:%M"),
            }

            format_output(summary, format=format, title=f"Quick Metric: {metric.name}")

            # Show usage hint
            console.print()
            print_info(f"Query this metric with: metricly query -m qm:{metric.name} -g month")

    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)


@quick_metrics_app.command("create")
def quick_metrics_create(
    name: Annotated[str, typer.Argument(help="Metric name (e.g., revenue_per_order)")],
    expression: Annotated[str, typer.Argument(help="Expression (e.g., 'total_revenue / order_count')")],
    description: Annotated[
        Optional[str],
        typer.Option("--description", "-d", help="Description"),
    ] = None,
    format: Annotated[
        OutputFormat,
        typer.Option("--format", "-f", help="Output format"),
    ] = "table",
):
    """Create a quick metric from an expression.

    Quick metrics are calculated from existing metrics using arithmetic
    expressions. Supported operators: +, -, *, /

    Once created, query them using the qm: prefix.

    Examples:
        metricly quick-metrics create revenue_per_order "total_revenue / order_count"
        metricly quick-metrics create gross_margin "(revenue - cogs) / revenue * 100" -d "Gross margin percentage"

    Then query with:
        metricly query -m qm:revenue_per_order -g month
    """
    user = require_auth()

    from services.quick_metrics import create_quick_metric, ExpressionError

    try:
        metric = run_async(
            create_quick_metric(
                user,
                name=name,
                expression=expression,
                description=description,
            )
        )

        print_success(f"Created quick metric: {metric.name}")

        summary = {
            "id": metric.id,
            "name": metric.name,
            "query_name": f"qm:{metric.name}",
            "expression": metric.expression,
            "base_metrics": ", ".join(metric.base_metrics),
        }
        format_output(summary, format=format, title="New Quick Metric")

        # Show usage hint
        console.print()
        print_info(f"Query this metric with: metricly query -m qm:{metric.name} -g month")

    except ExpressionError as e:
        print_error(f"Invalid expression: {e.message}")
        raise typer.Exit(1)
    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)


@quick_metrics_app.command("update")
def quick_metrics_update(
    metric_id: Annotated[str, typer.Argument(help="Quick metric ID to update")],
    name: Annotated[
        Optional[str],
        typer.Option("--name", help="New name"),
    ] = None,
    expression: Annotated[
        Optional[str],
        typer.Option("--expression", "-e", help="New expression"),
    ] = None,
    description: Annotated[
        Optional[str],
        typer.Option("--description", "-d", help="New description"),
    ] = None,
    format: Annotated[
        OutputFormat,
        typer.Option("--format", "-f", help="Output format"),
    ] = "table",
):
    """Update a quick metric.

    Update the name, expression, or description of an existing quick metric.

    Examples:
        metricly quick-metrics update abc123 --expression "total_revenue / orders"
        metricly quick-metrics update abc123 --name avg_order_value
        metricly quick-metrics update abc123 -d "Average value per order"
    """
    user = require_auth()

    from services.quick_metrics import update_quick_metric, ExpressionError

    # Check that at least one update is provided
    if name is None and expression is None and description is None:
        print_error(
            "No updates provided",
            hint="Use --name, --expression, or --description",
        )
        raise typer.Exit(1)

    try:
        metric = run_async(
            update_quick_metric(
                user,
                metric_id=metric_id,
                name=name,
                expression=expression,
                description=description,
            )
        )

        print_success(f"Updated quick metric: {metric.name}")

        summary = {
            "id": metric.id,
            "name": metric.name,
            "query_name": f"qm:{metric.name}",
            "expression": metric.expression,
            "base_metrics": ", ".join(metric.base_metrics),
        }
        format_output(summary, format=format, title="Updated Quick Metric")

    except ExpressionError as e:
        print_error(f"Invalid expression: {e.message}")
        raise typer.Exit(1)
    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)


@quick_metrics_app.command("delete")
def quick_metrics_delete(
    metric_id: Annotated[str, typer.Argument(help="Quick metric ID to delete")],
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Skip confirmation prompt"),
    ] = False,
):
    """Delete a quick metric.

    Permanently removes the quick metric. Requires confirmation
    unless --yes is passed.

    Examples:
        metricly quick-metrics delete abc123
        metricly quick-metrics delete abc123 --yes
    """
    user = require_auth()

    from services.quick_metrics import get_quick_metric, delete_quick_metric

    try:
        # First get the metric to show its name
        metric = run_async(get_quick_metric(user, metric_id))

        # Confirm deletion
        if not yes:
            confirm = typer.confirm(
                f"Delete quick metric '{metric.name}' ({metric_id})?"
            )
            if not confirm:
                print_info("Cancelled")
                raise typer.Exit(0)

        # Delete it
        run_async(delete_quick_metric(user, metric_id))
        print_success(f"Deleted quick metric: {metric.name}")

    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)


# ============================================================================
# Context sub-commands
# ============================================================================


@context_app.command("get")
def context_get(
    format: Annotated[
        OutputFormat,
        typer.Option("--format", "-f", help="Output format"),
    ] = "table",
):
    """Get your accumulated user context.

    Shows preferences, favorites, and notes that have been stored
    across sessions. This context is used by agents to personalize
    responses.

    Examples:
        metricly context get
        metricly context get --format json
    """
    user = require_auth()

    from services.context import get_user_preferences

    try:
        prefs = run_async(get_user_preferences(user.uid))

        if format == "json":
            format_output(prefs.model_dump(), format=format)
        else:
            # Display in sections
            console.print("\n[bold]Preferences[/]")
            has_prefs = False
            if prefs.default_currency:
                console.print(f"  default_currency: {prefs.default_currency}")
                has_prefs = True
            if prefs.default_grain:
                console.print(f"  default_grain: {prefs.default_grain}")
                has_prefs = True
            if prefs.decimal_places is not None:
                console.print(f"  decimal_places: {prefs.decimal_places}")
                has_prefs = True
            if prefs.preferred_chart_type:
                console.print(f"  preferred_chart_type: {prefs.preferred_chart_type}")
                has_prefs = True
            if not has_prefs:
                console.print("  (none)")

            console.print("\n[bold]Favorite Metrics[/]")
            if prefs.favorite_metrics:
                for fav in prefs.favorite_metrics:
                    console.print(f"  - {fav}")
            else:
                console.print("  (none)")

            console.print("\n[bold]Notes[/]")
            if prefs.notes:
                for subject, note in prefs.notes.items():
                    console.print(f"  [cyan]{subject}[/]: {note}")
            else:
                console.print("  (none)")

            if prefs.custom_instructions:
                console.print(f"\n[bold]Custom Instructions[/]\n  {prefs.custom_instructions}")

            console.print()

    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)


@context_app.command("update")
def context_update(
    preference: Annotated[
        Optional[list[str]],
        typer.Option("--pref", "-p", help="Set preference as key=value (e.g., default_grain=month)"),
    ] = None,
    favorite: Annotated[
        Optional[list[str]],
        typer.Option("--favorite", help="Set favorite metrics (replaces existing)"),
    ] = None,
    instructions: Annotated[
        Optional[str],
        typer.Option("--instructions", "-i", help="Set custom instructions"),
    ] = None,
    format: Annotated[
        OutputFormat,
        typer.Option("--format", "-f", help="Output format"),
    ] = "table",
):
    """Update your user context.

    Store preferences, favorites, and custom instructions that persist
    across sessions. Updates are merged with existing context.

    Valid preference keys:
        default_currency, default_grain, decimal_places, preferred_chart_type

    Examples:
        metricly context update --pref default_grain=month
        metricly context update --pref default_currency=EUR --pref decimal_places=2
        metricly context update --favorite total_revenue --favorite churn_rate
        metricly context update --instructions "Always show YoY comparisons"
    """
    user = require_auth()

    from services.context import update_user_preferences

    # Build updates dict
    updates = {}

    if preference:
        for p in preference:
            if "=" not in p:
                print_error(f"Invalid preference format: {p} (expected key=value)")
                raise typer.Exit(1)
            key, value = p.split("=", 1)
            # Handle numeric values
            if key == "decimal_places":
                try:
                    value = int(value)
                except ValueError:
                    print_error(f"decimal_places must be an integer")
                    raise typer.Exit(1)
            updates[key] = value

    if favorite:
        updates["favorite_metrics"] = favorite

    if instructions:
        updates["custom_instructions"] = instructions

    if not updates:
        print_error("No updates specified")
        raise typer.Exit(1)

    try:
        prefs = run_async(update_user_preferences(user.uid, updates))

        print_success("Updated context")

        if format == "json":
            format_output(prefs.model_dump(), format=format)
        else:
            summary = {"updated_fields": list(updates.keys())}
            format_output(summary, format=format, title="Context Updated")

    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)


@context_app.command("add-note")
def context_add_note(
    subject: Annotated[str, typer.Argument(help="Subject (metric name, dashboard, etc.)")],
    note: Annotated[str, typer.Argument(help="Note content")],
    format: Annotated[
        OutputFormat,
        typer.Option("--format", "-f", help="Output format"),
    ] = "table",
):
    """Add a note about a metric, dashboard, or data observation.

    Notes are persisted and available in future sessions. Use this to
    record important context about your data.

    Examples:
        metricly context add-note total_revenue "Excludes refunds since Q2 2024"
        metricly context add-note churn_rate "Calculated on 30-day window"
    """
    user = require_auth()

    from services.context import add_note as add_note_fn

    try:
        prefs = run_async(add_note_fn(user.uid, subject, note))

        print_success(f"Added note for '{subject}'")

        if format == "json":
            format_output(prefs.model_dump(), format=format)
        else:
            summary = {
                "subject": subject,
                "note": note,
            }
            format_output(summary, format=format, title="Note Added")

    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
