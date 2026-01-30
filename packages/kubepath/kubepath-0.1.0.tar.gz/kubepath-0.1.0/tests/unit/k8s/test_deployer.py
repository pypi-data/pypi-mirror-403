"""Unit tests for k8s deployer module."""

import subprocess
import pytest
from unittest.mock import patch, MagicMock

from kubepath.k8s.deployer import (
    DeployedResource,
    DeploymentResult,
    parse_manifest_resources,
    deploy_manifest,
    delete_resource,
    delete_resources,
)


class TestDeployedResource:
    """Tests for DeployedResource dataclass."""

    def test_resource_creation(self):
        """Test creating a deployed resource."""
        resource = DeployedResource(kind="Pod", name="test-pod")
        assert resource.kind == "Pod"
        assert resource.name == "test-pod"
        assert resource.namespace == "default"

    def test_resource_with_namespace(self):
        """Test creating resource with custom namespace."""
        resource = DeployedResource(kind="Deployment", name="test", namespace="production")
        assert resource.namespace == "production"


class TestParseManifestResources:
    """Tests for parse_manifest_resources function."""

    def test_parses_single_pod(self):
        """Test parsing a single pod manifest."""
        manifest = """
apiVersion: v1
kind: Pod
metadata:
  name: test-pod
spec:
  containers:
  - name: test
    image: nginx
"""
        resources = parse_manifest_resources(manifest)
        assert len(resources) == 1
        assert resources[0].kind == "Pod"
        assert resources[0].name == "test-pod"
        assert resources[0].namespace == "default"

    def test_parses_multi_document(self):
        """Test parsing multi-document YAML."""
        manifest = """
apiVersion: v1
kind: Pod
metadata:
  name: pod-1
---
apiVersion: v1
kind: Service
metadata:
  name: svc-1
"""
        resources = parse_manifest_resources(manifest)
        assert len(resources) == 2
        assert resources[0].kind == "Pod"
        assert resources[0].name == "pod-1"
        assert resources[1].kind == "Service"
        assert resources[1].name == "svc-1"

    def test_parses_namespace(self):
        """Test parsing resource with namespace."""
        manifest = """
apiVersion: v1
kind: Pod
metadata:
  name: test-pod
  namespace: production
"""
        resources = parse_manifest_resources(manifest)
        assert len(resources) == 1
        assert resources[0].namespace == "production"

    def test_handles_invalid_yaml(self):
        """Test handling invalid YAML."""
        manifest = "this is not: valid: yaml: ["
        resources = parse_manifest_resources(manifest)
        assert resources == []

    def test_handles_empty_manifest(self):
        """Test handling empty manifest."""
        resources = parse_manifest_resources("")
        assert resources == []

    def test_skips_empty_documents(self):
        """Test skipping empty documents in multi-doc YAML."""
        manifest = """
---
apiVersion: v1
kind: Pod
metadata:
  name: test-pod
---
"""
        resources = parse_manifest_resources(manifest)
        assert len(resources) == 1


class TestDeployManifest:
    """Tests for deploy_manifest function."""

    def test_successful_deployment(self):
        """Test successful manifest deployment."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "pod/test-pod created"

        manifest = """
apiVersion: v1
kind: Pod
metadata:
  name: test-pod
"""
        with patch("subprocess.run", return_value=mock_result):
            result = deploy_manifest(manifest)
            assert result.success is True
            assert len(result.resources) == 1
            assert result.resources[0].name == "test-pod"

    def test_deployment_failure(self):
        """Test deployment failure."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "error: resource not found"

        with patch("subprocess.run", return_value=mock_result):
            result = deploy_manifest("apiVersion: v1\nkind: Pod\nmetadata:\n  name: test")
            assert result.success is False
            assert "error" in result.message.lower()
            assert result.resources == []

    def test_deployment_timeout(self):
        """Test deployment timeout handling."""
        manifest = "apiVersion: v1\nkind: Pod\nmetadata:\n  name: test"

        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("kubectl", 30)):
            result = deploy_manifest(manifest)
            assert result.success is False
            assert "timed out" in result.message.lower()

    def test_kubectl_not_found(self):
        """Test handling kubectl not found."""
        manifest = "apiVersion: v1\nkind: Pod\nmetadata:\n  name: test"

        with patch("subprocess.run", side_effect=FileNotFoundError):
            result = deploy_manifest(manifest)
            assert result.success is False
            assert "kubectl" in result.message.lower()

    def test_custom_namespace(self):
        """Test deployment with custom namespace."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "pod/test-pod created"

        manifest = "apiVersion: v1\nkind: Pod\nmetadata:\n  name: test"

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            result = deploy_manifest(manifest, namespace="production")
            assert result.success is True
            # Check namespace flag was passed
            call_args = mock_run.call_args[0][0]
            assert "-n" in call_args
            assert "production" in call_args


class TestDeleteResource:
    """Tests for delete_resource function."""

    def test_successful_deletion(self):
        """Test successful resource deletion."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "pod \"test-pod\" deleted"

        resource = DeployedResource(kind="Pod", name="test-pod")

        with patch("subprocess.run", return_value=mock_result):
            result = delete_resource(resource)
            assert result.success is True

    def test_deletion_failure(self):
        """Test deletion failure."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "error: pod not found"

        resource = DeployedResource(kind="Pod", name="test-pod")

        with patch("subprocess.run", return_value=mock_result):
            result = delete_resource(resource)
            assert result.success is False

    def test_force_delete(self):
        """Test force deletion."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "deleted"

        resource = DeployedResource(kind="Pod", name="test-pod")

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            result = delete_resource(resource, force=True)
            assert result.success is True
            # Check force flags
            call_args = mock_run.call_args[0][0]
            assert "--force" in call_args
            assert "--grace-period=0" in call_args

    def test_deletion_timeout(self):
        """Test deletion timeout."""
        resource = DeployedResource(kind="Pod", name="test-pod")

        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("kubectl", 30)):
            result = delete_resource(resource)
            assert result.success is False
            assert "timed out" in result.message.lower()


class TestDeleteResources:
    """Tests for delete_resources function."""

    def test_delete_multiple_resources(self):
        """Test deleting multiple resources."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "deleted"

        resources = [
            DeployedResource(kind="Pod", name="pod-1"),
            DeployedResource(kind="Service", name="svc-1"),
        ]

        with patch("subprocess.run", return_value=mock_result):
            result = delete_resources(resources)
            assert result.success is True

    def test_delete_empty_list(self):
        """Test deleting empty list."""
        result = delete_resources([])
        assert result.success is True
        assert "no resources" in result.message.lower()

    def test_partial_failure(self):
        """Test partial deletion failure."""
        # First succeeds, second fails
        mock_results = [
            MagicMock(returncode=0, stdout="deleted"),
            MagicMock(returncode=1, stderr="error"),
        ]

        resources = [
            DeployedResource(kind="Pod", name="pod-1"),
            DeployedResource(kind="Pod", name="pod-2"),
        ]

        with patch("subprocess.run", side_effect=mock_results):
            result = delete_resources(resources)
            assert result.success is False
