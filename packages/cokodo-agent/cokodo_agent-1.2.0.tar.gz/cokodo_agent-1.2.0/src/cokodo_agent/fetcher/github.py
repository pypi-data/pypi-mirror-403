"""GitHub Release fetcher."""

import zipfile
from io import BytesIO
from pathlib import Path
from typing import Tuple

import httpx

from cokodo_agent.config import (
    DEFAULT_CACHE_DIR,
    GITHUB_API_URL,
    GITHUB_DOWNLOAD_URL,
)
from cokodo_agent.fetcher.base import (
    BaseFetcher,
    SourceUnavailableError,
)


class GitHubReleaseFetcher(BaseFetcher):
    """Fetch protocol from GitHub Release."""

    name = "GitHub Release"

    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout
        self.cache_dir = DEFAULT_CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def is_available(self) -> bool:
        """Check if GitHub API is accessible."""
        try:
            with httpx.Client(timeout=5.0) as client:
                resp = client.head("https://api.github.com")
                return resp.status_code == 200
        except Exception:
            return False

    def fetch(self) -> Tuple[Path, str]:
        """
        Fetch latest protocol from GitHub Release.

        Returns:
            Tuple of (protocol_path, version)
        """
        try:
            # Get latest release info
            version, download_url = self._get_latest_release()

            # Check cache
            cache_path = self.cache_dir / f"agent-{version}"
            if cache_path.exists():
                return cache_path / ".agent", version

            # Download and extract
            self._download_and_extract(download_url, cache_path)

            return cache_path / ".agent", version

        except httpx.RequestError as e:
            raise SourceUnavailableError(f"Network error: {e}")
        except Exception as e:
            raise SourceUnavailableError(f"GitHub fetch failed: {e}")

    def _get_latest_release(self) -> Tuple[str, str]:
        """Get latest release version and download URL."""
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.get(GITHUB_API_URL)
            resp.raise_for_status()

            data = resp.json()
            version = data["tag_name"].lstrip("v")

            # Find zipball URL
            download_url = data.get("zipball_url")
            if not download_url:
                # Fallback to constructed URL
                download_url = f"{GITHUB_DOWNLOAD_URL}/v{version}/agent-protocol-{version}.zip"

            return version, download_url

    def _download_and_extract(self, url: str, target_path: Path) -> None:
        """Download zip and extract to target path."""
        with httpx.Client(timeout=30.0, follow_redirects=True) as client:
            resp = client.get(url)
            resp.raise_for_status()

            # Extract zip
            with zipfile.ZipFile(BytesIO(resp.content)) as zf:
                # GitHub zipball has a root folder, we need to handle that
                members = zf.namelist()
                if members:
                    # Find the root folder name
                    root_folder = members[0].split("/")[0]

                    target_path.mkdir(parents=True, exist_ok=True)

                    for member in members:
                        # Skip the root folder itself
                        if member == root_folder + "/":
                            continue

                        # Remove root folder prefix
                        relative_path = member[len(root_folder) + 1 :]
                        if not relative_path:
                            continue

                        target_file = target_path / relative_path

                        if member.endswith("/"):
                            target_file.mkdir(parents=True, exist_ok=True)
                        else:
                            target_file.parent.mkdir(parents=True, exist_ok=True)
                            with zf.open(member) as src, open(target_file, "wb") as dst:
                                dst.write(src.read())
