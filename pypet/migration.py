"""
Migration utilities for upgrading snippets from old {param} syntax to new {{param}} syntax.
"""

import shutil
import sys
from datetime import datetime
from pathlib import Path

from .models import Snippet
from .parameters import ParameterDetector, ParameterMigrator
from .storage import Storage


class SnippetMigrator:
    """Utility for migrating snippets to the new parameter syntax."""

    def __init__(self, storage: Storage | None = None):
        """Initialize the migrator with a storage instance."""
        self.storage = storage or Storage()

    def get_snippets_needing_migration(self) -> list[tuple[str, Snippet]]:
        """Get all snippets that use the old {param} syntax."""
        snippets_to_migrate = []

        for snippet_id, snippet in self.storage.list_snippets():
            if ParameterDetector.has_old_syntax(snippet.command):
                snippets_to_migrate.append((snippet_id, snippet))

        return snippets_to_migrate

    def migrate_snippet(self, snippet: Snippet) -> tuple[Snippet, list[str]]:
        """
        Migrate a single snippet from old syntax to new syntax.

        Returns:
            Tuple of (migrated_snippet, migration_notes)
        """
        if not ParameterDetector.has_old_syntax(snippet.command):
            return snippet, []

        migrated_command, notes = ParameterMigrator.migrate_command(snippet.command)

        migrated_snippet = Snippet(
            command=migrated_command,
            description=snippet.description,
            tags=snippet.tags,
            parameters=snippet.parameters,
            alias=snippet.alias,
            created_at=snippet.created_at,
            updated_at=snippet.updated_at,
        )

        return migrated_snippet, notes

    def migrate_all_snippets(
        self, interactive: bool = True, dry_run: bool = False
    ) -> dict:
        """
        Migrate all snippets using old syntax to new syntax.

        Args:
            interactive: If True, show progress and prompt for confirmation
            dry_run: If True, don't actually save changes

        Returns:
            Dictionary with migration results
        """
        snippets_to_migrate = self.get_snippets_needing_migration()

        if not snippets_to_migrate:
            return {
                "status": "success",
                "message": "All snippets are already using the new {{param}} syntax",
                "migrated_count": 0,
                "total_snippets": len(self.storage.list_snippets()),
            }

        if interactive:
            print(f"\nFound {len(snippets_to_migrate)} snippet(s) using old syntax:")
            print()
            for snippet_id, snippet in snippets_to_migrate:
                print(f"  ID: {snippet_id[:8]}")
                print(f"  Command: {snippet.command}")
                print()

            response = (
                input("Migrate these snippets to new syntax? (yes/no): ")
                .strip()
                .lower()
            )
            if response not in ("yes", "y"):
                return {
                    "status": "cancelled",
                    "message": "Migration cancelled",
                    "migrated_count": 0,
                }

        migrated_count = 0
        errors = []

        for snippet_id, snippet in snippets_to_migrate:
            try:
                migrated_snippet, notes = self.migrate_snippet(snippet)

                if not dry_run:
                    self.storage.update_snippet(
                        snippet_id,
                        command=migrated_snippet.command,
                        description=migrated_snippet.description,
                        tags=migrated_snippet.tags,
                        parameters=migrated_snippet.parameters,
                        alias=migrated_snippet.alias,
                    )
                    migrated_count += 1

                    if interactive:
                        print(f"✓ Migrated {snippet_id[:8]}")
                else:
                    # dry run: do not increment count, but optionally show what would happen
                    if interactive:
                        print(f"✓ (dry-run) would migrate {snippet_id[:8]}")

            except Exception as e:
                error_msg = f"Failed to migrate {snippet_id}: {e!s}"
                errors.append(error_msg)
                if interactive:
                    print(f"✗ {error_msg}")

        return {
            "status": "success",
            "message": (
                f"Successfully migrated {migrated_count} snippet(s)"
                if not dry_run
                else "Dry run complete, no snippets were modified"
            ),
            "migrated_count": migrated_count,
            "total_snippets": len(self.storage.list_snippets()),
            "errors": errors,
            "dry_run": dry_run,
        }

    def backup_before_migration(self) -> Path | None:
        """
        Create a backup of the current snippets before migration.

        Returns:
            Path to the backup file, or None if backup failed
        """
        try:
            backup_dir = self.storage.config_path.parent / "backups"
            backup_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = backup_dir / f"snippets_backup_{timestamp}.toml"

            shutil.copy2(self.storage.config_path, backup_path)
            return backup_path

        except Exception as e:
            print(f"Warning: Failed to create backup: {e}", file=sys.stderr)
            return None
