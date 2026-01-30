"""Unit tests for auto-update module."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from kubepath.utils.updater import (
    UpdateResult,
    check_and_update,
    compare_versions,
    get_latest_remote_version,
    get_local_version,
    get_repo_root,
    is_git_available,
    is_git_repo,
    perform_git_pull,
    should_check_for_updates,
)


class TestUpdateResult:
    """Tests for UpdateResult dataclass."""

    def test_creation_minimal(self):
        """Test creating UpdateResult with required fields."""
        result = UpdateResult(
            checked=True,
            update_available=False,
            updated=False,
            local_version="0.1.0",
        )
        assert result.checked is True
        assert result.remote_version is None
        assert result.error is None

    def test_creation_full(self):
        """Test creating UpdateResult with all fields."""
        result = UpdateResult(
            checked=True,
            update_available=True,
            updated=True,
            local_version="0.1.0",
            remote_version="0.1.1",
            message="Update successful",
            error=None,
        )
        assert result.remote_version == "0.1.1"
        assert result.message == "Update successful"


class TestGetLocalVersion:
    """Tests for get_local_version function."""

    def test_returns_version_string(self):
        """Test that version is returned."""
        version = get_local_version()
        assert isinstance(version, str)
        assert len(version) > 0

    def test_version_format(self):
        """Test version follows semantic versioning format."""
        version = get_local_version()
        parts = version.split(".")
        assert len(parts) >= 2  # At least major.minor


class TestIsGitAvailable:
    """Tests for is_git_available function."""

    def test_git_found(self):
        """Test returns True when git is found."""
        with patch("shutil.which", return_value="/usr/bin/git"):
            assert is_git_available() is True

    def test_git_not_found(self):
        """Test returns False when git is not found."""
        with patch("shutil.which", return_value=None):
            assert is_git_available() is False


class TestGetRepoRoot:
    """Tests for get_repo_root function."""

    def test_returns_path_in_git_repo(self):
        """Test returns path when in git repo."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "/home/user/kubepath\n"

        with patch("subprocess.run", return_value=mock_result):
            result = get_repo_root()
            assert result == Path("/home/user/kubepath")

    def test_returns_none_outside_git_repo(self):
        """Test returns None when not in git repo."""
        mock_result = MagicMock()
        mock_result.returncode = 128

        with patch("subprocess.run", return_value=mock_result):
            result = get_repo_root()
            assert result is None

    def test_returns_none_on_timeout(self):
        """Test returns None on timeout."""
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("git", 10)):
            result = get_repo_root()
            assert result is None

    def test_returns_none_when_git_not_found(self):
        """Test returns None when git binary not found."""
        with patch("subprocess.run", side_effect=FileNotFoundError):
            result = get_repo_root()
            assert result is None


class TestIsGitRepo:
    """Tests for is_git_repo function."""

    def test_returns_true_in_repo(self):
        """Test returns True when in a git repo."""
        with patch(
            "kubepath.utils.updater.get_repo_root", return_value=Path("/some/path")
        ):
            assert is_git_repo() is True

    def test_returns_false_outside_repo(self):
        """Test returns False when not in a git repo."""
        with patch("kubepath.utils.updater.get_repo_root", return_value=None):
            assert is_git_repo() is False


class TestCompareVersions:
    """Tests for compare_versions function."""

    def test_local_older(self):
        """Test returns -1 when local is older."""
        assert compare_versions("0.1.0", "0.1.1") == -1
        assert compare_versions("0.1.0", "0.2.0") == -1
        assert compare_versions("0.1.0", "1.0.0") == -1

    def test_versions_equal(self):
        """Test returns 0 when versions are equal."""
        assert compare_versions("0.1.0", "0.1.0") == 0
        assert compare_versions("1.0.0", "1.0.0") == 0

    def test_local_newer(self):
        """Test returns 1 when local is newer."""
        assert compare_versions("0.1.1", "0.1.0") == 1
        assert compare_versions("0.2.0", "0.1.0") == 1
        assert compare_versions("1.0.0", "0.1.0") == 1

    def test_invalid_version_returns_zero(self):
        """Test returns 0 for invalid version strings."""
        assert compare_versions("invalid", "0.1.0") == 0
        assert compare_versions("0.1.0", "invalid") == 0


class TestGetLatestRemoteVersion:
    """Tests for get_latest_remote_version function."""

    def test_returns_version_on_success(self, tmp_path):
        """Test returns version when fetch and describe succeed."""
        fetch_result = MagicMock()
        fetch_result.returncode = 0

        describe_result = MagicMock()
        describe_result.returncode = 0
        describe_result.stdout = "v0.2.0\n"

        with patch("subprocess.run", side_effect=[fetch_result, describe_result]):
            version = get_latest_remote_version(tmp_path)
            assert version == "0.2.0"

    def test_strips_v_prefix(self, tmp_path):
        """Test strips 'v' prefix from tag."""
        fetch_result = MagicMock()
        fetch_result.returncode = 0

        describe_result = MagicMock()
        describe_result.returncode = 0
        describe_result.stdout = "v1.2.3\n"

        with patch("subprocess.run", side_effect=[fetch_result, describe_result]):
            version = get_latest_remote_version(tmp_path)
            assert version == "1.2.3"

    def test_returns_none_on_fetch_failure(self, tmp_path):
        """Test returns None when fetch fails."""
        fetch_result = MagicMock()
        fetch_result.returncode = 1

        with patch("subprocess.run", return_value=fetch_result):
            version = get_latest_remote_version(tmp_path)
            assert version is None

    def test_returns_none_on_network_timeout(self, tmp_path):
        """Test returns None on network timeout."""
        with patch(
            "subprocess.run", side_effect=subprocess.TimeoutExpired("git", 30)
        ):
            version = get_latest_remote_version(tmp_path)
            assert version is None


