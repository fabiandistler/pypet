"""CLI tests for AI snippet generation."""

from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from pypet.cli import main
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
