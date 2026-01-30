"""Unit tests for config module."""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from kubepath.config import (
    Config,
    load_config,
    save_config,
    get_gemini_api_key,
    set_gemini_api_key,
    clear_gemini_api_key,
    is_gemini_configured,
    get_gemini_model,
    set_gemini_model,
    get_config_status,
    _get_key_source,
    # Rate limit tracking
    get_today_pt,
    get_current_timestamp,
    mark_model_rate_limited,
    is_model_rate_limited,
    get_available_models,
    clear_expired_rate_limits,
    clear_all_rate_limits,
    FALLBACK_MODELS,
    RATE_LIMIT_COOLDOWN_SECONDS,
)
from datetime import datetime, timezone, timedelta


class TestConfig:
    """Tests for Config dataclass."""

    def test_default_values(self):
        """Test default config values."""
        config = Config()
        assert config.gemini_api_key is None
        assert config.gemini_model == "gemini-2.5-flash"
        assert config.rate_limited_models == {}

    def test_to_dict(self):
        """Test converting config to dict."""
        config = Config(gemini_api_key="test-key", gemini_model="gemini-pro")
        data = config.to_dict()
        assert data["gemini_api_key"] == "test-key"
        assert data["gemini_model"] == "gemini-pro"

    def test_from_dict(self):
        """Test creating config from dict."""
        data = {"gemini_api_key": "my-key", "gemini_model": "gemini-2.5-pro"}
        config = Config.from_dict(data)
        assert config.gemini_api_key == "my-key"
        assert config.gemini_model == "gemini-2.5-pro"

    def test_from_dict_defaults(self):
        """Test from_dict with missing keys uses defaults."""
        config = Config.from_dict({})
        assert config.gemini_api_key is None
        assert config.gemini_model == "gemini-2.5-flash"
        assert config.rate_limited_models == {}


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_missing_file(self, tmp_path):
        """Test loading config when file doesn't exist."""
        with patch("kubepath.config.CONFIG_FILE", tmp_path / "nonexistent.json"):
            config = load_config()
            assert config.gemini_api_key is None

    def test_load_valid_config(self, tmp_path):
        """Test loading valid config file."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({
            "gemini_api_key": "saved-key",
            "gemini_model": "gemini-pro"
        }))

        with patch("kubepath.config.CONFIG_FILE", config_file):
            config = load_config()
            assert config.gemini_api_key == "saved-key"
            assert config.gemini_model == "gemini-pro"

    def test_load_invalid_json(self, tmp_path):
        """Test loading config with invalid JSON."""
        config_file = tmp_path / "config.json"
        config_file.write_text("not valid json {{{")

        with patch("kubepath.config.CONFIG_FILE", config_file):
            config = load_config()
            # Should return default config
            assert config.gemini_api_key is None


class TestSaveConfig:
    """Tests for save_config function."""

    def test_save_config(self, tmp_path):
        """Test saving config file."""
        config_dir = tmp_path / ".kubepath"
        config_file = config_dir / "config.json"

        with patch("kubepath.config.CONFIG_DIR", config_dir):
            with patch("kubepath.config.CONFIG_FILE", config_file):
                config = Config(gemini_api_key="my-key")
                result = save_config(config)

                assert result is True
                assert config_file.exists()

                saved = json.loads(config_file.read_text())
                assert saved["gemini_api_key"] == "my-key"

    def test_save_creates_directory(self, tmp_path):
        """Test that save creates config directory."""
        config_dir = tmp_path / "nested" / ".kubepath"
        config_file = config_dir / "config.json"

        with patch("kubepath.config.CONFIG_DIR", config_dir):
            with patch("kubepath.config.CONFIG_FILE", config_file):
                config = Config(gemini_api_key="key")
                save_config(config)

                assert config_dir.exists()


class TestGetGeminiApiKey:
    """Tests for get_gemini_api_key function."""

    def test_get_from_config(self, tmp_path):
        """Test getting API key from config file."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({"gemini_api_key": "config-key"}))

        with patch("kubepath.config.CONFIG_FILE", config_file):
            with patch.dict("os.environ", {}, clear=True):
                key = get_gemini_api_key()
                assert key == "config-key"

    def test_get_from_env_gemini(self, tmp_path):
        """Test getting API key from GEMINI_API_KEY env var."""
        config_file = tmp_path / "config.json"

        with patch("kubepath.config.CONFIG_FILE", config_file):
            with patch.dict("os.environ", {"GEMINI_API_KEY": "env-key"}, clear=True):
                key = get_gemini_api_key()
                assert key == "env-key"

    def test_get_from_env_google(self, tmp_path):
        """Test getting API key from GOOGLE_API_KEY env var."""
        config_file = tmp_path / "config.json"

        with patch("kubepath.config.CONFIG_FILE", config_file):
            with patch.dict("os.environ", {"GOOGLE_API_KEY": "google-key"}, clear=True):
                key = get_gemini_api_key()
                assert key == "google-key"

    def test_config_takes_priority(self, tmp_path):
        """Test that config file takes priority over env vars."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({"gemini_api_key": "config-key"}))

        with patch("kubepath.config.CONFIG_FILE", config_file):
            with patch.dict("os.environ", {"GEMINI_API_KEY": "env-key"}):
                key = get_gemini_api_key()
                assert key == "config-key"

    def test_get_returns_none_when_not_configured(self, tmp_path):
        """Test that None is returned when no key configured."""
        config_file = tmp_path / "config.json"

        with patch("kubepath.config.CONFIG_FILE", config_file):
            with patch.dict("os.environ", {}, clear=True):
                key = get_gemini_api_key()
                assert key is None


class TestSetGeminiApiKey:
    """Tests for set_gemini_api_key function."""

    def test_set_api_key(self, tmp_path):
        """Test setting API key."""
        config_dir = tmp_path / ".kubepath"
        config_file = config_dir / "config.json"

        with patch("kubepath.config.CONFIG_DIR", config_dir):
            with patch("kubepath.config.CONFIG_FILE", config_file):
                result = set_gemini_api_key("new-key")

                assert result is True
                saved = json.loads(config_file.read_text())
                assert saved["gemini_api_key"] == "new-key"


class TestClearGeminiApiKey:
    """Tests for clear_gemini_api_key function."""

    def test_clear_api_key(self, tmp_path):
        """Test clearing API key."""
        config_dir = tmp_path / ".kubepath"
        config_file = config_dir / "config.json"
        config_dir.mkdir(parents=True)
        config_file.write_text(json.dumps({"gemini_api_key": "existing-key"}))

        with patch("kubepath.config.CONFIG_DIR", config_dir):
            with patch("kubepath.config.CONFIG_FILE", config_file):
                result = clear_gemini_api_key()

                assert result is True
                saved = json.loads(config_file.read_text())
                assert saved["gemini_api_key"] is None


class TestIsGeminiConfigured:
    """Tests for is_gemini_configured function."""

    def test_configured_from_config(self, tmp_path):
        """Test detecting config file key."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({"gemini_api_key": "key"}))

        with patch("kubepath.config.CONFIG_FILE", config_file):
            assert is_gemini_configured() is True

    def test_not_configured(self, tmp_path):
        """Test when not configured."""
        config_file = tmp_path / "config.json"

        with patch("kubepath.config.CONFIG_FILE", config_file):
            with patch.dict("os.environ", {}, clear=True):
                assert is_gemini_configured() is False


