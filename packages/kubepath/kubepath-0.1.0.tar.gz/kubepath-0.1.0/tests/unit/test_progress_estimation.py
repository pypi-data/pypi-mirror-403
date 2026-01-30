"""Tests for progress calculation and time estimation."""

import pytest
from unittest.mock import patch, MagicMock

from kubepath.utils.progress import (
    get_course_progress,
    get_chapter_progress,
    estimate_chapter_time,
    estimate_course_time_remaining,
    estimate_chapter_time_remaining,
    TIME_PER_CONCEPT,
    TIME_PER_PRACTICE,
    TIME_PER_SCENARIO,
    TIME_PER_QUIZ_QUESTION,
)
from kubepath.content.loader import (
    get_chapter_content_counts,
    get_all_chapter_content_counts,
)
from kubepath.content.renderer import format_time_remaining


class TestGetCourseProgress:
    """Tests for get_course_progress function."""

    def test_no_progress(self):
        """Test with no progress data."""
        with patch("kubepath.utils.progress.load_progress", return_value={"chapters": {}}):
            result = get_course_progress(10)

            assert result["completed_chapters"] == 0
            assert result["total_chapters"] == 10
            assert result["percentage"] == 0
            assert result["current_chapter"] is None
            assert result["current_section"] is None

    def test_some_chapters_completed(self):
        """Test with some chapters completed."""
        progress = {
            "active_chapter": 3,
            "active_section": "practice",
            "chapters": {
                "1": {"section": "completed"},
                "2": {"section": "completed"},
                "3": {"section": "practice"},
            },
        }
        with patch("kubepath.utils.progress.load_progress", return_value=progress):
            result = get_course_progress(10)

            assert result["completed_chapters"] == 2
            assert result["total_chapters"] == 10
            assert result["percentage"] == 20
            assert result["current_chapter"] == 3
            assert result["current_section"] == "practice"

    def test_all_chapters_completed(self):
        """Test with all chapters completed."""
        progress = {
            "chapters": {
                "1": {"section": "completed"},
                "2": {"section": "completed"},
                "3": {"section": "completed"},
            },
        }
        with patch("kubepath.utils.progress.load_progress", return_value=progress):
            result = get_course_progress(3)

            assert result["completed_chapters"] == 3
            assert result["percentage"] == 100

    def test_zero_total_chapters(self):
        """Test with zero total chapters."""
        with patch("kubepath.utils.progress.load_progress", return_value={"chapters": {}}):
            result = get_course_progress(0)

            assert result["percentage"] == 0


class TestGetChapterProgress:
    """Tests for get_chapter_progress function."""

    def test_no_progress(self):
        """Test with no chapter progress."""
        with patch("kubepath.utils.progress.load_progress", return_value={"chapters": {}}):
            result = get_chapter_progress(1)

            assert result["completed_sections"] == 0
            assert result["total_sections"] == 4
            assert result["current_section"] == "concepts"
            assert result["percentage"] == 0

    def test_concepts_completed(self):
        """Test with concepts section completed."""
        progress = {
            "chapters": {
                "1": {
                    "section": "practice",
                    "concepts_completed": True,
                },
            },
        }
        with patch("kubepath.utils.progress.load_progress", return_value=progress):
            result = get_chapter_progress(1)

            assert result["completed_sections"] == 1
            assert result["current_section"] == "practice"
            assert result["percentage"] == 20  # 0.20 * 100

    def test_practice_completed(self):
        """Test with concepts and practice completed."""
        progress = {
            "chapters": {
                "1": {
                    "section": "scenarios",
                    "concepts_completed": True,
                    "practice_completed": True,
                },
            },
        }
        with patch("kubepath.utils.progress.load_progress", return_value=progress):
            result = get_chapter_progress(1)

            assert result["completed_sections"] == 2
            assert result["current_section"] == "scenarios"
            assert result["percentage"] == 45  # (0.20 + 0.25) * 100

    def test_all_completed(self):
        """Test with all sections completed."""
        progress = {
            "chapters": {
                "1": {
                    "section": "completed",
                    "concepts_completed": True,
                    "practice_completed": True,
                    "scenarios_completed": True,
                    "quiz_completed": True,
                },
            },
        }
        with patch("kubepath.utils.progress.load_progress", return_value=progress):
            result = get_chapter_progress(1)

            assert result["completed_sections"] == 4
            assert result["percentage"] == 100


