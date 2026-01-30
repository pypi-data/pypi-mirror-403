"""Unit tests for cleanup module."""

import pytest
from unittest.mock import patch, MagicMock

from kubepath.scenarios.cleanup import CleanupManager
from kubepath.k8s.deployer import DeployedResource
from kubepath.k8s.validator import ValidationResult


class TestCleanupManager:
    """Tests for CleanupManager class."""

    def test_register_resources(self):
        """Test registering resources."""
        manager = CleanupManager()
        resources = [
            DeployedResource(kind="Pod", name="pod-1"),
            DeployedResource(kind="Pod", name="pod-2"),
        ]

        manager.register(resources)
        assert len(manager.deployed_resources) == 2
        assert manager.has_resources is True

    def test_register_multiple_times(self):
        """Test registering resources multiple times."""
        manager = CleanupManager()

        manager.register([DeployedResource(kind="Pod", name="pod-1")])
        manager.register([DeployedResource(kind="Pod", name="pod-2")])

        assert len(manager.deployed_resources) == 2

    def test_cleanup_success(self):
        """Test successful cleanup."""
        manager = CleanupManager()
        manager.register([DeployedResource(kind="Pod", name="pod-1")])

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "deleted"

        with patch("subprocess.run", return_value=mock_result):
            success = manager.cleanup()
            assert success is True
            assert manager.has_resources is False

    def test_cleanup_empty(self):
        """Test cleanup with no resources."""
        manager = CleanupManager()
        success = manager.cleanup()
        assert success is True

    def test_cleanup_already_done(self):
        """Test cleanup called twice."""
        manager = CleanupManager()
        manager.register([DeployedResource(kind="Pod", name="pod-1")])

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "deleted"

        with patch("subprocess.run", return_value=mock_result):
            manager.cleanup()
            # Second cleanup should be a no-op
            success = manager.cleanup()
            assert success is True

    def test_get_active_resources(self):
        """Test getting active resources."""
        manager = CleanupManager()
        resources = [DeployedResource(kind="Pod", name="pod-1")]
        manager.register(resources)

        active = manager.get_active_resources()
        assert len(active) == 1
        assert active[0].name == "pod-1"

    def test_get_active_resources_after_cleanup(self):
        """Test getting active resources after cleanup."""
        manager = CleanupManager()
        manager.register([DeployedResource(kind="Pod", name="pod-1")])

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "deleted"

        with patch("subprocess.run", return_value=mock_result):
            manager.cleanup()
            active = manager.get_active_resources()
            assert len(active) == 0

    def test_reset(self):
        """Test resetting the manager."""
        manager = CleanupManager()
        manager.register([DeployedResource(kind="Pod", name="pod-1")])
        manager._cleaned_up = True

        manager.reset()
        assert len(manager.deployed_resources) == 0
        assert manager._cleaned_up is False
        assert manager.has_resources is False

    def test_context_manager(self):
        """Test using as context manager."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "deleted"

        with patch("subprocess.run", return_value=mock_result):
            with CleanupManager() as manager:
                manager.register([DeployedResource(kind="Pod", name="pod-1")])
                assert manager.has_resources is True
            # After context exit, should be cleaned up
            assert manager._cleaned_up is True

    def test_context_manager_on_exception(self):
        """Test context manager cleans up on exception."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "deleted"

        with patch("subprocess.run", return_value=mock_result):
            with pytest.raises(ValueError):
                with CleanupManager() as manager:
                    manager.register([DeployedResource(kind="Pod", name="pod-1")])
                    raise ValueError("Test error")
            # Should still clean up
            assert manager._cleaned_up is True

    def test_has_resources_false_when_empty(self):
        """Test has_resources when no resources."""
        manager = CleanupManager()
        assert manager.has_resources is False

    def test_force_cleanup(self):
        """Test force cleanup option."""
        manager = CleanupManager()
        manager.register([DeployedResource(kind="Pod", name="pod-1")])

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "deleted"

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            manager.cleanup(force=True)
            # Check force flag was passed
            call_args = mock_run.call_args[0][0]
            assert "--force" in call_args
