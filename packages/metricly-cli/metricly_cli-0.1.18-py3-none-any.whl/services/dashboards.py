"""Dashboard services - CRUD operations and widget management.

Provides typed dashboard operations for MCP, CLI, and chat consumers.
Wraps storage.py with Pydantic validation and permission checks.
"""

from dataclasses import dataclass
from typing import Literal, Optional
import uuid

from generated.dashboard_types import (
    DashboardDefinition,
    PageDefinition,
    SectionDefinition,
    WidgetDefinition,
)
from services.auth import UserContext, require_role

import storage


# ============================================================================
# Widget Default Widths (out of 10-column grid)
# ============================================================================

DEFAULT_WIDGET_WIDTHS: dict[str, int] = {
    "kpi": 2,           # 5 per row
    "donut": 3,         # 3 per row
    "heatmap": 5,       # 2 per row
    "area_chart": 10,   # full width
    "line_chart": 10,   # full width
    "bar_chart": 10,    # full width
    "table": 10,        # full width
}


# ============================================================================
# Exceptions
# ============================================================================


class ConflictError(Exception):
    """Raised when optimistic locking detects a version conflict.

    This occurs when a dashboard has been modified by another client
    since it was last read. The client should re-fetch the dashboard
    and retry their changes.
    """

    def __init__(self, message: str, current_version: int, expected_version: int):
        super().__init__(message)
        self.current_version = current_version
        self.expected_version = expected_version


# ============================================================================
# Helper Functions (for atomic operations)
# ============================================================================


def _find_widget_location(
    dashboard: DashboardDefinition, widget_id: str
) -> tuple[int, int, int] | None:
    """Find widget by ID.

    Args:
        dashboard: Dashboard to search
        widget_id: Widget ID to find

    Returns:
        Tuple of (page_index, section_index, widget_index) or None if not found
    """
    for pi, page in enumerate(dashboard.pages):
        for si, section in enumerate(page.sections):
            for wi, widget in enumerate(section.widgets):
                if widget.id == widget_id:
                    return (pi, si, wi)
    return None


def _find_page_index(dashboard: DashboardDefinition, page_id: str) -> int | None:
    """Find page by ID.

    Args:
        dashboard: Dashboard to search
        page_id: Page ID to find

    Returns:
        Page index or None if not found
    """
    for i, page in enumerate(dashboard.pages):
        if page.id == page_id:
            return i
    return None


def _get_widget_by_id(
    dashboard: DashboardDefinition, widget_id: str
) -> WidgetDefinition | None:
    """Get widget by ID.

    Args:
        dashboard: Dashboard to search
        widget_id: Widget ID to find

    Returns:
        WidgetDefinition or None if not found
    """
    loc = _find_widget_location(dashboard, widget_id)
    if loc:
        pi, si, wi = loc
        return dashboard.pages[pi].sections[si].widgets[wi]
    return None


# ============================================================================
# Types
# ============================================================================


@dataclass
class DashboardSummary:
    """Summary info for dashboard listing."""

    id: str
    title: str
    description: str | None
    owner: str
    visibility: Literal["private", "org"]
    created_at: str
    updated_at: str


@dataclass
class DashboardList:
    """Result of list_dashboards."""

    personal: list[DashboardSummary]
    team: list[DashboardSummary]


# ============================================================================
# CRUD Operations
# ============================================================================


async def list_dashboards(user: UserContext) -> DashboardList:
    """List dashboards visible to user.

    Args:
        user: Authenticated user context

    Returns:
        DashboardList with personal and team sections
    """
    result = storage.list_dashboards(user.org_id, user.uid)

    def to_summary(d: dict) -> DashboardSummary:
        return DashboardSummary(
            id=d.get("id", ""),
            title=d.get("title", "Untitled"),
            description=d.get("description"),
            owner=d.get("owner", ""),
            visibility=d.get("visibility", "private"),
            created_at=d.get("created_at", ""),
            updated_at=d.get("updated_at", ""),
        )

    return DashboardList(
        personal=[to_summary(d) for d in result.get("personal", [])],
        team=[to_summary(d) for d in result.get("team", [])],
    )


