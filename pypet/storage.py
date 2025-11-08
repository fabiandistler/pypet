"""
Storage management for pypet snippets using TOML files
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

import toml

from .models import Parameter, Snippet


DEFAULT_CONFIG_PATH = Path.home() / ".config" / "pypet" / "snippets.toml"


class Storage:
    """Manages snippet storage in TOML format."""

    def __init__(self, config_path: Path | None = None):
        """Initialize storage with optional custom path."""
        self.config_path = config_path or DEFAULT_CONFIG_PATH
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.config_path.exists():
            self._save_snippets({})

    def _load_snippets(self) -> dict[str, dict]:
        """Load snippets from TOML file."""
        if not self.config_path.exists():
            return {}
        try:
            data = toml.load(self.config_path)
            return dict(data.items())
        except (toml.TomlDecodeError, OSError) as e:
            # Log error but return empty dict to allow graceful degradation
            print(
                f"Warning: Failed to load snippets from {self.config_path}: {e}",
                file=sys.stderr,
            )
            return {}

    def _save_snippets(self, snippets: dict[str, dict]) -> None:
        """Save snippets to TOML file."""
        with self.config_path.open("w", encoding="utf-8") as f:
            toml.dump(snippets, f)

    def add_snippet(
        self,
        command: str,
        description: str | None = None,
        tags: list[str] | None = None,
        parameters: dict[str, Parameter] | None = None,
        alias: str | None = None,
    ) -> str:
        """Add a new snippet and return its ID.

        Args:
            command: The command template with optional parameter placeholders
            description: Optional description of what the command does
            tags: Optional list of tags for organization
            parameters: Optional dictionary of Parameter objects for customization
            alias: Optional alias name for this snippet
        """
        snippets = self._load_snippets()

        # Generate a unique ID (timestamp + microseconds)
        now = datetime.now(timezone.utc)
        snippet_id = now.strftime("%Y%m%d%H%M%S%f")

        # Create and store new snippet
        snippet = Snippet(
            command=command,
            description=description,
            tags=tags or [],
            parameters=parameters,
            alias=alias,
        )
        snippets[snippet_id] = snippet.to_dict()

        self._save_snippets(snippets)
        return snippet_id

    def get_snippet(self, snippet_id: str) -> Snippet | None:
        """Get a snippet by its ID."""
        snippets = self._load_snippets()
        if snippet_id not in snippets:
            return None
        return Snippet.from_dict(snippets[snippet_id])

    def list_snippets(self) -> list[tuple[str, Snippet]]:
        """List all snippets with their IDs."""
        snippets = self._load_snippets()
        return [(id_, Snippet.from_dict(data)) for id_, data in snippets.items()]

    def search_snippets(self, query: str) -> list[tuple[str, Snippet]]:
        """Search snippets by command, description, tags, or parameter names."""
        query = query.lower()
        results = []

        for id_, snippet in self.list_snippets():
            if (
                query in snippet.command.lower()
                or (snippet.description and query in snippet.description.lower())
                or (snippet.tags and any(query in tag.lower() for tag in snippet.tags))
                or (
                    snippet.parameters
                    and any(
                        query in param.name.lower()
                        or (param.description and query in param.description.lower())
                        for param in snippet.parameters.values()
                    )
                )
            ):
                results.append((id_, snippet))

        return results

    def update_snippet(
        self,
        snippet_id: str,
        command: str | None = None,
        description: str | None = None,
        tags: list[str] | None = None,
        parameters: dict[str, Parameter] | None = None,
        alias: str | None = None,
    ) -> bool:
        """Update an existing snippet. Returns True if successful."""
        snippets = self._load_snippets()
        if snippet_id not in snippets:
            return False

        snippet = Snippet.from_dict(snippets[snippet_id])
        if command is not None:
            snippet.command = command
        if description is not None:
            snippet.description = description
        if tags is not None:
            snippet.tags = tags
        if parameters is not None:
            snippet.parameters = parameters
        if alias is not None:
            snippet.alias = alias if alias else None
        snippet.updated_at = datetime.now(timezone.utc)

        snippets[snippet_id] = snippet.to_dict()
        self._save_snippets(snippets)
        return True

    def delete_snippet(self, snippet_id: str) -> bool:
        """Delete a snippet by ID. Returns True if successful."""
        snippets = self._load_snippets()
        if snippet_id not in snippets:
            return False

        del snippets[snippet_id]
        self._save_snippets(snippets)
        return True

    def get_snippets_with_aliases(self) -> list[tuple[str, Snippet]]:
        """Get all snippets that have aliases defined."""
        return [
            (id_, snippet) for id_, snippet in self.list_snippets() if snippet.alias
        ]
