"""Unit tests for the context service module."""

import pytest
from unittest.mock import patch, MagicMock
from services.context import (
    UserPreferences,
    get_user_preferences,
    update_user_preferences,
    add_note,
    add_favorite,
    remove_favorite,
    remove_note,
)


class TestUserPreferences:
    """Tests for UserPreferences model."""

    def test_default_preferences(self):
        """Test default values for UserPreferences."""
        prefs = UserPreferences()
        assert prefs.default_currency is None
        assert prefs.default_grain is None
        assert prefs.decimal_places is None
        assert prefs.favorite_metrics == []
        assert prefs.preferred_chart_type is None
        assert prefs.notes == {}
        assert prefs.custom_instructions is None

    def test_preferences_with_values(self):
        """Test UserPreferences with values."""
        prefs = UserPreferences(
            default_currency="USD",
            default_grain="month",
            decimal_places=2,
            favorite_metrics=["revenue", "orders"],
            notes={"revenue": "Excludes refunds"},
            custom_instructions="Always show YoY comparison",
        )
        assert prefs.default_currency == "USD"
        assert prefs.default_grain == "month"
        assert prefs.decimal_places == 2
        assert prefs.favorite_metrics == ["revenue", "orders"]
        assert prefs.notes == {"revenue": "Excludes refunds"}


class TestGetUserPreferences:
    """Tests for get_user_preferences function."""

    @pytest.mark.asyncio
    async def test_get_existing_preferences(self):
        """Test getting existing user preferences."""
        mock_data = {
            "default_currency": "EUR",
            "default_grain": "week",
            "favorite_metrics": ["total_revenue"],
        }

        with patch("services.context.storage") as mock_storage:
            mock_storage.get_user_preferences.return_value = mock_data

            prefs = await get_user_preferences("user-123")

            mock_storage.get_user_preferences.assert_called_once_with("user-123")
            assert prefs.default_currency == "EUR"
            assert prefs.default_grain == "week"
            assert prefs.favorite_metrics == ["total_revenue"]

    @pytest.mark.asyncio
    async def test_get_nonexistent_preferences(self):
        """Test getting preferences for user with no saved preferences."""
        with patch("services.context.storage") as mock_storage:
            mock_storage.get_user_preferences.return_value = None

            prefs = await get_user_preferences("new-user")

            assert prefs.default_currency is None
            assert prefs.favorite_metrics == []


class TestUpdateUserPreferences:
    """Tests for update_user_preferences function."""

    @pytest.mark.asyncio
    async def test_update_currency(self):
        """Test updating currency preference."""
        with patch("services.context.storage") as mock_storage:
            mock_storage.get_user_preferences.return_value = None
            mock_storage.save_user_preferences.return_value = {
                "default_currency": "GBP",
            }

            prefs = await update_user_preferences("user-123", {"default_currency": "GBP"})

            assert prefs.default_currency == "GBP"
            mock_storage.save_user_preferences.assert_called_once()

    @pytest.mark.asyncio
    async def test_merge_notes(self):
        """Test that notes are merged, not replaced."""
        existing = {"notes": {"revenue": "Note 1"}}

        with patch("services.context.storage") as mock_storage:
            mock_storage.get_user_preferences.return_value = existing
            mock_storage.save_user_preferences.return_value = {
                "notes": {"revenue": "Note 1", "orders": "Note 2"},
            }

            prefs = await update_user_preferences(
                "user-123",
                {"notes": {"orders": "Note 2"}}
            )

            # Check that save was called with merged notes
            call_args = mock_storage.save_user_preferences.call_args[0]
            saved_data = call_args[1]
            assert "revenue" in saved_data["notes"]
            assert "orders" in saved_data["notes"]


class TestAddNote:
    """Tests for add_note function."""

    @pytest.mark.asyncio
    async def test_add_new_note(self):
        """Test adding a new note."""
        with patch("services.context.storage") as mock_storage:
            mock_storage.get_user_preferences.return_value = None
            mock_storage.save_user_preferences.return_value = {
                "notes": {"revenue": "This is a test note"},
            }

            prefs = await add_note("user-123", "revenue", "This is a test note")

            assert "revenue" in prefs.notes
            assert prefs.notes["revenue"] == "This is a test note"


class TestAddFavorite:
    """Tests for add_favorite function."""

    @pytest.mark.asyncio
    async def test_add_new_favorite(self):
        """Test adding a new favorite metric."""
        with patch("services.context.storage") as mock_storage:
            mock_storage.get_user_preferences.return_value = {"favorite_metrics": []}
            mock_storage.save_user_preferences.return_value = {
                "favorite_metrics": ["total_revenue"],
            }

            prefs = await add_favorite("user-123", "total_revenue")

            assert "total_revenue" in prefs.favorite_metrics

    @pytest.mark.asyncio
    async def test_add_duplicate_favorite(self):
        """Test adding a metric that's already a favorite (no duplicate)."""
        with patch("services.context.storage") as mock_storage:
            mock_storage.get_user_preferences.return_value = {
                "favorite_metrics": ["total_revenue"]
            }
            mock_storage.save_user_preferences.return_value = {
                "favorite_metrics": ["total_revenue"],
            }

            prefs = await add_favorite("user-123", "total_revenue")

            # Should not duplicate
            assert prefs.favorite_metrics.count("total_revenue") == 1


class TestRemoveFavorite:
    """Tests for remove_favorite function."""

    @pytest.mark.asyncio
    async def test_remove_favorite(self):
        """Test removing a favorite metric."""
        with patch("services.context.storage") as mock_storage:
            mock_storage.get_user_preferences.return_value = {
                "favorite_metrics": ["total_revenue", "orders"]
            }
            mock_storage.save_user_preferences.return_value = {
                "favorite_metrics": ["orders"],
            }

            prefs = await remove_favorite("user-123", "total_revenue")

            assert "total_revenue" not in prefs.favorite_metrics


class TestRemoveNote:
    """Tests for remove_note function."""

    @pytest.mark.asyncio
    async def test_remove_note(self):
        """Test removing a note by subject."""
        with patch("services.context.storage") as mock_storage:
            mock_storage.get_user_preferences.return_value = {
                "notes": {"revenue": "Note 1", "orders": "Note 2"}
            }
            mock_storage.save_user_preferences.return_value = {
                "notes": {"orders": "Note 2"},
            }

            prefs = await remove_note("user-123", "revenue")

            assert "revenue" not in prefs.notes
