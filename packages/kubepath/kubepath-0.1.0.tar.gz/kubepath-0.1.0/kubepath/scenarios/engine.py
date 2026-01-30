"""Core scenario engine for debugging challenges."""

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

import yaml

from kubepath.k8s.deployer import (
    DeployedResource,
    DeploymentResult,
    deploy_manifest,
)
from kubepath.k8s.validator import (
    ValidationResult,
    execute_command,
    validate_from_spec,
)
from kubepath.scenarios.cleanup import CleanupManager
from kubepath.scenarios.hints import HintManager
from kubepath.scenarios.history import CommandHistory
from kubepath.ai.gemini import GeminiClient, GeminiHint, get_gemini_client


def has_yaml_content(manifest: str) -> bool:
    """Check if manifest has actual YAML content (not just comments).

    Args:
        manifest: YAML manifest string.

    Returns:
        True if the manifest contains actual YAML documents with content.
    """
    if not manifest or not manifest.strip():
        return False

    try:
        docs = list(yaml.safe_load_all(manifest))
        return any(doc is not None for doc in docs)
    except yaml.YAMLError:
        return False


class ScenarioState(Enum):
    """Current state of a scenario."""

    NOT_STARTED = "not_started"
    DEPLOYING = "deploying"
    ACTIVE = "active"  # Learner is investigating
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class ScenarioResult:
    """Result of completing a scenario."""

    scenario_id: str
    success: bool
    points_earned: int
    max_points: int
    hints_used: int
    ai_hints_used: int
    hint_penalty: int
    commands_executed: int


@dataclass
class ScenarioContext:
    """Runtime context for an active scenario."""

    scenario_id: str
    title: str
    description: str
    manifest: str
    solution_validation: Dict[str, Any]
    base_points: int
    hint_penalty: int

    state: ScenarioState = ScenarioState.NOT_STARTED
    deployed_resources: List[DeployedResource] = field(default_factory=list)
    hint_manager: Optional[HintManager] = None
    command_history: Optional[CommandHistory] = None
    cleanup_manager: Optional[CleanupManager] = None


