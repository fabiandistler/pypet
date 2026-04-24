## 1. Dependencies and Packaging

- [ ] 1.1 Add optional dependency group `mcp = ["mcp>=1.0"]` to
  `pyproject.toml` under `[project.optional-dependencies]`.
- [ ] 1.2 Confirm `uv pip install -e ".[mcp]"` installs cleanly and
  `uv pip install -e "."` does not pull the MCP SDK.
- [ ] 1.3 Add a short note to `AGENTS.md` about the new optional
  install target.

## 2. Server Implementation

- [ ] 2.1 Create `pypet/mcp_server.py` with a `run()` entry point that
  constructs an MCP `Server`, registers tool handlers, and starts
  `stdio_server()`.
- [ ] 2.2 Implement tool `search_snippets(query, tag?)` backed by
  `Storage.search_snippets`, applying tag filter in-memory if provided.
- [ ] 2.3 Implement tool `list_snippets(tag?)` backed by
  `Storage.list_snippets`.
- [ ] 2.4 Implement tool `get_snippet(snippet_id)` backed by
  `Storage.get_snippet`; raise `ValueError` on unknown ID.
- [ ] 2.5 Implement tool `resolve_snippet(snippet_id, parameters)` that
  reuses the parameter substitution logic from `pypet/parameters.py`
  and returns `{command: <resolved string>}` without executing.
- [ ] 2.6 Implement tool `create_snippet(command, description, tags?,
  parameters?)` backed by `Storage.add_snippet`; return the new ID.
- [ ] 2.7 Define JSON schemas for each tool's input using the MCP SDK's
  schema helpers so clients see typed parameters.
- [ ] 2.8 Ensure snippet responses include `{id, command, description,
  tags, parameters}` in a stable shape shared across tools.

## 3. CLI Integration

- [ ] 3.1 Create `pypet/cli/mcp_commands.py` with a Click command `mcp`.
- [ ] 3.2 Lazy-import `pypet.mcp_server` inside the command; on
  `ImportError` print a friendly message instructing the user to
  `pip install pypet-cli[mcp]` and exit with code 1.
- [ ] 3.3 Wire the new command into `pypet/cli/__init__.py` or
  `pypet/cli/main.py` next to the existing subcommand registrations.
- [ ] 3.4 Verify `pypet mcp --help` renders and `pypet --help` lists
  the new command.

## 4. Testing

- [ ] 4.1 Add `tests/test_mcp_server.py` covering each tool handler
  directly (bypassing the stdio layer) against a temporary
  `Storage` instance with fixture snippets.
- [ ] 4.2 Cover failure paths: unknown snippet ID, missing required
  parameter on `resolve_snippet`, empty search result.
- [ ] 4.3 Add a CLI test that `pypet mcp` prints the install hint when
  the `mcp` package is not importable (monkeypatch the import).
- [ ] 4.4 Run `make all` and ensure ruff, mypy, and pytest all pass in
  both install modes (with and without `[mcp]`).

## 5. Documentation

- [ ] 5.1 Add a "Use pypet with AI agents (MCP)" section to `README.md`
  with:
  - Install command: `pip install pypet-cli[mcp]`.
  - Example Claude Desktop `claude_desktop_config.json` snippet.
  - Example Claude Code / Cursor MCP config snippet.
  - A 2-line summary of the available tools.
- [ ] 5.2 Add an entry to `CHANGELOG.md` under an unreleased section.
- [ ] 5.3 Update `AGENTS.md` with a one-paragraph description of the
  new capability and the tool surface.
