"""
Commands for Git synchronization
"""

from datetime import datetime

import click
from rich.table import Table

from . import main_module as cli_main
from .main import main


@main.group()
def sync() -> None:
    """Synchronize snippets with Git repositories."""
    pass


@sync.command()
@click.option("--remote", "-r", help="Remote repository URL")
def init(remote: str | None = None) -> None:
    """Initialize Git repository for snippet synchronization."""
    if not cli_main.sync_manager.git_available:
        cli_main.console.print(
            "[red]Git is not available. Please install Git to use sync features.[/red]"
        )
        raise click.ClickException("Git not available")

    if cli_main.sync_manager.is_git_repo:
        cli_main.console.print("[yellow]Git repository already initialized[/yellow]")
        return

    if cli_main.sync_manager.init_git_repo(remote):
        cli_main.console.print("[green]Git sync initialized successfully[/green]")
        if remote:
            cli_main.console.print(f"[blue]Remote origin set to: {remote}[/blue]")
    else:
        raise click.ClickException("Failed to initialize Git repository")


@sync.command()
def status() -> None:
    """Show Git synchronization status."""
    status_info = cli_main.sync_manager.get_status()

    table = Table(title="Git Sync Status")
    table.add_column("Property", style="blue")
    table.add_column("Value", style="cyan")

    for key, value in status_info.items():
        display_key = key.replace("_", " ").title()
        table.add_row(display_key, value)

    cli_main.console.print(table)


@sync.command()
@click.option("--message", "-m", help="Commit message")
def commit(message: str | None = None) -> None:
    """Commit current snippet changes to Git."""
    if cli_main.sync_manager.commit_changes(message):
        cli_main.console.print("[green]Changes committed successfully[/green]")
    else:
        raise click.ClickException("Failed to commit changes")


@sync.command()
def pull() -> None:
    """Pull snippet changes from remote repository."""
    if cli_main.sync_manager.pull_changes():
        cli_main.console.print("[green]Changes pulled successfully[/green]")
    else:
        raise click.ClickException("Failed to pull changes")


@sync.command()
def push() -> None:
    """Push snippet changes to remote repository."""
    if cli_main.sync_manager.push_changes():
        cli_main.console.print("[green]Changes pushed successfully[/green]")
    else:
        raise click.ClickException("Failed to push changes")


@sync.command("sync")
@click.option("--no-commit", is_flag=True, help="Skip auto-commit before sync")
@click.option("--message", "-m", help="Commit message for auto-commit")
def sync_all(no_commit: bool = False, message: str | None = None) -> None:
    """Perform full synchronization: commit, pull, and push."""
    auto_commit = not no_commit
    if cli_main.sync_manager.sync(auto_commit=auto_commit, commit_message=message):
        cli_main.console.print("[green]Full sync completed successfully[/green]")
    else:
        raise click.ClickException("Sync completed with errors")


@sync.command()
def backups() -> None:
    """List available backup files."""
    backup_files = cli_main.sync_manager.list_backups()

    if not backup_files:
        cli_main.console.print("[yellow]No backup files found[/yellow]")
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

    cli_main.console.print(table)


@sync.command()
@click.argument("backup_file")
def restore(backup_file: str) -> None:
    """Restore snippets from a backup file."""
    backup_path = cli_main.sync_manager.config_dir / backup_file

    if cli_main.sync_manager.restore_backup(backup_path):
        cli_main.console.print(
            f"[green]Successfully restored from {backup_file}[/green]"
        )
    else:
        raise click.ClickException(f"Failed to restore from {backup_file}")


@sync.command()
@click.argument("remote_url")
@click.option("--name", "-n", default="origin", help="Remote name (default: origin)")
def remote(remote_url: str, name: str = "origin") -> None:
    """Add or update a Git remote for synchronization."""
    if not cli_main.sync_manager.is_git_repo:
        cli_main.console.print(
            "[red]Not in a Git repository. Use 'pypet sync init' first.[/red]"
        )
        raise click.ClickException("Not in a Git repository")

    if not cli_main.sync_manager.repo:
        raise click.ClickException("Failed to access Git repository")

    try:
        # Check if remote already exists
        if name in [r.name for r in cli_main.sync_manager.repo.remotes]:
            # Update existing remote
            remote_obj = cli_main.sync_manager.repo.remotes[name]
            remote_obj.set_url(remote_url)
            cli_main.console.print(
                f"[green]✓ Updated remote '{name}' to: {remote_url}[/green]"
            )
        else:
            # Add new remote
            cli_main.sync_manager.repo.create_remote(name, remote_url)
            cli_main.console.print(
                f"[green]✓ Added remote '{name}': {remote_url}[/green]"
            )

        # Show current remotes
        cli_main.console.print("\n[blue]Current remotes:[/blue]")
        for r in cli_main.sync_manager.repo.remotes:
            cli_main.console.print(f"  {r.name}: {r.url}")

    except Exception as e:
        cli_main.console.print(f"[red]Failed to configure remote: {e}[/red]")
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
def cleanup(keep: int, dry_run: bool) -> None:
    """Clean up old backup files."""
    backups = cli_main.sync_manager.list_backups()

    if len(backups) <= keep:
        cli_main.console.print(
            f"[green]No cleanup needed. Found {len(backups)} backup files, keeping {keep}.[/green]"
        )
        return

    backups_to_delete = backups[keep:]

    if dry_run:
        cli_main.console.print(
            f"[yellow]Would delete {len(backups_to_delete)} backup files:[/yellow]"
        )
        for backup in backups_to_delete:
            cli_main.console.print(f"  {backup.name}")
        cli_main.console.print(
            "[blue]Run without --dry-run to actually delete them.[/blue]"
        )
    else:
        deleted_count = cli_main.sync_manager.cleanup_old_backups(keep)
        if deleted_count == 0:
            cli_main.console.print("[green]No backups were deleted.[/green]")
