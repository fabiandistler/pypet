"""
Parameter handling system for pypet snippets.

This module provides utilities for:
- Detecting parameter placeholders using the {{param}} syntax
- Validating parameter definitions
- Managing parameter metadata (names, defaults, descriptions)
- Supporting migration from old {param} syntax to new {{param}} syntax
"""

import re
from dataclasses import dataclass


@dataclass
class ParameterMetadata:
    """Metadata for a parameter."""

    name: str
    default: str | None = None
    description: str | None = None

    def __post_init__(self):
        """Normalize parameter attributes."""
        self.name = self.name.strip()
        if self.description:
            self.description = self.description.strip()

    def to_dict(self) -> dict:
        """Convert to dictionary for TOML storage."""
        return {
            "name": self.name,
            "default": self.default,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ParameterMetadata":
        """Create from dictionary."""
        return cls(
            name=data["name"],
            default=data.get("default"),
            description=data.get("description"),
        )


class ParameterValidator:
    """Validates parameter syntax and definitions."""

    VALID_PARAM_NAME_PATTERN = r"^[a-zA-Z_][a-zA-Z0-9_-]*$"

    @staticmethod
    def validate_parameter_name(name: str) -> tuple[bool, str | None]:
        """
        Validate a parameter name.

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not name or not name.strip():
            return False, "Parameter name cannot be empty"

        name = name.strip()
        if not re.match(ParameterValidator.VALID_PARAM_NAME_PATTERN, name):
            return (
                False,
                f"Invalid parameter name '{name}'. "
                "Names must start with letter or underscore "
                "and contain only alphanumeric characters, underscores, and hyphens.",
            )

        return True, None

    @staticmethod
    def validate_parameters(
        parameters: dict[str, ParameterMetadata],
    ) -> tuple[bool, list[str]]:
        """
        Validate a set of parameters.

        Returns:
            Tuple of (is_valid, list_of_error_messages)
        """
        errors = []

        for name, _param in parameters.items():
            is_valid, error = ParameterValidator.validate_parameter_name(name)
            if not is_valid and error:
                errors.append(error)

        return len(errors) == 0, errors


class ParameterDetector:
    """Detects parameters in command strings using the {{param}} syntax."""

    NEW_SYNTAX_PATTERN = r"\{\{([^}]+)\}\}"
    OLD_SYNTAX_PATTERN = r"\{([^}]+)\}"

    @staticmethod
    def detect_parameters_new_syntax(
        command: str,
    ) -> dict[str, ParameterMetadata]:
        """
        Detect parameters using new {{param}} syntax.

        Returns a dictionary mapping parameter names to ParameterMetadata objects.
        """
        parameters = {}
        placeholders = re.findall(ParameterDetector.NEW_SYNTAX_PATTERN, command)

        for placeholder in placeholders:
            if "=" in placeholder:
                param_name, param_default = placeholder.split("=", 1)
                param_name = param_name.strip()
                param_default = param_default.strip()
            else:
                param_name = placeholder.strip()
                param_default = None

            is_valid, error = ParameterValidator.validate_parameter_name(param_name)
            if not is_valid:
                raise ValueError(f"Invalid parameter in command: {error}")

            if param_name in parameters:
                raise ValueError(f"Duplicate parameter name: {param_name}")

            parameters[param_name] = ParameterMetadata(
                name=param_name, default=param_default, description=None
            )

        return parameters

    @staticmethod
    def detect_parameters_old_syntax(command: str) -> dict[str, str]:
        """
        Detect parameters using old {param} syntax.

        Returns a dictionary mapping parameter names to their defaults (or None).
        Used for migration detection.
        """
        parameters = {}
        placeholders = re.findall(ParameterDetector.OLD_SYNTAX_PATTERN, command)

        for placeholder in placeholders:
            if "=" in placeholder:
                param_name, param_default = placeholder.split("=", 1)
                param_name = param_name.strip()
            else:
                param_name = placeholder.strip()
                param_default = None

            parameters[param_name] = param_default

        return parameters

    @staticmethod
    def has_old_syntax(command: str) -> bool:
        """Check if command contains old {param} syntax (but not {{param}})."""
        parameters = ParameterDetector.detect_parameters_old_syntax(command)
        if not parameters:
            return False

        for placeholder in re.finditer(ParameterDetector.OLD_SYNTAX_PATTERN, command):
            full_match = placeholder.group(0)
            if not full_match.startswith("{{"):
                return True

        return False

    @staticmethod
    def has_new_syntax(command: str) -> bool:
        """Check if command contains new {{param}} syntax."""
        return bool(re.search(ParameterDetector.NEW_SYNTAX_PATTERN, command))


class ParameterSubstitutor:
    """Handles parameter substitution in commands."""

    @staticmethod
    def substitute_parameters(
        command: str, parameters: dict[str, str] | None = None
    ) -> str:
        """
        Substitute parameter placeholders with provided values.

        Args:
            command: Command string with {{param}} placeholders
            parameters: Dictionary mapping parameter names to values

        Returns:
            Command with placeholders replaced by values

        Raises:
            ValueError: If a required parameter has no value
        """
        parameters = parameters or {}
        result = command

        placeholders = re.findall(ParameterDetector.NEW_SYNTAX_PATTERN, command)

        for placeholder in placeholders:
            if "=" in placeholder:
                param_name, param_default = placeholder.split("=", 1)
                param_name = param_name.strip()
                param_default = param_default.strip()
            else:
                param_name = placeholder.strip()
                param_default = None

            value = parameters.get(param_name, param_default)
            if value is None:
                raise ValueError(
                    f"No value provided for required parameter: {param_name}"
                )

            placeholder_pattern = f"{{{{{placeholder}}}}}"
            result = result.replace(placeholder_pattern, value)

        return result


class ParameterMigrator:
    """Handles migration from old {param} syntax to new {{param}} syntax."""

    @staticmethod
    def migrate_command(command: str) -> tuple[str, list[str]]:
        """
        Migrate a command from old {param} syntax to new {{param}} syntax.

        Returns:
            Tuple of (migrated_command, list_of_migration_notes)
        """
        migrated = command
        notes = []

        old_pattern = r"\{([^}]+)\}"
        matches = list(re.finditer(old_pattern, command))

        for match in reversed(matches):
            placeholder = match.group(1)
            start, end = match.span()

            if command[start : start + 2] == "{{":
                continue

            migrated = migrated[:start] + "{{" + placeholder + "}}" + migrated[end:]
            notes.append(f"Migrated {{{{{placeholder}}}}} to {{{{{{{placeholder}}}}}}}")

        return migrated, notes

    @staticmethod
    def migrate_snippets_batch(
        snippets: list[tuple[str, dict]],
    ) -> list[tuple[str, dict, list[str]]]:
        """
        Migrate multiple snippets from old syntax to new syntax.

        Args:
            snippets: List of tuples (snippet_id, snippet_dict)

        Returns:
            List of tuples (snippet_id, migrated_snippet_dict, migration_notes)
        """
        results: list[tuple[str, dict, list[str]]] = []

        for snippet_id, snippet_dict in snippets:
            if "command" not in snippet_dict:
                results.append((snippet_id, snippet_dict, []))
                continue

            command = snippet_dict["command"]
            if not ParameterDetector.has_old_syntax(command):
                results.append((snippet_id, snippet_dict, []))
                continue

            migrated_command, notes = ParameterMigrator.migrate_command(command)
            migrated_dict = snippet_dict.copy()
            migrated_dict["command"] = migrated_command

            results.append((snippet_id, migrated_dict, notes))

        return results
