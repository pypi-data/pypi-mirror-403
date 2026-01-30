"""Unit tests for Gemini client module."""

import pytest
from unittest.mock import patch, MagicMock

from kubepath.ai.gemini import (
    GeminiHint,
    GeminiClient,
    get_gemini_client,
    reset_gemini_client,
    GEMINI_AVAILABLE,
)


class TestGeminiHint:
    """Tests for GeminiHint dataclass."""

    def test_hint_creation(self):
        """Test creating a hint."""
        hint = GeminiHint(
            hint_text="Check the image name",
            suggested_commands=["kubectl describe pod test", "kubectl get events"],
            confidence=0.9,
        )
        assert hint.hint_text == "Check the image name"
        assert len(hint.suggested_commands) == 2
        assert hint.confidence == 0.9

    def test_hint_default_confidence(self):
        """Test default confidence value."""
        hint = GeminiHint(hint_text="Test", suggested_commands=[])
        assert hint.confidence == 0.8


class TestGeminiClient:
    """Tests for GeminiClient class."""

    def test_init_with_api_key(self):
        """Test initialization with explicit API key."""
        client = GeminiClient(api_key="test-key")
        assert client.api_key == "test-key"

    def test_init_from_config(self, tmp_path):
        """Test initialization from config."""
        with patch("kubepath.ai.gemini.get_gemini_api_key", return_value="config-key"):
            client = GeminiClient()
            assert client.api_key == "config-key"

    def test_is_available_with_key(self):
        """Test is_available when API key is set."""
        if not GEMINI_AVAILABLE:
            pytest.skip("google-genai not installed")

        client = GeminiClient(api_key="test-key")
        assert client.is_available is True

    def test_is_available_without_key(self):
        """Test is_available when no API key."""
        with patch("kubepath.ai.gemini.get_gemini_api_key", return_value=None):
            client = GeminiClient()
            assert client.is_available is False

    def test_configure_without_availability(self):
        """Test configure when not available."""
        with patch("kubepath.ai.gemini.get_gemini_api_key", return_value=None):
            client = GeminiClient()
            result = client.configure()
            assert result is False

    @patch("kubepath.ai.gemini.GEMINI_AVAILABLE", True)
    @patch("kubepath.ai.gemini.genai")
    def test_configure_success(self, mock_genai):
        """Test successful configuration."""
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client

        client = GeminiClient(api_key="test-key")
        result = client.configure()

        assert result is True
        assert client._configured is True
        mock_genai.Client.assert_called_once_with(api_key="test-key")

    @patch("kubepath.ai.gemini.GEMINI_AVAILABLE", True)
    @patch("kubepath.ai.gemini.genai")
    def test_configure_failure(self, mock_genai):
        """Test configuration failure."""
        mock_genai.Client.side_effect = Exception("API Error")

        client = GeminiClient(api_key="test-key")
        result = client.configure()

        assert result is False

    def test_validate_api_key_no_package(self):
        """Test validate when package not installed."""
        with patch("kubepath.ai.gemini.GEMINI_AVAILABLE", False):
            client = GeminiClient(api_key="key")
            success, msg = client.validate_api_key()
            assert success is False
            assert "not installed" in msg

    def test_validate_api_key_no_key(self):
        """Test validate when no API key."""
        with patch("kubepath.ai.gemini.get_gemini_api_key", return_value=None):
            client = GeminiClient()
            success, msg = client.validate_api_key()
            assert success is False
            assert "No API key" in msg

    @patch("kubepath.ai.gemini.GEMINI_AVAILABLE", True)
    @patch("kubepath.ai.gemini.genai")
    def test_validate_api_key_success(self, mock_genai):
        """Test successful API key validation."""
        mock_response = MagicMock()
        mock_response.text = "OK"
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client

        client = GeminiClient(api_key="valid-key")
        success, msg = client.validate_api_key()

        assert success is True
        assert "valid" in msg.lower()

    @patch("kubepath.ai.gemini.GEMINI_AVAILABLE", True)
    @patch("kubepath.ai.gemini.genai")
    def test_validate_api_key_invalid(self, mock_genai):
        """Test invalid API key."""
        mock_genai.Client.side_effect = Exception("API_KEY_INVALID")

        client = GeminiClient(api_key="bad-key")
        success, msg = client.validate_api_key()

        assert success is False
        assert "Invalid" in msg

    @patch("kubepath.ai.gemini.GEMINI_AVAILABLE", True)
    @patch("kubepath.ai.gemini.genai")
    def test_validate_api_key_quota_exceeded(self, mock_genai):
        """Test quota exceeded error."""
        mock_genai.Client.side_effect = Exception("QUOTA exceeded")

        client = GeminiClient(api_key="key")
        success, msg = client.validate_api_key()

        assert success is False
        assert "quota" in msg.lower()

    def test_get_debugging_hint_not_configured(self):
        """Test get_debugging_hint when not configured."""
        with patch("kubepath.ai.gemini.get_gemini_api_key", return_value=None):
            client = GeminiClient()
            result = client.get_debugging_hint(
                scenario_description="Test",
                manifest="apiVersion: v1",
                command_history="$ kubectl get pods",
                current_error="Error",
            )
            assert result is None

    @patch("kubepath.ai.gemini.GEMINI_AVAILABLE", True)
    @patch("kubepath.ai.gemini.genai")
    def test_get_debugging_hint_success(self, mock_genai):
        """Test successful debugging hint."""
        mock_response = MagicMock()
        mock_response.text = "HINT: Check the image name carefully.\nCOMMANDS: kubectl describe pod test, kubectl get events"
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client

        client = GeminiClient(api_key="key")
        result = client.get_debugging_hint(
            scenario_description="Pod won't start",
            manifest="apiVersion: v1",
            command_history="$ kubectl get pods",
            current_error="ImagePullBackOff",
        )

        assert result is not None
        assert "image" in result.hint_text.lower()
        assert len(result.suggested_commands) == 2

    @patch("kubepath.ai.gemini.GEMINI_AVAILABLE", True)
    @patch("kubepath.ai.gemini.genai")
    def test_get_debugging_hint_api_error(self, mock_genai):
        """Test debugging hint when API fails."""
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("API Error")
        mock_genai.Client.return_value = mock_client

        client = GeminiClient(api_key="key")
        client._configured = True
        client._client = mock_client

        result = client.get_debugging_hint(
            scenario_description="Test",
            manifest="yaml",
            command_history="",
            current_error="",
        )

        assert result is None


