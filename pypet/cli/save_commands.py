"""
Commands for saving snippets from clipboard and shell history
"""

import os
import subprocess
from pathlib import Path

import click
import pyperclip
from rich.prompt import Confirm, Prompt

from . import main_module as cli_main
from .main import _auto_sync_if_enabled, _parse_parameters, main


@main.command("save-clipboard")
@click.option("--description", "-d", help="Description for the snippet")
@click.option("--tags", "-t", help="Tags for the snippet (comma-separated)")
@click.option(
    "--params",
    "-p",
    help="Parameters in format: name[=default][:description],... Example: host=localhost:The host,port=8080:Port number",
)
def save_clipboard(
    description: str | None = None,
    tags: str | None = None,
    params: str | None = None,
) -> None:
    """Save current clipboard content as a snippet."""
    try:
        command = pyperclip.paste()
        if not command or not command.strip():
            cli_main.console.print(
                "[red]Error:[/red] Clipboard is empty or contains only whitespace"
            )
            return

        command = command.strip()
        cli_main.console.print(f"[blue]Clipboard content:[/blue] {command}")

        # Ask for confirmation
        if not Confirm.ask("Save this as a snippet?"):
            cli_main.console.print("[yellow]Cancelled.[/yellow]")
            return

        # Prompt for description if not provided
        if not description:
            description = Prompt.ask("Description", default="Snippet from clipboard")

        # Parse tags and parameters
        tag_list = [t.strip() for t in tags.split(",")] if tags else []
        parameters = _parse_parameters(params) if params else None

        snippet_id = cli_main.storage.add_snippet(
            command=command,
            description=description,
            tags=tag_list,
            parameters=parameters,
        )
        cli_main.console.print(
            f"[green]Added new snippet with ID:[/green] {snippet_id}"
        )

        # Auto-sync if enabled
        _auto_sync_if_enabled()

    except Exception as e:
        cli_main.console.print(f"[red]Error accessing clipboard:[/red] {e}")


