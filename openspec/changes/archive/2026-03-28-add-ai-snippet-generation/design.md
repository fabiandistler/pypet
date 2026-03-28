## Context

Pypet currently requires users to write out complex shell commands manually, including formatting parameters correctly. To reduce friction, we are introducing `pypet gen`, a command that uses OpenRouter to generate snippets from natural language. We want to implement this without introducing heavy dependencies like LangChain or OpenAI SDKs to keep the CLI fast and lightweight.

## Goals / Non-Goals

**Goals:**

- Provide a `pypet gen "prompt"` command.
- Generate `command`, `description`, `tags`, and `parameters` from natural language.
- Provide an interactive confirmation prompt to save the snippet and assign an alias.
- Ask for and save the user's OpenRouter API key only when it's missing from both environment and config.
- Zero new external dependencies (use standard library `urllib`).

**Non-Goals:**

- We are not adding conversational memory. This is a one-shot generation task.
- We are not supporting other AI providers directly right now, though the OpenRouter API is OpenAI-compatible so it's trivial to switch the base URL later if needed.
- We are not auto-executing the generated command for safety reasons.

## Decisions

**1. Zero-Dependency API Client:**

- We will build a lightweight HTTP client in `pypet/ai.py` using `urllib.request`.
- **Rationale:** Pypet starts up instantly right now. Pulling in `langchain` or `openai` would add hundreds of megabytes of dependencies and significant startup latency.

**2. Prompt Engineering & JSON Schema:**

- We will use OpenRouter's API and instruct the model via a strict system prompt to return pure JSON that matches the existing `Snippet` model structure.
- **Rationale:** Structured JSON is easy to parse with `json.loads()` and maps perfectly to `storage.add_snippet()`.

**3. Configuration Management:**

- We will extend `pypet/config.py` to support `openrouter_api_key` and `ai_model`.
- We will support `OPENROUTER_API_KEY` and `OPENROUTER_MODEL` environment variable overrides, with environment values taking precedence over config values.
- **Rationale:** Keeps configuration centralized and allows users to switch models if they want to.

## Risks / Trade-offs

- **Risk:** LLM returns malformed JSON or hallucinates keys.
  - **Mitigation:** We will use a robust system prompt with JSON mode (if supported by the model) or strong instructions, and wrap the JSON parsing in a `try/except` block that gracefully displays an error and asks the user to try again.
- **Risk:** The generated command is destructive (e.g., `rm -rf /`).
  - **Mitigation:** We never execute the command. We only save it as a snippet. The user must review it before saving it, and review it again before running it via the standard `pypet` execution flow.
