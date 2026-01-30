"""Configuration management for kubepath."""

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional


# Default config directory
CONFIG_DIR = Path.home() / ".kubepath"
CONFIG_FILE = CONFIG_DIR / "config.json"

# Gemini models in priority order (best first)
# Note: gemini-3 models are still in preview, using stable 2.5 as primary
FALLBACK_MODELS = [
    "gemini-2.5-flash",       # Best stable model
    "gemini-2.5-flash-lite",  # Lighter alternative
    "gemini-2.0-flash",       # Deprecated but works until March 31, 2026
]

# Cooldown period in seconds before retrying a rate-limited model (for RPM limits)
RATE_LIMIT_COOLDOWN_SECONDS = 70  # Slightly more than 1 minute for RPM reset


@dataclass
class Config:
    """Configuration settings for kubepath."""

    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-2.5-flash"  # Best stable model
    rate_limited_models: Dict[str, str] = field(default_factory=dict)
    # Format: {"gemini-2.5-flash": "2026-01-25T10:30:00+00:00"}  # ISO timestamp when rate limited

    # Hands-on mode settings
    hands_on_mode: bool = True  # Enable practice/scenarios (requires K8s)
    hands_on_configured: bool = False  # Has user made initial choice?

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "gemini_api_key": self.gemini_api_key,
            "gemini_model": self.gemini_model,
            "rate_limited_models": self.rate_limited_models,
            "hands_on_mode": self.hands_on_mode,
            "hands_on_configured": self.hands_on_configured,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Config":
        """Create config from dictionary."""
        return cls(
            gemini_api_key=data.get("gemini_api_key"),
            gemini_model=data.get("gemini_model", "gemini-2.5-flash"),
            rate_limited_models=data.get("rate_limited_models", {}),
            hands_on_mode=data.get("hands_on_mode", True),
            hands_on_configured=data.get("hands_on_configured", False),
        )


