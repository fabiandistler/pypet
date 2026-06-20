"""Tests for the pypet MCP server (tool adapters over Storage)."""

import asyncio
import contextlib
import sys
from pathlib import Path

import pytest
from click.testing import CliRunner

from pypet.cli import main
from pypet.mcp_server import (
    build_server,
    get_snippet_impl,
    list_snippets_impl,
    save_snippet_impl,
    search_snippets_impl,
)
from pypet.storage import Storage


AGENT_TAG = "agent"


@pytest.fixture
def storage(tmp_path: Path) -> Storage:
    return Storage(config_path=tmp_path / "snippets.toml")


def test_search_returns_human_snippet_as_reviewed(storage):
    storage.add_snippet(
        command="docker ps -a", description="List containers", tags=["docker"]
    )

    results = search_snippets_impl(storage, "docker", AGENT_TAG)

    assert len(results) == 1
    result = results[0]
    assert result["command"] == "docker ps -a"
    assert result["reviewed"] is True
    assert result["source"] == "user"


def test_search_no_match_returns_empty(storage):
    storage.add_snippet(command="docker ps -a")

    assert search_snippets_impl(storage, "kubernetes", AGENT_TAG) == []


def test_get_snippet_includes_autodetected_parameters(storage):
    snippet_id = storage.add_snippet(
        command="ssh {{host}} -p {{port=22}}", description="SSH to a host"
    )

    payload = get_snippet_impl(storage, snippet_id, AGENT_TAG)

    assert payload is not None
    assert payload["id"] == snippet_id
    assert "host" in payload["parameters"]
    assert payload["parameters"]["port"]["default"] == "22"
    assert payload["reviewed"] is True
    assert payload["source"] == "user"


def test_get_missing_snippet_returns_none(storage):
    assert get_snippet_impl(storage, "does-not-exist", AGENT_TAG) is None


def test_list_returns_all_snippets(storage):
    storage.add_snippet(command="command-a")
    storage.add_snippet(command="command-b")

    payloads = list_snippets_impl(storage, AGENT_TAG)

    assert {p["command"] for p in payloads} == {"command-a", "command-b"}


def test_save_snippet_marks_agent_source_and_unreviewed(storage):
    payload = save_snippet_impl(
        storage,
        command="kubectl get pods",
        description="List pods",
        tags=["k8s"],
        parameters=None,
        agent_tag=AGENT_TAG,
    )

    assert payload["source"] == "agent"
    assert payload["reviewed"] is False
    assert AGENT_TAG in payload["tags"]
    assert "k8s" in payload["tags"]

    reread = get_snippet_impl(storage, payload["id"], AGENT_TAG)
    assert reread is not None
    assert reread["reviewed"] is False
    assert reread["source"] == "agent"


def test_save_snippet_does_not_duplicate_agent_tag(storage):
    payload = save_snippet_impl(
        storage,
        command="echo hi",
        description=None,
        tags=["agent"],
        parameters=None,
        agent_tag=AGENT_TAG,
    )

    assert payload["tags"].count(AGENT_TAG) == 1


def test_save_snippet_attaches_parameter_descriptions(storage):
    payload = save_snippet_impl(
        storage,
        command="curl {{url}}",
        description=None,
        tags=None,
        parameters={"url": "Target URL"},
        agent_tag=AGENT_TAG,
    )

    assert payload["parameters"]["url"]["description"] == "Target URL"


def test_build_server_registers_the_four_tools(storage):
    server = build_server(storage=storage, agent_tag=AGENT_TAG)

    tools = asyncio.run(server.list_tools())
    names = {tool.name for tool in tools}

    assert names == {
        "search_snippets",
        "get_snippet",
        "list_snippets",
        "save_snippet",
    }


def test_save_then_search_through_mcp_dispatch(storage):
    server = build_server(storage=storage, agent_tag=AGENT_TAG)

    _, saved = asyncio.run(
        server.call_tool(
            "save_snippet",
            {"command": "kubectl get pods", "description": "List pods"},
        )
    )
    assert saved["source"] == "agent"
    assert saved["reviewed"] is False

    _, found = asyncio.run(server.call_tool("search_snippets", {"query": "kubectl"}))
    results = found["result"]
    assert len(results) == 1
    assert results[0]["command"] == "kubectl get pods"
    assert results[0]["id"] == saved["id"]


def test_mcp_command_without_sdk_prints_install_hint(monkeypatch):
    runner = CliRunner()
    monkeypatch.setitem(sys.modules, "pypet.mcp_server", None)

    result = runner.invoke(main, ["mcp"])

    output = result.output
    with contextlib.suppress(ValueError):
        output += result.stderr

    assert result.exit_code != 0
    assert "pip install" in output
    assert "mcp" in output.lower()
