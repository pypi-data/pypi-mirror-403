"""
Auto-generated from schemas/format.schema.json
DO NOT EDIT MANUALLY - run `pnpm schema:generate` to regenerate
"""

from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field


class FormatType(str, Enum):
    """Available format types for widget values."""
    NUMBER = "number"
    CURRENCY = "currency"
    PERCENT = "percent"
    PERCENT_VALUE = "percent_value"
    DATE = "date"
    COMPACT = "compact"
    DURATION = "duration"


class DurationUnit(str, Enum):
    """Input unit for duration values."""
    SECONDS = "seconds"
    MINUTES = "minutes"
    HOURS = "hours"
    DAYS = "days"


class DurationStyle(str, Enum):
    """Output style for duration formatting."""
    SHORT = "short"
    LONG = "long"
    NARROW = "narrow"


class FormatDefinition(BaseModel):
    """Format configuration for displaying widget values."""

    type: Literal["number", "currency", "percent", "percent_value", "date", "compact", "duration"] = Field(
        description="Format type - match to metric type"
    )
    decimals: Optional[int] = Field(
        default=None,
        ge=0,
        le=10,
        description="Number of decimal places to display"
    )
    currency: Optional[str] = Field(
        default=None,
        min_length=3,
        max_length=3,
        description="ISO 4217 currency code (e.g., USD, EUR, DKK)"
    )
    compact: Optional[bool] = Field(
        default=None,
        description="Use compact notation for large numbers"
    )
    duration_unit: Optional[Literal["seconds", "minutes", "hours", "days"]] = Field(
        default=None,
        description="Input unit for duration values"
    )
    duration_style: Optional[Literal["short", "long", "narrow"]] = Field(
        default=None,
        description="Output style: long (2 hrs 18 mins), short (2h 18m), narrow (2:18)"
    )
    duration_max_parts: Optional[int] = Field(
        default=None,
        ge=1,
        le=6,
        description="Maximum number of time units to display"
    )

    model_config = {"extra": "forbid"}
