"""Scheduled reports service - CRUD operations for recurring report delivery.

Provides typed schedule operations for MCP, CLI, and chat consumers.
Schedules define recurring reports (dashboard PDF or query CSV) delivered via email.
"""

from datetime import datetime, UTC
from typing import Literal
import uuid

from pydantic import BaseModel, Field

from services.auth import UserContext, require_role
import storage


# ============================================================================
# Types
# ============================================================================


class ScheduleFrequency(BaseModel):
    """When to run the schedule."""

    type: Literal["daily", "weekly", "monthly"]
    time: str = "09:00"  # HH:MM in UTC
    day_of_week: int | None = None  # 0=Monday, for weekly
    day_of_month: int | None = None  # 1-28, for monthly


class DashboardReport(BaseModel):
    """Dashboard PDF report configuration."""

    dashboard_id: str
    format: Literal["pdf", "png"] = "pdf"


class QueryReport(BaseModel):
    """Query CSV report configuration."""

    metrics: list[str]
    dimensions: list[str] = Field(default_factory=list)
    filters: dict[str, str] = Field(default_factory=dict)
    format: Literal["csv", "json"] = "csv"


class Schedule(BaseModel):
    """A scheduled report definition."""

    id: str
    org_id: str
    created_by: str  # user_id
    name: str
    frequency: ScheduleFrequency
    report: DashboardReport | QueryReport
    recipients: list[str]  # email addresses
    enabled: bool = True
    created_at: datetime
    updated_at: datetime
    last_run_at: datetime | None = None
    last_run_status: Literal["success", "failed"] | None = None


class ScheduleSummary(BaseModel):
    """Summary info for schedule listing."""

    id: str
    name: str
    frequency_type: str  # daily, weekly, monthly
    frequency_time: str  # HH:MM
    report_type: str  # dashboard or query
    enabled: bool
    recipients_count: int
    last_run_at: datetime | None
    last_run_status: Literal["success", "failed"] | None


# ============================================================================
# Firestore Access Helpers
# ============================================================================


def _get_schedules_ref(org_id: str):
    """Get Firestore reference for schedules collection."""
    db = storage.get_firestore_client()
    return db.collection("organizations").document(org_id).collection("schedules")


def _schedule_to_dict(schedule: Schedule) -> dict:
    """Convert Schedule to Firestore document dict."""
    data = schedule.model_dump(mode="json")
    # Convert datetime objects to ISO strings for Firestore
    data["created_at"] = schedule.created_at.isoformat()
    data["updated_at"] = schedule.updated_at.isoformat()
    if schedule.last_run_at:
        data["last_run_at"] = schedule.last_run_at.isoformat()
    return data


def _dict_to_schedule(data: dict, doc_id: str) -> Schedule:
    """Convert Firestore document dict to Schedule."""
    data["id"] = doc_id

    # Parse datetime strings
    if isinstance(data.get("created_at"), str):
        data["created_at"] = datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
    if isinstance(data.get("updated_at"), str):
        data["updated_at"] = datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00"))
    if data.get("last_run_at") and isinstance(data["last_run_at"], str):
        data["last_run_at"] = datetime.fromisoformat(data["last_run_at"].replace("Z", "+00:00"))

    # Determine report type and parse
    report_data = data.get("report", {})
    if "dashboard_id" in report_data:
        data["report"] = DashboardReport.model_validate(report_data)
    else:
        data["report"] = QueryReport.model_validate(report_data)

    # Parse frequency
    data["frequency"] = ScheduleFrequency.model_validate(data.get("frequency", {}))

    return Schedule.model_validate(data)


def _schedule_to_summary(schedule: Schedule) -> ScheduleSummary:
    """Convert Schedule to ScheduleSummary."""
    report_type = "dashboard" if isinstance(schedule.report, DashboardReport) else "query"

    return ScheduleSummary(
        id=schedule.id,
        name=schedule.name,
        frequency_type=schedule.frequency.type,
        frequency_time=schedule.frequency.time,
        report_type=report_type,
        enabled=schedule.enabled,
        recipients_count=len(schedule.recipients),
        last_run_at=schedule.last_run_at,
        last_run_status=schedule.last_run_status,
    )


def _validate_frequency(frequency: ScheduleFrequency) -> None:
    """Validate frequency configuration.

    Raises:
        ValueError: If frequency configuration is invalid
    """
    # Validate time format (HH:MM)
    try:
        parts = frequency.time.split(":")
        if len(parts) != 2:
            raise ValueError("Invalid time format")
        hour, minute = int(parts[0]), int(parts[1])
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError("Invalid time values")
    except (ValueError, AttributeError):
        raise ValueError(f"Invalid time format: {frequency.time}. Expected HH:MM in 24-hour format.")

    # Validate day_of_week for weekly schedules
    if frequency.type == "weekly":
        if frequency.day_of_week is None:
            raise ValueError("Weekly schedules require day_of_week (0=Monday through 6=Sunday)")
        if not (0 <= frequency.day_of_week <= 6):
            raise ValueError(f"Invalid day_of_week: {frequency.day_of_week}. Must be 0-6 (Monday-Sunday).")

    # Validate day_of_month for monthly schedules
    if frequency.type == "monthly":
        if frequency.day_of_month is None:
            raise ValueError("Monthly schedules require day_of_month (1-28)")
        if not (1 <= frequency.day_of_month <= 28):
            raise ValueError(f"Invalid day_of_month: {frequency.day_of_month}. Must be 1-28.")


