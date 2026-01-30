"""Unit tests for progress tracking."""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from kubepath.utils.progress import (
    load_progress,
    save_progress,
    get_current_concept,
    clear_progress,
    get_progress_dir,
    get_progress_file,
)


class TestGetProgressDir:
    """Tests for get_progress_dir function."""

    def test_returns_path_in_home(self):
        """Test that progress dir is in user's home."""
        result = get_progress_dir()
        assert result.parent == Path.home()
        assert result.name == ".kubepath"


class TestLoadProgress:
    """Tests for load_progress function."""

    def test_returns_empty_when_no_file(self, tmp_path):
        """Test that missing file returns empty progress."""
        with patch("kubepath.utils.progress.get_progress_file", return_value=tmp_path / "nonexistent.json"):
            result = load_progress()
            assert result == {"chapters": {}}

    def test_loads_existing_progress(self, tmp_path):
        """Test loading existing progress file."""
        progress_file = tmp_path / "progress.json"
        progress_file.write_text('{"chapters": {"1": {"current_concept": 2}}}')

        with patch("kubepath.utils.progress.get_progress_file", return_value=progress_file):
            result = load_progress()
            assert result["chapters"]["1"]["current_concept"] == 2

    def test_handles_corrupted_json(self, tmp_path):
        """Test that corrupted JSON returns empty progress."""
        progress_file = tmp_path / "progress.json"
        progress_file.write_text("not valid json {{{")

        with patch("kubepath.utils.progress.get_progress_file", return_value=progress_file):
            result = load_progress()
            assert result == {"chapters": {}}


class TestSaveProgress:
    """Tests for save_progress function."""

    def test_creates_directory_and_file(self, tmp_path):
        """Test that save creates directory and file."""
        progress_dir = tmp_path / ".kubepath"
        progress_file = progress_dir / "progress.json"

        with patch("kubepath.utils.progress.get_progress_dir", return_value=progress_dir):
            with patch("kubepath.utils.progress.get_progress_file", return_value=progress_file):
                save_progress(1, 3)

                assert progress_dir.exists()
                assert progress_file.exists()

                data = json.loads(progress_file.read_text())
                assert data["chapters"]["1"]["current_concept"] == 3

    def test_updates_existing_progress(self, tmp_path):
        """Test that save updates existing chapter progress."""
        progress_dir = tmp_path / ".kubepath"
        progress_dir.mkdir()
        progress_file = progress_dir / "progress.json"
        progress_file.write_text('{"chapters": {"1": {"current_concept": 0}}}')

        with patch("kubepath.utils.progress.get_progress_dir", return_value=progress_dir):
            with patch("kubepath.utils.progress.get_progress_file", return_value=progress_file):
                save_progress(1, 5)

                data = json.loads(progress_file.read_text())
                assert data["chapters"]["1"]["current_concept"] == 5

    def test_preserves_other_chapters(self, tmp_path):
        """Test that saving one chapter preserves others."""
        progress_dir = tmp_path / ".kubepath"
        progress_dir.mkdir()
        progress_file = progress_dir / "progress.json"
        progress_file.write_text('{"chapters": {"1": {"current_concept": 2}}}')

        with patch("kubepath.utils.progress.get_progress_dir", return_value=progress_dir):
            with patch("kubepath.utils.progress.get_progress_file", return_value=progress_file):
                save_progress(2, 1)

                data = json.loads(progress_file.read_text())
                assert data["chapters"]["1"]["current_concept"] == 2
                assert data["chapters"]["2"]["current_concept"] == 1


class TestGetCurrentConcept:
    """Tests for get_current_concept function."""

    def test_returns_zero_when_no_progress(self, tmp_path):
        """Test that missing progress returns 0."""
        with patch("kubepath.utils.progress.get_progress_file", return_value=tmp_path / "nonexistent.json"):
            result = get_current_concept(1)
            assert result == 0

    def test_returns_saved_index(self, tmp_path):
        """Test that saved index is returned."""
        progress_file = tmp_path / "progress.json"
        progress_file.write_text('{"chapters": {"1": {"current_concept": 3}}}')

        with patch("kubepath.utils.progress.get_progress_file", return_value=progress_file):
            result = get_current_concept(1)
            assert result == 3

    def test_returns_zero_for_unknown_chapter(self, tmp_path):
        """Test that unknown chapter returns 0."""
        progress_file = tmp_path / "progress.json"
        progress_file.write_text('{"chapters": {"1": {"current_concept": 3}}}')

        with patch("kubepath.utils.progress.get_progress_file", return_value=progress_file):
            result = get_current_concept(99)
            assert result == 0


class TestClearProgress:
    """Tests for clear_progress function."""

    def test_clear_specific_chapter(self, tmp_path):
        """Test clearing a specific chapter."""
        progress_dir = tmp_path / ".kubepath"
        progress_dir.mkdir()
        progress_file = progress_dir / "progress.json"
        progress_file.write_text('{"chapters": {"1": {"current_concept": 2}, "2": {"current_concept": 1}}}')

        with patch("kubepath.utils.progress.get_progress_dir", return_value=progress_dir):
            with patch("kubepath.utils.progress.get_progress_file", return_value=progress_file):
                clear_progress(1)

                data = json.loads(progress_file.read_text())
                assert "1" not in data["chapters"]
                assert data["chapters"]["2"]["current_concept"] == 1

    def test_clear_all_progress(self, tmp_path):
        """Test clearing all progress."""
        progress_dir = tmp_path / ".kubepath"
        progress_dir.mkdir()
        progress_file = progress_dir / "progress.json"
        progress_file.write_text('{"chapters": {"1": {"current_concept": 2}}}')

        with patch("kubepath.utils.progress.get_progress_file", return_value=progress_file):
            clear_progress(None)
            assert not progress_file.exists()

    def test_clear_nonexistent_file_no_error(self, tmp_path):
        """Test that clearing nonexistent file doesn't raise."""
        with patch("kubepath.utils.progress.get_progress_file", return_value=tmp_path / "nonexistent.json"):
            # Should not raise
            clear_progress(1)
            clear_progress(None)
