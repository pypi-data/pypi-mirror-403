"""
Auto-generated from schemas/widget.schema.json
DO NOT EDIT MANUALLY - run `pnpm schema:generate` to regenerate
"""

from enum import Enum
from typing import Literal, Optional, Union

from pydantic import BaseModel, Field


class WidgetType(str, Enum):
    """Available widget types."""
    AREA_CHART = "area_chart"
    BAR_CHART = "bar_chart"
    LINE_CHART = "line_chart"
    DONUT = "donut"
    HEATMAP = "heatmap"
    KPI = "kpi"
    TABLE = "table"


class Grain(str, Enum):
    """Time granularity options."""
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"


class Orientation(str, Enum):
    """Bar chart orientation options."""
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"


class QueryParams(BaseModel):
    """Parameters for metric queries."""

    metrics: list[str] = Field(
        min_length=1,
        description="List of metric names to query"
    )
    dimensions: Optional[list[str]] = Field(
        default=None,
        description="Dimensions to group by"
    )
    grain: Optional[Literal["day", "week", "month", "quarter", "year"]] = Field(
        default=None,
        description="Time granularity for the query"
    )
    start_date: Optional[str] = Field(
        default=None,
        description="Start date in YYYY-MM-DD format"
    )
    end_date: Optional[str] = Field(
        default=None,
        description="End date in YYYY-MM-DD format"
    )
    limit: Optional[int] = Field(
        default=None,
        ge=1,
        le=10000,
        description="Maximum number of rows to return"
    )
    order_by: Optional[str] = Field(
        default=None,
        description="Column to sort by, append ' desc' for descending"
    )

    model_config = {"extra": "forbid"}


class WidgetConfig(BaseModel):
    """Widget configuration for dashboards."""

    type: Literal["area_chart", "bar_chart", "line_chart", "donut", "heatmap", "kpi", "table"] = Field(
        description="Widget type"
    )
    title: str = Field(
        min_length=1,
        description="Widget title (avoid grain words like 'Monthly', 'Daily')"
    )
    query: QueryParams = Field(
        description="Query configuration"
    )
    format: Optional[dict] = Field(
        default=None,
        description="Value formatting configuration"
    )
    orientation: Optional[Literal["horizontal", "vertical"]] = Field(
        default=None,
        description="Bar chart orientation (only for bar_chart type)"
    )
    width: Optional[Union[int, Literal["full"]]] = Field(
        default=None,
        description="Widget width in columns (1-10). Defaults: kpi=2, donut=3, charts/table=10"
    )

    model_config = {"extra": "forbid"}
