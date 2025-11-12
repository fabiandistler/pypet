"""
Commands for executing and copying snippets (exec, copy)
"""

import os
import subprocess
from pathlib import Path

import click
import pyperclip
from rich.prompt import Confirm, Prompt
from rich.table import Table

from . import main_module as cli_main
from .main import _format_parameters, _prompt_for_parameters, main


def _execute_with_shell_support(command: str) -> subprocess.CompletedProcess:
    """
    Execute a command with shell alias support.

    This function runs commands through the user's shell with alias expansion enabled.
    It detects the user's shell (bash/zsh) and sources the appropriate configuration
    file to load aliases before executing the command.

    Args:
        command: The command to execute

    Returns:
        CompletedProcess instance from subprocess.run

    Raises:
        subprocess.CalledProcessError: If the command fails
    """
    # Get user's shell from SHELL environment variable
    user_shell = os.environ.get("SHELL", "/bin/sh")
    shell_name = Path(user_shell).name

    # For bash and zsh, explicitly source config and enable alias expansion
    # This is more reliable than -i flag which can hang on interactive prompts
    if shell_name == "bash":
        # Source .bashrc and enable alias expansion, then run the command
        # Errors from sourcing are suppressed to handle missing/broken .bashrc
        wrapped_command = f"source ~/.bashrc 2>/dev/null; shopt -s expand_aliases; {command}"
        shell_command = [user_shell, "-c", wrapped_command]
        return subprocess.run(shell_command, check=True, stdin=subprocess.DEVNULL)
    if shell_name == "zsh":
        # Source .zshrc then run the command
        # Errors from sourcing are suppressed to handle missing/broken .zshrc
        wrapped_command = f"source ~/.zshrc 2>/dev/null; {command}"
        shell_command = [user_shell, "-c", wrapped_command]
        return subprocess.run(shell_command, check=True, stdin=subprocess.DEVNULL)
    # Fall back to the original behavior for other shells
    # Note: shell=True is required for pypet's use case of executing shell commands
    # with pipes, redirects, etc. User confirmation is required before execution.
    return subprocess.run(command, shell=True, check=True)


@main.command()
@click.argument("snippet_id", required=False)
@click.option(
    "--param",
    "-P",
    multiple=True,
    help="Parameter values in name=value format. Can be specified multiple times.",
)
def copy(
    snippet_id: str | None = None,
    param: tuple[str, ...] = (),
) -> None:
    """Copy a snippet to clipboard. If no snippet ID is provided, shows an interactive selection."""
    try:
        selected_snippet = None

        if snippet_id is None:
            # Show interactive snippet selection
            snippets = cli_main.storage.list_snippets()
            if not snippets:
                cli_main.console.print(
                    "[yellow]No snippets found.[/yellow] Add some with 'pypet new'"
                )
                return

            # Display snippets table for selection
            table = Table(title="Available Snippets")
            table.add_column("Index", style="blue", no_wrap=True)
            table.add_column("ID", style="cyan", no_wrap=True)
            table.add_column("Command", style="green", overflow="fold", no_wrap=False)
            table.add_column("Description", style="yellow", no_wrap=False)
            table.add_column("Parameters", style="magenta", no_wrap=False)

            for i, (id_, snippet) in enumerate(snippets, 1):
                table.add_row(
                    str(i),
                    id_,
                    snippet.command,
                    snippet.description or "",
                    _format_parameters(snippet),
                )

            cli_main.console.print(table)

            # Get user selection
            while True:
                try:
                    choice_str = Prompt.ask("Enter snippet number (or 'q' to quit)")
                    if choice_str.lower() == "q":
                        return
                    choice = int(choice_str)
                    if 1 <= choice <= len(snippets):
                        selected_snippet = snippets[choice - 1][1]
                        snippet_id = snippets[choice - 1][0]
                        break
                    cli_main.console.print("[red]Invalid selection[/red]")
                except (ValueError, EOFError):
                    cli_main.console.print("[red]Please enter a number[/red]")
                except KeyboardInterrupt:
                    cli_main.console.print("\n[yellow]Operation cancelled[/yellow]")
                    return
        else:
            # Get snippet by ID
            selected_snippet = cli_main.storage.get_snippet(snippet_id)
            if not selected_snippet:
                cli_main.console.print(f"[red]Snippet not found:[/red] {snippet_id}")
                raise click.ClickException(f"Snippet not found: {snippet_id}")

        # Parse provided parameter values
        param_values = {}
        for p in param:
            try:
                name, value = p.split("=", 1)
                param_values[name.strip()] = value.strip()
            except ValueError:
                cli_main.console.print(
                    f"[red]Invalid parameter format:[/red] {p}. Use name=value"
                )
                return

        # If not all parameters are provided via command line, prompt for them
        all_parameters = selected_snippet.get_all_parameters()
        if all_parameters and len(param_values) < len(all_parameters):
            interactive_values = _prompt_for_parameters(selected_snippet, param_values)
            param_values.update(interactive_values)

        # Apply parameters to get final command
        try:
            final_command = selected_snippet.apply_parameters(param_values)
        except ValueError as e:
            cli_main.console.print(f"[red]Error:[/red] {e!s}")
            return

        # Copy to clipboard
        try:
            pyperclip.copy(final_command)
            cli_main.console.print(
                f"[green]✓ Copied to clipboard:[/green] {final_command}"
            )
        except Exception as e:
            cli_main.console.print(f"[red]Failed to copy to clipboard:[/red] {e!s}")
            cli_main.console.print(f"[yellow]Command:[/yellow] {final_command}")

    except KeyboardInterrupt:
        cli_main.console.print("\n[yellow]Operation cancelled[/yellow]")


