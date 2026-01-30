"""Base class for protocol fetchers."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Tuple


class BaseFetcher(ABC):
    """Abstract base class for protocol fetchers."""

    name: str = "Base"

    @abstractmethod
    def fetch(self) -> Tuple[Path, str]:
        """
        Fetch protocol files.

        Returns:
            Tuple of (protocol_path, version)

        Raises:
            FetcherError: If fetching fails
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this fetcher source is available."""
        pass


class FetcherError(Exception):
    """Base exception for fetcher errors."""

    pass


class SourceUnavailableError(FetcherError):
    """Source is unavailable."""

    pass


class SourceNotConfiguredError(FetcherError):
    """Source is not configured."""

    pass
