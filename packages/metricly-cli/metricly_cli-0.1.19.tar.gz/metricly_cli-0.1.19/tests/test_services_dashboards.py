"""Tests for dashboard service layer.

These tests verify dashboard CRUD operations including the time_scope feature.
Tests can run without emulators using mocked storage.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from copy import deepcopy
from datetime import datetime
import uuid

from services.auth import UserContext
from services.dashboards import (
    add_widget,
    update_widget,
    DEFAULT_WIDGET_WIDTHS,
)
from generated.dashboard_types import (
    DashboardDefinition,
    PageDefinition,
    SectionDefinition,
    WidgetDefinition,
    DashboardControls,
    DateRangeSelection,
    QueryDefinition,
)


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def mock_user():
    """Create a test user context."""
    return UserContext(
        uid="test-user-123",
        email="test@example.com",
        org_id="test-org",
        org_name="Test Org",
        role="owner",
    )


@pytest.fixture
def mock_dashboard():
    """Create a minimal test dashboard."""
    return DashboardDefinition(
        id="dash-123",
        title="Test Dashboard",
        owner="test-user-123",
        visibility="private",
        controls=DashboardControls(
            date_range=DateRangeSelection(mode="relative", preset="last_30_days"),
            grain="month",
            comparison="none",
        ),
        pages=[
            PageDefinition(
                id="page-1",
                title="Overview",
                sections=[
                    SectionDefinition(
                        title="Key Metrics",
                        widgets=[],
                    )
                ],
            )
        ],
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat(),
        created_by="test-user-123",
        version=1,
    )


# =============================================================================
# Widget Width Tests
# =============================================================================


class TestWidgetDefaultWidths:
    """Tests for default widget width assignment."""

    def test_default_widths_defined(self):
        """All widget types should have default widths."""
        expected_types = ["kpi", "donut", "heatmap", "area_chart", "line_chart", "bar_chart", "table"]
        for wtype in expected_types:
            assert wtype in DEFAULT_WIDGET_WIDTHS, f"Missing default width for {wtype}"

    def test_kpi_width(self):
        """KPI widgets should be 2 columns (5 per row)."""
        assert DEFAULT_WIDGET_WIDTHS["kpi"] == 2

    def test_chart_widths(self):
        """Chart widgets should be full width (10 columns)."""
        for chart_type in ["area_chart", "line_chart", "bar_chart"]:
            assert DEFAULT_WIDGET_WIDTHS[chart_type] == 10

    def test_donut_width(self):
        """Donut widgets should be 3 columns."""
        assert DEFAULT_WIDGET_WIDTHS["donut"] == 3


# =============================================================================
# Add Widget Tests
# =============================================================================


class TestAddWidget:
    """Tests for add_widget function."""

    def _make_storage_mock(self, mock_dashboard):
        """Create a mock storage that captures and returns updated dashboard."""
        mock_storage = MagicMock()
        mock_storage.get_dashboard.return_value = mock_dashboard.model_dump()

        # Capture the updates and return them as the result
        def update_dashboard_side_effect(org_id, dashboard_id, user_id, updates, expected_version):
            # Merge updates into the dashboard
            dashboard_data = mock_dashboard.model_dump()
            dashboard_data.update(updates)
            dashboard_data['version'] = (dashboard_data.get('version') or 0) + 1
            return dashboard_data

        mock_storage.update_dashboard.side_effect = update_dashboard_side_effect
        return mock_storage

    @pytest.mark.asyncio
    async def test_add_widget_applies_default_width(self, mock_user, mock_dashboard):
        """Widget should get default width if not specified."""
        mock_storage = self._make_storage_mock(mock_dashboard)

        with patch("services.dashboards.storage", mock_storage):
            widget_data = {
                "type": "kpi",
                "title": "Revenue",
                "query": {"metrics": ["total_revenue"]},
            }

            result = await add_widget(mock_user, "dash-123", widget_data)

            # Verify the widget was added with default width
            added_widget = result.pages[0].sections[0].widgets[0]
            assert added_widget.width == 2  # KPI default

    @pytest.mark.asyncio
    async def test_add_widget_preserves_explicit_width(self, mock_user, mock_dashboard):
        """Widget should keep explicitly set width."""
        mock_storage = self._make_storage_mock(mock_dashboard)

        with patch("services.dashboards.storage", mock_storage):
            widget_data = {
                "type": "kpi",
                "title": "Revenue",
                "query": {"metrics": ["total_revenue"]},
                "width": 4,  # Explicit width
            }

            result = await add_widget(mock_user, "dash-123", widget_data)

            added_widget = result.pages[0].sections[0].widgets[0]
            assert added_widget.width == 4  # Should preserve explicit width

    @pytest.mark.asyncio
    async def test_add_widget_with_time_scope_latest(self, mock_user, mock_dashboard):
        """Widget with time_scope='latest' should be stored correctly."""
        mock_storage = self._make_storage_mock(mock_dashboard)

        with patch("services.dashboards.storage", mock_storage):
            widget_data = {
                "type": "kpi",
                "title": "This Month Revenue",
                "query": {"metrics": ["total_revenue"]},
                "time_scope": "latest",
            }

            result = await add_widget(mock_user, "dash-123", widget_data)

            added_widget = result.pages[0].sections[0].widgets[0]
            assert added_widget.time_scope == "latest"

    @pytest.mark.asyncio
    async def test_add_widget_with_time_scope_latest_complete(self, mock_user, mock_dashboard):
        """Widget with time_scope='latest_complete' should be stored correctly."""
        mock_storage = self._make_storage_mock(mock_dashboard)

        with patch("services.dashboards.storage", mock_storage):
            widget_data = {
                "type": "kpi",
                "title": "Last Month Revenue",
                "query": {"metrics": ["total_revenue"]},
                "time_scope": "latest_complete",
            }

            result = await add_widget(mock_user, "dash-123", widget_data)

            added_widget = result.pages[0].sections[0].widgets[0]
            assert added_widget.time_scope == "latest_complete"

    @pytest.mark.asyncio
    async def test_add_widget_without_time_scope(self, mock_user, mock_dashboard):
        """Widget without time_scope should default to None (uses full range)."""
        mock_storage = self._make_storage_mock(mock_dashboard)

        with patch("services.dashboards.storage", mock_storage):
            widget_data = {
                "type": "kpi",
                "title": "Total Revenue",
                "query": {"metrics": ["total_revenue"]},
            }

            result = await add_widget(mock_user, "dash-123", widget_data)

            added_widget = result.pages[0].sections[0].widgets[0]
            assert added_widget.time_scope is None

    @pytest.mark.asyncio
    async def test_add_widget_generates_uuid(self, mock_user, mock_dashboard):
        """Widget should get a UUID if not provided."""
        mock_storage = self._make_storage_mock(mock_dashboard)

        with patch("services.dashboards.storage", mock_storage):
            widget_data = {
                "type": "kpi",
                "title": "Revenue",
                "query": {"metrics": ["total_revenue"]},
            }

            result = await add_widget(mock_user, "dash-123", widget_data)

            added_widget = result.pages[0].sections[0].widgets[0]
            # Should be a valid UUID
            try:
                uuid.UUID(added_widget.id)
            except ValueError:
                pytest.fail("Widget ID should be a valid UUID")


# =============================================================================
# Update Widget Tests
# =============================================================================


class TestUpdateWidget:
    """Tests for update_widget function."""

    def _make_storage_mock(self, mock_dashboard):
        """Create a mock storage that captures and returns updated dashboard."""
        mock_storage = MagicMock()
        dashboard_data = mock_dashboard.model_dump()
        mock_storage.get_dashboard.return_value = dashboard_data

        def update_dashboard_side_effect(org_id, dashboard_id, user_id, updates, expected_version):
            # Merge updates into the dashboard
            result = deepcopy(dashboard_data)
            result.update(updates)
            result['version'] = (result.get('version') or 0) + 1
            return result

        mock_storage.update_dashboard.side_effect = update_dashboard_side_effect
        return mock_storage

    @pytest.mark.asyncio
    async def test_update_widget_time_scope(self, mock_user, mock_dashboard):
        """Should be able to update widget's time_scope."""
        # Add a widget to the dashboard first
        existing_widget = WidgetDefinition(
            id="widget-1",
            type="kpi",
            title="Revenue",
            query=QueryDefinition(metrics=["total_revenue"]),
            time_scope=None,
        )
        mock_dashboard.pages[0].sections[0].widgets = [existing_widget]
        mock_storage = self._make_storage_mock(mock_dashboard)

        with patch("services.dashboards.storage", mock_storage):
            updates = {"time_scope": "latest"}

            # update_widget takes page_index, section_index, widget_index
            result = await update_widget(
                mock_user,
                "dash-123",
                page_index=0,
                section_index=0,
                widget_index=0,
                updates=updates,
            )

            updated_widget = result.pages[0].sections[0].widgets[0]
            assert updated_widget.time_scope == "latest"

    @pytest.mark.asyncio
    async def test_update_widget_clear_time_scope(self, mock_user, mock_dashboard):
        """Should be able to clear widget's time_scope by setting to None."""
        existing_widget = WidgetDefinition(
            id="widget-1",
            type="kpi",
            title="Revenue",
            query=QueryDefinition(metrics=["total_revenue"]),
            time_scope="latest",
        )
        mock_dashboard.pages[0].sections[0].widgets = [existing_widget]
        mock_storage = self._make_storage_mock(mock_dashboard)

        with patch("services.dashboards.storage", mock_storage):
            updates = {"time_scope": None}

            result = await update_widget(
                mock_user,
                "dash-123",
                page_index=0,
                section_index=0,
                widget_index=0,
                updates=updates,
            )

            updated_widget = result.pages[0].sections[0].widgets[0]
            assert updated_widget.time_scope is None


