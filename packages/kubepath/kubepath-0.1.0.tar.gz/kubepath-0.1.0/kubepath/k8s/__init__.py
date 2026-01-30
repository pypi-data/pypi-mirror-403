"""Kubernetes environment detection and setup for kubepath."""

from kubepath.k8s.detector import (
    OSInfo,
    K8sEnvironment,
    detect_os,
    check_kubectl_installed,
    detect_k8s_environment,
    get_current_context,
    is_minikube_provider,
)
from kubepath.k8s.setup_guide import (
    show_setup_guide,
    show_kubectl_install,
    show_minikube_required_warning,
)
from kubepath.k8s.validator import (
    ValidationResult,
    validate_command_output,
    validate_from_spec,
    execute_command,
    validate_output,
)

__all__ = [
    "OSInfo",
    "K8sEnvironment",
    "detect_os",
    "check_kubectl_installed",
    "detect_k8s_environment",
    "get_current_context",
    "is_minikube_provider",
    "show_setup_guide",
    "show_kubectl_install",
    "show_minikube_required_warning",
    "ValidationResult",
    "validate_command_output",
    "validate_from_spec",
    "execute_command",
    "validate_output",
]
