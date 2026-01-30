"""Google Gemini API integration for AI-powered debugging assistance."""

from dataclasses import dataclass
from typing import List, Optional

from kubepath.config import (
    get_gemini_api_key,
    get_available_models,
    mark_model_rate_limited,
    FALLBACK_MODELS,
)

# Conditional import for when google-genai is not installed
try:
    from google import genai

    GEMINI_AVAILABLE = True
except ImportError:
    genai = None
    GEMINI_AVAILABLE = False


@dataclass
class GeminiHint:
    """AI-generated debugging hint."""

    hint_text: str
    suggested_commands: List[str]
    confidence: float = 0.8  # 0.0 - 1.0


class GeminiClient:
    """Client for Gemini API interactions.

    Provides AI-powered debugging hints for Kubernetes scenarios.
    Falls back gracefully when API is unavailable.

    Example:
        client = GeminiClient()
        if client.is_available:
            hint = client.get_debugging_hint(
                scenario_description="Pod won't start",
                manifest="apiVersion: v1...",
                command_history="$ kubectl get pods\\n...",
                current_error="ImagePullBackOff",
            )
    """

    # Recommended model for debugging assistance (best stable model)
    DEFAULT_MODEL = "gemini-2.5-flash"

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Gemini client.

        Args:
            api_key: Gemini API key. If None, reads from config or env vars.
        """
        self.api_key = api_key or get_gemini_api_key()
        self._configured = False
        self._client: Optional["genai.Client"] = None
        self._model_name = self._get_available_model()
        self._fallback_message: Optional[str] = None  # Message to show user

    def _get_available_model(self) -> str:
        """Get the highest priority model that's not rate-limited.

        Returns:
            Model name string.
        """
        available = get_available_models()
        if available:
            return available[0]
        # All models exhausted, return last one (will fail but with proper error)
        return FALLBACK_MODELS[-1] if FALLBACK_MODELS else self.DEFAULT_MODEL

    def _is_rate_limit_error(self, error: Exception) -> bool:
        """Check if an exception indicates a rate limit error.

        Args:
            error: The exception to check.

        Returns:
            True if this is a rate limit error.
        """
        msg = str(error).lower()
        return (
            "429" in msg
            or "resource_exhausted" in msg
            or "quota" in msg
            or "rate" in msg and "limit" in msg
        )

    def _handle_rate_limit(self) -> bool:
        """Handle rate limit by marking current model and switching to fallback.

        Returns:
            True if a fallback model is available, False if all exhausted.
        """
        # Mark current model as rate-limited
        mark_model_rate_limited(self._model_name)

        # Get remaining available models
        available = get_available_models()
        if available:
            old_model = self._model_name
            self._model_name = available[0]
            self._configured = False  # Force reconfiguration with new model
            self._fallback_message = (
                f"Model {old_model} rate-limited. Switching to {self._model_name}..."
            )
            return True

        self._fallback_message = "AI assistance unavailable (daily limit reached). Try again tomorrow!"
        return False

    @property
    def fallback_message(self) -> Optional[str]:
        """Get the last fallback message (for UI display).

        Returns:
            Message string or None.
        """
        msg = self._fallback_message
        self._fallback_message = None  # Clear after reading
        return msg

    @property
    def current_model(self) -> str:
        """Get the current model name.

        Returns:
            Model name string.
        """
        return self._model_name

    @property
    def is_available(self) -> bool:
        """Check if Gemini is available and configured.

        Returns:
            True if google-genai is installed and API key is set.
        """
        return GEMINI_AVAILABLE and bool(self.api_key)

    def configure(self) -> bool:
        """Configure the Gemini API client.

        Returns:
            True if configuration succeeded.
        """
        if not self.is_available:
            return False

        try:
            self._client = genai.Client(api_key=self.api_key)
            self._configured = True
            return True
        except Exception:
            return False

    def validate_api_key(self) -> tuple[bool, str]:
        """Test if API key works with a simple request.

        Returns:
            Tuple of (success, message).
        """
        if not GEMINI_AVAILABLE:
            return False, "google-genai package not installed"

        if not self.api_key:
            return False, "No API key configured"

        try:
            client = genai.Client(api_key=self.api_key)
            # Simple test request
            response = client.models.generate_content(
                model=self._model_name,
                contents="Say 'OK' if you can hear me.",
            )
            if response and response.text:
                return True, "API key is valid"
            return False, "Empty response from API"
        except Exception as e:
            error_msg = str(e)
            if "API_KEY_INVALID" in error_msg or "invalid" in error_msg.lower():
                return False, "Invalid API key"
            if "QUOTA" in error_msg or "quota" in error_msg.lower():
                return False, "API quota exceeded"
            return False, f"API error: {error_msg[:100]}"

    def get_debugging_hint(
        self,
        scenario_description: str,
        manifest: str,
        command_history: str,
        current_error: str,
    ) -> Optional[GeminiHint]:
        """Get an AI-powered debugging hint.

        Args:
            scenario_description: What the scenario is about.
            manifest: The broken manifest YAML.
            command_history: Formatted command history from learner.
            current_error: The current error or status.

        Returns:
            GeminiHint with suggestions, or None on failure.
        """
        if not self._configured:
            if not self.configure():
                return None

        prompt = self._build_debugging_prompt(
            scenario_description,
            manifest,
            command_history,
            current_error,
        )

        try:
            response = self._client.models.generate_content(
                model=self._model_name,
                contents=prompt,
            )
            if response and response.text:
                return self._parse_hint_response(response.text)
            return None
        except Exception as e:
            if self._is_rate_limit_error(e):
                if self._handle_rate_limit():
                    # Retry with fallback model
                    return self.get_debugging_hint(
                        scenario_description, manifest, command_history, current_error
                    )
            return None

    def _build_debugging_prompt(
        self,
        description: str,
        manifest: str,
        history: str,
        error: str,
    ) -> str:
        """Build the prompt for debugging assistance.

        Args:
            description: Scenario description.
            manifest: The broken manifest.
            history: Command history.
            error: Current error.

        Returns:
            Formatted prompt string.
        """
        return f"""You are a Kubernetes debugging assistant helping a learner fix a broken deployment.
