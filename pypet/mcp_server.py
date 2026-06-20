"""MCP server exposing pypet snippets to AI agents.

The stdio transport is JSON-RPC over stdout, so this module imports only the
storage/config/models layer -- never ``pypet.cli``, which builds a stdout
``Console`` at import time -- and keeps any diagnostics on stderr.
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from .config import Config
from .models import Parameter, Snippet
from .storage import Storage


def _snippet_payload(
    snippet_id: str, snippet: Snippet, agent_tag: str
) -> dict[str, Any]:
    tags = snippet.tags or []
    reviewed = not (agent_tag and agent_tag in tags)
    parameters = {
        name: {"default": param.default, "description": param.description}
        for name, param in snippet.get_all_parameters().items()
    }
    return {
        "id": snippet_id,
        "command": snippet.command,
        "description": snippet.description,
        "tags": tags,
        "parameters": parameters,
        "created_at": snippet.created_at.isoformat() if snippet.created_at else None,
        "reviewed": reviewed,
        "source": "user" if reviewed else "agent",
    }


def search_snippets_impl(
    storage: Storage, query: str, agent_tag: str
) -> list[dict[str, Any]]:
    return [
        _snippet_payload(snippet_id, snippet, agent_tag)
        for snippet_id, snippet in storage.search_snippets(query)
    ]


def get_snippet_impl(
    storage: Storage, snippet_id: str, agent_tag: str
) -> dict[str, Any] | None:
    snippet = storage.get_snippet(snippet_id)
    if snippet is None:
        return None
    return _snippet_payload(snippet_id, snippet, agent_tag)


def list_snippets_impl(storage: Storage, agent_tag: str) -> list[dict[str, Any]]:
    return [
        _snippet_payload(snippet_id, snippet, agent_tag)
        for snippet_id, snippet in storage.list_snippets()
    ]


def save_snippet_impl(
    storage: Storage,
    command: str,
    description: str | None,
    tags: list[str] | None,
    parameters: dict[str, str] | None,
    agent_tag: str,
) -> dict[str, Any]:
    final_tags = list(tags or [])
    if agent_tag and agent_tag not in final_tags:
        final_tags.append(agent_tag)

    parameter_objects = None
    if parameters:
        parameter_objects = {
            name: Parameter(name=name, description=param_description)
            for name, param_description in parameters.items()
        }

    snippet_id = storage.add_snippet(
        command=command,
        description=description,
        tags=final_tags,
        parameters=parameter_objects,
    )
    snippet = storage.get_snippet(snippet_id)
    assert snippet is not None
    return _snippet_payload(snippet_id, snippet, agent_tag)


def build_server(
    storage: Storage | None = None, agent_tag: str | None = None
) -> FastMCP:
    active_storage = storage or Storage()
    tag = agent_tag if agent_tag is not None else Config().agent_snippet_tag

    server = FastMCP("pypet")

    @server.tool()
    def search_snippets(query: str) -> list[dict[str, Any]]:
        """Search saved pypet snippets by command, description, tags, or parameters.

        Each result carries a "reviewed" flag and "source" ("user" or "agent").
        Treat unreviewed, agent-sourced snippets with extra caution -- a human has
        not vetted them yet.
        """
        return search_snippets_impl(active_storage, query, tag)

    @server.tool()
    def get_snippet(snippet_id: str) -> dict[str, Any] | None:
        """Get one pypet snippet by id, with its parameters and trust flags."""
        return get_snippet_impl(active_storage, snippet_id, tag)

    @server.tool()
    def list_snippets() -> list[dict[str, Any]]:
        """List all saved pypet snippets with their trust flags."""
        return list_snippets_impl(active_storage, tag)

    @server.tool()
    def save_snippet(
        command: str,
        description: str | None = None,
        tags: list[str] | None = None,
        parameters: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Save a new command as a pypet snippet for later reuse.

        Use pypet placeholders such as {{name}} or {{name=default}} for the
        variable parts of the command. "parameters" optionally maps a placeholder
        name to a human-readable description. The snippet is tagged as agent-sourced
        and marked unreviewed until a human vets it.
        """
        return save_snippet_impl(
            active_storage, command, description, tags, parameters, tag
        )

    return server


def run() -> None:
    """Run the pypet MCP server over stdio."""
    build_server().run(transport="stdio")
