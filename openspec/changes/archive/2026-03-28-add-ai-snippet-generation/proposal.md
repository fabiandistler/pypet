## Why

Users often struggle to write complex bash commands from scratch, including the correct syntax for pypet's parameter placeholders. Adding an AI snippet generator allows users to describe what they want to achieve in natural language and instantly receive a properly formatted, ready-to-save pypet snippet. This drastically lowers the barrier to entry and increases the utility of the tool.

## What Changes

- Add a new `pypet gen` command that accepts a natural language prompt.
- Add configuration options for `openrouter_api_key` and `ai_model` in `~/.config/pypet/config.toml`, with `OPENROUTER_API_KEY` / `OPENROUTER_MODEL` environment overrides.
- Add a lightweight API client module using Python's standard `urllib.request` to communicate with the OpenRouter API (zero new dependencies).
- Parse the AI's JSON response and provide an interactive prompt to save the generated snippet and assign an alias.

## Capabilities

### New Capabilities

- `ai-snippet-generation`: Allows users to generate shell snippets from natural language prompts using an external AI provider (OpenRouter) with zero additional dependencies.

### Modified Capabilities

## Impact

- Extends the `pypet/config.py` module to handle API keys and model selection from config and environment variables.
- Introduces `pypet/ai.py` for the OpenRouter API client.
- Introduces a new command `gen` in the CLI via `pypet/cli/ai_commands.py` (or similar).
- No impact on existing snippets or core storage mechanisms.
