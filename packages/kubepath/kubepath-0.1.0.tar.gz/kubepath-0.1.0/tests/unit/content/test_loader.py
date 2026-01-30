"""Unit tests for content loader."""

import pytest
from pathlib import Path
from unittest.mock import patch, mock_open

import yaml

from kubepath.content.loader import (
    load_chapter,
    get_available_chapters,
    ChapterNotFoundError,
    ChapterValidationError,
    get_content_dir,
    _validate_chapter,
)


class TestGetContentDir:
    """Tests for get_content_dir function."""

    def test_returns_path(self):
        """Test that get_content_dir returns a Path object."""
        result = get_content_dir()
        assert isinstance(result, Path)

    def test_path_ends_with_data(self):
        """Test that the path ends with 'data'."""
        result = get_content_dir()
        assert result.name == "data"


class TestLoadChapter:
    """Tests for load_chapter function."""

    def test_load_valid_chapter(self, tmp_path):
        """Test loading a valid chapter file."""
        # Create a temporary chapter file
        chapters_dir = tmp_path / "chapters"
        chapters_dir.mkdir()
        chapter_file = chapters_dir / "01-test.yaml"
        chapter_file.write_text("""
chapter:
  number: 1
  title: "Test Chapter"

concepts:
  - title: "Test Concept"
    content: "Test content"
""")

        with patch("kubepath.content.loader.get_content_dir", return_value=tmp_path):
            result = load_chapter(1)

        assert result["chapter"]["number"] == 1
        assert result["chapter"]["title"] == "Test Chapter"
        assert len(result["concepts"]) == 1

    def test_chapter_not_found(self, tmp_path):
        """Test that missing chapter raises ChapterNotFoundError."""
        chapters_dir = tmp_path / "chapters"
        chapters_dir.mkdir()

        with patch("kubepath.content.loader.get_content_dir", return_value=tmp_path):
            with pytest.raises(ChapterNotFoundError) as exc_info:
                load_chapter(999)

        assert "Chapter 999 not found" in str(exc_info.value)

    def test_invalid_yaml(self, tmp_path):
        """Test that invalid YAML raises yaml.YAMLError."""
        chapters_dir = tmp_path / "chapters"
        chapters_dir.mkdir()
        chapter_file = chapters_dir / "01-test.yaml"
        chapter_file.write_text("chapter:\n  title: 'unterminated string")

        with patch("kubepath.content.loader.get_content_dir", return_value=tmp_path):
            with pytest.raises(yaml.YAMLError):
                load_chapter(1)

    def test_missing_chapter_field(self, tmp_path):
        """Test that missing 'chapter' field raises ChapterValidationError."""
        chapters_dir = tmp_path / "chapters"
        chapters_dir.mkdir()
        chapter_file = chapters_dir / "01-test.yaml"
        chapter_file.write_text("""
title: "No chapter field"
concepts:
  - title: "Test"
    content: "Test"
""")

        with patch("kubepath.content.loader.get_content_dir", return_value=tmp_path):
            with pytest.raises(ChapterValidationError) as exc_info:
                load_chapter(1)

        assert "missing required 'chapter' field" in str(exc_info.value)

    def test_missing_concepts_field(self, tmp_path):
        """Test that missing 'concepts' field raises ChapterValidationError."""
        chapters_dir = tmp_path / "chapters"
        chapters_dir.mkdir()
        chapter_file = chapters_dir / "01-test.yaml"
        chapter_file.write_text("""
chapter:
  number: 1
  title: "Test"
""")

        with patch("kubepath.content.loader.get_content_dir", return_value=tmp_path):
            with pytest.raises(ChapterValidationError) as exc_info:
                load_chapter(1)

        assert "missing required 'concepts' field" in str(exc_info.value)

    def test_empty_concepts_list(self, tmp_path):
        """Test that empty concepts list raises ChapterValidationError."""
        chapters_dir = tmp_path / "chapters"
        chapters_dir.mkdir()
        chapter_file = chapters_dir / "01-test.yaml"
        chapter_file.write_text("""
chapter:
  number: 1
  title: "Test"

concepts: []
""")

        with patch("kubepath.content.loader.get_content_dir", return_value=tmp_path):
            with pytest.raises(ChapterValidationError) as exc_info:
                load_chapter(1)

        assert "must be a non-empty list" in str(exc_info.value)