@main.command()
@click.argument("snippet_id", required=False)
@click.option(
    "--print-only", "-p", is_flag=True, help="Only print the command without executing"
)
@click.option("--edit", "-e", is_flag=True, help="Edit command before execution")
@click.option(
    "--copy", "-c", is_flag=True, help="Copy command to clipboard instead of executing"
)
@click.option(
    "--param",
    "-P",
    multiple=True,
    help="Parameter values in name=value format. Can be specified multiple times.",
)
def exec(
    snippet_id: str | None = None,
    print_only: bool = False,
    edit: bool = False,
    copy: bool = False,
    param: tuple[str, ...] = (),
) -> None:
    """Execute a saved snippet. If no snippet ID is provided, shows an interactive selection."""
    try:
        selected_snippet = None

        if snippet_id is None:
            # Show interactive snippet selection
            snippets = cli_main.storage.list_snippets()
            if not snippets:
                cli_main.console.print(
                    "[yellow]No snippets found.[/yellow] Add some with 'pypet new'"
                )
                return

            # Display snippets table for selection
            table = Table(title="Available Snippets")
            table.add_column("Index", style="blue", no_wrap=True)
            table.add_column("ID", style="cyan", no_wrap=True)
            table.add_column("Command", style="green", overflow="fold", no_wrap=False)
            table.add_column("Description", style="yellow", no_wrap=False)
            table.add_column("Parameters", style="magenta", no_wrap=False)

            for i, (id_, snippet) in enumerate(snippets, 1):
                table.add_row(
                    str(i),
                    id_,
                    snippet.command,
                    snippet.description or "",
                    _format_parameters(snippet),
                )

            cli_main.console.print(table)

            # Get user selection
            while True:
                try:
                    choice_str = Prompt.ask("Enter snippet number (or 'q' to quit)")
                    if choice_str.lower() == "q":
                        return
                    choice = int(choice_str)
                    if 1 <= choice <= len(snippets):
                        selected_snippet = snippets[choice - 1][1]
                        snippet_id = snippets[choice - 1][0]
                        break
                    cli_main.console.print("[red]Invalid selection[/red]")
                except (ValueError, EOFError):
                    cli_main.console.print("[red]Please enter a number[/red]")
                except KeyboardInterrupt:
                    cli_main.console.print("\n[yellow]Operation cancelled[/yellow]")
                    return
        else:
            # Get snippet by ID
            selected_snippet = cli_main.storage.get_snippet(snippet_id)
            if not selected_snippet:
                cli_main.console.print(f"[red]Snippet not found:[/red] {snippet_id}")
                raise click.ClickException(f"Snippet not found: {snippet_id}")

        # Parse provided parameter values
        param_values = {}
        for p in param:
            try:
                name, value = p.split("=", 1)
                param_values[name.strip()] = value.strip()
            except ValueError:
                cli_main.console.print(
                    f"[red]Invalid parameter format:[/red] {p}. Use name=value"
                )
                return

        # If not all parameters are provided via command line, prompt for them
        all_parameters = selected_snippet.get_all_parameters()
        if all_parameters and len(param_values) < len(all_parameters):
            interactive_values = _prompt_for_parameters(selected_snippet, param_values)
            param_values.update(interactive_values)

        # Apply parameters to get final command
        try:
            final_command = selected_snippet.apply_parameters(param_values)
        except ValueError as e:
            cli_main.console.print(f"[red]Error:[/red] {e!s}")
            return

        if edit:
            try:
                final_command = click.edit(final_command)
                if final_command is None:
                    cli_main.console.print(
                        "[yellow]Command execution cancelled[/yellow]"
                    )
                    return
            except click.ClickException:
                # Fallback for non-interactive environments (like tests)
                cli_main.console.print(
                    "[yellow]Editor not available, using original command[/yellow]"
                )

        if print_only:
            cli_main.console.print(final_command)
        elif copy:
            try:
                pyperclip.copy(final_command)
                cli_main.console.print(
                    f"[green]✓ Copied to clipboard:[/green] {final_command}"
                )
            except Exception as e:
                cli_main.console.print(f"[red]Failed to copy to clipboard:[/red] {e!s}")
                cli_main.console.print(f"[yellow]Command:[/yellow] {final_command}")
        else:
            # Check for potentially dangerous patterns
            dangerous_patterns = [";", "&&", "||", "|", ">", ">>", "<", "`", "$()"]
            has_dangerous = any(
                pattern in final_command for pattern in dangerous_patterns
            )

            # Confirm before execution
            cli_main.console.print(f"[yellow]Execute command:[/yellow] {final_command}")

            if has_dangerous:
                cli_main.console.print(
                    "[red]Warning:[/red] Command contains shell operators that could be dangerous."
                )
                cli_main.console.print(
                    "[yellow]Please review carefully before executing.[/yellow]"
                )

            if not Confirm.ask("Execute this command?"):
                cli_main.console.print("[yellow]Command execution cancelled[/yellow]")
                return

            try:
                _execute_with_shell_support(final_command)
            except subprocess.CalledProcessError as e:
                cli_main.console.print(
                    f"[red]Command failed with exit code {e.returncode}[/red]"
                )
            except Exception as e:
                cli_main.console.print(f"[red]Error executing command:[/red] {e!s}")

    except KeyboardInterrupt:
        cli_main.console.print("\n[yellow]Operation cancelled[/yellow]")