def _repair_dashboard_data(data: dict) -> dict:
    """Repair corrupted dashboard data to pass Pydantic validation.

    Handles issues from older CLI versions:
    - Widgets without IDs: Auto-generates UUIDs
    - Corrupted controls: Fixes malformed date_range structure

    Args:
        data: Raw dashboard data from storage

    Returns:
        Repaired dashboard data
    """
    # Repair pages and widgets
    if "pages" in data:
        for page in data["pages"]:
            # Ensure page has ID
            if not page.get("id"):
                page["id"] = str(uuid.uuid4())

            for section in page.get("sections", []):
                for widget in section.get("widgets", []):
                    # Ensure widget has ID (handle missing, None, or empty string)
                    if not widget.get("id"):
                        widget["id"] = str(uuid.uuid4())

    # Repair corrupted controls structure
    # Some older versions incorrectly nested grain/comparison inside date_range
    if "controls" in data:
        controls = data["controls"]
        date_range = controls.get("date_range", {})

        # Check for corrupted structure: date_range contains nested date_range
        if "date_range" in date_range:
            # Extract the actual date_range config from nested structure
            nested_dr = date_range.pop("date_range")
            # Remove incorrectly nested fields
            date_range.pop("grain", None)
            date_range.pop("comparison", None)
            # Merge the nested date_range up
            date_range.update(nested_dr)

        # Ensure date_range has required 'mode' field
        if date_range and "mode" not in date_range:
            # Infer mode from content
            if "preset" in date_range:
                date_range["mode"] = "relative"
            elif "start" in date_range or "end" in date_range:
                date_range["mode"] = "absolute"
            else:
                date_range["mode"] = "relative"
                date_range["preset"] = "last_30_days"

        controls["date_range"] = date_range

    return data


async def get_dashboard(user: UserContext, dashboard_id: str) -> DashboardDefinition:
    """Get a dashboard by ID.

    Args:
        user: Authenticated user context
        dashboard_id: Dashboard ID

    Returns:
        Validated DashboardDefinition

    Raises:
        ValueError: If dashboard not found or access denied
    """
    data = storage.get_dashboard(user.org_id, dashboard_id, user.uid)

    if not data:
        raise ValueError(f"Dashboard '{dashboard_id}' not found or access denied")

    # Repair any corrupted data (e.g., missing widget IDs from older CLI versions)
    data = _repair_dashboard_data(data)

    return DashboardDefinition.model_validate(data)


async def create_dashboard(
    user: UserContext,
    title: str,
    description: str | None = None,
    visibility: Literal["private", "org"] = "private",
    pages: list[dict] | None = None,
    controls: dict | None = None,
) -> DashboardDefinition:
    """Create a new dashboard.

    Args:
        user: Authenticated user context
        title: Dashboard title
        description: Optional description
        visibility: "private" or "org"
        pages: Optional initial pages (defaults to empty page)
        controls: Optional dashboard controls config

    Returns:
        Created DashboardDefinition
    """
    # Build default controls if not provided
    if controls is None:
        controls = {
            "date_range": {"mode": "relative", "preset": "last_30_days"},
            "grain": "month",
            "comparison": "none",
        }

    # Build default page if not provided
    if pages is None:
        pages = [
            {
                "id": str(uuid.uuid4()),
                "title": "Overview",
                "sections": [],
            }
        ]

    dashboard_data = {
        "title": title,
        "description": description,
        "visibility": visibility,
        "controls": controls,
        "pages": pages,
    }

    result = storage.create_dashboard(user.org_id, user.uid, dashboard_data)
    return DashboardDefinition.model_validate(result)


async def create_dashboard_from_definition(
    user: UserContext,
    definition: dict,
) -> DashboardDefinition:
    """Create a dashboard from a full definition (e.g., from YAML file).

    Args:
        user: Authenticated user context
        definition: Dashboard definition dict

    Returns:
        Created DashboardDefinition
    """
    # Remove fields that will be set by storage
    definition.pop("id", None)
    definition.pop("owner", None)
    definition.pop("created_at", None)
    definition.pop("updated_at", None)
    definition.pop("created_by", None)

    # Validate before saving
    DashboardDefinition.model_validate({
        **definition,
        "id": "temp",
        "owner": user.uid,
        "created_at": "2000-01-01T00:00:00Z",
        "updated_at": "2000-01-01T00:00:00Z",
        "created_by": user.uid,
    })

    result = storage.create_dashboard(user.org_id, user.uid, definition)
    return DashboardDefinition.model_validate(result)