@main.command("save-last")
@click.option("--description", "-d", help="Description for the snippet")
@click.option("--tags", "-t", help="Tags for the snippet (comma-separated)")
@click.option(
    "--params",
    "-p",
    help="Parameters in format: name[=default][:description],... Example: host=localhost:The host,port=8080:Port number",
)
@click.option(
    "--lines", "-n", default=1, help="Number of history lines to show (default: 1)"
)
def save_last(
    description: str | None = None,
    tags: str | None = None,
    params: str | None = None,
    lines: int = 1,
) -> None:
    """Save the last command(s) from shell history as a snippet."""
    try:
        # Determine which shell we're using
        shell = os.environ.get("SHELL", "")
        recent_lines = []

        # Strategy 1: Try to read from shell's in-memory history (works in interactive shells)
        # This is more reliable for getting the most recent commands
        if "bash" in shell:
            try:
                # Use HISTFILE or default to ~/.bash_history
                histfile = os.environ.get(
                    "HISTFILE", str(Path.home() / ".bash_history")
                )

                # Run bash with -i (interactive) to access history builtin
                # Use 'history -a' to append current session history to file first
                # Then read a generous number of lines to ensure we get enough
                result = subprocess.run(
                    [
                        "bash",
                        "-i",
                        "-c",
                        f"history -a 2>/dev/null; history {lines + 50}",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=2,
                    check=False,
                    env={**os.environ, "HISTFILE": histfile},
                )

                if result.returncode == 0 and result.stdout:
                    # Parse bash history output format: "  123  command here"
                    for line in result.stdout.strip().split("\n"):
                        # Remove leading line numbers and whitespace
                        parts = line.strip().split(None, 1)
                        if len(parts) >= 2 and parts[0].isdigit():
                            cmd = parts[1].strip()
                            if cmd:
                                recent_lines.append(cmd)
            except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
                # Fall back to file reading if shell history command fails
                pass

        elif "zsh" in shell:
            try:
                # Use HISTFILE or default to ~/.zsh_history
                histfile = os.environ.get("HISTFILE", str(Path.home() / ".zsh_history"))

                # Run zsh with -i (interactive) to access fc builtin
                # fc -l lists history, -n suppresses line numbers, negative number for last N lines
                result = subprocess.run(
                    ["zsh", "-i", "-c", f"fc -W 2>/dev/null; fc -ln -{lines + 50}"],
                    capture_output=True,
                    text=True,
                    timeout=2,
                    check=False,
                    env={**os.environ, "HISTFILE": histfile},
                )

                if result.returncode == 0 and result.stdout:
                    for line in result.stdout.strip().split("\n"):
                        cmd = line.strip()
                        if cmd:
                            recent_lines.append(cmd)
            except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
                # Fall back to file reading
                pass

        # Strategy 2: Fall back to reading from history file directly
        if not recent_lines:
            history_file = None

            # Check common history file locations
            possible_files = [
                os.environ.get("HISTFILE"),  # User's custom HISTFILE
                Path.home() / ".bash_history",
                Path.home() / ".zsh_history",
                Path.home() / ".history",
            ]

            for hist_file in possible_files:
                if hist_file and Path(hist_file).exists():
                    history_file = Path(hist_file)
                    break

            if not history_file:
                cli_main.console.print(
                    "[red]Error:[/red] Could not find shell history file"
                )
                cli_main.console.print(
                    "[yellow]Tip:[/yellow] Try using 'pypet save-clipboard' instead"
                )
                cli_main.console.print(
                    "[blue]Info:[/blue] Looked for: ~/.bash_history, ~/.zsh_history, ~/.history"
                )
                return

            # Read last lines from history file
            try:
                with history_file.open(encoding="utf-8", errors="ignore") as f:
                    all_lines = f.readlines()
            except Exception as e:
                cli_main.console.print(f"[red]Error reading history file:[/red] {e}")
                cli_main.console.print(
                    "[yellow]Tip:[/yellow] Try using 'pypet save-clipboard' instead"
                )
                return

            if not all_lines:
                cli_main.console.print("[red]Error:[/red] History file is empty")
                return

            # Get last N non-empty lines
            for line in reversed(all_lines):
                cleaned_line = line.strip()
                if cleaned_line and not cleaned_line.startswith(
                    "#"
                ):  # Skip comments and empty lines
                    # Handle zsh extended history format: : 1234567890:0;command
                    if cleaned_line.startswith(": ") and ";" in cleaned_line:
                        cleaned_line = cleaned_line.split(";", 1)[1]
                    recent_lines.append(cleaned_line)
                    if (
                        len(recent_lines) >= lines + 50
                    ):  # Get extra to filter pypet commands
                        break

        if not recent_lines:
            cli_main.console.print("[red]Error:[/red] No commands found in history")
            return

        # Filter out pypet commands and prepare final list
        commands = []
        for command in recent_lines:
            # Skip pypet commands to avoid recursion
            if not command.startswith("pypet") and command.strip():
                commands.append(command.strip())
                if len(commands) >= lines:  # We have enough commands
                    break

        if not commands:
            cli_main.console.print(
                "[red]Error:[/red] No valid commands found in recent history"
            )
            cli_main.console.print(
                "[yellow]Tip:[/yellow] Make sure you run some commands first"
            )
            return

        # Show the commands and let user choose
        if len(commands) == 1:
            command = commands[0]
        else:
            cli_main.console.print("[blue]Recent commands:[/blue]")
            for i, cmd in enumerate(commands, 1):
                cli_main.console.print(f"  {i}. {cmd}")

            choice = Prompt.ask(
                "Which command to save?",
                choices=[str(i) for i in range(1, len(commands) + 1)],
                default="1",
            )
            command = commands[int(choice) - 1]

        cli_main.console.print(f"[blue]Selected command:[/blue] {command}")

        # Ask for confirmation
        if not Confirm.ask("Save this as a snippet?"):
            cli_main.console.print("[yellow]Cancelled.[/yellow]")
            return

        # Prompt for description if not provided
        if not description:
            description = Prompt.ask(
                "Description", default=f"Command from history: {command[:50]}..."
            )

        # Parse tags and parameters
        tag_list = [t.strip() for t in tags.split(",")] if tags else []
        parameters = _parse_parameters(params) if params else None

        snippet_id = cli_main.storage.add_snippet(
            command=command,
            description=description,
            tags=tag_list,
            parameters=parameters,
        )
        cli_main.console.print(
            f"[green]Added new snippet with ID:[/green] {snippet_id}"
        )

        # Auto-sync if enabled
        _auto_sync_if_enabled()

    except subprocess.TimeoutExpired:
        cli_main.console.print("[red]Error:[/red] Timeout accessing shell history")
    except Exception as e:
        cli_main.console.print(f"[red]Error:[/red] {e}")
        cli_main.console.print(
            "[yellow]Tip:[/yellow] Try using 'pypet save-clipboard' instead"
        )
