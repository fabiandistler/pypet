"""
Commands for managing snippets (new, list, search, delete, edit)
"""

import os
import subprocess

import click
from rich.prompt import Confirm, Prompt
from rich.table import Table

from ..alias_manager import AliasManager
from . import main_module as cli_main
from .main import _auto_sync_if_enabled, _format_parameters, _parse_parameters, main


@main.command(name="list")
def list_snippets() -> None:
    """List all snippets."""
    table = Table(title="Snippets")
    table.add_column("ID", style="blue", no_wrap=True)
    table.add_column("Command", style="cyan", overflow="fold", no_wrap=False)
    table.add_column("Description", style="green", no_wrap=False)
    table.add_column("Tags", style="yellow", no_wrap=False)
    table.add_column("Parameters", style="magenta", no_wrap=False)

    for snippet_id, snippet in cli_main.storage.list_snippets():
        table.add_row(
            snippet_id,
            snippet.command,
            snippet.description or "",
            ", ".join(snippet.tags) if snippet.tags else "",
            _format_parameters(snippet),
        )

    cli_main.console.print(table)


@main.command()
@click.argument("command")
@click.option("--description", "-d", help="Description of the snippet")
@click.option("--tags", "-t", help="Tags for the snippet (comma-separated)")
@click.option(
    "--params",
    "-p",
    help="Parameters in format: name[=default][:description],... Example: host=localhost:The host,port=8080:Port number",
)
@click.option("--alias", "-a", help="Create a shell alias for this snippet")
def new(
    command: str,
    description: str | None = None,
    tags: str | None = None,
    params: str | None = None,
    alias: str | None = None,
) -> None:
    """Create a new snippet."""
    tag_list = [t.strip() for t in tags.split(",")] if tags else []
    parameters = _parse_parameters(params) if params else None

    if alias:
        alias_manager = AliasManager()
        is_valid, error_msg = alias_manager.validate_alias_name(alias)
        if not is_valid:
            cli_main.console.print(f"[red]Error:[/red] {error_msg}")
            return

    snippet_id = cli_main.storage.add_snippet(
        command=command,
        description=description,
        tags=tag_list,
        parameters=parameters,
        alias=alias,
    )
    cli_main.console.print(f"[green]Added new snippet with ID:[/green] {snippet_id}")

    # If alias was provided, update the aliases file
    if alias:
        alias_manager = AliasManager()
        snippets_with_aliases = cli_main.storage.get_snippets_with_aliases()
        alias_manager.update_aliases_file(snippets_with_aliases)

        cli_main.console.print(f"[green]✓ Created alias:[/green] {alias}")
        cli_main.console.print(
            f"[dim]Run this to activate:[/dim] source {alias_manager.alias_path}"
        )

    # Auto-sync if enabled
    _auto_sync_if_enabled()


@main.command()
@click.argument("query")
def search(query: str) -> None:
    """Search for snippets."""
    table = Table(title=f"Search Results for '{query}'")
    table.add_column("ID", style="blue", no_wrap=True)
    table.add_column("Command", style="cyan", overflow="fold", no_wrap=False)
    table.add_column("Description", style="green", no_wrap=False)
    table.add_column("Tags", style="yellow", no_wrap=False)
    table.add_column("Parameters", style="magenta", no_wrap=False)

    for snippet_id, snippet in cli_main.storage.search_snippets(query):
        table.add_row(
            snippet_id,
            snippet.command,
            snippet.description or "",
            ", ".join(snippet.tags) if snippet.tags else "",
            _format_parameters(snippet),
        )

    cli_main.console.print(table)


