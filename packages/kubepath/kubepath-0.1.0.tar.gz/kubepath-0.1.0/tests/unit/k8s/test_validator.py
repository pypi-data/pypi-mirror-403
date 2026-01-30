"""Unit tests for k8s validator module."""

import subprocess
import pytest
from unittest.mock import patch, MagicMock

from kubepath.k8s.validator import (
    ValidationResult,
    validate_command_output,
    validate_from_spec,
    execute_command,
    validate_output,
)


class TestValidationResult:
    """Tests for ValidationResult dataclass."""

    def test_success_result(self):
        """Test creating a successful result."""
        result = ValidationResult(success=True, message="OK", output="test output")
        assert result.success is True
        assert result.message == "OK"
        assert result.output == "test output"

    def test_failure_result(self):
        """Test creating a failure result."""
        result = ValidationResult(success=False, message="Failed", output="")
        assert result.success is False
        assert result.message == "Failed"
        assert result.output == ""

    def test_default_output(self):
        """Test default empty output."""
        result = ValidationResult(success=True, message="OK")
        assert result.output == ""


class TestValidateCommandOutput:
    """Tests for validate_command_output function."""

    def test_successful_command_no_checks(self):
        """Test successful command with no output checks."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "some output"
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            result = validate_command_output("echo test")
            assert result.success is True
            assert "matches expected" in result.message
            assert result.output == "some output"

    def test_successful_command_with_expected_contains(self):
        """Test command passes when expected text is found."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Kubernetes master is running"
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            result = validate_command_output(
                "kubectl cluster-info",
                expected_contains="Kubernetes"
            )
            assert result.success is True

    def test_fails_when_expected_not_found(self):
        """Test command fails when expected text is not found."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "some other output"
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            result = validate_command_output(
                "kubectl cluster-info",
                expected_contains="Kubernetes"
            )
            assert result.success is False
            assert "not found" in result.message

    def test_fails_when_unexpected_text_found(self):
        """Test command fails when unexpected text is found."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Error: something went wrong"
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            result = validate_command_output(
                "kubectl get pods",
                expected_not_contains="Error"
            )
            assert result.success is False
            assert "Unexpected" in result.message

    def test_passes_when_unexpected_text_not_found(self):
        """Test command passes when unexpected text is absent."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "NAME   READY   STATUS"
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            result = validate_command_output(
                "kubectl get pods",
                expected_not_contains="Error"
            )
            assert result.success is True

    def test_command_failure_nonzero_exit(self):
        """Test command fails with non-zero exit code."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "error: the server doesn't have a resource type"

        with patch("subprocess.run", return_value=mock_result):
            result = validate_command_output("kubectl get invalid")
            assert result.success is False
            assert "exit code 1" in result.message

    def test_command_timeout(self):
        """Test command timeout handling."""
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 30)):
            result = validate_command_output("kubectl get pods", timeout=30)
            assert result.success is False
            assert "timed out" in result.message

    def test_command_not_found(self):
        """Test handling of command not found."""
        with patch("subprocess.run", side_effect=FileNotFoundError):
            result = validate_command_output("nonexistent-command")
            assert result.success is False
            assert "not found" in result.message

    def test_os_error(self):
        """Test handling of OS errors."""
        with patch("subprocess.run", side_effect=OSError("Permission denied")):
            result = validate_command_output("some-command")
            assert result.success is False
            assert "OS error" in result.message

    def test_combines_stdout_and_stderr(self):
        """Test that output combines stdout and stderr."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "standard output"
        mock_result.stderr = "error output"

        with patch("subprocess.run", return_value=mock_result):
            result = validate_command_output("some-command")
            assert "standard output" in result.output
            assert "error output" in result.output

    def test_custom_timeout(self):
        """Test that custom timeout is passed to subprocess."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            validate_command_output("echo test", timeout=60)
            mock_run.assert_called_once()
            assert mock_run.call_args.kwargs["timeout"] == 60