async def update_dashboard(
    user: UserContext,
    dashboard_id: str,
    updates: dict,
    expected_version: int | None = None,
) -> DashboardDefinition:
    """Update a dashboard.

    Args:
        user: Authenticated user context
        dashboard_id: Dashboard ID
        updates: Fields to update
        expected_version: If provided, reject if current version doesn't match (optimistic locking)

    Returns:
        Updated DashboardDefinition

    Raises:
        ValueError: If dashboard not found or user is not owner
        PermissionError: If user lacks permission
        ConflictError: If version mismatch detected (optimistic locking)
    """
    result = storage.update_dashboard(
        user.org_id, dashboard_id, user.uid, updates, expected_version
    )

    if not result:
        raise ValueError(
            f"Dashboard '{dashboard_id}' not found or you are not the owner"
        )

    return DashboardDefinition.model_validate(result)


async def delete_dashboard(user: UserContext, dashboard_id: str) -> bool:
    """Delete a dashboard.

    Args:
        user: Authenticated user context
        dashboard_id: Dashboard ID

    Returns:
        True if deleted

    Raises:
        ValueError: If dashboard not found or user is not owner
    """
    success = storage.delete_dashboard(user.org_id, dashboard_id, user.uid)

    if not success:
        raise ValueError(
            f"Dashboard '{dashboard_id}' not found or you are not the owner"
        )

    return True


# ============================================================================
# Dashboard Parity Operations
# ============================================================================


async def duplicate_dashboard(
    user: UserContext,
    dashboard_id: str,
    new_title: str | None = None,
) -> DashboardDefinition:
    """Duplicate a dashboard with all its pages, sections, and widgets.

    Creates a private copy owned by the current user.
    All widget and page IDs are regenerated to avoid conflicts.

    Args:
        user: Authenticated user context
        dashboard_id: ID of dashboard to duplicate
        new_title: Title for new dashboard (default: "Copy of {original_title}")

    Returns:
        Created DashboardDefinition (always private, owned by user)

    Raises:
        ValueError: If source dashboard not found or access denied
    """
    # Get source dashboard (includes permission check)
    source = await get_dashboard(user, dashboard_id)

    # Build new title
    title = new_title or f"Copy of {source.title}"

    # Deep copy pages with new IDs
    def regenerate_ids(pages: list) -> list:
        new_pages = []
        for page in pages:
            page_dict = page.model_dump() if hasattr(page, "model_dump") else dict(page)
            page_dict["id"] = str(uuid.uuid4())

            # Regenerate widget IDs in all sections
            new_sections = []
            for section in page_dict.get("sections", []):
                section_copy = dict(section)
                new_widgets = []
                for widget in section_copy.get("widgets", []):
                    widget_copy = dict(widget)
                    widget_copy["id"] = str(uuid.uuid4())
                    new_widgets.append(widget_copy)
                section_copy["widgets"] = new_widgets
                new_sections.append(section_copy)
            page_dict["sections"] = new_sections
            new_pages.append(page_dict)
        return new_pages

    new_pages = regenerate_ids(source.pages)

    # Create new dashboard (always private)
    return await create_dashboard(
        user,
        title=title,
        description=source.description,
        visibility="private",
        pages=new_pages,
        controls=source.controls.model_dump(),
    )


async def share_dashboard(
    user: UserContext,
    dashboard_id: str,
    visibility: Literal["private", "org"],
) -> DashboardDefinition:
    """Toggle dashboard visibility between private and shared.

    Args:
        user: Authenticated user context (must be owner)
        dashboard_id: Dashboard ID
        visibility: "private" or "org"

    Returns:
        Updated DashboardDefinition

    Raises:
        ValueError: If dashboard not found or user is not owner
    """
    if visibility not in ("private", "org"):
        raise ValueError(f"Invalid visibility: {visibility}. Must be 'private' or 'org'")

    return await update_dashboard(user, dashboard_id, {"visibility": visibility})


