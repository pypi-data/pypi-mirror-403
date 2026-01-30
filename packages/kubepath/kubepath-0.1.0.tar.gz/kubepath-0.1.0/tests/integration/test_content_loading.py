"""Integration tests for content loading."""

import pytest

from kubepath.content.loader import load_chapter, ChapterNotFoundError


class TestContentLoading:
    """Integration tests that load real chapter files."""

    def test_load_chapter_1(self):
        """Test loading the real chapter 1 file."""
        chapter = load_chapter(1)

        # Check chapter metadata
        assert chapter["chapter"]["number"] == 1
        assert chapter["chapter"]["title"] == "What is Kubernetes?"
        assert "description" in chapter["chapter"]

        # Check concepts exist
        assert "concepts" in chapter
        assert len(chapter["concepts"]) > 0

    def test_chapter_1_has_valid_concepts(self):
        """Test that chapter 1 concepts have required fields."""
        chapter = load_chapter(1)

        for concept in chapter["concepts"]:
            assert "title" in concept
            assert "content" in concept
            assert len(concept["title"]) > 0
            assert len(concept["content"]) > 0

    def test_chapter_1_has_kubernetes_content(self):
        """Test that chapter 1 actually teaches Kubernetes."""
        chapter = load_chapter(1)

        # Collect all content
        all_content = " ".join(c["content"] for c in chapter["concepts"])
        all_content_lower = all_content.lower()

        # Should mention Kubernetes concepts
        assert "kubernetes" in all_content_lower
        assert "pod" in all_content_lower or "container" in all_content_lower

    def test_nonexistent_chapter_raises_error(self):
        """Test that loading a nonexistent chapter raises error."""
        with pytest.raises(ChapterNotFoundError):
            load_chapter(999)
