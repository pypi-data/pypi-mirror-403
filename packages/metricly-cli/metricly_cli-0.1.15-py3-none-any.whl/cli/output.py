"""CLI Output Formatters - Rich tables, JSON, CSV output.

Provides consistent output formatting across all CLI commands.
"""

import csv
import io
import json
from typing import Any, Literal

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


# Shared console instance
console = Console()

OutputFormat = Literal["table", "json", "yaml", "csv"]


def print_table(
    data: list[dict],
    columns: list[str] | None = None,
    title: str | None = None,
):
    """Print data as a Rich table.

    Args:
        data: List of row dictionaries
        columns: Column names (defaults to keys from first row)
        title: Optional table title
    """
    if not data:
        console.print("[dim]No data to display[/]")
        return

    if columns is None:
        columns = list(data[0].keys())

    table = Table(title=title, show_header=True, header_style="bold")

    for col in columns:
        # Don't wrap ID columns so users can copy-paste full IDs
        if col.lower() == "id":
            table.add_column(col, no_wrap=True, overflow="fold")
        else:
            table.add_column(col)

    for row in data:
        table.add_row(*[_format_cell(row.get(col)) for col in columns])

    console.print(table)


def _format_cell(value: Any) -> str:
    """Format a cell value for display."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, float):
        # Format floats nicely
        if value == int(value):
            return str(int(value))
        return f"{value:,.2f}"
    return str(value)


def print_json(data: Any):
    """Print data as formatted JSON.

    Args:
        data: Any JSON-serializable data
    """
    console.print_json(json.dumps(data, indent=2, default=str))


def print_yaml(data: Any):
    """Print data as YAML.

    Args:
        data: Any data to format as YAML
    """
    try:
        import yaml

        console.print(yaml.dump(data, default_flow_style=False, sort_keys=False))
    except ImportError:
        # Fall back to JSON if PyYAML not installed
        console.print("[yellow]PyYAML not installed, showing as JSON:[/]")
        print_json(data)


def print_csv(data: list[dict], columns: list[str] | None = None):
    """Print data as CSV.

    Args:
        data: List of row dictionaries
        columns: Column names (defaults to keys from first row)
    """
    if not data:
        return

    if columns is None:
        columns = list(data[0].keys())

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=columns, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(data)

    console.print(output.getvalue(), highlight=False)


def format_output(
    data: Any,
    format: OutputFormat = "table",
    columns: list[str] | None = None,
    title: str | None = None,
):
    """Format and print data according to output format.

    Args:
        data: Data to output (list of dicts for table/csv, any for json/yaml)
        format: Output format
        columns: Column names for table/csv output
        title: Title for table output
    """
    if format == "table":
        if isinstance(data, list):
            print_table(data, columns=columns, title=title)
        else:
            # Single item - show as key-value pairs
            print_key_value(data)
    elif format == "json":
        print_json(data)
    elif format == "yaml":
        print_yaml(data)
    elif format == "csv":
        if isinstance(data, list):
            print_csv(data, columns=columns)
        else:
            console.print("[red]CSV format requires list data[/]")
    else:
        console.print(f"[red]Unknown format: {format}[/]")


def print_key_value(data: dict, title: str | None = None):
    """Print a single object as key-value pairs.

    Args:
        data: Dictionary to display
        title: Optional panel title
    """
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(style="bold cyan")
    table.add_column()

    for key, value in data.items():
        table.add_row(key, _format_cell(value))

    if title:
        console.print(Panel(table, title=title))
    else:
        console.print(table)


def print_success(message: str):
    """Print a success message.

    Args:
        message: Success message
    """
    console.print(f"[green]✓[/] {message}")


def print_error(message: str, hint: str | None = None):
    """Print an error message.

    Args:
        message: Error message
        hint: Optional hint for resolving the error
    """
    console.print(f"[red]✗ Error:[/] {message}")
    if hint:
        console.print(f"[dim]  Hint: {hint}[/]")


def print_warning(message: str):
    """Print a warning message.

    Args:
        message: Warning message
    """
    console.print(f"[yellow]⚠[/] {message}")


def print_info(message: str):
    """Print an info message.

    Args:
        message: Info message
    """
    console.print(f"[blue]ℹ[/] {message}")


def print_user_context(email: str, org_id: str, role: str, org_name: str | None = None):
    """Print user context in a nice format.

    Args:
        email: User email
        org_id: Organization ID
        role: User's role
        org_name: Optional organization name
    """
    org_display = org_name if org_name else org_id

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(style="bold")
    table.add_column()

    table.add_row("Email", email)
    table.add_row("Organization", org_display)
    table.add_row("Role", _format_role(role))

    console.print(Panel(table, title="[bold]Current User[/]"))


def _format_role(role: str) -> str:
    """Format role with color."""
    colors = {
        "owner": "magenta",
        "admin": "red",
        "member": "blue",
        "viewer": "dim",
    }
    color = colors.get(role, "white")
    return f"[{color}]{role}[/{color}]"


def print_visualization_suggestion(widget_type: str, rationale: str):
    """Print a visualization suggestion.

    Args:
        widget_type: Suggested widget type
        rationale: Reason for the suggestion
    """
    console.print()
    console.print(f"[bold]Suggested visualization:[/] {widget_type}")
    console.print(f"[dim]{rationale}[/]")
