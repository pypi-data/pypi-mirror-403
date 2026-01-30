"""Deploy and manage Kubernetes manifests."""

import subprocess
import tempfile
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

import yaml

from kubepath.k8s.validator import ValidationResult


@dataclass
class DeployedResource:
    """Tracks a deployed Kubernetes resource."""

    kind: str  # e.g., "Pod", "Deployment"
    name: str  # e.g., "broken-app"
    namespace: str = "default"  # e.g., "default"


@dataclass
class DeploymentResult:
    """Result of deploying a manifest."""

    success: bool
    message: str
    resources: List[DeployedResource] = field(default_factory=list)
    output: str = ""


def parse_manifest_resources(manifest_yaml: str) -> List[DeployedResource]:
    """Parse YAML manifest to extract resource kinds and names.

    Handles multi-document YAML (---) separators.

    Args:
        manifest_yaml: The YAML content to parse.

    Returns:
        List of DeployedResource objects.
    """
    resources = []

    try:
        # Handle multi-document YAML
        docs = list(yaml.safe_load_all(manifest_yaml))

        for doc in docs:
            if doc is None:
                continue

            kind = doc.get("kind", "")
            metadata = doc.get("metadata", {})
            name = metadata.get("name", "")
            namespace = metadata.get("namespace", "default")

            if kind and name:
                resources.append(
                    DeployedResource(kind=kind, name=name, namespace=namespace)
                )
    except yaml.YAMLError:
        # If parsing fails, return empty list
        pass

    return resources


def deploy_manifest(
    manifest_yaml: str,
    namespace: str = "default",
    timeout: int = 30,
) -> DeploymentResult:
    """Deploy a YAML manifest to the cluster.

    Args:
        manifest_yaml: The YAML content to deploy.
        namespace: Target namespace (applied via -n flag).
        timeout: kubectl timeout in seconds.

    Returns:
        DeploymentResult with success status and deployed resources.
    """
    # Parse resources first to track what we're deploying
    resources = parse_manifest_resources(manifest_yaml)

    # Update namespace if specified
    if namespace != "default":
        for resource in resources:
            if resource.namespace == "default":
                resource.namespace = namespace

    # Write manifest to temp file
    temp_file = None
    try:
        temp_file = tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        )
        temp_file.write(manifest_yaml)
        temp_file.close()

        # Run kubectl apply
        cmd = ["kubectl", "apply", "-f", temp_file.name]
        if namespace != "default":
            cmd.extend(["-n", namespace])

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        if result.returncode == 0:
            return DeploymentResult(
                success=True,
                message="Manifest deployed successfully",
                resources=resources,
                output=result.stdout,
            )
        else:
            return DeploymentResult(
                success=False,
                message=f"Deployment failed: {result.stderr}",
                resources=[],
                output=result.stderr,
            )

    except subprocess.TimeoutExpired:
        return DeploymentResult(
            success=False,
            message=f"Deployment timed out after {timeout} seconds",
            resources=[],
            output="",
        )
    except FileNotFoundError:
        return DeploymentResult(
            success=False,
            message="kubectl not found. Please install kubectl.",
            resources=[],
            output="",
        )
    except Exception as e:
        return DeploymentResult(
            success=False,
            message=f"Deployment error: {str(e)}",
            resources=[],
            output="",
        )
    finally:
        # Clean up temp file
        if temp_file:
            try:
                Path(temp_file.name).unlink()
            except OSError:
                pass


def delete_resource(
    resource: DeployedResource,
    timeout: int = 30,
    force: bool = False,
) -> ValidationResult:
    """Delete a specific resource from the cluster.

    Args:
        resource: The resource to delete.
        timeout: kubectl timeout in seconds.
        force: If True, use --force --grace-period=0.

    Returns:
        ValidationResult indicating success/failure.
    """
    try:
        cmd = [
            "kubectl",
            "delete",
            resource.kind.lower(),
            resource.name,
            "-n",
            resource.namespace,
        ]

        if force:
            cmd.extend(["--force", "--grace-period=0"])

        # Don't fail if resource doesn't exist
        cmd.append("--ignore-not-found")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        if result.returncode == 0:
            return ValidationResult(
                success=True,
                message=f"Deleted {resource.kind}/{resource.name}",
                output=result.stdout,
            )
        else:
            return ValidationResult(
                success=False,
                message=f"Failed to delete {resource.kind}/{resource.name}: {result.stderr}",
                output=result.stderr,
            )

    except subprocess.TimeoutExpired:
        return ValidationResult(
            success=False,
            message=f"Delete timed out for {resource.kind}/{resource.name}",
            output="",
        )
    except FileNotFoundError:
        return ValidationResult(
            success=False,
            message="kubectl not found",
            output="",
        )
    except Exception as e:
        return ValidationResult(
            success=False,
            message=f"Delete error: {str(e)}",
            output="",
        )


def delete_resources(
    resources: List[DeployedResource],
    timeout: int = 30,
    force: bool = False,
) -> ValidationResult:
    """Delete multiple resources from the cluster.

    Args:
        resources: List of resources to delete.
        timeout: kubectl timeout per resource.
        force: If True, use --force --grace-period=0.

    Returns:
        ValidationResult indicating overall success/failure.
    """
    if not resources:
        return ValidationResult(
            success=True,
            message="No resources to delete",
            output="",
        )

    all_success = True
    messages = []
    outputs = []

    for resource in resources:
        result = delete_resource(resource, timeout=timeout, force=force)
        if not result.success:
            all_success = False
        messages.append(result.message)
        if result.output:
            outputs.append(result.output)

    return ValidationResult(
        success=all_success,
        message="; ".join(messages),
        output="\n".join(outputs),
    )
