"""
Command-line interface for pypet
"""

import os
import subprocess
from datetime import datetime
from pathlib import Path

import click
import pyperclip
from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.table import Table

from .models import Parameter, Snippet
from .storage import Storage
from .sync import SyncManager


console = Console()
storage = Storage()
sync_manager = SyncManager(storage.config_path)


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
def main():
    """A command-line snippet manager inspired by pet."""
    pass


@main.command(name="list")
def list_snippets():
    """List all snippets."""
    table = Table(title="Snippets")
    table.add_column("ID", style="blue")
    table.add_column("Command", style="cyan")
    table.add_column("Description", style="green")
    table.add_column("Tags", style="yellow")
    table.add_column("Parameters", style="magenta")

    for snippet_id, snippet in storage.list_snippets():
        table.add_row(
            snippet_id,
            snippet.command,
            snippet.description or "",
            ", ".join(snippet.tags) if snippet.tags else "",
            _format_parameters(snippet),
        )

    console.print(table)


@main.command()
@click.argument("command")
@click.option("--description", "-d", help="Description of the snippet")
@click.option("--tags", "-t", help="Tags for the snippet (comma-separated)")
@click.option(
    "--params",
    "-p",
    help="Parameters in format: name[=default][:description],... Example: host=localhost:The host,port=8080:Port number",
)
def new(
    command: str,
    description: str | None = None,
    tags: str | None = None,
    params: str | None = None,
):
    """Create a new snippet."""
    tag_list = [t.strip() for t in tags.split(",")] if tags else []
    parameters = _parse_parameters(params) if params else None

    snippet_id = storage.add_snippet(
        command=command,
        description=description,
        tags=tag_list,
        parameters=parameters,
    )
    console.print(f"[green]Added new snippet with ID:[/green] {snippet_id}")


@main.command("save-clipboard")
@click.option("--description", "-d", help="Description for the snippet")
@click.option("--tags", "-t", help="Tags for the snippet (comma-separated)")
@click.option(
    "--params",
    "-p",
    help="Parameters in format: name[=default][:description],... Example: host=localhost:The host,port=8080:Port number",
)
def save_clipboard(
    description: str | None = None,
    tags: str | None = None,
    params: str | None = None,
):
    """Save current clipboard content as a snippet."""
    try:
        command = pyperclip.paste()
        if not command or not command.strip():
            console.print(
                "[red]Error:[/red] Clipboard is empty or contains only whitespace"
            )
            return

        command = command.strip()
        console.print(f"[blue]Clipboard content:[/blue] {command}")

        # Ask for confirmation
        if not Confirm.ask("Save this as a snippet?"):
            console.print("[yellow]Cancelled.[/yellow]")
            return

        # Prompt for description if not provided
        if not description:
            description = Prompt.ask("Description", default="Snippet from clipboard")

        # Parse tags and parameters
        tag_list = [t.strip() for t in tags.split(",")] if tags else []
        parameters = _parse_parameters(params) if params else None

        snippet_id = storage.add_snippet(
            command=command,
            description=description,
            tags=tag_list,
            parameters=parameters,
        )
        console.print(f"[green]Added new snippet with ID:[/green] {snippet_id}")

    except Exception as e:
        console.print(f"[red]Error accessing clipboard:[/red] {e}")


