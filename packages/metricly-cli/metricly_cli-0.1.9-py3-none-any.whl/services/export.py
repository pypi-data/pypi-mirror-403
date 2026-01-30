"""Data export services - export query results and dashboard data.

Provides export functionality for MCP, CLI, and chat consumers.
Supports CSV and JSON formats with optional file output.
"""

import csv
import io
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from services.auth import UserContext
from services.queries import QueryParams, query_metrics
from services.dashboards import get_dashboard


@dataclass
class ExportResult:
    """Result of a data export operation."""

    format: Literal["csv", "json"]
    row_count: int
    columns: list[str]
    content: str  # CSV string or JSON string
    saved_to: str | None = None  # File path if written to disk


def _to_csv(data: list[dict], columns: list[str]) -> str:
    """Convert data to CSV string."""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=columns, extrasaction="ignore")
    writer.writeheader()
    for row in data:
        writer.writerow(row)
    return output.getvalue()


def _to_json(data: list[dict]) -> str:
    """Convert data to JSON string."""
    return json.dumps(data, indent=2, default=str)


def _write_to_file(content: str, output_path: str) -> str:
    """Write content to file, creating directories as needed."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return str(path.absolute())


async def export_query_data(
    user: UserContext,
    params: QueryParams,
    format: Literal["csv", "json"] = "csv",
    output_path: str | None = None,
) -> ExportResult:
    """Export query results to CSV or JSON.

    Args:
        user: Authenticated user context
        params: Query parameters for data
        format: Output format (csv, json)
        output_path: If provided, write to this file

    Returns:
        ExportResult with data and optional file path
    """
    # Execute query
    result = await query_metrics(user.org_id, params)

    # Format data
    if format == "csv":
        content = _to_csv(result.data, result.columns)
    else:
        content = _to_json(result.data)

    # Write to file if path provided
    saved_to = None
    if output_path:
        saved_to = _write_to_file(content, output_path)

    return ExportResult(
        format=format,
        row_count=result.row_count,
        columns=result.columns,
        content=content,
        saved_to=saved_to,
    )


async def export_dashboard_data(
    user: UserContext,
    dashboard_id: str,
    format: Literal["csv", "json"] = "csv",
    output_path: str | None = None,
) -> ExportResult:
    """Export all widget data from a dashboard.

    Executes each widget's query and combines results.
    For CSV, creates separate sections per widget.
    For JSON, creates a nested structure.

    Args:
        user: Authenticated user context
        dashboard_id: Dashboard to export
        format: Output format (csv, json)
        output_path: If provided, write to this file

    Returns:
        ExportResult with combined data

    Raises:
        ValueError: If dashboard not found or access denied
    """
    # Get dashboard
    dashboard = await get_dashboard(user, dashboard_id)

    # Collect all widget queries
    all_data: list[dict] = []
    all_columns: set[str] = set()
    widget_results: dict[str, list[dict]] = {}
    total_rows = 0

    for page in dashboard.pages:
        for section in page.sections:
            for widget in section.widgets:
                # Build query params from widget query definition
                query = widget.query
                if not query.metrics:
                    continue

                params = QueryParams(
                    metrics=query.metrics,
                    dimensions=query.dimensions,
                    grain=query.grain if query.grain and query.grain != "$grain" else None,
                    limit=query.limit,
                    order_by=query.order_by[0] if query.order_by else None,
                )

                try:
                    result = await query_metrics(user.org_id, params)

                    # Tag each row with widget info for combined export
                    for row in result.data:
                        row["_widget_id"] = widget.id
                        row["_widget_title"] = widget.title

                    all_data.extend(result.data)
                    all_columns.update(result.columns)
                    widget_results[widget.id] = {
                        "title": widget.title,
                        "data": result.data,
                        "columns": result.columns,
                    }
                    total_rows += result.row_count
                except Exception:
                    # Skip widgets that fail to query
                    continue

    # Add metadata columns
    columns = ["_widget_id", "_widget_title"] + sorted(all_columns)

    # Format data
    if format == "csv":
        content = _to_csv(all_data, columns)
    else:
        # For JSON, use the structured widget_results
        content = json.dumps(
            {
                "dashboard_id": dashboard.id,
                "dashboard_title": dashboard.title,
                "widgets": widget_results,
            },
            indent=2,
            default=str,
        )

    # Write to file if path provided
    saved_to = None
    if output_path:
        saved_to = _write_to_file(content, output_path)

    return ExportResult(
        format=format,
        row_count=total_rows,
        columns=columns,
        content=content,
        saved_to=saved_to,
    )
