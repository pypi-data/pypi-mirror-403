"""Unit tests for the export service module."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from services.export import (
    ExportResult,
    export_query_data,
    export_dashboard_data,
    _to_csv,
    _to_json,
)
from services.auth import UserContext
from services.queries import QueryParams, QueryResult


@pytest.fixture
def mock_user():
    """Create a mock user context."""
    return UserContext(
        uid="test-user",
        email="test@example.com",
        org_id="test-org",
        org_name="Test Org",
        role="viewer",
    )


class TestToCsv:
    """Tests for CSV conversion."""

    def test_basic_csv(self):
        data = [
            {"name": "Alice", "value": 100},
            {"name": "Bob", "value": 200},
        ]
        columns = ["name", "value"]
        result = _to_csv(data, columns)

        # CSV module uses \r\n line endings, normalize for comparison
        lines = [line.strip() for line in result.strip().split("\n")]
        assert len(lines) == 3  # header + 2 rows
        assert lines[0] == "name,value"
        assert lines[1] == "Alice,100"
        assert lines[2] == "Bob,200"

    def test_csv_with_missing_columns(self):
        data = [
            {"name": "Alice", "value": 100, "extra": "ignored"},
            {"name": "Bob"},  # missing value
        ]
        columns = ["name", "value"]
        result = _to_csv(data, columns)

        lines = result.strip().split("\n")
        assert len(lines) == 3
        assert "Alice" in lines[1]

    def test_empty_data(self):
        data = []
        columns = ["name", "value"]
        result = _to_csv(data, columns)

        lines = result.strip().split("\n")
        assert len(lines) == 1  # header only
        assert lines[0] == "name,value"


class TestToJson:
    """Tests for JSON conversion."""

    def test_basic_json(self):
        import json
        data = [
            {"name": "Alice", "value": 100},
            {"name": "Bob", "value": 200},
        ]
        result = _to_json(data)
        parsed = json.loads(result)

        assert len(parsed) == 2
        assert parsed[0]["name"] == "Alice"
        assert parsed[1]["value"] == 200

    def test_empty_json(self):
        import json
        data = []
        result = _to_json(data)
        parsed = json.loads(result)

        assert parsed == []


class TestExportQueryData:
    """Tests for export_query_data function."""

    @pytest.mark.asyncio
    async def test_export_csv(self, mock_user):
        """Test exporting query results to CSV."""
        mock_result = QueryResult(
            data=[
                {"metric_time": "2024-01", "revenue": 1000},
                {"metric_time": "2024-02", "revenue": 1200},
            ],
            columns=["metric_time", "revenue"],
            row_count=2,
            query_time_ms=100.0,
        )

        with patch("services.export.query_metrics", new_callable=AsyncMock) as mock_query:
            mock_query.return_value = mock_result

            params = QueryParams(metrics=["revenue"], grain="month")
            result = await export_query_data(mock_user, params, format="csv")

            assert result.format == "csv"
            assert result.row_count == 2
            assert result.columns == ["metric_time", "revenue"]
            assert "metric_time,revenue" in result.content
            assert "2024-01" in result.content
            assert result.saved_to is None

    @pytest.mark.asyncio
    async def test_export_json(self, mock_user):
        """Test exporting query results to JSON."""
        import json

        mock_result = QueryResult(
            data=[
                {"metric_time": "2024-01", "revenue": 1000},
            ],
            columns=["metric_time", "revenue"],
            row_count=1,
            query_time_ms=100.0,
        )

        with patch("services.export.query_metrics", new_callable=AsyncMock) as mock_query:
            mock_query.return_value = mock_result

            params = QueryParams(metrics=["revenue"], grain="month")
            result = await export_query_data(mock_user, params, format="json")

            assert result.format == "json"
            parsed = json.loads(result.content)
            assert len(parsed) == 1
            assert parsed[0]["revenue"] == 1000

    @pytest.mark.asyncio
    async def test_export_to_file(self, mock_user, tmp_path):
        """Test exporting to a file."""
        mock_result = QueryResult(
            data=[{"value": 42}],
            columns=["value"],
            row_count=1,
            query_time_ms=100.0,
        )

        with patch("services.export.query_metrics", new_callable=AsyncMock) as mock_query:
            mock_query.return_value = mock_result

            output_path = str(tmp_path / "test.csv")
            params = QueryParams(metrics=["test"])
            result = await export_query_data(mock_user, params, output_path=output_path)

            assert result.saved_to == output_path

            # Verify file was written
            with open(output_path) as f:
                content = f.read()
            assert "value" in content
            assert "42" in content


class TestExportDashboardData:
    """Tests for export_dashboard_data function."""

    @pytest.mark.asyncio
    async def test_export_dashboard_csv(self, mock_user):
        """Test exporting dashboard data to CSV."""
        # Create a mock dashboard with widgets
        mock_dashboard = MagicMock()
        mock_dashboard.id = "dash-123"
        mock_dashboard.title = "Test Dashboard"

        mock_widget = MagicMock()
        mock_widget.id = "widget-1"
        mock_widget.title = "Revenue Widget"
        mock_widget.query.metrics = ["revenue"]
        mock_widget.query.dimensions = None
        mock_widget.query.grain = "month"
        mock_widget.query.limit = None
        mock_widget.query.order_by = []

        mock_section = MagicMock()
        mock_section.widgets = [mock_widget]

        mock_page = MagicMock()
        mock_page.sections = [mock_section]

        mock_dashboard.pages = [mock_page]

        mock_query_result = QueryResult(
            data=[{"revenue": 1000}],
            columns=["revenue"],
            row_count=1,
            query_time_ms=100.0,
        )

        with patch("services.export.get_dashboard", new_callable=AsyncMock) as mock_get:
            with patch("services.export.query_metrics", new_callable=AsyncMock) as mock_query:
                mock_get.return_value = mock_dashboard
                mock_query.return_value = mock_query_result

                result = await export_dashboard_data(mock_user, "dash-123", format="csv")

                assert result.format == "csv"
                assert result.row_count == 1
                assert "_widget_id" in result.columns
                assert "_widget_title" in result.columns

    @pytest.mark.asyncio
    async def test_export_dashboard_json(self, mock_user):
        """Test exporting dashboard data to JSON."""
        import json

        mock_dashboard = MagicMock()
        mock_dashboard.id = "dash-123"
        mock_dashboard.title = "Test Dashboard"

        mock_widget = MagicMock()
        mock_widget.id = "widget-1"
        mock_widget.title = "Revenue Widget"
        mock_widget.query.metrics = ["revenue"]
        mock_widget.query.dimensions = None
        mock_widget.query.grain = None
        mock_widget.query.limit = None
        mock_widget.query.order_by = []

        mock_section = MagicMock()
        mock_section.widgets = [mock_widget]

        mock_page = MagicMock()
        mock_page.sections = [mock_section]

        mock_dashboard.pages = [mock_page]

        mock_query_result = QueryResult(
            data=[{"revenue": 1000}],
            columns=["revenue"],
            row_count=1,
            query_time_ms=100.0,
        )

        with patch("services.export.get_dashboard", new_callable=AsyncMock) as mock_get:
            with patch("services.export.query_metrics", new_callable=AsyncMock) as mock_query:
                mock_get.return_value = mock_dashboard
                mock_query.return_value = mock_query_result

                result = await export_dashboard_data(mock_user, "dash-123", format="json")

                assert result.format == "json"
                parsed = json.loads(result.content)
                assert parsed["dashboard_id"] == "dash-123"
                assert parsed["dashboard_title"] == "Test Dashboard"
                assert "widgets" in parsed

    @pytest.mark.asyncio
    async def test_export_dashboard_not_found(self, mock_user):
        """Test exporting non-existent dashboard."""
        with patch("services.export.get_dashboard", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = ValueError("Dashboard not found")

            with pytest.raises(ValueError, match="Dashboard not found"):
                await export_dashboard_data(mock_user, "nonexistent")
