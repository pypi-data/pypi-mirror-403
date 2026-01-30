"""Unit tests for k8s setup_guide module."""

import pytest
from io import StringIO
from unittest.mock import patch

from rich.console import Console

from kubepath.k8s.detector import OSInfo
from kubepath.k8s.setup_guide import (
    SETUP_INSTRUCTIONS,
    KUBECTL_INSTALL,
    show_setup_guide,
    show_kubectl_install,
    show_minikube_required_warning,
)


def make_test_console() -> tuple[Console, StringIO]:
    """Create a test console that captures output."""
    output = StringIO()
    console = Console(file=output, force_terminal=True, width=100)
    return console, output


class TestSetupInstructions:
    """Tests for SETUP_INSTRUCTIONS constant."""

    def test_has_macos_instructions(self):
        """Test macOS instructions are defined."""
        assert "macos" in SETUP_INSTRUCTIONS
        assert "minikube" in SETUP_INSTRUCTIONS["macos"]

    def test_has_linux_instructions(self):
        """Test Linux instructions are defined."""
        assert "linux" in SETUP_INSTRUCTIONS
        assert "minikube" in SETUP_INSTRUCTIONS["linux"]

    def test_has_windows_instructions(self):
        """Test Windows instructions are defined."""
        assert "windows" in SETUP_INSTRUCTIONS
        assert "minikube" in SETUP_INSTRUCTIONS["windows"]

    def test_has_wsl_instructions(self):
        """Test WSL-specific instructions are defined."""
        assert "wsl" in SETUP_INSTRUCTIONS
        assert "minikube" in SETUP_INSTRUCTIONS["wsl"]

    def test_macos_has_only_minikube(self):
        """Test macOS has only minikube option."""
        assert len(SETUP_INSTRUCTIONS["macos"]) == 1
        assert "minikube" in SETUP_INSTRUCTIONS["macos"]
        info = SETUP_INSTRUCTIONS["macos"]["minikube"]
        assert "name" in info
        assert "install" in info

    def test_linux_has_only_minikube(self):
        """Test Linux has only minikube option."""
        assert len(SETUP_INSTRUCTIONS["linux"]) == 1
        assert "minikube" in SETUP_INSTRUCTIONS["linux"]

    def test_windows_has_only_minikube(self):
        """Test Windows has only minikube option."""
        assert len(SETUP_INSTRUCTIONS["windows"]) == 1
        assert "minikube" in SETUP_INSTRUCTIONS["windows"]

    def test_wsl_has_only_minikube(self):
        """Test WSL has only minikube option."""
        assert len(SETUP_INSTRUCTIONS["wsl"]) == 1
        assert "minikube" in SETUP_INSTRUCTIONS["wsl"]


class TestKubectlInstall:
    """Tests for KUBECTL_INSTALL constant."""

    def test_has_macos_instructions(self):
        """Test macOS kubectl install instructions."""
        assert "macos" in KUBECTL_INSTALL
        assert "install" in KUBECTL_INSTALL["macos"]

    def test_has_linux_instructions(self):
        """Test Linux kubectl install instructions."""
        assert "linux" in KUBECTL_INSTALL
        assert "install" in KUBECTL_INSTALL["linux"]

    def test_has_windows_instructions(self):
        """Test Windows kubectl install instructions."""
        assert "windows" in KUBECTL_INSTALL
        assert "install" in KUBECTL_INSTALL["windows"]


class TestShowSetupGuide:
    """Tests for show_setup_guide function."""

    def test_shows_macos_guide(self):
        """Test shows macOS setup guide with minikube."""
        console, output = make_test_console()
        os_info = OSInfo(system="Darwin", name="macos")

        with patch("kubepath.k8s.setup_guide.get_console", return_value=console):
            show_setup_guide(os_info)

        result = output.getvalue()
        assert "minikube" in result.lower()
        assert "Macos" in result or "macos" in result.lower()

    def test_shows_linux_guide(self):
        """Test shows Linux setup guide with minikube."""
        console, output = make_test_console()
        os_info = OSInfo(system="Linux", name="linux")

        with patch("kubepath.k8s.setup_guide.get_console", return_value=console):
            show_setup_guide(os_info)

        result = output.getvalue()
        assert "minikube" in result.lower()
        assert "Linux" in result or "linux" in result.lower()

    def test_shows_windows_guide(self):
        """Test shows Windows setup guide with minikube."""
        console, output = make_test_console()
        os_info = OSInfo(system="Windows", name="windows")

        with patch("kubepath.k8s.setup_guide.get_console", return_value=console):
            show_setup_guide(os_info)

        result = output.getvalue()
        assert "minikube" in result.lower()
        assert "Windows" in result or "windows" in result.lower()

    def test_shows_wsl_guide(self):
        """Test shows WSL-specific guide with minikube."""
        console, output = make_test_console()
        os_info = OSInfo(system="Linux", name="linux", is_wsl=True)

        with patch("kubepath.k8s.setup_guide.get_console", return_value=console):
            show_setup_guide(os_info)

        result = output.getvalue()
        assert "WSL" in result
        assert "minikube" in result.lower()

    def test_handles_unknown_os(self):
        """Test handles unknown OS gracefully."""
        console, output = make_test_console()
        os_info = OSInfo(system="FreeBSD", name="unknown")

        with patch("kubepath.k8s.setup_guide.get_console", return_value=console):
            show_setup_guide(os_info)

        result = output.getvalue()
        # Should show minikube docs link
        assert "minikube.sigs.k8s.io" in result

    def test_shows_not_detected_message(self):
        """Test shows cluster not detected message."""
        console, output = make_test_console()
        os_info = OSInfo(system="Darwin", name="macos")

        with patch("kubepath.k8s.setup_guide.get_console", return_value=console):
            show_setup_guide(os_info)

        result = output.getvalue()
        assert "not detected" in result.lower()

    def test_shows_requires_minikube_message(self):
        """Test shows that kubepath requires minikube."""
        console, output = make_test_console()
        os_info = OSInfo(system="Darwin", name="macos")

        with patch("kubepath.k8s.setup_guide.get_console", return_value=console):
            show_setup_guide(os_info)

        result = output.getvalue()
        assert "requires minikube" in result.lower()

    def test_shows_prerequisites(self):
        """Test shows prerequisites section."""
        console, output = make_test_console()
        os_info = OSInfo(system="Darwin", name="macos")

        with patch("kubepath.k8s.setup_guide.get_console", return_value=console):
            show_setup_guide(os_info)

        result = output.getvalue()
        assert "Prerequisites" in result


