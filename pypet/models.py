"""
Data models for pypet snippets
"""

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .parameters import ParameterDetector, ParameterSubstitutor


@dataclass
class Parameter:
    """A parameter for a command-line snippet (legacy support)."""

    name: str
    default: str | None = None
    description: str | None = None

    def __post_init__(self):
        """Normalize parameter attributes."""
        self.name = self.name.strip()
        if self.description:
            self.description = self.description.strip()

    def to_dict(self) -> dict:
        """Convert parameter to dictionary for TOML storage."""
        return {
            "name": self.name,
            "default": self.default,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Parameter":
        """Create parameter from dictionary."""
        return cls(
            name=data["name"],
            default=data.get("default"),
            description=data.get("description"),
        )


@dataclass
class Snippet:
    """A command-line snippet with metadata."""

    command: str
    description: str | None = None
    tags: list[str] | None = None
    parameters: dict[str, Parameter] | None = None
    alias: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self):
        """Initialize default values and normalize inputs."""
        # Initialize empty collections
        if self.tags is None:
            self.tags = []
        if self.parameters is None:
            self.parameters = {}

        # Strip whitespace from command and description
        self.command = self.command.strip() if self.command else ""
        self.description = self.description.strip() if self.description else None

        # Strip whitespace from alias
        self.alias = self.alias.strip() if self.alias else None

        # Remove duplicates and strip whitespace from tags
        if self.tags:
            self.tags = [t.strip() for t in self.tags if t and t.strip()]
            self.tags = list(
                dict.fromkeys(self.tags)
            )  # Remove duplicates while preserving order

        # Set timestamps
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)
        if self.updated_at is None:
            self.updated_at = self.created_at

    def to_dict(self) -> dict[str, Any]:
        """Convert snippet to dictionary for TOML storage."""
        result: dict[str, Any] = {
            "command": self.command,
            "description": self.description,
            "tags": self.tags or [],
            "alias": self.alias,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        # Only include parameters if there are any
        if self.parameters:
            result["parameters"] = {
                name: param.to_dict() for name, param in self.parameters.items()
            }

        return result

    @classmethod
    def from_dict(cls, data: dict) -> "Snippet":
        """Create snippet from dictionary (loaded from TOML)."""
        # Convert parameter dictionaries to Parameter objects
        parameters = {}
        if "parameters" in data:
            parameters = {
                name: Parameter.from_dict(param_data)
                for name, param_data in data["parameters"].items()
            }

        return cls(
            command=data["command"],
            description=data.get("description"),
            tags=data.get("tags", []),
            parameters=parameters,
            alias=data.get("alias"),
            created_at=(
                datetime.fromisoformat(data["created_at"])
                if data.get("created_at")
                else None
            ),
            updated_at=(
                datetime.fromisoformat(data["updated_at"])
                if data.get("updated_at")
                else None
            ),
        )

    def apply_parameters(self, params: dict[str, str] | None = None) -> str:
        """
        Apply parameter values to the command string.

        Supports both new {{param}} and legacy {param} syntax.
        """
        params = params or {}
        result = self.command

        # Try new syntax first
        if ParameterDetector.has_new_syntax(result):
            return ParameterSubstitutor.substitute_parameters(result, params)

        # Fall back to legacy syntax handling
        all_params = self.get_all_parameters()

        # Apply parameter substitution
        for name, param in all_params.items():
            value = params.get(name, param.default)
            if value is None:
                raise ValueError(f"No value provided for required parameter: {name}")

            # Replace both ${name} and {name} patterns (legacy)
            result = result.replace(f"${{{name}}}", value)
            result = result.replace(f"{{{name}}}", value)

            # Also replace {name=default} patterns (legacy)
            if param.default is not None:
                result = result.replace(f"{{{name}={param.default}}}", value)

        return result

    def get_all_parameters(self) -> dict[str, Parameter]:
        """
        Get all parameters for this snippet, including both formally defined ones
        and those discovered from command placeholders.

        Returns a dictionary mapping parameter names to Parameter objects.
        """
        # Build a complete parameter map combining defined parameters and discovered ones
        all_params = {}

        # First, add formally defined parameters
        if self.parameters:
            all_params.update(self.parameters)

        # Try to detect using new {{param}} syntax
        if ParameterDetector.has_new_syntax(self.command):
            try:
                new_syntax_params = ParameterDetector.detect_parameters_new_syntax(
                    self.command
                )
                for name, metadata in new_syntax_params.items():
                    if name not in all_params:
                        all_params[name] = Parameter(
                            name=name,
                            default=metadata.default,
                            description=metadata.description,
                        )
                return all_params
            except ValueError:
                pass

        # Fall back to legacy {param} syntax detection
        # Find all parameter placeholders in the command string
        placeholder_pattern = r"\{([^}]+)\}"
        placeholders = re.findall(placeholder_pattern, self.command)

        # Then, discover parameters from placeholders not already defined
        for placeholder in placeholders:
            if "=" in placeholder:
                # Format: {name=default}
                param_name, param_default = placeholder.split("=", 1)
                param_name = param_name.strip()
            else:
                # Format: {name}
                param_name = placeholder.strip()
                param_default = None

            # Only add if not already formally defined and is a valid name
            if (
                param_name not in all_params
                and param_name
                and not param_name.startswith("}")
            ):
                all_params[param_name] = Parameter(
                    name=param_name, default=param_default, description=None
                )

        return all_params
