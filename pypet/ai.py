"""AI snippet generation for pypet.

This module provides a zero-dependency client for OpenRouter's
OpenAI-compatible chat completions endpoint.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from .config import Config


OPENROUTER_CHAT_COMPLETIONS_URL = "https://openrouter.ai/api/v1/chat/completions"


class OpenRouterAIError(RuntimeError):
    """Raised when OpenRouter returns an error or invalid data."""


def _system_prompt() -> str:
    return (
        "You are an assistant that generates shell snippets for a tool called pypet. "
        "Given the user's intent, produce a single JSON object that matches the "
        "following schema exactly (no extra keys, no markdown, no surrounding text):\n\n"
        "{\n"
        '  "command": string,\n'
        '  "description": string | null,\n'
        '  "tags": string[],\n'
        '  "parameters": {\n'
        '    "<paramName>": {\n'
        '      "name": string,\n'
        '      "default": string | null,\n'
        '      "description": string | null\n'
        "    }\n"
        "  }\n"
        "}\n\n"
        "Rules:\n"
        "- 'command' must use pypet parameter placeholders. Prefer the new syntax: {{param}}.\n"
        "- Provide only the parameters needed by the command.\n"
        "- 'tags' should be 0-5 short strings.\n"
        "- Do not include backticks or code fences.\n"
        "- Return ONLY valid JSON."
    )


def _strip_to_json(text: str) -> str:
    """Best-effort extraction if the model adds leading/trailing text."""
    text = text.strip()
    if not text:
        return text
    # Fast path: already a JSON object.
    if text.startswith("{") and text.endswith("}"):
        return text

    # Best-effort: first '{' to last '}'.
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return text
    return text[start : end + 1]


def _build_request_body(prompt: str, model: str) -> dict[str, Any]:
    return {
        "model": model,
        "messages": [
            {"role": "system", "content": _system_prompt()},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
    }


def generate_snippet(prompt: str, config: Config | None = None) -> dict[str, Any]:
    """Generate a snippet dict from a natural language prompt."""
    cfg = config or Config()
    api_key = cfg.resolve_openrouter_api_key()
    model = cfg.resolve_ai_model()

    if not api_key:
        raise OpenRouterAIError("Missing OpenRouter API key.")
    if not model:
        raise OpenRouterAIError("Missing AI model configuration.")

    body = _build_request_body(prompt=prompt, model=model)
    payload = json.dumps(body).encode("utf-8")

    req = urllib.request.Request(
        OPENROUTER_CHAT_COMPLETIONS_URL,
        data=payload,
        method="POST",
    )
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", f"Bearer {api_key}")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
    except (TimeoutError, urllib.error.HTTPError, urllib.error.URLError) as e:
        raise OpenRouterAIError(f"OpenRouter request failed: {e}") from e

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise OpenRouterAIError(f"OpenRouter returned malformed JSON: {e}") from e

    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as e:
        raise OpenRouterAIError("OpenRouter response shape was unexpected.") from e

    content_json = _strip_to_json(content)
    try:
        snippet = json.loads(content_json)
    except json.JSONDecodeError as e:
        raise OpenRouterAIError(f"Model returned malformed JSON: {e}") from e

    # Validate and normalize keys expected by Snippet.from_dict.
    if not isinstance(snippet, dict):
        raise OpenRouterAIError("Generated snippet must be a JSON object.")

    command = snippet.get("command")
    if not isinstance(command, str) or not command.strip():
        raise OpenRouterAIError("Generated snippet is missing a valid 'command'.")

    description = snippet.get("description")
    if description is not None and not isinstance(description, str):
        description = str(description)

    tags = snippet.get("tags")
    if tags is None:
        tags = []
    if not isinstance(tags, list):
        raise OpenRouterAIError("Generated snippet 'tags' must be a list.")
    tags = [str(t) for t in tags]

    parameters = snippet.get("parameters")
    if parameters is None:
        parameters = {}
    if not isinstance(parameters, dict):
        raise OpenRouterAIError("Generated snippet 'parameters' must be an object.")

    normalized_params: dict[str, dict[str, Any]] = {}
    for name, param in parameters.items():
        if not isinstance(name, str):
            continue
        if not isinstance(param, dict):
            continue
        normalized_params[name] = {
            "name": str(param.get("name") or name),
            "default": param.get("default"),
            "description": param.get("description"),
        }

    return {
        "command": command,
        "description": description,
        "tags": tags,
        "parameters": normalized_params,
    }
