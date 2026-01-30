"""Command and resource validation for Kubernetes."""

import subprocess
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Result of a validation check."""

    success: bool
    message: str
    output: str = ""


def validate_command_output(
    command: str,
    expected_contains: str | None = None,
    expected_not_contains: str | None = None,
    timeout: int = 30,
) -> ValidationResult:
    """Run a command and validate its output.

    Args:
        command: The command to run (as a string).
        expected_contains: Text that must be present in output.
        expected_not_contains: Text that must NOT be present in output.
        timeout: Command timeout in seconds.

    Returns:
        ValidationResult with success status and message.
    """
    try:
        result = subprocess.run(
            command.split(),
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        output = result.stdout + result.stderr

        # Check for command failure
        if result.returncode != 0:
            return ValidationResult(
                success=False,
                message=f"Command failed with exit code {result.returncode}",
                output=output,
            )

        # Check expected_contains
        if expected_contains and expected_contains not in output:
            return ValidationResult(
                success=False,
                message=f"Expected '{expected_contains}' not found in output",
                output=output,
            )

        # Check expected_not_contains
        if expected_not_contains and expected_not_contains in output:
            return ValidationResult(
                success=False,
                message=f"Unexpected '{expected_not_contains}' found in output",
                output=output,
            )

        return ValidationResult(
            success=True,
            message="Command output matches expected criteria",
            output=output,
        )

    except subprocess.TimeoutExpired:
        return ValidationResult(
            success=False,
            message=f"Command timed out after {timeout} seconds",
            output="",
        )
    except FileNotFoundError:
        return ValidationResult(
            success=False,
            message="Command not found",
            output="",
        )
    except OSError as e:
        return ValidationResult(
            success=False,
            message=f"OS error: {e}",
            output="",
        )


def execute_command(command: str, timeout: int = 30) -> ValidationResult:
    """Execute a user-provided command and return the result.

    Args:
        command: The full command string to execute.
        timeout: Timeout in seconds.

    Returns:
        ValidationResult with success=True if command ran successfully,
        success=False if command failed to execute or returned non-zero.
    """
    try:
        result = subprocess.run(
            command,
            shell=True,  # Allow shell interpretation for pipes, etc.
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = result.stdout + result.stderr

        if result.returncode != 0:
            return ValidationResult(
                success=False,
                message=f"Command exited with code {result.returncode}",
                output=output,
            )

        return ValidationResult(
            success=True,
            message="Command executed successfully",
            output=output,
        )
    except subprocess.TimeoutExpired:
        return ValidationResult(
            success=False,
            message=f"Command timed out after {timeout} seconds",
            output="",
        )
    except Exception as e:
        return ValidationResult(
            success=False,
            message=f"Error executing command: {e}",
            output="",
        )


def validate_output(output: str, expected_contains: str | None = None) -> bool:
    """Check if output contains expected text (case-insensitive).

    Args:
        output: The command output to check.
        expected_contains: Text that must be present in output.

    Returns:
        True if output contains expected text (or if expected_contains is None).
    """
    if expected_contains and expected_contains.lower() not in output.lower():
        return False
    return True


def validate_resource_exists(
    resource: str,
    namespace: str = "default",
    timeout: int = 30,
) -> ValidationResult:
    """Check if a Kubernetes resource exists.

    Args:
        resource: Resource in format "type/name" (e.g., "pod/nginx", "deployment/web").
        namespace: Namespace to check in.
        timeout: Command timeout in seconds.

    Returns:
        ValidationResult with success status.
    """
    command = f"kubectl get {resource} -n {namespace} --no-headers"
    try:
        result = subprocess.run(
            command.split(),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = result.stdout + result.stderr

        if result.returncode == 0:
            return ValidationResult(
                success=True,
                message=f"Resource {resource} exists in namespace {namespace}",
                output=output,
            )
        else:
            return ValidationResult(
                success=False,
                message=f"Resource {resource} not found in namespace {namespace}",
                output=output,
            )

    except subprocess.TimeoutExpired:
        return ValidationResult(
            success=False,
            message=f"Command timed out after {timeout} seconds",
            output="",
        )
    except Exception as e:
        return ValidationResult(
            success=False,
            message=f"Error checking resource: {e}",
            output="",
        )


def validate_resource_state(
    resource: str,
    state: str,
    namespace: str = "default",
    timeout: int = 30,
) -> ValidationResult:
    """Check if a Kubernetes resource is in a specific state.

    Args:
        resource: Resource in format "type/name" (e.g., "pod/nginx").
        state: Expected state (e.g., "Running", "Ready", "Succeeded").
        namespace: Namespace to check in.
        timeout: Command timeout in seconds.

    Returns:
        ValidationResult with success status.
    """
    # First check if resource exists
    exists_result = validate_resource_exists(resource, namespace, timeout)
    if not exists_result.success:
        return exists_result

    # Parse resource type and name
    parts = resource.split("/")
    if len(parts) != 2:
        return ValidationResult(
            success=False,
            message=f"Invalid resource format: {resource}. Expected 'type/name'",
            output="",
        )

    resource_type, resource_name = parts

    # Get resource status based on type
    if resource_type.lower() in ["pod", "pods", "po"]:
        command = f"kubectl get pod {resource_name} -n {namespace} -o jsonpath={{.status.phase}}"
    elif resource_type.lower() in ["deployment", "deployments", "deploy"]:
        # For deployments, check if available replicas match desired
        command = f"kubectl get deployment {resource_name} -n {namespace} -o jsonpath={{.status.readyReplicas}}/{{.spec.replicas}}"
    elif resource_type.lower() in ["service", "services", "svc"]:
        # Services are considered "Ready" if they exist
        return ValidationResult(
            success=True,
            message=f"Service {resource_name} exists",
            output="",
        )
    else:
        # Generic check - just verify the resource exists
        return ValidationResult(
            success=True,
            message=f"Resource {resource} exists",
            output="",
        )

    try:
        result = subprocess.run(
            command.split(),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = result.stdout.strip()

        # Check state
        if resource_type.lower() in ["pod", "pods", "po"]:
            if output.lower() == state.lower():
                return ValidationResult(
                    success=True,
                    message=f"Pod {resource_name} is in state {state}",
                    output=output,
                )
            else:
                return ValidationResult(
                    success=False,
                    message=f"Pod {resource_name} is in state '{output}', expected '{state}'",
                    output=output,
                )
        elif resource_type.lower() in ["deployment", "deployments", "deploy"]:
            # For deployments, "Running" or "Ready" means all replicas are ready
            if "/" in output:
                ready, total = output.split("/")
                if ready == total and int(ready) > 0:
                    return ValidationResult(
                        success=True,
                        message=f"Deployment {resource_name} has {ready}/{total} replicas ready",
                        output=output,
                    )
                else:
                    return ValidationResult(
                        success=False,
                        message=f"Deployment {resource_name} has {ready}/{total} replicas ready",
                        output=output,
                    )

        return ValidationResult(
            success=False,
            message=f"Resource {resource} state check failed",
            output=output,
        )

    except subprocess.TimeoutExpired:
        return ValidationResult(
            success=False,
            message=f"Command timed out after {timeout} seconds",
            output="",
        )
    except Exception as e:
        return ValidationResult(
            success=False,
            message=f"Error checking resource state: {e}",
            output="",
        )


def validate_resource_state_stable(
    resource: str,
    state: str,
    namespace: str = "default",
    duration: int = 10,
    timeout: int = 60,
) -> ValidationResult:
    """Check if a resource maintains a state for a specified duration.

    Args:
        resource: Resource in format "type/name".
        state: Expected state to maintain.
        namespace: Namespace to check in.
        duration: How long the state must be stable (seconds).
        timeout: Overall timeout for the check.

    Returns:
        ValidationResult with success status.
    """
    import time

    start_time = time.time()
    stable_start = None

    while time.time() - start_time < timeout:
        result = validate_resource_state(resource, state, namespace, timeout=10)

        if result.success:
            if stable_start is None:
                stable_start = time.time()
            elif time.time() - stable_start >= duration:
                return ValidationResult(
                    success=True,
                    message=f"Resource {resource} has been in state {state} for {duration} seconds",
                    output=result.output,
                )
        else:
            # State changed, reset stable timer
            stable_start = None

        time.sleep(1)

    return ValidationResult(
        success=False,
        message=f"Resource {resource} did not maintain state {state} for {duration} seconds",
        output="",
    )


def validate_from_spec(validation_spec: dict) -> ValidationResult:
    """Validate based on a specification dictionary.

    Args:
        validation_spec: Dictionary with validation configuration:
            - type: "command_output", "resource_exists", "resource_state", or "resource_state_stable"
            - For command_output:
                - command: The command to run (required)
                - expected_contains: Text to find in output (optional)
                - expected_not_contains: Text that should not be in output (optional)
            - For resource_exists/resource_state:
                - resource: Resource in "type/name" format (required)
                - namespace: Namespace (optional, default "default")
                - state: Expected state (required for resource_state)
            - For resource_state_stable:
                - duration: Seconds state must be stable (optional, default 10)
            - timeout: Command timeout in seconds (optional, default 30)

    Returns:
        ValidationResult with success status and message.
    """
    validation_type = validation_spec.get("type", "command_output")
    timeout = validation_spec.get("timeout", 30)
    namespace = validation_spec.get("namespace", "default")

    if validation_type == "command_output":
        command = validation_spec.get("command")
        if not command:
            return ValidationResult(
                success=False,
                message="Validation spec missing 'command' field",
                output="",
            )
        return validate_command_output(
            command=command,
            expected_contains=validation_spec.get("expected_contains"),
            expected_not_contains=validation_spec.get("expected_not_contains"),
            timeout=timeout,
        )

    elif validation_type == "resource_exists":
        resource = validation_spec.get("resource")
        if not resource:
            return ValidationResult(
                success=False,
                message="Validation spec missing 'resource' field",
                output="",
            )
        return validate_resource_exists(
            resource=resource,
            namespace=namespace,
            timeout=timeout,
        )

    elif validation_type == "resource_state":
        resource = validation_spec.get("resource")
        state = validation_spec.get("state")
        if not resource:
            return ValidationResult(
                success=False,
                message="Validation spec missing 'resource' field",
                output="",
            )
        if not state:
            return ValidationResult(
                success=False,
                message="Validation spec missing 'state' field",
                output="",
            )
        return validate_resource_state(
            resource=resource,
            state=state,
            namespace=namespace,
            timeout=timeout,
        )

    elif validation_type == "resource_state_stable":
        resource = validation_spec.get("resource")
        state = validation_spec.get("state")
        duration = validation_spec.get("duration", 10)
        if not resource:
            return ValidationResult(
                success=False,
                message="Validation spec missing 'resource' field",
                output="",
            )
        if not state:
            return ValidationResult(
                success=False,
                message="Validation spec missing 'state' field",
                output="",
            )
        return validate_resource_state_stable(
            resource=resource,
            state=state,
            namespace=namespace,
            duration=duration,
            timeout=timeout,
        )

    else:
        return ValidationResult(
            success=False,
            message=f"Unknown validation type: {validation_type}",
            output="",
        )
