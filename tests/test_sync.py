"""Test cases for Git synchronization functionality"""

import pytest
from unittest.mock import patch, MagicMock

from pypet.sync import SyncManager


@pytest.fixture
def temp_config_path(tmp_path):
    """Create a temporary config path for testing."""
    config_path = tmp_path / "snippets.toml"
    config_path.write_text('[test]\ncommand = "test"\n')
    return config_path


@pytest.fixture
def sync_manager(temp_config_path):
    """Create a SyncManager instance for testing."""
    return SyncManager(temp_config_path)


def test_sync_manager_initialization(sync_manager, temp_config_path):
    """Test SyncManager initialization."""
    assert sync_manager.config_path == temp_config_path
    assert sync_manager.config_dir == temp_config_path.parent


def test_git_availability(sync_manager):
    """Test git availability detection."""
    # This will depend on whether GitPython is available
    assert isinstance(sync_manager.git_available, bool)


def test_get_status_no_git_repo(sync_manager):
    """Test status when not in a Git repository."""
    status = sync_manager.get_status()

    assert "git_available" in status
    assert "is_git_repo" in status
    assert status["is_git_repo"] == "False"
    assert "config_path" in status
    assert "config_dir" in status


@patch("pypet.sync.GIT_AVAILABLE", True)
@patch("pypet.sync.Repo")
def test_init_git_repo(mock_repo_class, sync_manager):
    """Test Git repository initialization."""
    mock_repo = MagicMock()
    mock_repo_class.init.return_value = mock_repo

    result = sync_manager.init_git_repo()

    assert result is True
    mock_repo_class.init.assert_called_once_with(sync_manager.config_dir)


@patch("pypet.sync.GIT_AVAILABLE", True)
@patch("pypet.sync.Repo")
def test_init_git_repo_with_remote(mock_repo_class, sync_manager):
    """Test Git repository initialization with remote URL."""
    mock_repo = MagicMock()
    mock_repo_class.init.return_value = mock_repo

    remote_url = "https://github.com/user/repo.git"
    result = sync_manager.init_git_repo(remote_url)

    assert result is True
    mock_repo_class.init.assert_called_once_with(sync_manager.config_dir)
    mock_repo.create_remote.assert_called_once_with("origin", remote_url)


@patch("pypet.sync.GIT_AVAILABLE", False)
def test_init_git_repo_no_git(sync_manager):
    """Test Git repository initialization when Git is not available."""
    result = sync_manager.init_git_repo()

    assert result is False


def test_create_backup(sync_manager):
    """Test backup creation."""
    backup_path = sync_manager.create_backup()

    assert backup_path is not None
    assert backup_path.exists()
    assert backup_path.name.startswith("snippets_backup_")
    assert backup_path.suffix == ".toml"


def test_create_backup_no_file(tmp_path):
    """Test backup creation when config file doesn't exist."""
    non_existent_path = tmp_path / "nonexistent.toml"
    sync_manager = SyncManager(non_existent_path)

    backup_path = sync_manager.create_backup()

    assert backup_path is None


def test_commit_changes_no_repo(sync_manager):
    """Test commit when not in a Git repository."""
    # This will naturally fail since sync_manager is not in a git repo
    result = sync_manager.commit_changes("test commit")

    assert result is False


def test_list_backups(sync_manager):
    """Test listing backup files."""
    # Create some mock backup files
    config_dir = sync_manager.config_dir
    backup1 = config_dir / "snippets_backup_20250101_120000.toml"
    backup2 = config_dir / "snippets_backup_20250102_120000.toml"

    backup1.write_text("backup1")
    backup2.write_text("backup2")

    backups = sync_manager.list_backups()

    assert len(backups) == 2
    assert backup2 in backups  # Should be sorted in reverse (newest first)
    assert backup1 in backups


def test_restore_backup(sync_manager):
    """Test restoring from backup."""
    # Create a backup file
    config_dir = sync_manager.config_dir
    backup_path = config_dir / "test_backup.toml"
    backup_content = '[restored]\ncommand = "restored command"\n'
    backup_path.write_text(backup_content)

    result = sync_manager.restore_backup(backup_path)

    assert result is True
    assert sync_manager.config_path.read_text() == backup_content


def test_restore_backup_nonexistent(sync_manager):
    """Test restoring from non-existent backup."""
    nonexistent_path = sync_manager.config_dir / "nonexistent.toml"

    result = sync_manager.restore_backup(nonexistent_path)

    assert result is False


def test_cleanup_old_backups(sync_manager):
    """Test cleaning up old backup files."""
    # Create several backup files
    backup_files = []
    for i in range(8):
        backup_path = (
            sync_manager.config_dir / f"snippets_backup_202401{i:02d}_120000.toml"
        )
        backup_path.write_text("test backup")
        backup_files.append(backup_path)

    # Should delete oldest 3 files (keeping 5)
    deleted_count = sync_manager.cleanup_old_backups(keep_count=5)

    assert deleted_count == 3

    # Check that 5 files remain
    remaining_backups = sync_manager.list_backups()
    assert len(remaining_backups) == 5


def test_cleanup_old_backups_no_excess(sync_manager):
    """Test cleanup when there are no excess backup files."""
    # Create only 3 backup files
    for i in range(3):
        backup_path = (
            sync_manager.config_dir / f"snippets_backup_202401{i:02d}_120000.toml"
        )
        backup_path.write_text("test backup")

    # Should delete nothing (keeping 5, have only 3)
    deleted_count = sync_manager.cleanup_old_backups(keep_count=5)

    assert deleted_count == 0

    # Check that all 3 files remain
    remaining_backups = sync_manager.list_backups()
    assert len(remaining_backups) == 3


def test_pull_changes_no_repo(sync_manager):
    """Test pull when not in a Git repository."""
    result = sync_manager.pull_changes()

    assert result is False


def test_push_changes_no_repo(sync_manager):
    """Test push when not in a Git repository."""
    result = sync_manager.push_changes()

    assert result is False


def test_sync_no_repo(sync_manager):
    """Test full sync when not in a Git repository."""
    result = sync_manager.sync()

    assert result is False
