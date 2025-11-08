"""
Commands for managing aliases
"""

import click
import pyperclip
from rich.table import Table

from ..alias_manager import AliasManager
from . import main_module as cli_main
from .main import main


alias_manager = AliasManager()


@main.group()
def alias() -> None:
    """Manage shell aliases for snippets."""
    pass


@alias.command(name="add")
@click.argument("snippet_id")
@click.argument("alias_name")
def add_alias(snippet_id: str, alias_name: str) -> None:
    """Add an alias to an existing snippet."""
    # Check if snippet exists
    snippet = cli_main.storage.get_snippet(snippet_id)
    if not snippet:
        cli_main.console.print(
            f"[red]Error:[/red] Snippet with ID '{snippet_id}' not found"
        )
        return

    is_valid, error_msg = alias_manager.validate_alias_name(alias_name)
    if not is_valid:
        cli_main.console.print(f"[red]Error:[/red] {error_msg}")
        return

    # Check if alias already exists on another snippet
    for sid, s in cli_main.storage.list_snippets():
        if s.alias == alias_name and sid != snippet_id:
            cli_main.console.print(
                f"[yellow]Warning:[/yellow] Alias '{alias_name}' is already used by snippet {sid}"
            )
            if not click.confirm("Do you want to continue and override?"):
                return

    # Update the snippet with the alias
    if cli_main.storage.update_snippet(snippet_id, alias=alias_name):
        # Regenerate aliases file
        snippets_with_aliases = cli_main.storage.get_snippets_with_aliases()
        alias_manager.update_aliases_file(snippets_with_aliases)

        cli_main.console.print(
            f"[green]✓ Added alias '{alias_name}' to snippet {snippet_id}[/green]"
        )
        cli_main.console.print(f"\n[cyan]Command:[/cyan] {snippet.command}")

        # Show what was generated
        all_params = snippet.get_all_parameters()
        if all_params:
            cli_main.console.print(
                "\n[yellow]Note:[/yellow] This snippet has parameters, so a shell function was created."
            )
            cli_main.console.print(
                f"Use: [cyan]{alias_name}[/cyan] to execute with parameter prompts"
            )
        else:
            cli_main.console.print(
                "\n[yellow]Note:[/yellow] Alias created successfully."
            )
            cli_main.console.print(
                f"Use: [cyan]{alias_name}[/cyan] to run this command"
            )

        # Show source instruction
        cli_main.console.print(
            f"\n[dim]Run this to activate in current shell:[/dim] source {alias_manager.alias_path}"
        )
    else:
        cli_main.console.print("[red]Failed to add alias[/red]")


@alias.command(name="list")
def list_aliases() -> None:
    """List all snippets with aliases."""
    snippets_with_aliases = cli_main.storage.get_snippets_with_aliases()

    if not snippets_with_aliases:
        cli_main.console.print("[yellow]No aliases defined yet.[/yellow]")
        cli_main.console.print("\nTo add an alias to a snippet, use:")
        cli_main.console.print("  pypet alias add <snippet-id> <alias-name>")
        return

    table = Table(title="Snippets with Aliases")
    table.add_column("Alias", style="green bold")
    table.add_column("ID", style="blue")
    table.add_column("Command", style="cyan")
    table.add_column("Description", style="yellow")
    table.add_column("Has Params", style="magenta")

    for snippet_id, snippet in snippets_with_aliases:
        has_params = "Yes" if snippet.get_all_parameters() else "No"
        table.add_row(
            snippet.alias or "",
            snippet_id,
            snippet.command,
            snippet.description or "",
            has_params,
        )

    cli_main.console.print(table)
    cli_main.console.print(
        f"\n[dim]Aliases are stored in:[/dim] {alias_manager.alias_path}"
    )
    cli_main.console.print(
        f"[dim]Run this to activate:[/dim] source {alias_manager.alias_path}"
    )


@alias.command(name="remove")
@click.argument("snippet_id")
def remove_alias(snippet_id: str) -> None:
    """Remove an alias from a snippet."""
    snippet = cli_main.storage.get_snippet(snippet_id)
    if not snippet:
        cli_main.console.print(
            f"[red]Error:[/red] Snippet with ID '{snippet_id}' not found"
        )
        return

    if not snippet.alias:
        cli_main.console.print(
            f"[yellow]Warning:[/yellow] Snippet {snippet_id} has no alias"
        )
        return

    old_alias = snippet.alias

    if cli_main.storage.update_snippet(snippet_id, alias=""):
        snippets_with_aliases = cli_main.storage.get_snippets_with_aliases()
        alias_manager.update_aliases_file(snippets_with_aliases)

        cli_main.console.print(
            f"[green]✓ Removed alias '{old_alias}' from snippet {snippet_id}[/green]"
        )
        cli_main.console.print(
            f"\n[dim]Run this to reload:[/dim] source {alias_manager.alias_path}"
        )
    else:
        cli_main.console.print("[red]Failed to remove alias[/red]")


@alias.command(name="update")
def update_aliases() -> None:
    """Regenerate the aliases.sh file from current snippets."""
    snippets_with_aliases = cli_main.storage.get_snippets_with_aliases()
    alias_manager.update_aliases_file(snippets_with_aliases)

    cli_main.console.print(
        f"[green]✓ Updated aliases file:[/green] {alias_manager.alias_path}"
    )
    cli_main.console.print(
        f"\nFound {len(snippets_with_aliases)} snippet(s) with aliases"
    )
    cli_main.console.print(
        f"\n[dim]Run this to reload:[/dim] source {alias_manager.alias_path}"
    )


@alias.command(name="setup")
@click.option("--copy", "-c", is_flag=True, help="Copy source command to clipboard")
def setup_aliases(copy: bool) -> None:
    """Show instructions for setting up aliases in your shell."""
    instructions = alias_manager.get_setup_instructions()

    for line in instructions:
        if line.startswith("  source"):
            cli_main.console.print(f"[green]{line}[/green]")
        else:
            cli_main.console.print(line)

    if copy:
        source_cmd = alias_manager.get_source_instruction()
        try:
            pyperclip.copy(source_cmd)
            cli_main.console.print(
                f"\n[green]✓ Copied to clipboard:[/green] {source_cmd}"
            )
        except Exception:
            cli_main.console.print(
                "\n[yellow]Note:[/yellow] Could not copy to clipboard (pyperclip not available)"
            )


@alias.command(name="show")
@click.argument("snippet_id")
def show_alias(snippet_id: str) -> None:
    """Show the alias definition for a snippet."""
    snippet = cli_main.storage.get_snippet(snippet_id)
    if not snippet:
        cli_main.console.print(
            f"[red]Error:[/red] Snippet with ID '{snippet_id}' not found"
        )
        return

    if not snippet.alias:
        cli_main.console.print(
            f"[yellow]Warning:[/yellow] Snippet {snippet_id} has no alias"
        )
        cli_main.console.print("\nTo add an alias, use:")
        cli_main.console.print(f"  pypet alias add {snippet_id} <alias-name>")
        return

    # Generate the alias definition
    alias_def = alias_manager._generate_alias_definition(
        snippet.alias, snippet_id, snippet
    )

    cli_main.console.print(
        f"[green]Alias definition for snippet {snippet_id}:[/green]\n"
    )
    cli_main.console.print(f"[cyan]{alias_def}[/cyan]")

    # Show the command
    cli_main.console.print(f"\n[yellow]Command:[/yellow] {snippet.command}")
    if snippet.description:
        cli_main.console.print(f"[yellow]Description:[/yellow] {snippet.description}")