class TestGetGeminiModel:
    """Tests for get_gemini_model function."""

    def test_get_default_model(self, tmp_path):
        """Test getting default model."""
        config_file = tmp_path / "config.json"

        with patch("kubepath.config.CONFIG_FILE", config_file):
            model = get_gemini_model()
            assert model == "gemini-2.5-flash"

    def test_get_custom_model(self, tmp_path):
        """Test getting custom model from config."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({"gemini_model": "gemini-pro"}))

        with patch("kubepath.config.CONFIG_FILE", config_file):
            model = get_gemini_model()
            assert model == "gemini-pro"


class TestSetGeminiModel:
    """Tests for set_gemini_model function."""

    def test_set_model(self, tmp_path):
        """Test setting model."""
        config_dir = tmp_path / ".kubepath"
        config_file = config_dir / "config.json"

        with patch("kubepath.config.CONFIG_DIR", config_dir):
            with patch("kubepath.config.CONFIG_FILE", config_file):
                result = set_gemini_model("gemini-2.5-pro")

                assert result is True
                saved = json.loads(config_file.read_text())
                assert saved["gemini_model"] == "gemini-2.5-pro"


class TestGetConfigStatus:
    """Tests for get_config_status function."""

    def test_status_with_config(self, tmp_path):
        """Test status when config exists."""
        config_dir = tmp_path / ".kubepath"
        config_file = config_dir / "config.json"
        config_dir.mkdir(parents=True)
        config_file.write_text(json.dumps({
            "gemini_api_key": "key",
            "gemini_model": "gemini-pro"
        }))

        with patch("kubepath.config.CONFIG_DIR", config_dir):
            with patch("kubepath.config.CONFIG_FILE", config_file):
                status = get_config_status()

                assert status["config_exists"] is True
                assert status["gemini_configured"] is True
                assert status["gemini_key_source"] == "config_file"
                assert status["gemini_model"] == "gemini-pro"

    def test_status_no_config(self, tmp_path):
        """Test status when no config."""
        config_file = tmp_path / "config.json"

        with patch("kubepath.config.CONFIG_FILE", config_file):
            with patch.dict("os.environ", {}, clear=True):
                status = get_config_status()

                assert status["config_exists"] is False
                assert status["gemini_configured"] is False


class TestGetKeySource:
    """Tests for _get_key_source function."""

    def test_source_config_file(self, tmp_path):
        """Test detecting config file as source."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({"gemini_api_key": "key"}))

        with patch("kubepath.config.CONFIG_FILE", config_file):
            assert _get_key_source() == "config_file"

    def test_source_gemini_env(self, tmp_path):
        """Test detecting GEMINI_API_KEY env var."""
        config_file = tmp_path / "config.json"

        with patch("kubepath.config.CONFIG_FILE", config_file):
            with patch.dict("os.environ", {"GEMINI_API_KEY": "key"}, clear=True):
                assert _get_key_source() == "GEMINI_API_KEY"

    def test_source_google_env(self, tmp_path):
        """Test detecting GOOGLE_API_KEY env var."""
        config_file = tmp_path / "config.json"

        with patch("kubepath.config.CONFIG_FILE", config_file):
            with patch.dict("os.environ", {"GOOGLE_API_KEY": "key"}, clear=True):
                assert _get_key_source() == "GOOGLE_API_KEY"

    def test_source_none(self, tmp_path):
        """Test when no key source."""
        config_file = tmp_path / "config.json"

        with patch("kubepath.config.CONFIG_FILE", config_file):
            with patch.dict("os.environ", {}, clear=True):
                assert _get_key_source() is None


