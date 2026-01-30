"""
Auto-generated from schemas/dashboard.schema.json
DO NOT EDIT MANUALLY - run `pnpm schema:generate` to regenerate
"""

from enum import Enum
from typing import Annotated, Any, Literal, Optional, Union

from pydantic import BaseModel, Field


# =============================================================================
# Enum Types
# =============================================================================

class DashboardVisibility(str, Enum):
    """Dashboard visibility."""
    PRIVATE = "private"
    ORG = "org"


class DateRangeMode(str, Enum):
    """Date range mode."""
    RELATIVE = "relative"
    ABSOLUTE = "absolute"


class DateRangePreset(str, Enum):
    """Relative date range presets."""
    TODAY = "today"
    YESTERDAY = "yesterday"
    LAST_7_DAYS = "last_7_days"
    LAST_14_DAYS = "last_14_days"
    LAST_30_DAYS = "last_30_days"
    LAST_90_DAYS = "last_90_days"
    LAST_12_MONTHS = "last_12_months"
    THIS_WEEK = "this_week"
    THIS_MONTH = "this_month"
    THIS_QUARTER = "this_quarter"
    THIS_YEAR = "this_year"
    YTD = "ytd"
    LAST_WEEK = "last_week"
    LAST_MONTH = "last_month"
    LAST_QUARTER = "last_quarter"
    LAST_YEAR = "last_year"


class GrainOption(str, Enum):
    """Time granularity for dashboard controls."""
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"


class ComparisonOption(str, Enum):
    """Comparison mode for dashboard controls."""
    NONE = "none"
    PREVIOUS_PERIOD = "previous_period"
    SAME_PERIOD_LAST_YEAR = "same_period_last_year"


class SectionLayout(str, Enum):
    """Section layout mode."""
    GRID = "grid"
    ROW = "row"


class FilterOperator(str, Enum):
    """Query filter operator."""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    IN = "in"
    NOT_IN = "not_in"
    GT = "gt"
    LT = "lt"
    GTE = "gte"
    LTE = "lte"


class WidgetType(str, Enum):
    """Type of widget visualization."""
    AREA_CHART = "area_chart"
    BAR_CHART = "bar_chart"
    LINE_CHART = "line_chart"
    DONUT = "donut"
    HEATMAP = "heatmap"
    KPI = "kpi"
    TABLE = "table"


class TrendDirection(str, Enum):
    """Controls delta color interpretation."""
    UP_IS_GOOD = "up_is_good"
    DOWN_IS_GOOD = "down_is_good"


class ChartCurve(str, Enum):
    """Line/area chart curve type."""
    LINEAR = "linear"
    NATURAL = "natural"
    STEP = "step"


class Orientation(str, Enum):
    """Bar chart orientation."""
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"


class ColorScale(str, Enum):
    """Heatmap color scale."""
    GREEN = "green"
    RED = "red"


class DonutVariant(str, Enum):
    """Donut/pie chart variant."""
    DONUT = "donut"
    PIE = "pie"


class CellType(str, Enum):
    """Table cell type."""
    TEXT = "text"
    BADGE = "badge"
    DELTA = "delta"
    SPARKLINE = "sparkline"
    PROGRESS = "progress"
    LINK = "link"


class ColumnAlign(str, Enum):
    """Column text alignment."""
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


class SortDirection(str, Enum):
    """Sort direction."""
    ASC = "asc"
    DESC = "desc"


# =============================================================================
# Model Definitions
# =============================================================================

class DateRangeSelection(BaseModel):
    """Date range selection for dashboard controls."""

    mode: Literal["relative", "absolute"] = Field(
        description="Date range mode: relative re-evaluates on each load, absolute uses fixed dates"
    )
    preset: Optional[Literal["today", "yesterday", "last_7_days", "last_14_days", "last_30_days", "last_90_days", "last_12_months", "this_week", "this_month", "this_quarter", "this_year", "ytd", "last_week", "last_month", "last_quarter", "last_year"]] = Field(
        default=None,
        description="For relative mode: preset name"
    )
    start_date: Optional[str] = Field(
        default=None,
        description="For absolute mode: ISO date string (YYYY-MM-DD)"
    )
    end_date: Optional[str] = Field(
        default=None,
        description="For absolute mode: ISO date string (YYYY-MM-DD)"
    )

    model_config = {"extra": "forbid"}


class DashboardControls(BaseModel):
    """Dashboard controls configuration."""

    date_range: DateRangeSelection = Field(
        description="Date range selection"
    )
    grain: Literal["day", "week", "month", "quarter", "year"] = Field(
        description="Time granularity"
    )
    comparison: Literal["none", "previous_period", "same_period_last_year"] = Field(
        description="Comparison mode"
    )

    model_config = {"extra": "forbid"}


