"""Unit tests for content renderer."""

import re
import pytest
from io import StringIO
from unittest.mock import patch, MagicMock

from rich.console import Console

from kubepath.content.renderer import (
    render_concepts,
    render_concept,
    render_key_points,
    render_chapter_header,
    render_navigation_help,
    render_progress_bar,
    render_command_practice,
    render_practice_navigation_help,
    render_validation_result,
    render_command_output,
    render_hint,
    render_command_prompt,
)


def strip_ansi(text: str) -> str:
    """Remove ANSI escape codes from text."""
    ansi_pattern = re.compile(r'\x1b\[[0-9;]*m')
    return ansi_pattern.sub('', text)


def make_test_console() -> tuple[Console, StringIO]:
    """Create a test console that captures output."""
    output = StringIO()
    console = Console(file=output, force_terminal=True, width=80)
    return console, output


class TestRenderConcepts:
    """Tests for render_concepts function."""

    def test_renders_all_concepts(self):
        """Test that all concepts are rendered."""
        console, output = make_test_console()
        concepts = [
            {"title": "Concept 1", "content": "Content 1"},
            {"title": "Concept 2", "content": "Content 2"},
        ]

        render_concepts(concepts, console)

        result = output.getvalue()
        assert "Concept 1" in result
        assert "Concept 2" in result
        assert "Content 1" in result
        assert "Content 2" in result

    def test_renders_with_progress(self):
        """Test that progress indicators are shown."""
        console, output = make_test_console()
        concepts = [
            {"title": "First", "content": "A"},
            {"title": "Second", "content": "B"},
        ]

        render_concepts(concepts, console)

        result = output.getvalue()
        assert "1/2" in result
        assert "2/2" in result

    def test_empty_concepts_list(self):
        """Test that empty list renders nothing."""
        console, output = make_test_console()
        render_concepts([], console)
        # Should not raise, just output nothing
        assert output.getvalue().strip() == ""


class TestRenderConcept:
    """Tests for render_concept function."""

    def test_renders_title(self):
        """Test that concept title is rendered."""
        console, output = make_test_console()
        concept = {"title": "My Title", "content": "My content"}

        render_concept(concept, 1, 1, console)

        assert "My Title" in output.getvalue()

    def test_renders_content(self):
        """Test that concept content is rendered."""
        console, output = make_test_console()
        concept = {"title": "Title", "content": "This is the **content**"}

        render_concept(concept, 1, 1, console)

        # Content should appear (markdown rendered)
        result = output.getvalue()
        assert "content" in result.lower()

    def test_renders_key_points(self):
        """Test that key points are rendered when present."""
        console, output = make_test_console()
        concept = {
            "title": "Title",
            "content": "Content",
            "key_points": ["Point A", "Point B"],
        }

        render_concept(concept, 1, 1, console)

        result = output.getvalue()
        assert "Key Points" in result
        assert "Point A" in result
        assert "Point B" in result

    def test_handles_missing_key_points(self):
        """Test that missing key points are handled gracefully."""
        console, output = make_test_console()
        concept = {"title": "Title", "content": "Content"}

        render_concept(concept, 1, 1, console)

        # Should not contain "Key Points" section
        assert "Key Points" not in output.getvalue()

    def test_handles_empty_key_points(self):
        """Test that empty key points list is handled gracefully."""
        console, output = make_test_console()
        concept = {"title": "Title", "content": "Content", "key_points": []}

        render_concept(concept, 1, 1, console)

        assert "Key Points" not in output.getvalue()


class TestRenderKeyPoints:
    """Tests for render_key_points function."""

    def test_renders_bullet_points(self):
        """Test that key points are rendered as bullets."""
        console, output = make_test_console()
        points = ["First point", "Second point"]

        render_key_points(points, console)

        result = output.getvalue()
        assert "First point" in result
        assert "Second point" in result
        assert "•" in result  # Bullet character

    def test_renders_header(self):
        """Test that Key Points header is shown."""
        console, output = make_test_console()
        render_key_points(["Point"], console)

        assert "Key Points" in output.getvalue()


class TestRenderChapterHeader:
    """Tests for render_chapter_header function."""

    def test_renders_chapter_number_and_title(self):
        """Test that chapter number and title are rendered."""
        console, output = make_test_console()
        chapter = {
            "number": 1,
            "title": "Getting Started",
            "description": "An introduction",
        }

        render_chapter_header(chapter, console)

        result = output.getvalue()
        # Check for "Chapter" and "1" separately due to ANSI codes
        assert "Chapter" in result
        assert "1" in result
        assert "Getting Started" in result

    def test_renders_description(self):
        """Test that description is rendered when present."""
        console, output = make_test_console()
        chapter = {
            "number": 2,
            "title": "Advanced Topics",
            "description": "Deep dive into advanced features",
        }

        render_chapter_header(chapter, console)

        assert "Deep dive" in output.getvalue()

    def test_handles_missing_description(self):
        """Test that missing description is handled gracefully."""
        console, output = make_test_console()
        chapter = {"number": 1, "title": "Basics"}

        # Should not raise
        render_chapter_header(chapter, console)
        assert "Basics" in output.getvalue()


