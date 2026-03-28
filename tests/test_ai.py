"""Tests for pypet AI snippet generation."""

import json
import urllib.error
from unittest.mock import patch

import pytest

from pypet.ai import OpenRouterAIError, _strip_to_json, generate_snippet
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


def test_generate_snippet_missing_api_key(tmp_path):
    cfg = Config(config_path=tmp_path / "config.toml")
    cfg.openrouter_api_key = ""
    with pytest.raises(OpenRouterAIError, match="Missing OpenRouter API key"):
        generate_snippet("prompt", config=cfg)


def test_generate_snippet_missing_model(tmp_path):
    cfg = Config(config_path=tmp_path / "config.toml")
    cfg.openrouter_api_key = "sk-test"
    cfg.ai_model = ""
    with pytest.raises(OpenRouterAIError, match="Missing AI model configuration"):
        generate_snippet("prompt", config=cfg)


def test_generate_snippet_request_failure(tmp_path):
    cfg = Config(config_path=tmp_path / "config.toml")
    cfg.openrouter_api_key = "sk-test"
    cfg.ai_model = "test-model"

    with (
        patch(
            "urllib.request.urlopen", side_effect=urllib.error.URLError("test error")
        ),
        pytest.raises(OpenRouterAIError, match="OpenRouter request failed"),
    ):
        generate_snippet("prompt", config=cfg)


def test_generate_snippet_malformed_openrouter_json(tmp_path):
    cfg = Config(config_path=tmp_path / "config.toml")
    cfg.openrouter_api_key = "sk-test"
    cfg.ai_model = "test-model"

    with patch("urllib.request.urlopen") as urlopen:
        urlopen.return_value = DummyResponse("not json")
        with pytest.raises(
            OpenRouterAIError, match="OpenRouter returned malformed JSON"
        ):
            generate_snippet("prompt", config=cfg)


def test_generate_snippet_unexpected_response_shape(tmp_path):
    cfg = Config(config_path=tmp_path / "config.toml")
    cfg.openrouter_api_key = "sk-test"
    cfg.ai_model = "test-model"

    with patch("urllib.request.urlopen") as urlopen:
        urlopen.return_value = DummyResponse(json.dumps({"choices": []}))
        with pytest.raises(
            OpenRouterAIError, match="OpenRouter response shape was unexpected"
        ):
            generate_snippet("prompt", config=cfg)


def test_strip_to_json():
    assert _strip_to_json('{"a": 1}') == '{"a": 1}'
    assert (
        _strip_to_json('Here is your json:\n```json\n{"a": 1}\n```\nEnjoy!')
        == '{"a": 1}'
    )
    assert _strip_to_json("no json here") == "no json here"
    assert _strip_to_json("{ incomplete") == "{ incomplete"
    assert _strip_to_json("   ") == ""


def test_generate_snippet_malformed_model_json(tmp_path):
    cfg = Config(config_path=tmp_path / "config.toml")
    cfg.openrouter_api_key = "sk-test"
    cfg.ai_model = "test-model"

    openrouter_response = {"choices": [{"message": {"content": "not a json object"}}]}
    with patch("urllib.request.urlopen") as urlopen:
        urlopen.return_value = DummyResponse(json.dumps(openrouter_response))
        with pytest.raises(OpenRouterAIError, match="Model returned malformed JSON"):
            generate_snippet("prompt", config=cfg)


def test_generate_snippet_non_dict_snippet(tmp_path):
    cfg = Config(config_path=tmp_path / "config.toml")
    cfg.openrouter_api_key = "sk-test"
    cfg.ai_model = "test-model"

    openrouter_response = {"choices": [{"message": {"content": '"string snippet"'}}]}
    with patch("urllib.request.urlopen") as urlopen:
        urlopen.return_value = DummyResponse(json.dumps(openrouter_response))
        with pytest.raises(
            OpenRouterAIError, match="Generated snippet must be a JSON object"
        ):
            generate_snippet("prompt", config=cfg)