@main.command()
@click.argument("snippet_id", required=False)
def delete(snippet_id: str | None = None) -> None:
    """Delete a snippet. If no snippet ID is provided, shows an interactive selection."""
    try:
        selected_snippet_id = None
        selected_snippet = None

        if snippet_id is None:
            # Show interactive snippet selection
            snippets = cli_main.storage.list_snippets()
            if not snippets:
                cli_main.console.print(
                    "[yellow]No snippets found.[/yellow] Add some with 'pypet new'"
                )
                return

            # Display snippets table for selection
            table = Table(title="Available Snippets")
            table.add_column("Index", style="blue", no_wrap=True)
            table.add_column("ID", style="cyan", no_wrap=True)
            table.add_column("Command", style="green", overflow="fold", no_wrap=False)
            table.add_column("Description", style="yellow", no_wrap=False)
            table.add_column("Parameters", style="magenta", no_wrap=False)

            for i, (id_, snippet) in enumerate(snippets, 1):
                table.add_row(
                    str(i),
                    id_,
                    snippet.command,
                    snippet.description or "",
                    _format_parameters(snippet),
                )

            cli_main.console.print(table)

            # Get user selection
            while True:
                try:
                    choice_str = Prompt.ask(
                        "Enter snippet number to delete (or 'q' to quit)"
                    )
                    if choice_str.lower() == "q":
                        return
                    choice = int(choice_str)
                    if 1 <= choice <= len(snippets):
                        selected_snippet_id = snippets[choice - 1][0]
                        selected_snippet = snippets[choice - 1][1]
                        break
                    cli_main.console.print("[red]Invalid selection[/red]")
                except (ValueError, EOFError):
                    cli_main.console.print("[red]Please enter a number[/red]")
                except KeyboardInterrupt:
                    cli_main.console.print("\n[yellow]Operation cancelled[/yellow]")
                    return
        else:
            # Use provided snippet ID
            selected_snippet_id = snippet_id
            selected_snippet = cli_main.storage.get_snippet(snippet_id)
            if not selected_snippet:
                cli_main.console.print(f"[red]Snippet not found:[/red] {snippet_id}")
                return

        # Show confirmation prompt before deleting
        cli_main.console.print("\n[yellow]About to delete snippet:[/yellow]")
        cli_main.console.print(f"  [cyan]ID:[/cyan] {selected_snippet_id}")
        cli_main.console.print(f"  [cyan]Command:[/cyan] {selected_snippet.command}")
        if selected_snippet.description:
            cli_main.console.print(
                f"  [cyan]Description:[/cyan] {selected_snippet.description}"
            )

        if not Confirm.ask(
            "\n[red]Are you sure you want to delete this snippet?[/red]", default=False
        ):
            cli_main.console.print("[yellow]Deletion cancelled[/yellow]")
            return

        # Perform deletion
        if cli_main.storage.delete_snippet(selected_snippet_id):
            cli_main.console.print(
                f"[green]✓ Deleted snippet:[/green] {selected_snippet_id}"
            )

            # Auto-sync if enabled
            _auto_sync_if_enabled()
        else:
            cli_main.console.print(
                f"[red]Failed to delete snippet:[/red] {selected_snippet_id}"
            )

    except KeyboardInterrupt:
        cli_main.console.print("\n[yellow]Operation cancelled[/yellow]")


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
) -> None:
    """Edit an existing snippet or open TOML file directly."""
    # Handle --file option to open TOML directly
    if edit_file:
        editor = os.environ.get("EDITOR", "nano")

        # Basic validation: editor should not contain shell metacharacters
        if any(char in editor for char in [";", "&", "|", ">", "<", "`", "$"]):
            cli_main.console.print(
                f"[red]Error:[/red] Invalid EDITOR value '{editor}'. "
                "EDITOR should be a simple command name or path."
            )
            return

        try:
            subprocess.run([editor, str(cli_main.storage.config_path)], check=False)
            cli_main.console.print(
                f"[green]✓ Opened {cli_main.storage.config_path} in {editor}[/green]"
            )

            # Auto-sync if enabled (user may have made changes)
            _auto_sync_if_enabled()
        except FileNotFoundError:
            cli_main.console.print(
                f"[red]Error:[/red] Editor '{editor}' not found. Set EDITOR environment variable."
            )
        except Exception as e:
            cli_main.console.print(f"[red]Error:[/red] Failed to open editor: {e}")
        return

    # Require snippet_id if not using --file option
    if not snippet_id:
        cli_main.console.print(
            "[red]Error:[/red] Either provide a snippet ID or use --file to edit TOML directly"
        )
        cli_main.console.print("[yellow]Examples:[/yellow]")
        cli_main.console.print("  pypet edit abc123 --command 'new command'")
        cli_main.console.print("  pypet edit --file")
        return

    # Check if snippet exists first
    existing = cli_main.storage.get_snippet(snippet_id)
    if not existing:
        cli_main.console.print(
            f"[red]Error:[/red] Snippet with ID '{snippet_id}' not found"
        )
        return

    # Only split tags if they were provided
    tag_list = [t.strip() for t in tags.split(",")] if tags is not None else None

    # Only parse parameters if they were provided
    parameters = _parse_parameters(params) if params is not None else None

    # Update the snippet
    if cli_main.storage.update_snippet(
        snippet_id,
        command=command,
        description=description,
        tags=tag_list,
        parameters=parameters,
    ):
        # Get the updated version
        updated = cli_main.storage.get_snippet(snippet_id)
        if updated:
            cli_main.console.print(
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

            cli_main.console.print(table)

        # Auto-sync if enabled
        _auto_sync_if_enabled()
    else:
        cli_main.console.print("[red]Failed to update snippet[/red]")
