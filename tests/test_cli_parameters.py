"""
Tests for CLI parameter utilities.
"""

import pytest

from pypet.cli_parameters import InteractiveParameterPrompt, ParameterEditorCLI
from pypet.parameters import ParameterMetadata


class TestInteractiveParameterPrompt:
    """Tests for InteractiveParameterPrompt."""

    def test_prompt_detects_parameters_from_command(self, monkeypatch):
        """Test that parameters are detected from command."""
        command = "docker run {{image}} -p {{port}}"
        monkeypatch.setattr("click.prompt", lambda *args, **kwargs: "")
        monkeypatch.setattr("click.confirm", lambda *args, **kwargs: False)
        params = InteractiveParameterPrompt.prompt_for_parameters(
            command, existing_params={}
        )
        assert "image" in params
        assert "port" in params

    def test_prompt_raises_error_on_invalid_command(self, monkeypatch):
        """Test that invalid command raises error."""
        command = "docker run {{123invalid}}"
        monkeypatch.setattr("click.prompt", lambda *args, **kwargs: "")
        monkeypatch.setattr("click.confirm", lambda *args, **kwargs: False)
        with pytest.raises(ValueError):
            InteractiveParameterPrompt.prompt_for_parameters(command)

    def test_confirm_parameters_returns_dict(self, monkeypatch):
        """Test parameter confirmation."""
        params = {
            "image": ParameterMetadata("image"),
            "port": ParameterMetadata("port", default="8080"),
        }
        monkeypatch.setattr("click.confirm", lambda *args, **kwargs: False)
        result = InteractiveParameterPrompt.confirm_parameters(params)
        assert isinstance(result, bool)

    def test_prompt_for_empty_parameters(self, monkeypatch):
        """Test prompting for no parameters."""
        params = {}
        monkeypatch.setattr("click.prompt", lambda *args, **kwargs: "")
        monkeypatch.setattr("click.confirm", lambda *args, **kwargs: False)
        result = InteractiveParameterPrompt.prompt_for_parameters(
            "ls -la", existing_params=params
        )
        assert result == {}


class TestParameterEditorCLI:
    """Tests for ParameterEditorCLI."""

    def test_editor_handles_empty_parameters(self, monkeypatch):
        """Test editor with no parameters."""
        params = {}
        monkeypatch.setattr("click.prompt", lambda *args, **kwargs: "")
        monkeypatch.setattr("click.confirm", lambda *args, **kwargs: False)
        result = ParameterEditorCLI.edit_parameters_prompt(params)
        assert isinstance(result, dict)

    def test_editor_preserves_existing_parameters(self, monkeypatch):
        """Test that existing parameters are preserved."""
        params = {
            "image": ParameterMetadata("image"),
            "port": ParameterMetadata("port", default="8080"),
        }
        monkeypatch.setattr("click.prompt", lambda *args, **kwargs: "")
        monkeypatch.setattr("click.confirm", lambda *args, **kwargs: False)
        result = ParameterEditorCLI.edit_parameters_prompt(params)
        assert "image" in result
        assert "port" in result