class TestParseHintResponse:
    """Tests for _parse_hint_response method."""

    def test_parse_valid_response(self):
        """Test parsing valid formatted response."""
        client = GeminiClient(api_key="key")
        response = "HINT: Check the pod logs.\nCOMMANDS: kubectl logs pod-1, kubectl describe pod pod-1"

        hint = client._parse_hint_response(response)

        assert hint.hint_text == "Check the pod logs."
        assert "kubectl logs pod-1" in hint.suggested_commands
        assert "kubectl describe pod pod-1" in hint.suggested_commands

    def test_parse_response_no_commands(self):
        """Test parsing response without commands section."""
        client = GeminiClient(api_key="key")
        response = "HINT: Just check the logs."

        hint = client._parse_hint_response(response)

        assert hint.hint_text == "Just check the logs."
        assert hint.suggested_commands == []

    def test_parse_unformatted_response(self):
        """Test parsing unformatted response."""
        client = GeminiClient(api_key="key")
        response = "This is an unformatted response about debugging"

        hint = client._parse_hint_response(response)

        # Should use full text as hint
        assert "debugging" in hint.hint_text


class TestAnalyzeError:
    """Tests for analyze_error method."""

    def test_analyze_not_configured(self):
        """Test analyze when not configured."""
        with patch("kubepath.ai.gemini.get_gemini_api_key", return_value=None):
            client = GeminiClient()
            result = client.analyze_error("Error output", "pod")
            assert result is None

    @patch("kubepath.ai.gemini.GEMINI_AVAILABLE", True)
    @patch("kubepath.ai.gemini.genai")
    def test_analyze_success(self, mock_genai):
        """Test successful error analysis."""
        mock_response = MagicMock()
        mock_response.text = "The pod can't pull the image due to invalid name."
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client

        client = GeminiClient(api_key="key")
        result = client.analyze_error("ImagePullBackOff", "pod")

        assert result is not None
        assert "image" in result.lower()


