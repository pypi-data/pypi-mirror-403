"""Activity logging service for tracking agent actions on dashboards.

Logs actions performed by agents (MCP, CLI, chat) and UI on dashboards,
stored in Firestore for real-time activity feeds.

Firestore Path:
    organizations/{org_id}/dashboards/{dashboard_id}/activity/{activity_id}
"""

import uuid
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field

import storage


# ============================================================================
# Types
# ============================================================================

ActorType = Literal["mcp", "cli", "chat", "ui"]
"""The interface that performed the action."""

ActionType = Literal[
    # Dashboard-level actions
    "create_dashboard",
    "update_dashboard",
    "delete_dashboard",
    # Widget actions
    "add_widget",
    "update_widget",
    "remove_widget",
    "move_widget",
    "copy_widget",
    "swap_widgets",
    # Section actions
    "create_section",
    "delete_section",
    "rename_section",
    "move_section",
    # Page actions
    "create_page",
    "delete_page",
    "rename_page",
    "reorder_pages",
]
"""The type of action performed."""


class Activity(BaseModel):
    """A logged action on a dashboard.

    Attributes:
        id: Unique identifier for this activity entry
        dashboard_id: ID of the dashboard this activity belongs to
        actor_type: Which interface performed the action (mcp, cli, chat, ui)
        actor_id: User ID if available
        action: The type of action performed
        target: Widget ID, section name, page title, etc.
        description: Human-readable description of the action
        metadata: Additional context about the action
        created_at: When the action was performed
    """

    id: str
    dashboard_id: str
    actor_type: ActorType
    actor_id: str | None = None
    action: ActionType
    target: str | None = None
    description: str
    metadata: dict = Field(default_factory=dict)
    created_at: datetime


# ============================================================================
# Service Functions
# ============================================================================


async def log_activity(
    org_id: str,
    dashboard_id: str,
    actor_type: ActorType,
    action: ActionType,
    description: str,
    target: str | None = None,
    actor_id: str | None = None,
    metadata: dict | None = None,
) -> Activity:
    """Log an activity on a dashboard.

    Called by dashboard service functions after successful operations.

    Args:
        org_id: Organization ID
        dashboard_id: Dashboard ID
        actor_type: Which interface performed the action (mcp, cli, chat, ui)
        action: The type of action performed
        description: Human-readable description (e.g., "Added KPI widget 'Revenue'")
        target: Widget ID, section name, page title, etc.
        actor_id: User ID if available
        metadata: Additional context about the action

    Returns:
        The created Activity record
    """
    activity = Activity(
        id=str(uuid.uuid4())[:8],
        dashboard_id=dashboard_id,
        actor_type=actor_type,
        actor_id=actor_id,
        action=action,
        target=target,
        description=description,
        metadata=metadata or {},
        created_at=datetime.now(timezone.utc),
    )

    # Store in Firestore
    db = storage.get_firestore_client()
    doc_ref = (
        db.collection("organizations")
        .document(org_id)
        .collection("dashboards")
        .document(dashboard_id)
        .collection("activity")
        .document(activity.id)
    )
    doc_ref.set(activity.model_dump(mode="json"))

    return activity


async def get_recent_activity(
    org_id: str,
    dashboard_id: str,
    limit: int = 20,
) -> list[Activity]:
    """Get recent activity for a dashboard.

    Args:
        org_id: Organization ID
        dashboard_id: Dashboard ID
        limit: Maximum number of activities to return (default: 20)

    Returns:
        List of Activity records, most recent first
    """
    db = storage.get_firestore_client()
    query = (
        db.collection("organizations")
        .document(org_id)
        .collection("dashboards")
        .document(dashboard_id)
        .collection("activity")
        .order_by("created_at", direction="DESCENDING")
        .limit(limit)
    )

    docs = query.stream()
    return [Activity.model_validate(doc.to_dict()) for doc in docs]


async def get_activity_by_actor(
    org_id: str,
    dashboard_id: str,
    actor_type: ActorType,
    limit: int = 20,
) -> list[Activity]:
    """Get activity filtered by actor type.

    Useful for seeing only agent actions (mcp, cli, chat) or only UI actions.

    Args:
        org_id: Organization ID
        dashboard_id: Dashboard ID
        actor_type: Filter by this actor type
        limit: Maximum number of activities to return

    Returns:
        List of Activity records, most recent first
    """
    db = storage.get_firestore_client()
    from google.cloud.firestore_v1.base_query import FieldFilter

    query = (
        db.collection("organizations")
        .document(org_id)
        .collection("dashboards")
        .document(dashboard_id)
        .collection("activity")
        .where(filter=FieldFilter("actor_type", "==", actor_type))
        .order_by("created_at", direction="DESCENDING")
        .limit(limit)
    )

    docs = query.stream()
    return [Activity.model_validate(doc.to_dict()) for doc in docs]


async def get_activity_by_action(
    org_id: str,
    dashboard_id: str,
    action: ActionType,
    limit: int = 20,
) -> list[Activity]:
    """Get activity filtered by action type.

    Useful for tracking specific operations like widget additions.

    Args:
        org_id: Organization ID
        dashboard_id: Dashboard ID
        action: Filter by this action type
        limit: Maximum number of activities to return

    Returns:
        List of Activity records, most recent first
    """
    db = storage.get_firestore_client()
    from google.cloud.firestore_v1.base_query import FieldFilter

    query = (
        db.collection("organizations")
        .document(org_id)
        .collection("dashboards")
        .document(dashboard_id)
        .collection("activity")
        .where(filter=FieldFilter("action", "==", action))
        .order_by("created_at", direction="DESCENDING")
        .limit(limit)
    )

    docs = query.stream()
    return [Activity.model_validate(doc.to_dict()) for doc in docs]


async def delete_activity(
    org_id: str,
    dashboard_id: str,
    activity_id: str,
) -> bool:
    """Delete a specific activity entry.

    Args:
        org_id: Organization ID
        dashboard_id: Dashboard ID
        activity_id: Activity ID to delete

    Returns:
        True if deleted, False if not found
    """
    db = storage.get_firestore_client()
    doc_ref = (
        db.collection("organizations")
        .document(org_id)
        .collection("dashboards")
        .document(dashboard_id)
        .collection("activity")
        .document(activity_id)
    )

    doc = doc_ref.get()
    if not doc.exists:
        return False

    doc_ref.delete()
    return True


async def clear_activity(
    org_id: str,
    dashboard_id: str,
) -> int:
    """Clear all activity for a dashboard.

    Useful for cleanup or when deleting a dashboard.

    Args:
        org_id: Organization ID
        dashboard_id: Dashboard ID

    Returns:
        Number of activity entries deleted
    """
    db = storage.get_firestore_client()
    activity_ref = (
        db.collection("organizations")
        .document(org_id)
        .collection("dashboards")
        .document(dashboard_id)
        .collection("activity")
    )

    # Delete all documents in the activity subcollection
    docs = activity_ref.stream()
    count = 0
    for doc in docs:
        doc.reference.delete()
        count += 1

    return count
