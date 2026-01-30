"""CLI commands for cokodo-agent."""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from cokodo_agent.config import BUNDLED_PROTOCOL_VERSION, VERSION
from cokodo_agent.fetcher import get_protocol
from cokodo_agent.generator import generate_protocol
from cokodo_agent.prompts import prompt_config

app = typer.Typer(
    name="cokodo",
    help="Cokodo Agent - AI collaboration protocol generator",
    add_completion=False,
)
console = Console()


def find_agent_dir(path: Optional[Path] = None) -> Path:
    """Find .agent directory from given path or current directory."""
    target = Path(path) if path else Path.cwd()
    target = target.resolve()

    agent_dir = target / ".agent"
    if agent_dir.exists():
        return agent_dir

    raise FileNotFoundError(f".agent directory not found at {target}")


@app.command()
def init(
    path: Optional[Path] = typer.Argument(
        None,
        help="Target directory (default: current directory)",
    ),
    yes: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Skip prompts, use defaults",
    ),
    name: Optional[str] = typer.Option(
        None,
        "--name",
        "-n",
        help="Project name",
    ),
    stack: Optional[str] = typer.Option(
        None,
        "--stack",
        "-s",
        help="Tech stack (python/rust/qt/mixed/other)",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite existing .agent directory",
    ),
    offline: bool = typer.Option(
        False,
        "--offline",
        help="Use built-in protocol (no network)",
    ),
) -> None:
    """Create .agent protocol in target directory."""

    # Header
    console.print()
    console.print(
        Panel.fit(
            f"[bold blue]Cokodo Agent[/bold blue] v{VERSION}",
            border_style="blue",
        )
    )
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
        console.print("  [green]OK[/green] Created .agent/")
    except Exception as e:
        console.print(f"  [red]Error:[/red] {e}")
        raise typer.Exit(1)

    console.print()

    # Success message
    console.print(
        Panel(
            f"[green]Success![/green] Created .agent in [bold]{target_path}[/bold]\n\n"
            "[bold]Next steps:[/bold]\n"
            "  1. Review [cyan].agent/project/context.md[/cyan]\n"
            "  2. Customize [cyan].agent/project/tech-stack.md[/cyan]\n"
            "  3. Start coding with AI assistance!",
            title="Done",
            border_style="green",
        )
    )


@app.command()
def lint(
    path: Optional[Path] = typer.Argument(
        None,
        help="Path to project (default: current directory)",
    ),
    rule: Optional[str] = typer.Option(
        None,
        "--rule",
        "-r",
        help="Check specific rule only",
    ),
    format: str = typer.Option(
        "text",
        "--format",
        "-f",
        help="Output format (text/json/github)",
    ),
) -> None:
    """Check protocol compliance."""
    import json as json_module

    from cokodo_agent.linter import ProtocolLinter

    try:
        agent_dir = find_agent_dir(path)
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

    linter = ProtocolLinter(agent_dir)

    if rule:
        results = linter.lint_rule(rule)
    else:
        results = linter.lint_all()

    errors = [r for r in results if not r.passed]

    if format == "json":
        print(json_module.dumps([r._asdict() for r in results], indent=2, ensure_ascii=False))

    elif format == "github":
        for r in results:
            if not r.passed:
                file_part = f"file={r.file}" if r.file else ""
                line_part = f",line={r.line}" if r.line else ""
                print(f"::error {file_part}{line_part}::[{r.rule}] {r.message}")
        if not errors:
            print("::notice ::All protocol checks passed")

    else:  # text format
        console.print()
        console.print(
            Panel.fit(
                "[bold]Protocol Compliance Check[/bold]\n"
                "Based on: agent-protocol-rules.md v3.0.0",
                border_style="blue",
            )
        )
        console.print()

        # Group by rule
        rules = sorted(set(r.rule for r in results))
        for rule_name in rules:
            rule_results = [r for r in results if r.rule == rule_name]
            passed = sum(1 for r in rule_results if r.passed)
            total = len(rule_results)

            if passed == total:
                console.print(f"[green][OK][/green] {rule_name}: {passed}/{total} passed")
            else:
                console.print(f"[red][FAIL][/red] {rule_name}: {passed}/{total} passed")

                # Show errors
                for r in rule_results:
                    if not r.passed:
                        loc = f"  {r.file}" if r.file else ""
                        if r.line:
                            loc += f":{r.line}"
                        console.print(f"    [red]x[/red]{loc}: {r.message}")

        console.print()
        total_passed = len(results) - len(errors)
        console.print(f"Total: {total_passed}/{len(results)} passed")

        if errors:
            console.print(f"\n[red][FAIL][/red] {len(errors)} error(s) found")
            raise typer.Exit(1)
        else:
            console.print("\n[green][OK][/green] All checks passed")


