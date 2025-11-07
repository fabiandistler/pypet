"""
Alias management for pypet snippets
"""

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

    def _generate_alias_definition(
        self, alias_name: str, snippet_id: str, snippet: Snippet
    ) -> str:
        """
        Generate alias or function definition for a snippet.

        For snippets without parameters, creates a simple alias.
        For snippets with parameters, creates a shell function that calls pypet exec.
        """
        # Get all parameters (including those in placeholders)
        all_params = snippet.get_all_parameters()

        if not all_params:
            # No parameters - create a simple alias
            # Use shlex.quote to safely escape the command
            safe_command = shlex.quote(snippet.command)
            return f"alias {alias_name}={safe_command}"
        # Has parameters - create a function that calls pypet exec
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

            # Add a comment with the snippet description
            if snippet.description:
                lines.append(f"# {snippet.description}")

            # Generate and add the alias/function definition
            alias_def = self._generate_alias_definition(
                snippet.alias, snippet_id, snippet
            )
            lines.append(alias_def)
            lines.append("")

        # Write the file
        with self.alias_path.open("w", encoding="utf-8") as f:
            f.write("\n".join(lines))

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
