"""Unit tests for k8s detector module."""

import pytest
from unittest.mock import patch, mock_open, MagicMock
import subprocess

from kubepath.k8s.detector import (
    OSInfo,
    K8sEnvironment,
    detect_os,
    _is_wsl,
    check_kubectl_installed,
    get_current_context,
    _detect_provider_from_context,
    detect_k8s_environment,
    _check_cluster_running,
    is_minikube_provider,
)


class TestOSInfo:
    """Tests for OSInfo dataclass."""

    def test_osinfo_creation(self):
        """Test OSInfo can be created with required fields."""
        info = OSInfo(system="Darwin", name="macos")
        assert info.system == "Darwin"
        assert info.name == "macos"
        assert info.is_wsl is False

    def test_osinfo_with_wsl(self):
        """Test OSInfo with WSL flag."""
        info = OSInfo(system="Linux", name="linux", is_wsl=True)
        assert info.is_wsl is True


class TestDetectOS:
    """Tests for detect_os function."""

    def test_detects_macos(self):
        """Test detecting macOS."""
        with patch("platform.system", return_value="Darwin"):
            result = detect_os()
            assert result.system == "Darwin"
            assert result.name == "macos"
            assert result.is_wsl is False

    def test_detects_linux(self):
        """Test detecting Linux."""
        with patch("platform.system", return_value="Linux"):
            with patch("kubepath.k8s.detector._is_wsl", return_value=False):
                result = detect_os()
                assert result.system == "Linux"
                assert result.name == "linux"
                assert result.is_wsl is False

    def test_detects_windows(self):
        """Test detecting Windows."""
        with patch("platform.system", return_value="Windows"):
            result = detect_os()
            assert result.system == "Windows"
            assert result.name == "windows"
            assert result.is_wsl is False

    def test_detects_unknown_os(self):
        """Test handling unknown OS."""
        with patch("platform.system", return_value="FreeBSD"):
            result = detect_os()
            assert result.system == "FreeBSD"
            assert result.name == "unknown"

    def test_detects_wsl(self):
        """Test detecting WSL."""
        with patch("platform.system", return_value="Linux"):
            with patch("kubepath.k8s.detector._is_wsl", return_value=True):
                result = detect_os()
                assert result.system == "Linux"
                assert result.name == "linux"
                assert result.is_wsl is True


class TestIsWSL:
    """Tests for _is_wsl function."""

    def test_detects_wsl_microsoft(self):
        """Test detecting WSL via microsoft in /proc/version."""
        mock_content = "Linux version 5.15.0 (Microsoft@Microsoft.com)"
        with patch("builtins.open", mock_open(read_data=mock_content)):
            assert _is_wsl() is True

    def test_detects_wsl_wsl_keyword(self):
        """Test detecting WSL via WSL keyword."""
        mock_content = "Linux version 5.15.0-WSL2"
        with patch("builtins.open", mock_open(read_data=mock_content)):
            assert _is_wsl() is True

    def test_not_wsl_on_regular_linux(self):
        """Test regular Linux is not detected as WSL."""
        mock_content = "Linux version 5.15.0-generic (ubuntu@build)"
        with patch("builtins.open", mock_open(read_data=mock_content)):
            assert _is_wsl() is False

    def test_not_wsl_when_file_not_found(self):
        """Test returns False when /proc/version doesn't exist."""
        with patch("builtins.open", side_effect=FileNotFoundError):
            assert _is_wsl() is False

    def test_not_wsl_on_permission_error(self):
        """Test returns False on permission error."""
        with patch("builtins.open", side_effect=PermissionError):
            assert _is_wsl() is False


class TestCheckKubectlInstalled:
    """Tests for check_kubectl_installed function."""

    def test_kubectl_found(self):
        """Test returns True when kubectl is found."""
        with patch("shutil.which", return_value="/usr/local/bin/kubectl"):
            assert check_kubectl_installed() is True

    def test_kubectl_not_found(self):
        """Test returns False when kubectl is not found."""
        with patch("shutil.which", return_value=None):
            assert check_kubectl_installed() is False


