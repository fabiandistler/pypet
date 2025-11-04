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
```

### Code Quality
```bash
# Format code with black (required before commit)
uv run python -m black pypet tests

# Check linting with ruff
uv run python -m ruff check pypet tests

# Both together
uv run python -m black pypet tests && uv run python -m ruff check pypet tests
```

### Project Management
```bash
# Install dependencies using uv (preferred)
uv pip install -e .

# Install with pip
pip install -e .

# Run the CLI locally
pypet --help
```

## Architecture Overview

This is a Python CLI tool (`pypet`) for managing command-line snippets, inspired by the Go-based `pet` tool. The architecture consists of three main components:

### Core Components

1. **Models (`pypet/models.py`)**: Defines `Snippet` and `Parameter` dataclasses
   - `Snippet`: Represents a command with metadata (description, tags, parameters, timestamps)
   - `Parameter`: Represents customizable parameters within commands (with defaults and descriptions)
   - Both models support TOML serialization/deserialization

2. **Storage (`pypet/storage.py`)**: Handles TOML-based persistence
   - Default storage location: `~/.config/pypet/snippets.toml`
   - Operations: add, get, list, search, update, delete snippets
   - Thread-safe file operations with error handling

3. **CLI (`pypet/cli.py`)**: Click-based command interface with Rich formatting
   - Commands: `new`, `list`, `search`, `edit`, `delete`, `exec`, `copy`, `sync`, `save-clipboard`, `save-last`
   - Interactive execution with parameter prompting
   - **Clipboard integration** using pyperclip library
   - **Shell history integration** for saving recent commands
   - **Git synchronization** with backup/restore functionality
   - Rich terminal tables and colored output

4. **Sync (`pypet/sync.py`)**: Git-based synchronization system
   - Git repository detection and initialization
   - Commit, pull, push operations with automatic backups
   - Conflict-safe operations with backup/restore
   - Cross-platform Git integration using GitPython

### Key Features

- **Parameterized Snippets**: Commands can contain placeholders like `{port}` or `{env=development}`
- **Interactive Execution**: `pypet exec` without ID shows snippet selection table
- **Clipboard Integration**: `pypet copy` command, `--copy` option, and `save-clipboard` command for easy snippet sharing
- **Shell History Integration**: Save recent commands from shell history with `save-last` command
- **Git Synchronization**: Full Git workflow with automatic backups and conflict resolution
- **Automatic Backup Management**: Smart cleanup keeps only the 5 most recent backups
- **Rich Terminal Output**: All commands use Rich library for formatted tables and colors
- **TOML Storage**: Human-readable configuration format at `~/.config/pypet/snippets.toml`
- **Comprehensive Search**: Search across commands, descriptions, tags, and parameter names

### Testing Structure

Tests are organized by component:
- `tests/test_models.py`: Model validation and serialization
- `tests/test_storage.py`: File operations and persistence
- `tests/test_cli.py`: Command-line interface using Click's testing utilities
- `tests/test_sync.py`: Git synchronization functionality
- `tests/test_sync_cli.py`: Sync command-line interface tests

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

## Recent Updates & Important Notes

### v0.2.0 (2025-06-26) - Current Version
- **New `pypet save-clipboard` command** (Issue #8): Save clipboard content as snippets with automatic parameter detection
- **New `pypet save-last` command** (Issue #8): Save command(s) from shell history (bash, zsh, etc.)
- **Enhanced `pypet edit --file` option** (Issue #13): Open TOML configuration file directly in editor
- **Automatic backup cleanup** (Issue #12): Smart management keeps only 5 most recent backups
- **Pre-push git hooks**: Automatically run linting and tests before push
- **Development Makefile**: Streamlined workflow with `make dev`, `make test`, `make all`, etc.
- Updated to 80 total tests (expanded coverage for new features)

### v0.1.1 (2025-06-25)
- **Fixed Issue #10**: Git sync remote feature now works reliably
- **Added `pypet sync remote <url>` command** for easy remote management
- **Improved first-time sync**: Handles empty repositories automatically
- **Auto-upstream setup**: Sets branch tracking on first push
- **Enhanced error handling**: Clear guidance for common sync issues
- 74 total tests

### Development Workflow Notes
- **Git Hooks**: Pre-push hooks automatically run linting and tests
- **Makefile**: Use `make` commands for development tasks
- **Linting**: `black` and `ruff` are enforced via pre-push hooks
- **Release process**: GitHub Actions handles PyPI publishing automatically on tag push
- **Git sync feature**: Works with any Git service, handles edge cases robustly
- **Testing**: All tests must pass before any release

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
make format        # Auto-format code
make lint          # Check linting
make test          # Run tests
make all           # Run format + lint + test
```

### Git Workflow Guidelines
- **Pre-push hooks**: Automatically run linting and tests before push
- **Bypass hooks**: Use `git push --no-verify` only in emergencies
- **Always work with PRs and don't push to main without asking**
- **Skip tests**: Set `SKIP_TESTS=1` to skip tests in hooks
