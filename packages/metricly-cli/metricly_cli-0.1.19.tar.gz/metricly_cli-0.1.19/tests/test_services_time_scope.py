"""Tests for time_scope service module."""

import pytest
from datetime import date

from services.time_scope import (
    get_period_start,
    get_period_end,
    get_previous_period_start,
    calculate_time_scope_range,
    should_apply_time_scope,
    apply_time_scope,
)


class TestGetPeriodStart:
    """Tests for get_period_start function."""

    def test_day_grain(self):
        d = date(2024, 6, 15)
        assert get_period_start(d, "day") == date(2024, 6, 15)

    def test_week_grain_monday(self):
        # Monday should return same date
        d = date(2024, 6, 17)  # Monday
        assert get_period_start(d, "week") == date(2024, 6, 17)

    def test_week_grain_wednesday(self):
        # Wednesday should return Monday of same week
        d = date(2024, 6, 19)  # Wednesday
        assert get_period_start(d, "week") == date(2024, 6, 17)

    def test_week_grain_sunday(self):
        # Sunday should return Monday of same week
        d = date(2024, 6, 23)  # Sunday
        assert get_period_start(d, "week") == date(2024, 6, 17)

    def test_month_grain(self):
        d = date(2024, 6, 15)
        assert get_period_start(d, "month") == date(2024, 6, 1)

    def test_quarter_grain_q1(self):
        d = date(2024, 2, 15)
        assert get_period_start(d, "quarter") == date(2024, 1, 1)

    def test_quarter_grain_q2(self):
        d = date(2024, 5, 15)
        assert get_period_start(d, "quarter") == date(2024, 4, 1)

    def test_quarter_grain_q3(self):
        d = date(2024, 8, 15)
        assert get_period_start(d, "quarter") == date(2024, 7, 1)

    def test_quarter_grain_q4(self):
        d = date(2024, 11, 15)
        assert get_period_start(d, "quarter") == date(2024, 10, 1)

    def test_year_grain(self):
        d = date(2024, 6, 15)
        assert get_period_start(d, "year") == date(2024, 1, 1)


class TestGetPeriodEnd:
    """Tests for get_period_end function."""

    def test_day_grain(self):
        d = date(2024, 6, 15)
        assert get_period_end(d, "day") == date(2024, 6, 15)

    def test_week_grain_monday(self):
        d = date(2024, 6, 17)  # Monday
        assert get_period_end(d, "week") == date(2024, 6, 23)  # Sunday

    def test_month_grain(self):
        d = date(2024, 6, 15)
        assert get_period_end(d, "month") == date(2024, 6, 30)

    def test_month_grain_february_leap_year(self):
        d = date(2024, 2, 15)  # 2024 is leap year
        assert get_period_end(d, "month") == date(2024, 2, 29)

    def test_month_grain_december(self):
        d = date(2024, 12, 15)
        assert get_period_end(d, "month") == date(2024, 12, 31)

    def test_quarter_grain_q1(self):
        d = date(2024, 2, 15)
        assert get_period_end(d, "quarter") == date(2024, 3, 31)

    def test_quarter_grain_q4(self):
        d = date(2024, 11, 15)
        assert get_period_end(d, "quarter") == date(2024, 12, 31)

    def test_year_grain(self):
        d = date(2024, 6, 15)
        assert get_period_end(d, "year") == date(2024, 12, 31)


class TestGetPreviousPeriodStart:
    """Tests for get_previous_period_start function."""

    def test_day_grain(self):
        d = date(2024, 6, 15)
        assert get_previous_period_start(d, "day") == date(2024, 6, 14)

    def test_week_grain(self):
        d = date(2024, 6, 19)  # Wednesday
        # Current week starts June 17, previous week starts June 10
        assert get_previous_period_start(d, "week") == date(2024, 6, 10)

    def test_month_grain(self):
        d = date(2024, 6, 15)
        assert get_previous_period_start(d, "month") == date(2024, 5, 1)

    def test_month_grain_january(self):
        d = date(2024, 1, 15)
        assert get_previous_period_start(d, "month") == date(2023, 12, 1)

    def test_quarter_grain_q2(self):
        d = date(2024, 5, 15)  # Q2
        assert get_previous_period_start(d, "quarter") == date(2024, 1, 1)

    def test_quarter_grain_q1(self):
        d = date(2024, 2, 15)  # Q1
        assert get_previous_period_start(d, "quarter") == date(2023, 10, 1)

    def test_year_grain(self):
        d = date(2024, 6, 15)
        assert get_previous_period_start(d, "year") == date(2023, 1, 1)