class TestGetCurrentContext:
    """Tests for get_current_context function."""

    def test_returns_context_when_available(self):
        """Test returns context name when kubectl works."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "minikube\n"

        with patch("shutil.which", return_value="/usr/local/bin/kubectl"):
            with patch("subprocess.run", return_value=mock_result):
                result = get_current_context()
                assert result == "minikube"

    def test_returns_none_when_kubectl_not_installed(self):
        """Test returns None when kubectl is not installed."""
        with patch("shutil.which", return_value=None):
            result = get_current_context()
            assert result is None

    def test_returns_none_when_command_fails(self):
        """Test returns None when kubectl command fails."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""

        with patch("shutil.which", return_value="/usr/local/bin/kubectl"):
            with patch("subprocess.run", return_value=mock_result):
                result = get_current_context()
                assert result is None

    def test_returns_none_on_timeout(self):
        """Test returns None on command timeout."""
        with patch("shutil.which", return_value="/usr/local/bin/kubectl"):
            with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("kubectl", 10)):
                result = get_current_context()
                assert result is None

    def test_returns_none_on_file_not_found(self):
        """Test returns None when kubectl binary disappears."""
        with patch("shutil.which", return_value="/usr/local/bin/kubectl"):
            with patch("subprocess.run", side_effect=FileNotFoundError):
                result = get_current_context()
                assert result is None


class TestDetectProviderFromContext:
    """Tests for _detect_provider_from_context function."""

    def test_detects_docker_desktop(self):
        """Test detecting Docker Desktop."""
        assert _detect_provider_from_context("docker-desktop") == "docker-desktop"
        assert _detect_provider_from_context("docker-for-desktop") == "docker-desktop"

    def test_detects_minikube(self):
        """Test detecting minikube."""
        assert _detect_provider_from_context("minikube") == "minikube"
        assert _detect_provider_from_context("minikube-dev") == "minikube"

    def test_detects_kind(self):
        """Test detecting kind."""
        assert _detect_provider_from_context("kind-my-cluster") == "kind"
        assert _detect_provider_from_context("kind") == "kind"

    def test_detects_k3s(self):
        """Test detecting k3s/k3d."""
        assert _detect_provider_from_context("k3s-default") == "k3s"
        assert _detect_provider_from_context("k3d-mycluster") == "k3s"

    def test_detects_rancher_desktop(self):
        """Test detecting Rancher Desktop."""
        assert _detect_provider_from_context("rancher-desktop") == "rancher-desktop"

    def test_detects_microk8s(self):
        """Test detecting MicroK8s."""
        assert _detect_provider_from_context("microk8s") == "microk8s"

    def test_detects_cloud_providers(self):
        """Test detecting cloud providers."""
        assert _detect_provider_from_context("gke_project_zone_cluster") == "gke"
        assert _detect_provider_from_context("arn:aws:eks:region:account:cluster") == "eks"
        assert _detect_provider_from_context("my-aks-cluster") == "aks"

    def test_returns_unknown_for_unrecognized(self):
        """Test returns unknown for unrecognized contexts."""
        assert _detect_provider_from_context("my-custom-cluster") == "unknown"
        assert _detect_provider_from_context("production") == "unknown"


