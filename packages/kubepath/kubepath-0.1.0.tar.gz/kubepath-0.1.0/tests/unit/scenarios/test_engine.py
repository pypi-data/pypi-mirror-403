"""Unit tests for scenario engine module."""

import pytest
from unittest.mock import patch, MagicMock
from dataclasses import dataclass

from kubepath.scenarios.engine import (
    ScenarioState,
    ScenarioResult,
    ScenarioContext,
    ScenarioEngine,
    create_scenario_engine,
)
from kubepath.k8s.deployer import DeployedResource, DeploymentResult
from kubepath.k8s.validator import ValidationResult
from kubepath.ai.gemini import GeminiHint


# Test fixtures
@pytest.fixture
def sample_scenario():
    """Create a sample scenario dict."""
    return {
        "id": "test-scenario-01",
        "title": "Fix the Broken Pod",
        "description": "The pod is failing to start due to an image issue.",
        "manifest": """apiVersion: v1
kind: Pod
metadata:
  name: broken-pod
spec:
  containers:
  - name: app
    image: nginx:wrong-tag
""",
        "hints": [
            "Check the pod events",
            "Look at the image name carefully",
            "Fix the image tag",
        ],
        "solution_validation": {
            "type": "resource_state",
            "resource": "pod/broken-pod",
            "state": "Running",
        },
        "points": 25,
        "hint_penalty": 5,
        "ai_hint_penalty": 2,
    }


@pytest.fixture
def scenario_no_manifest():
    """Create a scenario without manifest."""
    return {
        "id": "investigation-01",
        "title": "Find the Problem",
        "description": "Investigate the cluster issue.",
        "hints": ["Check the nodes"],
        "solution_validation": {"type": "command_output", "command": "kubectl get nodes", "contains": "Ready"},
        "points": 20,
    }


class TestScenarioState:
    """Tests for ScenarioState enum."""

    def test_all_states_exist(self):
        """Test all expected states are defined."""
        assert ScenarioState.NOT_STARTED.value == "not_started"
        assert ScenarioState.DEPLOYING.value == "deploying"
        assert ScenarioState.ACTIVE.value == "active"
        assert ScenarioState.VALIDATING.value == "validating"
        assert ScenarioState.COMPLETED.value == "completed"
        assert ScenarioState.FAILED.value == "failed"
        assert ScenarioState.SKIPPED.value == "skipped"


class TestScenarioResult:
    """Tests for ScenarioResult dataclass."""

    def test_result_creation(self):
        """Test creating a result."""
        result = ScenarioResult(
            scenario_id="test-01",
            success=True,
            points_earned=20,
            max_points=25,
            hints_used=1,
            ai_hints_used=0,
            hint_penalty=5,
            commands_executed=10,
        )
        assert result.scenario_id == "test-01"
        assert result.success is True
        assert result.points_earned == 20


class TestScenarioContext:
    """Tests for ScenarioContext dataclass."""

    def test_context_creation(self):
        """Test creating a context."""
        context = ScenarioContext(
            scenario_id="test",
            title="Test Scenario",
            description="A test",
            manifest="apiVersion: v1",
            solution_validation={"type": "command_output"},
            base_points=25,
            hint_penalty=5,
        )
        assert context.scenario_id == "test"
        assert context.state == ScenarioState.NOT_STARTED
        assert context.deployed_resources == []


class TestScenarioEngineInit:
    """Tests for ScenarioEngine initialization."""

    def test_init_without_gemini(self):
        """Test initialization without Gemini client."""
        engine = ScenarioEngine()
        assert engine.gemini_client is None
        assert engine.current_context is None

    def test_init_with_gemini(self):
        """Test initialization with Gemini client."""
        mock_client = MagicMock()
        engine = ScenarioEngine(gemini_client=mock_client)
        assert engine.gemini_client is mock_client


