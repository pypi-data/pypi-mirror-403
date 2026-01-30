"""Built-in protocol fetcher."""

from pathlib import Path
from typing import Tuple

from cokodo_agent.config import BUNDLED_PROTOCOL_VERSION
from cokodo_agent.fetcher.base import (
    BaseFetcher,
    SourceUnavailableError,
)


class BuiltinFetcher(BaseFetcher):
    """Fetch protocol from bundled files in the package."""

    name = "Built-in"

    def __init__(self) -> None:
        # Get the bundled directory path
        self.bundled_path = Path(__file__).parent.parent / "bundled" / "agent"

    def is_available(self) -> bool:
        """Check if bundled protocol exists."""
        manifest_exists = self.bundled_path.exists() and (self.bundled_path / "start-here.md").exists()
        return bool(manifest_exists)

    def fetch(self) -> Tuple[Path, str]:
        """
        Return path to bundled protocol.

        Returns:
            Tuple of (protocol_path, version)
        """
        if not self.is_available():
            raise SourceUnavailableError(
                "Built-in protocol not found. " "The package may be corrupted. Please reinstall."
            )

        return self.bundled_path, BUNDLED_PROTOCOL_VERSION
