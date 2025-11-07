"""
Main entry point for pypet CLI
"""

import io
from contextlib import redirect_stderr, redirect_stdout

import click
from rich.console import Console
from rich.prompt import Prompt

from ..config import Config
from ..models import Parameter, Snippet
from ..storage import Storage
from ..sync import SyncManager


# Global instances
console = Console()
storage = Storage()
sync_manager = SyncManager(storage.config_path)
config = Config()


def _auto_sync_if_enabled() -> None:
    """Perform auto-sync if enabled in config."""
    if not config.auto_sync:
        return

    # Only auto-sync if we're in a git repo with a remote
    if not sync_manager.is_git_repo:
        return

    if not sync_manager.repo or "origin" not in [
        r.name for r in sync_manager.repo.remotes
    ]:
        return

    # Perform sync quietly (suppress normal output)
    try:
        # Create a buffer to capture output
        buffer = io.StringIO()

        with redirect_stdout(buffer), redirect_stderr(buffer):
            success = sync_manager.sync(auto_commit=True, commit_message=None)

        # Only show errors or minimal success message
        if not success:
            console.print(
                "[yellow]Auto-sync encountered errors. Use 'pypet sync status' to check.[/yellow]"
            )
    except Exception:
        # Silently fail - don't interrupt the user's workflow
        pass


def _format_parameters(snippet: Snippet | None) -> str:
    """Format parameters for display in table."""
    if not snippet:
        return ""

    parameters = snippet.get_all_parameters()
    if not parameters:
        return ""

    return ", ".join(
        f"{name}={param.default or '<required>'}"
        + (f" ({param.description})" if param.description else "")
        for name, param in parameters.items()
    )


def _parse_parameters(param_str: str) -> dict[str, Parameter]:
    """Parse parameter string into Parameter objects.

    Format: name[=default][:description],name[=default][:description],...
    Example: host=localhost:The host to connect to,port=8080:Port number
    """
    if not param_str:
        return {}

    parameters = {}
    for param_def in param_str.split(","):
        if ":" in param_def:
            param_part, description = param_def.split(":", 1)
        else:
            param_part, description = param_def, None

        if "=" in param_part:
            name, default = param_part.split("=", 1)
        else:
            name, default = param_part, None

        parameters[name.strip()] = Parameter(
            name=name.strip(),
            default=default.strip() if default else None,
            description=description.strip() if description else None,
        )

    return parameters


def _prompt_for_parameters(
    snippet: Snippet, provided_params: dict[str, str] | None = None
) -> dict[str, str]:
    """Prompt user for parameter values that weren't already provided."""
    provided_params = provided_params or {}
    all_parameters = snippet.get_all_parameters()
    if not all_parameters:
        return {}

    values = {}
    for name, param in all_parameters.items():
        # Skip parameters that were already provided
        if name in provided_params:
            continue

        prompt = f"{name}"
        if param.description:
            prompt += f" ({param.description})"
        if param.default:
            prompt += f" [{param.default}]"

        value = Prompt.ask(prompt)
        if value:
            values[name] = value
        elif param.default:
            values[name] = param.default

    return values


@click.group()
@click.version_option()
def main() -> None:
    """A command-line snippet manager inspired by pet."""
    pass
