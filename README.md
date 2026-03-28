[![PyPI Downloads](https://static.pepy.tech/personalized-badge/pypet-cli?period=total&units=INTERNATIONAL_SYSTEM&left_color=BLACK&right_color=GREEN&left_text=downloads)](https://pepy.tech/projects/pypet-cli)

# pypet - Command Line Snippet Manager

`pypet` is a Python-based command-line snippet manager inspired by [pet](https://github.com/knqyf263/pet). It helps you organize and reuse command-line snippets efficiently, with a focus on simplicity and usability.

## Features

- Store command snippets with descriptions and tags
- TOML-based storage (`~/.config/pypet/snippets.toml`)
- List and search your snippets with rich terminal output
- Interactive command execution with pre-execution editing
- **Copy snippets to clipboard** for easy pasting into other applications
- **Shell aliases** - create persistent bash/zsh aliases from snippets
- **Git synchronization** for backup and sharing across devices
- Parameterized snippets with default values
- AI-assisted snippet generation
- Automatic backup and restore functionality
- Tag-based organization
- Modern Python implementation with type hints
- Comprehensive test coverage

## Installation

### PyPI (Recommended)

```bash
pip install pypet-cli
```

### Development Installation

```bash
# Clone repository
git clone https://github.com/fabiandistler/pypet.git
cd pypet

# Install with uv (recommended)
uv pip install -e .

# Or with pip
pip install -e .
```

### Requirements

- Python 3.10 or higher
- Git (for synchronization features)

## Usage

### Basic Commands

```bash
# List all snippets
pypet list

# Add a new snippet
pypet new "git commit -m" -d "Create a git commit" -t "git,version-control"

# Save clipboard content as a snippet
pypet save-clipboard -d "Description" -t "tag1,tag2"

# Save last command(s) from shell history
pypet save-last                    # Save last command
pypet save-last -n 3               # Save last 3 commands

# Search snippets
pypet search "git"

# Execute a snippet (interactive if no ID provided)
pypet exec [snippet-id]

# Execute with editing
pypet exec [snippet-id] -e

# Copy a snippet to clipboard
pypet copy [snippet-id]

# Execute with copy to clipboard option
pypet exec [snippet-id] --copy

# Generate a snippet from a natural-language prompt
pypet gen "kill process listening on port 3000"

# Edit a snippet
pypet edit <snippet-id>

# Edit the snippets configuration file directly
pypet edit --file

# Delete a snippet
pypet delete <snippet-id>

# Alias management
pypet alias add <snippet-id> <alias-name>    # Add alias to snippet
pypet alias list                              # List all aliases
pypet alias remove <snippet-id>               # Remove alias from snippet
pypet alias setup                             # Show setup instructions

# Git synchronization
pypet sync init                    # Initialize Git repository
pypet sync remote <repo-url>       # Add/update remote repository
pypet sync status                  # Show sync status
pypet sync commit -m "message"     # Commit changes
pypet sync pull                    # Pull from remote
pypet sync push                    # Push to remote
pypet sync sync                    # Full sync (commit + pull + push)
```

### Shell Completion

`pypet` supports shell completion for Bash, Zsh, and Fish. This feature allows you to use the **Tab** key to automatically complete commands, subcommands, and options.

To enable shell completion:

#### Bash

Add the following to your `~/.bashrc`:

```bash
eval "$(_PYPET_COMPLETE=bash_source pypet)"
```

#### Zsh

Add the following to your `~/.zshrc`:

```zsh
eval "$(_PYPET_COMPLETE=zsh_source pypet)"
```

#### Fish

Add the following to your `~/.config/fish/completions/pypet.fish`:

```fish
_PYPET_COMPLETE=fish_source pypet | source
```

---

### Parameterized Snippets

You can create snippets with customizable parameters:

```bash
# Create a snippet with parameters
pypet new "docker run -p {{port}}:80 -v {{path}}:/app -e NODE_ENV={{env=development}} {{image}}" \
    -d "Run a Docker container with custom settings" \
    -t "docker,container" \
    -p "port:Host port to bind,path:Volume path,env=development:Node environment,image:Docker image name"

# Execute with parameter values
pypet exec <snippet-id> -P port=3000 -P path=$PWD -P image=node:18-alpine

# Or execute interactively (will prompt for parameter values)
pypet exec <snippet-id>
```

Parameters can have:

- Required values: `{{name}}`
- Default values: `{{name=default}}`
- Descriptions (shown when prompting)

Example TOML storage for a parameterized snippet:

```toml
[snippets.unique-id]
command = "docker run -p {{port}}:80 -v {{path}}:/app -e NODE_ENV={{env=development}} {{image}}"
description = "Run a Docker container with custom settings"
tags = ["docker", "container"]
created_at = "2025-06-17T10:00:00+00:00"
updated_at = "2025-06-17T10:00:00+00:00"

[snippets.unique-id.parameters.port]
name = "port"
description = "Host port to bind"

[snippets.unique-id.parameters.path]
name = "path"
description = "Volume path"

[snippets.unique-id.parameters.env]
name = "env"
default = "development"
description = "Node environment"

[snippets.unique-id.parameters.image]
name = "image"
description = "Docker image name"
```

### AI Snippet Generation

`pypet gen` turns a natural-language prompt into a snippet draft.

```bash
# Generate a snippet from a prompt
pypet gen "kill process listening on port 3000"
```

How it works:

1. `pypet` reads `OPENROUTER_API_KEY` or `~/.config/pypet/config.toml`.
2. If no key is available, it prompts once and saves it.
3. It sends your prompt plus a strict JSON schema request to OpenRouter.
4. The response is shown in a review table with `command`, `description`,
   `tags`, and `parameters`.
5. If you confirm, `pypet` saves the snippet and can optionally create an
   alias.

Configuration:

```toml
openrouter_api_key = "sk-..."
ai_model = "google/gemini-2.5-flash"
```

Environment variables override the config file:

- `OPENROUTER_API_KEY`
- `OPENROUTER_MODEL`

Notes:

- The generated command is never executed automatically.
- Quote prompts with spaces, for example `pypet gen "..."`.

### Saving Snippets from Clipboard and History

`pypet` provides convenient ways to save snippets from your clipboard or shell history:

#### Save from Clipboard

```bash
# Save current clipboard content
pypet save-clipboard -d "My command description" -t "docker,development"

# Interactive mode (prompts for description and tags)
pypet save-clipboard
```

This command automatically detects parameters in the clipboard content and prompts you to add descriptions for them.

#### Save from Shell History

```bash
# Save the last command from your shell history
pypet save-last

# Save multiple commands (creates separate snippets)
pypet save-last -n 3

# With description and tags
pypet save-last -d "Build command" -t "build,make"
```

The `save-last` command works with bash, zsh, and other popular shells. It reads from your shell history file and lets you save recent commands as snippets.

> **⚠️ Note:** This feature has limitations. Bash only writes to the history file when the shell exits or when you run `history -a`. Commands in your current session may not be available. Run `history -a && pypet save-last` for best results.

### Shell Aliases

`pypet` can create persistent shell aliases from your snippets, making frequently-used commands instantly accessible without needing to run `pypet exec`.

#### Adding Aliases to Snippets

```bash
# Create a new snippet with an alias
pypet new "ls -la" -d "List all files" -a ll

# Add an alias to an existing snippet
pypet alias add <snippet-id> ll

# List all snippets with aliases
pypet alias list

# Show the generated alias definition
pypet alias show <snippet-id>

# Remove an alias from a snippet
pypet alias remove <snippet-id>
```

#### Setting Up Aliases

After creating aliases, you need to source the aliases file in your shell:

```bash
# Show setup instructions
pypet alias setup

# Copy the source command to clipboard
pypet alias setup --copy
```

Add this line to your shell profile (`~/.bashrc` for bash, `~/.zshrc` for zsh):

```bash
source ~/.config/pypet/aliases.sh
```

Then reload your shell or run:

```bash
source ~/.config/pypet/aliases.sh
```

#### How Aliases Work

- **Simple snippets** (no parameters): Created as regular shell aliases

  ```bash
  pypet new "ls -la" -a ll
  # Generates: alias ll='ls -la'
  ```

- **Parameterized snippets**: Created as shell functions that call `pypet exec`

  ```bash
  pypet new "ssh {{user}}@{{host}}" -a myssh
  # Generates a function that prompts for parameters
  ```

#### Managing Aliases

```bash
# Regenerate the aliases file (useful after manual edits)
pypet alias update

# View all aliases
pypet alias list
```

The aliases are stored in `~/.config/pypet/aliases.sh` and are automatically updated whenever you add or remove aliases.

### Interactive Mode

When running `pypet exec` without a snippet ID, it enters interactive mode:

1. Shows a table of all available snippets
2. Lets you select a snippet by number
3. Optionally allows editing the command before execution
4. Asks for confirmation before running the command

## Git Synchronization

`pypet` supports Git-based synchronization to backup and share your snippets across devices.

### Setup

```bash
# Initialize Git repository for snippets
pypet sync init

# Initialize with remote repository
pypet sync init --remote https://github.com/username/pypet-snippets.git

# Or add remote to existing repository
pypet sync remote https://github.com/username/pypet-snippets.git
```

### Basic Operations

```bash
# Check sync status
pypet sync status

# Commit current changes
pypet sync commit -m "Added new Docker snippets"

# Pull changes from remote
pypet sync pull

# Push changes to remote
pypet sync push

# Full sync (commit + pull + push)
pypet sync sync
```

### Backup Management

```bash
# List available backups
pypet sync backups

# Restore from backup
pypet sync restore snippets_backup_20250101_120000.toml
```

**Automatic Cleanup**: `pypet` automatically manages your backups by keeping only the 5 most recent backup files. Old backups are cleaned up during sync operations to prevent disk space accumulation.

### Workflow

1. **Initial Setup**: Run `pypet sync init` to create a Git repository
2. **Add Remote**: Use `--remote` option or manually configure Git remote
3. **Regular Sync**: Use `pypet sync sync` to keep snippets synchronized
4. **Automatic Backups**: Backups are created before pull operations

## Development

This project uses `uv` for dependency management, `pytest` for testing, and includes pre-push git hooks for quality assurance.

### Quick Setup

```bash
# Clone the repository
git clone https://github.com/fabiandistler/pypet.git
cd pypet

# Set up development environment with hooks (recommended)
make dev
```

This installs the package in development mode and sets up pre-push git hooks that automatically run linting and tests before each push.

### Manual Setup

```bash
# Create virtual environment
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install package in development mode
uv pip install -e ".[dev]"

# Install git hooks (optional but recommended)
make hooks
```

### Development Commands

```bash
# Format code with Ruff
make format

# Check linting with ruff
make lint

# Run tests
make test

# Run format, lint, type-check, clean, and quick tests
make all

# Clean build artifacts
make clean
```

### Testing

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_cli.py

# Run with coverage
pytest --cov=pypet
```

### Git Hooks

Pre-push hooks automatically run before each push:

- Code formatting with `ruff format --check`
- Linting with `ruff check`
- Quick tests with `pytest -x -q`

To bypass hooks (use sparingly):

```bash
git push --no-verify
```

To skip only tests (for quick iterations):

```bash
SKIP_TESTS=1 git push
```

## Storage Format

Snippets are stored in TOML format at `~/.config/pypet/snippets.toml`:

```toml
[snippets.unique-id]
command = "git status"
description = "Check git status"
tags = ["git", "status"]
alias = "gs"
created_at = "2025-06-17T10:00:00+00:00"
updated_at = "2025-06-17T10:00:00+00:00"
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see the [LICENSE](LICENSE) file for details