class TestPerformGitPull:
    """Tests for perform_git_pull function."""

    def test_success(self, tmp_path):
        """Test returns success on successful pull."""
        mock_result = MagicMock()
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result):
            success, message = perform_git_pull(tmp_path)
            assert success is True
            assert "successful" in message.lower()

    def test_fails_with_local_changes(self, tmp_path):
        """Test fails when local changes would be overwritten."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "error: Your local changes would be overwritten"

        with patch("subprocess.run", return_value=mock_result):
            success, message = perform_git_pull(tmp_path)
            assert success is False
            assert "local changes" in message.lower()

    def test_fails_on_timeout(self, tmp_path):
        """Test fails on timeout."""
        with patch(
            "subprocess.run", side_effect=subprocess.TimeoutExpired("git", 60)
        ):
            success, message = perform_git_pull(tmp_path)
            assert success is False
            assert "timed out" in message.lower()

    def test_fails_when_git_not_found(self, tmp_path):
        """Test fails when git not found."""
        with patch("subprocess.run", side_effect=FileNotFoundError):
            success, message = perform_git_pull(tmp_path)
            assert success is False
            assert "git not found" in message.lower()


class TestCheckAndUpdate:
    """Tests for check_and_update function."""

    def test_skips_when_git_not_available(self):
        """Test skips update when git not available."""
        with patch("kubepath.utils.updater.is_git_available", return_value=False):
            result = check_and_update()
            assert result.checked is False
            assert result.error == "Git not available"

    def test_skips_when_not_git_repo(self):
        """Test skips update when not in git repo."""
        with patch("kubepath.utils.updater.is_git_available", return_value=True):
            with patch("kubepath.utils.updater.get_repo_root", return_value=None):
                result = check_and_update()
                assert result.checked is False
                assert "git repository" in result.error.lower()

    def test_skips_when_cannot_fetch_remote(self, tmp_path):
        """Test skips when remote version cannot be fetched."""
        with patch("kubepath.utils.updater.is_git_available", return_value=True):
            with patch("kubepath.utils.updater.get_repo_root", return_value=tmp_path):
                with patch(
                    "kubepath.utils.updater.get_latest_remote_version",
                    return_value=None,
                ):
                    result = check_and_update()
                    assert result.checked is False
                    assert "remote version" in result.error.lower()

    def test_already_up_to_date(self, tmp_path):
        """Test returns up-to-date when versions match."""
        with patch("kubepath.utils.updater.is_git_available", return_value=True):
            with patch("kubepath.utils.updater.get_repo_root", return_value=tmp_path):
                with patch(
                    "kubepath.utils.updater.get_local_version", return_value="0.1.0"
                ):
                    with patch(
                        "kubepath.utils.updater.get_latest_remote_version",
                        return_value="0.1.0",
                    ):
                        result = check_and_update()
                        assert result.checked is True
                        assert result.update_available is False
                        assert result.updated is False

    def test_performs_update_when_available(self, tmp_path):
        """Test performs update when newer version available."""
        with patch("kubepath.utils.updater.is_git_available", return_value=True):
            with patch("kubepath.utils.updater.get_repo_root", return_value=tmp_path):
                with patch(
                    "kubepath.utils.updater.get_local_version", return_value="0.1.0"
                ):
                    with patch(
                        "kubepath.utils.updater.get_latest_remote_version",
                        return_value="0.2.0",
                    ):
                        with patch(
                            "kubepath.utils.updater.perform_git_pull",
                            return_value=(True, "Success"),
                        ):
                            result = check_and_update()
                            assert result.checked is True
                            assert result.update_available is True
                            assert result.updated is True

    def test_handles_failed_update(self, tmp_path):
        """Test handles failed git pull."""
        with patch("kubepath.utils.updater.is_git_available", return_value=True):
            with patch("kubepath.utils.updater.get_repo_root", return_value=tmp_path):
                with patch(
                    "kubepath.utils.updater.get_local_version", return_value="0.1.0"
                ):
                    with patch(
                        "kubepath.utils.updater.get_latest_remote_version",
                        return_value="0.2.0",
                    ):
                        with patch(
                            "kubepath.utils.updater.perform_git_pull",
                            return_value=(False, "Local changes"),
                        ):
                            result = check_and_update()
                            assert result.checked is True
                            assert result.update_available is True
                            assert result.updated is False
                            assert result.error is not None


class TestShouldCheckForUpdates:
    """Tests for should_check_for_updates function."""

    def test_returns_true_by_default(self):
        """Test returns True when no env vars set."""
        with patch.dict("os.environ", {}, clear=True):
            assert should_check_for_updates() is True

    def test_returns_false_when_disabled(self):
        """Test returns False when KUBEPATH_NO_UPDATE=1."""
        with patch.dict("os.environ", {"KUBEPATH_NO_UPDATE": "1"}):
            assert should_check_for_updates() is False

    def test_returns_false_in_ci(self):
        """Test returns False in CI environment."""
        with patch.dict("os.environ", {"CI": "true"}, clear=True):
            assert should_check_for_updates() is False

    def test_returns_false_in_github_actions(self):
        """Test returns False in GitHub Actions."""
        with patch.dict("os.environ", {"GITHUB_ACTIONS": "true"}, clear=True):
            assert should_check_for_updates() is False

    def test_returns_true_when_disabled_with_zero(self):
        """Test returns True when KUBEPATH_NO_UPDATE=0."""
        with patch.dict("os.environ", {"KUBEPATH_NO_UPDATE": "0"}, clear=True):
            assert should_check_for_updates() is True
