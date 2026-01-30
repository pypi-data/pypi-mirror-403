"""Unit tests for kubepath.gamification.levels module."""

import pytest

from kubepath.gamification.levels import (
    LEVELS,
    MAX_LEVEL,
    get_level_for_score,
    get_next_level,
    get_progress_to_next_level,
    check_level_up,
)


class TestLevelsConstants:
    """Test level constants."""

    def test_levels_count(self):
        """Should have exactly 12 levels."""
        assert len(LEVELS) == 12

    def test_max_level(self):
        """Max level should be 12."""
        assert MAX_LEVEL == 12

    def test_levels_are_sorted(self):
        """Levels should be sorted by min_score."""
        scores = [level["min_score"] for level in LEVELS]
        assert scores == sorted(scores)

    def test_level_1_starts_at_zero(self):
        """Level 1 should start at score 0."""
        assert LEVELS[0]["min_score"] == 0
        assert LEVELS[0]["level"] == 1


class TestGetLevelForScore:
    """Test get_level_for_score function."""

    def test_score_zero_returns_level_1(self):
        """Score 0 should return level 1."""
        result = get_level_for_score(0)
        assert result["level"] == 1
        assert result["name"] == "Pod Seedling"

    def test_score_99_returns_level_1(self):
        """Score 99 (just below level 2) should return level 1."""
        result = get_level_for_score(99)
        assert result["level"] == 1

    def test_score_100_returns_level_2(self):
        """Score 100 (exactly level 2 threshold) should return level 2."""
        result = get_level_for_score(100)
        assert result["level"] == 2
        assert result["name"] == "Container Cadet"

    def test_score_1000_returns_level_5(self):
        """Score 1000 should return level 5."""
        result = get_level_for_score(1000)
        assert result["level"] == 5
        assert result["name"] == "Service Scout"

    def test_score_6600_returns_max_level(self):
        """Score 6600 (max level threshold) should return level 12."""
        result = get_level_for_score(6600)
        assert result["level"] == 12
        assert result["name"] == "Kubernetes Kurator"

    def test_very_high_score_returns_max_level(self):
        """Very high score should still return level 12."""
        result = get_level_for_score(99999)
        assert result["level"] == 12

    def test_negative_score_returns_level_1(self):
        """Negative score should return level 1."""
        result = get_level_for_score(-100)
        assert result["level"] == 1


class TestGetNextLevel:
    """Test get_next_level function."""

    def test_level_1_next_is_level_2(self):
        """Next level after 1 should be level 2."""
        result = get_next_level(1)
        assert result is not None
        assert result["level"] == 2
        assert result["name"] == "Container Cadet"

    def test_level_11_next_is_level_12(self):
        """Next level after 11 should be level 12."""
        result = get_next_level(11)
        assert result is not None
        assert result["level"] == 12

    def test_max_level_returns_none(self):
        """At max level (12), next should be None."""
        result = get_next_level(12)
        assert result is None

    def test_level_above_max_returns_none(self):
        """Level above max should return None."""
        result = get_next_level(15)
        assert result is None


class TestGetProgressToNextLevel:
    """Test get_progress_to_next_level function."""

    def test_score_0_progress(self):
        """Score 0 should show progress towards level 2."""
        current, needed = get_progress_to_next_level(0)
        assert current == 0
        assert needed == 100  # Level 2 threshold is 100

    def test_score_50_progress(self):
        """Score 50 should show 50/100 progress."""
        current, needed = get_progress_to_next_level(50)
        assert current == 50
        assert needed == 100

    def test_score_100_progress(self):
        """Score 100 (level 2) should show progress towards level 3."""
        current, needed = get_progress_to_next_level(100)
        assert current == 0  # Just reached level 2
        assert needed == 200  # Level 3 is at 300, so need 200 more

    def test_score_1100_progress(self):
        """Score 1100 (level 5) should show 100/500 progress."""
        current, needed = get_progress_to_next_level(1100)
        assert current == 100  # 1100 - 1000 = 100
        assert needed == 500  # 1500 - 1000 = 500

    def test_max_level_progress(self):
        """At max level, progress should be (0, 0)."""
        current, needed = get_progress_to_next_level(7000)
        assert current == 0
        assert needed == 0


class TestCheckLevelUp:
    """Test check_level_up function."""

    def test_no_level_up(self):
        """Same level should return None."""
        result = check_level_up(50, 60)
        assert result is None

    def test_level_up_1_to_2(self):
        """Going from 90 to 110 should trigger level up to 2."""
        result = check_level_up(90, 110)
        assert result is not None
        assert result["level"] == 2
        assert result["name"] == "Container Cadet"

    def test_level_up_multiple_levels(self):
        """Large score jump should return the correct new level."""
        result = check_level_up(50, 1100)  # Jump from level 1 to level 5
        assert result is not None
        assert result["level"] == 5
        assert result["name"] == "Service Scout"

    def test_exact_threshold(self):
        """Hitting exact threshold should trigger level up."""
        result = check_level_up(99, 100)
        assert result is not None
        assert result["level"] == 2

    def test_same_score(self):
        """Same score should return None."""
        result = check_level_up(500, 500)
        assert result is None
