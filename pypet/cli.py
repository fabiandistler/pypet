"""
Command-line interface for pypet
"""

from typing import Dict, Optional, cast
import click
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt

from .models import Parameter, Snippet
from .storage import Storage

console = Console()
storage = Storage()


def _format_parameters(parameters: Optional[Dict[str, Parameter]]) -> str:
    """Format parameters for display in table."""
    if not parameters:
        return ""
    return ", ".join(
        f"{name}={param.default or '<required>'}"
        + (f" ({param.description})" if param.description else "")
        for name, param in parameters.items()
    )


def _parse_parameters(param_str: str) -> Dict[str, Parameter]:
    """Parse parameter string into Parameter objects.
    
    Format: name[=default][:description],name[=default][:description],...
    Example: host=localhost:The host to connect to,port=8080:Port number
    """
    if not param_str:
        return {}
    
    parameters = {}
    for param_def in param_str.split(","):
        if ":" in param_def:
            param_part, description = param_def.split(":", 1)
        else:
            param_part, description = param_def, None
            
        if "=" in param_part:
            name, default = param_part.split("=", 1)
        else:
            name, default = param_part, None
            
        parameters[name.strip()] = Parameter(
            name=name.strip(),
            default=default.strip() if default else None,
            description=description.strip() if description else None
        )
    
    return parameters


def _prompt_for_parameters(snippet: Snippet) -> Dict[str, str]:
    """Prompt user for parameter values."""
    if not snippet.parameters:
        return {}
    
    values = {}
    for name, param in snippet.parameters.items():
        prompt = f"{name}"
        if param.description:
            prompt += f" ({param.description})"
        if param.default:
            prompt += f" [{param.default}]"
        
        value = Prompt.ask(prompt)
        if value:
            values[name] = value
        elif param.default:
            values[name] = param.default
            
    return values


@click.group()
@click.version_option()
def main():
    """A command-line snippet manager inspired by pet."""
    pass


@main.command(name="list")
def list_snippets():
    """List all snippets."""
    table = Table(title="Snippets")
    table.add_column("ID", style="blue")
    table.add_column("Command", style="cyan")
    table.add_column("Description", style="green")
    table.add_column("Tags", style="yellow")
    table.add_column("Parameters", style="magenta")

    for snippet_id, snippet in storage.list_snippets():
        table.add_row(
            snippet_id,
            snippet.command,
            snippet.description or "",
            ", ".join(snippet.tags) if snippet.tags else "",
            _format_parameters(snippet.parameters),
        )

    console.print(table)


@main.command()
@click.argument("command")
@click.option("--description", "-d", help="Description of the snippet")
@click.option("--tags", "-t", help="Tags for the snippet (comma-separated)")
@click.option(
    "--params",
    "-p",
    help="Parameters in format: name[=default][:description],... Example: host=localhost:The host,port=8080:Port number",
)
def new(
    command: str,
    description: Optional[str] = None,
    tags: Optional[str] = None,
    params: Optional[str] = None,
):
    """Create a new snippet."""
    tag_list = [t.strip() for t in tags.split(",")] if tags else []
    parameters = _parse_parameters(params) if params else None
    
    snippet_id = storage.add_snippet(
        command=command,
        description=description,
        tags=tag_list,
        parameters=parameters,
    )
    console.print(f"[green]Added new snippet with ID:[/green] {snippet_id}")


@main.command()
@click.argument("query")
def search(query: str):
    """Search for snippets."""
    table = Table(title=f"Search Results for '{query}'")
    table.add_column("ID", style="blue")
    table.add_column("Command", style="cyan")
    table.add_column("Description", style="green")
    table.add_column("Tags", style="yellow")
    table.add_column("Parameters", style="magenta")

    for snippet_id, snippet in storage.search_snippets(query):
        table.add_row(
            snippet_id,
            snippet.command,
            snippet.description or "",
            ", ".join(snippet.tags) if snippet.tags else "",
            _format_parameters(snippet.parameters),
        )

    console.print(table)


@main.command()
@click.argument("snippet_id")
def delete(snippet_id: str):
    """Delete a snippet."""
    if storage.delete_snippet(snippet_id):
        console.print(f"[green]Deleted snippet:[/green] {snippet_id}")
    else:
        console.print(f"[red]Snippet not found:[/red] {snippet_id}")