class TestStartScenario:
    """Tests for start_scenario method."""

    def test_start_with_manifest_success(self, sample_scenario):
        """Test starting scenario with successful deployment."""
        engine = ScenarioEngine()

        mock_deploy_result = DeploymentResult(
            success=True,
            message="Deployed",
            output="pod/broken-pod created",
            resources=[DeployedResource(kind="Pod", name="broken-pod")],
        )

        with patch("kubepath.scenarios.engine.deploy_manifest", return_value=mock_deploy_result):
            result = engine.start_scenario(sample_scenario)

            assert result.success is True
            assert engine.current_context is not None
            assert engine.current_context.state == ScenarioState.ACTIVE
            assert len(engine.current_context.deployed_resources) == 1

    def test_start_with_manifest_failure(self, sample_scenario):
        """Test starting scenario when deployment fails."""
        engine = ScenarioEngine()

        mock_deploy_result = DeploymentResult(
            success=False,
            message="kubectl apply failed",
            output="error: invalid manifest",
            resources=[],
        )

        with patch("kubepath.scenarios.engine.deploy_manifest", return_value=mock_deploy_result):
            result = engine.start_scenario(sample_scenario)

            assert result.success is False
            assert engine.current_context.state == ScenarioState.FAILED

    def test_start_without_manifest(self, scenario_no_manifest):
        """Test starting scenario without manifest."""
        engine = ScenarioEngine()

        result = engine.start_scenario(scenario_no_manifest)

        assert result.success is True
        assert "no manifest" in result.message.lower()
        assert engine.current_context.state == ScenarioState.ACTIVE

    def test_start_initializes_managers(self, sample_scenario):
        """Test that managers are initialized."""
        engine = ScenarioEngine()

        mock_result = DeploymentResult(success=True, message="OK", output="", resources=[])
        with patch("kubepath.scenarios.engine.deploy_manifest", return_value=mock_result):
            engine.start_scenario(sample_scenario)

            assert engine.current_context.hint_manager is not None
            assert engine.current_context.command_history is not None
            assert engine.current_context.cleanup_manager is not None


class TestExecuteLearnerCommand:
    """Tests for execute_learner_command method."""

    def test_execute_no_active_scenario(self):
        """Test executing command without active scenario."""
        engine = ScenarioEngine()
        result = engine.execute_learner_command("kubectl get pods")

        assert result.success is False
        assert "No active scenario" in result.message

    def test_execute_not_active_state(self, sample_scenario):
        """Test executing command when not in ACTIVE state."""
        engine = ScenarioEngine()
        engine.current_context = ScenarioContext(
            scenario_id="test",
            title="Test",
            description="",
            manifest="",
            solution_validation={},
            base_points=25,
            hint_penalty=5,
        )
        engine.current_context.state = ScenarioState.COMPLETED

        result = engine.execute_learner_command("kubectl get pods")

        assert result.success is False
        assert "not active" in result.message.lower()

    def test_execute_command_success(self, sample_scenario):
        """Test successful command execution."""
        engine = ScenarioEngine()

        mock_deploy = DeploymentResult(success=True, message="OK", output="", resources=[])
        mock_exec = ValidationResult(success=True, message="OK", output="pod/test Running")

        with patch("kubepath.scenarios.engine.deploy_manifest", return_value=mock_deploy):
            engine.start_scenario(sample_scenario)

        with patch("kubepath.scenarios.engine.execute_command", return_value=mock_exec):
            result = engine.execute_learner_command("kubectl get pods")

            assert result.success is True
            assert "Running" in result.output
            # Check command was recorded
            assert engine.current_context.command_history.command_count == 1


class TestValidateSolution:
    """Tests for validate_solution method."""

    def test_validate_no_scenario(self):
        """Test validation without scenario."""
        engine = ScenarioEngine()
        result = engine.validate_solution()

        assert result.success is False
        assert "No active scenario" in result.message

    def test_validate_success(self, sample_scenario):
        """Test successful validation."""
        engine = ScenarioEngine()

        mock_deploy = DeploymentResult(success=True, message="OK", output="", resources=[])
        mock_validate = ValidationResult(success=True, message="Pod is Running", output="")

        with patch("kubepath.scenarios.engine.deploy_manifest", return_value=mock_deploy):
            engine.start_scenario(sample_scenario)

        with patch("kubepath.scenarios.engine.validate_from_spec", return_value=mock_validate):
            result = engine.validate_solution()

            assert result.success is True
            assert engine.current_context.state == ScenarioState.COMPLETED

    def test_validate_failure_returns_to_active(self, sample_scenario):
        """Test that failed validation returns to ACTIVE state."""
        engine = ScenarioEngine()

        mock_deploy = DeploymentResult(success=True, message="OK", output="", resources=[])
        mock_validate = ValidationResult(success=False, message="Pod not running", output="")

        with patch("kubepath.scenarios.engine.deploy_manifest", return_value=mock_deploy):
            engine.start_scenario(sample_scenario)

        with patch("kubepath.scenarios.engine.validate_from_spec", return_value=mock_validate):
            result = engine.validate_solution()

            assert result.success is False
            assert engine.current_context.state == ScenarioState.ACTIVE


