"""Configuration management for Precogs CLI."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class Config:
    """Manage CLI configuration stored in ~/.precogs/config.json"""

    def __init__(self):
        self.config_dir = Path.home() / ".precogs"
        self.config_file = self.config_dir / "config.json"
        self._config: dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        """Load config from disk."""
        if self.config_file.exists():
            try:
                self._config = json.loads(self.config_file.read_text())
            except (json.JSONDecodeError, IOError):
                self._config = {}

    def _save(self) -> None:
        """Save config to disk."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file.write_text(json.dumps(self._config, indent=2))

    @property
    def api_key(self) -> str | None:
        """Get stored API key."""
        return self._config.get("api_key")

    @api_key.setter
    def api_key(self, value: str) -> None:
        """Store API key."""
        self._config["api_key"] = value
        self._save()

    @property
    def default_project(self) -> str | None:
        """Get default project ID."""
        return self._config.get("default_project")

    @default_project.setter
    def default_project(self, value: str) -> None:
        """Set default project ID."""
        self._config["default_project"] = value
        self._save()

    def clear(self) -> None:
        """Clear all configuration."""
        self._config = {}
        if self.config_file.exists():
            self.config_file.unlink()


# Global config instance
config = Config()
