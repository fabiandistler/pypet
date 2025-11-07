"""
Commands for managing snippets (new, list, search, delete, edit)
"""

import os
import subprocess

import click
from rich.table import Table

from . import main_module as cli_main
from .main import _format_parameters, _parse_parameters, main


@main.command(name="list")
def list_snippets() -> None:
    """List all snippets."""
    table = Table(title="Snippets")
    table.add_column("ID", style="blue")
    table.add_column("Command", style="cyan")
    table.add_column("Description", style="green")
    table.add_column("Tags", style="yellow")
    table.add_column("Parameters", style="magenta")

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
def new(
    command: str,
    description: str | None = None,
    tags: str | None = None,
    params: str | None = None,
) -> None:
    """Create a new snippet."""
    tag_list = [t.strip() for t in tags.split(",")] if tags else []
    parameters = _parse_parameters(params) if params else None

    snippet_id = cli_main.storage.add_snippet(
        command=command,
        description=description,
        tags=tag_list,
        parameters=parameters,
    )
    cli_main.console.print(f"[green]Added new snippet with ID:[/green] {snippet_id}")


@main.command()
@click.argument("query")
def search(query: str) -> None:
    """Search for snippets."""
    table = Table(title=f"Search Results for '{query}'")
    table.add_column("ID", style="blue")
    table.add_column("Command", style="cyan")
    table.add_column("Description", style="green")
    table.add_column("Tags", style="yellow")
    table.add_column("Parameters", style="magenta")

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
@click.argument("snippet_id")
def delete(snippet_id: str) -> None:
    """Delete a snippet."""
    if cli_main.storage.delete_snippet(snippet_id):
        cli_main.console.print(f"[green]Deleted snippet:[/green] {snippet_id}")
    else:
        cli_main.console.print(f"[red]Snippet not found:[/red] {snippet_id}")


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
    else:
        cli_main.console.print("[red]Failed to update snippet[/red]")
