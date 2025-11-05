"""
CLI module for pypet - command-line snippet manager

This module is organized into submodules for better maintainability:
- main: Core CLI group and helper functions
- snippet_commands: Commands for managing snippets (new, list, search, delete, edit)
- execution_commands: Commands for executing and copying snippets (exec, copy)
- save_commands: Commands for saving from clipboard and shell history
- sync_commands: Commands for Git synchronization
"""

# Import the main module to make its attributes accessible for tests
from . import main as main_module

# Import the Click group for the entry point
from .main import main

# Import command modules to register commands with the main group
from . import execution_commands  # noqa: F401
from . import save_commands  # noqa: F401
from . import snippet_commands  # noqa: F401
from . import sync_commands  # noqa: F401

# Re-export global instances for tests
console = main_module.console
storage = main_module.storage
sync_manager = main_module.sync_manager

# Export main and global instances for the entry point and tests
__all__ = ["main", "console", "storage", "sync_manager", "main_module"]