class TestGetHint:
    """Tests for get_hint method."""

    def test_get_hint_no_scenario(self):
        """Test getting hint without scenario."""
        engine = ScenarioEngine()
        result = engine.get_hint()
        assert result is None

    def test_get_hint_success(self, sample_scenario):
        """Test getting a hint."""
        engine = ScenarioEngine()

        mock_deploy = DeploymentResult(success=True, message="OK", output="", resources=[])
        with patch("kubepath.scenarios.engine.deploy_manifest", return_value=mock_deploy):
            engine.start_scenario(sample_scenario)

        hint = engine.get_hint()

        assert hint is not None
        assert hint["text"] == "Check the pod events"
        assert hint["number"] == 1
        assert hint["total"] == 3
        assert hint["penalty"] == 5
        assert hint["has_more"] is True

    def test_get_hint_no_more_hints(self, sample_scenario):
        """Test getting hint when none left."""
        engine = ScenarioEngine()

        mock_deploy = DeploymentResult(success=True, message="OK", output="", resources=[])
        with patch("kubepath.scenarios.engine.deploy_manifest", return_value=mock_deploy):
            engine.start_scenario(sample_scenario)

        # Use all hints
        engine.get_hint()
        engine.get_hint()
        engine.get_hint()

        # Should return None
        result = engine.get_hint()
        assert result is None


class TestGetAIHint:
    """Tests for get_ai_hint method."""

    def test_get_ai_hint_no_scenario(self):
        """Test AI hint without scenario."""
        engine = ScenarioEngine()
        result = engine.get_ai_hint()
        assert result is None

    def test_get_ai_hint_not_available(self, sample_scenario):
        """Test AI hint when Gemini not available."""
        mock_client = MagicMock()
        mock_client.is_available = False

        engine = ScenarioEngine(gemini_client=mock_client)

        mock_deploy = DeploymentResult(success=True, message="OK", output="", resources=[])
        with patch("kubepath.scenarios.engine.deploy_manifest", return_value=mock_deploy):
            engine.start_scenario(sample_scenario)

        result = engine.get_ai_hint()
        assert result is None

    def test_get_ai_hint_success(self, sample_scenario):
        """Test successful AI hint."""
        mock_hint = GeminiHint(
            hint_text="Check the image tag",
            suggested_commands=["kubectl describe pod broken-pod"],
            confidence=0.9,
        )
        mock_client = MagicMock()
        mock_client.is_available = True
        mock_client.get_debugging_hint.return_value = mock_hint

        engine = ScenarioEngine(gemini_client=mock_client)

        mock_deploy = DeploymentResult(success=True, message="OK", output="", resources=[])
        with patch("kubepath.scenarios.engine.deploy_manifest", return_value=mock_deploy):
            engine.start_scenario(sample_scenario)

        result = engine.get_ai_hint("ImagePullBackOff")

        assert result is not None
        assert result.hint_text == "Check the image tag"
        # Check AI hint was recorded
        assert engine.current_context.hint_manager.ai_hints_used == 1


class TestCalculateScore:
    """Tests for calculate_score method."""

    def test_calculate_score_no_scenario(self):
        """Test score calculation without scenario."""
        engine = ScenarioEngine()
        assert engine.calculate_score() == 0

    def test_calculate_score_not_completed(self, sample_scenario):
        """Test score when scenario not completed."""
        engine = ScenarioEngine()

        mock_deploy = DeploymentResult(success=True, message="OK", output="", resources=[])
        with patch("kubepath.scenarios.engine.deploy_manifest", return_value=mock_deploy):
            engine.start_scenario(sample_scenario)

        assert engine.calculate_score() == 0

    def test_calculate_score_no_hints(self, sample_scenario):
        """Test score with no hints used."""
        engine = ScenarioEngine()

        mock_deploy = DeploymentResult(success=True, message="OK", output="", resources=[])
        mock_validate = ValidationResult(success=True, message="OK", output="")

        with patch("kubepath.scenarios.engine.deploy_manifest", return_value=mock_deploy):
            engine.start_scenario(sample_scenario)

        with patch("kubepath.scenarios.engine.validate_from_spec", return_value=mock_validate):
            engine.validate_solution()

        assert engine.calculate_score() == 25

    def test_calculate_score_with_hints(self, sample_scenario):
        """Test score with hints used."""
        engine = ScenarioEngine()

        mock_deploy = DeploymentResult(success=True, message="OK", output="", resources=[])
        mock_validate = ValidationResult(success=True, message="OK", output="")

        with patch("kubepath.scenarios.engine.deploy_manifest", return_value=mock_deploy):
            engine.start_scenario(sample_scenario)

        # Use 2 hints (10 point penalty)
        engine.get_hint()
        engine.get_hint()

        with patch("kubepath.scenarios.engine.validate_from_spec", return_value=mock_validate):
            engine.validate_solution()

        assert engine.calculate_score() == 15


