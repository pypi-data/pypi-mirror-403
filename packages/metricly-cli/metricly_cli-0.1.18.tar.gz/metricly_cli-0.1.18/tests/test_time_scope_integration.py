"""Integration tests for time_scope feature.

These tests verify that widgets with different time_scope settings
actually query different date ranges and return different data.

To run against emulators with full E2E:
    # Start emulators first: pnpm dev:firebase
    # Then run seed: pnpm seed
    FIRESTORE_EMULATOR_HOST=localhost:8081 pytest tests/test_time_scope_integration.py -v
"""

import pytest
from datetime import date
from unittest.mock import patch, AsyncMock

from services.time_scope import (
    calculate_time_scope_range,
    apply_time_scope,
    should_apply_time_scope,
)


# =============================================================================
# Scenario Tests: Two KPIs, Same Metric, Different time_scope
# =============================================================================


class TestTimeScopeScenarios:
    """
    Test real-world scenarios where two widgets differ only by time_scope.

    Scenario: Dashboard shows two KPIs for "total_revenue"
    - KPI 1: "This Month Revenue" with time_scope="latest"
    - KPI 2: "YTD Revenue" with time_scope="range" (or None)

    These should query different date ranges and return different values.
    """

    def test_latest_vs_range_date_calculation(self):
        """Verify 'latest' and 'range' produce different date ranges."""
        # Simulate mid-month query (e.g., Jan 15, 2026)
        reference = date(2026, 1, 15)
        dashboard_start = "2025-01-01"  # YTD
        dashboard_end = "2026-01-15"
        grain = "month"

        # KPI 1: time_scope="latest" - should get current month only
        latest_range = calculate_time_scope_range(
            time_scope="latest",
            grain=grain,
            reference_date=reference,
        )

        # KPI 2: time_scope=None (range) - should use full dashboard range
        range_start, range_end = apply_time_scope(
            time_scope=None,
            grain=grain,
            start_date=dashboard_start,
            end_date=dashboard_end,
            group_by=[],  # KPI has no dimensions
        )

        # "latest" should give Jan 1-15, 2026 (current month)
        assert latest_range[0] == date(2026, 1, 1)
        assert latest_range[1] == date(2026, 1, 15)

        # "range" (None) should give full dashboard range (unchanged)
        assert range_start == "2025-01-01"
        assert range_end == "2026-01-15"

        # The ranges are different!
        assert latest_range[0].isoformat() != range_start

    def test_latest_complete_vs_latest(self):
        """
        Verify 'latest_complete' and 'latest' produce different date ranges.

        Scenario: Dashboard shows two KPIs
        - KPI 1: "This Month Revenue" with time_scope="latest"
        - KPI 2: "Last Month Revenue" with time_scope="latest_complete"
        """
        reference = date(2026, 1, 15)
        grain = "month"

        # KPI 1: "latest" - current incomplete month
        latest_range = calculate_time_scope_range(
            time_scope="latest",
            grain=grain,
            reference_date=reference,
        )

        # KPI 2: "latest_complete" - last complete month
        latest_complete_range = calculate_time_scope_range(
            time_scope="latest_complete",
            grain=grain,
            reference_date=reference,
        )

        # "latest" = Jan 1-15, 2026 (incomplete)
        assert latest_range[0] == date(2026, 1, 1)
        assert latest_range[1] == date(2026, 1, 15)

        # "latest_complete" = Dec 1-31, 2025 (complete month)
        assert latest_complete_range[0] == date(2025, 12, 1)
        assert latest_complete_range[1] == date(2025, 12, 31)

        # Different months!
        assert latest_range[0].month != latest_complete_range[0].month

    def test_time_series_chart_ignores_time_scope(self):
        """
        Time-series charts should NOT have time_scope applied.

        A line chart with grain="month" needs the full date range to show trends.
        """
        dashboard_start = "2025-01-01"
        dashboard_end = "2026-01-15"

        # Line chart with metric_time in group_by
        result_start, result_end = apply_time_scope(
            time_scope="latest",
            grain="month",
            start_date=dashboard_start,
            end_date=dashboard_end,
            group_by=["metric_time__month"],  # Time-series query
        )

        # Should return original range, not apply time_scope
        assert result_start == dashboard_start
        assert result_end == dashboard_end

    def test_kpi_applies_time_scope(self):
        """
        KPI widgets (no metric_time) should have time_scope applied.
        """
        reference = date(2026, 1, 15)
        dashboard_start = "2025-01-01"
        dashboard_end = "2026-01-15"

        # KPI with no time dimension
        result_start, result_end = apply_time_scope(
            time_scope="latest",
            grain="month",
            start_date=dashboard_start,
            end_date=dashboard_end,
            group_by=[],  # No dimensions - typical KPI
            reference_date=reference,
        )

        # Should apply time_scope, returning current month only
        assert result_start == "2026-01-01"
        assert result_end == "2026-01-15"
        assert result_start != dashboard_start  # Different from original!