# ============================================================================
# Rate Limit Tracking Tests
# ============================================================================


class TestGetTodayPT:
    """Tests for get_today_pt function."""

    def test_returns_date_string(self):
        """Test that function returns a date string."""
        today = get_today_pt()
        assert isinstance(today, str)
        # Should be in YYYY-MM-DD format
        assert len(today) == 10
        assert today[4] == "-"
        assert today[7] == "-"


class TestGetCurrentTimestamp:
    """Tests for get_current_timestamp function."""

    def test_returns_iso_format(self):
        """Test that function returns ISO format timestamp."""
        ts = get_current_timestamp()
        assert isinstance(ts, str)
        # Should be parseable as ISO format
        parsed = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        assert parsed is not None

    def test_is_recent(self):
        """Test that timestamp is recent (within 5 seconds)."""
        ts = get_current_timestamp()
        parsed = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        diff = abs((now - parsed).total_seconds())
        assert diff < 5


class TestMarkModelRateLimited:
    """Tests for mark_model_rate_limited function."""

    def test_marks_model_with_timestamp(self, tmp_path):
        """Test that marking a model saves current timestamp."""
        config_dir = tmp_path / ".kubepath"
        config_file = config_dir / "config.json"

        with patch("kubepath.config.CONFIG_DIR", config_dir):
            with patch("kubepath.config.CONFIG_FILE", config_file):
                mark_model_rate_limited("gemini-2.5-flash")

                saved = json.loads(config_file.read_text())
                assert "gemini-2.5-flash" in saved["rate_limited_models"]
                # Should be an ISO timestamp
                ts = saved["rate_limited_models"]["gemini-2.5-flash"]
                assert "T" in ts  # ISO format includes T

    def test_marks_multiple_models(self, tmp_path):
        """Test marking multiple models."""
        config_dir = tmp_path / ".kubepath"
        config_file = config_dir / "config.json"

        with patch("kubepath.config.CONFIG_DIR", config_dir):
            with patch("kubepath.config.CONFIG_FILE", config_file):
                mark_model_rate_limited("gemini-2.5-flash")
                mark_model_rate_limited("gemini-2.5-flash")

                saved = json.loads(config_file.read_text())
                assert "gemini-2.5-flash" in saved["rate_limited_models"]
                assert "gemini-2.5-flash" in saved["rate_limited_models"]


