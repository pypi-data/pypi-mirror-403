"""Unit tests for kubepath.gamification.streaks module."""

from datetime import date, timedelta
from unittest.mock import patch

import pytest

from kubepath.gamification.streaks import (
    STREAK_MILESTONES,
    update_streak,
    check_streak_milestone,
    format_streak_display,
)


class TestStreakMilestones:
    """Test streak milestone constants."""

    def test_milestones_exist(self):
        """Should have defined milestones."""
        assert len(STREAK_MILESTONES) > 0

    def test_milestones_include_common_values(self):
        """Should include common milestone values."""
        assert 7 in STREAK_MILESTONES
        assert 14 in STREAK_MILESTONES
        assert 30 in STREAK_MILESTONES


class TestUpdateStreak:
    """Test update_streak function."""

    def test_first_time_user(self):
        """First time user should start with streak of 1."""
        result = update_streak(None)
        assert result["current"] == 1
        assert result["longest"] == 1
        assert result["maintained"] is True
        assert result["milestone"] is None

    @patch("kubepath.gamification.streaks.date")
    def test_same_day_activity(self, mock_date):
        """Same day activity should not increment streak."""
        today = date(2026, 1, 26)
        mock_date.today.return_value = today
        mock_date.fromisoformat = date.fromisoformat

        result = update_streak(
            last_active_date="2026-01-26",
            current_streak=5,
            longest_streak=10,
        )

        assert result["current"] == 5  # No change
        assert result["longest"] == 10
        assert result["maintained"] is True
        assert result["milestone"] is None

    @patch("kubepath.gamification.streaks.date")
    def test_yesterday_activity_continues_streak(self, mock_date):
        """Activity from yesterday should continue streak."""
        today = date(2026, 1, 26)
        mock_date.today.return_value = today
        mock_date.fromisoformat = date.fromisoformat

        result = update_streak(
            last_active_date="2026-01-25",
            current_streak=6,
            longest_streak=10,
        )

        assert result["current"] == 7
        assert result["longest"] == 10
        assert result["maintained"] is True
        assert result["milestone"] == 7  # Hit 7-day milestone

    @patch("kubepath.gamification.streaks.date")
    def test_gap_resets_streak(self, mock_date):
        """Gap of more than 1 day should reset streak."""
        today = date(2026, 1, 26)
        mock_date.today.return_value = today
        mock_date.fromisoformat = date.fromisoformat

        result = update_streak(
            last_active_date="2026-01-24",  # 2 days ago
            current_streak=10,
            longest_streak=15,
        )

        assert result["current"] == 1  # Reset to 1
        assert result["longest"] == 15  # Longest preserved
        assert result["maintained"] is False
        assert result["milestone"] is None

    @patch("kubepath.gamification.streaks.date")
    def test_new_longest_streak(self, mock_date):
        """New streak should update longest if higher."""
        today = date(2026, 1, 26)
        mock_date.today.return_value = today
        mock_date.fromisoformat = date.fromisoformat

        result = update_streak(
            last_active_date="2026-01-25",
            current_streak=14,
            longest_streak=14,
        )

        assert result["current"] == 15
        assert result["longest"] == 15  # Updated to new high
        assert result["maintained"] is True

    @patch("kubepath.gamification.streaks.date")
    def test_milestone_14_days(self, mock_date):
        """Should detect 14-day milestone."""
        today = date(2026, 1, 26)
        mock_date.today.return_value = today
        mock_date.fromisoformat = date.fromisoformat

        result = update_streak(
            last_active_date="2026-01-25",
            current_streak=13,
            longest_streak=13,
        )

        assert result["current"] == 14
        assert result["milestone"] == 14


class TestCheckStreakMilestone:
    """Test check_streak_milestone function."""

    def test_milestone_7(self):
        """7 days should be a milestone."""
        assert check_streak_milestone(7) == 7

    def test_milestone_14(self):
        """14 days should be a milestone."""
        assert check_streak_milestone(14) == 14

    def test_milestone_30(self):
        """30 days should be a milestone."""
        assert check_streak_milestone(30) == 30

    def test_non_milestone(self):
        """Non-milestone days should return None."""
        assert check_streak_milestone(5) is None
        assert check_streak_milestone(10) is None
        assert check_streak_milestone(15) is None


class TestFormatStreakDisplay:
    """Test format_streak_display function."""

    def test_no_streak(self):
        """Zero streak should show 'No streak'."""
        assert format_streak_display(0, 0) == "No streak"

    def test_one_day_streak(self):
        """1 day streak should be singular."""
        assert format_streak_display(1, 1) == "1-day streak"

    def test_multi_day_streak(self):
        """Multi-day streak should be plural."""
        assert format_streak_display(7, 10) == "7-day streak"
        assert format_streak_display(30, 30) == "30-day streak"

    def test_negative_streak(self):
        """Negative streak should show 'No streak'."""
        assert format_streak_display(-1, 5) == "No streak"