async def set_dashboard_controls(
    user: UserContext,
    dashboard_id: str,
    date_range: dict | None = None,
    grain: str | None = None,
    comparison: str | None = None,
) -> DashboardDefinition:
    """Update dashboard controls (date_range, grain, comparison).

    Only provided fields are updated; others remain unchanged.

    Args:
        user: Authenticated user context
        dashboard_id: Dashboard ID
        date_range: Date range config (mode, preset/start_date/end_date)
        grain: Time granularity (day, week, month, quarter, year)
        comparison: Comparison mode (none, previous_period, same_period_last_year)

    Returns:
        Updated DashboardDefinition

    Raises:
        ValueError: If dashboard not found, user is not owner, or invalid values
    """
    # Validate grain if provided
    valid_grains = {"day", "week", "month", "quarter", "year"}
    if grain is not None and grain not in valid_grains:
        raise ValueError(f"Invalid grain: {grain}. Must be one of: {', '.join(valid_grains)}")

    # Validate comparison if provided
    valid_comparisons = {"none", "previous_period", "same_period_last_year"}
    if comparison is not None and comparison not in valid_comparisons:
        raise ValueError(f"Invalid comparison: {comparison}. Must be one of: {', '.join(valid_comparisons)}")

    # Get current dashboard to merge controls
    dashboard = await get_dashboard(user, dashboard_id)
    current_controls = dashboard.controls.model_dump()

    # Merge provided controls
    if date_range is not None:
        current_controls["date_range"] = date_range
    if grain is not None:
        current_controls["grain"] = grain
    if comparison is not None:
        current_controls["comparison"] = comparison

    return await update_dashboard(user, dashboard_id, {"controls": current_controls})


# ============================================================================
# Widget Operations
# ============================================================================


async def add_widget(
    user: UserContext,
    dashboard_id: str,
    widget: dict,
    page_index: int = 0,
    section_index: int = 0,
    expected_version: int | None = None,
) -> DashboardDefinition:
    """Add a widget to a dashboard.

    Args:
        user: Authenticated user context
        dashboard_id: Dashboard ID
        widget: Widget definition dict
        page_index: Index of page to add to
        section_index: Index of section within page
        expected_version: If provided, reject if current version doesn't match (optimistic locking)

    Returns:
        Updated DashboardDefinition

    Raises:
        ValueError: If dashboard/page/section not found or validation fails
        ConflictError: If version mismatch detected (optimistic locking)
    """
    # Get current dashboard
    dashboard = await get_dashboard(user, dashboard_id)

    # Use dashboard version if expected_version not provided but we need atomic check
    effective_version = expected_version if expected_version is not None else dashboard.version

    # Validate widget - ensure ID exists (handle missing, None, or empty string)
    if not widget.get("id"):
        widget["id"] = str(uuid.uuid4())

    # Apply default width based on widget type if not specified
    if not widget.get("width"):
        widget_type = widget.get("type", "")
        widget["width"] = DEFAULT_WIDGET_WIDTHS.get(widget_type, 5)

    validated_widget = WidgetDefinition.model_validate(widget)

    # Get pages as mutable list
    pages = [p.model_dump() for p in dashboard.pages]

    # Validate indices
    if page_index < 0 or page_index >= len(pages):
        raise ValueError(f"Page index {page_index} out of range (0-{len(pages)-1})")

    page = pages[page_index]
    sections = page.get("sections", [])

    if section_index < 0 or section_index >= len(sections):
        # Create section if it doesn't exist and index is 0
        if section_index == 0 and len(sections) == 0:
            sections.append({"widgets": []})
        else:
            raise ValueError(
                f"Section index {section_index} out of range (0-{len(sections)-1})"
            )

    # Add widget to section
    sections[section_index]["widgets"].append(validated_widget.model_dump())
    pages[page_index]["sections"] = sections

    # Update dashboard with version check
    return await update_dashboard(user, dashboard_id, {"pages": pages}, effective_version)


async def remove_widget(
    user: UserContext,
    dashboard_id: str,
    page_index: int,
    section_index: int,
    widget_index: int,
    expected_version: int | None = None,
) -> DashboardDefinition:
    """Remove a widget from a dashboard.

    Args:
        user: Authenticated user context
        dashboard_id: Dashboard ID
        page_index: Index of page
        section_index: Index of section within page
        widget_index: Index of widget within section
        expected_version: If provided, reject if current version doesn't match (optimistic locking)

    Returns:
        Updated DashboardDefinition

    Raises:
        ValueError: If indices are invalid
        ConflictError: If version mismatch detected (optimistic locking)
    """
    # Get current dashboard
    dashboard = await get_dashboard(user, dashboard_id)

    # Use dashboard version if expected_version not provided but we need atomic check
    effective_version = expected_version if expected_version is not None else dashboard.version

    # Get pages as mutable list
    pages = [p.model_dump() for p in dashboard.pages]

    # Validate indices
    if page_index < 0 or page_index >= len(pages):
        raise ValueError(f"Page index {page_index} out of range")

    sections = pages[page_index].get("sections", [])
    if section_index < 0 or section_index >= len(sections):
        raise ValueError(f"Section index {section_index} out of range")

    widgets = sections[section_index].get("widgets", [])
    if widget_index < 0 or widget_index >= len(widgets):
        raise ValueError(f"Widget index {widget_index} out of range")

    # Remove widget
    widgets.pop(widget_index)
    pages[page_index]["sections"][section_index]["widgets"] = widgets

    # Update dashboard with version check
    return await update_dashboard(user, dashboard_id, {"pages": pages}, effective_version)