@app.command("update-checksums")
def update_checksums(
    path: Optional[Path] = typer.Argument(
        None,
        help="Path to project (default: current directory)",
    ),
) -> None:
    """Update checksums in manifest.json (maintainer only)."""
    from cokodo_agent.linter import update_checksums as do_update

    try:
        agent_dir = find_agent_dir(path)
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

    try:
        checksums = do_update(agent_dir)
        console.print(f"[green]OK[/green] Updated checksums for {len(checksums)} locked files")
        console.print(f"    Written to {agent_dir / 'manifest.json'}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def diff(
    path: Optional[Path] = typer.Argument(
        None,
        help="Path to project (default: current directory)",
    ),
    offline: bool = typer.Option(
        False,
        "--offline",
        help="Use built-in protocol (no network)",
    ),
) -> None:
    """Compare local .agent with latest protocol."""
    from cokodo_agent.sync import diff_protocol

    try:
        agent_dir = find_agent_dir(path)
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

    console.print("[bold]Comparing with latest protocol...[/bold]")
    console.print()

    try:
        results, local_version, remote_version = diff_protocol(agent_dir, offline=offline)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

    console.print(f"Local version:  [cyan]{local_version}[/cyan]")
    console.print(f"Remote version: [cyan]{remote_version}[/cyan]")
    console.print()

    # Count changes
    added = [r for r in results if r.status == "added"]
    removed = [r for r in results if r.status == "removed"]
    modified = [r for r in results if r.status == "modified"]
    unchanged = [r for r in results if r.status == "unchanged"]

    if not added and not removed and not modified:
        console.print("[green]No changes detected. Protocol is up to date.[/green]")
        return

    # Show summary
    table = Table(title="Changes")
    table.add_column("Status", style="bold")
    table.add_column("Count")

    if added:
        table.add_row("[green]Added[/green]", str(len(added)))
    if removed:
        table.add_row("[red]Removed[/red]", str(len(removed)))
    if modified:
        table.add_row("[yellow]Modified[/yellow]", str(len(modified)))
    table.add_row("Unchanged", str(len(unchanged)))

    console.print(table)
    console.print()

    # Show details
    if added:
        console.print("[green]Added files:[/green]")
        for r in added:
            console.print(f"  + {r.path}")
        console.print()

    if removed:
        console.print("[red]Removed files:[/red]")
        for r in removed:
            console.print(f"  - {r.path}")
        console.print()

    if modified:
        console.print("[yellow]Modified files:[/yellow]")
        for r in modified:
            console.print(f"  ~ {r.path}")
        console.print()

    console.print("Run [cyan]co sync[/cyan] to update your protocol.")


@app.command()
def sync(
    path: Optional[Path] = typer.Argument(
        None,
        help="Path to project (default: current directory)",
    ),
    offline: bool = typer.Option(
        False,
        "--offline",
        help="Use built-in protocol (no network)",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show what would be updated without making changes",
    ),
    yes: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Skip confirmation prompt",
    ),
) -> None:
    """Sync local .agent with latest protocol."""
    from cokodo_agent.sync import diff_protocol, sync_protocol

    try:
        agent_dir = find_agent_dir(path)
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

    # First show diff
    console.print("[bold]Checking for updates...[/bold]")
    console.print()

    try:
        diff_results, local_version, remote_version = diff_protocol(agent_dir, offline=offline)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

    console.print(f"Local version:  [cyan]{local_version}[/cyan]")
    console.print(f"Remote version: [cyan]{remote_version}[/cyan]")
    console.print()

    # Count changes (excluding project/ files)
    changes = [
        r for r in diff_results if r.status != "unchanged" and not r.path.startswith("project/")
    ]

    if not changes:
        console.print("[green]Protocol is up to date. No changes needed.[/green]")
        return

    console.print(f"[yellow]{len(changes)} file(s) will be updated[/yellow]")
    console.print()

    # Confirm
    if not yes and not dry_run:
        confirm = typer.confirm("Proceed with sync?")
        if not confirm:
            console.print("Aborted.")
            raise typer.Exit(0)

    # Sync
    if dry_run:
        console.print("[bold]Dry run - no changes will be made[/bold]")
        console.print()

    try:
        result, _, _ = sync_protocol(agent_dir, offline=offline, dry_run=dry_run)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

    # Show results
    if result.updated:
        console.print("[green]Updated:[/green]")
        for f in result.updated:
            console.print(f"  {f}")
        console.print()

    if result.skipped:
        console.print("[yellow]Skipped:[/yellow]")
        for f in result.skipped:
            console.print(f"  {f}")
        console.print()

    if result.errors:
        console.print("[red]Errors:[/red]")
        for err in result.errors:
            console.print(f"  {err}")
        raise typer.Exit(1)

    if not dry_run:
        console.print(f"[green]OK[/green] Synced to v{remote_version}")


