"""Test cases for alias CLI commands"""

from unittest.mock import patch

import pytest
from click.testing import CliRunner

from pypet.alias_manager import AliasManager
from pypet.cli import main
from pypet.storage import Storage


@pytest.fixture
def runner():
    """Create a CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def mock_storage(tmp_path):
    """Create a temporary storage with test snippets."""
    storage = Storage(config_path=tmp_path / "test_snippets.toml")

    # Add test snippets
    storage.add_snippet("ls -la", "List files", alias="ll")
    storage.add_snippet("git status", "Git status", alias="gs")
    storage.add_snippet("pwd", "Print working directory")  # No alias

    return storage


@pytest.fixture
def mock_alias_manager(tmp_path):
    """Create a temporary alias manager."""
    alias_path = tmp_path / "aliases.sh"
    return AliasManager(alias_path)


def test_alias_list_command(runner, mock_storage, mock_alias_manager):
    """Test listing aliases."""
    with (
        patch("pypet.cli.main_module.storage", mock_storage),
        patch("pypet.cli.alias_commands.alias_manager", mock_alias_manager),
    ):
        result = runner.invoke(main, ["alias", "list"])
        assert result.exit_code == 0
        assert "ll" in result.output
        assert "gs" in result.output


def test_alias_list_empty(runner, tmp_path):
    """Test listing aliases when none exist."""
    storage = Storage(config_path=tmp_path / "empty_snippets.toml")

    with patch("pypet.cli.main_module.storage", storage):
        result = runner.invoke(main, ["alias", "list"])
        assert result.exit_code == 0
        assert "No aliases defined" in result.output


def test_alias_add_command(runner, mock_storage, mock_alias_manager):
    """Test adding an alias to a snippet."""
    snippets = mock_storage.list_snippets()
    snippet_id = snippets[2][0]  # Get the snippet without an alias

    with (
        patch("pypet.cli.main_module.storage", mock_storage),
        patch("pypet.cli.alias_commands.alias_manager", mock_alias_manager),
    ):
        result = runner.invoke(main, ["alias", "add", snippet_id, "mypwd"])
        assert result.exit_code == 0
        assert "Added alias" in result.output
        assert "mypwd" in result.output

        # Verify the alias was added to the snippet
        updated_snippet = mock_storage.get_snippet(snippet_id)
        assert updated_snippet.alias == "mypwd"


def test_alias_add_invalid_name(runner, mock_storage):
    """Test adding an invalid alias name."""
    snippets = mock_storage.list_snippets()
    snippet_id = snippets[0][0]

    with patch("pypet.cli.main_module.storage", mock_storage):
        result = runner.invoke(main, ["alias", "add", snippet_id, "my alias!"])
        assert result.exit_code == 0
        assert "Invalid alias name" in result.output


def test_alias_add_nonexistent_snippet(runner, mock_storage):
    """Test adding an alias to a nonexistent snippet."""
    with patch("pypet.cli.main_module.storage", mock_storage):
        result = runner.invoke(main, ["alias", "add", "nonexistent", "myalias"])
        assert result.exit_code == 0
        assert "not found" in result.output


def test_alias_remove_command(runner, mock_storage, mock_alias_manager):
    """Test removing an alias from a snippet."""
    snippets = mock_storage.list_snippets()
    snippet_id = snippets[0][0]  # Get a snippet with an alias

    with (
        patch("pypet.cli.main_module.storage", mock_storage),
        patch("pypet.cli.alias_commands.alias_manager", mock_alias_manager),
    ):
        result = runner.invoke(main, ["alias", "remove", snippet_id])
        assert result.exit_code == 0
        assert "Removed alias" in result.output

        # Verify the alias was removed
        updated_snippet = mock_storage.get_snippet(snippet_id)
        assert not updated_snippet.alias


def test_alias_remove_no_alias(runner, mock_storage):
    """Test removing an alias from a snippet that has none."""
    snippets = mock_storage.list_snippets()
    snippet_id = snippets[2][0]  # Get the snippet without an alias

    with patch("pypet.cli.main_module.storage", mock_storage):
        result = runner.invoke(main, ["alias", "remove", snippet_id])
        assert result.exit_code == 0
        assert "has no alias" in result.output


def test_alias_update_command(runner, mock_storage, mock_alias_manager):
    """Test updating the aliases file."""
    with (
        patch("pypet.cli.main_module.storage", mock_storage),
        patch("pypet.cli.alias_commands.alias_manager", mock_alias_manager),
    ):
        result = runner.invoke(main, ["alias", "update"])
        assert result.exit_code == 0
        assert "Updated aliases file" in result.output
        assert mock_alias_manager.alias_path.exists()


def test_alias_setup_command(runner, mock_alias_manager):
    """Test showing setup instructions."""
    with patch("pypet.cli.alias_commands.alias_manager", mock_alias_manager):
        result = runner.invoke(main, ["alias", "setup"])
        assert result.exit_code == 0
        assert "source" in result.output
        assert "bashrc" in result.output.lower()
        assert "zshrc" in result.output.lower()


def test_alias_setup_with_copy(runner, mock_alias_manager):
    """Test setup command with copy flag."""
    with (
        patch("pypet.cli.alias_commands.alias_manager", mock_alias_manager),
        patch("pyperclip.copy") as mock_copy,
    ):
        result = runner.invoke(main, ["alias", "setup", "--copy"])
        assert result.exit_code == 0
        assert "source" in result.output
        mock_copy.assert_called_once()


def test_alias_show_command(runner, mock_storage, mock_alias_manager):
    """Test showing alias definition for a snippet."""
    snippets = mock_storage.list_snippets()
    snippet_id = snippets[0][0]  # Get a snippet with an alias

    with (
        patch("pypet.cli.main_module.storage", mock_storage),
        patch("pypet.cli.alias_commands.alias_manager", mock_alias_manager),
    ):
        result = runner.invoke(main, ["alias", "show", snippet_id])
        assert result.exit_code == 0
        assert "Alias definition" in result.output


def test_alias_show_no_alias(runner, mock_storage):
    """Test showing alias for a snippet without an alias."""
    snippets = mock_storage.list_snippets()
    snippet_id = snippets[2][0]  # Get the snippet without an alias

    with patch("pypet.cli.main_module.storage", mock_storage):
        result = runner.invoke(main, ["alias", "show", snippet_id])
        assert result.exit_code == 0
        assert "has no alias" in result.output


def test_new_command_with_alias(runner, mock_storage):
    """Test creating a new snippet with an alias."""
    with (
        patch("pypet.cli.main_module.storage", mock_storage),
        patch("pypet.cli.snippet_commands.cli_main.storage", mock_storage),
    ):
        result = runner.invoke(
            main,
            ["new", "echo 'test'", "-d", "Test command", "-a", "mytest"],
        )
        assert result.exit_code == 0
        assert "Added new snippet" in result.output
        assert "Created alias" in result.output
        assert "mytest" in result.output


def test_new_command_with_invalid_alias(runner, mock_storage):
    """Test creating a new snippet with an invalid alias."""
    with patch("pypet.cli.main_module.storage", mock_storage):
        result = runner.invoke(
            main,
            ["new", "echo 'test'", "-a", "my alias!"],
        )
        assert result.exit_code == 0
        assert "Invalid alias name" in result.output


def test_alias_add_duplicate_warning(runner, mock_storage, mock_alias_manager):
    """Test adding a duplicate alias name (should warn)."""
    snippets = mock_storage.list_snippets()
    snippet_id = snippets[2][0]  # Get the snippet without an alias

    with (
        patch("pypet.cli.main_module.storage", mock_storage),
        patch("pypet.cli.alias_commands.alias_manager", mock_alias_manager),
        patch("click.confirm", return_value=False),  # User declines to override
    ):
        result = runner.invoke(main, ["alias", "add", snippet_id, "ll"])
        assert result.exit_code == 0
        # Should show warning about existing alias
        assert "already used" in result.output