@main.command("save-last")
@click.option("--description", "-d", help="Description for the snippet")
@click.option("--tags", "-t", help="Tags for the snippet (comma-separated)")
@click.option(
    "--params",
    "-p",
    help="Parameters in format: name[=default][:description],... Example: host=localhost:The host,port=8080:Port number",
)
@click.option(
    "--lines", "-n", default=1, help="Number of history lines to show (default: 1)"
)
def save_last(
    description: str | None = None,
    tags: str | None = None,
    params: str | None = None,
    lines: int = 1,
):
    """Save the last command(s) from shell history as a snippet."""
    try:
        # Try to read from history file directly (more reliable than history builtin)
        history_file = None

        # Check common history file locations
        possible_files = [
            os.environ.get("HISTFILE"),  # User's custom HISTFILE
            Path.home() / ".bash_history",
            Path.home() / ".zsh_history",
            Path.home() / ".history",
        ]

        for hist_file in possible_files:
            if hist_file and Path(hist_file).exists():
                history_file = Path(hist_file)
                break

        if not history_file:
            console.print("[red]Error:[/red] Could not find shell history file")
            console.print(
                "[yellow]Tip:[/yellow] Try using 'pypet save-clipboard' instead"
            )
            console.print(
                "[blue]Info:[/blue] Looked for: ~/.bash_history, ~/.zsh_history, ~/.history"
            )
            return

        # Read last lines from history file
        try:
            with history_file.open(encoding="utf-8", errors="ignore") as f:
                all_lines = f.readlines()
        except Exception as e:
            console.print(f"[red]Error reading history file:[/red] {e}")
            console.print(
                "[yellow]Tip:[/yellow] Try using 'pypet save-clipboard' instead"
            )
            return

        if not all_lines:
            console.print("[red]Error:[/red] History file is empty")
            return

        # Get last N non-empty lines
        recent_lines = []
        for line in reversed(all_lines):
            cleaned_line = line.strip()
            if cleaned_line and not cleaned_line.startswith("#"):  # Skip comments and empty lines
                # Handle zsh extended history format: : 1234567890:0;command
                if cleaned_line.startswith(": ") and ";" in cleaned_line:
                    cleaned_line = cleaned_line.split(";", 1)[1]
                recent_lines.append(cleaned_line)
                if (
                    len(recent_lines) >= lines + 10
                ):  # Get extra to filter pypet commands
                    break

        if not recent_lines:
            console.print("[red]Error:[/red] No commands found in history")
            return

        # Filter out pypet commands and prepare final list
        commands = []
        for command in recent_lines:
            # Skip pypet commands to avoid recursion
            if not command.startswith("pypet") and command.strip():
                commands.append(command.strip())
                if len(commands) >= lines:  # We have enough commands
                    break

        if not commands:
            console.print("[red]Error:[/red] No valid commands found in recent history")
            console.print("[yellow]Tip:[/yellow] Make sure you run some commands first")
            return

        # Show the commands and let user choose
        if len(commands) == 1:
            command = commands[0]
        else:
            console.print("[blue]Recent commands:[/blue]")
            for i, cmd in enumerate(commands, 1):
                console.print(f"  {i}. {cmd}")

            choice = Prompt.ask(
                "Which command to save?",
                choices=[str(i) for i in range(1, len(commands) + 1)],
                default="1",
            )
            command = commands[int(choice) - 1]

        console.print(f"[blue]Selected command:[/blue] {command}")

        # Ask for confirmation
        if not Confirm.ask("Save this as a snippet?"):
            console.print("[yellow]Cancelled.[/yellow]")
            return

        # Prompt for description if not provided
        if not description:
            description = Prompt.ask(
                "Description", default=f"Command from history: {command[:50]}..."
            )

        # Parse tags and parameters
        tag_list = [t.strip() for t in tags.split(",")] if tags else []
        parameters = _parse_parameters(params) if params else None

        snippet_id = storage.add_snippet(
            command=command,
            description=description,
            tags=tag_list,
            parameters=parameters,
        )
        console.print(f"[green]Added new snippet with ID:[/green] {snippet_id}")

    except subprocess.TimeoutExpired:
        console.print("[red]Error:[/red] Timeout accessing shell history")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        console.print("[yellow]Tip:[/yellow] Try using 'pypet save-clipboard' instead")


@main.command()
@click.argument("query")
def search(query: str):
    """Search for snippets."""
    table = Table(title=f"Search Results for '{query}'")
    table.add_column("ID", style="blue")
    table.add_column("Command", style="cyan")
    table.add_column("Description", style="green")
    table.add_column("Tags", style="yellow")
    table.add_column("Parameters", style="magenta")

    for snippet_id, snippet in storage.search_snippets(query):
        table.add_row(
            snippet_id,
            snippet.command,
            snippet.description or "",
            ", ".join(snippet.tags) if snippet.tags else "",
            _format_parameters(snippet),
        )

    console.print(table)


@main.command()
@click.argument("snippet_id")
def delete(snippet_id: str):
    """Delete a snippet."""
    if storage.delete_snippet(snippet_id):
        console.print(f"[green]Deleted snippet:[/green] {snippet_id}")
    else:
        console.print(f"[red]Snippet not found:[/red] {snippet_id}")