class TestCalculateTimeScopeRange:
    """Tests for calculate_time_scope_range function."""

    def test_range_raises_error(self):
        with pytest.raises(ValueError, match="should use dashboard date range"):
            calculate_time_scope_range("range", "month")

    def test_latest_month(self):
        ref = date(2024, 6, 15)
        start, end = calculate_time_scope_range("latest", "month", ref)
        assert start == date(2024, 6, 1)
        assert end == date(2024, 6, 15)

    def test_latest_complete_month(self):
        ref = date(2024, 6, 15)
        start, end = calculate_time_scope_range("latest_complete", "month", ref)
        assert start == date(2024, 5, 1)
        assert end == date(2024, 5, 31)

    def test_latest_day(self):
        ref = date(2024, 6, 15)
        start, end = calculate_time_scope_range("latest", "day", ref)
        assert start == date(2024, 6, 15)
        assert end == date(2024, 6, 15)

    def test_latest_complete_day(self):
        ref = date(2024, 6, 15)
        start, end = calculate_time_scope_range("latest_complete", "day", ref)
        assert start == date(2024, 6, 14)
        assert end == date(2024, 6, 14)

    def test_latest_complete_quarter(self):
        ref = date(2024, 5, 15)  # Q2
        start, end = calculate_time_scope_range("latest_complete", "quarter", ref)
        assert start == date(2024, 1, 1)
        assert end == date(2024, 3, 31)


class TestShouldApplyTimeScope:
    """Tests for should_apply_time_scope function."""

    def test_none_time_scope(self):
        assert should_apply_time_scope(None, ["region"]) is False

    def test_range_time_scope(self):
        assert should_apply_time_scope("range", ["region"]) is False

    def test_latest_without_metric_time(self):
        assert should_apply_time_scope("latest", ["region"]) is True

    def test_latest_complete_without_metric_time(self):
        assert should_apply_time_scope("latest_complete", ["region", "product"]) is True

    def test_latest_with_metric_time(self):
        # Time-series query - time_scope should be ignored
        assert should_apply_time_scope("latest", ["metric_time__month"]) is False

    def test_latest_with_metric_time_and_dimensions(self):
        assert should_apply_time_scope("latest", ["region", "metric_time__day"]) is False

    def test_empty_group_by(self):
        assert should_apply_time_scope("latest", []) is True
        assert should_apply_time_scope("latest", None) is True


class TestApplyTimeScope:
    """Tests for apply_time_scope function."""

    def test_range_returns_original(self):
        start, end = apply_time_scope(
            time_scope="range",
            grain="month",
            start_date="2024-01-01",
            end_date="2024-06-30",
            group_by=["region"],
        )
        assert start == "2024-01-01"
        assert end == "2024-06-30"

    def test_latest_modifies_dates(self):
        ref = date(2024, 6, 15)
        start, end = apply_time_scope(
            time_scope="latest",
            grain="month",
            start_date="2024-01-01",
            end_date="2024-06-30",
            group_by=["region"],
            reference_date=ref,
        )
        assert start == "2024-06-01"
        assert end == "2024-06-15"

    def test_latest_complete_modifies_dates(self):
        ref = date(2024, 6, 15)
        start, end = apply_time_scope(
            time_scope="latest_complete",
            grain="month",
            start_date="2024-01-01",
            end_date="2024-06-30",
            group_by=["region"],
            reference_date=ref,
        )
        assert start == "2024-05-01"
        assert end == "2024-05-31"

    def test_time_series_query_not_modified(self):
        ref = date(2024, 6, 15)
        start, end = apply_time_scope(
            time_scope="latest_complete",
            grain="month",
            start_date="2024-01-01",
            end_date="2024-06-30",
            group_by=["metric_time__month"],
            reference_date=ref,
        )
        # Should return original dates (time-series query)
        assert start == "2024-01-01"
        assert end == "2024-06-30"
