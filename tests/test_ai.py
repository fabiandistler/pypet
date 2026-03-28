"""Tests for pypet AI snippet generation."""

import json
from unittest.mock import patch

import pytest

from pypet.ai import OpenRouterAIError, generate_snippet
from pypet.config import Config


class DummyResponse:
    def __init__(self, text: str):
        self._text = text

    def read(self) -> bytes:
        return self._text.encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_generate_snippet_normalizes_output(tmp_path):
    cfg = Config(config_path=tmp_path / "config.toml")
    cfg.openrouter_api_key = "sk-test"
    cfg.ai_model = "test-model"

    model_return = {
        "command": "echo {{name}}",
        "description": "Echo a name",
        "tags": ["demo"],
        "parameters": {
            "name": {"name": "name", "default": "world", "description": None}
        },
    }

    openrouter_response = {
        "choices": [
            {
                "message": {
                    "content": json.dumps(model_return),
                }
            }
        ]
    }

    with patch("urllib.request.urlopen") as urlopen:
        urlopen.return_value = DummyResponse(json.dumps(openrouter_response))

        out = generate_snippet("say hi", config=cfg)

    assert out["command"] == "echo {{name}}"
    assert out["description"] == "Echo a name"
    assert out["tags"] == ["demo"]
    assert out["parameters"]["name"]["default"] == "world"


def test_generate_snippet_rejects_missing_command(tmp_path):
    cfg = Config(config_path=tmp_path / "config.toml")
    cfg.openrouter_api_key = "sk-test"
    cfg.ai_model = "test-model"

    model_return = {"description": "x", "tags": [], "parameters": {}}
    openrouter_response = {
        "choices": [
            {
                "message": {
                    "content": json.dumps(model_return),
                }
            }
        ]
    }

    with patch("urllib.request.urlopen") as urlopen:
        urlopen.return_value = DummyResponse(json.dumps(openrouter_response))

        with pytest.raises(OpenRouterAIError):
            generate_snippet("prompt", config=cfg)