@main.command()
@click.argument("snippet_id", required=False)
@click.option("--command", "-c", help="New command")
@click.option("--description", "-d", help="New description")
@click.option("--tags", "-t", help="New tags (comma-separated)")
@click.option(
    "--params",
    "-p",
    help="Parameters in format: name[=default][:description],... Example: host=localhost:The host,port=8080:Port number",
)
@click.option(
    "--file", "-f", "edit_file", is_flag=True, help="Open TOML file directly in editor"
)
def edit(
    snippet_id: str | None = None,
    command: str | None = None,
    description: str | None = None,
    tags: str | None = None,
    params: str | None = None,
    edit_file: bool = False,
):
    """Edit an existing snippet or open TOML file directly."""
    # Handle --file option to open TOML directly
    if edit_file:
        editor = os.environ.get("EDITOR", "nano")

        # Basic validation: editor should not contain shell metacharacters
        if any(char in editor for char in [";", "&", "|", ">", "<", "`", "$"]):
            console.print(
                f"[red]Error:[/red] Invalid EDITOR value '{editor}'. "
                "EDITOR should be a simple command name or path."
            )
            return

        try:
            subprocess.run([editor, str(storage.config_path)], check=False)
            console.print(f"[green]✓ Opened {storage.config_path} in {editor}[/green]")
        except FileNotFoundError:
            console.print(
                f"[red]Error:[/red] Editor '{editor}' not found. Set EDITOR environment variable."
            )
        except Exception as e:
            console.print(f"[red]Error:[/red] Failed to open editor: {e}")
        return

    # Require snippet_id if not using --file option
    if not snippet_id:
        console.print(
            "[red]Error:[/red] Either provide a snippet ID or use --file to edit TOML directly"
        )
        console.print("[yellow]Examples:[/yellow]")
        console.print("  pypet edit abc123 --command 'new command'")
        console.print("  pypet edit --file")
        return

    # Check if snippet exists first
    existing = storage.get_snippet(snippet_id)
    if not existing:
        console.print(f"[red]Error:[/red] Snippet with ID '{snippet_id}' not found")
        return

    # Only split tags if they were provided
    tag_list = [t.strip() for t in tags.split(",")] if tags is not None else None

    # Only parse parameters if they were provided
    parameters = _parse_parameters(params) if params is not None else None

    # Update the snippet
    if storage.update_snippet(
        snippet_id,
        command=command,
        description=description,
        tags=tag_list,
        parameters=parameters,
    ):
        # Get the updated version
        updated = storage.get_snippet(snippet_id)
        if updated:
            console.print(
                f"\n[green]Successfully updated snippet:[/green] {snippet_id}"
            )

            # Show the updated snippet
            table = Table(title="Updated Snippet")
            table.add_column("Field", style="blue")
            table.add_column("Value", style="cyan")

            table.add_row("ID", snippet_id)
            table.add_row("Command", updated.command)
            table.add_row("Description", updated.description or "")
            table.add_row("Tags", ", ".join(updated.tags) if updated.tags else "")
            table.add_row("Parameters", _format_parameters(updated))

            console.print(table)
    else:
        console.print("[red]Failed to update snippet[/red]")


