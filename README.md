# pypet - Command Line Snippet Manager

`pypet` is a Python-based command-line snippet manager inspired by [pet](https://github.com/knqyf263/pet). It helps you organize and reuse command-line snippets efficiently, with a focus on simplicity and usability.

## Features

- Store command snippets with descriptions and tags
- TOML-based storage (`~/.config/pypet/snippets.toml`)
- List and search your snippets with rich terminal output
- Interactive command execution with pre-execution editing
- Tag-based organization
- Modern Python implementation with type hints
- Comprehensive test coverage

## Installation

```bash
# Using uv (recommended)
uv pip install pypet

# Or using pip
pip install pypet
```

## Usage

### Basic Commands

```bash
# List all snippets
pypet list

# Add a new snippet
pypet new "git commit -m" -d "Create a git commit" -t "git,version-control"

# Search snippets
pypet search "git"

# Execute a snippet (interactive if no ID provided)
pypet exec [snippet-id]

# Execute with editing
pypet exec [snippet-id] -e

# Edit a snippet
pypet edit <snippet-id>

# Delete a snippet
pypet delete <snippet-id>
```

### Interactive Mode

When running `pypet exec` without a snippet ID, it enters interactive mode:

1. Shows a table of all available snippets
2. Lets you select a snippet by number
3. Optionally allows editing the command before execution
4. Asks for confirmation before running the command

## Development

This project uses `uv` for dependency management and `pytest` for testing.

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/pypet.git
   cd pypet
   ```

2. Set up the development environment:

   ```bash
   uv venv
   source .venv/bin/activate
   uv pip install -e ".[dev]"
   ```

3. Run tests:

   ```bash
   pytest
   ```

4. Try the CLI:

   ```bash
   pypet --help
   ```

## Storage Format

Snippets are stored in TOML format at `~/.config/pypet/snippets.toml`:

```toml
[snippets.unique-id]
command = "git status"
description = "Check git status"
tags = ["git", "status"]
created_at = "2025-06-17T10:00:00+00:00"
updated_at = "2025-06-17T10:00:00+00:00"
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see the [LICENSE](LICENSE) file for details
