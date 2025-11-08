# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Testing
```bash
# Run all tests
pytest

# Run tests with verbose output
pytest -v

# Run a specific test file
pytest tests/test_models.py

# Run a specific test
pytest tests/test_models.py::test_snippet_initialization

# Quick test for CI/hooks (stop on first failure)
make test-quick
```

### Code Quality
```bash
# Auto-format and fix code with ruff (required before commit)
make format
# Or: uv run ruff check --fix .

# Check linting with ruff
make lint
# Or: uv run ruff check .

# Run all checks (format + lint + test)
make all
```

### Project Management
```bash
# Install dependencies using uv (preferred)
uv pip install -e ".[dev]"

# Set up complete development environment with hooks
make dev

# Run the CLI locally
pypet --help
```

## Architecture Overview

This is a Python CLI tool (`pypet`) for managing command-line snippets, inspired by the Go-based `pet` tool. The architecture consists of three main components:

### Core Components

1. **Models (`pypet/models.py`)**: Defines `Snippet` and `Parameter` dataclasses
   - `Snippet`: Represents a command with metadata (description, tags, parameters, alias, timestamps)
   - `Parameter`: Represents customizable parameters within commands (with defaults and descriptions)
   - Both models support TOML serialization/deserialization

2. **Storage (`pypet/storage.py`)**: Handles TOML-based persistence
   - Default storage location: `~/.config/pypet/snippets.toml`
   - Operations: add, get, list, search, update, delete snippets
   - Support for alias management
   - Thread-safe file operations with error handling

3. **CLI (`pypet/cli/*.py`)**: Click-based command interface with Rich formatting (organized into modules)
   - Commands: `new`, `list`, `search`, `edit`, `delete`, `exec`, `copy`, `sync`, `save-clipboard`, `save-last`, `alias`
   - Interactive execution with parameter prompting
   - **Clipboard integration** using pyperclip library
   - **Shell history integration** for saving recent commands
   - **Shell alias management** for creating persistent bash/zsh aliases
   - **Git synchronization** with backup/restore functionality
   - Rich terminal tables and colored output

4. **Sync (`pypet/sync.py`)**: Git-based synchronization system
   - Git repository detection and initialization
   - Commit, pull, push operations with automatic backups
   - Conflict-safe operations with backup/restore
   - Cross-platform Git integration using GitPython

5. **Alias Manager (`pypet/alias_manager.py`)**: Shell alias management
   - Generate alias definitions for snippets
   - Manage `~/.config/pypet/aliases.sh` file
   - Support for both simple aliases and parameterized functions
   - Shell profile integration instructions

### Key Features

- **Parameterized Snippets**: Commands can contain placeholders like `{port}` or `{env=development}`
- **Interactive Execution**: `pypet exec` without ID shows snippet selection table
- **Clipboard Integration**: `pypet copy` command, `--copy` option, and `save-clipboard` command for easy snippet sharing
- **Shell History Integration**: Save recent commands from shell history with `save-last` command
- **Shell Aliases**: Create persistent bash/zsh aliases from snippets, with automatic function generation for parameterized commands
- **Git Synchronization**: Full Git workflow with automatic backups and conflict resolution
- **Automatic Backup Management**: Smart cleanup keeps only the 5 most recent backups
- **Rich Terminal Output**: All commands use Rich library for formatted tables and colors
- **TOML Storage**: Human-readable configuration format at `~/.config/pypet/snippets.toml`
- **Comprehensive Search**: Search across commands, descriptions, tags, and parameter names

### Testing Structure

Tests are organized by component (130 total tests):
- `tests/test_models.py`: Model validation and serialization
- `tests/test_storage.py`: File operations and persistence
- `tests/test_cli.py`: Command-line interface using Click's testing utilities
- `tests/test_sync.py`: Git synchronization functionality (15 tests)
- `tests/test_sync_cli.py`: Sync command-line interface tests (15 tests)
- `tests/test_alias.py`: Alias manager and storage integration tests (15 tests)
- `tests/test_alias_cli.py`: Alias CLI command tests (15 tests)

### Parameter System

Commands support two parameter formats:
- `{name}` - required parameter
- `{name=default}` - parameter with default value

Parameters are defined with optional descriptions and are prompted for during interactive execution.

## Code Conventions