def _validate_recipients(recipients: list[str]) -> None:
    """Validate email recipients.

    Raises:
        ValueError: If recipients list is empty or contains invalid emails
    """
    if not recipients:
        raise ValueError("At least one recipient email is required")

    # Basic email validation
    for email in recipients:
        if not email or "@" not in email or "." not in email.split("@")[-1]:
            raise ValueError(f"Invalid email address: {email}")


async def _validate_dashboard_exists(user: UserContext, dashboard_id: str) -> None:
    """Validate that a dashboard exists and user has access.

    Raises:
        ValueError: If dashboard not found or access denied
    """
    from services.dashboards import get_dashboard

    try:
        await get_dashboard(user, dashboard_id)
    except ValueError as e:
        raise ValueError(f"Dashboard validation failed: {e}")


# ============================================================================
# CRUD Operations
# ============================================================================


async def create_schedule(
    user: UserContext,
    name: str,
    frequency: ScheduleFrequency,
    report: DashboardReport | QueryReport,
    recipients: list[str],
) -> Schedule:
    """Create a new scheduled report.

    Args:
        user: Authenticated user context
        name: Schedule name
        frequency: When to run (daily/weekly/monthly + time)
        report: Report configuration (dashboard or query)
        recipients: Email addresses to send to

    Returns:
        Created Schedule

    Raises:
        PermissionError: If user lacks member role
        ValueError: If validation fails
    """
    # Require at least member role to create schedules
    require_role(user, "member")

    # Validate inputs
    _validate_frequency(frequency)
    _validate_recipients(recipients)

    # Validate dashboard exists if it's a dashboard report
    if isinstance(report, DashboardReport):
        await _validate_dashboard_exists(user, report.dashboard_id)

    # Create schedule
    now = datetime.now(UTC)
    schedule_id = str(uuid.uuid4())

    schedule = Schedule(
        id=schedule_id,
        org_id=user.org_id,
        created_by=user.uid,
        name=name,
        frequency=frequency,
        report=report,
        recipients=recipients,
        enabled=True,
        created_at=now,
        updated_at=now,
        last_run_at=None,
        last_run_status=None,
    )

    # Save to Firestore
    schedules_ref = _get_schedules_ref(user.org_id)
    doc_ref = schedules_ref.document(schedule_id)
    doc_ref.set(_schedule_to_dict(schedule))

    return schedule


async def list_schedules(user: UserContext) -> list[ScheduleSummary]:
    """List all schedules for the user's organization.

    Args:
        user: Authenticated user context

    Returns:
        List of ScheduleSummary objects
    """
    schedules_ref = _get_schedules_ref(user.org_id)

    summaries = []
    for doc in schedules_ref.stream():
        data = doc.to_dict()
        schedule = _dict_to_schedule(data, doc.id)
        summaries.append(_schedule_to_summary(schedule))

    # Sort by name
    summaries.sort(key=lambda s: s.name.lower())

    return summaries


async def get_schedule(user: UserContext, schedule_id: str) -> Schedule:
    """Get a schedule by ID.

    Args:
        user: Authenticated user context
        schedule_id: Schedule ID

    Returns:
        Schedule object

    Raises:
        ValueError: If schedule not found
    """
    schedules_ref = _get_schedules_ref(user.org_id)
    doc_ref = schedules_ref.document(schedule_id)
    doc = doc_ref.get()

    if not doc.exists:
        raise ValueError(f"Schedule '{schedule_id}' not found")

    return _dict_to_schedule(doc.to_dict(), doc.id)


