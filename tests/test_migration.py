"""
Tests for the migration utility.
"""

from pypet.migration import SnippetMigrator
from pypet.models import Snippet
from pypet.storage import Storage


class TestSnippetMigrator:
    """Tests for SnippetMigrator."""

    def test_migrator_detects_old_syntax_snippets(self, tmp_path):
        """Test that migrator can find snippets with old syntax."""
        storage = Storage(config_path=tmp_path / "snippets.toml")

        storage.add_snippet(command="docker run {image}", description="Old syntax")
        storage.add_snippet(
            command="docker run {{container}}", description="New syntax"
        )
        storage.add_snippet(command="ls -la", description="No parameters")

        migrator = SnippetMigrator(storage)
        snippets_to_migrate = migrator.get_snippets_needing_migration()

        assert len(snippets_to_migrate) == 1
        assert "{image}" in snippets_to_migrate[0][1].command

    def test_migrator_migrates_single_snippet(self):
        """Test migrating a single snippet."""
        snippet = Snippet(command="docker run {image}", description="Test")
        migrator = SnippetMigrator()

        migrated, notes = migrator.migrate_snippet(snippet)

        assert "{{image}}" in migrated.command
        assert len(notes) > 0

    def test_migrator_preserves_new_syntax(self):
        """Test that snippets with new syntax are not modified."""
        snippet = Snippet(command="docker run {{image}}", description="Test")
        migrator = SnippetMigrator()

        migrated, notes = migrator.migrate_snippet(snippet)

        assert migrated.command == snippet.command
        assert len(notes) == 0

    def test_migrator_backup_creation(self, tmp_path):
        """Test that backup is created before migration."""
        storage = Storage(config_path=tmp_path / "snippets.toml")
        storage.add_snippet(command="docker run {image}")

        migrator = SnippetMigrator(storage)
        backup_path = migrator.backup_before_migration()

        assert backup_path is not None
        assert backup_path.exists()

    def test_migrator_all_snippets_dry_run(self, tmp_path):
        """Test dry-run migration."""
        storage = Storage(config_path=tmp_path / "snippets.toml")
        storage.add_snippet(command="docker run {image}")
        storage.add_snippet(command="docker run {container}")

        migrator = SnippetMigrator(storage)
        result = migrator.migrate_all_snippets(interactive=False, dry_run=True)

        assert result["status"] == "success"
        assert result["migrated_count"] == 0
        assert result["dry_run"] is True
        assert result["total_snippets"] == 2
