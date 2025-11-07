"""
Configuration management for pypet
"""

from pathlib import Path
from typing import Any

import toml


DEFAULT_CONFIG_DIR = Path.home() / ".config" / "pypet"
DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "config.toml"

DEFAULT_SETTINGS = {
    "auto_sync": False,
}


class Config:
    """Manages pypet configuration settings."""

    def __init__(self, config_path: Path | None = None):
        """Initialize config with optional custom path."""
        self.config_path = config_path or DEFAULT_CONFIG_FILE
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_config_exists()

    def _ensure_config_exists(self) -> None:
        """Create config file with defaults if it doesn't exist."""
        if not self.config_path.exists():
            self._save_config(DEFAULT_SETTINGS)

    def _load_config(self) -> dict:
        """Load configuration from TOML file."""
        try:
            return toml.load(self.config_path)
        except (toml.TomlDecodeError, OSError):
            # Return defaults if config is corrupted
            return DEFAULT_SETTINGS.copy()

    def _save_config(self, config: dict) -> None:
        """Save configuration to TOML file."""
        with self.config_path.open("w", encoding="utf-8") as f:
            toml.dump(config, f)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        config = self._load_config()
        return config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        config = self._load_config()
        config[key] = value
        self._save_config(config)

    @property
    def auto_sync(self) -> bool:
        """Get auto_sync setting."""
        return bool(self.get("auto_sync", False))

    @auto_sync.setter
    def auto_sync(self, value: bool) -> None:
        """Set auto_sync setting."""
        self.set("auto_sync", value)

    def get_all(self) -> dict:
        """Get all configuration settings."""
        return self._load_config()
