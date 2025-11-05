"""
Commands for executing and copying snippets (exec, copy)
"""

import subprocess

import click
import pyperclip
from rich.prompt import Confirm, Prompt
from rich.table import Table

from . import main_module as cli_main
from .main import _format_parameters, _prompt_for_parameters, main


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
            table.add_column("Index", style="blue")
            table.add_column("ID", style="cyan")
            table.add_column("Command", style="green")
            table.add_column("Description", style="yellow")
            table.add_column("Parameters", style="magenta")

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
            table.add_column("Index", style="blue")
            table.add_column("ID", style="cyan")
            table.add_column("Command", style="green")
            table.add_column("Description", style="yellow")
            table.add_column("Parameters", style="magenta")

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
                # Note: shell=True is required for pypet's use case of executing shell commands
                # with pipes, redirects, etc. User confirmation is required before execution.
                subprocess.run(final_command, shell=True, check=True)
            except subprocess.CalledProcessError as e:
                cli_main.console.print(
                    f"[red]Command failed with exit code {e.returncode}[/red]"
                )
            except Exception as e:
                cli_main.console.print(f"[red]Error executing command:[/red] {e!s}")

    except KeyboardInterrupt:
        cli_main.console.print("\n[yellow]Operation cancelled[/yellow]")
