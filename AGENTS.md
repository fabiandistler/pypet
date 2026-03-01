# AGENTS.md - Development Guidelines for pypet

This file contains development guidelines and commands for agentic coding agents working on the pypet project.

## Development Commands

### Package Management
```bash
uv pip install -e ".[dev]"    # Install dependencies using uv
make install                  # Install package in development mode
make dev                      # Set up complete development environment with hooks
```

### Testing
```bash
make test                     # Run all tests with verbose output
make test-quick               # Quick test for CI/hooks (stop on first failure)
pytest tests/test_models.py                       # Run specific test file
pytest tests/test_models.py::test_snippet_init    # Run specific test
```

### Code Quality
```bash
make format                   # Auto-format and fix code with ruff
make lint                     # Check linting with ruff
make type-check               # Run type checking with mypy
make all                      # Run all checks (format + lint + test)
```

### Git Workflow
```bash
make hooks                    # Install pre-push git hooks
git push --no-verify          # Bypass hooks (use sparingly)
SKIP_TESTS=1 git push        # Skip tests in hooks for quick iterations
```

## Code Style Guidelines

### Python Standards
- **Python Version**: 3.10+
- **Package Manager**: Use `uv` for all dependency management
- **Formatter/Linter**: Ruff handles both formatting and linting
- **Type Hints**: Enforced via ruff's ANN rules (except self/cls and Any)
- **Line Length**: 88 characters
- **Quotes**: Double quotes for strings
- **Indentation**: 4 spaces per level

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

### Naming Conventions
- **Classes**: PascalCase (e.g., `Snippet`, `Storage`, `AliasManager`)
- **Functions/Methods**: snake_case (e.g., `add_snippet`, `get_all_parameters`)
- **Variables**: snake_case (e.g., `snippet_id`, `config_path`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `DEFAULT_CONFIG_PATH`)
- **Private Methods**: Prefix with underscore (e.g., `_load_snippets`)

### Error Handling
- Use specific exception types
- Graceful degradation for file operations
- Log errors to stderr with context
- Return boolean success indicators for operations

## Project Structure

### Code Organization
- **Models**: `pypet/models.py` - use `to_dict()` and `from_dict()` for TOML serialization
- **Storage**: `pypet/storage.py` - handles TOML persistence
- **CLI**: Organized into submodules under `pypet/cli/` to avoid circular imports
- **Global Instances**: Shared instances (console, storage, sync_manager) in `cli/main.py`
- **Dataclasses**: Use `@dataclass` decorator for models with type hints

### CLI Development
- **Framework**: Use Click for all command-line interfaces
- **Output**: Use Rich for all terminal output formatting (no print statements)
- **Command Organization**: Group related commands in separate modules
- **Interactive Mode**: Provide interactive selection when no ID is provided

## Testing Requirements
- **Location**: All tests in `tests/` directory
- **Naming**: Use descriptive test names with docstrings
- **Fixtures**: Use `tmp_path` fixture for file-based tests
- **Run Specific Tests**:
  ```bash
  pytest tests/test_models.py                   # Single file
  pytest tests/test_models.py::test_name         # Single test
  pytest tests/ -k "test_name"                  # Pattern match
  ```

## Storage Guidelines
- **Default Location**: `~/.config/pypet/snippets.toml`
- **File Operations**: Use atomic operations with proper error handling
- **Backup Management**: Automatic backup creation before destructive operations
- **TOML Format**: Human-readable with proper section organization

## Alias Management
- **Validation**: Use `AliasManager.validate_alias_name()` for shell safety
- **Function Generation**: Create shell functions for parameterized snippets
- **File Location**: `~/.config/pypet/aliases.sh`

## Important Notes
- **No Print Statements**: Use Rich console for all output instead of print()
- **UTC Timestamps**: All datetime operations use UTC timezone
- **Thread Safety**: Consider thread safety for file operations
- **Shell Integration**: Ensure shell alias functionality works across bash/zsh

## Development Workflow
1. Run `make dev` to set up environment with hooks
2. Use `make format` and `make lint` frequently during development
3. Run `make all` before commit to ensure all checks pass
4. Pre-push hooks automatically run quality checks

## Security Best Practices
- Validate all user inputs and parameters
- Set appropriate file permissions for configuration files
- Sanitize command execution with proper quoting
- Never commit secrets or sensitive data
- Validate alias names and snippet IDs for shell safety
