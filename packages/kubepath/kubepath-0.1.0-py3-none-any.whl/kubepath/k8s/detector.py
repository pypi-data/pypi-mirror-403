"""OS and Kubernetes environment detection."""

import platform
import shutil
import subprocess
from dataclasses import dataclass


@dataclass
class OSInfo:
    """Operating system information."""

    system: str  # 'Darwin', 'Linux', 'Windows'
    name: str  # 'macos', 'linux', 'windows', 'unknown'
    is_wsl: bool = False


@dataclass
class K8sEnvironment:
    """Kubernetes environment information."""

    provider: str  # 'docker-desktop', 'minikube', 'kind', 'k3s', 'rancher-desktop', etc.
    context: str
    is_running: bool


def detect_os() -> OSInfo:
    """Detect the current operating system.

    Returns:
        OSInfo with system details.
    """
    system = platform.system()
    name_map = {
        "Darwin": "macos",
        "Linux": "linux",
        "Windows": "windows",
    }
    name = name_map.get(system, "unknown")

    is_wsl = False
    if system == "Linux":
        is_wsl = _is_wsl()

    return OSInfo(system=system, name=name, is_wsl=is_wsl)


def _is_wsl() -> bool:
    """Check if running inside Windows Subsystem for Linux.

    Returns:
        True if running in WSL, False otherwise.
    """
    try:
        with open("/proc/version", "r") as f:
            version_info = f.read().lower()
            return "microsoft" in version_info or "wsl" in version_info
    except (FileNotFoundError, OSError, PermissionError):
        return False


def check_kubectl_installed() -> bool:
    """Check if kubectl is installed and in PATH.

    Returns:
        True if kubectl is available, False otherwise.
    """
    return shutil.which("kubectl") is not None


def get_current_context() -> str | None:
    """Get the current kubectl context.

    Returns:
        Current context name, or None if not available.
    """
    if not check_kubectl_installed():
        return None

    try:
        result = subprocess.run(
            ["kubectl", "config", "current-context"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass

    return None


def _detect_provider_from_context(context: str) -> str:
    """Detect K8s provider from context name.

    Args:
        context: The kubectl context name.

    Returns:
        Provider name (best guess based on context name).
    """
    context_lower = context.lower()

    if "docker-desktop" in context_lower or "docker-for-desktop" in context_lower:
        return "docker-desktop"
    elif "minikube" in context_lower:
        return "minikube"
    elif "kind" in context_lower:
        return "kind"
    elif "k3s" in context_lower or "k3d" in context_lower:
        return "k3s"
    elif "rancher" in context_lower:
        return "rancher-desktop"
    elif "microk8s" in context_lower:
        return "microk8s"
    elif "gke" in context_lower or "gcloud" in context_lower:
        return "gke"
    elif "eks" in context_lower or "aws" in context_lower:
        return "eks"
    elif "aks" in context_lower or "azure" in context_lower:
        return "aks"
    else:
        return "unknown"


def detect_k8s_environment() -> K8sEnvironment | None:
    """Detect the Kubernetes environment.

    Returns:
        K8sEnvironment if a cluster is detected, None otherwise.
    """
    if not check_kubectl_installed():
        return None

    context = get_current_context()
    if not context:
        return None

    # Try to check if the cluster is actually running
    is_running = _check_cluster_running()

    provider = _detect_provider_from_context(context)

    return K8sEnvironment(
        provider=provider,
        context=context,
        is_running=is_running,
    )


def _check_cluster_running() -> bool:
    """Check if the Kubernetes cluster is running and reachable.

    Returns:
        True if cluster responds, False otherwise.
    """
    try:
        result = subprocess.run(
            ["kubectl", "cluster-info"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        # Check if we got a successful response with cluster info
        return result.returncode == 0 and "Kubernetes" in result.stdout
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False


def is_minikube_provider(env: K8sEnvironment | None) -> bool:
    """Check if the detected environment is minikube.

    Args:
        env: The detected K8s environment, or None.

    Returns:
        True if the provider is minikube, False otherwise.
    """
    if env is None:
        return False
    return env.provider == "minikube"
