"""MCP (Model Context Protocol) commands for server management.

Extracted from cli.py as part of EPIC-003 CLI Architecture Refactor.
"""

from __future__ import annotations

import json
import sys

import typer
from rich.console import Console
from rich.table import Table

# Initialize Rich console
console = Console()


def print_json(data: dict) -> None:
    """Print JSON to stdout without Rich formatting."""
    sys.stdout.write(json.dumps(data, indent=2))
    sys.stdout.write("\n")
    sys.stdout.flush()


# MCP sub-app
app = typer.Typer(
    help="MCP (Model Context Protocol) server commands",
    context_settings={"help_option_names": ["-h", "--help"]}
)


@app.command("serve")
def mcp_serve(
    transport: str = typer.Option("stdio", "--transport", "-t", help="Transport: stdio or sse"),
    port: int = typer.Option(3000, "--port", "-p", help="Port for SSE transport"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
):
    """Start MCP server for Claude and other MCP-compatible agents."""
    try:
        from ..mcp.server import run_server
    except ImportError:
        try:
            from bpsai_pair.mcp.server import run_server
        except ImportError:
            console.print("[red]MCP package not installed.[/red]")
            console.print("[dim]Install with: pip install 'bpsai-pair[mcp]'[/dim]")
            raise typer.Exit(1)

    if verbose:
        console.print(f"[dim]Starting MCP server on {transport}...[/dim]")

    try:
        run_server(transport=transport, port=port)
    except ImportError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command("tools")
def mcp_tools(
    json_out: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """List available MCP tools."""
    try:
        from ..mcp.server import list_tools
    except ImportError:
        from bpsai_pair.mcp.server import list_tools

    tools = list_tools()

    if json_out:
        print_json({"tools": tools, "count": len(tools)})
    else:
        table = Table(title="Available MCP Tools")
        table.add_column("Tool", style="cyan")
        table.add_column("Description")
        table.add_column("Parameters", style="dim")

        for tool in tools:
            params = ", ".join(tool["parameters"]) if tool["parameters"] else "-"
            table.add_row(tool["name"], tool["description"], params)

        console.print(table)


@app.command("test")
def mcp_test(
    tool: str = typer.Argument(..., help="Tool name to test"),
    input_json: str = typer.Argument("{}", help="JSON input for the tool"),
    json_out: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Test an MCP tool locally."""
    import asyncio

    try:
        input_data = json.loads(input_json)
    except json.JSONDecodeError as e:
        console.print(f"[red]Invalid JSON: {e}[/red]")
        raise typer.Exit(1)

    try:
        from ..mcp.server import test_tool
    except ImportError:
        try:
            from bpsai_pair.mcp.server import test_tool
        except ImportError:
            console.print("[red]MCP package not installed.[/red]")
            console.print("[dim]Install with: pip install 'bpsai-pair[mcp]'[/dim]")
            raise typer.Exit(1)

    try:
        result = asyncio.run(test_tool(tool, input_data))

        if json_out:
            print_json(result)
        else:
            console.print(f"[bold]Tool:[/bold] {tool}")
            console.print(f"[bold]Input:[/bold] {input_data}")
            console.print("[bold]Result:[/bold]")
            console.print_json(data=result)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