@app.command()
def context(
    path: Optional[Path] = typer.Argument(
        None,
        help="Path to project (default: current directory)",
    ),
    stack: Optional[str] = typer.Option(
        None,
        "--stack",
        "-s",
        help="Tech stack (python/rust/qt/mixed)",
    ),
    task: Optional[str] = typer.Option(
        None,
        "--task",
        "-t",
        help="Task type (coding/testing/review/documentation/bug_fix/feature_development)",
    ),
    output: str = typer.Option(
        "list",
        "--output",
        "-o",
        help="Output format (list/paths/content)",
    ),
) -> None:
    """Get context files based on stack and task type."""
    from cokodo_agent.sync import get_context_files

    try:
        agent_dir = find_agent_dir(path)
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

    files = get_context_files(agent_dir, stack=stack, task=task)

    if not files:
        console.print("[yellow]No context files found for the given criteria.[/yellow]")
        return

    if output == "paths":
        # Output absolute paths, one per line (for scripting)
        for f in files:
            print(agent_dir / f)

    elif output == "content":
        # Output file contents (for piping to AI)
        for f in files:
            file_path = agent_dir / f
            if file_path.exists():
                console.print(f"[bold]# {f}[/bold]")
                console.print(file_path.read_text(encoding="utf-8"))
                console.print()

    else:  # list
        console.print(
            f"[bold]Context files for stack={stack or 'all'}, task={task or 'all'}:[/bold]"
        )
        console.print()
        for f in files:
            file_path = agent_dir / f
            exists = "[green]OK[/green]" if file_path.exists() else "[red]MISSING[/red]"
            console.print(f"  {exists} {f}")