def test_generate_snippet_invalid_command(tmp_path):
    cfg = Config(config_path=tmp_path / "config.toml")
    cfg.openrouter_api_key = "sk-test"
    cfg.ai_model = "test-model"

    openrouter_response = {"choices": [{"message": {"content": '{"command": "  "}'}}]}
    with patch("urllib.request.urlopen") as urlopen:
        urlopen.return_value = DummyResponse(json.dumps(openrouter_response))
        with pytest.raises(
            OpenRouterAIError, match="Generated snippet is missing a valid 'command'"
        ):
            generate_snippet("prompt", config=cfg)


def test_generate_snippet_tags_normalization(tmp_path):
    cfg = Config(config_path=tmp_path / "config.toml")
    cfg.openrouter_api_key = "sk-test"
    cfg.ai_model = "test-model"

    openrouter_response = {
        "choices": [{"message": {"content": '{"command": "ls", "tags": null}'}}]
    }
    with patch("urllib.request.urlopen") as urlopen:
        urlopen.return_value = DummyResponse(json.dumps(openrouter_response))
        out = generate_snippet("prompt", config=cfg)
        assert out["tags"] == []

    openrouter_response = {
        "choices": [{"message": {"content": '{"command": "ls", "tags": "not a list"}'}}]
    }
    with patch("urllib.request.urlopen") as urlopen:
        urlopen.return_value = DummyResponse(json.dumps(openrouter_response))
        with pytest.raises(
            OpenRouterAIError, match="Generated snippet 'tags' must be a list"
        ):
            generate_snippet("prompt", config=cfg)


def test_generate_snippet_parameters_normalization(tmp_path):
    cfg = Config(config_path=tmp_path / "config.toml")
    cfg.openrouter_api_key = "sk-test"
    cfg.ai_model = "test-model"

    openrouter_response = {
        "choices": [{"message": {"content": '{"command": "ls", "parameters": null}'}}]
    }
    with patch("urllib.request.urlopen") as urlopen:
        urlopen.return_value = DummyResponse(json.dumps(openrouter_response))
        out = generate_snippet("prompt", config=cfg)
        assert out["parameters"] == {}

    openrouter_response = {
        "choices": [
            {"message": {"content": '{"command": "ls", "parameters": "not dict"}'}}
        ]
    }
    with patch("urllib.request.urlopen") as urlopen:
        urlopen.return_value = DummyResponse(json.dumps(openrouter_response))
        with pytest.raises(
            OpenRouterAIError, match="Generated snippet 'parameters' must be an object"
        ):
            generate_snippet("prompt", config=cfg)

    # invalid parameter entries
    openrouter_response = {
        "choices": [
            {
                "message": {
                    "content": json.dumps(
                        {
                            "command": "ls",
                            "parameters": {
                                "valid": {"name": "valid_name", "default": "val"},
                                "invalid_type": "string instead of dict",
                                "no_name": {"default": "val2"},
                            },
                        }
                    )
                }
            }
        ]
    }
    with patch("urllib.request.urlopen") as urlopen:
        urlopen.return_value = DummyResponse(json.dumps(openrouter_response))
        out = generate_snippet("prompt", config=cfg)
        assert "invalid_type" not in out["parameters"]
        assert out["parameters"]["valid"]["name"] == "valid_name"
        assert out["parameters"]["no_name"]["name"] == "no_name"  # defaults to key

    with patch("urllib.request.urlopen") as urlopen:
        urlopen.return_value = DummyResponse(json.dumps(openrouter_response))
        with patch(
            "json.loads",
            side_effect=[
                openrouter_response,
                {
                    "command": "ls",
                    "parameters": {123: {"name": "invalid", "default": "val"}},
                },
            ],
        ):
            out = generate_snippet("prompt", config=cfg)
            assert 123 not in out["parameters"]


def test_generate_snippet_description_normalization(tmp_path):
    cfg = Config(config_path=tmp_path / "config.toml")
    cfg.openrouter_api_key = "sk-test"
    cfg.ai_model = "test-model"

    openrouter_response = {
        "choices": [{"message": {"content": '{"command": "ls", "description": 123}'}}]
    }
    with patch("urllib.request.urlopen") as urlopen:
        urlopen.return_value = DummyResponse(json.dumps(openrouter_response))
        out = generate_snippet("prompt", config=cfg)
        assert out["description"] == "123" # Should be converted to string
