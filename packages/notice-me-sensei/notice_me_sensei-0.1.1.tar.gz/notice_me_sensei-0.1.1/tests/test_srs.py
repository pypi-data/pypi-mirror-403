"""Tests for SRS algorithm."""

from datetime import datetime, timedelta

from sensei.srs import (
    calculate_due_date_from_days,
    calculate_next_interval,
    get_initial_srs_metadata,
)


class TestInitialMetadata:
    def test_initial_values(self):
        meta = get_initial_srs_metadata()
        assert meta["interval_days"] == 1
        assert meta["ease_factor"] == 2.5
        assert meta["repetition_count"] == 0


class TestCalculateNextInterval:
    def test_first_pass(self):
        meta = get_initial_srs_metadata()
        new_meta, due = calculate_next_interval(meta, passed=True)

        assert new_meta["repetition_count"] == 1
        assert new_meta["interval_days"] == 1
        assert due > datetime.now()

    def test_second_pass(self):
        meta = {"interval_days": 1, "ease_factor": 2.5, "repetition_count": 1}
        new_meta, due = calculate_next_interval(meta, passed=True)

        assert new_meta["repetition_count"] == 2
        assert new_meta["interval_days"] == 3

    def test_third_pass(self):
        meta = {"interval_days": 3, "ease_factor": 2.5, "repetition_count": 2}
        new_meta, due = calculate_next_interval(meta, passed=True)

        assert new_meta["repetition_count"] == 3
        # 3 * 2.5 = 7.5, rounded to 8
        assert new_meta["interval_days"] == 8

    def test_fail_resets_count(self):
        meta = {"interval_days": 7, "ease_factor": 2.5, "repetition_count": 3}
        new_meta, due = calculate_next_interval(meta, passed=False)

        assert new_meta["repetition_count"] == 0
        assert new_meta["interval_days"] == 1
        assert new_meta["ease_factor"] == 2.3  # 2.5 - 0.2

    def test_fail_ease_factor_minimum(self):
        meta = {"interval_days": 1, "ease_factor": 1.3, "repetition_count": 0}
        new_meta, due = calculate_next_interval(meta, passed=False)

        # Should not go below 1.3
        assert new_meta["ease_factor"] == 1.3

    def test_high_score_increases_ease(self):
        meta = {"interval_days": 1, "ease_factor": 2.0, "repetition_count": 0}
        new_meta, due = calculate_next_interval(meta, passed=True, score=9.0)

        assert new_meta["ease_factor"] == 2.1  # 2.0 + 0.1

    def test_low_score_decreases_ease(self):
        meta = {"interval_days": 1, "ease_factor": 2.0, "repetition_count": 0}
        new_meta, due = calculate_next_interval(meta, passed=True, score=3.0)

        assert new_meta["ease_factor"] == 1.9  # 2.0 - 0.1

    def test_ease_factor_max(self):
        meta = {"interval_days": 1, "ease_factor": 2.5, "repetition_count": 0}
        new_meta, due = calculate_next_interval(meta, passed=True, score=10.0)

        # Should not exceed 2.5
        assert new_meta["ease_factor"] == 2.5


class TestCalculateDueDateFromDays:
    def test_days_from_now(self):
        due = calculate_due_date_from_days(7)
        expected = datetime.now() + timedelta(days=7)

        # Allow 1 second tolerance
        assert abs((due - expected).total_seconds()) < 1
