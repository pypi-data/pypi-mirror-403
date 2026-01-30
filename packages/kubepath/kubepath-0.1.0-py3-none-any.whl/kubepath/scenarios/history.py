"""Track learner commands during scenario debugging."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from kubepath.k8s.validator import ValidationResult


@dataclass
class CommandRecord:
    """Record of a single command execution."""

    command: str
    timestamp: datetime
    result: ValidationResult
    duration_ms: int = 0


@dataclass
class CommandHistory:
    """Tracks all commands executed during a scenario.

    Used for:
    - Providing context to AI for better hints
    - Showing learner what they tried
    - Analytics on learning patterns

    Example:
        history = CommandHistory()
        history.add("kubectl get pods", result, duration_ms=150)
        context = history.format_for_ai_context()
    """

    records: List[CommandRecord] = field(default_factory=list)

    def add(
        self,
        command: str,
        result: ValidationResult,
        duration_ms: int = 0,
    ) -> None:
        """Add a command to history.

        Args:
            command: The command that was executed.
            result: The result of the command execution.
            duration_ms: How long the command took in milliseconds.
        """
        self.records.append(
            CommandRecord(
                command=command,
                timestamp=datetime.now(),
                result=result,
                duration_ms=duration_ms,
            )
        )

    @property
    def command_count(self) -> int:
        """Total number of commands executed."""
        return len(self.records)

    def get_recent(self, n: int = 5) -> List[CommandRecord]:
        """Get the N most recent commands.

        Args:
            n: Number of recent commands to return.

        Returns:
            List of the most recent CommandRecords.
        """
        return self.records[-n:] if n > 0 else []

    def get_failures(self) -> List[CommandRecord]:
        """Get all failed commands.

        Returns:
            List of CommandRecords where the command failed.
        """
        return [r for r in self.records if not r.result.success]

    def get_successes(self) -> List[CommandRecord]:
        """Get all successful commands.

        Returns:
            List of CommandRecords where the command succeeded.
        """
        return [r for r in self.records if r.result.success]

    def get_kubectl_commands(self) -> List[str]:
        """Get all kubectl commands (for AI context).

        Returns:
            List of command strings that start with 'kubectl'.
        """
        return [r.command for r in self.records if r.command.startswith("kubectl")]

    def format_for_ai_context(self, max_commands: int = 10) -> str:
        """Format history as context for AI assistance.

        Args:
            max_commands: Maximum number of recent commands to include.

        Returns:
            Formatted string suitable for including in AI prompts.
        """
        if not self.records:
            return "No commands executed yet."

        lines = ["Recent commands:"]
        for record in self.get_recent(max_commands):
            status = "OK" if record.result.success else "FAILED"
            lines.append(f"$ {record.command} [{status}]")

            if record.result.output:
                # Truncate long output
                output = record.result.output.strip()
                if len(output) > 200:
                    output = output[:200] + "..."
                # Indent output lines
                for line in output.split("\n")[:3]:  # Max 3 lines
                    lines.append(f"  {line}")

        return "\n".join(lines)

    def get_last_output(self) -> Optional[str]:
        """Get the output from the last command.

        Returns:
            The output string, or None if no commands executed.
        """
        if not self.records:
            return None
        return self.records[-1].result.output

    def get_last_error(self) -> Optional[str]:
        """Get the last error message.

        Returns:
            The error message from the last failed command, or None.
        """
        failures = self.get_failures()
        if not failures:
            return None
        return failures[-1].result.message

    def clear(self) -> None:
        """Clear command history."""
        self.records.clear()

    def get_summary(self) -> dict:
        """Get summary statistics of command history.

        Returns:
            Dictionary with command statistics.
        """
        return {
            "total_commands": len(self.records),
            "successful": len(self.get_successes()),
            "failed": len(self.get_failures()),
            "kubectl_commands": len(self.get_kubectl_commands()),
        }