class ScenarioEngine:
    """Orchestrates scenario deployment, validation, and cleanup.

    The main orchestrator for debugging scenarios. Handles:
    - Deploying broken manifests to the cluster
    - Executing learner commands
    - Validating solutions
    - Managing hints (static and AI)
    - Cleanup of deployed resources

    Example:
        engine = ScenarioEngine()
        result = engine.start_scenario(scenario_dict)
        if result.success:
            # Scenario is active, learner can investigate
            cmd_result = engine.execute_learner_command("kubectl get pods")
            # ...
            validation = engine.validate_solution()
            if validation.success:
                score = engine.calculate_score()
            engine.cleanup()
    """

    def __init__(
        self,
        gemini_client: Optional[GeminiClient] = None,
    ):
        """Initialize the scenario engine.

        Args:
            gemini_client: Optional Gemini client for AI hints.
        """
        self.gemini_client = gemini_client
        self.current_context: Optional[ScenarioContext] = None

    def start_scenario(self, scenario: Dict[str, Any]) -> ValidationResult:
        """Start a new scenario.

        Deploys the broken manifest and sets up tracking.

        Args:
            scenario: Scenario dict from chapter YAML with keys:
                - id: Unique scenario identifier
                - title: Display title
                - description: Problem description
                - manifest: YAML manifest to deploy
                - hints: List of hint strings
                - solution_validation: Validation spec dict
                - points: Base points (default 25)
                - hint_penalty: Points per hint (default 5)

        Returns:
            ValidationResult indicating if deployment succeeded.
        """
        # Create context
        self.current_context = ScenarioContext(
            scenario_id=scenario["id"],
            title=scenario["title"],
            description=scenario.get("description", ""),
            manifest=scenario.get("manifest", ""),
            solution_validation=scenario.get("solution_validation", {}),
            base_points=scenario.get("points", 25),
            hint_penalty=scenario.get("hint_penalty", 5),
        )

        # Initialize managers
        hints = scenario.get("hints", [])
        self.current_context.hint_manager = HintManager(
            hints=hints,
            hint_penalty=scenario.get("hint_penalty", 5),
            ai_hint_penalty=scenario.get("ai_hint_penalty", 2),
        )
        self.current_context.command_history = CommandHistory()
        self.current_context.cleanup_manager = CleanupManager()

        # Check if there's a manifest to deploy (actual YAML content, not just comments)
        manifest = scenario.get("manifest", "")
        if not has_yaml_content(manifest):
            # No manifest or only comments - just activate for investigation scenarios
            self.current_context.state = ScenarioState.ACTIVE
            return ValidationResult(
                success=True,
                message="Scenario started (no manifest to deploy)",
                output="",
            )

        # Deploy the broken manifest
        self.current_context.state = ScenarioState.DEPLOYING

        deploy_result = deploy_manifest(
            manifest_yaml=manifest,
            namespace=scenario.get("namespace", "default"),
        )

        if deploy_result.success:
            self.current_context.deployed_resources = deploy_result.resources
            self.current_context.cleanup_manager.register(deploy_result.resources)
            self.current_context.state = ScenarioState.ACTIVE

            return ValidationResult(
                success=True,
                message="Scenario deployed successfully",
                output=deploy_result.output,
            )
        else:
            self.current_context.state = ScenarioState.FAILED

            # Improve error message for kubectl PATH issues
            message = deploy_result.message
            if "not found" in message.lower() or "command not found" in message.lower():
                message = (
                    "kubectl not found. If you just installed kubectl, "
                    "close this terminal and open a new one to update your PATH."
                )

            return ValidationResult(
                success=False,
                message=message,
                output=deploy_result.output,
            )

    def execute_learner_command(self, command: str) -> ValidationResult:
        """Execute a command typed by the learner.

        Records the command in history for AI context.

        Args:
            command: The kubectl (or other) command to run.

        Returns:
            ValidationResult with command output.
        """
        if not self.current_context:
            return ValidationResult(
                success=False,
                message="No active scenario",
                output="",
            )

        if self.current_context.state != ScenarioState.ACTIVE:
            return ValidationResult(
                success=False,
                message=f"Scenario not active (state: {self.current_context.state.value})",
                output="",
            )

        start = time.time()
        result = execute_command(command)
        duration_ms = int((time.time() - start) * 1000)

        # Record in history
        self.current_context.command_history.add(command, result, duration_ms)

        return result

    def validate_solution(self) -> ValidationResult:
        """Check if the learner has fixed the scenario.

        Uses the solution_validation spec to check the cluster state.

        Returns:
            ValidationResult indicating if the fix is correct.
        """
        if not self.current_context:
            return ValidationResult(
                success=False,
                message="No active scenario",
                output="",
            )

        validation_spec = self.current_context.solution_validation
        if not validation_spec:
            return ValidationResult(
                success=False,
                message="No validation spec defined for this scenario",
                output="",
            )

        self.current_context.state = ScenarioState.VALIDATING
        result = validate_from_spec(validation_spec)

        if result.success:
            self.current_context.state = ScenarioState.COMPLETED
        else:
            self.current_context.state = ScenarioState.ACTIVE

        return result

    def get_hint(self) -> Optional[Dict[str, Any]]:
        """Get the next static hint.

        Returns:
            Dict with hint info (text, number, total, penalty, has_more),
            or None if no hints left.
        """
        if not self.current_context or not self.current_context.hint_manager:
            return None

        hint_result = self.current_context.hint_manager.get_next_hint()
        if not hint_result:
            return None

        return {
            "text": hint_result.hint_text,
            "number": hint_result.hint_number,
            "total": hint_result.total_hints,
            "penalty": hint_result.penalty_applied,
            "has_more": hint_result.has_more_hints,
        }

    def get_ai_hint(self, current_error: str = "") -> Optional[GeminiHint]:
        """Get an AI-powered hint from Gemini.

        Args:
            current_error: Current error message or cluster state.

        Returns:
            GeminiHint with AI suggestions, or None if unavailable.
        """
        if not self.current_context:
            return None

        # Get or create Gemini client
        client = self.gemini_client or get_gemini_client()
        if not client.is_available:
            return None

        # Build context from command history
        history = self.current_context.command_history.format_for_ai_context()

        # Get AI hint
        hint = client.get_debugging_hint(
            scenario_description=self.current_context.description,
            manifest=self.current_context.manifest,
            command_history=history,
            current_error=current_error or self.current_context.command_history.get_last_error() or "",
        )

        if hint:
            # Record AI hint usage for scoring
            self.current_context.hint_manager.record_ai_hint()

        return hint

    def calculate_score(self) -> int:
        """Calculate the final score for the scenario.

        Returns:
            Final score after hint penalties (minimum 0).
        """
        if not self.current_context:
            return 0

        if self.current_context.state != ScenarioState.COMPLETED:
            return 0

        return self.current_context.hint_manager.calculate_final_score(
            self.current_context.base_points
        )

    def get_result(self) -> Optional[ScenarioResult]:
        """Get the final result for the scenario.

        Returns:
            ScenarioResult with all statistics, or None if no scenario.
        """
        if not self.current_context:
            return None

        return ScenarioResult(
            scenario_id=self.current_context.scenario_id,
            success=self.current_context.state == ScenarioState.COMPLETED,
            points_earned=self.calculate_score(),
            max_points=self.current_context.base_points,
            hints_used=self.current_context.hint_manager.hints_used,
            ai_hints_used=self.current_context.hint_manager.ai_hints_used,
            hint_penalty=self.current_context.hint_manager.total_penalty,
            commands_executed=self.current_context.command_history.command_count,
        )

    def skip_scenario(self) -> None:
        """Skip the current scenario without completing."""
        if self.current_context:
            self.current_context.state = ScenarioState.SKIPPED
            self.cleanup()

    def cleanup(self) -> bool:
        """Clean up all resources from the current scenario.

        Returns:
            True if cleanup succeeded.
        """
        if not self.current_context:
            return True

        if not self.current_context.cleanup_manager:
            return True

        return self.current_context.cleanup_manager.cleanup(force=True)

    @property
    def is_active(self) -> bool:
        """Check if a scenario is currently active.

        Returns:
            True if a scenario is in ACTIVE state.
        """
        return (
            self.current_context is not None
            and self.current_context.state == ScenarioState.ACTIVE
        )

    @property
    def is_completed(self) -> bool:
        """Check if the current scenario is completed.

        Returns:
            True if scenario is in COMPLETED state.
        """
        return (
            self.current_context is not None
            and self.current_context.state == ScenarioState.COMPLETED
        )

    def get_status(self) -> Dict[str, Any]:
        """Get current scenario status.

        Returns:
            Dictionary with scenario status information.
        """
        if not self.current_context:
            return {"active": False}

        return {
            "active": True,
            "scenario_id": self.current_context.scenario_id,
            "title": self.current_context.title,
            "state": self.current_context.state.value,
            "hints_used": self.current_context.hint_manager.hints_used if self.current_context.hint_manager else 0,
            "hints_remaining": self.current_context.hint_manager.hints_remaining if self.current_context.hint_manager else 0,
            "commands_executed": self.current_context.command_history.command_count if self.current_context.command_history else 0,
            "resources_deployed": len(self.current_context.deployed_resources),
        }

    def get_command_history_for_persistence(self) -> List[Dict[str, Any]]:
        """Get command history in a format suitable for JSON persistence.

        Returns last 10 commands to keep size reasonable.

        Returns:
            List of command dicts with command, success, and output.
        """
        if not self.current_context or not self.current_context.command_history:
            return []

        recent = self.current_context.command_history.get_recent(10)
        return [
            {
                "command": r.command,
                "success": r.result.success,
                "output": r.result.output[:200] if r.result.output else "",
            }
            for r in recent
        ]

    def restore_hint_state(self, hints_used: int, ai_hints_used: int) -> None:
        """Restore hint manager state when resuming a scenario.

        Args:
            hints_used: Number of static hints already used.
            ai_hints_used: Number of AI hints already used.
        """
        if self.current_context and self.current_context.hint_manager:
            self.current_context.hint_manager._hints_used = hints_used
            self.current_context.hint_manager._ai_hints_used = ai_hints_used

    def restore_command_history(self, history: List[Dict[str, Any]]) -> None:
        """Restore command history for AI context when resuming.

        Args:
            history: List of command dicts with command, success, output.
        """
        if not self.current_context or not self.current_context.command_history:
            return

        for entry in history:
            # Create minimal ValidationResult for history
            result = ValidationResult(
                success=entry.get("success", False),
                message="",
                output=entry.get("output", ""),
            )
            self.current_context.command_history.add(
                entry.get("command", ""), result, duration_ms=0
            )


def create_scenario_engine(
    enable_ai: bool = True,
) -> ScenarioEngine:
    """Create a configured ScenarioEngine.

    Args:
        enable_ai: Whether to enable Gemini AI hints.

    Returns:
        Configured ScenarioEngine instance.
    """
    gemini = get_gemini_client() if enable_ai else None
    return ScenarioEngine(gemini_client=gemini)
