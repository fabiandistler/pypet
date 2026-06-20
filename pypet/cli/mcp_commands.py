"""Command to run pypet as an MCP server for AI agents."""

import click

from .main import main


@main.command("mcp")
def mcp() -> None:
    """Run pypet as an MCP server (stdio) so AI agents can search and save snippets.

    Register it with an MCP client, e.g. for Claude Code:

        claude mcp add pypet -- pypet mcp

    Requires the optional "mcp" extra: pip install "pypet-cli[mcp]"
    """
    try:
        from ..mcp_server import run  # noqa: PLC0415
    except ImportError:
        click.echo(
            'The pypet MCP server needs the "mcp" extra. '
            'Install it with: pip install "pypet-cli[mcp]"',
            err=True,
        )
        raise SystemExit(1)

    run()
