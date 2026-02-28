"""
Commands for migration from old parameter syntax to new syntax
"""

import click

from ..migration import SnippetMigrator
from . import main_module as cli_main
from .main import main


@main.command()
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be migrated without making changes",
)
@click.option(
    "--interactive/--non-interactive",
    default=True,
    help="Ask for confirmation before migrating",
)
def migrate(dry_run: bool = False, interactive: bool = True) -> None:
    """Migrate snippets from old {param} syntax to new {{param}} syntax.

    This command helps you upgrade your existing snippets to use the new parameter
    syntax introduced in pypet v0.6.0. The new {{param}} syntax avoids conflicts
    with shell brace expansion.

    Use --dry-run to preview changes without modifying your snippets.
    """
    cli_main.console.print("\n[bold]pypet Parameter Syntax Migration[/bold]")
    cli_main.console.print("[dim]Upgrading snippets to new {{param}} syntax[/dim]\n")

    migrator = SnippetMigrator(cli_main.storage)

    if dry_run:
        cli_main.console.print(
            "[yellow]DRY RUN MODE - No changes will be made[/yellow]\n"
        )

    snippets_to_migrate = migrator.get_snippets_needing_migration()

    if not snippets_to_migrate:
        cli_main.console.print(
            "[green]✓ All snippets are already using the new syntax![/green]"
        )
        return

    cli_main.console.print(
        f"[cyan]Found {len(snippets_to_migrate)} snippet(s) using old syntax:[/cyan]\n"
    )

    for snippet_id, snippet in snippets_to_migrate:
        snippet_short_id = snippet_id[:8]
        cli_main.console.print(f"  [blue]{snippet_short_id}[/blue]")
        cli_main.console.print(f"    Command: {snippet.command}")
        if snippet.description:
            cli_main.console.print(f"    Description: {snippet.description}")
        cli_main.console.print()

    if not interactive:
        cli_main.console.print(
            "[red]Not running in interactive mode. Use --interactive to confirm.[/red]"
        )
        return

    if dry_run:
        cli_main.console.print("[cyan]These snippets would be migrated:[/cyan]\n")
        for snippet_id, snippet in snippets_to_migrate:
            migrated, notes = migrator.migrate_snippet(snippet)
            cli_main.console.print(f"  {snippet_id[:8]}: {snippet.command}")
            cli_main.console.print(f"  → {migrated.command}\n")
    else:
        confirm = click.confirm(
            f"Migrate these {len(snippets_to_migrate)} snippet(s)?", default=True
        )
        if not confirm:
            cli_main.console.print("[yellow]Migration cancelled[/yellow]")
            return

        backup_path = migrator.backup_before_migration()
        if backup_path:
            cli_main.console.print(f"[green]✓ Created backup:[/green] {backup_path}")

        result = migrator.migrate_all_snippets(interactive=False, dry_run=False)

        if result["status"] == "success":
            cli_main.console.print(
                f"\n[green]✓ Successfully migrated {result['migrated_count']} snippet(s)[/green]"
            )

            if result.get("errors"):
                cli_main.console.print("\n[yellow]Warnings:[/yellow]")
                for error in result["errors"]:
                    cli_main.console.print(f"  [yellow]• {error}[/yellow]")
        else:
            cli_main.console.print(
                f"\n[red]✗ Migration failed: {result.get('message')}"
            )