@main.command()
@click.argument("snippet_id", required=False)
@click.option(
    "--param",
    "-P",
    multiple=True,
    help="Parameter values in name=value format. Can be specified multiple times.",
)
def copy(
    snippet_id: str | None = None,
    param: tuple[str, ...] = (),
):
    """Copy a snippet to clipboard. If no snippet ID is provided, shows an interactive selection."""
    try:
        selected_snippet = None

        if snippet_id is None:
            # Show interactive snippet selection
            snippets = storage.list_snippets()
            if not snippets:
                console.print(
                    "[yellow]No snippets found.[/yellow] Add some with 'pypet new'"
                )
                return

            # Display snippets table for selection
            table = Table(title="Available Snippets")
            table.add_column("Index", style="blue")
            table.add_column("ID", style="cyan")
            table.add_column("Command", style="green")
            table.add_column("Description", style="yellow")
            table.add_column("Parameters", style="magenta")

            for i, (id_, snippet) in enumerate(snippets, 1):
                table.add_row(
                    str(i),
                    id_,
                    snippet.command,
                    snippet.description or "",
                    _format_parameters(snippet),
                )

            console.print(table)

            # Get user selection
            while True:
                try:
                    choice_str = Prompt.ask("Enter snippet number (or 'q' to quit)")
                    if choice_str.lower() == "q":
                        return
                    choice = int(choice_str)
                    if 1 <= choice <= len(snippets):
                        selected_snippet = snippets[choice - 1][1]
                        snippet_id = snippets[choice - 1][0]
                        break
                    console.print("[red]Invalid selection[/red]")
                except (ValueError, EOFError):
                    console.print("[red]Please enter a number[/red]")
                except KeyboardInterrupt:
                    console.print("\n[yellow]Operation cancelled[/yellow]")
                    return
        else:
            # Get snippet by ID
            selected_snippet = storage.get_snippet(snippet_id)
            if not selected_snippet:
                console.print(f"[red]Snippet not found:[/red] {snippet_id}")
                raise click.ClickException(f"Snippet not found: {snippet_id}")

        # Parse provided parameter values
        param_values = {}
        for p in param:
            try:
                name, value = p.split("=", 1)
                param_values[name.strip()] = value.strip()
            except ValueError:
                console.print(
                    f"[red]Invalid parameter format:[/red] {p}. Use name=value"
                )
                return

        # If not all parameters are provided via command line, prompt for them
        all_parameters = selected_snippet.get_all_parameters()
        if all_parameters and len(param_values) < len(all_parameters):
            interactive_values = _prompt_for_parameters(selected_snippet, param_values)
            param_values.update(interactive_values)

        # Apply parameters to get final command
        try:
            final_command = selected_snippet.apply_parameters(param_values)
        except ValueError as e:
            console.print(f"[red]Error:[/red] {e!s}")
            return

        # Copy to clipboard
        try:
            pyperclip.copy(final_command)
            console.print(f"[green]✓ Copied to clipboard:[/green] {final_command}")
        except Exception as e:
            console.print(f"[red]Failed to copy to clipboard:[/red] {e!s}")
            console.print(f"[yellow]Command:[/yellow] {final_command}")

    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled[/yellow]")


