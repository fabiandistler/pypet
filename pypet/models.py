"""
Data models for pypet snippets
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, List, Dict


@dataclass
class Parameter:
    """A parameter for a command-line snippet."""

    name: str
    default: Optional[str] = None
    description: Optional[str] = None

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
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    parameters: Optional[Dict[str, Parameter]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

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

    def to_dict(self) -> dict:
        """Convert snippet to dictionary for TOML storage."""
        return {
            "command": self.command,
            "description": self.description,
            "tags": self.tags or [],
            "parameters": (
                {name: param.to_dict() for name, param in self.parameters.items()}
                if self.parameters
                else {}
            ),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

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

    def apply_parameters(self, params: Optional[Dict[str, str]] = None) -> str:
        """
        Apply parameter values to the command string.

        If a parameter is not provided in params, its default value will be used.
        If a parameter has no default and is not provided, a ValueError is raised.
        """
        params = params or {}
        result = self.command

        if self.parameters:
            for name, param in self.parameters.items():
                value = params.get(name, param.default)
                if value is None:
                    raise ValueError(
                        f"No value provided for required parameter: {name}"
                    )

                # Replace both ${name} and {name} patterns
                result = result.replace(f"${{{name}}}", value)
                result = result.replace(f"{{{name}}}", value)

        return result
