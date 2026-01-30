"""Unit tests for hints module."""

import pytest

from kubepath.scenarios.hints import HintManager, HintResult


class TestHintResult:
    """Tests for HintResult dataclass."""

    def test_hint_result_creation(self):
        """Test creating a hint result."""
        result = HintResult(
            hint_text="Check the pod status",
            hint_number=1,
            total_hints=3,
            penalty_applied=5,
            has_more_hints=True,
        )
        assert result.hint_text == "Check the pod status"
        assert result.hint_number == 1
        assert result.total_hints == 3
        assert result.penalty_applied == 5
        assert result.has_more_hints is True


class TestHintManager:
    """Tests for HintManager class."""

    def test_get_next_hint(self):
        """Test getting the next hint."""
        manager = HintManager(
            hints=["Hint 1", "Hint 2", "Hint 3"],
            hint_penalty=5,
        )

        hint = manager.get_next_hint()
        assert hint is not None
        assert hint.hint_text == "Hint 1"
        assert hint.hint_number == 1
        assert hint.total_hints == 3
        assert hint.penalty_applied == 5
        assert hint.has_more_hints is True

    def test_hints_used_increments(self):
        """Test that hints_used increments."""
        manager = HintManager(hints=["Hint 1", "Hint 2"])

        assert manager.hints_used == 0
        manager.get_next_hint()
        assert manager.hints_used == 1
        manager.get_next_hint()
        assert manager.hints_used == 2

    def test_no_more_hints(self):
        """Test when no more hints available."""
        manager = HintManager(hints=["Hint 1"])

        manager.get_next_hint()
        hint = manager.get_next_hint()
        assert hint is None

    def test_hints_remaining(self):
        """Test hints_remaining property."""
        manager = HintManager(hints=["Hint 1", "Hint 2", "Hint 3"])

        assert manager.hints_remaining == 3
        manager.get_next_hint()
        assert manager.hints_remaining == 2
        manager.get_next_hint()
        assert manager.hints_remaining == 1
        manager.get_next_hint()
        assert manager.hints_remaining == 0

    def test_total_penalty(self):
        """Test total penalty calculation."""
        manager = HintManager(hints=["Hint 1", "Hint 2"], hint_penalty=5)

        assert manager.total_penalty == 0
        manager.get_next_hint()
        assert manager.total_penalty == 5
        manager.get_next_hint()
        assert manager.total_penalty == 10

    def test_calculate_final_score(self):
        """Test final score calculation."""
        manager = HintManager(hints=["Hint 1", "Hint 2"], hint_penalty=5)

        # No hints used
        assert manager.calculate_final_score(25) == 25

        # One hint used
        manager.get_next_hint()
        assert manager.calculate_final_score(25) == 20

        # Two hints used
        manager.get_next_hint()
        assert manager.calculate_final_score(25) == 15

    def test_score_minimum_is_zero(self):
        """Test that score doesn't go below zero."""
        manager = HintManager(hints=["H1", "H2", "H3", "H4"], hint_penalty=10)

        # Use all hints (40 points penalty)
        for _ in range(4):
            manager.get_next_hint()

        assert manager.calculate_final_score(25) == 0

    def test_peek_next_hint(self):
        """Test peeking at next hint."""
        manager = HintManager(hints=["Hint 1", "Hint 2"])

        # Peek doesn't increment usage
        assert manager.peek_next_hint() == "Hint 1"
        assert manager.hints_used == 0
        assert manager.peek_next_hint() == "Hint 1"
        assert manager.hints_used == 0

    def test_peek_when_no_hints_left(self):
        """Test peeking when no hints left."""
        manager = HintManager(hints=["Hint 1"])
        manager.get_next_hint()

        assert manager.peek_next_hint() is None

    def test_reset(self):
        """Test resetting hint usage."""
        manager = HintManager(hints=["Hint 1", "Hint 2"], hint_penalty=5)

        manager.get_next_hint()
        manager.get_next_hint()
        assert manager.hints_used == 2
        assert manager.total_penalty == 10

        manager.reset()
        assert manager.hints_used == 0
        assert manager.total_penalty == 0
        assert manager.hints_remaining == 2

    def test_ai_hint_penalty(self):
        """Test AI hint penalty is separate."""
        manager = HintManager(
            hints=["Hint 1"],
            hint_penalty=5,
            ai_hint_penalty=2,
        )

        # Record AI hint
        penalty = manager.record_ai_hint()
        assert penalty == 2
        assert manager.ai_hints_used == 1

        # Total penalty includes both
        assert manager.total_penalty == 2

        # Use static hint
        manager.get_next_hint()
        assert manager.total_penalty == 7  # 2 + 5

    def test_get_summary(self):
        """Test getting hint usage summary."""
        manager = HintManager(hints=["H1", "H2", "H3"], hint_penalty=5, ai_hint_penalty=2)

        manager.get_next_hint()
        manager.record_ai_hint()

        summary = manager.get_summary()
        assert summary["static_hints_used"] == 1
        assert summary["static_hints_total"] == 3
        assert summary["ai_hints_used"] == 1
        assert summary["total_penalty"] == 7

    def test_empty_hints_list(self):
        """Test with empty hints list."""
        manager = HintManager(hints=[])

        assert manager.get_next_hint() is None
        assert manager.hints_remaining == 0
        assert manager.calculate_final_score(25) == 25
