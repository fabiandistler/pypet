## Context

pypet today is a human-facing CLI: a user types `pypet search git`,
picks a snippet, and executes it. With AI coding agents taking over
much of the direct terminal interaction, that interaction model is
increasingly bypassed — agents regenerate commands from scratch each
session instead of reusing the user's curated library.

The Model Context Protocol (MCP) is the emerging standard for exposing
local tools and data sources to AI agents. Claude Desktop, Claude Code,
Cursor, and a growing set of clients consume MCP servers over stdio.
By shipping pypet as an MCP server, we make the user's snippet library
a first-class capability for their agent.

## Goals / Non-Goals

**Goals:**

- Expose pypet snippets to any MCP-compatible client with a single
  command: `pypet mcp`.
- Reuse the existing `Storage` API without duplication.
- Keep the core `pypet-cli` install footprint unchanged (the `mcp`
  dependency is opt-in via `pip install pypet-cli[mcp]`).
- Provide safe, read-heavy tools plus a write tool (`create_snippet`)
  so the agent can persist newly-discovered commands.
- Resolve parameter placeholders server-side so the agent receives
  ready-to-run command strings.

**Non-Goals:**

- Executing snippets from the MCP server. The agent decides whether
  and how to run the resolved command using its own shell tool,
  preserving the user's approval flow.
- Supporting MCP transports beyond stdio in v1.
- Adding authentication or ACLs. The server is a local, per-user
  process with the same file-system authority as the CLI.
- Exposing sync, alias, or AI-generation commands via MCP in v1. They
  are out of scope for the memory-layer use case and can be added
  later if justified.

## Decisions

**1. Use the official `mcp` Python SDK as an optional extra.**

- We add a new optional dependency group `mcp = ["mcp>=1.0"]` in
  `pyproject.toml`. Users install it with `pip install pypet-cli[mcp]`.
- The `pypet mcp` command imports the SDK lazily inside the command
  handler and raises a friendly error with install instructions if the
  extra is missing.
- **Rationale:** The MCP protocol is non-trivial to implement correctly
  (stdio framing, JSON-RPC, capability negotiation). The SDK is
  maintained by Anthropic and used by every reference server. Making
  it optional keeps the zero-cost install that pypet's audience expects
  for a simple snippet manager.

**2. stdio transport only in v1.**

- The server runs under `pypet mcp` using the SDK's `stdio_server()`
  context manager.
- **Rationale:** Every target client (Claude Desktop, Claude Code,
  Cursor) supports stdio. HTTP/SSE adds deployment complexity (ports,
  auth) and is unnecessary for a per-user local tool. We can add it
  later without breaking changes.

**3. Five tools, read-heavy, with a deliberate omission of `execute`.**

Exposed tools:

- `search_snippets(query: str, tag: str | None)` — wraps
  `Storage.search_snippets`. Returns `[{id, command, description, tags,
  parameters}]`.
- `list_snippets(tag: str | None)` — wraps `Storage.list_snippets`,
  with in-memory tag filtering.
- `get_snippet(snippet_id: str)` — wraps `Storage.get_snippet`,
  including the full parameter schema (name, default, description).
- `resolve_snippet(snippet_id: str, parameters: dict[str, str])` —
  reuses the existing parameter-substitution logic from
  `pypet/parameters.py` and returns `{command: str}`. Does **not**
  execute.
- `create_snippet(command, description, tags?, parameters?)` — wraps
  `Storage.add_snippet`, returns the new snippet ID.

Deliberately omitted:

- `execute_snippet`: letting the agent run shell commands directly
  removes the user's review step. The agent already has a shell tool
  in every target client; we hand it a resolved string and let its
  existing approval flow apply.
- `delete_snippet`, `update_snippet`: destructive and easy to misuse.
  Users can invoke them through the CLI when needed.

**4. Return snippet IDs verbatim.**

- Tool responses include the same short IDs the CLI uses, so agents can
  cross-reference what the user sees in `pypet list`.
- **Rationale:** Consistency between the human and agent views is the
  whole point of the feature.

**5. Error surface: raise, let the SDK convert.**

- Tool handlers raise plain exceptions (e.g. `ValueError` for unknown
  IDs). The MCP SDK converts them to structured JSON-RPC errors.
- **Rationale:** No custom error type needed. Matches how the CLI
  commands currently surface errors.

**6. No new storage code.**

- `mcp_server.py` is a thin adapter: it instantiates `Storage()` and
  translates MCP tool calls to storage method calls. If we need
  behavior beyond what `Storage` exposes, we add it to `Storage`, not
  to the MCP adapter.
- **Rationale:** Avoids a second, drifting representation of snippet
  operations.

## Risks / Trade-offs

- **Risk:** Agent writes low-quality or duplicate snippets via
  `create_snippet`.
  - **Mitigation:** The tool description instructs agents to check for
    existing similar snippets first (via `search_snippets`). Users can
    always review via `pypet list` and delete. For v1 we accept the
    trade-off — if duplicates become a real problem, we can add a
    dedup heuristic to `Storage.add_snippet`.
- **Risk:** Installing the `mcp` extra pulls in transitive dependencies
  that bloat the CLI.
  - **Mitigation:** It is opt-in. Users who only want the CLI pay
    nothing. CI covers both install modes.
- **Risk:** The MCP SDK's API changes before 1.0 is stable.
  - **Mitigation:** Pin `mcp>=1.0`. If the SDK breaks, only users with
    the optional extra are affected, and the core CLI keeps working.
- **Trade-off:** Not exposing `execute_snippet` means the agent has to
  call `resolve_snippet` and then its shell tool — a two-step dance.
  We accept this friction in exchange for keeping the execution
  decision in the user-visible shell-tool approval flow.
- **Risk:** Confusion between `pypet gen` (generates a snippet via
  OpenRouter) and the MCP server (lets an agent generate snippets
  directly).
  - **Mitigation:** README section explaining which to use when. In the
    mid-term, `pypet gen` can become a convenience wrapper — the MCP
    route is the strategic direction.