@main.command()
@click.argument("snippet_id", required=False)
@click.option(
    "--print-only", "-p", is_flag=True, help="Only print the command without executing"
)
@click.option("--edit", "-e", is_flag=True, help="Edit command before execution")
@click.option(
    "--copy", "-c", is_flag=True, help="Copy command to clipboard instead of executing"
)
@click.option(
    "--param",
    "-P",
    multiple=True,
    help="Parameter values in name=value format. Can be specified multiple times.",
)
def exec(
    snippet_id: str | None = None,
    print_only: bool = False,
    edit: bool = False,
    copy: bool = False,
    param: tuple[str, ...] = (),
):
    """Execute a saved snippet. If no snippet ID is provided, shows an interactive selection."""
    try:
        selected_snippet = None

        if snippet_id is None:
            # Show interactive snippet selection
            snippets = storage.list_snippets()
            if not snippets:
                console.print(
                    "[yellow]No snippets found.[/yellow] Add some with 'pypet new'"
                )
                return

            # Display snippets table for selection
            table = Table(title="Available Snippets")
            table.add_column("Index", style="blue")
            table.add_column("ID", style="cyan")
            table.add_column("Command", style="green")
            table.add_column("Description", style="yellow")
            table.add_column("Parameters", style="magenta")

            for i, (id_, snippet) in enumerate(snippets, 1):
                table.add_row(
                    str(i),
                    id_,
                    snippet.command,
                    snippet.description or "",
                    _format_parameters(snippet),
                )

            console.print(table)

            # Get user selection
            while True:
                try:
                    choice_str = Prompt.ask("Enter snippet number (or 'q' to quit)")
                    if choice_str.lower() == "q":
                        return
                    choice = int(choice_str)
                    if 1 <= choice <= len(snippets):
                        selected_snippet = snippets[choice - 1][1]
                        snippet_id = snippets[choice - 1][0]
                        break
                    console.print("[red]Invalid selection[/red]")
                except (ValueError, EOFError):
                    console.print("[red]Please enter a number[/red]")
                except KeyboardInterrupt:
                    console.print("\n[yellow]Operation cancelled[/yellow]")
                    return
        else:
            # Get snippet by ID
            selected_snippet = storage.get_snippet(snippet_id)
            if not selected_snippet:
                console.print(f"[red]Snippet not found:[/red] {snippet_id}")
                raise click.ClickException(f"Snippet not found: {snippet_id}")

        # Parse provided parameter values
        param_values = {}
        for p in param:
            try:
                name, value = p.split("=", 1)
                param_values[name.strip()] = value.strip()
            except ValueError:
                console.print(
                    f"[red]Invalid parameter format:[/red] {p}. Use name=value"
                )
                return

        # If not all parameters are provided via command line, prompt for them
        all_parameters = selected_snippet.get_all_parameters()
        if all_parameters and len(param_values) < len(all_parameters):
            interactive_values = _prompt_for_parameters(selected_snippet, param_values)
            param_values.update(interactive_values)

        # Apply parameters to get final command
        try:
            final_command = selected_snippet.apply_parameters(param_values)
        except ValueError as e:
            console.print(f"[red]Error:[/red] {e!s}")
            return

        if edit:
            try:
                final_command = click.edit(final_command)
                if final_command is None:
                    console.print("[yellow]Command execution cancelled[/yellow]")
                    return
            except click.ClickException:
                # Fallback for non-interactive environments (like tests)
                console.print(
                    "[yellow]Editor not available, using original command[/yellow]"
                )

        if print_only:
            console.print(final_command)
        elif copy:
            try:
                pyperclip.copy(final_command)
                console.print(f"[green]✓ Copied to clipboard:[/green] {final_command}")
            except Exception as e:
                console.print(f"[red]Failed to copy to clipboard:[/red] {e!s}")
                console.print(f"[yellow]Command:[/yellow] {final_command}")
        else:
            # Check for potentially dangerous patterns
            dangerous_patterns = [";", "&&", "||", "|", ">", ">>", "<", "`", "$()"]
            has_dangerous = any(
                pattern in final_command for pattern in dangerous_patterns
            )

            # Confirm before execution
            console.print(f"[yellow]Execute command:[/yellow] {final_command}")

            if has_dangerous:
                console.print(
                    "[red]Warning:[/red] Command contains shell operators that could be dangerous."
                )
                console.print(
                    "[yellow]Please review carefully before executing.[/yellow]"
                )

            if not Confirm.ask("Execute this command?"):
                console.print("[yellow]Command execution cancelled[/yellow]")
                return

            try:
                # Note: shell=True is required for pypet's use case of executing shell commands
                # with pipes, redirects, etc. User confirmation is required before execution.
                subprocess.run(final_command, shell=True, check=True)
            except subprocess.CalledProcessError as e:
                console.print(
                    f"[red]Command failed with exit code {e.returncode}[/red]"
                )
            except Exception as e:
                console.print(f"[red]Error executing command:[/red] {e!s}")

    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled[/yellow]")


@main.group()
def sync():
    """Synchronize snippets with Git repositories."""
    pass


@sync.command()
@click.option("--remote", "-r", help="Remote repository URL")
def init(remote: str | None = None):
    """Initialize Git repository for snippet synchronization."""
    if not sync_manager.git_available:
        console.print(
            "[red]Git is not available. Please install Git to use sync features.[/red]"
        )
        raise click.ClickException("Git not available")

    if sync_manager.is_git_repo:
        console.print("[yellow]Git repository already initialized[/yellow]")
        return

    if sync_manager.init_git_repo(remote):
        console.print("[green]Git sync initialized successfully[/green]")
        if remote:
            console.print(f"[blue]Remote origin set to: {remote}[/blue]")
    else:
        raise click.ClickException("Failed to initialize Git repository")


@sync.command()
def status():
    """Show Git synchronization status."""
    status_info = sync_manager.get_status()

    table = Table(title="Git Sync Status")
    table.add_column("Property", style="blue")
    table.add_column("Value", style="cyan")

    for key, value in status_info.items():
        display_key = key.replace("_", " ").title()
        table.add_row(display_key, value)

    console.print(table)


@sync.command()
@click.option("--message", "-m", help="Commit message")
def commit(message: str | None = None):
    """Commit current snippet changes to Git."""
    if sync_manager.commit_changes(message):
        console.print("[green]Changes committed successfully[/green]")
    else:
        raise click.ClickException("Failed to commit changes")