class TestQueryDateRangeVerification:
    """
    Tests that verify the actual query date ranges passed to the query engine.

    These simulate what would happen when useWidgetData calls the API.
    """

    def test_mock_query_flow_latest_vs_range(self):
        """
        Simulate the full flow: widget config -> date calculation -> query

        Two widgets on the same dashboard:
        1. KPI "This Month Revenue" with time_scope="latest"
        2. KPI "Total Revenue" with time_scope=None (uses dashboard range)

        Verify they would send different date ranges to the query API.
        """
        # Dashboard settings
        dashboard_grain = "month"
        dashboard_start = "2025-01-01"
        dashboard_end = "2026-01-15"
        reference = date(2026, 1, 15)

        # Widget 1: time_scope="latest"
        w1_start, w1_end = apply_time_scope(
            time_scope="latest",
            grain=dashboard_grain,
            start_date=dashboard_start,
            end_date=dashboard_end,
            group_by=[],
            reference_date=reference,
        )

        # Widget 2: time_scope=None (range)
        w2_start, w2_end = apply_time_scope(
            time_scope=None,
            grain=dashboard_grain,
            start_date=dashboard_start,
            end_date=dashboard_end,
            group_by=[],
            reference_date=reference,
        )

        # Build simulated query params
        query1 = {
            "metrics": ["total_revenue"],
            "start_date": w1_start,
            "end_date": w1_end,
        }

        query2 = {
            "metrics": ["total_revenue"],
            "start_date": w2_start,
            "end_date": w2_end,
        }

        # Verify the queries have different date ranges
        assert query1["start_date"] != query2["start_date"], \
            "Widget with time_scope='latest' should have different start_date"

        # Widget 1 should query just current month
        assert query1["start_date"] == "2026-01-01"
        assert query1["end_date"] == "2026-01-15"

        # Widget 2 should query full dashboard range
        assert query2["start_date"] == "2025-01-01"
        assert query2["end_date"] == "2026-01-15"

    def test_mock_query_with_mock_data(self):
        """
        Simulate query results to verify the numbers add up.

        Mock data:
        - Jan 2025: $100k
        - Feb 2025: $150k
        - ... (monthly data)
        - Dec 2025: $200k
        - Jan 2026 (partial): $50k

        Widget 1 (latest, month grain, Jan 15): Should show $50k
        Widget 2 (range, full YTD): Should show $50k + all of 2025 = much more
        """
        # Mock monthly revenue data
        monthly_revenue = {
            "2025-01": 100_000,
            "2025-02": 150_000,
            "2025-03": 120_000,
            "2025-04": 180_000,
            "2025-05": 160_000,
            "2025-06": 200_000,
            "2025-07": 190_000,
            "2025-08": 210_000,
            "2025-09": 220_000,
            "2025-10": 250_000,
            "2025-11": 280_000,
            "2025-12": 300_000,
            "2026-01": 50_000,  # Partial month
        }

        def mock_query(start_date_str: str, end_date_str: str) -> int:
            """Simulate querying revenue for a date range."""
            start_date = date.fromisoformat(start_date_str)
            end_date = date.fromisoformat(end_date_str)
            total = 0
            for month_key, amount in monthly_revenue.items():
                year, month = map(int, month_key.split("-"))
                month_start = date(year, month, 1)
                # Simplified: count month if it overlaps with range
                if month_start >= start_date and month_start <= end_date:
                    total += amount
            return total

        # Widget 1: time_scope="latest" for Jan 2026
        latest_range = calculate_time_scope_range(
            time_scope="latest",
            grain="month",
            reference_date=date(2026, 1, 15),
        )
        widget1_result = mock_query(
            latest_range[0].isoformat(),
            latest_range[1].isoformat()
        )

        # Widget 2: time_scope=None (full range)
        widget2_result = mock_query("2025-01-01", "2026-01-15")

        # Widget 1 should show only Jan 2026 partial
        assert widget1_result == 50_000, f"Latest month should be $50k, got ${widget1_result:,}"

        # Widget 2 should show all months
        expected_total = sum(monthly_revenue.values())
        assert widget2_result == expected_total, \
            f"Total range should be ${expected_total:,}, got ${widget2_result:,}"

        # The values are different!
        assert widget1_result != widget2_result
        assert widget2_result > widget1_result

        # Verify the math: full range = all months combined
        assert widget2_result == 2_410_000


