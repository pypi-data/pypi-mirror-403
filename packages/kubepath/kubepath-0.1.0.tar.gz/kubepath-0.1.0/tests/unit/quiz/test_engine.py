"""Tests for quiz engine."""

import pytest
from unittest.mock import patch, MagicMock

from kubepath.quiz.engine import QuizEngine, QuizResult


@pytest.fixture
def sample_quiz_data():
    """Sample quiz data for testing."""
    return {
        "passing_score": 70,
        "questions": [
            {
                "type": "multiple_choice",
                "question": "What is a Pod?",
                "options": [
                    "A single container",
                    "The smallest deployable unit",
                    "A node",
                    "A namespace",
                ],
                "correct": 1,
                "explanation": "A Pod is the smallest deployable unit in K8s.",
                "points": 5,
            },
            {
                "type": "true_false",
                "question": "Pods can contain multiple containers.",
                "correct": True,
                "explanation": "Yes, pods can have multiple containers.",
                "points": 5,
            },
            {
                "type": "command_challenge",
                "question": "List all pods in the cluster.",
                "expected_contains": "kubectl get pods",
                "alternatives": ["kubectl get po", "kubectl get pods -A"],
                "hint": "Use kubectl get",
                "explanation": "kubectl get pods lists all pods.",
                "points": 10,
            },
            {
                "type": "fill_yaml",
                "question": "What status shows a healthy node?",
                "yaml_template": "STATUS: ____",
                "expected": "Ready",
                "explanation": "Ready indicates a healthy node.",
                "points": 10,
            },
        ],
    }


class TestQuizEngineInit:
    """Tests for QuizEngine initialization."""

    def test_init_basic(self, sample_quiz_data):
        """Test basic initialization."""
        engine = QuizEngine(chapter=1, quiz_data=sample_quiz_data)

        assert engine.chapter == 1
        assert len(engine.original_questions) == 4
        assert engine.passing_score == 70
        assert engine.current_index == 0
        assert engine.total_points == 0
        assert engine.hints_used == 0

    def test_init_empty_quiz(self):
        """Test initialization with empty quiz data."""
        engine = QuizEngine(chapter=1, quiz_data={})

        assert len(engine.original_questions) == 0
        assert engine.passing_score == 70  # Default

    def test_init_custom_passing_score(self):
        """Test initialization with custom passing score."""
        quiz_data = {"passing_score": 80, "questions": []}
        engine = QuizEngine(chapter=1, quiz_data=quiz_data)

        assert engine.passing_score == 80


class TestPrepareQuestions:
    """Tests for prepare_questions method."""

    def test_prepare_without_error_bank(self, sample_quiz_data):
        """Test prepare questions without error bank."""
        with patch("kubepath.quiz.engine.get_error_bank_questions", return_value=[]):
            engine = QuizEngine(chapter=1, quiz_data=sample_quiz_data)
            engine.prepare_questions(error_bank_percent=20)

            assert len(engine.questions) == 4
            assert engine.max_points == 30  # 5 + 5 + 10 + 10

    def test_prepare_with_error_bank(self, sample_quiz_data):
        """Test prepare questions with error bank questions."""
        error_question = {
            "type": "multiple_choice",
            "question": "Error bank question",
            "options": ["A", "B", "C", "D"],
            "correct": 0,
            "points": 5,
        }

        with patch(
            "kubepath.quiz.engine.get_error_bank_questions",
            return_value=[error_question],
        ):
            engine = QuizEngine(chapter=1, quiz_data=sample_quiz_data)
            engine.prepare_questions(error_bank_percent=20)

            # Should have replaced 1 question (20% of 4 = ~1)
            assert len(engine.questions) == 4
            # At least one question should be from error bank
            assert len(engine._error_bank_indices) >= 1