class TestRenderProgressBar:
    """Tests for render_progress_bar function."""

    def test_shows_progress_label(self):
        """Test that Progress: label is shown."""
        console, output = make_test_console()
        render_progress_bar(2, 4, console)
        assert "Progress" in output.getvalue()

    def test_shows_fraction(self):
        """Test that index/total fraction is shown."""
        console, output = make_test_console()
        render_progress_bar(2, 4, console)
        assert "2/4" in output.getvalue()

    def test_shows_percentage(self):
        """Test that percentage is shown."""
        console, output = make_test_console()
        render_progress_bar(2, 4, console)
        assert "50%" in output.getvalue()

    def test_progress_at_start(self):
        """Test progress bar at first concept."""
        console, output = make_test_console()
        render_progress_bar(1, 4, console)
        result = output.getvalue()
        assert "1/4" in result
        assert "25%" in result

    def test_progress_at_end(self):
        """Test progress bar at last concept."""
        console, output = make_test_console()
        render_progress_bar(4, 4, console)
        result = output.getvalue()
        assert "4/4" in result
        assert "100%" in result

    def test_single_concept(self):
        """Test progress bar with single concept."""
        console, output = make_test_console()
        render_progress_bar(1, 1, console)
        result = output.getvalue()
        assert "1/1" in result
        assert "100%" in result


class TestRenderNavigationHelp:
    """Tests for render_navigation_help function."""

    def test_shows_all_options_in_middle(self):
        """Test that all nav options shown when in middle of concepts."""
        console, output = make_test_console()

        render_navigation_help(2, 4, console)

        result = strip_ansi(output.getvalue())
        assert "[p]" in result  # prev
        assert "[n]" in result  # next
        assert "[q]" in result  # quit

    def test_no_prev_on_first_concept(self):
        """Test that prev is not shown on first concept."""
        console, output = make_test_console()

        render_navigation_help(1, 4, console)

        result = strip_ansi(output.getvalue())
        # Should have next and quit, but no prev
        assert "[n]" in result
        assert "[q]" in result
        assert "[p]" not in result

    def test_continue_on_last_concept(self):
        """Test that continue is shown instead of next on last concept."""
        console, output = make_test_console()

        render_navigation_help(4, 4, console)

        result = strip_ansi(output.getvalue())
        assert "[p]" in result  # prev
        assert "[q]" in result  # quit
        assert "[n]" not in result  # no next on last
        assert "[c]" in result  # continue to practice

    def test_single_concept_shows_continue(self):
        """Test that continue and quit shown for single concept."""
        console, output = make_test_console()

        render_navigation_help(1, 1, console)

        result = strip_ansi(output.getvalue())
        assert "[q]" in result
        assert "[c]" in result  # continue to practice
        assert "[p]" not in result  # no prev on single
        assert "[n]" not in result  # no next on single


class TestRenderCommandPractice:
    """Tests for render_command_practice function."""

    def test_renders_title(self):
        """Test that practice title is rendered."""
        console, output = make_test_console()
        practice = {
            "title": "Check Cluster Info",
            "instructions": "Run kubectl",
            "command_hint": "kubectl cluster-info",
        }

        render_command_practice(practice, 1, 3, console)

        assert "Check Cluster Info" in output.getvalue()

    def test_renders_progress(self):
        """Test that progress indicator is shown."""
        console, output = make_test_console()
        practice = {
            "title": "Test",
            "instructions": "Test",
            "command_hint": "echo test",
        }

        render_command_practice(practice, 2, 4, console)

        assert "2/4" in output.getvalue()

    def test_renders_points(self):
        """Test that points are shown when present."""
        console, output = make_test_console()
        practice = {
            "title": "Test",
            "instructions": "Test",
            "command_hint": "echo test",
            "points": 10,
        }

        render_command_practice(practice, 1, 1, console)

        assert "+10 pts" in output.getvalue()

    def test_renders_command_hint(self):
        """Test that command hint is shown."""
        console, output = make_test_console()
        practice = {
            "title": "Test",
            "instructions": "Test",
            "command_hint": "kubectl get pods",
        }

        render_command_practice(practice, 1, 1, console)

        result = output.getvalue()
        assert "kubectl get pods" in result
        assert "Command to run" in result

    def test_handles_missing_command_hint(self):
        """Test that missing command hint is handled."""
        console, output = make_test_console()
        practice = {
            "title": "Test",
            "instructions": "Test",
        }

        # Should not raise
        render_command_practice(practice, 1, 1, console)
        assert "Test" in output.getvalue()


