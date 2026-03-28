## 1. Config Updates

- [x] 1.1 Update `pypet/config.py` to add `openrouter_api_key` and `ai_model` properties
- [x] 1.2 Add defaults for `ai_model` (e.g. `google/gemini-2.5-flash`)
- [x] 1.3 Add config helpers to resolve API key and model with ENV precedence (`OPENROUTER_API_KEY`, `OPENROUTER_MODEL`) before config values

## 2. API Client Implementation

- [x] 2.1 Create `pypet/ai.py`
- [x] 2.2 Implement a lightweight `urllib.request` client for `https://openrouter.ai/api/v1/chat/completions`
- [x] 2.3 Write the system prompt instructing the model to output structured JSON matching the `Snippet` format
- [x] 2.4 Add robust error handling (timeout, malformed JSON, API errors)
- [x] 2.5 Ensure the API call returns a dictionary matching the expected `Snippet` kwargs (`command`, `description`, `tags`, `parameters`)

## 3. CLI Command Implementation

- [x] 3.1 Create `pypet/cli/ai_commands.py`
- [x] 3.2 Implement `@main.command(name="gen")` taking a `prompt` argument
- [x] 3.3 Add logic to check for API key, and prompt/save it if missing
- [x] 3.4 Call `pypet.ai` module with a rich spinner (`console.status`)
- [x] 3.5 Display generated `command`, `description`, `tags`, and `parameters` in a Rich Table
- [x] 3.6 Implement the interactive `[Y/n]` save flow (prompting for an optional alias)
- [x] 3.7 Integrate the new command into `pypet/cli/main.py` or `pypet/cli/__init__.py`

## 4. Testing

- [ ] 4.1 Write unit tests for config changes in `tests/test_config.py`, including ENV-over-config resolution for API key/model
- [x] 4.2 Write mocked tests for `pypet/ai.py` so it doesn't hit the real API, including a case that validates `parameters` with defaults/descriptions
- [x] 4.3 Write CLI tests for `pypet gen` covering missing-vs-existing API key behavior and save flow
- [ ] 4.4 Run `make all` to ensure format, lint, and tests pass
