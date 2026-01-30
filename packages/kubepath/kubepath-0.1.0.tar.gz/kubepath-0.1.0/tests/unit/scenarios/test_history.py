"""Unit tests for history module."""

import pytest
from datetime import datetime

from kubepath.scenarios.history import CommandHistory, CommandRecord
from kubepath.k8s.validator import ValidationResult


class TestCommandRecord:
    """Tests for CommandRecord dataclass."""

    def test_record_creation(self):
        """Test creating a command record."""
        result = ValidationResult(success=True, message="OK", output="output")
        record = CommandRecord(
            command="kubectl get pods",
            timestamp=datetime.now(),
            result=result,
            duration_ms=150,
        )
        assert record.command == "kubectl get pods"
        assert record.result.success is True
        assert record.duration_ms == 150


class TestCommandHistory:
    """Tests for CommandHistory class."""

    def test_add_command(self):
        """Test adding a command to history."""
        history = CommandHistory()
        result = ValidationResult(success=True, message="OK", output="output")

        history.add("kubectl get pods", result, duration_ms=100)

        assert history.command_count == 1

    def test_add_multiple_commands(self):
        """Test adding multiple commands."""
        history = CommandHistory()
        result = ValidationResult(success=True, message="OK", output="output")

        history.add("kubectl get pods", result)
        history.add("kubectl describe pod test", result)

        assert history.command_count == 2

    def test_get_recent(self):
        """Test getting recent commands."""
        history = CommandHistory()
        result = ValidationResult(success=True, message="OK", output="output")

        for i in range(10):
            history.add(f"command-{i}", result)

        recent = history.get_recent(3)
        assert len(recent) == 3
        assert recent[0].command == "command-7"
        assert recent[2].command == "command-9"

    def test_get_recent_fewer_than_n(self):
        """Test get_recent when fewer commands than requested."""
        history = CommandHistory()
        result = ValidationResult(success=True, message="OK", output="output")

        history.add("command-1", result)
        history.add("command-2", result)

        recent = history.get_recent(5)
        assert len(recent) == 2

    def test_get_failures(self):
        """Test getting failed commands."""
        history = CommandHistory()
        success = ValidationResult(success=True, message="OK", output="")
        failure = ValidationResult(success=False, message="Error", output="")

        history.add("good-command", success)
        history.add("bad-command", failure)
        history.add("another-good", success)

        failures = history.get_failures()
        assert len(failures) == 1
        assert failures[0].command == "bad-command"

    def test_get_successes(self):
        """Test getting successful commands."""
        history = CommandHistory()
        success = ValidationResult(success=True, message="OK", output="")
        failure = ValidationResult(success=False, message="Error", output="")

        history.add("good-command", success)
        history.add("bad-command", failure)
        history.add("another-good", success)

        successes = history.get_successes()
        assert len(successes) == 2

    def test_get_kubectl_commands(self):
        """Test getting only kubectl commands."""
        history = CommandHistory()
        result = ValidationResult(success=True, message="OK", output="")

        history.add("kubectl get pods", result)
        history.add("ls -la", result)
        history.add("kubectl describe pod test", result)
        history.add("cat file.yaml", result)

        kubectl_cmds = history.get_kubectl_commands()
        assert len(kubectl_cmds) == 2
        assert "kubectl get pods" in kubectl_cmds
        assert "kubectl describe pod test" in kubectl_cmds

    def test_format_for_ai_context_empty(self):
        """Test formatting empty history for AI."""
        history = CommandHistory()
        context = history.format_for_ai_context()
        assert "No commands executed yet" in context

    def test_format_for_ai_context(self):
        """Test formatting history for AI context."""
        history = CommandHistory()
        success = ValidationResult(success=True, message="OK", output="pod/test Running")
        failure = ValidationResult(success=False, message="Error", output="not found")

        history.add("kubectl get pods", success)
        history.add("kubectl describe pod missing", failure)

        context = history.format_for_ai_context()
        assert "Recent commands:" in context
        assert "kubectl get pods" in context
        assert "[OK]" in context
        assert "[FAILED]" in context

    def test_format_for_ai_context_truncates_output(self):
        """Test that long output is truncated."""
        history = CommandHistory()
        long_output = "x" * 500
        result = ValidationResult(success=True, message="OK", output=long_output)

        history.add("kubectl get all", result)
        context = history.format_for_ai_context()

        # Output should be truncated
        assert "..." in context

    def test_get_last_output(self):
        """Test getting last command output."""
        history = CommandHistory()
        result1 = ValidationResult(success=True, message="OK", output="output1")
        result2 = ValidationResult(success=True, message="OK", output="output2")

        history.add("command1", result1)
        history.add("command2", result2)

        assert history.get_last_output() == "output2"

    def test_get_last_output_empty(self):
        """Test get_last_output with no commands."""
        history = CommandHistory()
        assert history.get_last_output() is None

    def test_get_last_error(self):
        """Test getting last error message."""
        history = CommandHistory()
        success = ValidationResult(success=True, message="OK", output="")
        failure = ValidationResult(success=False, message="Connection refused", output="")

        history.add("good", success)
        history.add("bad", failure)
        history.add("good2", success)

        assert history.get_last_error() == "Connection refused"

    def test_get_last_error_no_errors(self):
        """Test get_last_error with no errors."""
        history = CommandHistory()
        success = ValidationResult(success=True, message="OK", output="")

        history.add("good", success)
        assert history.get_last_error() is None

    def test_clear(self):
        """Test clearing history."""
        history = CommandHistory()
        result = ValidationResult(success=True, message="OK", output="")

        history.add("command1", result)
        history.add("command2", result)

        history.clear()
        assert history.command_count == 0

    def test_get_summary(self):
        """Test getting history summary."""
        history = CommandHistory()
        success = ValidationResult(success=True, message="OK", output="")
        failure = ValidationResult(success=False, message="Error", output="")

        history.add("kubectl get pods", success)
        history.add("ls -la", success)
        history.add("kubectl describe pod x", failure)

        summary = history.get_summary()
        assert summary["total_commands"] == 3
        assert summary["successful"] == 2
        assert summary["failed"] == 1
        assert summary["kubectl_commands"] == 2
