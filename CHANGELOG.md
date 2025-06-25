# Changelog

All notable changes to pypet will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-06-25

### 🎉 Initial Release

The first beta release of pypet - a modern command-line snippet manager inspired by [pet](https://github.com/knqyf263/pet).

### ✨ Features

#### Core Snippet Management
- **Create, list, search, edit, and delete** command snippets
- **TOML-based storage** at `~/.config/pypet/snippets.toml` 
- **Tag-based organization** for easy categorization
- **Rich terminal interface** with colored tables and formatted output
- **Interactive snippet selection** when no ID is provided

#### 🔧 Parameterized Snippets
- **Dynamic parameters** with `{name}` and `{name=default}` syntax
- **Interactive parameter prompting** during execution
- **Default value support** for commonly used parameters
- **Parameter descriptions** for better usability

#### 📋 Clipboard Integration  
- **Copy snippets to clipboard** with `pypet copy` command
- **Copy option in exec** with `pypet exec --copy`
- **Cross-platform support** (Windows, macOS, Linux)
- **Parameter substitution** before copying

#### 🔄 Git Synchronization
- **Initialize Git repositories** for snippet storage
- **Commit, pull, and push** operations with `pypet sync`
- **Automatic backup creation** before pull operations
- **Full sync workflow** with `pypet sync sync`
- **Backup management** with list and restore commands
- **Support for all Git services** (GitHub, GitLab, Bitbucket, etc.)

#### 💻 Commands
- `pypet new` - Create new snippets with parameters and tags
- `pypet list` - Display all snippets in a formatted table
- `pypet search <query>` - Search across commands, descriptions, and tags
- `pypet exec [id]` - Execute snippets with parameter substitution
- `pypet edit <id>` - Update existing snippets
- `pypet delete <id>` - Remove snippets
- `pypet copy [id]` - Copy snippets to clipboard
- `pypet sync` - Git synchronization commands (8 subcommands)

### 🛠️ Technical Details
- **Python 3.10+** with modern type hints and dataclasses
- **Professional dependencies**: Click, Rich, GitPython, pyperclip
- **Cross-platform compatibility** 
- **Comprehensive test suite** with 64+ tests
- **Human-readable storage** format

### 📚 Documentation
- Complete README with usage examples
- Git synchronization workflows
- Parameter system documentation
- Development setup guide

### 🔧 Dependencies
- `click>=8.1.7` - CLI framework
- `rich>=13.7.0` - Terminal formatting
- `toml>=0.10.2` - Configuration parsing
- `pyperclip>=1.9.0` - Clipboard operations
- `gitpython>=3.1.40` - Git integration

---

## Installation

```bash
pip install pypet
```

## Quick Start

```bash
# Create your first snippet
pypet new "docker run -p {port=8080}:80 {image}" -d "Run Docker container" -t "docker"

# List all snippets
pypet list

# Execute with parameters
pypet exec

# Copy to clipboard
pypet copy

# Initialize Git sync
pypet sync init
```

For full documentation, visit the [GitHub repository](https://github.com/fabiandistler/pypet).