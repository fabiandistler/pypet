"""
Integration tests for the complete parameter system
"""

import pytest

from pypet.migration import SnippetMigrator
from pypet.parameters import (
    ParameterDetector,
    ParameterSubstitutor,
)
from pypet.storage import Storage


class TestParameterSystemIntegration:
    """Integration tests for the complete parameter system."""

    def test_end_to_end_snippet_with_new_syntax(self, tmp_path):
        """Test creating and executing a snippet with new {{param}} syntax."""
        storage = Storage(config_path=tmp_path / "snippets.toml")

        command = "docker run -p {{port=8080}} {{image}}"
        snippet_id = storage.add_snippet(
            command=command,
            description="Docker container with new syntax",
        )

        retrieved = storage.get_snippet(snippet_id)
        assert retrieved is not None
        assert "{{port" in retrieved.command

        params = retrieved.get_all_parameters()
        assert "port" in params
        assert "image" in params
        assert params["port"].default == "8080"

        result = retrieved.apply_parameters({"image": "ubuntu", "port": "3000"})
        assert result == "docker run -p 3000 ubuntu"

    def test_end_to_end_migration_flow(self, tmp_path):
        """Test the complete migration flow from old to new syntax."""
        storage = Storage(config_path=tmp_path / "snippets.toml")

        old_id = storage.add_snippet(
            command="ssh {user}@{host} -p {port=22}",
            description="SSH with old syntax",
        )

        migrator = SnippetMigrator(storage)
        snippets = migrator.get_snippets_needing_migration()
        assert len(snippets) == 1

        backup_path = migrator.backup_before_migration()
        assert backup_path.exists()

        result = migrator.migrate_all_snippets(interactive=False, dry_run=False)
        assert result["migrated_count"] == 1

        migrated_snippet = storage.get_snippet(old_id)
        assert "{{user}}" in migrated_snippet.command
        assert "{{host}}" in migrated_snippet.command
        assert "{{port=22}}" in migrated_snippet.command

    def test_mixed_old_and_new_syntax_coexistence(self, tmp_path):
        """Test that old and new syntax can coexist during transition."""
        storage = Storage(config_path=tmp_path / "snippets.toml")

        old_id = storage.add_snippet(
            command="echo {old_param}",
            description="Old syntax",
        )
        new_id = storage.add_snippet(
            command="echo {{new_param}}",
            description="New syntax",
        )

        old_snippet = storage.get_snippet(old_id)
        new_snippet = storage.get_snippet(new_id)

        assert old_snippet.apply_parameters({"old_param": "value"}) == "echo value"
        assert new_snippet.apply_parameters({"new_param": "value"}) == "echo value"

    def test_parameter_validation_catches_errors(self):
        """Test that parameter validation prevents invalid parameters."""
        valid_command = "docker run {{my_image}}"
        params = ParameterDetector.detect_parameters_new_syntax(valid_command)
        assert len(params) == 1

        invalid_command = "docker run {{123invalid}}"
        with pytest.raises(ValueError):
            ParameterDetector.detect_parameters_new_syntax(invalid_command)

        duplicate_command = "docker run {{image}} {{image}}"
        with pytest.raises(ValueError, match="Duplicate"):
            ParameterDetector.detect_parameters_new_syntax(duplicate_command)

    def test_parameter_substitution_with_complex_values(self):
        """Test parameter substitution with complex values."""
        command = "curl -H 'Authorization: Bearer {{token}}' {{url}}"
        params = {
            "token": "abc123xyz789",
            "url": "https://api.example.com/endpoint",
        }
        result = ParameterSubstitutor.substitute_parameters(command, params)

        assert "abc123xyz789" in result
        assert "https://api.example.com/endpoint" in result
        assert "{{" not in result

    def test_backward_compatibility_with_old_syntax(self, tmp_path):
        """Test that old syntax still works for backward compatibility."""
        storage = Storage(config_path=tmp_path / "snippets.toml")

        snippet_id = storage.add_snippet(
            command="ssh {user=admin}@{host} -p {port=22}",
            description="Legacy SSH command",
        )

        snippet = storage.get_snippet(snippet_id)
        params = snippet.get_all_parameters()

        assert params["user"].default == "admin"
        assert params["host"].default is None
        assert params["port"].default == "22"

        result = snippet.apply_parameters({"host": "example.com"})
        assert result == "ssh admin@example.com -p 22"

    def test_detector_identifies_old_vs_new_syntax(self):
        """Test detection of old vs new syntax."""
        assert ParameterDetector.has_old_syntax("command {param}")
        assert not ParameterDetector.has_old_syntax("command {{param}}")
        assert not ParameterDetector.has_old_syntax("command $(param)")

        assert ParameterDetector.has_new_syntax("command {{param}}")
        assert not ParameterDetector.has_new_syntax("command {param}")

    def test_migration_preserves_snippet_metadata(self, tmp_path):
        """Test that migration preserves all snippet metadata."""
        storage = Storage(config_path=tmp_path / "snippets.toml")

        snippet_id = storage.add_snippet(
            command="docker {image}",
            description="Docker command",
            tags=["docker", "container"],
            alias="d",
        )

        original = storage.get_snippet(snippet_id)
        original_desc = original.description
        original_tags = original.tags
        original_alias = original.alias

        migrator = SnippetMigrator(storage)
        migrator.migrate_all_snippets(interactive=False, dry_run=False)

        migrated = storage.get_snippet(snippet_id)

        assert migrated.description == original_desc
        assert migrated.tags == original_tags
        assert migrated.alias == original_alias
        assert "{{image}}" in migrated.command
