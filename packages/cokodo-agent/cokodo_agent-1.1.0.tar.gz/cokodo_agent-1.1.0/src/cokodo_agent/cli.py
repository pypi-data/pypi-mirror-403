"""CLI commands for cokodo-agent."""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

from cokodo_agent import __version__
from cokodo_agent.config import VERSION, BUNDLED_PROTOCOL_VERSION
from cokodo_agent.generator import generate_protocol
from cokodo_agent.prompts import prompt_config
from cokodo_agent.fetcher import get_protocol

app = typer.Typer(
    name="cokodo",
    help="Cokodo Agent - AI collaboration protocol generator",
    add_completion=False,
)
console = Console()


@app.command()
def init(
    path: Optional[Path] = typer.Argument(
        None,
        help="Target directory (default: current directory)",
    ),
    yes: bool = typer.Option(
        False,
        "--yes", "-y",
        help="Skip prompts, use defaults",
    ),
    name: Optional[str] = typer.Option(
        None,
        "--name", "-n",
        help="Project name",
    ),
    stack: Optional[str] = typer.Option(
        None,
        "--stack", "-s",
        help="Tech stack (python/rust/qt/mixed/other)",
    ),
    force: bool = typer.Option(
        False,
        "--force", "-f",
        help="Overwrite existing .agent directory",
    ),
    offline: bool = typer.Option(
        False,
        "--offline",
        help="Use built-in protocol (no network)",
    ),
):
    """Create .agent protocol in target directory."""
    
    # Header
    console.print()
    console.print(Panel.fit(
        f"[bold blue]Cokodo Agent[/bold blue] v{VERSION}",
        border_style="blue",
    ))
    console.print()
    
    # Resolve target path
    target_path = Path(path) if path else Path.cwd()
    target_path = target_path.resolve()
    
    # Check existing .agent
    agent_dir = target_path / ".agent"
    if agent_dir.exists() and not force:
        console.print(f"[red]Error:[/red] .agent already exists at {agent_dir}")
        console.print("Use --force to overwrite")
        raise typer.Exit(1)
    
    # Fetch protocol
    console.print("[bold]Fetching protocol...[/bold]")
    try:
        protocol_path, protocol_version = get_protocol(offline=offline)
        console.print(f"  [green]OK[/green] Protocol v{protocol_version}")
    except Exception as e:
        console.print(f"  [red]Error:[/red] {e}")
        raise typer.Exit(1)
    
    console.print()
    
    # Get configuration
    if yes:
        # Use defaults or provided options
        config = {
            "project_name": name or target_path.name,
            "description": "",
            "tech_stack": stack or "python",
            "ai_tools": ["cokodo"],  # Default: protocol only, no extra files
        }
    else:
        # Interactive prompts
        config = prompt_config(
            default_name=name or target_path.name,
            default_stack=stack,
        )
    
    console.print()
    
    # Generate
    console.print("[bold]Generating .agent/[/bold]")
    try:
        generate_protocol(
            source_path=protocol_path,
            target_path=target_path,
            config=config,
            force=force,
        )
        console.print(f"  [green]OK[/green] Created .agent/")
    except Exception as e:
        console.print(f"  [red]Error:[/red] {e}")
        raise typer.Exit(1)
    
    console.print()
    
    # Success message
    console.print(Panel(
        f"[green]Success![/green] Created .agent in [bold]{target_path}[/bold]\n\n"
        "[bold]Next steps:[/bold]\n"
        "  1. Review [cyan].agent/project/context.md[/cyan]\n"
        "  2. Customize [cyan].agent/project/tech-stack.md[/cyan]\n"
        "  3. Start coding with AI assistance!",
        title="Done",
        border_style="green",
    ))


@app.command()
def version():
    """Show version information."""
    console.print(f"cokodo-agent v{VERSION}")
    console.print()
    console.print("Protocol versions:")
    console.print(f"  Built-in: v{BUNDLED_PROTOCOL_VERSION}")


if __name__ == "__main__":
    app()