async def update_schedule(
    user: UserContext,
    schedule_id: str,
    updates: dict,
) -> Schedule:
    """Update schedule properties.

    Allowed updates: name, frequency, report, recipients, enabled

    Args:
        user: Authenticated user context
        schedule_id: Schedule ID
        updates: Fields to update

    Returns:
        Updated Schedule

    Raises:
        PermissionError: If user is not creator and lacks admin role
        ValueError: If schedule not found or validation fails
    """
    schedules_ref = _get_schedules_ref(user.org_id)
    doc_ref = schedules_ref.document(schedule_id)
    doc = doc_ref.get()

    if not doc.exists:
        raise ValueError(f"Schedule '{schedule_id}' not found")

    current_data = doc.to_dict()
    schedule = _dict_to_schedule(current_data, doc.id)

    # Permission check: creator can always update, others need admin
    if schedule.created_by != user.uid:
        require_role(user, "admin")

    # Filter allowed updates
    allowed_fields = {"name", "frequency", "report", "recipients", "enabled"}
    filtered_updates = {k: v for k, v in updates.items() if k in allowed_fields}

    # Validate frequency if provided
    if "frequency" in filtered_updates:
        freq_data = filtered_updates["frequency"]
        if isinstance(freq_data, dict):
            frequency = ScheduleFrequency.model_validate(freq_data)
        else:
            frequency = freq_data
        _validate_frequency(frequency)
        filtered_updates["frequency"] = frequency.model_dump(mode="json")

    # Validate recipients if provided
    if "recipients" in filtered_updates:
        _validate_recipients(filtered_updates["recipients"])

    # Validate report if provided
    if "report" in filtered_updates:
        report_data = filtered_updates["report"]
        if isinstance(report_data, dict):
            if "dashboard_id" in report_data:
                report = DashboardReport.model_validate(report_data)
                await _validate_dashboard_exists(user, report.dashboard_id)
            else:
                report = QueryReport.model_validate(report_data)
            filtered_updates["report"] = report.model_dump(mode="json")

    # Update timestamp
    now = datetime.now(UTC)
    filtered_updates["updated_at"] = now.isoformat() + "Z"

    # Apply updates
    doc_ref.update(filtered_updates)

    # Return updated schedule
    return await get_schedule(user, schedule_id)


async def delete_schedule(user: UserContext, schedule_id: str) -> None:
    """Delete a schedule.

    Args:
        user: Authenticated user context
        schedule_id: Schedule ID

    Raises:
        PermissionError: If user is not creator and lacks admin role
        ValueError: If schedule not found
    """
    schedules_ref = _get_schedules_ref(user.org_id)
    doc_ref = schedules_ref.document(schedule_id)
    doc = doc_ref.get()

    if not doc.exists:
        raise ValueError(f"Schedule '{schedule_id}' not found")

    current_data = doc.to_dict()
    schedule = _dict_to_schedule(current_data, doc.id)

    # Permission check: creator can always delete, others need admin
    if schedule.created_by != user.uid:
        require_role(user, "admin")

    doc_ref.delete()


async def update_run_status(
    org_id: str,
    schedule_id: str,
    status: Literal["success", "failed"],
) -> None:
    """Update last run status (called by executor).

    This is an internal function called by the schedule executor Cloud Function,
    not by user-facing APIs. It does not require user authentication.

    Args:
        org_id: Organization ID
        schedule_id: Schedule ID
        status: Run status ("success" or "failed")

    Raises:
        ValueError: If schedule not found
    """
    schedules_ref = _get_schedules_ref(org_id)
    doc_ref = schedules_ref.document(schedule_id)
    doc = doc_ref.get()

    if not doc.exists:
        raise ValueError(f"Schedule '{schedule_id}' not found")

    now = datetime.now(UTC)
    doc_ref.update({
        "last_run_at": now.isoformat() + "Z",
        "last_run_status": status,
        "updated_at": now.isoformat() + "Z",
    })


# ============================================================================
# Query Helpers
# ============================================================================


async def get_schedules_due(org_id: str, current_time: datetime) -> list[Schedule]:
    """Get schedules that are due to run.

    This is used by the Cloud Function scheduler to find schedules
    that should be executed at the current time.

    Args:
        org_id: Organization ID
        current_time: Current UTC time

    Returns:
        List of Schedule objects due to run
    """
    schedules_ref = _get_schedules_ref(org_id)

    # Get current time components
    current_hour = current_time.hour
    current_minute = current_time.minute
    current_weekday = current_time.weekday()  # 0=Monday
    current_day = current_time.day

    time_str = f"{current_hour:02d}:{current_minute:02d}"

    due_schedules = []

    for doc in schedules_ref.where("enabled", "==", True).stream():
        data = doc.to_dict()
        schedule = _dict_to_schedule(data, doc.id)

        # Check if schedule matches current time
        if schedule.frequency.time != time_str:
            continue

        # Check frequency-specific conditions
        if schedule.frequency.type == "daily":
            due_schedules.append(schedule)
        elif schedule.frequency.type == "weekly":
            if schedule.frequency.day_of_week == current_weekday:
                due_schedules.append(schedule)
        elif schedule.frequency.type == "monthly":
            if schedule.frequency.day_of_month == current_day:
                due_schedules.append(schedule)

    return due_schedules


async def get_schedules_for_dashboard(
    user: UserContext,
    dashboard_id: str,
) -> list[ScheduleSummary]:
    """Get all schedules that reference a specific dashboard.

    Useful for showing schedules on a dashboard's detail page.

    Args:
        user: Authenticated user context
        dashboard_id: Dashboard ID

    Returns:
        List of ScheduleSummary objects
    """
    all_schedules = await list_schedules(user)

    # Filter to schedules for this dashboard
    dashboard_schedules = []
    for summary in all_schedules:
        if summary.report_type == "dashboard":
            # Need to fetch full schedule to check dashboard_id
            schedule = await get_schedule(user, summary.id)
            if isinstance(schedule.report, DashboardReport):
                if schedule.report.dashboard_id == dashboard_id:
                    dashboard_schedules.append(summary)

    return dashboard_schedules
