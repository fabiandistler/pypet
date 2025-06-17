"""
Storage management for pypet snippets using TOML files
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
import toml

from .models import Snippet

DEFAULT_CONFIG_PATH = Path.home() / ".config" / "pypet" / "snippets.toml"


class Storage:
    """Manages snippet storage in TOML format."""

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize storage with optional custom path."""
        self.config_path = config_path or DEFAULT_CONFIG_PATH
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.config_path.exists():
            self._save_snippets({})

    def _load_snippets(self) -> Dict[str, dict]:
        """Load snippets from TOML file."""
        if not self.config_path.exists():
            return {}
        try:
            data = toml.load(self.config_path)
            return {
                snippet_id: snippet_data for snippet_id, snippet_data in data.items()
            }
        except Exception:
            return {}

    def _save_snippets(self, snippets: Dict[str, dict]) -> None:
        """Save snippets to TOML file."""
        with open(self.config_path, "w", encoding="utf-8") as f:
            try:
                toml.dump(snippets, f)
            except Exception as e:
                raise

    def add_snippet(
        self,
        command: str,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> str:
        """Add a new snippet and return its ID."""
        snippets = self._load_snippets()

        # Generate a unique ID (timestamp + microseconds)
        now = datetime.now(timezone.utc)
        snippet_id = now.strftime("%Y%m%d%H%M%S%f")

        # Create and store new snippet
        snippet = Snippet(command=command, description=description, tags=tags or [])
        snippets[snippet_id] = snippet.to_dict()

        self._save_snippets(snippets)
        return snippet_id

    def get_snippet(self, snippet_id: str) -> Optional[Snippet]:
        """Get a snippet by its ID."""
        snippets = self._load_snippets()
        if snippet_id not in snippets:
            return None

        data = snippets[snippet_id]
        return Snippet(
            command=data["command"],
            description=data.get("description"),
            tags=data.get("tags", []),
        )

    def list_snippets(self) -> List[tuple[str, Snippet]]:
        """List all snippets with their IDs."""
        snippets = self._load_snippets()
        return [(id_, Snippet.from_dict(data)) for id_, data in snippets.items()]

    def search_snippets(self, query: str) -> List[tuple[str, Snippet]]:
        """Search snippets by command, description, or tags."""
        query = query.lower()
        results = []

        for id_, snippet in self.list_snippets():
            if (
                query in snippet.command.lower()
                or (snippet.description and query in snippet.description.lower())
                or any(query in tag.lower() for tag in snippet.tags)
            ):
                results.append((id_, snippet))

        return results

    def update_snippet(
        self,
        snippet_id: str,
        command: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
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
