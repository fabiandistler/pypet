"""
CLI module for pypet - command-line snippet manager

This module is organized into submodules for better maintainability:
- main: Core CLI group and helper functions
- snippet_commands: Commands for managing snippets (new, list, search, delete, edit)
- execution_commands: Commands for executing and copying snippets (exec, copy)
- save_commands: Commands for saving from clipboard and shell history
- sync_commands: Commands for Git synchronization
"""

# Import main module first to avoid circular imports
from . import main as main_module  # noqa: I001
from .main import main

# Import command modules to register commands (they depend on main_module)
from . import (  # noqa: F401
    alias_commands,
    execution_commands,
    save_commands,
    snippet_commands,
    sync_commands,
)


# Re-export global instances for tests
console = main_module.console
storage = main_module.storage
sync_manager = main_module.sync_manager
config = main_module.config

# Export main and global instances for the entry point and tests
__all__ = ["config", "console", "main", "main_module", "storage", "sync_manager"]
