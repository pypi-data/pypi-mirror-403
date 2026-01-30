"""Integration tests for content rendering."""

import pytest
from io import StringIO

from rich.console import Console

from kubepath.content import load_chapter, render_concepts, render_chapter_header


def make_test_console() -> tuple[Console, StringIO]:
    """Create a test console that captures output."""
    output = StringIO()
    console = Console(file=output, force_terminal=True, width=100)
    return console, output


class TestContentRendering:
    """Integration tests for loading and rendering chapter content."""

    def test_load_and_render_chapter_1(self):
        """Test loading and rendering chapter 1 concepts."""
        console, output = make_test_console()

        # Load real chapter 1
        chapter_data = load_chapter(1)

        # Render header
        render_chapter_header(chapter_data["chapter"], console)

        # Render concepts
        render_concepts(chapter_data["concepts"], console)

        result = output.getvalue()

        # Should contain chapter info
        assert "What is Kubernetes?" in result

        # Should contain at least some concept content
        assert "Kubernetes" in result

    def test_rendered_output_is_readable(self):
        """Test that rendered output doesn't have obvious formatting issues."""
        console, output = make_test_console()

        chapter_data = load_chapter(1)
        render_chapter_header(chapter_data["chapter"], console)
        render_concepts(chapter_data["concepts"], console)

        result = output.getvalue()

        # Should have some structure (panels, etc.)
        assert len(result) > 100  # Should have substantial content

        # Should have multiple concepts rendered
        lines = result.split("\n")
        assert len(lines) > 10  # Should have multiple lines

    def test_all_concepts_rendered(self):
        """Test that all concepts from chapter 1 are rendered."""
        console, output = make_test_console()

        chapter_data = load_chapter(1)
        concepts = chapter_data["concepts"]

        render_concepts(concepts, console)

        result = output.getvalue()

        # Every concept title should appear in output
        for concept in concepts:
            title = concept["title"]
            assert title in result, f"Concept '{title}' not found in rendered output"
