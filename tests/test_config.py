"""Tests for configuration module."""

import json
import os
import pytest
from pathlib import Path

from organiser.config import Config, load_config


class TestConfig:
    """Tests for Config dataclass."""

    def test_default_config(self):
        """Default config should have sensible values."""
        config = Config()
        assert config.api_url == "https://apifreellm.com/api/v1/chat"
        assert config.api_key is None
        assert config.model == "apifreellm"
        assert config.max_retries == 3
        assert config.timeout_seconds == 120
        assert config.rate_limit_seconds == 6.0
        assert config.log_file == "organizer_log.json"
        assert config.rollback_manifest == "organizer_rollback_manifest.json"

    def test_custom_config(self):
        """Config should accept custom values."""
        config = Config(
            api_url="https://custom.api.com",
            api_key="test-key",
            model="custom-model",
            max_retries=5,
            timeout_seconds=60,
            rate_limit_seconds=2.5,
        )
        assert config.api_url == "https://custom.api.com"
        assert config.api_key == "test-key"
        assert config.model == "custom-model"
        assert config.max_retries == 5
        assert config.timeout_seconds == 60
        assert config.rate_limit_seconds == 2.5

    def test_exclude_patterns_default(self):
        """Default exclude patterns should include common system folders."""
        config = Config()
        assert 'venv' in config.exclude_patterns
        assert '.git' in config.exclude_patterns
        assert '__pycache__' in config.exclude_patterns
        assert 'node_modules' in config.exclude_patterns

    def test_to_dict(self):
        """Config should serialize to dictionary."""
        config = Config(api_key="test-key", max_retries=5)
        data = config.to_dict()

        assert data["api_url"] == "https://apifreellm.com/api/v1/chat"
        assert data["api_key"] == "test-key"
        assert data["max_retries"] == 5
        assert isinstance(data["exclude_patterns"], list)

    def test_save_and_load(self, tmp_path):
        """Config should save and load from file."""
        config = Config(api_key="test-key", max_retries=5)
        config_path = tmp_path / "config.json"

        config.save(config_path)

        loaded = Config.from_file(config_path)
        assert loaded.api_key == "test-key"
        assert loaded.max_retries == 5


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_from_env(self, monkeypatch):
        """Config should load from environment variables."""
        monkeypatch.setenv("AI_FOLDER_ORG_API_KEY", "env-key")
        monkeypatch.setenv("AI_FOLDER_ORG_MODEL", "env-model")
        monkeypatch.setenv("AI_FOLDER_ORG_MAX_RETRIES", "10")

        config = load_config()

        assert config.api_key == "env-key"
        assert config.model == "env-model"
        assert config.max_retries == 10

    def test_load_from_file(self, tmp_path):
        """Config should load from JSON file."""
        config_path = tmp_path / "config.json"
        config_data = {
            "api_key": "file-key",
            "model": "file-model",
            "max_retries": 7,
        }
        config_path.write_text(json.dumps(config_data))

        config = load_config(config_path)

        assert config.api_key == "file-key"
        assert config.model == "file-model"
        assert config.max_retries == 7

    def test_env_overrides_file(self, tmp_path, monkeypatch):
        """Environment variables should override config file."""
        config_path = tmp_path / "config.json"
        config_data = {"api_key": "file-key", "model": "file-model"}
        config_path.write_text(json.dumps(config_data))

        monkeypatch.setenv("AI_FOLDER_ORG_API_KEY", "env-key")

        config = load_config(config_path)

        # Env var should win
        assert config.api_key == "env-key"
        # File value should remain for non-overridden fields
        assert config.model == "file-model"

    def test_missing_file_uses_defaults(self):
        """Missing config file should use defaults."""
        config = load_config(Path("/nonexistent/config.json"))

        assert config.api_key is None
        assert config.model == "apifreellm"
