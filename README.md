# pypet - Command Line Snippet Manager

`pypet` is a Python-based command-line snippet manager inspired by [pet](https://github.com/knqyf263/pet). It helps you organize and reuse command-line snippets efficiently, with a focus on simplicity and usability.

## Features

- Store command snippets with descriptions and tags
- TOML-based storage (`~/.config/pypet/snippets.toml`)
- List and search your snippets with rich terminal output
- Interactive command execution with pre-execution editing
- **Copy snippets to clipboard** for easy pasting into other applications
- **Git synchronization** for backup and sharing across devices
- Parameterized snippets with default values
- Automatic backup and restore functionality
- Tag-based organization
- Modern Python implementation with type hints
- Comprehensive test coverage

## Installation

### PyPI (Recommended)

```bash
pip install pypet
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

# Edit a snippet
pypet edit <snippet-id>

# Delete a snippet
pypet delete <snippet-id>

# Git synchronization
pypet sync init                    # Initialize Git repository
pypet sync status                  # Show sync status
pypet sync commit -m "message"     # Commit changes
pypet sync pull                    # Pull from remote
pypet sync push                    # Push to remote
pypet sync sync                    # Full sync (commit + pull + push)
```

### Parameterized Snippets

You can create snippets with customizable parameters:

```bash
# Create a snippet with parameters
pypet new "docker run -p {port}:80 -v {path}:/app -e NODE_ENV={env=development} {image}" \
    -d "Run a Docker container with custom settings" \
    -t "docker,container" \
    -p "port:Host port to bind,path:Volume path,env=development:Node environment,image:Docker image name"

# Execute with parameter values
pypet exec <snippet-id> -P port=3000 -P path=$PWD -P image=node:18-alpine

# Or execute interactively (will prompt for parameter values)
pypet exec <snippet-id>
```

Parameters can have:

- Required values: `{name}`
- Default values: `{name=default}`
- Descriptions (shown when prompting)

Example TOML storage for a parameterized snippet:

```toml
[snippets.unique-id]
command = "docker run -p {port}:80 -v {path}:/app -e NODE_ENV={env=development} {image}"
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

### Workflow

1. **Initial Setup**: Run `pypet sync init` to create a Git repository
2. **Add Remote**: Use `--remote` option or manually configure Git remote
3. **Regular Sync**: Use `pypet sync sync` to keep snippets synchronized
4. **Automatic Backups**: Backups are created before pull operations

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
