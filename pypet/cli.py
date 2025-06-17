"""
Command-line interface for pypet
"""

from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from .storage import Storage

console = Console()
storage = Storage()


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

    for snippet_id, snippet in storage.list_snippets():
        table.add_row(
            snippet_id,
            snippet.command,
            snippet.description or "",
            ", ".join(snippet.tags) if snippet.tags else "",
        )

    console.print(table)


@main.command()
@click.argument("command")
@click.option("--description", "-d", help="Description of the snippet")
@click.option("--tags", "-t", help="Tags for the snippet (comma-separated)")
def new(command: str, description: Optional[str] = None, tags: Optional[str] = None):
    """Create a new snippet."""
    tag_list = [t.strip() for t in tags.split(",")] if tags else []
    snippet_id = storage.add_snippet(command, description, tag_list)
    console.print(f"[green]Added new snippet with ID:[/green] {snippet_id}")


@main.command()
@click.argument("query")
def search(query: str):
    """Search for snippets."""
    table = Table(title=f"Search Results for '{query}'")
    table.add_column("ID", style="blue")
    table.add_column("Command", style="cyan")
    table.add_column("Description", style="green")
    table.add_column("Tags", style="yellow")

    for snippet_id, snippet in storage.search_snippets(query):
        table.add_row(
            snippet_id,
            snippet.command,
            snippet.description or "",
            ", ".join(snippet.tags) if snippet.tags else "",
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
@click.argument("snippet_id")
@click.option("--command", "-c", help="New command")
@click.option("--description", "-d", help="New description")
@click.option("--tags", "-t", help="New tags (comma-separated)")
def edit(
    snippet_id: str,
    command: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[str] = None,
):
    """Edit an existing snippet."""
    # Check if snippet exists first
    existing = storage.get_snippet(snippet_id)
    if not existing:
        console.print(f"[red]Error:[/red] Snippet with ID '{snippet_id}' not found")
        return

    # Only split tags if they were provided
    tag_list = [t.strip() for t in tags.split(",")] if tags is not None else None

    # Update the snippet
    if storage.update_snippet(snippet_id, command, description, tag_list):
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

            console.print(table)
    else:
        console.print(f"[red]Failed to update snippet[/red]")


@main.command()
@click.argument("snippet_id", required=False)
@click.option(
    "--print-only", "-p", is_flag=True, help="Only print the command without executing"
)
@click.option("--edit", "-e", is_flag=True, help="Edit command before execution")
def exec(
    snippet_id: Optional[str] = None, print_only: bool = False, edit: bool = False
):
    """Execute a saved snippet. If no snippet ID is provided, shows an interactive selection."""
    try:
        if snippet_id is None:
            # Show interactive snippet selection
            snippets = storage.list_snippets()
            if not snippets:
                console.print(
                    "[yellow]No snippets found.[/yellow] Add some with 'pypet new'"
                )
                return

            # Create selection table
            table = Table(title="Select a Snippet", show_lines=True)
            table.add_column("#", style="blue")
            table.add_column("ID", style="dim")
            table.add_column("Command", style="cyan")
            table.add_column("Description", style="green")
            table.add_column("Tags", style="yellow")

            # Add snippets to table
            for idx, (sid, snip) in enumerate(snippets, 1):
                table.add_row(
                    str(idx),
                    sid,
                    snip.command,
                    snip.description or "",
                    ", ".join(snip.tags) if snip.tags else "",
                )

            console.print(table)
            console.print()

            while True:
                console.print("Enter number to execute (or 'q' to quit): ", end="")
                choice = input().strip().lower()

                if choice == "q":
                    return

                try:
                    idx = int(choice)
                    if 1 <= idx <= len(snippets):
                        snippet_id = snippets[idx - 1][0]
                        break
                    else:
                        console.print("[red]Invalid number. Please try again.[/red]")
                except ValueError:
                    console.print("[red]Please enter a valid number.[/red]")

        snippet = storage.get_snippet(snippet_id)
        if not snippet:
            console.print(f"[red]Error:[/red] Snippet with ID '{snippet_id}' not found")
            return

        if print_only:
            console.print(snippet.command)
            return

        from rich.box import ROUNDED

        # Show snippet information
        table = Table(title="Snippet Details", show_header=False, box=ROUNDED)
        table.add_column("Field", style="blue")
        table.add_column("Value", style="cyan")
        table.add_row("Command", snippet.command)
        if snippet.description:
            table.add_row("Description", snippet.description)
        if snippet.tags:
            table.add_row("Tags", ", ".join(snippet.tags))
        console.print(table)
        console.print()

        command_to_run = snippet.command

        if edit:
            # Show edit instructions
            console.print(
                "[yellow]Edit mode:[/yellow] You can modify the command before execution."
            )
            console.print("[dim]Press Enter to keep the original command[/dim]")
            console.print("[cyan]Original:[/cyan] " + command_to_run)
            console.print("[green]Modified:[/green] ", end="")

            # Get user input
            modified = input()
            if modified.strip():
                command_to_run = modified
                console.print()
                console.print("[yellow]Using modified command:[/yellow]")
                console.print(f"[cyan]{command_to_run}[/cyan]")

        # Show execution confirmation
        console.print("\nExecute this command? [Y/n/e] ", end="")
        console.print("[dim](Y = execute, n = cancel, e = edit)[/dim]")
        while True:
            response = input().strip().lower()

            if response in ["", "y", "yes"]:
                break
            elif response in ["n", "no"]:
                console.print("[yellow]Execution cancelled[/yellow]")
                return
            elif response == "e":
                console.print("[cyan]Original:[/cyan] " + command_to_run)
                console.print("[green]Modified:[/green] ", end="")
                modified = input()
                if modified.strip():
                    command_to_run = modified
                console.print()
                console.print("[yellow]Using modified command:[/yellow]")
                console.print(f"[cyan]{command_to_run}[/cyan]")
                console.print("\nExecute this command? [Y/n/e] ", end="")
                console.print("[dim](Y = execute, n = cancel, e = edit)[/dim]")
                continue
            else:
                console.print(
                    "[red]Invalid input.[/red] Please enter 'y', 'n', or 'e': ", end=""
                )

        import subprocess
        import os

        try:
            # Use the user's shell from environment or default to bash
            shell = os.environ.get("SHELL", "/bin/bash")
            print()  # Add a newline for better spacing
            subprocess.run([shell, "-c", command_to_run], check=True)
            print()  # Add a newline for better spacing
            console.print("[green]Command executed successfully[/green]")
        except subprocess.CalledProcessError as e:
            console.print(f"[red]Error executing command:[/red] {e}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")


if __name__ == "__main__":
    main()