- Uses dataclasses with type hints throughout
- Error handling with specific exception types
- Rich library for all terminal output formatting
- Click framework for CLI with proper option/argument handling
- UTC timestamps for all datetime operations
- Ruff for both formatting and linting (configured in pyproject.toml)
- Type annotations enforced via ruff's ANN rules (except self/cls and Any)

## Recent Updates & Important Notes

### v0.5.0 (2025-11-07) - Current Version
- **Shell Alias Functionality** (Issue #7): Create persistent bash/zsh aliases from snippets
  - `pypet alias add/list/remove/update/setup/show` commands
  - Simple aliases for non-parameterized commands, functions for parameterized ones
  - Aliases stored in `~/.config/pypet/aliases.sh`
  - Validation and duplicate detection with override option
- **Interactive Delete Mode** (Issue #32): `pypet delete` without ID for interactive selection
- **Enhanced Snippet model**: Added `alias` field with TOML serialization
- **New AliasManager module**: `pypet/alias_manager.py` handles alias file generation
- **130 total tests** (30 new tests for alias functionality)

### v0.2.1 (2025-11-05)
- **Consolidated to Ruff-only**: Removed Black, using Ruff for both formatting and linting
- **Updated Makefile and hooks**: Simplified to use Ruff exclusively

### v0.2.0 (2025-06-26)
- **New `pypet save-clipboard` command** (Issue #8): Save clipboard content as snippets
- **New `pypet save-last` command** (Issue #8): Save command(s) from shell history
- **Enhanced `pypet edit --file` option** (Issue #13): Open TOML config directly
- **Automatic backup cleanup** (Issue #12): Keeps 5 most recent backups
- **Pre-push git hooks**: Run linting and tests before push
- **Development Makefile**: Streamlined workflow with `make dev`, `make test`, etc.

### v0.1.1 (2025-06-25)
- **Fixed Issue #10**: Git sync remote feature reliability
- **Added `pypet sync remote <url>` command**
- **Improved first-time sync**: Handles empty repositories
- **Auto-upstream setup**: Sets branch tracking on first push

### Development Workflow Notes
- **Git Hooks**: Pre-push hooks automatically run linting and tests
- **Makefile**: Use `make` commands for development tasks (preferred over direct uv commands)
- **Linting**: Ruff is enforced for both formatting and linting via pre-push hooks
- **Release process**: GitHub Actions handles PyPI publishing automatically on tag push
- **Git sync feature**: Works with any Git service, handles edge cases robustly
- **Testing**: All tests must pass before any release (130 tests total)
- **CLI Module Organization**: Commands organized into submodules (snippet_commands, execution_commands, save_commands, sync_commands, alias_commands)

### Development Setup
```bash
# Install development environment with hooks
make dev

# Or manually:
make install        # Install package in dev mode
make hooks         # Install pre-push git hooks
```

### Daily Development Commands
```bash
make format        # Auto-format and fix code with ruff
make lint          # Check linting with ruff
make test          # Run tests
make test-quick    # Run tests with early exit (for CI/hooks)
make all           # Run format + lint + test
make clean         # Remove build artifacts and cache files
```

### Git Workflow Guidelines
- **Pre-push hooks**: Automatically run linting and tests before push (installed via `make dev` or `make hooks`)
- **Bypass hooks**: Use `git push --no-verify` only in emergencies
- **Always work with PRs and don't push to main without asking**
- **Skip tests**: Set `SKIP_TESTS=1` to skip tests in hooks (for quick iterations)
- **Hook location**: `.git/hooks/pre-push` (installed from `scripts/install-hooks.sh`)

## Important Development Patterns

### CLI Module Structure
The CLI is organized into submodules to avoid circular imports:
1. `cli/main.py` - Defines the main Click group and shared instances (console, storage, sync_manager)
2. Command modules import `main` module and register commands via decorators
3. Order matters: `cli/__init__.py` imports `main` first, then command modules
4. Shared instances exported from `cli/__init__.py` for tests

### Adding New Commands
When adding a new command:
1. Create command in appropriate module (e.g., `cli/snippet_commands.py`)
2. Import `main` from `.main` to access the Click group
3. Register command with `@main.command()` decorator
4. Import the module in `cli/__init__.py` to trigger registration
5. Add corresponding tests in `tests/test_*_cli.py`

### Storage and Snippet Management
- Default location: `~/.config/pypet/snippets.toml`
- Snippets have unique IDs (first 8 chars shown to users)
- All operations are atomic with proper file locking
- Backups created before destructive sync operations
- Storage methods handle both single snippets and batch operations
