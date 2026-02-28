# AGENTS.md - Development Guidelines for pypet

This file contains development guidelines and commands for agentic coding agents working on the pypet project.

## Development Commands

### Package Management
```bash
# Install dependencies using uv (preferred)
uv pip install -e ".[dev]"

# Install package in development mode
make install

# Set up complete development environment with hooks
make dev
```

### Testing
```bash
# Run all tests
make test

# Run tests with verbose output
make test

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

# Type checking with mypy
make type-check
# Or: uv run python -m mypy pypet --ignore-missing-imports
```

### Git Workflow
```bash
# Install pre-push git hooks
make hooks
# Or: ./scripts/install-hooks.sh

# Bypass hooks (use sparingly)
git push --no-verify

# Skip tests in hooks (for quick iterations)
SKIP_TESTS=1 git push
```

## Code Style Guidelines

### Python Standards
- **Python Version**: 3.10+
- **Package Manager**: Use `uv` for all dependency management
- **Formatter**: Ruff handles both formatting and linting
- **Type Hints**: Enforced via ruff's ANN rules (except self/cls and Any)
- **Line Length**: 88 characters
- **Quotes**: Double quotes for strings
- **Indentation**: Spaces (4 spaces per level)

### Import Organization (isort)
```python
# Standard library imports first
import sys
from datetime import datetime, timezone
from pathlib import Path

# Third-party imports next
import click
import toml
from rich.console import Console

# First-party imports last
from pypet.models import Snippet, Parameter
from pypet.storage import Storage
```

### Code Structure
- **Dataclasses**: Use `@dataclass` for models with type hints
- **Models**: Located in `pypet/models.py` - use `to_dict()` and `from_dict()` for TOML serialization
- **Storage**: Use `Storage` class for all file operations - handles TOML persistence
- **CLI**: Organized into submodules under `pypet/cli/` to avoid circular imports
- **Global Instances**: Shared instances (console, storage, sync_manager) in `cli/main.py`

### Error Handling
- Use specific exception types
- Graceful degradation for file operations
- Log errors to stderr with context
- Return boolean success indicators for operations

### Naming Conventions
- **Classes**: PascalCase (e.g., `Snippet`, `Storage`, `AliasManager`)
- **Functions/Methods**: snake_case (e.g., `add_snippet`, `get_all_parameters`)
- **Variables**: snake_case (e.g., `snippet_id`, `config_path`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `DEFAULT_CONFIG_PATH`)
- **Private Methods**: Prefix with underscore (e.g., `_load_snippets`)

### Model Guidelines
- **Snippet Model**: Core data model with command, metadata, and parameters
- **Parameter Model**: Represents command parameters with name, default, and description
- **TOML Serialization**: Use `to_dict()` and `from_dict()` methods for persistence
- **Timestamp Handling**: Use UTC timezone for all datetime operations
- **Parameter Detection**: Automatic discovery of parameters from command placeholders

### CLI Development
- **Click Framework**: Use Click for all command-line interfaces
- **Rich Library**: Use Rich for all terminal output formatting
- **Command Organization**: Group related commands in separate modules
- **Interactive Mode**: Provide interactive selection when no ID is provided
- **Parameter Handling**: Use `_prompt_for_parameters()` for user input

### Testing Requirements
- **Test Location**: All tests in `tests/` directory
- **Test Naming**: Use descriptive test names with docstrings
- **Fixtures**: Use `tmp_path` fixture for file-based tests
- **Coverage**: Aim for comprehensive test coverage
- **Type Checking**: Include type annotation tests where relevant

### Storage Guidelines
- **Default Location**: `~/.config/pypet/snippets.toml`
- **File Operations**: Use atomic operations with proper error handling
- **Backup Management**: Automatic backup creation before destructive operations
- **TOML Format**: Human-readable with proper section organization
- **Parameter Storage**: Only include parameters section when parameters exist

### Alias Management
- **Alias Validation**: Use `AliasManager.validate_alias_name()` for shell safety
- **Function Generation**: Create shell functions for parameterized snippets
- **File Location**: `~/.config/pypet/aliases.sh`
- **Setup Instructions**: Provide clear shell profile integration guidance

### Git Synchronization
- **GitPython**: Use GitPython for all Git operations
- **Backup Strategy**: Create backups before pull operations
- **Conflict Resolution**: Implement backup/restore for safe operations
- **Auto-Sync**: Optional auto-sync with minimal user disruption

### Development Workflow
1. **Before Changes**: Run `make dev` to set up environment with hooks
2. **During Development**: Use `make format` and `make lint` frequently
3. **Before Commit**: Run `make all` to ensure all checks pass
4. **After Changes**: Verify tests pass with `make test`
5. **Git Hooks**: Pre-push hooks automatically run quality checks

### Important Notes
- **No Print Statements**: Use Rich console for all output instead of print()
- **UTC Timestamps**: All datetime operations use UTC timezone
- **Thread Safety**: Consider thread safety for file operations
- **Cross-Platform**: Test on different operating systems
- **Shell Integration**: Ensure shell alias functionality works across bash/zsh
- **Clipboard Support**: Test pyperclip functionality on all platforms

### Performance Considerations
- **Lazy Loading**: Load snippets only when needed
- **Search Optimization**: Use efficient search algorithms for large snippet collections
- **Memory Management**: Clean up temporary files and caches
- **Async Operations**: Consider async operations for long-running tasks

### Security Best Practices
- **Input Validation**: Validate all user inputs and parameters
- **File Permissions**: Set appropriate file permissions for configuration files
- **Command Injection**: Sanitize command execution with proper quoting
- **Secrets Management**: Never commit secrets or sensitive data
- **Shell Safety**: Validate alias names and snippet IDs for shell safety