# =============================================================================
# Backwards Compatibility Tests
# =============================================================================


class TestTimeScopeBackwardsCompatibility:
    """
    Tests ensuring time_scope is backwards compatible.

    IMPORTANT: Widgets without time_scope (or time_scope=None/range) must
    behave exactly as before - using the full dashboard date range.
    """

    def test_null_time_scope_uses_full_range(self):
        """Widget with time_scope=None should use full dashboard range."""
        from services.time_scope import apply_time_scope

        dashboard_start = "2025-01-01"
        dashboard_end = "2026-01-15"

        result_start, result_end = apply_time_scope(
            time_scope=None,  # Not specified
            grain="month",
            start_date=dashboard_start,
            end_date=dashboard_end,
            group_by=[],
        )

        # Should return original range unchanged
        assert result_start == dashboard_start
        assert result_end == dashboard_end

    def test_range_time_scope_uses_full_range(self):
        """Widget with time_scope='range' should use full dashboard range."""
        from services.time_scope import apply_time_scope

        dashboard_start = "2025-01-01"
        dashboard_end = "2026-01-15"

        result_start, result_end = apply_time_scope(
            time_scope="range",  # Explicit full range
            grain="month",
            start_date=dashboard_start,
            end_date=dashboard_end,
            group_by=[],
        )

        # Should return original range unchanged
        assert result_start == dashboard_start
        assert result_end == dashboard_end

    def test_existing_widgets_unaffected(self):
        """
        Existing widgets (without time_scope field) must work unchanged.

        This tests the scenario where an old dashboard JSON doesn't have
        the time_scope field at all.
        """
        # Simulate old widget definition without time_scope
        old_widget_data = {
            "id": "widget-123",
            "type": "kpi",
            "title": "Revenue",
            "query": {"metrics": ["total_revenue"]},
            # Note: no time_scope field
        }

        # Widget should be valid
        widget = WidgetDefinition(**old_widget_data)
        assert widget.time_scope is None  # Defaults to None

    def test_default_is_full_range_behavior(self):
        """
        Default behavior (time_scope=None) must match pre-feature behavior.

        This is the critical backwards compatibility test.
        """
        from services.time_scope import should_apply_time_scope

        # With time_scope=None, should_apply_time_scope returns False
        # meaning the original date range is used unchanged
        assert should_apply_time_scope(None, []) is False
        assert should_apply_time_scope(None, ["region"]) is False
        assert should_apply_time_scope(None, ["metric_time__month"]) is False


