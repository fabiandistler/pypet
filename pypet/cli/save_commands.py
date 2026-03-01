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
        shell = os.environ.get("SHELL", "")
        recent_lines: list[str] = []

        def _get_history_file() -> Path | None:
            """Find the history file to use."""
            possible_files = [
                os.environ.get("HISTFILE"),
                Path.home() / ".bash_history",
                Path.home() / ".zsh_history",
                Path.home() / ".history",
            ]
            for hist_file in possible_files:
                if hist_file and Path(hist_file).exists():
                    return Path(hist_file)
            return None

        def _read_from_shell() -> list[str]:
            """Read history using shell's interactive mode."""
            histfile = _get_history_file()
            if not histfile:
                return []

            try:
                if "bash" in shell:
                    result = subprocess.run(
                        [
                            "bash",
                            "-i",
                            "-c",
                            f"history -a 2>/dev/null; history {lines + 50}",
                        ],
                        capture_output=True,
                        text=True,
                        timeout=3,
                        check=False,
                        env={**os.environ, "HISTFILE": str(histfile)},
                    )
                    if result.returncode == 0 and result.stdout:
                        cmds = []
                        for line in result.stdout.strip().split("\n"):
                            parts = line.strip().split(None, 1)
                            if len(parts) >= 2 and parts[0].isdigit():
                                cmd = parts[1].strip()
                                if cmd:
                                    cmds.append(cmd)
                        return list(reversed(cmds))

                elif "zsh" in shell:
                    result = subprocess.run(
                        ["zsh", "-i", "-c", f"fc -W 2>/dev/null; fc -ln -{lines + 50}"],
                        capture_output=True,
                        text=True,
                        timeout=3,
                        check=False,
                        env={**os.environ, "HISTFILE": str(histfile)},
                    )
                    if result.returncode == 0 and result.stdout:
                        cmds = [
                            line.strip()
                            for line in result.stdout.strip().split("\n")
                            if line.strip()
                        ]
                        return list(reversed(cmds))

                return []
            except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
                return []

        def _read_from_file() -> list[str]:
            """Read history directly from file (newest first)."""
            history_file = _get_history_file()
            if not history_file:
                return []

            try:
                with history_file.open(encoding="utf-8", errors="ignore") as f:
                    all_lines = f.readlines()

                commands = []
                for line in reversed(all_lines):
                    cleaned_line = line.strip()
                    if not cleaned_line or cleaned_line.startswith("#"):
                        continue
                    if cleaned_line.startswith(": ") and ";" in cleaned_line:
                        cleaned_line = cleaned_line.split(";", 1)[1]
                    if cleaned_line:
                        commands.append(cleaned_line)
                        if len(commands) >= lines + 50:
                            break
                return commands
            except Exception:
                return []

        recent_lines = _read_from_shell()
        if not recent_lines:
            recent_lines = _read_from_file()

        if not recent_lines:
            cli_main.console.print("[red]Error:[/red] No commands found in history")
            cli_main.console.print(
                "[yellow]Tip:[/yellow] Try using 'pypet save-clipboard' instead"
            )
            return

        commands = []
        for command in recent_lines:
            if not command.startswith("pypet") and command.strip():
                commands.append(command.strip())
                if len(commands) >= lines:
                    break

        if not commands:
            cli_main.console.print(
                "[red]Error:[/red] No valid commands found in recent history"
            )
            cli_main.console.print(
                "[yellow]Tip:[/yellow] Make sure you run some commands first"
            )
            return

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

        if not Confirm.ask("Save this as a snippet?"):
            cli_main.console.print("[yellow]Cancelled.[/yellow]")
            return

        if not description:
            description = Prompt.ask(
                "Description", default=f"Command from history: {command[:50]}..."
            )

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

        _auto_sync_if_enabled()

    except subprocess.TimeoutExpired:
        cli_main.console.print("[red]Error:[/red] Timeout accessing shell history")
    except Exception as e:
        cli_main.console.print(f"[red]Error:[/red] {e}")
        cli_main.console.print(
            "[yellow]Tip:[/yellow] Try using 'pypet save-clipboard' instead"
        )