async def update_widget(
    user: UserContext,
    dashboard_id: str,
    page_index: int,
    section_index: int,
    widget_index: int,
    updates: dict,
    expected_version: int | None = None,
) -> DashboardDefinition:
    """Update a specific widget in a dashboard.

    Args:
        user: Authenticated user context
        dashboard_id: Dashboard ID
        page_index: Index of page
        section_index: Index of section within page
        widget_index: Index of widget within section
        updates: Fields to update on the widget
        expected_version: If provided, reject if current version doesn't match (optimistic locking)

    Returns:
        Updated DashboardDefinition

    Raises:
        ValueError: If indices are invalid or validation fails
        ConflictError: If version mismatch detected (optimistic locking)
    """
    # Get current dashboard
    dashboard = await get_dashboard(user, dashboard_id)

    # Use dashboard version if expected_version not provided but we need atomic check
    effective_version = expected_version if expected_version is not None else dashboard.version

    # Get pages as mutable list
    pages = [p.model_dump() for p in dashboard.pages]

    # Validate indices
    if page_index < 0 or page_index >= len(pages):
        raise ValueError(f"Page index {page_index} out of range")

    sections = pages[page_index].get("sections", [])
    if section_index < 0 or section_index >= len(sections):
        raise ValueError(f"Section index {section_index} out of range")

    widgets = sections[section_index].get("widgets", [])
    if widget_index < 0 or widget_index >= len(widgets):
        raise ValueError(f"Widget index {widget_index} out of range")

    # Update widget
    current_widget = widgets[widget_index]
    updated_widget = {**current_widget, **updates}

    # Validate updated widget
    validated = WidgetDefinition.model_validate(updated_widget)
    widgets[widget_index] = validated.model_dump()
    pages[page_index]["sections"][section_index]["widgets"] = widgets

    # Update dashboard with version check
    return await update_dashboard(user, dashboard_id, {"pages": pages}, effective_version)


async def reorder_widgets(
    user: UserContext,
    dashboard_id: str,
    page_index: int,
    section_index: int,
    widget_ids: list[str],
    expected_version: int | None = None,
) -> DashboardDefinition:
    """Reorder widgets within a section.

    Args:
        user: Authenticated user context
        dashboard_id: Dashboard ID
        page_index: Index of page
        section_index: Index of section within page
        widget_ids: New order of widget IDs
        expected_version: If provided, reject if current version doesn't match (optimistic locking)

    Returns:
        Updated DashboardDefinition

    Raises:
        ValueError: If indices are invalid or widget IDs don't match
        ConflictError: If version mismatch detected (optimistic locking)
    """
    # Get current dashboard
    dashboard = await get_dashboard(user, dashboard_id)

    # Use dashboard version if expected_version not provided but we need atomic check
    effective_version = expected_version if expected_version is not None else dashboard.version

    # Get pages as mutable list
    pages = [p.model_dump() for p in dashboard.pages]

    # Validate indices
    if page_index < 0 or page_index >= len(pages):
        raise ValueError(f"Page index {page_index} out of range")

    sections = pages[page_index].get("sections", [])
    if section_index < 0 or section_index >= len(sections):
        raise ValueError(f"Section index {section_index} out of range")

    widgets = sections[section_index].get("widgets", [])
    widget_map = {w["id"]: w for w in widgets}

    # Validate widget IDs
    current_ids = set(widget_map.keys())
    new_ids = set(widget_ids)
    if current_ids != new_ids:
        raise ValueError("Widget IDs don't match current widgets")

    # Reorder
    reordered = [widget_map[wid] for wid in widget_ids]
    pages[page_index]["sections"][section_index]["widgets"] = reordered

    # Update dashboard with version check
    return await update_dashboard(user, dashboard_id, {"pages": pages}, effective_version)