class TestMultipleChoice:
    """Tests for multiple choice validation."""

    def test_correct_answer(self, sample_quiz_data):
        """Test correct multiple choice answer."""
        engine = QuizEngine(chapter=1, quiz_data=sample_quiz_data)
        engine.prepare_questions(error_bank_percent=0)

        result = engine.check_answer("B")  # correct is index 1

        assert result.correct is True
        assert result.points_earned == 5
        assert engine.total_points == 5

    def test_wrong_answer(self, sample_quiz_data):
        """Test wrong multiple choice answer."""
        engine = QuizEngine(chapter=1, quiz_data=sample_quiz_data)
        engine.prepare_questions(error_bank_percent=0)

        result = engine.check_answer("A")  # Wrong

        assert result.correct is False
        assert result.points_earned == 0
        assert engine.total_points == 0

    def test_case_insensitive(self, sample_quiz_data):
        """Test case insensitive answer."""
        engine = QuizEngine(chapter=1, quiz_data=sample_quiz_data)
        engine.prepare_questions(error_bank_percent=0)

        result = engine.check_answer("b")  # Lowercase

        assert result.correct is True

    def test_invalid_letter(self, sample_quiz_data):
        """Test invalid answer letter."""
        engine = QuizEngine(chapter=1, quiz_data=sample_quiz_data)
        engine.prepare_questions(error_bank_percent=0)

        result = engine.check_answer("E")  # Invalid

        assert result.correct is False


class TestTrueFalse:
    """Tests for true/false validation."""

    def test_true_answer_correct(self, sample_quiz_data):
        """Test correct true answer."""
        engine = QuizEngine(chapter=1, quiz_data=sample_quiz_data)
        engine.prepare_questions(error_bank_percent=0)
        engine.current_index = 1  # True/false question

        # Test various true formats
        for answer in ["A", "a", "True", "true", "T", "t", "Yes", "yes", "Y", "y"]:
            engine.answers = {}  # Reset
            engine.total_points = 0
            result = engine.check_answer(answer)
            assert result.correct is True, f"Failed for answer: {answer}"

    def test_false_answer(self, sample_quiz_data):
        """Test false answer."""
        engine = QuizEngine(chapter=1, quiz_data=sample_quiz_data)
        engine.prepare_questions(error_bank_percent=0)
        engine.current_index = 1  # True/false question (correct is True)

        # False answers should be wrong
        for answer in ["B", "b", "False", "false", "F", "f", "No", "no", "N", "n"]:
            engine.answers = {}
            engine.total_points = 0
            result = engine.check_answer(answer)
            assert result.correct is False, f"Should be wrong for: {answer}"


class TestCommandChallenge:
    """Tests for command challenge validation."""

    def test_exact_match(self, sample_quiz_data):
        """Test exact command match."""
        engine = QuizEngine(chapter=1, quiz_data=sample_quiz_data)
        engine.prepare_questions(error_bank_percent=0)
        engine.current_index = 2  # Command challenge

        result = engine.check_answer("kubectl get pods")

        assert result.correct is True
        assert result.points_earned == 10

    def test_partial_match(self, sample_quiz_data):
        """Test command with additional flags."""
        engine = QuizEngine(chapter=1, quiz_data=sample_quiz_data)
        engine.prepare_questions(error_bank_percent=0)
        engine.current_index = 2

        result = engine.check_answer("kubectl get pods -n default")

        assert result.correct is True  # Contains expected

    def test_alternative_match(self, sample_quiz_data):
        """Test alternative command."""
        engine = QuizEngine(chapter=1, quiz_data=sample_quiz_data)
        engine.prepare_questions(error_bank_percent=0)
        engine.current_index = 2

        result = engine.check_answer("kubectl get po")

        assert result.correct is True  # Matches alternative

    def test_wrong_command(self, sample_quiz_data):
        """Test wrong command."""
        engine = QuizEngine(chapter=1, quiz_data=sample_quiz_data)
        engine.prepare_questions(error_bank_percent=0)
        engine.current_index = 2

        result = engine.check_answer("kubectl describe pods")

        assert result.correct is False