class TestValidateFromSpec:
    """Tests for validate_from_spec function."""

    def test_valid_command_output_spec(self):
        """Test validation with valid command_output spec."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Kubernetes control plane is running"
        mock_result.stderr = ""

        spec = {
            "type": "command_output",
            "command": "kubectl cluster-info",
            "expected_contains": "Kubernetes",
        }

        with patch("subprocess.run", return_value=mock_result):
            result = validate_from_spec(spec)
            assert result.success is True

    def test_spec_with_expected_not_contains(self):
        """Test spec with expected_not_contains."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "NAME   READY   STATUS"
        mock_result.stderr = ""

        spec = {
            "type": "command_output",
            "command": "kubectl get pods",
            "expected_not_contains": "Error",
        }

        with patch("subprocess.run", return_value=mock_result):
            result = validate_from_spec(spec)
            assert result.success is True

    def test_spec_with_custom_timeout(self):
        """Test spec with custom timeout."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""

        spec = {
            "type": "command_output",
            "command": "kubectl get pods",
            "timeout": 120,
        }

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            validate_from_spec(spec)
            assert mock_run.call_args.kwargs["timeout"] == 120

    def test_unknown_validation_type(self):
        """Test spec with unknown validation type."""
        spec = {
            "type": "unknown_type",
            "command": "echo test",
        }

        result = validate_from_spec(spec)
        assert result.success is False
        assert "Unknown validation type" in result.message

    def test_missing_command_in_spec(self):
        """Test spec missing required command field."""
        spec = {
            "type": "command_output",
            "expected_contains": "test",
        }

        result = validate_from_spec(spec)
        assert result.success is False
        assert "missing 'command'" in result.message

    def test_default_type_is_command_output(self):
        """Test that missing type defaults to command_output."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "test"
        mock_result.stderr = ""

        spec = {
            "command": "echo test",
        }

        with patch("subprocess.run", return_value=mock_result):
            result = validate_from_spec(spec)
            assert result.success is True

    def test_full_spec_example(self):
        """Test complete spec as would appear in chapter YAML."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Kubernetes control plane is running at https://127.0.0.1:6443"
        mock_result.stderr = ""

        spec = {
            "type": "command_output",
            "command": "kubectl cluster-info",
            "expected_contains": "Kubernetes",
            "timeout": 30,
        }

        with patch("subprocess.run", return_value=mock_result):
            result = validate_from_spec(spec)
            assert result.success is True
            assert "Kubernetes" in result.output


class TestExecuteCommand:
    """Tests for execute_command function."""

    def test_successful_command(self):
        """Test successful command execution."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "command output"
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            result = execute_command("echo test")
            assert result.success is True
            assert result.message == "Command executed successfully"
            assert result.output == "command output"

    def test_command_with_nonzero_exit(self):
        """Test command with non-zero exit code."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "error message"

        with patch("subprocess.run", return_value=mock_result):
            result = execute_command("false")
            assert result.success is False
            assert "exited with code 1" in result.message
            assert result.output == "error message"

    def test_command_timeout(self):
        """Test command timeout handling."""
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 30)):
            result = execute_command("sleep 100", timeout=30)
            assert result.success is False
            assert "timed out" in result.message

    def test_command_exception(self):
        """Test handling of general exceptions."""
        with patch("subprocess.run", side_effect=Exception("something broke")):
            result = execute_command("bad-command")
            assert result.success is False
            assert "Error executing command" in result.message

    def test_uses_shell_true(self):
        """Test that shell=True is used for shell interpretation."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "output"
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            execute_command("echo test | grep test")
            mock_run.assert_called_once()
            assert mock_run.call_args.kwargs["shell"] is True

    def test_combines_stdout_stderr(self):
        """Test that output combines stdout and stderr."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "standard out"
        mock_result.stderr = "standard err"

        with patch("subprocess.run", return_value=mock_result):
            result = execute_command("some-command")
            assert "standard out" in result.output
            assert "standard err" in result.output

    def test_custom_timeout(self):
        """Test custom timeout is passed to subprocess."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            execute_command("echo test", timeout=60)
            assert mock_run.call_args.kwargs["timeout"] == 60


class TestValidateOutput:
    """Tests for validate_output function."""

    def test_returns_true_when_expected_found(self):
        """Test returns True when expected text is found."""
        assert validate_output("Kubernetes is running", "Kubernetes") is True

    def test_returns_false_when_expected_not_found(self):
        """Test returns False when expected text is not found."""
        assert validate_output("No pods found", "Kubernetes") is False

    def test_case_insensitive_match(self):
        """Test that match is case-insensitive."""
        assert validate_output("KUBERNETES is running", "kubernetes") is True
        assert validate_output("kubernetes is running", "KUBERNETES") is True

    def test_returns_true_when_expected_is_none(self):
        """Test returns True when expected_contains is None."""
        assert validate_output("any output", None) is True

    def test_returns_true_when_expected_is_empty(self):
        """Test returns True when expected_contains is empty string."""
        assert validate_output("any output", "") is True

    def test_empty_output_with_expected(self):
        """Test empty output fails when expecting text."""
        assert validate_output("", "Kubernetes") is False

    def test_partial_match(self):
        """Test partial string match works."""
        assert validate_output("Kubernetes control plane", "control") is True