@app.command()
def journal(
    path: Optional[Path] = typer.Argument(
        None,
        help="Path to project (default: current directory)",
    ),
    title: Optional[str] = typer.Option(
        None,
        "--title",
        "-t",
        help="Session title (e.g., 'Feature X implementation')",
    ),
    completed: Optional[str] = typer.Option(
        None,
        "--completed",
        "-c",
        help="Completed items (comma-separated)",
    ),
    debt: Optional[str] = typer.Option(
        None,
        "--debt",
        "-d",
        help="Technical debt items (comma-separated)",
    ),
    decisions: Optional[str] = typer.Option(
        None,
        "--decisions",
        help="Key decisions made (comma-separated)",
    ),
    interactive: bool = typer.Option(
        False,
        "--interactive",
        "-i",
        help="Interactive mode with prompts",
    ),
) -> None:
    """Record a session entry to session-journal.md."""
    from datetime import datetime

    import questionary

    try:
        agent_dir = find_agent_dir(path)
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

    journal_path = agent_dir / "project" / "session-journal.md"
    if not journal_path.exists():
        console.print(f"[red]Error:[/red] session-journal.md not found at {journal_path}")
        raise typer.Exit(1)

    # Interactive mode
    if interactive or (not title and not completed):
        console.print()
        console.print(
            Panel.fit(
                "[bold blue]Session Journal Entry[/bold blue]",
                border_style="blue",
            )
        )
        console.print()

        title = questionary.text(
            "Session title:",
            default=title or "",
        ).ask()

        if not title:
            console.print("[yellow]Aborted.[/yellow]")
            raise typer.Exit(0)

        completed_input = questionary.text(
            "Completed items (comma-separated):",
            default=completed or "",
        ).ask()

        debt_input = questionary.text(
            "Technical debt (comma-separated, or leave empty):",
            default=debt or "",
        ).ask()

        decisions_input = questionary.text(
            "Key decisions (comma-separated, or leave empty):",
            default=decisions or "",
        ).ask()

        completed = completed_input
        debt = debt_input
        decisions = decisions_input

    # Build entry
    today = datetime.now().strftime("%Y-%m-%d")

    entry_lines = [
        f"\n## {today} Session: {title}",
        "",
        "### Completed",
    ]

    if completed:
        for item in completed.split(","):
            item = item.strip()
            if item:
                entry_lines.append(f"- {item}")
    else:
        entry_lines.append("- (no items recorded)")

    entry_lines.append("")
    entry_lines.append("### Technical Debt")

    if debt:
        for item in debt.split(","):
            item = item.strip()
            if item:
                entry_lines.append(f"- {item}")
    else:
        entry_lines.append("- None")

    entry_lines.append("")
    entry_lines.append("### Decisions")

    if decisions:
        for item in decisions.split(","):
            item = item.strip()
            if item:
                entry_lines.append(f"- {item}")
    else:
        entry_lines.append("- (no decisions recorded)")

    entry_lines.append("")
    entry_lines.append("---")
    entry_lines.append("")

    entry_text = "\n".join(entry_lines)

    # Append to journal
    try:
        content = journal_path.read_text(encoding="utf-8")

        # Find the append marker
        marker = "*Append new sessions below this line.*"
        if marker in content:
            content = content.replace(marker, marker + entry_text)
        else:
            # Just append at the end
            content = content.rstrip() + "\n" + entry_text

        journal_path.write_text(content, encoding="utf-8")

        console.print()
        console.print(f"[green]OK[/green] Added session entry to {journal_path}")
        console.print()
        console.print("[bold]Entry preview:[/bold]")
        console.print(entry_text)

    except Exception as e:
        console.print(f"[red]Error:[/red] Failed to write journal: {e}")
        raise typer.Exit(1)


@app.command()
def version() -> None:
    """Show version information."""
    console.print(f"cokodo-agent v{VERSION}")
    console.print()
    console.print("Protocol versions:")
    console.print(f"  Built-in: v{BUNDLED_PROTOCOL_VERSION}")