async def move_widget(
    user: UserContext,
    dashboard_id: str,
    widget_id: str,
    target_page_id: str,
    target_section_index: int,
    position: int | None = None,
) -> DashboardDefinition:
    """Move widget to a different location.

    Args:
        user: Authenticated user context
        dashboard_id: Dashboard ID
        widget_id: ID of widget to move
        target_page_id: ID of destination page
        target_section_index: Index of destination section
        position: Position within section (None = append to end)

    Returns:
        Updated DashboardDefinition

    Raises:
        ValueError: If widget/page not found or section index out of range
    """
    dashboard = await get_dashboard(user, dashboard_id)
    pages = [p.model_dump() for p in dashboard.pages]

    # Find and remove widget from current location
    source_loc = _find_widget_location(dashboard, widget_id)
    if not source_loc:
        raise ValueError(f"Widget '{widget_id}' not found")

    src_pi, src_si, src_wi = source_loc
    widget = pages[src_pi]["sections"][src_si]["widgets"].pop(src_wi)

    # Find target page
    target_pi = _find_page_index(dashboard, target_page_id)
    if target_pi is None:
        raise ValueError(f"Page '{target_page_id}' not found")

    # Validate target section exists
    target_sections = pages[target_pi].get("sections", [])
    if target_section_index < 0 or target_section_index >= len(target_sections):
        raise ValueError(f"Section index {target_section_index} out of range")

    # Insert at position
    target_widgets = target_sections[target_section_index].get("widgets", [])
    if position is None or position >= len(target_widgets):
        target_widgets.append(widget)
    else:
        target_widgets.insert(max(0, position), widget)

    pages[target_pi]["sections"][target_section_index]["widgets"] = target_widgets
    return await update_dashboard(user, dashboard_id, {"pages": pages})


# ============================================================================
# Page Operations
# ============================================================================


async def create_page(
    user: UserContext,
    dashboard_id: str,
    title: str,
    position: int | None = None,
) -> DashboardDefinition:
    """Create a new page in a dashboard.

    Args:
        user: Authenticated user context
        dashboard_id: Dashboard ID
        title: Page title
        position: Position to insert (None = append to end)

    Returns:
        Updated DashboardDefinition
    """
    dashboard = await get_dashboard(user, dashboard_id)
    pages = [p.model_dump() for p in dashboard.pages]

    new_page = {
        "id": str(uuid.uuid4()),
        "title": title,
        "sections": [],
    }

    if position is None or position >= len(pages):
        pages.append(new_page)
    else:
        pages.insert(max(0, position), new_page)

    return await update_dashboard(user, dashboard_id, {"pages": pages})


async def create_section(
    user: UserContext,
    dashboard_id: str,
    page_id: str,
    title: str | None = None,
    position: int | None = None,
) -> DashboardDefinition:
    """Create a new section in a page.

    Args:
        user: Authenticated user context
        dashboard_id: Dashboard ID
        page_id: ID of page to add section to
        title: Optional section title
        position: Position to insert (None = append to end)

    Returns:
        Updated DashboardDefinition

    Raises:
        ValueError: If page not found
    """
    dashboard = await get_dashboard(user, dashboard_id)
    pages = [p.model_dump() for p in dashboard.pages]

    page_idx = _find_page_index(dashboard, page_id)
    if page_idx is None:
        raise ValueError(f"Page '{page_id}' not found")

    new_section = {"title": title, "widgets": []}
    sections = pages[page_idx].get("sections", [])

    if position is None or position >= len(sections):
        sections.append(new_section)
    else:
        sections.insert(max(0, position), new_section)

    pages[page_idx]["sections"] = sections
    return await update_dashboard(user, dashboard_id, {"pages": pages})


async def rename_page(
    user: UserContext,
    dashboard_id: str,
    page_id: str,
    title: str,
) -> DashboardDefinition:
    """Rename a page.

    Args:
        user: Authenticated user context
        dashboard_id: Dashboard ID
        page_id: ID of page to rename
        title: New title

    Returns:
        Updated DashboardDefinition

    Raises:
        ValueError: If page not found
    """
    dashboard = await get_dashboard(user, dashboard_id)
    pages = [p.model_dump() for p in dashboard.pages]

    page_idx = _find_page_index(dashboard, page_id)
    if page_idx is None:
        raise ValueError(f"Page '{page_id}' not found")

    pages[page_idx]["title"] = title
    return await update_dashboard(user, dashboard_id, {"pages": pages})


