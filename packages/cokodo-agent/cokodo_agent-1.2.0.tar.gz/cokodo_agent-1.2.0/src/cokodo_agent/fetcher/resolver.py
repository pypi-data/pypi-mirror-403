"""Protocol source resolver with priority fallback."""

from pathlib import Path
from typing import List, Tuple

from rich.console import Console

from cokodo_agent.fetcher.base import BaseFetcher, FetcherError
from cokodo_agent.fetcher.builtin import BuiltinFetcher
from cokodo_agent.fetcher.github import GitHubReleaseFetcher

console = Console()


def get_protocol(offline: bool = False) -> Tuple[Path, str]:
    """
    Get protocol from available sources with priority fallback.

    Priority:
        1. GitHub Release (latest version)
        2. Remote Server (reserved, not implemented)
        3. Built-in (offline fallback)

    Args:
        offline: If True, skip network sources and use built-in directly

    Returns:
        Tuple of (protocol_path, version)

    Raises:
        FetcherError: If all sources fail
    """

    if offline:
        # Directly use built-in
        console.print("  [dim]Using offline mode[/dim]")
        fetcher = BuiltinFetcher()
        return fetcher.fetch()

    # Define sources with priority
    sources: List[BaseFetcher] = [
        GitHubReleaseFetcher(),  # Priority 1
        # RemoteServerFetcher(),  # Priority 2 (reserved)
        BuiltinFetcher(),  # Priority 3 (fallback)
    ]

    errors = []

    for i, source in enumerate(sources, 1):
        source_label = f"[{i}/{len(sources)}] {source.name}"

        try:
            console.print(f"  {source_label}...", end=" ")

            path, version = source.fetch()
            console.print(f"[green]OK[/green] (v{version})")

            return path, version

        except FetcherError as e:
            console.print("[yellow]unavailable[/yellow]")
            errors.append(f"{source.name}: {e}")
            continue
        except Exception as e:
            console.print("[red]error[/red]")
            errors.append(f"{source.name}: {e}")
            continue

    # All sources failed
    error_details = "\n".join(f"  - {err}" for err in errors)
    raise FetcherError(f"All protocol sources failed:\n{error_details}")
