"""Time scope utilities for widget date range calculation.

Provides functions to calculate date ranges based on time_scope settings,
allowing widgets to show latest-period data instead of full date range.
"""

from datetime import date, timedelta
from typing import Literal

TimeScope = Literal["range", "latest", "latest_complete"]
Grain = Literal["day", "week", "month", "quarter", "year"]


def get_period_start(d: date, grain: Grain) -> date:
    """Get the start of the period containing date d."""
    if grain == "day":
        return d
    elif grain == "week":
        # Start of week (Monday)
        return d - timedelta(days=d.weekday())
    elif grain == "month":
        return d.replace(day=1)
    elif grain == "quarter":
        quarter_month = ((d.month - 1) // 3) * 3 + 1
        return d.replace(month=quarter_month, day=1)
    elif grain == "year":
        return d.replace(month=1, day=1)
    else:
        return d


def get_period_end(d: date, grain: Grain) -> date:
    """Get the end of the period containing date d."""
    if grain == "day":
        return d
    elif grain == "week":
        # End of week (Sunday)
        return d + timedelta(days=(6 - d.weekday()))
    elif grain == "month":
        # Last day of month
        if d.month == 12:
            return d.replace(month=12, day=31)
        return d.replace(month=d.month + 1, day=1) - timedelta(days=1)
    elif grain == "quarter":
        quarter_end_month = ((d.month - 1) // 3) * 3 + 3
        if quarter_end_month == 12:
            return d.replace(month=12, day=31)
        return d.replace(month=quarter_end_month + 1, day=1) - timedelta(days=1)
    elif grain == "year":
        return d.replace(month=12, day=31)
    else:
        return d


def get_previous_period_start(d: date, grain: Grain) -> date:
    """Get the start of the previous period before date d."""
    period_start = get_period_start(d, grain)

    if grain == "day":
        return period_start - timedelta(days=1)
    elif grain == "week":
        return period_start - timedelta(weeks=1)
    elif grain == "month":
        if period_start.month == 1:
            return period_start.replace(year=period_start.year - 1, month=12)
        return period_start.replace(month=period_start.month - 1)
    elif grain == "quarter":
        if period_start.month <= 3:
            return period_start.replace(year=period_start.year - 1, month=10)
        return period_start.replace(month=period_start.month - 3)
    elif grain == "year":
        return period_start.replace(year=period_start.year - 1)
    else:
        return period_start - timedelta(days=1)


def calculate_time_scope_range(
    time_scope: TimeScope,
    grain: Grain,
    reference_date: date | None = None,
) -> tuple[date, date]:
    """Calculate date range for a time_scope setting.

    Args:
        time_scope: The time scope setting
        grain: Dashboard grain (day, week, month, quarter, year)
        reference_date: Reference date (default: today)

    Returns:
        Tuple of (start_date, end_date) for the query

    Raises:
        ValueError: If time_scope is "range" (use dashboard date range instead)
    """
    if time_scope == "range":
        raise ValueError("time_scope='range' should use dashboard date range")

    today = reference_date or date.today()

    if time_scope == "latest":
        # Current period (may be incomplete)
        start = get_period_start(today, grain)
        end = today
        return (start, end)

    elif time_scope == "latest_complete":
        # Last complete period
        current_period_start = get_period_start(today, grain)

        # If we're at the start of a period, the "latest complete" is the previous period
        # Otherwise, go back one period from current
        prev_start = get_previous_period_start(today, grain)
        prev_end = get_period_end(prev_start, grain)

        return (prev_start, prev_end)

    else:
        raise ValueError(f"Unknown time_scope: {time_scope}")


def should_apply_time_scope(
    time_scope: TimeScope | None,
    group_by: list[str] | None,
) -> bool:
    """Check if time_scope should be applied to a query.

    Time scope only applies to non-time-series queries (those without metric_time).

    Args:
        time_scope: Widget's time_scope setting
        group_by: Query's group_by dimensions

    Returns:
        True if time_scope should modify the date range
    """
    if not time_scope or time_scope == "range":
        return False

    # Check if query has time dimension
    group_by_list = group_by or []
    has_time_dimension = any(
        "metric_time" in dim.lower()
        for dim in group_by_list
    )

    # Only apply time_scope to non-time-series queries
    return not has_time_dimension


def apply_time_scope(
    time_scope: TimeScope | None,
    grain: Grain,
    start_date: str | None,
    end_date: str | None,
    group_by: list[str] | None,
    reference_date: date | None = None,
) -> tuple[str | None, str | None]:
    """Apply time_scope to query date range.

    Args:
        time_scope: Widget's time_scope setting
        grain: Dashboard grain
        start_date: Original start date (ISO format)
        end_date: Original end date (ISO format)
        group_by: Query's group_by dimensions
        reference_date: Reference date for calculations (default: today)

    Returns:
        Tuple of (adjusted_start_date, adjusted_end_date) in ISO format
    """
    if not should_apply_time_scope(time_scope, group_by):
        return (start_date, end_date)

    # Calculate new date range based on time_scope
    new_start, new_end = calculate_time_scope_range(
        time_scope,  # type: ignore (we know it's not "range" here)
        grain,
        reference_date,
    )

    return (new_start.isoformat(), new_end.isoformat())