class TestEstimateChapterTime:
    """Tests for estimate_chapter_time function."""

    def test_empty_chapter(self):
        """Test with empty chapter."""
        counts = {
            "concepts": 0,
            "practices": 0,
            "scenarios": 0,
            "quiz_questions": 0,
        }
        result = estimate_chapter_time(counts)
        assert result == 0

    def test_typical_chapter(self):
        """Test with typical chapter content."""
        counts = {
            "concepts": 3,
            "practices": 3,
            "scenarios": 2,
            "quiz_questions": 6,
        }
        expected = (
            3 * TIME_PER_CONCEPT +
            3 * TIME_PER_PRACTICE +
            2 * TIME_PER_SCENARIO +
            6 * TIME_PER_QUIZ_QUESTION
        )
        result = estimate_chapter_time(counts)
        assert result == int(expected)


class TestEstimateChapterTimeRemaining:
    """Tests for estimate_chapter_time_remaining function."""

    def test_at_concepts(self):
        """Test time remaining when at concepts section."""
        counts = {
            "concepts": 4,
            "practices": 3,
            "scenarios": 2,
            "quiz_questions": 6,
        }
        with patch("kubepath.utils.progress.load_progress", return_value={"chapters": {}}):
            result = estimate_chapter_time_remaining(1, counts, "concepts")

            # 50% of concepts + full practice + full scenarios + full quiz
            expected = (
                int(4 * TIME_PER_CONCEPT * 0.5) +
                int(3 * TIME_PER_PRACTICE) +
                int(2 * TIME_PER_SCENARIO) +
                int(6 * TIME_PER_QUIZ_QUESTION)
            )
            assert result == expected

    def test_at_practice(self):
        """Test time remaining when at practice section."""
        counts = {
            "concepts": 4,
            "practices": 3,
            "scenarios": 2,
            "quiz_questions": 6,
        }
        with patch("kubepath.utils.progress.load_progress", return_value={"chapters": {}}):
            result = estimate_chapter_time_remaining(1, counts, "practice")

            # 50% of practice + full scenarios + full quiz
            expected = (
                int(3 * TIME_PER_PRACTICE * 0.5) +
                int(2 * TIME_PER_SCENARIO) +
                int(6 * TIME_PER_QUIZ_QUESTION)
            )
            assert result == expected

    def test_at_scenarios(self):
        """Test time remaining when at scenarios section."""
        counts = {
            "concepts": 4,
            "practices": 3,
            "scenarios": 2,
            "quiz_questions": 6,
        }
        with patch("kubepath.utils.progress.load_progress", return_value={"chapters": {}}):
            result = estimate_chapter_time_remaining(1, counts, "scenarios")

            # 50% of scenarios + full quiz
            expected = (
                int(2 * TIME_PER_SCENARIO * 0.5) +
                int(6 * TIME_PER_QUIZ_QUESTION)
            )
            assert result == expected

    def test_at_quiz(self):
        """Test time remaining when at quiz section."""
        counts = {
            "concepts": 4,
            "practices": 3,
            "scenarios": 2,
            "quiz_questions": 6,
        }
        with patch("kubepath.utils.progress.load_progress", return_value={"chapters": {}}):
            result = estimate_chapter_time_remaining(1, counts, "quiz")

            # 50% of quiz
            expected = int(6 * TIME_PER_QUIZ_QUESTION * 0.5)
            assert result == expected

    def test_at_completed(self):
        """Test time remaining when chapter is completed."""
        counts = {
            "concepts": 4,
            "practices": 3,
            "scenarios": 2,
            "quiz_questions": 6,
        }
        with patch("kubepath.utils.progress.load_progress", return_value={"chapters": {}}):
            result = estimate_chapter_time_remaining(1, counts, "completed")
            assert result == 0


class TestEstimateCourseTimeRemaining:
    """Tests for estimate_course_time_remaining function."""

    def test_no_progress(self):
        """Test with no progress."""
        chapters_content = {
            1: {"concepts": 3, "practices": 3, "scenarios": 2, "quiz_questions": 6},
            2: {"concepts": 3, "practices": 3, "scenarios": 2, "quiz_questions": 6},
        }
        with patch("kubepath.utils.progress.load_progress", return_value={"chapters": {}}):
            result = estimate_course_time_remaining(chapters_content)

            # Both chapters should be counted
            assert result > 0

    def test_some_chapters_completed(self):
        """Test with some chapters completed."""
        chapters_content = {
            1: {"concepts": 3, "practices": 3, "scenarios": 2, "quiz_questions": 6},
            2: {"concepts": 3, "practices": 3, "scenarios": 2, "quiz_questions": 6},
        }
        progress = {
            "chapters": {
                "1": {"section": "completed"},
            },
        }
        with patch("kubepath.utils.progress.load_progress", return_value=progress):
            result = estimate_course_time_remaining(chapters_content)

            # Only chapter 2 should be counted
            # At concepts section (default)
            expected = estimate_chapter_time_remaining(2, chapters_content[2], "concepts")
            assert result == expected

    def test_all_chapters_completed(self):
        """Test with all chapters completed."""
        chapters_content = {
            1: {"concepts": 3, "practices": 3, "scenarios": 2, "quiz_questions": 6},
        }
        progress = {
            "chapters": {
                "1": {"section": "completed"},
            },
        }
        with patch("kubepath.utils.progress.load_progress", return_value=progress):
            result = estimate_course_time_remaining(chapters_content)
            assert result == 0