class TestIsModelRateLimited:
    """Tests for is_model_rate_limited function."""

    def test_returns_true_within_cooldown(self, tmp_path):
        """Test returns True for model within cooldown period."""
        config_dir = tmp_path / ".kubepath"
        config_file = config_dir / "config.json"
        config_dir.mkdir(parents=True)
        # Recent timestamp (within cooldown)
        recent_ts = datetime.now(timezone.utc).isoformat()
        config_file.write_text(json.dumps({
            "rate_limited_models": {"gemini-2.5-flash": recent_ts}
        }))

        with patch("kubepath.config.CONFIG_FILE", config_file):
            assert is_model_rate_limited("gemini-2.5-flash") is True

    def test_returns_false_after_cooldown(self, tmp_path):
        """Test returns False for model after cooldown period."""
        config_dir = tmp_path / ".kubepath"
        config_file = config_dir / "config.json"
        config_dir.mkdir(parents=True)
        # Old timestamp (past cooldown)
        old_ts = (datetime.now(timezone.utc) - timedelta(seconds=RATE_LIMIT_COOLDOWN_SECONDS + 10)).isoformat()
        config_file.write_text(json.dumps({
            "rate_limited_models": {"gemini-2.5-flash": old_ts}
        }))

        with patch("kubepath.config.CONFIG_FILE", config_file):
            assert is_model_rate_limited("gemini-2.5-flash") is False

    def test_returns_false_for_legacy_date_format(self, tmp_path):
        """Test returns False for old date-only format (past cooldown)."""
        config_dir = tmp_path / ".kubepath"
        config_file = config_dir / "config.json"
        config_dir.mkdir(parents=True)
        config_file.write_text(json.dumps({
            "rate_limited_models": {"gemini-2.5-flash": "2020-01-01"}
        }))

        with patch("kubepath.config.CONFIG_FILE", config_file):
            assert is_model_rate_limited("gemini-2.5-flash") is False

    def test_returns_false_for_unknown_model(self, tmp_path):
        """Test returns False for model not in rate limit list."""
        config_file = tmp_path / "config.json"

        with patch("kubepath.config.CONFIG_FILE", config_file):
            assert is_model_rate_limited("unknown-model") is False

    def test_returns_false_for_invalid_timestamp(self, tmp_path):
        """Test returns False for invalid timestamp format."""
        config_dir = tmp_path / ".kubepath"
        config_file = config_dir / "config.json"
        config_dir.mkdir(parents=True)
        config_file.write_text(json.dumps({
            "rate_limited_models": {"gemini-2.5-flash": "invalid-timestamp"}
        }))

        with patch("kubepath.config.CONFIG_FILE", config_file):
            assert is_model_rate_limited("gemini-2.5-flash") is False