Your goal is to TEACH, not to give away the answer directly.

SCENARIO: {description}

BROKEN MANIFEST:
```yaml
{manifest[:1500]}
```

LEARNER'S COMMAND HISTORY:
{history[:1000]}

CURRENT ERROR/STATUS:
{error[:500]}

Provide a helpful hint to guide the learner toward the solution.

RULES:
1. Don't give away the answer directly - help them learn to debug
2. Suggest 1-2 specific kubectl commands to investigate
3. Point them toward the right area to look (events, logs, describe output)
4. Keep the hint concise (2-3 sentences max)
5. Be encouraging and educational

FORMAT YOUR RESPONSE EXACTLY LIKE THIS:
HINT: [your hint here - 2-3 sentences]
COMMANDS: [comma-separated list of kubectl commands to try]

Example response:
HINT: The pod is failing to pull its container image. Check the image name carefully - container registries are case-sensitive and typos are common.
COMMANDS: kubectl describe pod broken-app, kubectl get events --sort-by='.lastTimestamp'
"""

    def _parse_hint_response(self, response_text: str) -> GeminiHint:
        """Parse Gemini's response into structured hint.

        Args:
            response_text: Raw response from Gemini.

        Returns:
            GeminiHint with parsed data.
        """
        lines = response_text.strip().split("\n")
        hint_text = ""
        commands = []

        for line in lines:
            line = line.strip()
            if line.upper().startswith("HINT:"):
                hint_text = line[5:].strip()
            elif line.upper().startswith("COMMANDS:"):
                cmd_str = line[9:].strip()
                commands = [c.strip() for c in cmd_str.split(",") if c.strip()]

        # Fallback if parsing didn't work
        if not hint_text:
            hint_text = response_text[:300].strip()

        return GeminiHint(
            hint_text=hint_text,
            suggested_commands=commands,
            confidence=0.8,
        )

    def analyze_error(
        self,
        error_output: str,
        resource_type: str = "pod",
    ) -> Optional[str]:
        """Analyze kubectl error output and explain in simple terms.

        Args:
            error_output: Output from kubectl describe or logs.
            resource_type: Type of resource (pod, deployment, etc).

        Returns:
            Simple explanation of the error, or None on failure.
        """
        if not self._configured:
            if not self.configure():
                return None

        prompt = f"""Analyze this Kubernetes {resource_type} error and explain it simply for a learner:

```
{error_output[:2000]}
```

Provide a 1-2 sentence explanation of what's wrong and what the learner should check.
Be educational and encouraging. Don't give the exact fix, just explain the problem."""

        try:
            response = self._client.models.generate_content(
                model=self._model_name,
                contents=prompt,
            )
            if response and response.text:
                return response.text.strip()[:500]
            return None
        except Exception as e:
            if self._is_rate_limit_error(e):
                if self._handle_rate_limit():
                    # Retry with fallback model
                    return self.analyze_error(error_output, resource_type)
            return None

    def answer_question(
        self,
        context_title: str,
        context_content: str,
        learner_question: str,
        section_type: str = "concept",
    ) -> Optional[str]:
        """Answer a learner's question about the current content.

        Args:
            context_title: Title of the current concept or practice.
            context_content: The content being studied.
            learner_question: The question the learner is asking.
            section_type: Either "concept" or "practice".

        Returns:
            Concise, educational answer (2-4 sentences), or None on failure.
        """
        if not self._configured:
            if not self.configure():
                return None

        section_label = "concept" if section_type == "concept" else "practice exercise"

        prompt = f"""You are a Kubernetes learning assistant. A learner is studying and has a question.

CURRENT {section_label.upper()}: {context_title}

CONTENT BEING STUDIED:
{context_content[:1500]}

LEARNER'S QUESTION: {learner_question}

RULES:
1. Answer in 2-4 sentences maximum - be concise
2. Use simple, clear language
3. Stay on topic - relate your answer to Kubernetes concepts
4. Be educational - help them understand, don't just give facts
5. If the question is unclear, give a helpful general answer about the topic

Provide your answer directly without any prefix or formatting."""

        try:
            response = self._client.models.generate_content(
                model=self._model_name,
                contents=prompt,
            )
            if response and response.text:
                return response.text.strip()[:500]
            return None
        except Exception as e:
            if self._is_rate_limit_error(e):
                if self._handle_rate_limit():
                    # Retry with fallback model
                    return self.answer_question(
                        context_title, context_content, learner_question, section_type
                    )
            return None


# Singleton instance for convenience
_client: Optional[GeminiClient] = None


def get_gemini_client() -> GeminiClient:
    """Get or create the global Gemini client.

    Returns:
        GeminiClient instance.
    """
    global _client
    if _client is None:
        _client = GeminiClient()
    return _client


def reset_gemini_client() -> None:
    """Reset the global Gemini client (useful after config changes)."""
    global _client
    _client = None
