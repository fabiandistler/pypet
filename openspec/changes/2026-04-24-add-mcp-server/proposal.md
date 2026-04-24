## Why

Developers increasingly drive their terminal work through AI coding agents
(Claude Code, Cursor, Copilot CLI). In that workflow, a human-facing
snippet manager is bypassed: the agent generates commands from scratch
each time and has no memory of the user's personal conventions, flags,
or project-specific workflows.

Exposing pypet's snippet library via the Model Context Protocol (MCP)
repositions the tool as a **long-term memory layer for AI agents**. The
agent gains tools to search, read, and create pypet snippets, and can
use the user's curated commands instead of re-deriving them. This
complements, rather than competes with, AI agents.

## What Changes

- Add a new `pypet mcp` subcommand that starts an MCP server on stdio.
- Add a thin server module `pypet/mcp_server.py` built on the official
  `mcp` Python SDK, exposing pypet's `Storage` through MCP tools.
- Expose the following MCP tools (v1):
  - `search_snippets(query, tag?)` — full-text search, optionally filtered by tag.
  - `list_snippets(tag?)` — enumerate snippets (optionally filtered by tag).
  - `get_snippet(snippet_id)` — fetch one snippet including parameter schema.
  - `resolve_snippet(snippet_id, parameters)` — substitute parameter
    placeholders and return the final command string **without executing it**.
  - `create_snippet(command, description, tags?, parameters?)` —
    persist a new snippet to the user's library.
- Treat `mcp` as an **optional extra** (`pip install pypet-cli[mcp]`) so
  the core CLI keeps its fast, small-footprint install.
- Document the integration for Claude Code and Claude Desktop in the README.

## Capabilities

### New Capabilities

- `mcp-server`: Exposes pypet snippets to AI agents via the Model Context
  Protocol, turning the local snippet library into shared memory across
  agent sessions.

### Modified Capabilities

None. The MCP server is a new frontend over the existing `Storage` API
and does not alter snippet semantics or on-disk format.

## Impact

- New module `pypet/mcp_server.py`.
- New CLI command file `pypet/cli/mcp_commands.py` (Click integration).
- New optional dependency group `[project.optional-dependencies].mcp =
  ["mcp>=1.0"]` in `pyproject.toml`.
- New test file `tests/test_mcp_server.py`.
- README section with example client configuration.
- No changes to `Storage`, `models.py`, or the TOML snippet format.
- No impact on users who do not install the `mcp` extra.

## Non-Goals

- **No snippet execution via MCP.** An `execute_snippet` tool is deliberately
  omitted from v1. Agents should call `resolve_snippet` and then run the
  resolved command through their own shell tool, keeping the user in the loop.
- **No HTTP/SSE transport in v1.** stdio is sufficient for every current
  MCP client (Claude Desktop, Claude Code, Cursor). Remote transport can
  be added later if needed.
- **No authentication layer.** The server runs locally under the user's
  shell account and only accesses the user's own snippet file.
- **No agent-facing telemetry.** We do not track which snippets agents
  use; that is out of scope and would conflict with the project's
  privacy-first stance.