class TestDetectK8sEnvironment:
    """Tests for detect_k8s_environment function."""

    def test_returns_none_when_kubectl_not_installed(self):
        """Test returns None when kubectl is not installed."""
        with patch("kubepath.k8s.detector.check_kubectl_installed", return_value=False):
            result = detect_k8s_environment()
            assert result is None

    def test_returns_none_when_no_context(self):
        """Test returns None when no context is set."""
        with patch("kubepath.k8s.detector.check_kubectl_installed", return_value=True):
            with patch("kubepath.k8s.detector.get_current_context", return_value=None):
                result = detect_k8s_environment()
                assert result is None

    def test_returns_environment_when_cluster_running(self):
        """Test returns K8sEnvironment when cluster is running."""
        with patch("kubepath.k8s.detector.check_kubectl_installed", return_value=True):
            with patch("kubepath.k8s.detector.get_current_context", return_value="minikube"):
                with patch("kubepath.k8s.detector._check_cluster_running", return_value=True):
                    result = detect_k8s_environment()
                    assert result is not None
                    assert result.context == "minikube"
                    assert result.provider == "minikube"
                    assert result.is_running is True

    def test_returns_environment_when_cluster_not_running(self):
        """Test returns K8sEnvironment even when cluster not responding."""
        with patch("kubepath.k8s.detector.check_kubectl_installed", return_value=True):
            with patch("kubepath.k8s.detector.get_current_context", return_value="docker-desktop"):
                with patch("kubepath.k8s.detector._check_cluster_running", return_value=False):
                    result = detect_k8s_environment()
                    assert result is not None
                    assert result.context == "docker-desktop"
                    assert result.provider == "docker-desktop"
                    assert result.is_running is False


class TestCheckClusterRunning:
    """Tests for _check_cluster_running function."""

    def test_returns_true_when_cluster_responds(self):
        """Test returns True when cluster-info succeeds."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Kubernetes control plane is running at https://127.0.0.1:6443"

        with patch("subprocess.run", return_value=mock_result):
            assert _check_cluster_running() is True

    def test_returns_false_when_command_fails(self):
        """Test returns False when cluster-info fails."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = "error: unable to connect"

        with patch("subprocess.run", return_value=mock_result):
            assert _check_cluster_running() is False

    def test_returns_false_when_no_kubernetes_in_output(self):
        """Test returns False when output doesn't contain Kubernetes."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Some other output"

        with patch("subprocess.run", return_value=mock_result):
            assert _check_cluster_running() is False

    def test_returns_false_on_timeout(self):
        """Test returns False on timeout."""
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("kubectl", 10)):
            assert _check_cluster_running() is False

    def test_returns_false_on_file_not_found(self):
        """Test returns False when kubectl not found."""
        with patch("subprocess.run", side_effect=FileNotFoundError):
            assert _check_cluster_running() is False


class TestIsMinikubeProvider:
    """Tests for is_minikube_provider function."""

    def test_returns_true_for_minikube(self):
        """Test returns True when provider is minikube."""
        env = K8sEnvironment(provider="minikube", context="minikube", is_running=True)
        assert is_minikube_provider(env) is True

    def test_returns_true_for_minikube_not_running(self):
        """Test returns True for minikube even when not running."""
        env = K8sEnvironment(provider="minikube", context="minikube", is_running=False)
        assert is_minikube_provider(env) is True

    def test_returns_false_for_docker_desktop(self):
        """Test returns False for docker-desktop provider."""
        env = K8sEnvironment(provider="docker-desktop", context="docker-desktop", is_running=True)
        assert is_minikube_provider(env) is False

    def test_returns_false_for_kind(self):
        """Test returns False for kind provider."""
        env = K8sEnvironment(provider="kind", context="kind-cluster", is_running=True)
        assert is_minikube_provider(env) is False

    def test_returns_false_for_k3s(self):
        """Test returns False for k3s provider."""
        env = K8sEnvironment(provider="k3s", context="k3s-default", is_running=True)
        assert is_minikube_provider(env) is False

    def test_returns_false_for_unknown(self):
        """Test returns False for unknown provider."""
        env = K8sEnvironment(provider="unknown", context="custom", is_running=True)
        assert is_minikube_provider(env) is False

    def test_returns_false_for_none(self):
        """Test returns False when env is None."""
        assert is_minikube_provider(None) is False

    def test_returns_false_for_cloud_providers(self):
        """Test returns False for cloud providers."""
        for provider in ["gke", "eks", "aks"]:
            env = K8sEnvironment(provider=provider, context=f"{provider}-cluster", is_running=True)
            assert is_minikube_provider(env) is False
