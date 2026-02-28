"""
Tests for the parameter handling system.
"""

import pytest

from pypet.parameters import (
    ParameterDetector,
    ParameterMetadata,
    ParameterMigrator,
    ParameterSubstitutor,
    ParameterValidator,
)


class TestParameterValidator:
    """Tests for ParameterValidator."""

    def test_valid_parameter_name(self):
        """Test that valid parameter names are accepted."""
        valid_names = ["param", "param_name", "param-name", "_param", "param123"]
        for name in valid_names:
            is_valid, error = ParameterValidator.validate_parameter_name(name)
            assert is_valid, f"Expected '{name}' to be valid, but got error: {error}"

    def test_invalid_parameter_name_empty(self):
        """Test that empty parameter names are rejected."""
        is_valid, error = ParameterValidator.validate_parameter_name("")
        assert not is_valid

    def test_invalid_parameter_name_starts_with_digit(self):
        """Test that parameter names starting with digits are rejected."""
        is_valid, error = ParameterValidator.validate_parameter_name("123param")
        assert not is_valid

    def test_invalid_parameter_name_with_spaces(self):
        """Test that parameter names with spaces are rejected."""
        is_valid, error = ParameterValidator.validate_parameter_name("param name")
        assert not is_valid

    def test_validate_parameters_dict(self):
        """Test validation of a parameter dictionary."""
        params = {
            "param1": ParameterMetadata("param1"),
            "param2": ParameterMetadata("param2", default="default"),
        }
        is_valid, errors = ParameterValidator.validate_parameters(params)
        assert is_valid
        assert len(errors) == 0


class TestParameterMetadata:
    """Tests for ParameterMetadata."""

    def test_parameter_metadata_creation(self):
        """Test creating parameter metadata."""
        param = ParameterMetadata(
            "test_param", default="default", description="A test param"
        )
        assert param.name == "test_param"
        assert param.default == "default"
        assert param.description == "A test param"

    def test_parameter_metadata_to_dict(self):
        """Test converting parameter metadata to dictionary."""
        param = ParameterMetadata("test", default="val", description="desc")
        result = param.to_dict()
        assert result["name"] == "test"
        assert result["default"] == "val"
        assert result["description"] == "desc"

    def test_parameter_metadata_from_dict(self):
        """Test creating parameter metadata from dictionary."""
        data = {"name": "test", "default": "val", "description": "desc"}
        param = ParameterMetadata.from_dict(data)
        assert param.name == "test"
        assert param.default == "val"
        assert param.description == "desc"


class TestParameterDetector:
    """Tests for ParameterDetector."""

    def test_detect_single_parameter_new_syntax(self):
        """Test detecting a single parameter in new syntax."""
        command = "docker run {{image}}"
        params = ParameterDetector.detect_parameters_new_syntax(command)
        assert "image" in params
        assert params["image"].default is None

    def test_detect_multiple_parameters_new_syntax(self):
        """Test detecting multiple parameters in new syntax."""
        command = "docker run -p {{port}}:8080 {{image}}"
        params = ParameterDetector.detect_parameters_new_syntax(command)
        assert "port" in params
        assert "image" in params

    def test_detect_parameters_with_defaults_new_syntax(self):
        """Test detecting parameters with default values in new syntax."""
        command = "docker run -e ENV={{env=production}} {{image}}"
        params = ParameterDetector.detect_parameters_new_syntax(command)
        assert params["env"].default == "production"
        assert params["image"].default is None

    def test_detect_parameters_old_syntax(self):
        """Test detecting parameters in old {param} syntax."""
        command = "docker run -p {port}:8080 {image}"
        params = ParameterDetector.detect_parameters_old_syntax(command)
        assert "port" in params
        assert "image" in params

    def test_has_old_syntax(self):
        """Test detecting old syntax in command."""
        assert ParameterDetector.has_old_syntax("docker run {image}")
        assert not ParameterDetector.has_old_syntax("docker run {{image}}")
        assert not ParameterDetector.has_old_syntax("docker run image")

    def test_has_new_syntax(self):
        """Test detecting new syntax in command."""
        assert ParameterDetector.has_new_syntax("docker run {{image}}")
        assert not ParameterDetector.has_new_syntax("docker run {image}")
        assert not ParameterDetector.has_new_syntax("docker run image")

    def test_detect_duplicate_parameters_raises_error(self):
        """Test that duplicate parameters raise an error."""
        command = "docker run {{image}} {{image}}"
        with pytest.raises(ValueError, match="Duplicate parameter name"):
            ParameterDetector.detect_parameters_new_syntax(command)

    def test_detect_invalid_parameter_name_raises_error(self):
        """Test that invalid parameter names raise an error."""
        command = "docker run {{123invalid}}"
        with pytest.raises(ValueError, match="Invalid parameter"):
            ParameterDetector.detect_parameters_new_syntax(command)


