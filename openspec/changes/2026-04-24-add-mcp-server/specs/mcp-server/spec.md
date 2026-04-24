## ADDED Requirements

### Requirement: Start MCP Server

The system SHALL provide a `pypet mcp` command that starts a Model
Context Protocol server on stdio, exposing the user's snippet library
to MCP-compatible AI agents.

#### Scenario: MCP extra installed

- **WHEN** the user runs `pypet mcp` with the `mcp` optional extra
  installed
- **THEN** the system starts an MCP server on stdio and blocks,
  listening for JSON-RPC messages until the client disconnects

#### Scenario: MCP extra not installed

- **WHEN** the user runs `pypet mcp` without the `mcp` optional extra
  installed
- **THEN** the system prints a message instructing the user to run
  `pip install pypet-cli[mcp]` and exits with a non-zero status code

### Requirement: Expose Snippet Read Tools

The server SHALL expose tools that let agents discover and read the
user's snippets without modifying them.

#### Scenario: Searching snippets

- **WHEN** an agent calls the `search_snippets` tool with a query
  string and an optional tag filter
- **THEN** the server returns the list of matching snippets, each with
  `id`, `command`, `description`, `tags`, and `parameters`

#### Scenario: Listing snippets by tag

- **WHEN** an agent calls the `list_snippets` tool with a `tag`
  argument
- **THEN** the server returns only snippets whose tag list contains
  that tag

#### Scenario: Fetching a single snippet

- **WHEN** an agent calls the `get_snippet` tool with a known snippet
  ID
- **THEN** the server returns the full snippet record including its
  parameter schema

#### Scenario: Fetching an unknown snippet

- **WHEN** an agent calls the `get_snippet` tool with an unknown ID
- **THEN** the server raises an error that the MCP SDK surfaces as a
  structured JSON-RPC error to the client

### Requirement: Resolve Parameters Without Execution

The server SHALL resolve parameter placeholders into a final command
string without executing the command.

#### Scenario: Resolving a parameterized snippet

- **WHEN** an agent calls `resolve_snippet` with a snippet ID and a
  mapping of parameter names to values
- **THEN** the server returns a `{command}` object containing the
  substituted command string and does not execute it

#### Scenario: Missing required parameter

- **WHEN** an agent calls `resolve_snippet` without providing a value
  for a parameter that has no default
- **THEN** the server raises an error indicating which parameter is
  missing

### Requirement: Create Snippets From the Agent

The server SHALL allow agents to persist new snippets on behalf of the
user.

#### Scenario: Creating a snippet

- **WHEN** an agent calls `create_snippet` with a command,
  description, optional tags, and optional parameter schema
- **THEN** the server persists the snippet using the same storage
  layer as the CLI and returns the new snippet's ID

### Requirement: No Remote Execution

The server SHALL NOT expose a tool that executes snippets on the host.

#### Scenario: Attempting execution via MCP

- **WHEN** an agent inspects the tool catalog
- **THEN** no tool named `execute_snippet` (or equivalent) is
  advertised, and the agent must invoke its own shell tool on the
  output of `resolve_snippet` to run a command