class TestValidateChapter:
    """Tests for _validate_chapter function."""

    def test_valid_chapter(self):
        """Test that valid chapter passes validation."""
        data = {
            "chapter": {"number": 1, "title": "Test"},
            "concepts": [{"title": "Concept", "content": "Content"}],
        }
        # Should not raise
        _validate_chapter(data, Path("test.yaml"))

    def test_non_dict_data(self):
        """Test that non-dict data raises error."""
        with pytest.raises(ChapterValidationError) as exc_info:
            _validate_chapter("not a dict", Path("test.yaml"))
        assert "must contain a YAML dictionary" in str(exc_info.value)

    def test_chapter_not_dict(self):
        """Test that non-dict chapter field raises error."""
        data = {"chapter": "not a dict", "concepts": []}
        with pytest.raises(ChapterValidationError) as exc_info:
            _validate_chapter(data, Path("test.yaml"))
        assert "'chapter' must be a dictionary" in str(exc_info.value)

    def test_missing_chapter_title(self):
        """Test that missing title raises error."""
        data = {"chapter": {"number": 1}, "concepts": [{"title": "T", "content": "C"}]}
        with pytest.raises(ChapterValidationError) as exc_info:
            _validate_chapter(data, Path("test.yaml"))
        assert "missing required field 'title'" in str(exc_info.value)

    def test_concept_missing_title(self):
        """Test that concept without title raises error."""
        data = {
            "chapter": {"number": 1, "title": "Test"},
            "concepts": [{"content": "No title"}],
        }
        with pytest.raises(ChapterValidationError) as exc_info:
            _validate_chapter(data, Path("test.yaml"))
        assert "concept 0 missing required 'title' field" in str(exc_info.value)

    def test_concept_missing_content(self):
        """Test that concept without content raises error."""
        data = {
            "chapter": {"number": 1, "title": "Test"},
            "concepts": [{"title": "No content"}],
        }
        with pytest.raises(ChapterValidationError) as exc_info:
            _validate_chapter(data, Path("test.yaml"))
        assert "concept 0 missing required 'content' field" in str(exc_info.value)


class TestGetAvailableChapters:
    """Tests for get_available_chapters function."""

    def test_returns_empty_list_when_no_chapters(self, tmp_path):
        """Test returns empty list when no chapter files exist."""
        chapters_dir = tmp_path / "chapters"
        chapters_dir.mkdir()

        with patch("kubepath.content.loader.get_content_dir", return_value=tmp_path):
            result = get_available_chapters()

        assert result == []

    def test_returns_empty_list_when_chapters_dir_missing(self, tmp_path):
        """Test returns empty list when chapters directory doesn't exist."""
        with patch("kubepath.content.loader.get_content_dir", return_value=tmp_path):
            result = get_available_chapters()

        assert result == []

    def test_finds_single_chapter(self, tmp_path):
        """Test finds a single chapter file."""
        chapters_dir = tmp_path / "chapters"
        chapters_dir.mkdir()
        (chapters_dir / "01-basics.yaml").write_text("chapter: {}")

        with patch("kubepath.content.loader.get_content_dir", return_value=tmp_path):
            result = get_available_chapters()

        assert result == [1]

    def test_finds_multiple_chapters(self, tmp_path):
        """Test finds multiple chapter files."""
        chapters_dir = tmp_path / "chapters"
        chapters_dir.mkdir()
        (chapters_dir / "01-basics.yaml").write_text("chapter: {}")
        (chapters_dir / "02-pods.yaml").write_text("chapter: {}")
        (chapters_dir / "03-deployments.yaml").write_text("chapter: {}")

        with patch("kubepath.content.loader.get_content_dir", return_value=tmp_path):
            result = get_available_chapters()

        assert result == [1, 2, 3]

    def test_returns_sorted_list(self, tmp_path):
        """Test chapters are returned in sorted order."""
        chapters_dir = tmp_path / "chapters"
        chapters_dir.mkdir()
        # Create files in non-sorted order
        (chapters_dir / "03-deployments.yaml").write_text("chapter: {}")
        (chapters_dir / "01-basics.yaml").write_text("chapter: {}")
        (chapters_dir / "02-pods.yaml").write_text("chapter: {}")

        with patch("kubepath.content.loader.get_content_dir", return_value=tmp_path):
            result = get_available_chapters()

        assert result == [1, 2, 3]

    def test_ignores_non_chapter_files(self, tmp_path):
        """Test ignores files that don't match chapter pattern."""
        chapters_dir = tmp_path / "chapters"
        chapters_dir.mkdir()
        (chapters_dir / "01-basics.yaml").write_text("chapter: {}")
        (chapters_dir / "readme.yaml").write_text("not a chapter")
        (chapters_dir / "schema.yaml").write_text("not a chapter")

        with patch("kubepath.content.loader.get_content_dir", return_value=tmp_path):
            result = get_available_chapters()

        assert result == [1]

    def test_handles_double_digit_chapters(self, tmp_path):
        """Test handles chapter numbers >= 10."""
        chapters_dir = tmp_path / "chapters"
        chapters_dir.mkdir()
        (chapters_dir / "01-basics.yaml").write_text("chapter: {}")
        (chapters_dir / "10-advanced.yaml").write_text("chapter: {}")
        (chapters_dir / "99-final.yaml").write_text("chapter: {}")

        with patch("kubepath.content.loader.get_content_dir", return_value=tmp_path):
            result = get_available_chapters()

        assert result == [1, 10, 99]