class TestSingletonFunctions:
    """Tests for singleton management functions."""

    def test_get_gemini_client(self):
        """Test getting singleton client."""
        reset_gemini_client()  # Clean state

        client1 = get_gemini_client()
        client2 = get_gemini_client()

        assert client1 is client2

    def test_reset_gemini_client(self):
        """Test resetting singleton."""
        client1 = get_gemini_client()
        reset_gemini_client()
        client2 = get_gemini_client()

        assert client1 is not client2


class TestBuildDebuggingPrompt:
    """Tests for _build_debugging_prompt method."""

    def test_prompt_includes_scenario(self):
        """Test that prompt includes scenario info."""
        client = GeminiClient(api_key="key")
        prompt = client._build_debugging_prompt(
            description="Pod won't start",
            manifest="apiVersion: v1\nkind: Pod",
            history="$ kubectl get pods",
            error="CrashLoopBackOff",
        )

        assert "Pod won't start" in prompt
        assert "apiVersion: v1" in prompt
        assert "kubectl get pods" in prompt
        assert "CrashLoopBackOff" in prompt
        assert "HINT:" in prompt  # Format instructions

    def test_prompt_truncates_long_content(self):
        """Test that long content is truncated."""
        client = GeminiClient(api_key="key")
        long_manifest = "x" * 3000

        prompt = client._build_debugging_prompt(
            description="Test",
            manifest=long_manifest,
            history="",
            error="",
        )

        # Manifest should be truncated to 1500 chars
        assert len(prompt) < len(long_manifest)


class TestAnswerQuestion:
    """Tests for answer_question method."""

    def test_answer_not_configured(self):
        """Test answer_question when not configured."""
        with patch("kubepath.ai.gemini.get_gemini_api_key", return_value=None):
            client = GeminiClient()
            result = client.answer_question(
                context_title="What is a Pod?",
                context_content="A Pod is the smallest unit...",
                learner_question="What's the difference?",
                section_type="concept",
            )
            assert result is None

    @patch("kubepath.ai.gemini.GEMINI_AVAILABLE", True)
    @patch("kubepath.ai.gemini.genai")
    def test_answer_success(self, mock_genai):
        """Test successful question answering."""
        mock_response = MagicMock()
        mock_response.text = "A Pod can hold multiple containers that share resources."
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client

        client = GeminiClient(api_key="key")
        result = client.answer_question(
            context_title="What is a Pod?",
            context_content="A Pod is the smallest deployable unit in Kubernetes.",
            learner_question="Can a Pod have multiple containers?",
            section_type="concept",
        )

        assert result is not None
        assert "containers" in result.lower()

    @patch("kubepath.ai.gemini.GEMINI_AVAILABLE", True)
    @patch("kubepath.ai.gemini.genai")
    def test_answer_practice_type(self, mock_genai):
        """Test answer_question with practice section type."""
        mock_response = MagicMock()
        mock_response.text = "Use kubectl get pods to list all pods."
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client

        client = GeminiClient(api_key="key")
        result = client.answer_question(
            context_title="List Pods",
            context_content="Practice listing pods in the cluster.",
            learner_question="How do I see running pods?",
            section_type="practice",
        )

        assert result is not None
        assert "kubectl" in result.lower()

    @patch("kubepath.ai.gemini.GEMINI_AVAILABLE", True)
    @patch("kubepath.ai.gemini.genai")
    def test_answer_api_error(self, mock_genai):
        """Test answer_question when API fails."""
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("API Error")
        mock_genai.Client.return_value = mock_client

        client = GeminiClient(api_key="key")
        client._configured = True
        client._client = mock_client

        result = client.answer_question(
            context_title="Test",
            context_content="Content",
            learner_question="Question?",
        )

        assert result is None

    @patch("kubepath.ai.gemini.GEMINI_AVAILABLE", True)
    @patch("kubepath.ai.gemini.genai")
    def test_answer_truncates_long_response(self, mock_genai):
        """Test that long answers are truncated."""
        mock_response = MagicMock()
        mock_response.text = "x" * 1000  # Long response
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client

        client = GeminiClient(api_key="key")
        result = client.answer_question(
            context_title="Test",
            context_content="Content",
            learner_question="Question?",
        )

        assert result is not None
        assert len(result) <= 500


