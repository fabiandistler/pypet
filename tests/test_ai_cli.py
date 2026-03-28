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


def test_gen_prompts_for_missing_key(runner, mock_storage, tmp_path):
    cfg = Config(config_path=tmp_path / "config.toml")

    with (
        patch("pypet.cli.main_module.storage", mock_storage),
        patch("pypet.cli.ai_commands.Config", return_value=cfg),
        patch("pypet.cli.ai_commands.generate_snippet") as gen_snippet,
        patch("pypet.cli.ai_commands.Confirm.ask", return_value=True),
        patch("pypet.cli.ai_commands.Prompt.ask", side_effect=["sk-test", ""]),
    ):
        gen_snippet.return_value = {
            "command": "echo {{name}}",
            "description": "Echo a name",
            "tags": ["demo"],
            "parameters": {
                "name": {"name": "name", "default": "world", "description": None}
            },
        }

        result = runner.invoke(main, ["gen", "say hi"])
        assert result.exit_code == 0
        assert "Added new snippet with ID" in result.output
        assert cfg.openrouter_api_key == "sk-test"
        gen_snippet.assert_called_once_with(prompt="say hi", config=cfg)


def test_gen_aborts_when_prompted_api_key_is_blank(runner, mock_storage, tmp_path):
    cfg = Config(config_path=tmp_path / "config.toml")
    cfg.openrouter_api_key = ""

    with (
        patch("pypet.cli.main_module.storage", mock_storage),
        patch("pypet.cli.ai_commands.Config", return_value=cfg),
        patch("pypet.cli.ai_commands.Prompt.ask", return_value="   "),
    ):
        result = runner.invoke(main, ["gen", "say hi"])
        assert result.exit_code == 0
        assert "OpenRouter API key is required" in result.output


def test_gen_prints_error_when_generate_snippet_fails(runner, mock_storage, tmp_path):
    cfg = Config(config_path=tmp_path / "config.toml")
    cfg.openrouter_api_key = "sk-test"

    with (
        patch("pypet.cli.main_module.storage", mock_storage),
        patch("pypet.cli.ai_commands.Config", return_value=cfg),
        patch(
            "pypet.cli.ai_commands.generate_snippet",
            side_effect=OpenRouterAIError("Test error"),
        ),
    ):
        result = runner.invoke(main, ["gen", "say hi"])
        assert result.exit_code == 0
        assert "Error:" in result.output
        assert "Test error" in result.output


def test_gen_does_not_save_when_user_declines(runner, mock_storage, tmp_path):
    cfg = Config(config_path=tmp_path / "config.toml")
    cfg.openrouter_api_key = "sk-test"

    with (
        patch("pypet.cli.main_module.storage", mock_storage),
        patch("pypet.cli.ai_commands.Config", return_value=cfg),
        patch("pypet.cli.ai_commands.generate_snippet") as gen_snippet,
        patch("pypet.cli.ai_commands.Confirm.ask", return_value=False),
    ):
        gen_snippet.return_value = {"command": "echo hi"}
        result = runner.invoke(main, ["gen", "say hi"])
        assert result.exit_code == 0
        assert "Not saved." in result.output
        assert "Added new snippet" not in result.output


def test_gen_updates_aliases_file_when_alias_provided(runner, mock_storage, tmp_path):
    cfg = Config(config_path=tmp_path / "config.toml")
    cfg.openrouter_api_key = "sk-test"

    with (
        patch("pypet.cli.main_module.storage", mock_storage),
        patch("pypet.cli.ai_commands.Config", return_value=cfg),
        patch("pypet.cli.ai_commands.generate_snippet") as gen_snippet,
        patch("pypet.cli.ai_commands.Confirm.ask", return_value=True),
        patch("pypet.cli.ai_commands.Prompt.ask", return_value="myalias"),
        patch(
            "pypet.cli.ai_commands.AliasManager.update_aliases_file"
        ) as mock_update_aliases,
    ):
        gen_snippet.return_value = {"command": "echo hi"}
        result = runner.invoke(main, ["gen", "say hi"])
        assert result.exit_code == 0
        assert "Created alias:" in result.output
        assert "myalias" in result.output
        assert "Run this to activate:" in result.output
        mock_update_aliases.assert_called_once()


def test_build_snippet_from_generated_skips_non_dict_parameter_values():
    data = {
        "command": "test",
        "parameters": {
            "valid": {"name": "valid", "default": "v"},
            "invalid": "string",
            "noname": {},
        },
    }
    snippet = _build_snippet_from_generated(data)
    assert snippet.parameters is not None
    assert "valid" in snippet.parameters
    assert "invalid" not in snippet.parameters
    assert snippet.parameters["noname"].name == "noname"
