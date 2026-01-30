"""User context accumulation for agent personalization.

Stores and retrieves user preferences, favorites, and notes.
Data is stored per-user in Firestore at users/{uid}/preferences/context.

This enables agents to:
- Remember user formatting preferences (currency, decimals, grain)
- Track favorite metrics for quick access
- Store notes about metrics and data quality
- Apply custom instructions to all interactions
"""

from pydantic import BaseModel, Field
from typing import Any

import storage


class UserPreferences(BaseModel):
    """Accumulated context for a user - read/updated by agents."""

    # Format preferences
    default_currency: str | None = None
    default_grain: str | None = None
    decimal_places: int | None = None

    # Behavioral preferences
    favorite_metrics: list[str] = Field(default_factory=list)
    preferred_chart_type: str | None = None

    # Notes about data/metrics (subject -> note)
    notes: dict[str, str] = Field(default_factory=dict)

    # Custom instructions from user
    custom_instructions: str | None = None

    # Timestamp
    updated_at: str | None = None


async def get_user_preferences(user_id: str) -> UserPreferences:
    """Get accumulated context for a user.

    Returns empty UserPreferences if none exists.

    Args:
        user_id: User's UID

    Returns:
        UserPreferences instance
    """
    data = storage.get_user_preferences(user_id)
    if data is None:
        return UserPreferences()
    return UserPreferences.model_validate(data)


async def update_user_preferences(
    user_id: str,
    updates: dict[str, Any],
) -> UserPreferences:
    """Update user preferences (merge, not replace).

    Only provided fields are updated; others remain unchanged.

    Args:
        user_id: User's UID
        updates: Fields to update (merged with existing)

    Returns:
        Updated UserPreferences
    """
    # Get current preferences
    current = await get_user_preferences(user_id)
    current_dict = current.model_dump(exclude_none=True)

    # Merge updates
    for key, value in updates.items():
        if key == "notes" and isinstance(value, dict):
            # Merge notes dict rather than replacing
            current_notes = current_dict.get("notes", {})
            current_notes.update(value)
            current_dict["notes"] = current_notes
        elif key == "favorite_metrics" and isinstance(value, list):
            # For favorites, we could either replace or merge
            # For simplicity, replace (caller can include existing if desired)
            current_dict["favorite_metrics"] = value
        else:
            current_dict[key] = value

    # Save and return
    saved = storage.save_user_preferences(user_id, current_dict)
    return UserPreferences.model_validate(saved)


async def add_note(
    user_id: str,
    subject: str,
    note: str,
) -> UserPreferences:
    """Add a note about a metric, dashboard, or topic.

    Notes are keyed by subject and replace any existing note for that subject.

    Args:
        user_id: User's UID
        subject: Subject of the note (e.g., metric name)
        note: The note content

    Returns:
        Updated UserPreferences
    """
    return await update_user_preferences(user_id, {"notes": {subject: note}})


async def add_favorite(user_id: str, metric_name: str) -> UserPreferences:
    """Add a metric to favorites.

    Args:
        user_id: User's UID
        metric_name: Name of the metric to add

    Returns:
        Updated UserPreferences
    """
    current = await get_user_preferences(user_id)
    favorites = list(current.favorite_metrics)
    if metric_name not in favorites:
        favorites.append(metric_name)
    return await update_user_preferences(user_id, {"favorite_metrics": favorites})


async def remove_favorite(user_id: str, metric_name: str) -> UserPreferences:
    """Remove a metric from favorites.

    Args:
        user_id: User's UID
        metric_name: Name of the metric to remove

    Returns:
        Updated UserPreferences
    """
    current = await get_user_preferences(user_id)
    favorites = [m for m in current.favorite_metrics if m != metric_name]
    return await update_user_preferences(user_id, {"favorite_metrics": favorites})


async def remove_note(user_id: str, subject: str) -> UserPreferences:
    """Remove a note by subject.

    Args:
        user_id: User's UID
        subject: Subject of the note to remove

    Returns:
        Updated UserPreferences
    """
    current = await get_user_preferences(user_id)
    notes = dict(current.notes)
    notes.pop(subject, None)
    return await update_user_preferences(user_id, {"notes": notes})