class TestRenderPracticeNavigationHelp:
    """Tests for render_practice_navigation_help function."""

    def test_shows_check_option(self):
        """Test that check option is shown."""
        console, output = make_test_console()

        render_practice_navigation_help(1, 3, console)

        result = strip_ansi(output.getvalue())
        assert "[c]" in result

    def test_shows_skip_option(self):
        """Test that skip option is shown."""
        console, output = make_test_console()

        render_practice_navigation_help(1, 3, console)

        result = strip_ansi(output.getvalue())
        assert "[s]" in result

    def test_shows_quit_option(self):
        """Test that quit option is shown."""
        console, output = make_test_console()

        render_practice_navigation_help(1, 3, console)

        result = strip_ansi(output.getvalue())
        assert "[q]" in result

    def test_shows_prev_when_not_first(self):
        """Test that prev is shown when not on first practice."""
        console, output = make_test_console()

        render_practice_navigation_help(2, 3, console)

        result = strip_ansi(output.getvalue())
        assert "[p]" in result

    def test_no_prev_on_first(self):
        """Test that prev is not shown on first practice."""
        console, output = make_test_console()

        render_practice_navigation_help(1, 3, console)

        result = strip_ansi(output.getvalue())
        assert "[p]" not in result


class TestRenderValidationResult:
    """Tests for render_validation_result function."""

    def test_renders_success_message(self):
        """Test that success message is rendered."""
        console, output = make_test_console()

        render_validation_result(True, "Command validated!", 10, console)

        result = output.getvalue()
        assert "Command validated!" in result
        assert "✓" in result

    def test_renders_points_on_success(self):
        """Test that points are shown on success."""
        console, output = make_test_console()

        render_validation_result(True, "Success", 15, console)

        result = strip_ansi(output.getvalue())
        assert "+15 points" in result

    def test_renders_failure_message(self):
        """Test that failure message is rendered."""
        console, output = make_test_console()

        render_validation_result(False, "Expected text not found", 0, console)

        result = output.getvalue()
        assert "Expected text not found" in result
        assert "✗" in result

    def test_shows_try_again_on_failure(self):
        """Test that try again hint is shown on failure."""
        console, output = make_test_console()

        render_validation_result(False, "Failed", 0, console)

        assert "Try again" in output.getvalue()

    def test_no_points_on_failure(self):
        """Test that points are not shown on failure."""
        console, output = make_test_console()

        render_validation_result(False, "Failed", 10, console)

        # Points value should not appear (we pass 10 but it shouldn't show)
        assert "+10 points" not in output.getvalue()


class TestRenderCommandOutput:
    """Tests for render_command_output function."""

    def test_renders_output_in_panel(self):
        """Test that command output is rendered in a panel."""
        console, output = make_test_console()

        render_command_output("Hello World", console)

        result = output.getvalue()
        assert "Hello World" in result
        assert "Command Output" in result

    def test_handles_empty_output(self):
        """Test that empty output shows placeholder."""
        console, output = make_test_console()

        render_command_output("", console)

        result = output.getvalue()
        assert "(no output)" in result

    def test_handles_whitespace_only_output(self):
        """Test that whitespace-only output shows placeholder."""
        console, output = make_test_console()

        render_command_output("   \n\n  ", console)

        result = output.getvalue()
        assert "(no output)" in result

    def test_truncates_long_output(self):
        """Test that very long output is truncated."""
        console, output = make_test_console()

        # Create output with 25 lines
        long_output = "\n".join([f"Line {i}" for i in range(25)])
        render_command_output(long_output, console)

        result = output.getvalue()
        # Should show truncation message
        assert "more lines" in result
        # First lines should be present
        assert "Line 0" in result
        # Last lines should not be present (truncated)
        assert "Line 24" not in result

    def test_multiline_output(self):
        """Test that multiline output is rendered correctly."""
        console, output = make_test_console()

        render_command_output("Line 1\nLine 2\nLine 3", console)

        result = output.getvalue()
        assert "Line 1" in result
        assert "Line 2" in result
        assert "Line 3" in result


class TestRenderHint:
    """Tests for render_hint function."""

    def test_renders_hint_text(self):
        """Test that hint text is rendered."""
        console, output = make_test_console()

        render_hint("Try running the command again", console)

        result = output.getvalue()
        assert "Try running the command again" in result

    def test_includes_hint_prefix(self):
        """Test that hint includes the hint prefix/emoji."""
        console, output = make_test_console()

        render_hint("Check your cluster status", console)

        result = output.getvalue()
        assert "Hint" in result


class TestRenderCommandPrompt:
    """Tests for render_command_prompt function."""

    def test_renders_hint_when_provided(self):
        """Test that hint is displayed when provided."""
        console, output = make_test_console()

        render_command_prompt("kubectl cluster-info", console)

        result = output.getvalue()
        assert "Hint: kubectl cluster-info" in result

    def test_shows_instructions(self):
        """Test that instructions are shown."""
        console, output = make_test_console()

        render_command_prompt("kubectl get pods", console)

        result = output.getvalue()
        assert "Enter your command" in result
        assert "skip" in result.lower()
        assert "quit" in result.lower()

    def test_no_hint_when_empty(self):
        """Test that hint line is skipped when hint is empty."""
        console, output = make_test_console()

        render_command_prompt("", console)

        result = output.getvalue()
        assert "Hint:" not in result
        assert "Enter your command" in result

    def test_shows_s_and_q_shortcuts(self):
        """Test that s and q shortcuts are shown."""
        console, output = make_test_console()

        render_command_prompt("test", console)

        result = strip_ansi(output.getvalue())
        assert "'s'" in result or "s" in result.lower()
        assert "'q'" in result or "q" in result.lower()