class TestGetAvailableModels:
    """Tests for get_available_models function."""

    def test_returns_all_when_none_limited(self, tmp_path):
        """Test returns all models when none rate-limited."""
        config_file = tmp_path / "config.json"

        with patch("kubepath.config.CONFIG_FILE", config_file):
            available = get_available_models()
            assert available == FALLBACK_MODELS

    def test_excludes_rate_limited_models(self, tmp_path):
        """Test excludes models within cooldown period."""
        config_dir = tmp_path / ".kubepath"
        config_file = config_dir / "config.json"
        config_dir.mkdir(parents=True)
        # Recent timestamp (within cooldown)
        recent_ts = datetime.now(timezone.utc).isoformat()
        config_file.write_text(json.dumps({
            "rate_limited_models": {"gemini-2.5-flash": recent_ts}
        }))

        with patch("kubepath.config.CONFIG_DIR", config_dir):
            with patch("kubepath.config.CONFIG_FILE", config_file):
                available = get_available_models()
                # gemini-2.5-flash should NOT be in available (it's rate limited)
                assert "gemini-2.5-flash" not in available
                # The fallback models should be available
                assert "gemini-2.5-flash-lite" in available
                assert "gemini-2.0-flash" in available

    def test_returns_empty_when_all_limited(self, tmp_path):
        """Test returns empty list when all models in cooldown."""
        config_dir = tmp_path / ".kubepath"
        config_file = config_dir / "config.json"
        config_dir.mkdir(parents=True)
        # Recent timestamp for all models
        recent_ts = datetime.now(timezone.utc).isoformat()
        config_file.write_text(json.dumps({
            "rate_limited_models": {
                "gemini-2.5-flash": recent_ts,
                "gemini-2.5-flash-lite": recent_ts,
                "gemini-2.0-flash": recent_ts,
            }
        }))

        with patch("kubepath.config.CONFIG_DIR", config_dir):
            with patch("kubepath.config.CONFIG_FILE", config_file):
                available = get_available_models()
                assert available == []

    def test_preserves_priority_order(self, tmp_path):
        """Test that available models are in priority order."""
        config_dir = tmp_path / ".kubepath"
        config_file = config_dir / "config.json"
        config_dir.mkdir(parents=True)
        recent_ts = datetime.now(timezone.utc).isoformat()
        config_file.write_text(json.dumps({
            "rate_limited_models": {"gemini-2.5-flash": recent_ts}
        }))

        with patch("kubepath.config.CONFIG_DIR", config_dir):
            with patch("kubepath.config.CONFIG_FILE", config_file):
                available = get_available_models()
                # gemini-2.5-flash-lite should be first (gemini-2.5-flash is rate limited)
                assert available[0] == "gemini-2.5-flash-lite"

    def test_includes_models_after_cooldown(self, tmp_path):
        """Test includes models after cooldown expires."""
        config_dir = tmp_path / ".kubepath"
        config_file = config_dir / "config.json"
        config_dir.mkdir(parents=True)
        # Old timestamp (past cooldown)
        old_ts = (datetime.now(timezone.utc) - timedelta(seconds=RATE_LIMIT_COOLDOWN_SECONDS + 10)).isoformat()
        config_file.write_text(json.dumps({
            "rate_limited_models": {"gemini-2.5-flash": old_ts}
        }))

        with patch("kubepath.config.CONFIG_DIR", config_dir):
            with patch("kubepath.config.CONFIG_FILE", config_file):
                available = get_available_models()
                # gemini-2.5-flash should be available again after cooldown
                assert "gemini-2.5-flash" in available