async def delete_page(
    user: UserContext,
    dashboard_id: str,
    page_id: str,
    cascade: bool = False,
) -> DashboardDefinition:
    """Delete a page from a dashboard.

    Args:
        user: Authenticated user context
        dashboard_id: Dashboard ID
        page_id: ID of page to delete
        cascade: If True, delete even if page has widgets

    Returns:
        Updated DashboardDefinition

    Raises:
        ValueError: If page not found, is the last page,
                   or has widgets and cascade=False
    """
    dashboard = await get_dashboard(user, dashboard_id)

    if len(dashboard.pages) <= 1:
        raise ValueError("Cannot delete the last page")

    pages = [p.model_dump() for p in dashboard.pages]
    page_idx = _find_page_index(dashboard, page_id)

    if page_idx is None:
        raise ValueError(f"Page '{page_id}' not found")

    # Check if empty
    sections = pages[page_idx].get("sections", [])
    widgets_count = sum(len(s.get("widgets", [])) for s in sections)

    if widgets_count > 0 and not cascade:
        raise ValueError(f"Page has {widgets_count} widgets. Use cascade=True to delete anyway.")

    pages.pop(page_idx)
    return await update_dashboard(user, dashboard_id, {"pages": pages})


async def swap_widgets(
    user: UserContext,
    dashboard_id: str,
    widget_id_1: str,
    widget_id_2: str,
) -> DashboardDefinition:
    """Swap positions of two widgets.

    Args:
        user: Authenticated user context
        dashboard_id: Dashboard ID
        widget_id_1: First widget ID
        widget_id_2: Second widget ID

    Returns:
        Updated DashboardDefinition

    Raises:
        ValueError: If either widget not found
    """
    dashboard = await get_dashboard(user, dashboard_id)
    pages = [p.model_dump() for p in dashboard.pages]

    # Find both widgets
    loc1 = _find_widget_location(dashboard, widget_id_1)
    loc2 = _find_widget_location(dashboard, widget_id_2)

    if not loc1:
        raise ValueError(f"Widget '{widget_id_1}' not found")
    if not loc2:
        raise ValueError(f"Widget '{widget_id_2}' not found")

    # Get widgets
    p1, s1, w1 = loc1
    p2, s2, w2 = loc2

    widget1 = pages[p1]["sections"][s1]["widgets"][w1]
    widget2 = pages[p2]["sections"][s2]["widgets"][w2]

    # Swap
    pages[p1]["sections"][s1]["widgets"][w1] = widget2
    pages[p2]["sections"][s2]["widgets"][w2] = widget1

    return await update_dashboard(user, dashboard_id, {"pages": pages})


async def rename_section(
    user: UserContext,
    dashboard_id: str,
    page_id: str,
    section_index: int,
    title: str | None,
) -> DashboardDefinition:
    """Rename a section.

    Args:
        user: Authenticated user context
        dashboard_id: Dashboard ID
        page_id: ID of page containing section
        section_index: Index of section to rename
        title: New title (None to remove title)

    Returns:
        Updated DashboardDefinition

    Raises:
        ValueError: If page not found or section index out of range
    """
    dashboard = await get_dashboard(user, dashboard_id)
    pages = [p.model_dump() for p in dashboard.pages]

    page_idx = _find_page_index(dashboard, page_id)
    if page_idx is None:
        raise ValueError(f"Page '{page_id}' not found")

    sections = pages[page_idx].get("sections", [])
    if section_index < 0 or section_index >= len(sections):
        raise ValueError(f"Section index {section_index} out of range")

    sections[section_index]["title"] = title
    pages[page_idx]["sections"] = sections
    return await update_dashboard(user, dashboard_id, {"pages": pages})


async def delete_section(
    user: UserContext,
    dashboard_id: str,
    page_id: str,
    section_index: int,
    cascade: bool = False,
) -> DashboardDefinition:
    """Delete a section from a page.

    Args:
        user: Authenticated user context
        dashboard_id: Dashboard ID
        page_id: ID of page containing section
        section_index: Index of section to delete
        cascade: If True, delete even if section has widgets

    Returns:
        Updated DashboardDefinition

    Raises:
        ValueError: If page not found, section index out of range,
                   or section has widgets and cascade=False
    """
    dashboard = await get_dashboard(user, dashboard_id)
    pages = [p.model_dump() for p in dashboard.pages]

    page_idx = _find_page_index(dashboard, page_id)
    if page_idx is None:
        raise ValueError(f"Page '{page_id}' not found")

    sections = pages[page_idx].get("sections", [])
    if section_index < 0 or section_index >= len(sections):
        raise ValueError(f"Section index {section_index} out of range")

    widgets = sections[section_index].get("widgets", [])
    if widgets and not cascade:
        raise ValueError(f"Section has {len(widgets)} widgets. Use cascade=True to delete anyway.")

    sections.pop(section_index)
    pages[page_idx]["sections"] = sections
    return await update_dashboard(user, dashboard_id, {"pages": pages})