# =============================================================================
# Time Scope Validation Tests
# =============================================================================


class TestTimeScopeValidation:
    """Tests for time_scope field validation."""

    @pytest.mark.asyncio
    async def test_invalid_time_scope_rejected(self, mock_user, mock_dashboard):
        """Invalid time_scope values should be rejected by Pydantic."""
        with patch("services.dashboards.storage") as mock_storage:
            mock_storage.get_dashboard.return_value = mock_dashboard.model_dump()

            widget_data = {
                "type": "kpi",
                "title": "Revenue",
                "query": {"metrics": ["total_revenue"]},
                "time_scope": "invalid_value",  # Invalid
            }

            # Should raise validation error
            with pytest.raises(Exception):  # Pydantic ValidationError
                await add_widget(mock_user, "dash-123", widget_data)

    def test_valid_time_scope_values(self):
        """Valid time_scope values should be accepted."""
        valid_values = ["range", "latest", "latest_complete", None]

        for value in valid_values:
            widget = WidgetDefinition(
                id="test",
                type="kpi",
                title="Test",
                query=QueryDefinition(metrics=["test"]),
                time_scope=value,
            )
            assert widget.time_scope == value

    @pytest.mark.asyncio
    async def test_time_scope_in_query_rejected_with_helpful_error(self, mock_user, mock_dashboard):
        """time_scope inside query should be rejected with helpful error message."""
        with patch("services.dashboards.storage") as mock_storage:
            mock_storage.get_dashboard.return_value = mock_dashboard.model_dump()

            widget_data = {
                "type": "kpi",
                "title": "Revenue",
                "query": {
                    "metrics": ["total_revenue"],
                    "time_scope": "latest",  # Wrong place!
                },
            }

            # Should raise ValueError with helpful message
            with pytest.raises(ValueError) as exc_info:
                await add_widget(mock_user, "dash-123", widget_data)

            assert "time_scope must be at widget level" in str(exc_info.value)
            assert "not inside query" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_widget_time_scope_in_query_rejected(self, mock_user):
        """Updating widget with time_scope in query should be rejected."""
        # Create dashboard with existing widget
        dashboard_with_widget = DashboardDefinition(
            id="dash-123",
            title="Test Dashboard",
            owner="test-user-123",
            visibility="private",
            controls=DashboardControls(
                date_range=DateRangeSelection(mode="relative", preset="last_30_days"),
                grain="month",
                comparison="none",
            ),
            pages=[
                PageDefinition(
                    id="page-1",
                    title="Overview",
                    sections=[
                        SectionDefinition(
                            title="Key Metrics",
                            widgets=[
                                WidgetDefinition(
                                    id="widget-1",
                                    type="kpi",
                                    title="Revenue",
                                    query=QueryDefinition(metrics=["total_revenue"]),
                                )
                            ],
                        )
                    ],
                )
            ],
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            created_by="test-user-123",
            version=1,
        )

        with patch("services.dashboards.get_dashboard") as mock_get, \
             patch("services.dashboards.update_dashboard") as mock_update:
            mock_get.return_value = dashboard_with_widget

            updates = {
                "query": {
                    "metrics": ["total_revenue"],
                    "time_scope": "latest",  # Wrong place!
                },
            }

            with pytest.raises(ValueError) as exc_info:
                await update_widget(mock_user, "dash-123", 0, 0, 0, updates)

            assert "time_scope must be at widget level" in str(exc_info.value)
