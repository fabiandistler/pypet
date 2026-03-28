"""CLI tests for AI snippet generation."""

from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from pypet.ai import OpenRouterAIError
from pypet.cli import main
from pypet.cli.ai_commands import _build_snippet_from_generated
from pypet.config import Config
from pypet.storage import Storage


@pytest.fixture(autouse=True)
def disable_auto_sync():
    with patch("pypet.cli.main_module._auto_sync_if_enabled"):
        yield


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def mock_storage(tmp_path: Path):
    return Storage(config_path=tmp_path / "snippets.toml")


def test_gen_saves_snippet_when_alias_not_provided(runner, mock_storage, tmp_path):
    cfg = Config(config_path=tmp_path / "config.toml")
    cfg.openrouter_api_key = "sk-test"

    with (
        patch("pypet.cli.main_module.storage", mock_storage),
        patch("pypet.cli.ai_commands.Config", return_value=cfg),
        patch("pypet.cli.ai_commands.generate_snippet") as gen_snippet,
        patch("pypet.cli.ai_commands.Confirm.ask", return_value=True),
        patch("pypet.cli.ai_commands.Prompt.ask", return_value=""),  # No alias provided
    ):
        gen_snippet.return_value = {"command": "echo hi"}
        result = runner.invoke(main, ["gen", "say hi"])
        assert result.exit_code == 0, f"Expected exit code 0, but got {result.exit_code}"
        assert "Added new snippet with ID" in result.output
        assert "Created alias:" not in result.output # Alias creation should not happen


def test_gen_handles_empty_tags_and_parameters(runner, mock_storage, tmp_path):
    cfg = Config(config_path=tmp_path / "config.toml")
    cfg.openrouter_api_key = "sk-test"

    with (
        patch("pypet.cli.main_module.storage", mock_storage),
        patch("pypet.cli.ai_commands.Config", return_value=cfg),
        patch("pypet.cli.ai_commands.generate_snippet") as gen_snippet,
        patch("pypet.cli.ai_commands.Confirm.ask", return_value=True),
    ):
        gen_snippet.return_value = {
            "command": "echo",
            "description": "An empty command",
            "tags": [],
            "parameters": {},
        }
        result = runner.invoke(main, ["gen", "say hi"])
        assert result.exit_code == 0, f"Expected exit code 0, but got {result.exit_code}"
        assert "Added new snippet with ID" in result.output
        stored_snippets = mock_storage.get_all_snippets()
        assert len(stored_snippets) == 1
        saved_snippet = stored_snippets[0]
        assert saved_snippet.tags == []
        assert saved_snippet.parameters == {}


def test_gen_does_not_prompt_for_key_if_already_set(runner, mock_storage, tmp_path):
    cfg = Config(config_path=tmp_path / "config.toml")
    cfg.openrouter_api_key = "sk-test-from-config" # Key is already set

    with (
        patch("pypet.cli.main_module.storage", mock_storage),
        patch("pypet.cli.ai_commands.Config", return_value=cfg),
        patch("pypet.cli.ai_commands.generate_snippet") as gen_snippet,
        patch("pypet.cli.ai_commands.Confirm.ask", return_value=True),
        patch("pypet.cli.ai_commands.Prompt.ask") as mock_prompt_ask, # Mock Prompt.ask to check if it's called
    ):
        gen_snippet.return_value = {"command": "echo hi"}
        result = runner.invoke(main, ["gen", "say hi"])
        assert result.exit_code == 0, f"Expected exit code 0, but got {result.exit_code}"
        assert "Added new snippet with ID" in result.output
        mock_prompt_ask.assert_not_called()


def test_gen_handles_non_dict_generated_snippet(runner, mock_storage, tmp_path):
    cfg = Config(config_path=tmp_path / "config.toml")
    cfg.openrouter_api_key = "sk-test"

    with (
        patch("pypet.cli.main_module.storage", mock_storage),
        patch("pypet.cli.ai_commands.Config", return_value=cfg),
        patch("pypet.cli.ai_commands.generate_snippet") as gen_snippet,
    ):
        gen_snippet.return_value = "this is not a dict" # Invalid return type
        result = runner.invoke(main, ["gen", "say hi"])
        assert result.exit_code == 0, f"Expected exit code 0, but got {result.exit_code}"
        assert "Error:" in result.output
        assert "Generated snippet must be a JSON object." in result.output


def test_gen_handles_malformed_json_from_generate_snippet(runner, mock_storage, tmp_path):
    cfg = Config(config_path=tmp_path / "config.toml")
    cfg.openrouter_api_key = "sk-test"

    with (
        patch("pypet.cli.main_module.storage", mock_storage),
        patch("pypet.cli.ai_commands.Config", return_value=cfg),
        patch("pypet.cli.ai_commands.generate_snippet") as gen_snippet,
    ):
        malformed_ai_response = {
            "description": "This response is missing the command key",
            "tags": [],
            "parameters": {}
        }
        gen_snippet.return_value = malformed_ai_response
        
        result = runner.invoke(main, ["gen", "say hi"])
        assert result.exit_code == 0, f"Expected exit code 0, but got {result.exit_code}"
        assert "Error:" in result.output
        assert "Generated snippet is missing a valid 'command'." in result.output


def test_gen_updates_aliases_file_when_no_alias_provided(runner, mock_storage, tmp_path):
    cfg = Config(config_path=tmp_path / "config.toml")
    cfg.openrouter_api_key = "sk-test"

    with (
        patch("pypet.cli.main_module.storage", mock_storage),
        patch("pypet.cli.ai_commands.Config", return_value=cfg),
        patch("pypet.cli.ai_commands.generate_snippet") as gen_snippet,
        patch("pypet.cli.ai_commands.Confirm.ask", return_value=True),
        patch("pypet.cli.ai_commands.Prompt.ask", return_value=""),  # No alias provided
        patch(
            "pypet.cli.ai_commands.AliasManager.update_aliases_file"
        ) as mock_update_aliases,
        patch("pypet.cli.ai_commands.AliasManager", autospec=True) 
    ):
        gen_snippet.return_value = {"command": "echo hi"}
        result = runner.invoke(main, ["gen", "say hi"])
        assert result.exit_code == 0, f"Expected exit code 0, but got {result.exit_code}"
        mock_update_aliases.assert_not_called()