# ============================================================================
# Rate Limit Fallback Tests
# ============================================================================


class TestRateLimitDetection:
    """Tests for rate limit error detection."""

    def test_detects_429_error(self):
        """Test detection of 429 rate limit error."""
        client = GeminiClient(api_key="key")
        error = Exception("Error 429: Too many requests")
        assert client._is_rate_limit_error(error) is True

    def test_detects_resource_exhausted(self):
        """Test detection of RESOURCE_EXHAUSTED error."""
        client = GeminiClient(api_key="key")
        error = Exception("RESOURCE_EXHAUSTED: Quota exceeded")
        assert client._is_rate_limit_error(error) is True

    def test_detects_quota_error(self):
        """Test detection of quota error."""
        client = GeminiClient(api_key="key")
        error = Exception("API quota limit reached")
        assert client._is_rate_limit_error(error) is True

    def test_detects_rate_limit_message(self):
        """Test detection of rate limit message."""
        client = GeminiClient(api_key="key")
        error = Exception("Rate limit exceeded, try again later")
        assert client._is_rate_limit_error(error) is True

    def test_non_rate_limit_error(self):
        """Test that non-rate-limit errors are not detected."""
        client = GeminiClient(api_key="key")
        error = Exception("Invalid API key")
        assert client._is_rate_limit_error(error) is False


class TestModelFallback:
    """Tests for model fallback functionality."""

    def test_get_available_model_returns_best(self):
        """Test that _get_available_model returns best available."""
        with patch("kubepath.ai.gemini.get_available_models", return_value=[
            "gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-2.0-flash"
        ]):
            client = GeminiClient(api_key="key")
            assert client._model_name == "gemini-2.5-flash"

    def test_get_available_model_skips_limited(self):
        """Test that _get_available_model skips rate-limited models."""
        with patch("kubepath.ai.gemini.get_available_models", return_value=[
            "gemini-2.5-flash-lite", "gemini-2.0-flash"  # gemini-2.5-flash is limited
        ]):
            client = GeminiClient(api_key="key")
            assert client._model_name == "gemini-2.5-flash-lite"

    def test_get_available_model_all_exhausted(self):
        """Test _get_available_model when all models exhausted."""
        with patch("kubepath.ai.gemini.get_available_models", return_value=[]):
            client = GeminiClient(api_key="key")
            # Should return last fallback model
            assert client._model_name == "gemini-2.0-flash"

    @patch("kubepath.ai.gemini.mark_model_rate_limited")
    @patch("kubepath.ai.gemini.get_available_models")
    def test_handle_rate_limit_switches_model(self, mock_get_available, mock_mark):
        """Test that _handle_rate_limit switches to fallback."""
        mock_get_available.return_value = ["gemini-2.5-flash-lite", "gemini-2.0-flash"]

        with patch("kubepath.ai.gemini.get_available_models", return_value=[
            "gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-2.0-flash"
        ]):
            client = GeminiClient(api_key="key")

        # Simulate initial model
        client._model_name = "gemini-2.5-flash"

        # Trigger rate limit handling
        mock_get_available.return_value = ["gemini-2.5-flash-lite", "gemini-2.0-flash"]
        result = client._handle_rate_limit()

        assert result is True
        mock_mark.assert_called_once_with("gemini-2.5-flash")
        assert client._model_name == "gemini-2.5-flash-lite"
        assert client._configured is False  # Force reconfiguration

    @patch("kubepath.ai.gemini.mark_model_rate_limited")
    @patch("kubepath.ai.gemini.get_available_models")
    def test_handle_rate_limit_all_exhausted(self, mock_get_available, mock_mark):
        """Test _handle_rate_limit when all models exhausted."""
        with patch("kubepath.ai.gemini.get_available_models", return_value=[
            "gemini-2.5-flash"
        ]):
            client = GeminiClient(api_key="key")

        client._model_name = "gemini-2.5-flash"

        mock_get_available.return_value = []  # All exhausted
        result = client._handle_rate_limit()

        assert result is False
        assert "unavailable" in client._fallback_message.lower()

    def test_fallback_message_cleared_after_read(self):
        """Test that fallback_message is cleared after reading."""
        with patch("kubepath.ai.gemini.get_available_models", return_value=["gemini-2.5-flash"]):
            client = GeminiClient(api_key="key")

        client._fallback_message = "Test message"

        first_read = client.fallback_message
        second_read = client.fallback_message

        assert first_read == "Test message"
        assert second_read is None

    def test_current_model_property(self):
        """Test current_model property."""
        with patch("kubepath.ai.gemini.get_available_models", return_value=[
            "gemini-2.5-flash", "gemini-2.5-flash-lite"
        ]):
            client = GeminiClient(api_key="key")
            assert client.current_model == "gemini-2.5-flash"


