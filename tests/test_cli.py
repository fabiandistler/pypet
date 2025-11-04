"""Test cases for the CLI interface"""

from unittest.mock import mock_open, patch

import pytest
from click.testing import CliRunner

from pypet.cli import main
from pypet.storage import Storage


@pytest.fixture
def runner():
    """Create a CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def mock_storage(tmp_path):
    """Create a temporary storage with some test snippets."""
    storage = Storage(config_path=tmp_path / "test_snippets.toml")

    # Add some test snippets
    storage.add_snippet("ls -la", "List files", ["system"])
    storage.add_snippet("git status", "Git status", ["git"])

    return storage


def test_list_command(runner, mock_storage):
    """Test the list command."""
    with patch("pypet.cli.storage", mock_storage):
        result = runner.invoke(main, ["list"])
        assert result.exit_code == 0
        assert "ls -la" in result.output
        assert "git status" in result.output


def test_new_command(runner, mock_storage):
    """Test adding a new snippet."""
    with patch("pypet.cli.storage", mock_storage):
        result = runner.invoke(
            main, ["new", "echo 'test'", "-d", "Test command", "-t", "test,demo"]
        )
        assert result.exit_code == 0
        assert "Added new snippet" in result.output


def test_exec_with_id(runner, mock_storage):
    """Test executing a snippet with direct ID."""
    snippets = mock_storage.list_snippets()
    snippet_id = snippets[0][0]  # Get ID of first snippet

    with (
        patch("pypet.cli.storage", mock_storage),
        patch("rich.prompt.Confirm.ask", return_value=True),
        patch("subprocess.run") as mock_run,
    ):
        result = runner.invoke(main, ["exec", snippet_id])
        assert result.exit_code == 0
        mock_run.assert_called_once()


def test_exec_interactive_selection(runner, mock_storage):
    """Test executing a snippet through interactive selection."""
    with (
        patch("pypet.cli.storage", mock_storage),
        patch("rich.prompt.Prompt.ask", return_value="1"),
        patch("rich.prompt.Confirm.ask", return_value=True),
        patch("subprocess.run") as mock_run,
    ):
        result = runner.invoke(main, ["exec"])
        assert result.exit_code == 0
        mock_run.assert_called_once()


def test_exec_with_edit(runner, mock_storage):
    """Test executing a snippet with editing."""
    snippets = mock_storage.list_snippets()
    snippet_id = snippets[0][0]

    with (
        patch("pypet.cli.storage", mock_storage),
        patch("click.edit", return_value="ls -lah"),
        patch("subprocess.run") as mock_run,
        patch("rich.prompt.Confirm.ask", return_value=True),
    ):
        result = runner.invoke(main, ["exec", snippet_id, "-e"])
        assert result.exit_code == 0
        mock_run.assert_called_once()
        # Verify modified command was used
        assert mock_run.call_args[0][0] == "ls -lah"


def test_exec_cancel(runner, mock_storage):
    """Test cancelling snippet execution."""
    snippets = mock_storage.list_snippets()
    snippet_id = snippets[0][0]

    with (
        patch("pypet.cli.storage", mock_storage),
        patch("rich.prompt.Confirm.ask", return_value=False),
        patch("subprocess.run") as mock_run,
    ):
        result = runner.invoke(main, ["exec", snippet_id])
        assert result.exit_code == 0
        mock_run.assert_not_called()


def test_exec_interactive_invalid_choice(runner, mock_storage):
    """Test invalid input in interactive selection."""
    with (
        patch("pypet.cli.storage", mock_storage),
        patch("rich.prompt.Prompt.ask", side_effect=["invalid", "q"]),
    ):
        result = runner.invoke(main, ["exec"])
        assert result.exit_code == 0
        assert "Please enter a number" in result.output


def test_search_command(runner, mock_storage):
    """Test the search command with different criteria."""
    with patch("pypet.cli.storage", mock_storage):
        # Search by command
        result = runner.invoke(main, ["search", "git"])
        assert result.exit_code == 0
        assert "git status" in result.output

        # Search by description
        result = runner.invoke(main, ["search", "files"])
        assert result.exit_code == 0
        assert "ls -la" in result.output

        # Search by tag
        result = runner.invoke(main, ["search", "system"])
        assert result.exit_code == 0
        assert "ls -la" in result.output


def test_edit_command(runner, mock_storage):
    """Test editing a snippet."""
    snippets = mock_storage.list_snippets()
    snippet_id = snippets[0][0]

    with patch("pypet.cli.storage", mock_storage):
        result = runner.invoke(
            main,
            [
                "edit",
                snippet_id,
                "--command",
                "new command",
                "--description",
                "new description",
                "--tags",
                "tag1,tag2",
            ],
        )
        assert result.exit_code == 0
        assert "Successfully updated snippet" in result.output

        # Verify changes
        snippet = mock_storage.get_snippet(snippet_id)
        assert snippet.command == "new command"
        assert snippet.description == "new description"
        assert snippet.tags == ["tag1", "tag2"]


def test_save_clipboard_command(runner, mock_storage):
    """Test saving from clipboard."""
    with (
        patch("pypet.cli.storage", mock_storage),
        patch("pypet.cli.pyperclip.paste", return_value="git status"),
        patch("pypet.cli.Confirm.ask", return_value=True),
        patch("pypet.cli.Prompt.ask", return_value="Git status check"),
    ):
        result = runner.invoke(main, ["save-clipboard"])
        assert result.exit_code == 0
        assert "Added new snippet with ID" in result.output


def test_save_clipboard_empty(runner, mock_storage):
    """Test saving from empty clipboard."""
    with (
        patch("pypet.cli.storage", mock_storage),
        patch("pypet.cli.pyperclip.paste", return_value=""),
    ):
        result = runner.invoke(main, ["save-clipboard"])
        assert result.exit_code == 0
        assert "Clipboard is empty" in result.output


def test_save_clipboard_with_options(runner, mock_storage):
    """Test saving from clipboard with description and tags."""
    with (
        patch("pypet.cli.storage", mock_storage),
        patch("pypet.cli.pyperclip.paste", return_value="docker ps"),
        patch("pypet.cli.Confirm.ask", return_value=True),
    ):
        result = runner.invoke(
            main,
            [
                "save-clipboard",
                "--description",
                "List Docker containers",
                "--tags",
                "docker,containers",
            ],
        )
        assert result.exit_code == 0
        assert "Added new snippet with ID" in result.output


def test_save_last_command(runner, mock_storage):
    """Test saving from shell history."""
    # Mock a history file with some commands
    history_content = "ls -la\ngit status\npypet list\necho hello\n"

    with (
        patch("pypet.cli.storage", mock_storage),
        patch("pathlib.Path.exists", return_value=True),
        patch("builtins.open", mock_open(read_data=history_content)),
        patch("pypet.cli.Confirm.ask", return_value=True),
        patch("pypet.cli.Prompt.ask", return_value="List files"),
    ):
        result = runner.invoke(main, ["save-last"])
        assert result.exit_code == 0
        assert "Added new snippet with ID" in result.output


def test_save_last_no_history(runner, mock_storage):
    """Test saving from history when no history available."""
    with (
        patch("pypet.cli.storage", mock_storage),
        patch("pathlib.Path.exists", return_value=False),
    ):
        result = runner.invoke(main, ["save-last"])
        assert result.exit_code == 0
        assert "Could not find shell history file" in result.output


def test_edit_file_option(runner, mock_storage):
    """Test editing with --file option."""
    with (
        patch("pypet.cli.storage", mock_storage),
        patch("pypet.cli.subprocess.run") as mock_run,
        patch.dict("os.environ", {"EDITOR": "vim"}),
    ):
        result = runner.invoke(main, ["edit", "--file"])
        assert result.exit_code == 0
        assert "Opened" in result.output
        mock_run.assert_called_once_with(["vim", str(mock_storage.config_path)], check=False)


def test_edit_no_args_error(runner, mock_storage):
    """Test edit command with no arguments shows error."""
    with patch("pypet.cli.storage", mock_storage):
        result = runner.invoke(main, ["edit"])
        assert result.exit_code == 0
        assert "Either provide a snippet ID or use --file" in result.output


def test_delete_command(runner, mock_storage):
    """Test deleting a snippet."""
    snippets = mock_storage.list_snippets()
    snippet_id = snippets[0][0]

    with patch("pypet.cli.storage", mock_storage):
        # Test successful deletion
        result = runner.invoke(main, ["delete", snippet_id])
        assert result.exit_code == 0
        assert "Deleted snippet" in result.output
        assert mock_storage.get_snippet(snippet_id) is None

        # Test deleting non-existent snippet
        result = runner.invoke(main, ["delete", "nonexistent"])
        assert result.exit_code == 0
        assert "Snippet not found" in result.output


def test_exec_special_characters(runner, mock_storage):
    """Test executing commands with special characters."""
    # Add a snippet with special characters
    snippet_id = mock_storage.add_snippet(
        command="echo 'Hello World!' && ls -la",
        description="Command with quotes and operators",
        tags=["test"],
    )

    with (
        patch("pypet.cli.storage", mock_storage),
        patch("rich.prompt.Confirm.ask", return_value=True),
        patch("subprocess.run") as mock_run,
    ):
        result = runner.invoke(main, ["exec", snippet_id])
        assert result.exit_code == 0
        mock_run.assert_called_once()
        # Verify command was passed correctly
        assert mock_run.call_args[0][0] == "echo 'Hello World!' && ls -la"


def test_exec_interactive_invalid_input(runner, mock_storage):
    """Test interactive exec with invalid selection."""
    with (
        patch("pypet.cli.storage", mock_storage),
        patch("rich.prompt.Prompt.ask", side_effect=["invalid", "q"]),
    ):
        result = runner.invoke(main, ["exec"])
        assert result.exit_code == 0
        assert "Please enter a number" in result.output


def test_exec_snippet_not_found(runner, mock_storage):
    """Test executing a non-existent snippet."""
    with patch("pypet.cli.storage", mock_storage):
        result = runner.invoke(main, ["exec", "non-existent-id"])
        assert result.exit_code == 1  # Click's error exit code
        assert "Snippet not found" in result.output


def test_copy_command(runner, mock_storage):
    """Test copying a snippet to clipboard."""
    snippets = mock_storage.list_snippets()
    snippet_id = snippets[0][0]

    with patch("pypet.cli.storage", mock_storage), patch("pyperclip.copy") as mock_copy:
        result = runner.invoke(main, ["copy", snippet_id])
        assert result.exit_code == 0
        mock_copy.assert_called_once_with("ls -la")
        assert "Copied to clipboard" in result.output


def test_copy_interactive_selection(runner, mock_storage):
    """Test copying a snippet through interactive selection."""
    with (
        patch("pypet.cli.storage", mock_storage),
        patch("rich.prompt.Prompt.ask", return_value="1"),
        patch("pyperclip.copy") as mock_copy,
    ):
        result = runner.invoke(main, ["copy"])
        assert result.exit_code == 0
        mock_copy.assert_called_once_with("ls -la")
        assert "Copied to clipboard" in result.output


def test_copy_snippet_not_found(runner, mock_storage):
    """Test copying a non-existent snippet."""
    with patch("pypet.cli.storage", mock_storage):
        result = runner.invoke(main, ["copy", "non-existent-id"])
        assert result.exit_code == 1
        assert "Snippet not found" in result.output


def test_exec_with_copy_option(runner, mock_storage):
    """Test executing a snippet with copy option."""
    snippets = mock_storage.list_snippets()
    snippet_id = snippets[0][0]

    with patch("pypet.cli.storage", mock_storage), patch("pyperclip.copy") as mock_copy:
        result = runner.invoke(main, ["exec", snippet_id, "--copy"])
        assert result.exit_code == 0
        mock_copy.assert_called_once_with("ls -la")
        assert "Copied to clipboard" in result.output


def test_copy_with_clipboard_error(runner, mock_storage):
    """Test copy command when clipboard fails."""
    snippets = mock_storage.list_snippets()
    snippet_id = snippets[0][0]

    with (
        patch("pypet.cli.storage", mock_storage),
        patch("pyperclip.copy", side_effect=Exception("Clipboard error")),
    ):
        result = runner.invoke(main, ["copy", snippet_id])
        assert result.exit_code == 0
        assert "Failed to copy to clipboard" in result.output
        assert "Command:" in result.output