class TestFillYaml:
    """Tests for fill YAML validation."""

    def test_exact_match(self, sample_quiz_data):
        """Test exact value match."""
        engine = QuizEngine(chapter=1, quiz_data=sample_quiz_data)
        engine.prepare_questions(error_bank_percent=0)
        engine.current_index = 3  # Fill YAML question

        result = engine.check_answer("Ready")

        assert result.correct is True
        assert result.points_earned == 10

    def test_case_insensitive(self, sample_quiz_data):
        """Test case insensitive match."""
        engine = QuizEngine(chapter=1, quiz_data=sample_quiz_data)
        engine.prepare_questions(error_bank_percent=0)
        engine.current_index = 3

        result = engine.check_answer("ready")

        assert result.correct is True

    def test_with_whitespace(self, sample_quiz_data):
        """Test with leading/trailing whitespace."""
        engine = QuizEngine(chapter=1, quiz_data=sample_quiz_data)
        engine.prepare_questions(error_bank_percent=0)
        engine.current_index = 3

        result = engine.check_answer("  Ready  ")

        assert result.correct is True

    def test_wrong_value(self, sample_quiz_data):
        """Test wrong value."""
        engine = QuizEngine(chapter=1, quiz_data=sample_quiz_data)
        engine.prepare_questions(error_bank_percent=0)
        engine.current_index = 3

        result = engine.check_answer("NotReady")

        assert result.correct is False


class TestSkipQuestion:
    """Tests for skip_question method."""

    def test_skip_advances_index(self, sample_quiz_data):
        """Test that skip advances to next question."""
        with patch("kubepath.quiz.engine.save_to_error_bank"):
            engine = QuizEngine(chapter=1, quiz_data=sample_quiz_data)
            engine.prepare_questions(error_bank_percent=0)

            assert engine.current_index == 0
            engine.skip_question()
            assert engine.current_index == 1

    def test_skip_awards_zero_points(self, sample_quiz_data):
        """Test that skip gives 0 points."""
        with patch("kubepath.quiz.engine.save_to_error_bank"):
            engine = QuizEngine(chapter=1, quiz_data=sample_quiz_data)
            engine.prepare_questions(error_bank_percent=0)

            engine.skip_question()

            assert engine.total_points == 0
            assert 0 in engine.answers
            assert engine.answers[0]["correct"] is False

    def test_skip_saves_to_error_bank(self, sample_quiz_data):
        """Test that skip saves question to error bank."""
        with patch("kubepath.quiz.engine.save_to_error_bank") as mock_save:
            engine = QuizEngine(chapter=1, quiz_data=sample_quiz_data)
            engine.prepare_questions(error_bank_percent=0)

            engine.skip_question()

            mock_save.assert_called_once()
            call_args = mock_save.call_args
            assert call_args[1]["chapter"] == 1
            assert call_args[1]["user_answer"] == "skipped"


class TestQuizCompletion:
    """Tests for quiz completion."""

    def test_is_complete_false(self, sample_quiz_data):
        """Test is_complete returns False when questions remain."""
        engine = QuizEngine(chapter=1, quiz_data=sample_quiz_data)
        engine.prepare_questions(error_bank_percent=0)

        assert engine.is_complete() is False

    def test_is_complete_true(self, sample_quiz_data):
        """Test is_complete returns True when all answered."""
        engine = QuizEngine(chapter=1, quiz_data=sample_quiz_data)
        engine.prepare_questions(error_bank_percent=0)
        engine.current_index = 4  # Past all questions

        assert engine.is_complete() is True

    def test_get_summary(self, sample_quiz_data):
        """Test get_summary returns correct stats."""
        engine = QuizEngine(chapter=1, quiz_data=sample_quiz_data)
        engine.prepare_questions(error_bank_percent=0)

        # Answer 2 questions correctly
        engine.check_answer("B")  # Correct (5 pts)
        engine.advance()
        engine.check_answer("A")  # Correct (5 pts)
        engine.advance()
        engine.current_index = 4  # Complete

        summary = engine.get_summary()

        assert summary["score"] == 10
        assert summary["max_score"] == 30
        assert summary["correct"] == 2
        assert summary["total"] == 4
        assert summary["percentage"] == 33  # 10/30 = 33%
        assert summary["passed"] is False  # < 70%