@app.command()
def help(
    command: Optional[str] = typer.Argument(
        None,
        help="Command to get help for",
    ),
) -> None:
    """Show help information for commands."""
    commands_info = {
        "init": {
            "description": "Create .agent protocol in target directory",
            "usage": "co init [PATH] [OPTIONS]",
            "options": [
                ("-y, --yes", "Skip prompts, use defaults"),
                ("-n, --name", "Project name"),
                ("-s, --stack", "Tech stack (python/rust/qt/mixed/other)"),
                ("-f, --force", "Overwrite existing .agent directory"),
                ("--offline", "Use built-in protocol (no network)"),
            ],
            "examples": [
                ("co init", "Initialize in current directory with prompts"),
                ("co init -y", "Initialize with defaults"),
                ("co init ./myproject -n MyApp -s python", "Initialize with options"),
                ("co init --offline", "Initialize using built-in protocol"),
            ],
        },
        "lint": {
            "description": "Check protocol compliance against rules",
            "usage": "co lint [PATH] [OPTIONS]",
            "options": [
                ("-r, --rule", "Check specific rule only"),
                ("-f, --format", "Output format (text/json/github)"),
            ],
            "examples": [
                ("co lint", "Check current directory"),
                ("co lint -r integrity-violation", "Check specific rule"),
                ("co lint -f json", "Output as JSON"),
                ("co lint -f github", "Output for GitHub Actions"),
            ],
        },
        "diff": {
            "description": "Compare local .agent with latest protocol",
            "usage": "co diff [PATH] [OPTIONS]",
            "options": [
                ("--offline", "Use built-in protocol (no network)"),
            ],
            "examples": [
                ("co diff", "Show differences with latest"),
                ("co diff --offline", "Compare with built-in protocol"),
            ],
        },
        "sync": {
            "description": "Sync local .agent with latest protocol",
            "usage": "co sync [PATH] [OPTIONS]",
            "options": [
                ("--offline", "Use built-in protocol (no network)"),
                ("--dry-run", "Show what would be updated"),
                ("-y, --yes", "Skip confirmation prompt"),
            ],
            "examples": [
                ("co sync", "Sync with confirmation"),
                ("co sync -y", "Sync without confirmation"),
                ("co sync --dry-run", "Preview changes"),
            ],
        },
        "context": {
            "description": "Get context files based on stack and task type",
            "usage": "co context [PATH] [OPTIONS]",
            "options": [
                ("-s, --stack", "Tech stack (python/rust/qt/mixed)"),
                ("-t, --task", "Task type (coding/testing/review/...)"),
                ("-o, --output", "Output format (list/paths/content)"),
            ],
            "examples": [
                ("co context", "List all context files"),
                ("co context -s python", "Files for Python stack"),
                ("co context -t testing", "Files for testing task"),
                ("co context -o content", "Output file contents"),
            ],
        },
        "journal": {
            "description": "Record a session entry to session-journal.md",
            "usage": "co journal [PATH] [OPTIONS]",
            "options": [
                ("-t, --title", "Session title"),
                ("-c, --completed", "Completed items (comma-separated)"),
                ("-d, --debt", "Technical debt items"),
                ("--decisions", "Key decisions made"),
                ("-i, --interactive", "Interactive mode with prompts"),
            ],
            "examples": [
                ("co journal -i", "Interactive mode"),
                ('co journal -t "Feature X" -c "Task 1, Task 2"', "Quick entry"),
            ],
        },
        "update-checksums": {
            "description": "Update checksums in manifest.json (maintainer only)",
            "usage": "co update-checksums [PATH]",
            "options": [],
            "examples": [
                ("co update-checksums", "Update checksums"),
            ],
        },
        "version": {
            "description": "Show version information",
            "usage": "co version",
            "options": [],
            "examples": [
                ("co version", "Show version"),
            ],
        },
        "help": {
            "description": "Show help information for commands",
            "usage": "co help [COMMAND]",
            "options": [],
            "examples": [
                ("co help", "Show all commands"),
                ("co help init", "Show help for init command"),
            ],
        },
    }

    if command:
        # Show help for specific command
        if command not in commands_info:
            console.print(f"[red]Error:[/red] Unknown command '{command}'")
            console.print()
            console.print("Available commands:")
            for cmd in commands_info:
                console.print(f"  {cmd}")
            raise typer.Exit(1)

        info = commands_info[command]
        console.print()
        console.print(Panel.fit(f"[bold blue]co {command}[/bold blue]", border_style="blue"))
        console.print()
        console.print(f"[bold]Description:[/bold] {info['description']}")
        console.print()
        console.print(f"[bold]Usage:[/bold] {info['usage']}")

        if info["options"]:
            console.print()
            console.print("[bold]Options:[/bold]")
            for opt, desc in info["options"]:
                console.print(f"  [cyan]{opt:20}[/cyan] {desc}")

        console.print()
        console.print("[bold]Examples:[/bold]")
        for example, desc in info["examples"]:
            console.print(f"  [green]{example}[/green]")
            console.print(f"    {desc}")

    else:
        # Show overview of all commands
        console.print()
        console.print(
            Panel.fit(
                f"[bold blue]Cokodo Agent[/bold blue] v{VERSION}\n"
                "AI Collaboration Protocol Generator",
                border_style="blue",
            )
        )
        console.print()
        console.print("[bold]Commands:[/bold]")
        console.print()

        # Group commands by category
        categories = {
            "Setup": ["init"],
            "Protocol Management": ["lint", "diff", "sync", "update-checksums"],
            "Development": ["context", "journal"],
            "Information": ["version", "help"],
        }

        for category, cmds in categories.items():
            console.print(f"  [bold cyan]{category}[/bold cyan]")
            for cmd in cmds:
                if cmd in commands_info:
                    desc = commands_info[cmd]["description"]
                    console.print(f"    [green]{cmd:18}[/green] {desc}")
            console.print()

        console.print("[bold]Usage:[/bold]")
        console.print("  co <command> [options]")
        console.print()
        console.print("[bold]Get help for a command:[/bold]")
        console.print("  co help <command>")
        console.print()
        console.print("[bold]Quick start:[/bold]")
        console.print("  co init          # Create .agent in current directory")
        console.print("  co lint          # Check protocol compliance")
        console.print("  co sync          # Update to latest protocol")
        console.print()
        console.print("Documentation: https://github.com/dinwind/agent_protocol")


if __name__ == "__main__":
    app()
