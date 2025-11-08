"""
Alias management for pypet snippets
"""

import re
import shlex
from pathlib import Path

from .models import Snippet


DEFAULT_ALIAS_PATH = Path.home() / ".config" / "pypet" / "aliases.sh"


class AliasManager:
    """Manages shell aliases for pypet snippets."""

    def __init__(self, alias_path: Path | None = None):
        """Initialize alias manager with optional custom path."""
        self.alias_path = alias_path or DEFAULT_ALIAS_PATH
        self.alias_path.parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def validate_alias_name(alias_name: str) -> tuple[bool, str]:
        """
        Validate alias name for shell safety.

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not alias_name:
            return False, "Alias name cannot be empty"

        if len(alias_name) > 64:
            return False, "Alias name too long (max 64 characters)"

        if not alias_name.replace("_", "").replace("-", "").isalnum():
            return (
                False,
                f"Invalid alias name '{alias_name}'. "
                "Alias names should contain only letters, numbers, underscores, and hyphens.",
            )

        return True, ""

    @staticmethod
    def validate_snippet_id(snippet_id: str) -> None:
        """
        Validate snippet ID for shell safety.

        Raises:
            ValueError: If snippet ID contains unsafe characters
        """
        if not re.match(r"^[a-zA-Z0-9_-]+$", snippet_id):
            raise ValueError(
                f"Invalid snippet ID '{snippet_id}': must contain only alphanumeric characters, underscores, and hyphens"
            )

    def _generate_alias_definition(
        self, alias_name: str, snippet_id: str, snippet: Snippet
    ) -> str:
        """
        Generate alias or function definition for a snippet.

        For snippets without parameters, creates a simple alias.
        For snippets with parameters, creates a shell function that calls pypet exec.
        """
        self.validate_snippet_id(snippet_id)

        all_params = snippet.get_all_parameters()

        if not all_params:
            safe_command = shlex.quote(snippet.command)
            return f"alias {alias_name}={safe_command}"

        return f'{alias_name}() {{\n    pypet exec {snippet_id} "$@"\n}}'

    def update_aliases_file(
        self, snippets_with_aliases: list[tuple[str, Snippet]]
    ) -> None:
        """
        Update the aliases.sh file with all current aliases.

        Args:
            snippets_with_aliases: List of (snippet_id, snippet) tuples where snippet has an alias
        """
        lines = [
            "# pypet aliases - Auto-generated file",
            "# Source this file in your shell profile (~/.bashrc, ~/.zshrc, etc.)",
            "# Add this line to your shell profile:",
            f"#   source {self.alias_path}",
            "",
        ]

        for snippet_id, snippet in snippets_with_aliases:
            if not snippet.alias:
                continue

            if snippet.description:
                lines.append(f"# {snippet.description}")

            alias_def = self._generate_alias_definition(
                snippet.alias, snippet_id, snippet
            )
            lines.append(alias_def)
            lines.append("")

        temp_file = self.alias_path.with_suffix(".tmp")
        try:
            with temp_file.open("w", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n")
            temp_file.replace(self.alias_path)
        except Exception:
            if temp_file.exists():
                temp_file.unlink()
            raise

    def get_source_instruction(self) -> str:
        """Get instruction for sourcing the aliases file."""
        return f"source {self.alias_path}"

    def get_setup_instructions(self) -> list[str]:
        """Get instructions for setting up aliases in shell profile."""
        return [
            "To use pypet aliases in your shell, add this line to your shell profile:",
            "",
            f"  source {self.alias_path}",
            "",
            "For bash, add it to ~/.bashrc",
            "For zsh, add it to ~/.zshrc",
            "",
            "Then reload your shell or run:",
            f"  source {self.alias_path}",
        ]

    def check_if_sourced(self) -> str:
        """
        Generate a command to check if aliases file is sourced in shell profile.

        Returns a helpful message about how to check.
        """
        profiles = ["~/.bashrc", "~/.zshrc", "~/.bash_profile", "~/.profile"]
        return f"To check if {self.alias_path} is sourced, run:\n\n" + "\n".join(
            f"  grep -q 'source.*{self.alias_path.name}' {profile} && echo 'Found in {profile}'"
            for profile in profiles
        )