class QueryFilter(BaseModel):
    """Query filter."""

    dimension: str = Field(
        description="Dimension to filter on"
    )
    operator: Literal["equals", "not_equals", "in", "not_in", "gt", "lt", "gte", "lte"] = Field(
        description="Filter operator"
    )
    value: Any = Field(
        description="Filter value (string, number, or array for in/not_in)"
    )

    model_config = {"extra": "forbid"}


class QueryDefinition(BaseModel):
    """Query configuration for widgets."""

    metrics: list[str] = Field(
        min_length=1,
        description="List of metric names to query"
    )
    dimensions: Optional[list[str]] = Field(
        default=None,
        description="Dimensions to group by"
    )
    grain: Optional[str] = Field(
        default=None,
        description="Time granularity or '$grain' to bind to dashboard control"
    )
    date_range: Optional[str] = Field(
        default=None,
        description="Date range override"
    )
    filters: Optional[list[QueryFilter]] = Field(
        default=None,
        description="Query filters"
    )
    order_by: Optional[str] = Field(
        default=None,
        description="Column to sort by, append ' desc' for descending"
    )
    limit: Optional[Annotated[int, Field(ge=1, le=10000)]] = Field(
        default=None,
        description="Maximum rows to return"
    )
    skip_date_filter: Optional[bool] = Field(
        default=None,
        description="Skip dashboard date range filter (for cohort queries)"
    )

    model_config = {"extra": "forbid"}


class ColumnCondition(BaseModel):
    """Conditional styling for table columns."""

    condition: str = Field(description="Condition expression")
    color: Optional[str] = Field(default=None, description="Text color")
    background_color: Optional[str] = Field(default=None, description="Background color")
    bold: Optional[bool] = Field(default=None, description="Bold text")

    model_config = {"extra": "forbid"}


class ColumnDefinition(BaseModel):
    """Table column definition."""

    field: str = Field(description="Field name")
    title: str = Field(description="Column title")
    width: Optional[str] = Field(default=None, description="Column width")
    align: Optional[Literal["left", "center", "right"]] = Field(
        default=None,
        description="Column alignment"
    )
    format: Optional[dict] = Field(default=None, description="Value format")
    conditions: Optional[list[ColumnCondition]] = Field(default=None, description="Conditional styles")
    cell_type: Optional[Literal["text", "badge", "delta", "sparkline", "progress", "link"]] = Field(
        default=None,
        description="Cell type"
    )
    cell_config: Optional[dict] = Field(default=None, description="Cell type configuration")

    model_config = {"extra": "forbid"}


class WidgetComparison(BaseModel):
    """KPI comparison configuration."""

    type: Literal["previous_period", "previous_year", "target"] = Field(
        description="Comparison type"
    )
    target_value: Optional[float] = Field(default=None, description="Target value for target comparison")

    model_config = {"extra": "forbid"}


class TablePagination(BaseModel):
    """Table pagination settings."""

    enabled: bool = Field(description="Enable pagination")
    page_size: Optional[Annotated[int, Field(ge=1)]] = Field(default=None, description="Page size")

    model_config = {"extra": "forbid"}


class TableSorting(BaseModel):
    """Table sorting settings."""

    enabled: bool = Field(description="Enable sorting")
    default_column: Optional[str] = Field(default=None, description="Default sort column")
    default_direction: Optional[Literal["asc", "desc"]] = Field(
        default=None,
        description="Default sort direction"
    )

    model_config = {"extra": "forbid"}


class TableSearch(BaseModel):
    """Table search settings."""

    enabled: bool = Field(description="Enable search")
    placeholder: Optional[str] = Field(default=None, description="Search placeholder text")
    columns: Optional[list[str]] = Field(default=None, description="Searchable columns")

    model_config = {"extra": "forbid"}


WidgetWidth = Union[int, Literal["full"]]


