# AGENTS.md - pypet Repository Guide

This file is for agentic coding agents working in this repo. Keep changes small,
respect the existing codebase, and avoid overwriting user work.

## Repository Map

- `pypet/models.py` - snippet and parameter dataclasses plus TOML conversion.
- `pypet/storage.py` - snippet persistence, search, and ID generation.
- `pypet/config.py` - config file handling and environment variable precedence.
- `pypet/alias_manager.py` - shell alias generation and shell-safety checks.
- `pypet/cli/` - Click command modules and CLI wiring.
- `tests/` - pytest suite for models, storage, CLI, sync, aliases, and AI code.
- `scripts/` - helper scripts for hooks and release automation.

## Setup

- Preferred package manager: `uv`.
- Install development dependencies with `uv pip install -e ".[dev]"`.
- Or use `make install` for the same editable install.
- Use `make dev` to install dependencies and git hooks together.

## Build and Quality Commands

- `make format` - auto-fix code with Ruff (`ruff check --fix .`).
- `make lint` - run Ruff lint checks (`ruff check .`).
- `make type-check` - run mypy in best-effort mode.
- `make all` - run format, lint, type-check, clean, and quick tests.
- `make clean` - remove build artifacts and caches.
- `make build` - produce a wheel and sdist with `uv build`.
- `make cli-test` - smoke test the CLI with `--help` and `list`.
- `make hooks` - install the pre-push hook from `scripts/install-hooks.sh`.

## Testing Commands

- `make test` - full pytest run with verbose output.
- `make test-quick` - fast failing test pass for hooks and local iteration.
- Preferred direct test invocation: `uv run python -m pytest ...`.
- A specific test file: `uv run python -m pytest tests/test_models.py -v`.
- A specific test function: `uv run python -m pytest tests/test_models.py::test_snippet_init -v`.
- A single test with short traces: `uv run python -m pytest tests/test_models.py::test_snippet_init -vv --tb=short`.
- Pattern matching a subset of tests: `uv run python -m pytest tests -k "snippet and not slow" -v`.
- If the environment is already active, `pytest ...` is fine too.
- Use `-x` when you want to stop after the first failure.
- Use `-q` for quieter output and `--tb=short` for concise traces.

## CLI Smoke Testing

- `uv run python -m pypet.cli --help` checks Click wiring and imports.
- `uv run python -m pypet.cli list` is a quick end-to-end sanity check.
- For import issues, use `uv run python -c "from pypet import ..."`.

## Code Style

- Target Python 3.10+ and keep compatibility with the versions in `pyproject.toml`.
- Use Ruff for formatting and linting; line length is 88 characters.
- Use double quotes for strings unless a case clearly requires otherwise.
- Prefer 4-space indentation and standard PEP 8 layout.
- Keep imports ordered as stdlib, third-party, then first-party.
- Prefer `pathlib.Path` over `os.path` for filesystem work.
- Avoid wildcard imports and unnecessary local imports.
- Keep functions short and focused; break up long CLI handlers when they grow.
- Use type hints in production code; avoid untyped public APIs.
- Use `Any` only when the data is truly dynamic.
- In tests, type hints are optional unless they clarify tricky fixtures.
- Keep docstrings concise and factual; use them to explain intent, not restate code.

## Naming Conventions

- Classes and dataclasses use `PascalCase`.
- Functions, methods, variables, and modules use `snake_case`.
- Constants use `UPPER_SNAKE_CASE`.
- Private helpers start with `_`.
- Test names should be descriptive and usually start with `test_`.
- Keep file names aligned with their primary responsibility.

## Data Models and Serialization

- Models live in `pypet/models.py` and are implemented as `@dataclass` types.
- Use `to_dict()` and `from_dict()` for TOML round-tripping.
- Keep snippet timestamps in UTC and serialize them as ISO-8601 strings.
- Preserve backwards compatibility when changing snippet or parameter formats.
- Update storage migration helpers when schema changes affect persisted data.

## Persistence and Config

- Default snippet storage lives at `~/.config/pypet/snippets.toml`.
- Default config lives at `~/.config/pypet/config.toml`.
- Default aliases live at `~/.config/pypet/aliases.sh`.
- `Storage` and `Config` create parent directories automatically.
- `Config` resolves `OPENROUTER_API_KEY` and `OPENROUTER_MODEL` from the env
  before falling back to file values.
- Keep file writes atomic when possible, especially for user-facing state.

## CLI Conventions

- Use Click for command definitions and grouping.
- Use Rich for user-facing terminal output in CLI code.
- Keep shared CLI instances in `pypet/cli/main.py` unless there is a strong
  reason to move them.
- Prefer interactive prompts when a command can reasonably recover missing input.
- Avoid adding new `print()` calls in CLI code; use Rich or Click patterns instead.
- Lower-level modules may still write warnings to stderr when that matches the
  existing recovery behavior.

## Error Handling

- Raise specific exceptions instead of bare `except:` blocks.
- Return `None` or `False` when the caller can handle a missing resource cleanly.
- Use stderr for recoverable warnings only when that matches existing behavior.
- Keep file operations atomic when writing user data.
- Clean up temporary files on failure.
- Preserve graceful degradation for corrupted or missing TOML files.
- Do not swallow unexpected exceptions unless there is a deliberate UX reason.

## Security and Shell Safety

- Validate alias names and snippet IDs before writing shell-friendly output.
- Quote shell commands with `shlex.quote` when generating aliases.
- Do not build shell commands from unsanitized user input.
- Keep shell integration compatible with bash and zsh.
- Treat configuration, alias, and sync paths under `~/.config/pypet/` as the
  default locations unless a caller provides a custom path.

## Testing Conventions

- Put all tests in `tests/`.
- Use `tmp_path` for filesystem tests.
- Use small, targeted fixtures instead of heavy setup.
- Allow plain `assert` statements in tests.
- Prefer one assertion group per behavior so failures are easy to read.
- Add regression tests for bugs before or alongside the fix.
- When changing storage or serialization, test both save and load paths.

## Workflow Notes

- Check for existing user changes before editing files and avoid unrelated edits.
- Run the narrowest useful test set first, then widen only if needed.
- Update docs or examples when a behavior change affects CLI usage.
- Keep changes aligned with the repo's current patterns unless there is a clear
  reason to refactor.
- If you need to inspect the CLI contract, start with `README.md` and
  `pyproject.toml`.

## Rule Files

- No `.cursor/rules/`, `.cursorrules`, or `.github/copilot-instructions.md` files
  were present when this guide was written.
- If any of those files are added later, fold their guidance into this document.

## Common Gotchas

- `make type-check` ends with `|| true`, so it is a signal, not a hard gate.
- `make format` uses `ruff check --fix .`, not a separate formatter target.
- The project already has a few low-level stderr warnings; do not replace them
  with noisy CLI output unless you are improving the UX.
- Generated artifacts in `build/`, `dist/`, and cache directories should not be
  edited by hand.
- Keep shell alias generation safe for both simple aliases and parameterized
  functions.

## Quick Reference

- Full checks: `make all`
- Fast checks: `make test-quick`
- Single test: `uv run python -m pytest tests/test_models.py::test_snippet_init -v`
- Format/lint: `make format` / `make lint`
- Type check: `make type-check`
- Build: `make build`