@sync.command()
def pull():
    """Pull snippet changes from remote repository."""
    if sync_manager.pull_changes():
        console.print("[green]Changes pulled successfully[/green]")
    else:
        raise click.ClickException("Failed to pull changes")


@sync.command()
def push():
    """Push snippet changes to remote repository."""
    if sync_manager.push_changes():
        console.print("[green]Changes pushed successfully[/green]")
    else:
        raise click.ClickException("Failed to push changes")


@sync.command("sync")
@click.option("--no-commit", is_flag=True, help="Skip auto-commit before sync")
@click.option("--message", "-m", help="Commit message for auto-commit")
def sync_all(no_commit: bool = False, message: str | None = None):
    """Perform full synchronization: commit, pull, and push."""
    auto_commit = not no_commit
    if sync_manager.sync(auto_commit=auto_commit, commit_message=message):
        console.print("[green]Full sync completed successfully[/green]")
    else:
        raise click.ClickException("Sync completed with errors")


@sync.command()
def backups():
    """List available backup files."""
    backup_files = sync_manager.list_backups()

    if not backup_files:
        console.print("[yellow]No backup files found[/yellow]")
        return

    table = Table(title="Available Backups")
    table.add_column("File", style="blue")
    table.add_column("Size", style="green")
    table.add_column("Modified", style="yellow")

    for backup in backup_files:
        stat = backup.stat()
        size = f"{stat.st_size} bytes"
        modified = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        table.add_row(backup.name, size, modified)

    console.print(table)


@sync.command()
@click.argument("backup_file")
def restore(backup_file: str):
    """Restore snippets from a backup file."""
    backup_path = sync_manager.config_dir / backup_file

    if sync_manager.restore_backup(backup_path):
        console.print(f"[green]Successfully restored from {backup_file}[/green]")
    else:
        raise click.ClickException(f"Failed to restore from {backup_file}")


@sync.command()
@click.argument("remote_url")
@click.option("--name", "-n", default="origin", help="Remote name (default: origin)")
def remote(remote_url: str, name: str = "origin"):
    """Add or update a Git remote for synchronization."""
    if not sync_manager.is_git_repo:
        console.print(
            "[red]Not in a Git repository. Use 'pypet sync init' first.[/red]"
        )
        raise click.ClickException("Not in a Git repository")

    if not sync_manager.repo:
        raise click.ClickException("Failed to access Git repository")

    try:
        # Check if remote already exists
        if name in [r.name for r in sync_manager.repo.remotes]:
            # Update existing remote
            remote_obj = sync_manager.repo.remotes[name]
            remote_obj.set_url(remote_url)
            console.print(f"[green]✓ Updated remote '{name}' to: {remote_url}[/green]")
        else:
            # Add new remote
            sync_manager.repo.create_remote(name, remote_url)
            console.print(f"[green]✓ Added remote '{name}': {remote_url}[/green]")

        # Show current remotes
        console.print("\n[blue]Current remotes:[/blue]")
        for r in sync_manager.repo.remotes:
            console.print(f"  {r.name}: {r.url}")

    except Exception as e:
        console.print(f"[red]Failed to configure remote: {e}[/red]")
        raise click.ClickException(f"Failed to configure remote: {e}")


@sync.command()
@click.option(
    "--keep", "-k", default=5, help="Number of backup files to keep (default: 5)"
)
@click.option(
    "--dry-run",
    "-n",
    is_flag=True,
    help="Show what would be deleted without actually deleting",
)
def cleanup(keep: int, dry_run: bool):
    """Clean up old backup files."""
    backups = sync_manager.list_backups()

    if len(backups) <= keep:
        console.print(
            f"[green]No cleanup needed. Found {len(backups)} backup files, keeping {keep}.[/green]"
        )
        return

    backups_to_delete = backups[keep:]

    if dry_run:
        console.print(
            f"[yellow]Would delete {len(backups_to_delete)} backup files:[/yellow]"
        )
        for backup in backups_to_delete:
            console.print(f"  {backup.name}")
        console.print("[blue]Run without --dry-run to actually delete them.[/blue]")
    else:
        deleted_count = sync_manager.cleanup_old_backups(keep)
        if deleted_count == 0:
            console.print("[green]No backups were deleted.[/green]")


if __name__ == "__main__":
    main()
