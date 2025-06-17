"""
Data models for pypet snippets
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, List


@dataclass
class Snippet:
    """A command-line snippet with metadata."""

    command: str
    description: Optional[str] = None
    tags: List[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Initialize default values and normalize inputs."""
        # Initialize empty tag list
        if self.tags is None:
            self.tags = []

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
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Snippet":
        """Create snippet from dictionary (loaded from TOML)."""
        return cls(
            command=data["command"],
            description=data.get("description"),
            tags=data.get("tags", []),
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