class TestFormatTimeRemaining:
    """Tests for format_time_remaining function."""

    def test_zero_minutes(self):
        """Test with zero minutes."""
        assert format_time_remaining(0) == "Complete"

    def test_negative_minutes(self):
        """Test with negative minutes."""
        assert format_time_remaining(-5) == "Complete"

    def test_small_minutes(self):
        """Test with small number of minutes."""
        assert format_time_remaining(5) == "~5 min"
        assert format_time_remaining(30) == "~30 min"
        assert format_time_remaining(59) == "~59 min"

    def test_one_hour(self):
        """Test with around one hour."""
        assert format_time_remaining(60) == "~1.0 hours"
        assert format_time_remaining(90) == "~1.5 hours"
        assert format_time_remaining(119) == "~2.0 hours"

    def test_multiple_hours(self):
        """Test with multiple hours."""
        assert format_time_remaining(120) == "~2 hours"
        assert format_time_remaining(180) == "~3 hours"
        assert format_time_remaining(600) == "~10 hours"


class TestGetChapterContentCounts:
    """Tests for get_chapter_content_counts function."""

    def test_chapter_not_found(self):
        """Test with non-existent chapter."""
        from kubepath.content.loader import ChapterNotFoundError

        with patch(
            "kubepath.content.loader.load_chapter",
            side_effect=ChapterNotFoundError("Not found"),
        ):
            result = get_chapter_content_counts(999)

            assert result["concepts"] == 0
            assert result["practices"] == 0
            assert result["scenarios"] == 0
            assert result["quiz_questions"] == 0

    def test_chapter_with_content(self):
        """Test with chapter that has content."""
        chapter_data = {
            "chapter": {"number": 1, "title": "Test"},
            "concepts": [{"title": "C1"}, {"title": "C2"}],
            "command_practice": [{"id": "p1"}],
            "scenarios": [{"id": "s1"}, {"id": "s2"}, {"id": "s3"}],
            "quiz": {"questions": [{"type": "mc"}, {"type": "mc"}]},
        }
        with patch("kubepath.content.loader.load_chapter", return_value=chapter_data):
            result = get_chapter_content_counts(1)

            assert result["concepts"] == 2
            assert result["practices"] == 1
            assert result["scenarios"] == 3
            assert result["quiz_questions"] == 2

    def test_chapter_with_no_optional_sections(self):
        """Test with chapter that has no optional sections."""
        chapter_data = {
            "chapter": {"number": 1, "title": "Test"},
            "concepts": [{"title": "C1"}],
        }
        with patch("kubepath.content.loader.load_chapter", return_value=chapter_data):
            result = get_chapter_content_counts(1)

            assert result["concepts"] == 1
            assert result["practices"] == 0
            assert result["scenarios"] == 0
            assert result["quiz_questions"] == 0


class TestGetAllChapterContentCounts:
    """Tests for get_all_chapter_content_counts function."""

    def test_caching(self):
        """Test that results are cached."""
        # Reset cache
        import kubepath.content.loader as loader_module
        loader_module._chapter_content_cache = None

        chapter_data = {
            "chapter": {"number": 1, "title": "Test"},
            "concepts": [{"title": "C1"}],
        }

        with patch(
            "kubepath.content.loader.get_available_chapters",
            return_value=[1],
        ):
            with patch(
                "kubepath.content.loader.load_chapter",
                return_value=chapter_data,
            ) as mock_load:
                # First call
                result1 = get_all_chapter_content_counts()
                # Second call should use cache
                result2 = get_all_chapter_content_counts()

                # load_chapter should only be called once
                assert mock_load.call_count == 1
                assert result1 == result2

        # Clean up cache for other tests
        loader_module._chapter_content_cache = None