class WidgetDefinition(BaseModel):
    """Widget definition."""

    id: str = Field(description="Unique widget identifier (UUID)")
    type: Literal["area_chart", "bar_chart", "line_chart", "donut", "heatmap", "kpi", "table"] = Field(
        description="Widget type"
    )
    title: str = Field(min_length=1, description="Widget title")
    width: Optional[WidgetWidth] = Field(default=None, description="Widget width in columns (1-10 or 'full')")
    time_scope: Optional[Literal["range", "latest", "latest_complete"]] = Field(
        default=None,
        description="Date scope for non-time-series widgets: range (full), latest (current period), latest_complete (last complete period)"
    )
    query: QueryDefinition = Field(description="Query configuration")
    format: Optional[dict] = Field(default=None, description="Value formatting (see format.schema.json)")

    # KPI-specific
    comparison: Optional[WidgetComparison] = Field(default=None, description="KPI comparison configuration")
    sparkline: Optional[bool] = Field(default=None, description="KPI: show sparkline")
    trend: Optional[Literal["up_is_good", "down_is_good"]] = Field(
        default=None,
        description="Controls delta color: up_is_good (default) or down_is_good (for costs, churn)"
    )

    # Chart-specific
    stacked: Optional[bool] = Field(default=None, description="Area/bar chart: stack series")
    colors: Optional[list[str]] = Field(default=None, description="Custom color palette")
    show_legend: Optional[bool] = Field(default=None, description="Show chart legend")
    curve: Optional[Literal["linear", "natural", "step"]] = Field(
        default=None,
        description="Line/area chart curve type"
    )
    orientation: Optional[Literal["horizontal", "vertical"]] = Field(
        default=None,
        description="Bar chart orientation"
    )
    show_markers: Optional[bool] = Field(default=None, description="Line chart: show data point markers")
    display_grain: Optional[str] = Field(default=None, description="Line chart: display grain for cumulative metrics")

    # Donut-specific
    show_label: Optional[bool] = Field(default=None, description="Donut: show center label")
    variant: Optional[Literal["donut", "pie"]] = Field(
        default=None,
        description="Donut/pie variant"
    )

    # Table-specific
    columns: Optional[list[ColumnDefinition]] = Field(default=None, description="Table columns configuration")
    pagination: Optional[TablePagination] = Field(default=None, description="Table pagination")
    sorting: Optional[TableSorting] = Field(default=None, description="Table sorting")
    search: Optional[TableSearch] = Field(default=None, description="Table search")

    # Heatmap-specific
    row_dimension: Optional[str] = Field(default=None, description="Heatmap: dimension for rows")
    column_dimension: Optional[str] = Field(default=None, description="Heatmap: dimension for columns")
    row_label: Optional[str] = Field(default=None, description="Heatmap: row axis label")
    column_label: Optional[str] = Field(default=None, description="Heatmap: column axis label")
    color_scale: Optional[Literal["green", "red"]] = Field(
        default=None,
        description="Heatmap color scale (green = high is good, red = high is bad)"
    )
    show_values: Optional[bool] = Field(default=None, description="Heatmap: show cell values")
    max_columns: Optional[Annotated[int, Field(ge=1, le=48)]] = Field(
        default=None,
        description="Heatmap: max columns to display"
    )

    model_config = {"extra": "forbid"}


class SectionDefinition(BaseModel):
    """Dashboard section definition."""

    title: Optional[str] = Field(default=None, description="Section title")
    description: Optional[str] = Field(default=None, description="Section description")
    layout: Optional[Literal["grid", "row"]] = Field(
        default=None,
        description="Section layout mode"
    )
    widgets: list[WidgetDefinition] = Field(description="Widgets in this section")

    model_config = {"extra": "forbid"}


class PageDefinition(BaseModel):
    """Dashboard page definition."""

    id: str = Field(description="Unique page identifier")
    title: str = Field(min_length=1, description="Page title")
    icon: Optional[str] = Field(default=None, description="Page icon (Lucide icon name)")
    sections: list[SectionDefinition] = Field(description="Sections on this page")

    model_config = {"extra": "forbid"}


class DashboardDefinition(BaseModel):
    """Complete dashboard definition."""

    id: str = Field(description="Unique dashboard identifier")
    title: str = Field(min_length=1, description="Dashboard title")
    description: Optional[str] = Field(default=None, description="Dashboard description")
    owner: str = Field(description="User ID who owns this dashboard")
    visibility: Literal["private", "org"] = Field(
        description="Dashboard visibility: 'private' = only owner, 'org' = shared with team"
    )
    controls: DashboardControls = Field(description="Dashboard controls configuration")
    pages: list[PageDefinition] = Field(min_length=1, description="Dashboard pages")
    created_at: str = Field(description="Creation timestamp (ISO 8601)")
    updated_at: str = Field(description="Last update timestamp (ISO 8601)")
    created_by: str = Field(description="User ID who created this dashboard")
    version: Optional[Annotated[int, Field(ge=1)]] = Field(
        default=None,
        description="Dashboard version for optimistic locking"
    )

    model_config = {"extra": "forbid"}