class TestFallbackIntegration:
    """Integration tests for fallback on rate limit."""

    @patch("kubepath.ai.gemini.GEMINI_AVAILABLE", True)
    @patch("kubepath.ai.gemini.genai")
    @patch("kubepath.ai.gemini.mark_model_rate_limited")
    @patch("kubepath.ai.gemini.get_available_models")
    def test_answer_question_fallback_on_rate_limit(
        self, mock_get_available, mock_mark, mock_genai
    ):
        """Test that answer_question falls back on rate limit."""
        # Setup: First call raises rate limit, second succeeds
        call_count = [0]

        def generate_side_effect(**kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise Exception("Error 429: Rate limited")
            response = MagicMock()
            response.text = "This is the answer from fallback model."
            return response

        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = generate_side_effect
        mock_genai.Client.return_value = mock_client

        # Initial model available
        mock_get_available.return_value = ["gemini-2.5-flash", "gemini-2.5-flash-lite"]
        client = GeminiClient(api_key="key")

        # After rate limit, return fallback
        mock_get_available.side_effect = [
            ["gemini-2.5-flash", "gemini-2.5-flash-lite"],  # After marking limited
            ["gemini-2.5-flash", "gemini-2.5-flash-lite"],  # On retry
        ]

        result = client.answer_question(
            context_title="Test",
            context_content="Content",
            learner_question="Question?",
        )

        assert result is not None
        assert "answer" in result.lower()
        mock_mark.assert_called_once()  # Model was marked as limited

    @patch("kubepath.ai.gemini.GEMINI_AVAILABLE", True)
    @patch("kubepath.ai.gemini.genai")
    @patch("kubepath.ai.gemini.mark_model_rate_limited")
    @patch("kubepath.ai.gemini.get_available_models")
    def test_get_debugging_hint_fallback_on_rate_limit(
        self, mock_get_available, mock_mark, mock_genai
    ):
        """Test that get_debugging_hint falls back on rate limit."""
        call_count = [0]

        def generate_side_effect(**kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise Exception("RESOURCE_EXHAUSTED")
            response = MagicMock()
            response.text = "HINT: Check the logs.\nCOMMANDS: kubectl logs pod-1"
            return response

        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = generate_side_effect
        mock_genai.Client.return_value = mock_client

        mock_get_available.return_value = ["gemini-2.5-flash", "gemini-2.5-flash-lite"]
        client = GeminiClient(api_key="key")

        mock_get_available.side_effect = [
            ["gemini-2.5-flash"],
            ["gemini-2.5-flash"],
        ]

        result = client.get_debugging_hint(
            scenario_description="Pod failing",
            manifest="apiVersion: v1",
            command_history="kubectl get pods",
            current_error="CrashLoopBackOff",
        )

        assert result is not None
        assert "logs" in result.hint_text.lower()

    @patch("kubepath.ai.gemini.GEMINI_AVAILABLE", True)
    @patch("kubepath.ai.gemini.genai")
    @patch("kubepath.ai.gemini.mark_model_rate_limited")
    @patch("kubepath.ai.gemini.get_available_models")
    def test_returns_none_when_all_models_exhausted(
        self, mock_get_available, mock_mark, mock_genai
    ):
        """Test returns None when all models are rate limited."""
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("429: Rate limited")
        mock_genai.Client.return_value = mock_client

        mock_get_available.return_value = ["gemini-2.5-flash"]
        client = GeminiClient(api_key="key")

        # All models exhausted after rate limit
        mock_get_available.return_value = []

        result = client.answer_question(
            context_title="Test",
            context_content="Content",
            learner_question="Question?",
        )

        assert result is None