class TestEdgeCases:
    """Test edge cases for time_scope."""

    def test_first_day_of_month_latest(self):
        """On first day of month, 'latest' should still be valid."""
        result = calculate_time_scope_range(
            time_scope="latest",
            grain="month",
            reference_date=date(2026, 1, 1),
        )
        assert result[0] == date(2026, 1, 1)
        assert result[1] == date(2026, 1, 1)

    def test_last_day_of_month_latest_complete(self):
        """On last day of month, 'latest_complete' should return previous month."""
        result = calculate_time_scope_range(
            time_scope="latest_complete",
            grain="month",
            reference_date=date(2026, 1, 31),
        )
        # Still should return December 2025, not January (which is still the current period)
        assert result[0] == date(2025, 12, 1)
        assert result[1] == date(2025, 12, 31)

    def test_year_boundary(self):
        """Test time_scope across year boundary."""
        # On Jan 5, 2026, latest_complete for year grain should be 2025
        result = calculate_time_scope_range(
            time_scope="latest_complete",
            grain="year",
            reference_date=date(2026, 1, 5),
        )
        assert result[0] == date(2025, 1, 1)
        assert result[1] == date(2025, 12, 31)

    def test_week_grain_monday_start(self):
        """Week grain should use Monday as start of week."""
        # Wednesday Jan 15, 2026
        result = calculate_time_scope_range(
            time_scope="latest",
            grain="week",
            reference_date=date(2026, 1, 15),
        )
        # Week should start Monday Jan 12
        assert result[0] == date(2026, 1, 12)
        assert result[0].weekday() == 0  # Monday


# =============================================================================
# E2E Test with Real Query (requires emulators + DuckDB)
# =============================================================================

@pytest.mark.skipif(
    True,  # Set to False when running with emulators
    reason="Requires emulators: FIRESTORE_EMULATOR_HOST=localhost:8081"
)
class TestTimeScopeE2E:
    """
    End-to-end tests that query the actual DuckDB database.

    To run these tests:
    1. Start emulators: pnpm dev:firebase
    2. Seed data: pnpm seed
    3. Run: FIRESTORE_EMULATOR_HOST=localhost:8081 pytest tests/test_time_scope_integration.py::TestTimeScopeE2E -v
    """

    @pytest.fixture
    def mock_user(self):
        from services.auth import UserContext
        return UserContext(
            uid="test-user",
            email="demo@metricly.xyz",
            org_id="local-dev",
            org_name="Local Dev",
            role="owner",
        )

    @pytest.mark.asyncio
    async def test_revenue_latest_vs_range(self, mock_user):
        """
        Query total_revenue with different time_scope settings.

        This test verifies that:
        1. time_scope="latest" returns data for current period only
        2. time_scope=None returns data for full date range
        3. The values are different
        """
        from services.queries import query_metrics, QueryParams

        # Use a fixed reference date in the demo data range
        reference = date(2024, 6, 15)  # Mid-June 2024

        # Calculate date ranges
        latest_range = calculate_time_scope_range(
            time_scope="latest",
            grain="month",
            reference_date=reference,
        )

        # Query 1: "This month" (June 2024 only)
        result1 = await query_metrics(
            org_id=mock_user.org_id,
            params=QueryParams(
                metrics=["total_revenue"],
                start_date=latest_range[0],
                end_date=latest_range[1],
            ),
        )

        # Query 2: Full range (Jan 2024 - June 15, 2024)
        result2 = await query_metrics(
            org_id=mock_user.org_id,
            params=QueryParams(
                metrics=["total_revenue"],
                start_date=date(2024, 1, 1),
                end_date=reference,
            ),
        )

        # Extract values
        value1 = result1.data[0]["total_revenue"] if result1.data else 0
        value2 = result2.data[0]["total_revenue"] if result2.data else 0

        print(f"\ntime_scope='latest' (June only): ${value1:,.2f}")
        print(f"time_scope=None (YTD): ${value2:,.2f}")

        # Verify different values
        assert value1 != value2, "Latest and range should return different values"
        assert value2 > value1, "Full range should be larger than single month"

        # The full range should include the latest month
        assert value2 >= value1