class TestShowKubectlInstall:
    """Tests for show_kubectl_install function."""

    def test_shows_macos_instructions(self):
        """Test shows macOS kubectl install instructions."""
        console, output = make_test_console()
        os_info = OSInfo(system="Darwin", name="macos")

        with patch("kubepath.k8s.setup_guide.get_console", return_value=console):
            show_kubectl_install(os_info)

        result = output.getvalue()
        assert "kubectl" in result.lower()
        assert "brew" in result.lower() or "curl" in result.lower()

    def test_shows_linux_instructions(self):
        """Test shows Linux kubectl install instructions."""
        console, output = make_test_console()
        os_info = OSInfo(system="Linux", name="linux")

        with patch("kubepath.k8s.setup_guide.get_console", return_value=console):
            show_kubectl_install(os_info)

        result = output.getvalue()
        assert "kubectl" in result.lower()
        assert "curl" in result.lower()

    def test_shows_linux_instructions_for_wsl(self):
        """Test shows Linux instructions for WSL."""
        console, output = make_test_console()
        os_info = OSInfo(system="Linux", name="linux", is_wsl=True)

        with patch("kubepath.k8s.setup_guide.get_console", return_value=console):
            show_kubectl_install(os_info)

        result = output.getvalue()
        # WSL should use Linux instructions
        assert "curl" in result.lower()

    def test_shows_not_found_message(self):
        """Test shows kubectl not found message."""
        console, output = make_test_console()
        os_info = OSInfo(system="Darwin", name="macos")

        with patch("kubepath.k8s.setup_guide.get_console", return_value=console):
            show_kubectl_install(os_info)

        result = output.getvalue()
        assert "not found" in result.lower()

    def test_handles_unknown_os(self):
        """Test handles unknown OS gracefully."""
        console, output = make_test_console()
        os_info = OSInfo(system="FreeBSD", name="unknown")

        with patch("kubepath.k8s.setup_guide.get_console", return_value=console):
            show_kubectl_install(os_info)

        result = output.getvalue()
        # Should show generic message
        assert "kubernetes.io" in result.lower()


class TestShowMinikubeRequiredWarning:
    """Tests for show_minikube_required_warning function."""

    def test_shows_warning_for_docker_desktop(self):
        """Test shows warning for docker-desktop provider."""
        console, output = make_test_console()

        with patch("kubepath.k8s.setup_guide.get_console", return_value=console):
            show_minikube_required_warning("docker-desktop")

        result = output.getvalue()
        assert "non-minikube" in result.lower()
        assert "docker-desktop" in result.lower()

    def test_shows_warning_for_kind(self):
        """Test shows warning for kind provider."""
        console, output = make_test_console()

        with patch("kubepath.k8s.setup_guide.get_console", return_value=console):
            show_minikube_required_warning("kind")

        result = output.getvalue()
        assert "kind" in result.lower()
        assert "minikube" in result.lower()

    def test_shows_switch_instructions(self):
        """Test shows instructions to switch to minikube."""
        console, output = make_test_console()

        with patch("kubepath.k8s.setup_guide.get_console", return_value=console):
            show_minikube_required_warning("k3s")

        result = output.getvalue()
        assert "minikube start" in result
        assert "kubectl config use-context minikube" in result

    def test_shows_designed_for_minikube(self):
        """Test shows that kubepath is designed for minikube."""
        console, output = make_test_console()

        with patch("kubepath.k8s.setup_guide.get_console", return_value=console):
            show_minikube_required_warning("gke")

        result = output.getvalue()
        assert "designed for minikube" in result.lower()