class TestGetResult:
    """Tests for get_result method."""

    def test_get_result_no_scenario(self):
        """Test getting result without scenario."""
        engine = ScenarioEngine()
        assert engine.get_result() is None

    def test_get_result_completed(self, sample_scenario):
        """Test getting result after completion."""
        engine = ScenarioEngine()

        mock_deploy = DeploymentResult(success=True, message="OK", output="", resources=[])
        mock_validate = ValidationResult(success=True, message="OK", output="")
        mock_exec = ValidationResult(success=True, message="OK", output="output")

        with patch("kubepath.scenarios.engine.deploy_manifest", return_value=mock_deploy):
            engine.start_scenario(sample_scenario)

        with patch("kubepath.scenarios.engine.execute_command", return_value=mock_exec):
            engine.execute_learner_command("kubectl get pods")

        engine.get_hint()  # Use 1 hint

        with patch("kubepath.scenarios.engine.validate_from_spec", return_value=mock_validate):
            engine.validate_solution()

        result = engine.get_result()

        assert result.scenario_id == "test-scenario-01"
        assert result.success is True
        assert result.points_earned == 20
        assert result.max_points == 25
        assert result.hints_used == 1
        assert result.commands_executed == 1


class TestSkipScenario:
    """Tests for skip_scenario method."""

    def test_skip_scenario(self, sample_scenario):
        """Test skipping a scenario."""
        engine = ScenarioEngine()

        mock_deploy = DeploymentResult(
            success=True,
            message="OK",
            output="",
            resources=[DeployedResource(kind="Pod", name="test")],
        )

        with patch("kubepath.scenarios.engine.deploy_manifest", return_value=mock_deploy):
            engine.start_scenario(sample_scenario)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="deleted")
            engine.skip_scenario()

        assert engine.current_context.state == ScenarioState.SKIPPED


class TestCleanup:
    """Tests for cleanup method."""

    def test_cleanup_no_scenario(self):
        """Test cleanup without scenario."""
        engine = ScenarioEngine()
        assert engine.cleanup() is True

    def test_cleanup_with_resources(self, sample_scenario):
        """Test cleanup with deployed resources."""
        engine = ScenarioEngine()

        mock_deploy = DeploymentResult(
            success=True,
            message="OK",
            output="",
            resources=[DeployedResource(kind="Pod", name="test-pod")],
        )

        with patch("kubepath.scenarios.engine.deploy_manifest", return_value=mock_deploy):
            engine.start_scenario(sample_scenario)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="deleted")
            result = engine.cleanup()

        assert result is True


class TestProperties:
    """Tests for engine properties."""

    def test_is_active_no_scenario(self):
        """Test is_active without scenario."""
        engine = ScenarioEngine()
        assert engine.is_active is False

    def test_is_active_true(self, sample_scenario):
        """Test is_active when scenario active."""
        engine = ScenarioEngine()

        mock_deploy = DeploymentResult(success=True, message="OK", output="", resources=[])
        with patch("kubepath.scenarios.engine.deploy_manifest", return_value=mock_deploy):
            engine.start_scenario(sample_scenario)

        assert engine.is_active is True

    def test_is_completed_true(self, sample_scenario):
        """Test is_completed when scenario completed."""
        engine = ScenarioEngine()

        mock_deploy = DeploymentResult(success=True, message="OK", output="", resources=[])
        mock_validate = ValidationResult(success=True, message="OK", output="")

        with patch("kubepath.scenarios.engine.deploy_manifest", return_value=mock_deploy):
            engine.start_scenario(sample_scenario)

        with patch("kubepath.scenarios.engine.validate_from_spec", return_value=mock_validate):
            engine.validate_solution()

        assert engine.is_completed is True


class TestGetStatus:
    """Tests for get_status method."""

    def test_get_status_no_scenario(self):
        """Test status without scenario."""
        engine = ScenarioEngine()
        status = engine.get_status()
        assert status["active"] is False

    def test_get_status_active(self, sample_scenario):
        """Test status with active scenario."""
        engine = ScenarioEngine()

        mock_deploy = DeploymentResult(
            success=True,
            message="OK",
            output="",
            resources=[DeployedResource(kind="Pod", name="test")],
        )

        with patch("kubepath.scenarios.engine.deploy_manifest", return_value=mock_deploy):
            engine.start_scenario(sample_scenario)

        engine.get_hint()  # Use one hint

        status = engine.get_status()

        assert status["active"] is True
        assert status["scenario_id"] == "test-scenario-01"
        assert status["title"] == "Fix the Broken Pod"
        assert status["state"] == "active"
        assert status["hints_used"] == 1
        assert status["hints_remaining"] == 2
        assert status["resources_deployed"] == 1


class TestCreateScenarioEngine:
    """Tests for create_scenario_engine factory function."""

    def test_create_with_ai(self):
        """Test creating engine with AI enabled."""
        with patch("kubepath.scenarios.engine.get_gemini_client") as mock_get:
            mock_client = MagicMock()
            mock_get.return_value = mock_client

            engine = create_scenario_engine(enable_ai=True)

            assert engine.gemini_client is mock_client

    def test_create_without_ai(self):
        """Test creating engine with AI disabled."""
        engine = create_scenario_engine(enable_ai=False)
        assert engine.gemini_client is None