class TestParameterSubstitutor:
    """Tests for ParameterSubstitutor."""

    def test_substitute_required_parameter(self):
        """Test substituting a required parameter."""
        command = "docker run {{image}}"
        result = ParameterSubstitutor.substitute_parameters(
            command, {"image": "ubuntu"}
        )
        assert result == "docker run ubuntu"

    def test_substitute_multiple_parameters(self):
        """Test substituting multiple parameters."""
        command = "docker run -p {{port}}:8080 {{image}}"
        result = ParameterSubstitutor.substitute_parameters(
            command, {"port": "3000", "image": "ubuntu"}
        )
        assert result == "docker run -p 3000:8080 ubuntu"

    def test_substitute_with_default_value(self):
        """Test substituting a parameter with default value."""
        command = "docker run {{env=production}} {{image}}"
        result = ParameterSubstitutor.substitute_parameters(
            command, {"image": "ubuntu"}
        )
        assert result == "docker run production ubuntu"

    def test_substitute_override_default_value(self):
        """Test overriding a default parameter value."""
        command = "docker run {{env=production}} {{image}}"
        result = ParameterSubstitutor.substitute_parameters(
            command, {"env": "staging", "image": "ubuntu"}
        )
        assert result == "docker run staging ubuntu"

    def test_substitute_missing_required_parameter_raises_error(self):
        """Test that missing required parameter raises error."""
        command = "docker run {{image}}"
        with pytest.raises(ValueError, match="No value provided"):
            ParameterSubstitutor.substitute_parameters(command, {})


class TestParameterMigrator:
    """Tests for ParameterMigrator."""

    def test_migrate_single_parameter(self):
        """Test migrating a single parameter."""
        command = "docker run {image}"
        migrated, notes = ParameterMigrator.migrate_command(command)
        assert migrated == "docker run {{image}}"
        assert len(notes) > 0

    def test_migrate_multiple_parameters(self):
        """Test migrating multiple parameters."""
        command = "docker run -p {port}:8080 {image}"
        migrated, notes = ParameterMigrator.migrate_command(command)
        assert migrated == "docker run -p {{port}}:8080 {{image}}"
        assert len(notes) == 2

    def test_migrate_with_defaults(self):
        """Test migrating parameters with default values."""
        command = "docker run {{env=production}} {image}"
        migrated, notes = ParameterMigrator.migrate_command(command)
        assert migrated == "docker run {{env=production}} {{image}}"

    def test_migrate_null_on_no_old_syntax(self):
        """Test that commands without old syntax are not modified."""
        command = "docker run {{image}}"
        migrated, notes = ParameterMigrator.migrate_command(command)
        assert migrated == command
        assert len(notes) == 0

    def test_migrate_snippets_batch(self):
        """Test batch migration of snippets."""
        snippets = [
            ("id1", {"command": "docker run {image}"}),
            ("id2", {"command": "docker run {{container}}"}),
            ("id3", {"command": "ls -la"}),
        ]
        results = ParameterMigrator.migrate_snippets_batch(snippets)

        assert len(results) == 3
        assert results[0][1]["command"] == "docker run {{image}}"
        assert results[1][1]["command"] == "docker run {{container}}"
        assert results[2][1]["command"] == "ls -la"
        assert len(results[0][2]) > 0
        assert len(results[1][2]) == 0
        assert len(results[2][2]) == 0