@main.command()
@click.argument("snippet_id")
@click.option("--command", "-c", help="New command")
@click.option("--description", "-d", help="New description")
@click.option("--tags", "-t", help="New tags (comma-separated)")
@click.option(
    "--params",
    "-p",
    help="Parameters in format: name[=default][:description],... Example: host=localhost:The host,port=8080:Port number",
)
def edit(
    snippet_id: str,
    command: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[str] = None,
    params: Optional[str] = None,
):
    """Edit an existing snippet."""
    # Check if snippet exists first
    existing = storage.get_snippet(snippet_id)
    if not existing:
        console.print(f"[red]Error:[/red] Snippet with ID '{snippet_id}' not found")
        return

    # Only split tags if they were provided
    tag_list = [t.strip() for t in tags.split(",")] if tags is not None else None
    
    # Only parse parameters if they were provided
    parameters = _parse_parameters(params) if params is not None else None

    # Update the snippet
    if storage.update_snippet(
        snippet_id,
        command=command,
        description=description,
        tags=tag_list,
        parameters=parameters,
    ):
        # Get the updated version
        updated = storage.get_snippet(snippet_id)
        if updated:
            console.print(
                f"\n[green]Successfully updated snippet:[/green] {snippet_id}"
            )

            # Show the updated snippet
            table = Table(title="Updated Snippet")
            table.add_column("Field", style="blue")
            table.add_column("Value", style="cyan")

            table.add_row("ID", snippet_id)
            table.add_row("Command", updated.command)
            table.add_row("Description", updated.description or "")
            table.add_row("Tags", ", ".join(updated.tags) if updated.tags else "")
            table.add_row("Parameters", _format_parameters(updated.parameters))

            console.print(table)
    else:
        console.print(f"[red]Failed to update snippet[/red]")


@main.command()
@click.argument("snippet_id", required=False)
@click.option(
    "--print-only", "-p", is_flag=True, help="Only print the command without executing"
)
@click.option("--edit", "-e", is_flag=True, help="Edit command before execution")
@click.option(
    "--param",
    "-P",
    multiple=True,
    help="Parameter values in name=value format. Can be specified multiple times.",
)
def exec(
    snippet_id: Optional[str] = None,
    print_only: bool = False,
    edit: bool = False,
    param: tuple[str, ...] = (),
):
    """Execute a saved snippet. If no snippet ID is provided, shows an interactive selection."""
    try:
        selected_snippet = None
        
        if snippet_id is None:
            # Show interactive snippet selection
            snippets = storage.list_snippets()
            if not snippets:
                console.print(
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
                    _format_parameters(snippet.parameters),
                )

            console.print(table)

            # Get user selection
            while True:
                try:
                    choice_str = Prompt.ask("Enter snippet number (or 'q' to quit)")
                    if choice_str.lower() == 'q':
                        return
                    choice = int(choice_str)
                    if 1 <= choice <= len(snippets):
                        selected_snippet = snippets[choice - 1][1]
                        snippet_id = snippets[choice - 1][0]
                        break
                    console.print("[red]Invalid selection[/red]")
                except (ValueError, EOFError):
                    console.print("[red]Please enter a number[/red]")
                except KeyboardInterrupt:
                    console.print("\n[yellow]Operation cancelled[/yellow]")
                    return
        else:
            # Get snippet by ID
            selected_snippet = storage.get_snippet(snippet_id)
            if not selected_snippet:
                console.print(f"[red]Snippet not found:[/red] {snippet_id}")
                raise click.ClickException(f"Snippet not found: {snippet_id}")

        # Parse provided parameter values
        param_values = {}
        for p in param:
            try:
                name, value = p.split("=", 1)
                param_values[name.strip()] = value.strip()
            except ValueError:
                console.print(
                    f"[red]Invalid parameter format:[/red] {p}. Use name=value"
                )
                return

        # If not all parameters are provided via command line, prompt for them
        if selected_snippet.parameters and len(param_values) < len(selected_snippet.parameters):
            interactive_values = _prompt_for_parameters(selected_snippet)
            param_values.update(interactive_values)

        # Apply parameters to get final command
        try:
            final_command = selected_snippet.apply_parameters(param_values)
        except ValueError as e:
            console.print(f"[red]Error:[/red] {str(e)}")
            return

        if edit:
            try:
                final_command = click.edit(final_command)
                if final_command is None:
                    console.print("[yellow]Command execution cancelled[/yellow]")
                    return
            except click.ClickException:
                # Fallback for non-interactive environments (like tests)
                console.print("[yellow]Editor not available, using original command[/yellow]")

        if print_only:
            console.print(final_command)
        else:
            import subprocess

            try:
                subprocess.run(final_command, shell=True, check=True)
            except subprocess.CalledProcessError as e:
                console.print(
                    f"[red]Command failed with exit code {e.returncode}[/red]"
                )
            except Exception as e:
                console.print(f"[red]Error executing command:[/red] {str(e)}")

    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled[/yellow]")


if __name__ == "__main__":
    main()
