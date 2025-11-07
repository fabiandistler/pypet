"""Test cases for sync CLI commands"""

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from pypet.cli import main
from pypet.config import Config


@pytest.fixture
def runner():
    """Create a CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def temp_config_dir(tmp_path):
    """Create a temporary config directory."""
    config_dir = tmp_path / "pypet"
    config_dir.mkdir()
    config_file = config_dir / "snippets.toml"
    config_file.write_text('[test]\ncommand = "test"\n')
    return config_dir


def test_sync_status_command(runner):
    """Test sync status command."""
    result = runner.invoke(main, ["sync", "status"])
    assert result.exit_code == 0
    assert "Git Sync Status" in result.output
    assert "Git Available" in result.output


@patch("pypet.sync.GIT_AVAILABLE", False)
def test_sync_init_no_git(runner):
    """Test sync init when Git is not available."""
    result = runner.invoke(main, ["sync", "init"])
    assert result.exit_code == 1
    assert "Git is not available" in result.output


@patch("pypet.sync.GIT_AVAILABLE", True)
@patch("pypet.sync.Repo")
def test_sync_init_success(mock_repo_class, runner):
    """Test successful sync init."""
    mock_repo = MagicMock()
    mock_repo_class.init.return_value = mock_repo

    with patch("pypet.cli.main_module.sync_manager") as mock_sync_manager:
        mock_sync_manager.git_available = True
        mock_sync_manager.is_git_repo = False
        mock_sync_manager.init_git_repo.return_value = True

        result = runner.invoke(main, ["sync", "init"])
        assert result.exit_code == 0
        assert "Git sync initialized successfully" in result.output


@patch("pypet.sync.GIT_AVAILABLE", True)
def test_sync_init_already_initialized(runner):
    """Test sync init when already initialized."""
    with patch("pypet.cli.main_module.sync_manager") as mock_sync_manager:
        mock_sync_manager.git_available = True
        mock_sync_manager.is_git_repo = True

        result = runner.invoke(main, ["sync", "init"])
        assert result.exit_code == 0
        assert "already initialized" in result.output


def test_sync_commit_command(runner):
    """Test sync commit command."""
    with patch("pypet.cli.main_module.sync_manager") as mock_sync_manager:
        mock_sync_manager.commit_changes.return_value = True

        result = runner.invoke(main, ["sync", "commit", "-m", "test commit"])
        assert result.exit_code == 0
        assert "Changes committed successfully" in result.output
        mock_sync_manager.commit_changes.assert_called_once_with("test commit")


def test_sync_commit_failure(runner):
    """Test sync commit command failure."""
    with patch("pypet.cli.main_module.sync_manager") as mock_sync_manager:
        mock_sync_manager.commit_changes.return_value = False

        result = runner.invoke(main, ["sync", "commit"])
        assert result.exit_code == 1
        assert "Failed to commit changes" in result.output


def test_sync_pull_command(runner):
    """Test sync pull command."""
    with patch("pypet.cli.main_module.sync_manager") as mock_sync_manager:
        mock_sync_manager.pull_changes.return_value = True

        result = runner.invoke(main, ["sync", "pull"])
        assert result.exit_code == 0
        assert "Changes pulled successfully" in result.output


def test_sync_push_command(runner):
    """Test sync push command."""
    with patch("pypet.cli.main_module.sync_manager") as mock_sync_manager:
        mock_sync_manager.push_changes.return_value = True

        result = runner.invoke(main, ["sync", "push"])
        assert result.exit_code == 0
        assert "Changes pushed successfully" in result.output


def test_sync_sync_command(runner):
    """Test sync sync command (full sync)."""
    with patch("pypet.cli.main_module.sync_manager") as mock_sync_manager:
        mock_sync_manager.sync.return_value = True

        result = runner.invoke(main, ["sync", "sync"])
        assert result.exit_code == 0
        assert "Full sync completed successfully" in result.output
        mock_sync_manager.sync.assert_called_once_with(
            auto_commit=True, commit_message=None
        )


def test_sync_sync_no_commit(runner):
    """Test sync sync command with no-commit flag."""
    with patch("pypet.cli.main_module.sync_manager") as mock_sync_manager:
        mock_sync_manager.sync.return_value = True

        result = runner.invoke(main, ["sync", "sync", "--no-commit"])
        assert result.exit_code == 0
        mock_sync_manager.sync.assert_called_once_with(
            auto_commit=False, commit_message=None
        )


def test_sync_backups_empty(runner):
    """Test sync backups command when no backups exist."""
    with patch("pypet.cli.main_module.sync_manager") as mock_sync_manager:
        mock_sync_manager.list_backups.return_value = []

        result = runner.invoke(main, ["sync", "backups"])
        assert result.exit_code == 0
        assert "No backup files found" in result.output


def test_sync_backups_list(runner):
    """Test sync backups command with existing backups."""
    mock_backup = MagicMock()
    mock_backup.name = "snippets_backup_20250101_120000.toml"
    mock_backup.stat.return_value.st_size = 1024
    mock_backup.stat.return_value.st_mtime = 1640995200  # 2022-01-01 12:00:00

    with patch("pypet.cli.main_module.sync_manager") as mock_sync_manager:
        mock_sync_manager.list_backups.return_value = [mock_backup]

        result = runner.invoke(main, ["sync", "backups"])
        assert result.exit_code == 0
        assert "Available Backups" in result.output
        assert "snippets_backup_20250101_120000.toml" in result.output


def test_sync_restore_command(runner):
    """Test sync restore command."""
    with patch("pypet.cli.main_module.sync_manager") as mock_sync_manager:
        mock_sync_manager.restore_backup.return_value = True

        result = runner.invoke(main, ["sync", "restore", "test_backup.toml"])
        assert result.exit_code == 0
        assert "Successfully restored from test_backup.toml" in result.output


def test_sync_restore_failure(runner):
    """Test sync restore command failure."""
    with patch("pypet.cli.main_module.sync_manager") as mock_sync_manager:
        mock_sync_manager.restore_backup.return_value = False

        result = runner.invoke(main, ["sync", "restore", "nonexistent.toml"])
        assert result.exit_code == 1
        assert "Failed to restore from nonexistent.toml" in result.output


def test_sync_remote_add(runner):
    """Test adding a remote."""
    mock_repo = MagicMock()
    mock_repo.remotes = []
    mock_repo.create_remote = MagicMock()

    with patch("pypet.cli.main_module.sync_manager") as mock_sync_manager:
        mock_sync_manager.is_git_repo = True
        mock_sync_manager.repo = mock_repo

        result = runner.invoke(
            main, ["sync", "remote", "https://github.com/test/repo.git"]
        )
        assert result.exit_code == 0
        assert "Added remote 'origin'" in result.output
        mock_repo.create_remote.assert_called_once_with(
            "origin", "https://github.com/test/repo.git"
        )


def test_sync_remote_update(runner):
    """Test updating an existing remote."""
    mock_remote = MagicMock()
    mock_remote.name = "origin"
    mock_remote.set_url = MagicMock()

    # Create a proper mock for remotes collection
    mock_remotes = MagicMock()
    mock_remotes.__contains__ = MagicMock(return_value=True)  # "origin" in remotes
    mock_remotes.__getitem__ = MagicMock(return_value=mock_remote)  # remotes["origin"]
    mock_remotes.__iter__ = MagicMock(
        return_value=iter([mock_remote])
    )  # for r in remotes

    mock_repo = MagicMock()
    mock_repo.remotes = mock_remotes

    with patch("pypet.cli.main_module.sync_manager") as mock_sync_manager:
        mock_sync_manager.is_git_repo = True
        mock_sync_manager.repo = mock_repo

        result = runner.invoke(
            main, ["sync", "remote", "https://github.com/test/new-repo.git"]
        )
        assert result.exit_code == 0
        assert "Updated remote 'origin'" in result.output
        mock_remote.set_url.assert_called_once_with(
            "https://github.com/test/new-repo.git"
        )


def test_sync_remote_not_git_repo(runner):
    """Test remote command when not in git repo."""
    with patch("pypet.cli.main_module.sync_manager") as mock_sync_manager:
        mock_sync_manager.is_git_repo = False

        result = runner.invoke(
            main, ["sync", "remote", "https://github.com/test/repo.git"]
        )
        assert result.exit_code == 1
        assert "Not in a Git repository" in result.output


def test_sync_auto_enable(runner, tmp_path):
    """Test enabling auto-sync."""
    config_file = tmp_path / "config.toml"

    with (
        patch("pypet.cli.sync_commands.config.config_path", config_file),
        patch("pypet.cli.main_module.sync_manager") as mock_sync_manager,
    ):
        mock_sync_manager.is_git_repo = True
        mock_repo = MagicMock()
        mock_remote = MagicMock()
        mock_remote.name = "origin"
        mock_repo.remotes = [mock_remote]
        mock_sync_manager.repo = mock_repo

        result = runner.invoke(main, ["sync", "auto", "enable"])
        assert result.exit_code == 0
        assert "Auto-sync enabled" in result.output

        # Verify config was set
        config = Config(config_file)
        assert config.auto_sync is True


def test_sync_auto_enable_no_git_repo(runner, tmp_path):
    """Test enabling auto-sync when no git repo."""
    config_file = tmp_path / "config.toml"

    with (
        patch("pypet.cli.sync_commands.config.config_path", config_file),
        patch("pypet.cli.main_module.sync_manager") as mock_sync_manager,
    ):
        mock_sync_manager.is_git_repo = False

        result = runner.invoke(main, ["sync", "auto", "enable"])
        assert result.exit_code == 0
        assert "Auto-sync enabled" in result.output
        assert "Git repository not initialized" in result.output


def test_sync_auto_enable_no_remote(runner, tmp_path):
    """Test enabling auto-sync when no remote configured."""
    config_file = tmp_path / "config.toml"

    with (
        patch("pypet.cli.sync_commands.config.config_path", config_file),
        patch("pypet.cli.main_module.sync_manager") as mock_sync_manager,
    ):
        mock_sync_manager.is_git_repo = True
        mock_repo = MagicMock()
        mock_repo.remotes = []
        mock_sync_manager.repo = mock_repo

        result = runner.invoke(main, ["sync", "auto", "enable"])
        assert result.exit_code == 0
        assert "Auto-sync enabled" in result.output
        assert "No Git remote configured" in result.output


def test_sync_auto_disable(runner, tmp_path):
    """Test disabling auto-sync."""
    config_file = tmp_path / "config.toml"

    with patch("pypet.cli.sync_commands.config.config_path", config_file):
        result = runner.invoke(main, ["sync", "auto", "disable"])
        assert result.exit_code == 0
        assert "Auto-sync disabled" in result.output

        # Verify config was set
        config = Config(config_file)
        assert config.auto_sync is False


def test_sync_auto_status_enabled(runner, tmp_path):
    """Test auto-sync status when enabled."""
    config_file = tmp_path / "config.toml"

    # Set auto-sync to True first
    config = Config(config_file)
    config.auto_sync = True

    with (
        patch("pypet.cli.sync_commands.config.config_path", config_file),
        patch("pypet.cli.main_module.sync_manager") as mock_sync_manager,
    ):
        mock_sync_manager.is_git_repo = True
        mock_repo = MagicMock()
        mock_remote = MagicMock()
        mock_remote.name = "origin"
        mock_repo.remotes = [mock_remote]
        mock_sync_manager.repo = mock_repo

        result = runner.invoke(main, ["sync", "auto", "status"])
        assert result.exit_code == 0
        assert "Auto-Sync Status" in result.output
        assert "Enabled" in result.output


def test_sync_auto_status_disabled(runner, tmp_path):
    """Test auto-sync status when disabled."""
    config_file = tmp_path / "config.toml"

    with (
        patch("pypet.cli.sync_commands.config.config_path", config_file),
        patch("pypet.cli.main_module.sync_manager") as mock_sync_manager,
    ):
        mock_sync_manager.is_git_repo = False

        result = runner.invoke(main, ["sync", "auto", "status"])
        assert result.exit_code == 0
        assert "Auto-Sync Status" in result.output
        assert "Disabled" in result.output
        assert "enable auto-sync" in result.output
