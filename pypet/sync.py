"""
Git synchronization functionality for pypet snippets
"""

from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List
import shutil

try:
    from git import Repo, InvalidGitRepositoryError

    GIT_AVAILABLE = True
except ImportError:
    GIT_AVAILABLE = False

from rich.console import Console

console = Console()


class SyncManager:
    """Manages Git synchronization for pypet snippet files."""

    def __init__(self, config_path: Path):
        """Initialize sync manager with config path."""
        self.config_path = config_path
        self.config_dir = config_path.parent
        self._repo: Optional[Repo] = None

    @property
    def git_available(self) -> bool:
        """Check if Git is available."""
        return GIT_AVAILABLE

    @property
    def repo(self) -> Optional[Repo]:
        """Get Git repository if available."""
        if not self.git_available:
            return None

        if self._repo is None:
            try:
                # Try to find repo starting from config directory
                self._repo = Repo(self.config_dir, search_parent_directories=True)
            except InvalidGitRepositoryError:
                return None
        return self._repo

    @property
    def is_git_repo(self) -> bool:
        """Check if config directory is in a Git repository."""
        return self.repo is not None

    def init_git_repo(self, remote_url: Optional[str] = None) -> bool:
        """Initialize Git repository in config directory."""
        if not self.git_available:
            console.print("[red]Git is not available[/red]")
            return False

        try:
            # Create git repo in config directory
            self._repo = Repo.init(self.config_dir)

            # Add remote if provided
            if remote_url:
                self._repo.create_remote("origin", remote_url)

            # Create initial commit if snippets file exists
            if self.config_path.exists():
                self._repo.index.add([str(self.config_path.name)])
                self._repo.index.commit("Initial pypet snippets")

            console.print(
                f"[green]✓ Git repository initialized in {self.config_dir}[/green]"
            )
            return True

        except Exception as e:
            console.print(f"[red]Failed to initialize Git repository: {e}[/red]")
            return False

    def get_status(self) -> Dict[str, str]:
        """Get sync status information."""
        status = {
            "git_available": str(self.git_available),
            "is_git_repo": str(self.is_git_repo),
            "config_path": str(self.config_path),
            "config_dir": str(self.config_dir),
        }

        if self.is_git_repo and self.repo:
            try:
                status["branch"] = self.repo.active_branch.name
                status["remote"] = (
                    "origin"
                    if "origin" in [r.name for r in self.repo.remotes]
                    else "none"
                )
                status["uncommitted_changes"] = str(bool(self.repo.is_dirty()))
                status["last_commit"] = (
                    self.repo.head.commit.hexsha[:8]
                    if self.repo.head.is_valid()
                    else "none"
                )
            except Exception as e:
                status["error"] = str(e)

        return status

    def create_backup(self) -> Optional[Path]:
        """Create backup of snippets file."""
        if not self.config_path.exists():
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.config_dir / f"snippets_backup_{timestamp}.toml"

        try:
            shutil.copy2(self.config_path, backup_path)
            return backup_path
        except Exception as e:
            console.print(f"[red]Failed to create backup: {e}[/red]")
            return None

    def commit_changes(self, message: Optional[str] = None) -> bool:
        """Commit current changes to Git."""
        if not self.is_git_repo or not self.repo:
            console.print("[red]Not in a Git repository[/red]")
            return False

        try:
            # Add snippets file to index
            if self.config_path.exists():
                self.repo.index.add([str(self.config_path.name)])

            # Check if there are changes to commit
            if not self.repo.index.diff("HEAD"):
                console.print("[yellow]No changes to commit[/yellow]")
                return True

            # Commit changes
            commit_message = (
                message
                or f"Update snippets - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            self.repo.index.commit(commit_message)

            console.print(f"[green]✓ Changes committed: {commit_message}[/green]")
            return True

        except Exception as e:
            console.print(f"[red]Failed to commit changes: {e}[/red]")
            return False

    def pull_changes(self) -> bool:
        """Pull changes from remote repository."""
        if not self.is_git_repo or not self.repo:
            console.print("[red]Not in a Git repository[/red]")
            return False

        # Create backup before pulling
        backup_path = self.create_backup()
        if backup_path:
            console.print(f"[blue]Backup created: {backup_path}[/blue]")

        try:
            # Check if origin remote exists
            if "origin" not in [r.name for r in self.repo.remotes]:
                console.print("[red]No 'origin' remote configured[/red]")
                return False

            # Pull from origin
            origin = self.repo.remotes.origin
            origin.pull()

            console.print("[green]✓ Successfully pulled changes from origin[/green]")
            return True

        except Exception as e:
            console.print(f"[red]Failed to pull changes: {e}[/red]")
            # Restore backup if pull failed
            if backup_path and backup_path.exists():
                shutil.copy2(backup_path, self.config_path)
                console.print("[yellow]Backup restored due to pull failure[/yellow]")
            return False

    def push_changes(self) -> bool:
        """Push changes to remote repository."""
        if not self.is_git_repo or not self.repo:
            console.print("[red]Not in a Git repository[/red]")
            return False

        try:
            # Check if origin remote exists
            if "origin" not in [r.name for r in self.repo.remotes]:
                console.print("[red]No 'origin' remote configured[/red]")
                return False

            # Push to origin
            origin = self.repo.remotes.origin
            origin.push()

            console.print("[green]✓ Successfully pushed changes to origin[/green]")
            return True

        except Exception as e:
            console.print(f"[red]Failed to push changes: {e}[/red]")
            return False

    def sync(
        self, auto_commit: bool = True, commit_message: Optional[str] = None
    ) -> bool:
        """Perform full sync: commit, pull, push."""
        if not self.is_git_repo:
            console.print(
                "[red]Not in a Git repository. Use 'pypet sync init' to initialize.[/red]"
            )
            return False

        # Check if remote is configured before attempting sync
        if not self.repo or "origin" not in [r.name for r in self.repo.remotes]:
            console.print("[red]No 'origin' remote configured.[/red]")
            console.print("[yellow]To fix this, run one of:[/yellow]")
            console.print("  [cyan]git -C ~/.config/pypet remote add origin <your-repo-url>[/cyan]")
            console.print("  [cyan]pypet sync init --remote <your-repo-url>[/cyan] (reinitialize)")
            console.print("[blue]Example:[/blue] git -C ~/.config/pypet remote add origin https://github.com/username/pypet-snippets.git")
            return False

        success = True

        # Auto-commit if requested and there are changes
        if auto_commit and self.repo and self.repo.is_dirty():
            if not self.commit_changes(commit_message):
                success = False

        # Pull changes
        if not self.pull_changes():
            success = False

        # Push changes
        if not self.push_changes():
            success = False

        if success:
            console.print("[green]✓ Sync completed successfully[/green]")
        else:
            console.print("[red]Sync completed with errors[/red]")

        return success

    def list_backups(self) -> List[Path]:
        """List available backup files."""
        backup_pattern = "snippets_backup_*.toml"
        return sorted(self.config_dir.glob(backup_pattern), reverse=True)

    def restore_backup(self, backup_path: Path) -> bool:
        """Restore from a backup file."""
        if not backup_path.exists():
            console.print(f"[red]Backup file not found: {backup_path}[/red]")
            return False

        try:
            shutil.copy2(backup_path, self.config_path)
            console.print(f"[green]✓ Restored from backup: {backup_path}[/green]")
            return True
        except Exception as e:
            console.print(f"[red]Failed to restore backup: {e}[/red]")
            return False