class TestClearExpiredRateLimits:
    """Tests for clear_expired_rate_limits function."""

    def test_removes_expired_timestamps(self, tmp_path):
        """Test removes rate limits past cooldown period."""
        config_dir = tmp_path / ".kubepath"
        config_file = config_dir / "config.json"
        config_dir.mkdir(parents=True)
        old_ts = (datetime.now(timezone.utc) - timedelta(seconds=RATE_LIMIT_COOLDOWN_SECONDS + 10)).isoformat()
        recent_ts = datetime.now(timezone.utc).isoformat()
        config_file.write_text(json.dumps({
            "rate_limited_models": {
                "gemini-2.0-flash": old_ts,  # Expired
                "gemini-2.5-flash": recent_ts,  # Still valid
            }
        }))

        with patch("kubepath.config.CONFIG_DIR", config_dir):
            with patch("kubepath.config.CONFIG_FILE", config_file):
                clear_expired_rate_limits()

                saved = json.loads(config_file.read_text())
                assert "gemini-2.0-flash" not in saved["rate_limited_models"]
                assert "gemini-2.5-flash" in saved["rate_limited_models"]

    def test_removes_legacy_date_format(self, tmp_path):
        """Test removes old date-only format entries."""
        config_dir = tmp_path / ".kubepath"
        config_file = config_dir / "config.json"
        config_dir.mkdir(parents=True)
        recent_ts = datetime.now(timezone.utc).isoformat()
        config_file.write_text(json.dumps({
            "rate_limited_models": {
                "gemini-2.0-flash": "2020-01-01",  # Legacy date format
                "gemini-2.5-flash": recent_ts,  # Current timestamp
            }
        }))

        with patch("kubepath.config.CONFIG_DIR", config_dir):
            with patch("kubepath.config.CONFIG_FILE", config_file):
                clear_expired_rate_limits()

                saved = json.loads(config_file.read_text())
                assert "gemini-2.0-flash" not in saved["rate_limited_models"]
                assert "gemini-2.5-flash" in saved["rate_limited_models"]

    def test_no_change_when_all_recent(self, tmp_path):
        """Test no changes when all rate limits are recent."""
        config_dir = tmp_path / ".kubepath"
        config_file = config_dir / "config.json"
        config_dir.mkdir(parents=True)
        recent_ts = datetime.now(timezone.utc).isoformat()
        config_file.write_text(json.dumps({
            "rate_limited_models": {"gemini-2.5-flash": recent_ts}
        }))

        with patch("kubepath.config.CONFIG_DIR", config_dir):
            with patch("kubepath.config.CONFIG_FILE", config_file):
                clear_expired_rate_limits()

                saved = json.loads(config_file.read_text())
                assert "gemini-2.5-flash" in saved["rate_limited_models"]


class TestClearAllRateLimits:
    """Tests for clear_all_rate_limits function."""

    def test_clears_all_models(self, tmp_path):
        """Test clears all rate-limited models."""
        config_dir = tmp_path / ".kubepath"
        config_file = config_dir / "config.json"
        config_dir.mkdir(parents=True)
        recent_ts = datetime.now(timezone.utc).isoformat()
        config_file.write_text(json.dumps({
            "rate_limited_models": {
                "gemini-2.5-flash": recent_ts,
                "gemini-2.5-flash-lite": recent_ts,
            }
        }))

        with patch("kubepath.config.CONFIG_DIR", config_dir):
            with patch("kubepath.config.CONFIG_FILE", config_file):
                clear_all_rate_limits()

                saved = json.loads(config_file.read_text())
                assert saved["rate_limited_models"] == {}


class TestCooldownBehavior:
    """Tests for RPM cooldown behavior."""

    def test_model_available_after_cooldown(self, tmp_path):
        """Test that model becomes available after cooldown period."""
        config_dir = tmp_path / ".kubepath"
        config_file = config_dir / "config.json"
        config_dir.mkdir(parents=True)

        # Just past cooldown
        past_cooldown = (datetime.now(timezone.utc) - timedelta(seconds=RATE_LIMIT_COOLDOWN_SECONDS + 1)).isoformat()
        config_file.write_text(json.dumps({
            "rate_limited_models": {"gemini-2.5-flash": past_cooldown}
        }))

        with patch("kubepath.config.CONFIG_DIR", config_dir):
            with patch("kubepath.config.CONFIG_FILE", config_file):
                # Should not be rate-limited anymore
                assert is_model_rate_limited("gemini-2.5-flash") is False
                # Should be in available models (after cooldown expired)
                available = get_available_models()
                assert "gemini-2.5-flash" in available

    def test_model_blocked_during_cooldown(self, tmp_path):
        """Test that model is blocked during cooldown period."""
        config_dir = tmp_path / ".kubepath"
        config_file = config_dir / "config.json"
        config_dir.mkdir(parents=True)

        # Half the cooldown period ago
        during_cooldown = (datetime.now(timezone.utc) - timedelta(seconds=RATE_LIMIT_COOLDOWN_SECONDS // 2)).isoformat()
        config_file.write_text(json.dumps({
            "rate_limited_models": {"gemini-2.5-flash": during_cooldown}
        }))

        with patch("kubepath.config.CONFIG_DIR", config_dir):
            with patch("kubepath.config.CONFIG_FILE", config_file):
                # Should still be rate-limited
                assert is_model_rate_limited("gemini-2.5-flash") is True
                # Should not be in available models (still in cooldown)
                available = get_available_models()
                assert "gemini-2.5-flash" not in available