class TestAIHints:
    """Tests for AI hint functionality."""

    def test_hint_without_gemini(self, sample_quiz_data):
        """Test AI hint when gemini not available."""
        engine = QuizEngine(chapter=1, quiz_data=sample_quiz_data)
        engine.prepare_questions(error_bank_percent=0)

        hint = engine.get_ai_hint()

        assert hint is None
        # Points should not be deducted when no gemini client
        assert engine.total_points == 0
        # hints_used should NOT increment since no hint was given
        assert engine.hints_used == 0

    def test_hint_deducts_points(self, sample_quiz_data):
        """Test AI hint deducts points only on success."""
        mock_gemini = MagicMock()
        mock_gemini.answer_question.return_value = "Try thinking about what kubectl get does."

        engine = QuizEngine(chapter=1, quiz_data=sample_quiz_data, gemini_client=mock_gemini)
        engine.prepare_questions(error_bank_percent=0)
        engine.total_points = 10  # Start with some points

        hint = engine.get_ai_hint()

        assert hint is not None
        assert engine.total_points == 8  # 10 - 2 penalty
        assert engine.hints_used == 1
        # Verify answer_question was called with correct params
        mock_gemini.answer_question.assert_called_once()

    def test_hint_failure_no_point_deduction(self, sample_quiz_data):
        """Test that points are NOT deducted when AI hint fails."""
        mock_gemini = MagicMock()
        mock_gemini.answer_question.return_value = None  # AI fails to respond

        engine = QuizEngine(chapter=1, quiz_data=sample_quiz_data, gemini_client=mock_gemini)
        engine.prepare_questions(error_bank_percent=0)
        engine.total_points = 10  # Start with some points

        hint = engine.get_ai_hint()

        assert hint is None
        # Points should NOT be deducted on failure
        assert engine.total_points == 10
        # hints_used should NOT increment on failure
        assert engine.hints_used == 0


class TestStatePersistence:
    """Tests for state save/restore."""

    def test_get_state_for_persistence(self, sample_quiz_data):
        """Test getting state for saving."""
        engine = QuizEngine(chapter=1, quiz_data=sample_quiz_data)
        engine.prepare_questions(error_bank_percent=0)
        engine.check_answer("B")  # Correct
        engine.advance()
        engine.hints_used = 2

        state = engine.get_state_for_persistence()

        assert state["current_index"] == 1
        assert state["total_points"] == 5
        assert state["hints_used"] == 2
        assert 0 in state["answers"]

    def test_restore_state(self, sample_quiz_data):
        """Test restoring from saved state."""
        engine = QuizEngine(chapter=1, quiz_data=sample_quiz_data)
        engine.prepare_questions(error_bank_percent=0)

        saved_state = {
            "current_index": 2,
            "answers": {0: {"answer": "B", "correct": True, "points": 5}},
            "total_points": 15,
            "hints_used": 1,
        }

        engine.restore_state(saved_state)

        assert engine.current_index == 2
        assert engine.total_points == 15
        assert engine.hints_used == 1
        assert 0 in engine.answers


class TestUnlimitedRetries:
    """Tests for unlimited retry functionality."""

    def test_retry_no_point_penalty(self, sample_quiz_data):
        """Test that retrying doesn't deduct points."""
        engine = QuizEngine(chapter=1, quiz_data=sample_quiz_data)
        engine.prepare_questions(error_bank_percent=0)

        # Wrong answer
        result1 = engine.check_answer("A")
        assert result1.correct is False
        assert engine.total_points == 0

        # Retry with correct answer
        result2 = engine.check_answer("B")
        assert result2.correct is True
        assert engine.total_points == 5  # Full points

    def test_multiple_retries_full_points(self, sample_quiz_data):
        """Test multiple retries still give full points."""
        engine = QuizEngine(chapter=1, quiz_data=sample_quiz_data)
        engine.prepare_questions(error_bank_percent=0)

        # Multiple wrong answers
        engine.check_answer("A")
        engine.check_answer("C")
        engine.check_answer("D")

        # Finally correct
        result = engine.check_answer("B")
        assert result.correct is True
        assert engine.total_points == 5  # Still full points