async def move_section(
    user: UserContext,
    dashboard_id: str,
    source_page_id: str,
    section_index: int,
    target_page_id: str,
    target_position: int | None = None,
) -> DashboardDefinition:
    """Move a section to a different page or position.

    Args:
        user: Authenticated user context
        dashboard_id: Dashboard ID
        source_page_id: ID of page containing section
        section_index: Index of section to move
        target_page_id: ID of destination page
        target_position: Position in target page (None = append)

    Returns:
        Updated DashboardDefinition

    Raises:
        ValueError: If page not found or section index out of range
    """
    dashboard = await get_dashboard(user, dashboard_id)
    pages = [p.model_dump() for p in dashboard.pages]

    # Find source page
    src_pi = _find_page_index(dashboard, source_page_id)
    if src_pi is None:
        raise ValueError(f"Source page '{source_page_id}' not found")

    src_sections = pages[src_pi].get("sections", [])
    if section_index < 0 or section_index >= len(src_sections):
        raise ValueError(f"Section index {section_index} out of range")

    # Remove from source
    section = src_sections.pop(section_index)
    pages[src_pi]["sections"] = src_sections

    # Find target page
    tgt_pi = _find_page_index(dashboard, target_page_id)
    if tgt_pi is None:
        raise ValueError(f"Target page '{target_page_id}' not found")

    # Insert at target
    tgt_sections = pages[tgt_pi].get("sections", [])
    if target_position is None or target_position >= len(tgt_sections):
        tgt_sections.append(section)
    else:
        tgt_sections.insert(max(0, target_position), section)

    pages[tgt_pi]["sections"] = tgt_sections
    return await update_dashboard(user, dashboard_id, {"pages": pages})


async def copy_widget(
    user: UserContext,
    dashboard_id: str,
    widget_id: str,
    target_page_id: str,
    target_section_index: int,
    new_title: str | None = None,
) -> DashboardDefinition:
    """Copy widget to a new location with a new ID.

    Args:
        user: Authenticated user context
        dashboard_id: Dashboard ID
        widget_id: ID of widget to copy
        target_page_id: ID of destination page
        target_section_index: Index of destination section
        new_title: Title for copy (default: "Copy of {original}")

    Returns:
        Updated DashboardDefinition

    Raises:
        ValueError: If widget/page not found or section index out of range
    """
    dashboard = await get_dashboard(user, dashboard_id)
    pages = [p.model_dump() for p in dashboard.pages]

    # Find source widget
    widget = _get_widget_by_id(dashboard, widget_id)
    if not widget:
        raise ValueError(f"Widget '{widget_id}' not found")

    # Create copy with new ID
    widget_copy = widget.model_dump()
    widget_copy["id"] = str(uuid.uuid4())
    widget_copy["title"] = new_title or f"Copy of {widget.title}"

    # Find target page
    target_pi = _find_page_index(dashboard, target_page_id)
    if target_pi is None:
        raise ValueError(f"Page '{target_page_id}' not found")

    # Validate and insert
    target_sections = pages[target_pi].get("sections", [])
    if target_section_index < 0 or target_section_index >= len(target_sections):
        raise ValueError(f"Section index {target_section_index} out of range")

    pages[target_pi]["sections"][target_section_index]["widgets"].append(widget_copy)
    return await update_dashboard(user, dashboard_id, {"pages": pages})


async def reorder_pages(
    user: UserContext,
    dashboard_id: str,
    page_ids: list[str],
) -> DashboardDefinition:
    """Reorder pages in a dashboard.

    Args:
        user: Authenticated user context
        dashboard_id: Dashboard ID
        page_ids: List of all page IDs in new order

    Returns:
        Updated DashboardDefinition

    Raises:
        ValueError: If page IDs don't match existing pages
    """
    dashboard = await get_dashboard(user, dashboard_id)
    pages = [p.model_dump() for p in dashboard.pages]

    # Validate all IDs match
    current_ids = {p["id"] for p in pages}
    new_ids = set(page_ids)

    if current_ids != new_ids:
        raise ValueError("Page IDs don't match. All existing page IDs must be provided.")

    # Reorder
    page_map = {p["id"]: p for p in pages}
    reordered = [page_map[pid] for pid in page_ids]

    return await update_dashboard(user, dashboard_id, {"pages": reordered})