def ensure_config_dir() -> None:
    """Ensure the config directory exists."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> Config:
    """Load configuration from file.

    Returns:
        Config object with loaded settings.
    """
    if not CONFIG_FILE.exists():
        return Config()

    try:
        with open(CONFIG_FILE, "r") as f:
            data = json.load(f)
            return Config.from_dict(data)
    except (json.JSONDecodeError, IOError):
        return Config()


def save_config(config: Config) -> bool:
    """Save configuration to file.

    Args:
        config: Config object to save.

    Returns:
        True if save succeeded.
    """
    try:
        ensure_config_dir()
        with open(CONFIG_FILE, "w") as f:
            json.dump(config.to_dict(), f, indent=2)
        return True
    except IOError:
        return False


def get_gemini_api_key() -> Optional[str]:
    """Get Gemini API key from config or environment.

    Checks in order:
    1. Config file (~/.kubepath/config.json)
    2. GEMINI_API_KEY environment variable
    3. GOOGLE_API_KEY environment variable

    Returns:
        API key string or None if not configured.
    """
    # First check config file
    config = load_config()
    if config.gemini_api_key:
        return config.gemini_api_key

    # Then check environment variables
    return os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")


def set_gemini_api_key(api_key: str) -> bool:
    """Save Gemini API key to config file.

    Args:
        api_key: The API key to save.

    Returns:
        True if save succeeded.
    """
    config = load_config()
    config.gemini_api_key = api_key
    return save_config(config)


def clear_gemini_api_key() -> bool:
    """Remove Gemini API key from config file.

    Returns:
        True if clear succeeded.
    """
    config = load_config()
    config.gemini_api_key = None
    return save_config(config)


def is_gemini_configured() -> bool:
    """Check if Gemini API key is configured.

    Returns:
        True if API key is available.
    """
    return get_gemini_api_key() is not None


def get_gemini_model() -> str:
    """Get the configured Gemini model.

    Returns:
        Model name string.
    """
    config = load_config()
    return config.gemini_model


def set_gemini_model(model: str) -> bool:
    """Set the Gemini model to use.

    Args:
        model: Model name (e.g., "gemini-2.5-flash").

    Returns:
        True if save succeeded.
    """
    config = load_config()
    config.gemini_model = model
    return save_config(config)


def get_config_status() -> Dict[str, Any]:
    """Get current configuration status.

    Returns:
        Dictionary with configuration status.
    """
    config = load_config()
    has_key = is_gemini_configured()

    return {
        "config_file": str(CONFIG_FILE),
        "config_exists": CONFIG_FILE.exists(),
        "gemini_configured": has_key,
        "gemini_key_source": _get_key_source(),
        "gemini_model": config.gemini_model,
    }


def _get_key_source() -> Optional[str]:
    """Determine where the API key is configured.

    Returns:
        Source string or None if not configured.
    """
    config = load_config()
    if config.gemini_api_key:
        return "config_file"
    if os.getenv("GEMINI_API_KEY"):
        return "GEMINI_API_KEY"
    if os.getenv("GOOGLE_API_KEY"):
        return "GOOGLE_API_KEY"
    return None


# ============================================================================
# Rate Limit Tracking Functions
# ============================================================================


def get_current_timestamp() -> str:
    """Get current UTC timestamp in ISO format.

    Returns:
        ISO timestamp string.
    """
    return datetime.now(timezone.utc).isoformat()


def get_today_pt() -> str:
    """Get today's date in Pacific Time (when Gemini RPD resets).

    Returns:
        Date string in YYYY-MM-DD format.
    """
    # Pacific Time is UTC-8 (or UTC-7 during DST)
    # Using UTC-8 as a conservative estimate
    pt_offset = timedelta(hours=-8)
    pt_time = datetime.now(timezone.utc) + pt_offset
    return pt_time.strftime("%Y-%m-%d")


def mark_model_rate_limited(model: str) -> None:
    """Mark a model as rate-limited with current timestamp.

    The model will be unavailable until the cooldown period passes (for RPM)
    or until the next day (for RPD).

    Args:
        model: The model name to mark as rate-limited.
    """
    config = load_config()
    config.rate_limited_models[model] = get_current_timestamp()
    save_config(config)


def is_model_rate_limited(model: str) -> bool:
    """Check if a model is still in cooldown period.

    A model is considered rate-limited if it was marked within the
    cooldown period (handles RPM limits) AND is from today (handles RPD).

    Args:
        model: The model name to check.

    Returns:
        True if the model is still rate-limited.
    """
    config = load_config()
    limited_timestamp = config.rate_limited_models.get(model)
    if not limited_timestamp:
        return False

    try:
        # Parse the timestamp
        if "T" in limited_timestamp:
            # ISO format timestamp
            limited_time = datetime.fromisoformat(limited_timestamp.replace("Z", "+00:00"))
        else:
            # Legacy date format (YYYY-MM-DD) - treat as start of day PT
            pt_offset = timedelta(hours=-8)
            limited_time = datetime.strptime(limited_timestamp, "%Y-%m-%d").replace(
                tzinfo=timezone.utc
            ) - pt_offset

        now = datetime.now(timezone.utc)
        elapsed = (now - limited_time).total_seconds()

        # Model is rate-limited if still within cooldown period
        return elapsed < RATE_LIMIT_COOLDOWN_SECONDS

    except (ValueError, TypeError):
        # Invalid timestamp format, consider not limited
        return False


def get_available_models() -> List[str]:
    """Get models that are not rate-limited, in priority order.

    Models become available again after the cooldown period passes,
    allowing retry for RPM limits while cycling through models.

    Returns:
        List of available model names, best first.
    """
    # Clean up expired rate limits first
    clear_expired_rate_limits()

    return [model for model in FALLBACK_MODELS if not is_model_rate_limited(model)]


def clear_expired_rate_limits() -> None:
    """Clear rate limits that have passed the cooldown period."""
    config = load_config()
    now = datetime.now(timezone.utc)

    # Find models with expired rate limits
    expired = []
    for model, timestamp in config.rate_limited_models.items():
        try:
            if "T" in timestamp:
                limited_time = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            else:
                # Legacy date format
                pt_offset = timedelta(hours=-8)
                limited_time = datetime.strptime(timestamp, "%Y-%m-%d").replace(
                    tzinfo=timezone.utc
                ) - pt_offset

            elapsed = (now - limited_time).total_seconds()
            if elapsed >= RATE_LIMIT_COOLDOWN_SECONDS:
                expired.append(model)
        except (ValueError, TypeError):
            expired.append(model)

    if expired:
        for model in expired:
            del config.rate_limited_models[model]
        save_config(config)


def clear_all_rate_limits() -> None:
    """Clear all rate limits (useful for testing)."""
    config = load_config()
    config.rate_limited_models = {}
    save_config(config)


# ============================================================================
# Hands-On Mode Functions
# ============================================================================


def get_hands_on_mode() -> bool:
    """Get whether hands-on mode is enabled.

    When enabled, practice and scenario sections will be available
    (requiring a Kubernetes cluster). When disabled, these sections
    are skipped and only concepts/quizzes are shown.

    Returns:
        True if hands-on mode is enabled.
    """
    config = load_config()
    return config.hands_on_mode


def set_hands_on_mode(enabled: bool) -> bool:
    """Set hands-on mode preference.

    Args:
        enabled: True to enable practice/scenarios, False for theory only.

    Returns:
        True if save succeeded.
    """
    config = load_config()
    config.hands_on_mode = enabled
    config.hands_on_configured = True  # Mark as configured when set
    return save_config(config)


def is_hands_on_configured() -> bool:
    """Check if user has made their initial hands-on mode choice.

    This is used to detect first run and prompt the user.

    Returns:
        True if user has already chosen their preference.
    """
    config = load_config()
    return config.hands_on_configured


def mark_hands_on_configured() -> bool:
    """Mark that user has made their hands-on mode choice.

    Returns:
        True if save succeeded.
    """
    config = load_config()
    config.hands_on_configured = True
    return save_config(config)
