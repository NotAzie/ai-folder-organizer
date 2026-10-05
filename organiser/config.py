"""
Configuration management for AI Folder Organizer.

Supports multiple configuration sources:
1. Environment variables (highest priority)
2. Configuration file (config.json or config.yaml)
3. Default values (lowest priority)

Security Note: API keys should NEVER be hardcoded in source code.
Always use environment variables or secure configuration files.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


@dataclass
class Config:
    """Configuration for the AI Folder Organizer."""

    # API Configuration
    api_url: str = "https://apifreellm.com/api/v1/chat"
    api_key: Optional[str] = None
    model: str = "apifreellm"
    max_retries: int = 3
    timeout_seconds: int = 120
    rate_limit_seconds: float = 6.0

    # Logging
    log_file: str = "organizer_log.json"
    rollback_manifest: str = "organizer_rollback_manifest.json"

    # Exclusion patterns for folder scanning
    exclude_patterns: set[str] = field(default_factory=lambda: {
        'appdata', 'isolatedstorage', 'temp', 'tmp', 'cache',
        '.git', '.vscode', '__pycache__', 'node_modules', '.env',
        'venv', 'env', '.pytest_cache', 'dist', 'build', '.next',
        'launchdarkly', 'system volume information', '$recycle.bin',
    })

    # UI Settings
    default_headless: bool = False

    @classmethod
    def from_env(cls) -> Config:
        """Load configuration from environment variables."""
        return cls(
            api_url=os.getenv("AI_FOLDER_ORG_API_URL", "https://apifreellm.com/api/v1/chat"),
            api_key=os.getenv("AI_FOLDER_ORG_API_KEY"),
            model=os.getenv("AI_FOLDER_ORG_MODEL", "apifreellm"),
            max_retries=int(os.getenv("AI_FOLDER_ORG_MAX_RETRIES", "3")),
            timeout_seconds=int(os.getenv("AI_FOLDER_ORG_TIMEOUT", "120")),
            rate_limit_seconds=float(os.getenv("AI_FOLDER_ORG_RATE_LIMIT", "6")),
            log_file=os.getenv("AI_FOLDER_ORG_LOG_FILE", "organizer_log.json"),
            rollback_manifest=os.getenv("AI_FOLDER_ORG_ROLLBACK_MANIFEST", "organizer_rollback_manifest.json"),
        )

    @classmethod
    def from_file(cls, path: Path | str) -> Config:
        """Load configuration from a JSON file."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return cls(
            api_url=data.get("api_url", "https://apifreellm.com/api/v1/chat"),
            api_key=data.get("api_key"),
            model=data.get("model", "apifreellm"),
            max_retries=data.get("max_retries", 3),
            timeout_seconds=data.get("timeout_seconds", 120),
            rate_limit_seconds=data.get("rate_limit_seconds", 6),
            log_file=data.get("log_file", "organizer_log.json"),
            rollback_manifest=data.get("rollback_manifest", "organizer_rollback_manifest.json"),
            exclude_patterns=set(data.get("exclude_patterns", [])) or None,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "api_url": self.api_url,
            "api_key": self.api_key,
            "model": self.model,
            "max_retries": self.max_retries,
            "timeout_seconds": self.timeout_seconds,
            "rate_limit_seconds": self.rate_limit_seconds,
            "log_file": self.log_file,
            "rollback_manifest": self.rollback_manifest,
            "exclude_patterns": list(self.exclude_patterns),
        }

    def save(self, path: Path | str) -> None:
        """Save configuration to a JSON file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)


def load_config(config_path: Optional[Path | str] = None) -> Config:
    """
    Load configuration from multiple sources.

    Priority order (highest to lowest):
    1. Environment variables
    2. Configuration file (if specified)
    3. Default values

    Args:
        config_path: Optional path to configuration file.

    Returns:
        Config object with merged settings.
    """
    env_config = Config.from_env()

    # Start with file config or defaults
    if config_path:
        try:
            base_config = Config.from_file(config_path)
        except FileNotFoundError:
            base_config = Config()
    else:
        base_config = Config()

    # Merge: env vars override file config
    return Config(
        api_url=os.getenv("AI_FOLDER_ORG_API_URL", base_config.api_url),
        api_key=os.getenv("AI_FOLDER_ORG_API_KEY", base_config.api_key),
        model=os.getenv("AI_FOLDER_ORG_MODEL", base_config.model),
        max_retries=int(os.getenv("AI_FOLDER_ORG_MAX_RETRIES", str(base_config.max_retries))),
        timeout_seconds=int(os.getenv("AI_FOLDER_ORG_TIMEOUT", str(base_config.timeout_seconds))),
        rate_limit_seconds=float(os.getenv("AI_FOLDER_ORG_RATE_LIMIT", str(base_config.rate_limit_seconds))),
        log_file=os.getenv("AI_FOLDER_ORG_LOG_FILE", base_config.log_file),
        rollback_manifest=os.getenv("AI_FOLDER_ORG_ROLLBACK_MANIFEST", base_config.rollback_manifest),
        exclude_patterns=base_config.exclude_patterns,
    )
