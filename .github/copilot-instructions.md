<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

# Project-Specific Instructions

This is a Python-based command-line snippet manager inspired by [pet](https://github.com/knqyf263/pet). The project uses:

- TOML for snippet storage (`~/.config/pypet/snippets.toml`)
- Click for CLI interface
- Rich for terminal UI
- UV for package management
- Pytest for testing

The project aims to be a simple yet powerful snippet manager with a focus on:
- Clean, idiomatic Python code
- Modern Python practices (type hints, dataclasses)
- Comprehensive testing
- User-friendly CLI interface

When generating code for this project:
1. Follow Python best practices and PEP 8 style guidelines
2. Use type hints for all function parameters and return values
3. Include docstrings for all modules, classes, and functions
4. Implement proper error handling with clear user feedback
5. Keep the CLI interface simple and intuitive
6. Use Rich for attractive terminal output
7. Add appropriate tests for new functionality
8. Store snippets in TOML format with proper validation
9. Support interactive command execution with editing
10. Maintain backwards compatibility with existing snippet storage

Key Components:
- `models.py`: Contains the Snippet dataclass with proper data validation
- `storage.py`: Handles TOML-based snippet storage with error handling
- `cli.py`: Implements the CLI interface using Click and Rich
- `tests/`: Comprehensive test suite covering models, storage, and CLI
