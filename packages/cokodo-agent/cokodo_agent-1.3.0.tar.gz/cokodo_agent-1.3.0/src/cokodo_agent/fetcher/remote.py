"""Remote server fetcher - Reserved for future implementation."""

from pathlib import Path
from typing import Tuple

from cokodo_agent.config import REMOTE_SERVER_URL
from cokodo_agent.fetcher.base import (
    BaseFetcher,
    SourceNotConfiguredError,
)


class RemoteServerFetcher(BaseFetcher):
    """
    Fetch protocol from self-hosted remote server.

    Reserved for future implementation.
    Users can configure via COKODO_REMOTE_SERVER environment variable.
    """

    name = "Remote Server"

    def __init__(self) -> None:
        self.base_url = REMOTE_SERVER_URL

    def is_available(self) -> bool:
        """Check if remote server is configured and accessible."""
        # Not implemented yet
        return False

    def fetch(self) -> Tuple[Path, str]:
        """
        Fetch protocol from remote server.

        This feature is reserved for future implementation.
        """
        if not self.base_url:
            raise SourceNotConfiguredError(
                "Remote server not configured. " "Set COKODO_REMOTE_SERVER environment variable."
            )

        raise NotImplementedError(
            "Remote server support is reserved for future implementation. "
            "Please use GitHub Release or built-in protocol."
        )
