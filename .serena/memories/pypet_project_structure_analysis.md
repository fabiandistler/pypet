# pypet Project Structure Analysis

## Project Overview
- **Name**: pypet-cli
- **Version**: 0.2.0
- **Purpose**: Modern command-line snippet manager with Git synchronization, clipboard integration, and parameterized commands
- **Language**: Python 3.10+
- **Repository**: https://github.com/fabiandistler/pypet

## Disk Space Summary
- `.venv/` - 77 MB (active virtual environment with uv)
- `pypet-env/` - 16 MB (legacy/unused virtual environment)
- `.git/` - 2.3 MB (repository history)
- Total project: ~180 MB

## Directory Structure

### Core Source Code
- `pypet/` - Main package directory
  - `__init__.py` - Package initialization
  - `cli.py` - Click-based CLI interface
  - `models.py` - Dataclasses for Snippet and Parameter
  - `storage.py` - TOML file persistence
  - `sync.py` - Git synchronization
  - `__pycache__/` - Python bytecode cache (ignored)

### Tests
- `tests/` - Test suite (280 KB)
  - `test_cli.py` - CLI command tests
  - `test_models.py` - Model validation tests
  - `test_storage.py` - Storage/persistence tests
  - `test_sync.py` - Git sync tests
  - `test_sync_cli.py` - Sync CLI tests
  - `__init__.py` - Package marker
  - `__pycache__/` - Test bytecode (ignored)

### Configuration Files
- `pyproject.toml` - Project metadata and dependencies (uv format)
- `pytest.ini` - Pytest configuration
- `Makefile` - Development commands (format, lint, test, etc.)
- `uv.lock` - uv dependency lock file (119 KB)

### Documentation
- `README.md` - Project readme
- `CHANGELOG.md` - Version history
- `CLAUDE.md` - Project-specific instructions for Claude Code
- `LICENSE` - MIT license

### Scripts
- `scripts/install-hooks.sh` - Pre-push git hook installation script

### IDE & Editor Configuration
- `.vscode/settings.json` - VS Code pytest configuration
- `.vscode/tasks.json` - VS Code build tasks

### CI/CD
- `.github/workflows/ci.yml` - GitHub Actions CI pipeline
- `.github/workflows/release.yml` - GitHub Actions release automation

### Development Tools (Serena)
- `.serena/project.yml` - Serena language server configuration (metadata)
- `.serena/memories/` - Serena development memory files
- `.serena/.gitignore` - Serena-specific gitignore

### Virtual Environments
- `.venv/` - **ACTIVE** uv-managed virtual environment (77 MB)
  - Contains: black, ruff, pytest, pyperclip, gitpython, click, rich, toml
  - Status: Current, fully functional
  
- `pypet-env/` - **LEGACY/UNUSED** virtual environment (16 MB)
  - Status: Appears to be an old environment that was never fully populated
  - bin/ is empty except for basic activation scripts
  - Should be deleted as it's redundant

### Cache Directories (All Ignored)
- `.pytest_cache/` (44 KB)
  - `v/cache/lastfailed` - Failed test tracking
  - `v/cache/nodeids` - Test discovery cache
  - `CACHEDIR.TAG` - Cache marker
  
- `.ruff_cache/` (24 KB)
  - Version-specific cache: `0.12.0/`
  - Contains compiled lint checks
  
- `.claude/` - Claude/Claude Code agent data (ignored)

### Ignored Files (Not Committed)
- `.env` - Local environment configuration
- `.pypet.toml` - Local pypet configuration
- `__pycache__/` - Python bytecode everywhere
- `*.pyc`, `*.pyo` - Compiled Python files
- `*.egg-info/` - Egg metadata
- `.installed.cfg` - Installation marker
- `build/`, `dist/`, `downloads/`, `wheels/` - Build artifacts
- `lib/`, `lib64/`, `var/`, `sdist/` - Build directories

### Demo/Example
- `demo-pypet/` - Example/demo directory structure
  - `.config/pypet/` - Demo config location
  - Status: Appears to be a testing structure for config

## Potentially Problematic Items

### 1. Redundant Virtual Environment
- **Location**: `pypet-env/` (16 MB)
- **Issue**: Legacy virtual environment that's not used; project uses `.venv/` with uv
- **Impact**: Takes up 16 MB disk space, causes confusion about which venv is active
- **Recommendation**: DELETE

### 2. Serena Untracked Files
- **Location**: `.serena/` (20 KB)
- **Issue**: Currently untracked (not in gitignore but appears as untracked in git status)
- **Status**: Contains useful project metadata (project.yml, memories/)
- **Question**: Should this be tracked or added to gitignore?

### 3. Demo Directory
- **Location**: `demo-pypet/` (12 KB)
- **Issue**: Unclear purpose, appears to be a test config structure
- **Recommendation**: Clarify purpose or document

### 4. Gitignore Patterns
- All cache directories properly ignored
- No tracked cache/build files detected
- Virtual environment patterns correctly configured

## File Type Summary
- Python code: `pypet/*.py`, `tests/*.py` - clean source
- Configuration: TOML, YAML, INI, JSON - well organized
- Documentation: Markdown files - README, CLAUDE, CHANGELOG
- Build/Cache: All properly excluded
- IDE: VS Code configuration only

## Development Workflow Notes
- Uses `uv` for package management and virtual environment
- Pre-push git hooks installed (via `scripts/install-hooks.sh`)
- Black (formatter) and Ruff (linter) configured
- Pytest configured for testing
- GitHub Actions for CI/Release

## Recommendations for Cleanup
1. Delete `pypet-env/` directory (16 MB space savings)
2. Clarify/document purpose of `demo-pypet/`
3. Consider adding `.serena/` to gitignore if not intended to be tracked (or track it properly)
4. Current cache/build artifact exclusions are appropriate
