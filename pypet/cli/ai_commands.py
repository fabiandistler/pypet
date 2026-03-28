"""Commands for generating snippets with OpenRouter."""

from __future__ import annotations

from typing import Any

import click
from rich.prompt import Confirm, Prompt
from rich.table import Table

from ..ai import OpenRouterAIError, generate_snippet
from ..alias_manager import AliasManager
from ..config import Config
from ..models import Parameter, Snippet
from . import main_module as cli_main
from .main import _auto_sync_if_enabled, main


def _build_snippet_from_generated(data: dict[str, Any]) -> Snippet:
    parameters = None
    raw_parameters = data.get("parameters")
    if isinstance(raw_parameters, dict):
        parameters = {
            name: Parameter(
                name=param.get("name") or name,
                default=param.get("default"),
                description=param.get("description"),
            )
            for name, param in raw_parameters.items()
            if isinstance(param, dict)
        }

    return Snippet(
        command=data["command"],
        description=data.get("description"),
        tags=data.get("tags"),
        parameters=parameters,
    )


@main.command(name="gen")
@click.argument("prompt")
def gen(prompt: str) -> None:
    """Generate a snippet from a natural language prompt."""
    cfg = Config()

    api_key = cfg.resolve_openrouter_api_key()
    if not api_key:
        api_key = Prompt.ask("OpenRouter API key", password=True).strip()
        if not api_key:
            cli_main.console.print("[red]Error:[/red] OpenRouter API key is required.")
            return
        cfg.openrouter_api_key = api_key

    # Generate
    try:
        with cli_main.console.status("Generating snippet..."):
            generated = generate_snippet(prompt=prompt, config=cfg)
    except OpenRouterAIError as e:
        cli_main.console.print(f"[red]Error:[/red] {e}")
        return

    snippet = _build_snippet_from_generated(generated)

    table = Table(title="Generated Snippet")
    table.add_column("Field", style="blue")
    table.add_column("Value", style="cyan")
    table.add_row("Command", snippet.command)
    table.add_row("Description", snippet.description or "")
    table.add_row("Tags", ", ".join(snippet.tags or []) if snippet.tags else "")
    table.add_row("Parameters", ", ".join(snippet.get_all_parameters().keys()))
    cli_main.console.print(table)

    if not Confirm.ask("Save this as a snippet?", default=True):
        cli_main.console.print("[yellow]Not saved.[/yellow]")
        return

    alias_input = Prompt.ask("Optional alias (press enter to skip)", default="")
    alias = alias_input.strip() or None

    snippet_id = cli_main.storage.add_snippet(
        command=snippet.command,
        description=snippet.description,
        tags=snippet.tags,
        parameters=snippet.parameters,
        alias=alias,
    )

    cli_main.console.print(f"[green]Added new snippet with ID:[/green] {snippet_id}")

    if alias:
        alias_manager = AliasManager()
        alias_manager.update_aliases_file(cli_main.storage.get_snippets_with_aliases())
        cli_main.console.print(f"[green]✓ Created alias:[/green] {alias}")
        cli_main.console.print(
            f"[dim]Run this to activate:[/dim] source {alias_manager.alias_path}"
        )

    _auto_sync_if_enabled()
