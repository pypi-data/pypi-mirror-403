"""Resource cleanup management for scenarios."""

from dataclasses import dataclass, field
from typing import List

from kubepath.k8s.deployer import DeployedResource, delete_resources


@dataclass
class CleanupManager:
    """Tracks and cleans up scenario resources.

    Can be used as a context manager to ensure cleanup on exceptions.

    Example:
        with CleanupManager() as cleanup:
            cleanup.register(deployed_resources)
            # Do scenario work...
        # Resources automatically cleaned up
    """

    deployed_resources: List[DeployedResource] = field(default_factory=list)
    _cleaned_up: bool = False

    def register(self, resources: List[DeployedResource]) -> None:
        """Register resources for cleanup tracking.

        Args:
            resources: List of deployed resources to track.
        """
        self.deployed_resources.extend(resources)

    def cleanup(self, force: bool = False, timeout: int = 30) -> bool:
        """Clean up all tracked resources.

        Args:
            force: If True, force deletion without waiting for graceful shutdown.
            timeout: Timeout per resource deletion.

        Returns:
            True if cleanup succeeded for all resources.
        """
        if self._cleaned_up:
            return True

        if not self.deployed_resources:
            self._cleaned_up = True
            return True

        result = delete_resources(
            self.deployed_resources, timeout=timeout, force=force
        )

        if result.success:
            self._cleaned_up = True
            self.deployed_resources.clear()

        return result.success

    def get_active_resources(self) -> List[DeployedResource]:
        """Get list of currently tracked resources.

        Returns:
            List of resources that haven't been cleaned up yet.
        """
        if self._cleaned_up:
            return []
        return list(self.deployed_resources)

    @property
    def has_resources(self) -> bool:
        """Check if there are resources to clean up.

        Returns:
            True if there are tracked resources.
        """
        return len(self.deployed_resources) > 0 and not self._cleaned_up

    def reset(self) -> None:
        """Reset the cleanup manager for reuse.

        Clears tracked resources and reset cleaned_up flag.
        """
        self.deployed_resources.clear()
        self._cleaned_up = False

    def __enter__(self) -> "CleanupManager":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Context manager exit - always cleanup.

        Args:
            exc_type: Exception type if an exception was raised.
            exc_val: Exception value if an exception was raised.
            exc_tb: Exception traceback if an exception was raised.

        Returns:
            False to not suppress exceptions.
        """
        # Always cleanup, even on exceptions
        self.cleanup(force=True)
        return False  # Don't suppress exceptions
