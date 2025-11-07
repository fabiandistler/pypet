"""
Tests for pypet configuration management
"""

from pathlib import Path

from pypet.config import Config


def test_config_initialization(tmp_path: Path) -> None:
    """Test that config file is created with defaults."""
    config_path = tmp_path / "config.toml"
    config = Config(config_path)

    assert config_path.exists()
    assert config.auto_sync is False


def test_get_and_set(tmp_path: Path) -> None:
    """Test getting and setting config values."""
    config_path = tmp_path / "config.toml"
    config = Config(config_path)

    # Test default value
    assert config.get("auto_sync") is False

    # Test setting value
    config.set("auto_sync", True)
    assert config.get("auto_sync") is True

    # Test persistence
    config2 = Config(config_path)
    assert config2.get("auto_sync") is True


def test_auto_sync_property(tmp_path: Path) -> None:
    """Test auto_sync property."""
    config_path = tmp_path / "config.toml"
    config = Config(config_path)

    # Test default
    assert config.auto_sync is False

    # Test setting via property
    config.auto_sync = True
    assert config.auto_sync is True

    # Test persistence
    config2 = Config(config_path)
    assert config2.auto_sync is True

    # Test setting to False
    config.auto_sync = False
    assert config.auto_sync is False


def test_get_all(tmp_path: Path) -> None:
    """Test getting all config values."""
    config_path = tmp_path / "config.toml"
    config = Config(config_path)

    # Set some values
    config.set("auto_sync", True)
    config.set("custom_key", "custom_value")

    # Get all
    all_config = config.get_all()
    assert all_config["auto_sync"] is True
    assert all_config["custom_key"] == "custom_value"


def test_get_with_default(tmp_path: Path) -> None:
    """Test getting config value with default."""
    config_path = tmp_path / "config.toml"
    config = Config(config_path)

    # Test non-existent key with default
    value = config.get("non_existent", "default_value")
    assert value == "default_value"

    # Test existing key ignores default
    config.set("existing", "actual_value")
    value = config.get("existing", "default_value")
    assert value == "actual_value"


def test_corrupted_config(tmp_path: Path) -> None:
    """Test that corrupted config file falls back to defaults."""
    config_path = tmp_path / "config.toml"

    # Create invalid TOML
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text("invalid toml {]}")

    # Should not crash and should return defaults
    config = Config(config_path)
    assert config.auto_sync is False
