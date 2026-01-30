"""Configuration constants."""

import os
from pathlib import Path
from typing import TypedDict


class AIToolInfo(TypedDict):
    """Type definition for AI tool configuration."""

    name: str
    file: str | None
    template: str | None


# Version
VERSION = "1.3.0"
BUNDLED_PROTOCOL_VERSION = "3.0.0"

# GitHub Release
GITHUB_REPO = "dinwind/agent_protocol"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
GITHUB_DOWNLOAD_URL = f"https://github.com/{GITHUB_REPO}/releases/download"

# Remote Server (reserved for future)
REMOTE_SERVER_URL = os.environ.get("COKODO_REMOTE_SERVER", "")

# Cache
DEFAULT_CACHE_DIR = Path(
    os.environ.get(
        "COKODO_CACHE_DIR",
        (
            Path.home() / ".cache" / "cokodo"
            if os.name != "nt"
            else Path(os.environ.get("LOCALAPPDATA", Path.home())) / "cokodo" / "cache"
        ),
    )
)

# Offline mode
OFFLINE_MODE = os.environ.get("COKODO_OFFLINE", "").lower() in ("1", "true", "yes")

# Tech stacks
TECH_STACKS = {
    "python": "Python",
    "rust": "Rust",
    "qt": "Qt/C++",
    "mixed": "Mixed (Python + Rust)",
    "other": "Other",
}

# AI Tools
AI_TOOLS: dict[str, AIToolInfo] = {
    "cokodo": {
        "name": "Cokodo (Protocol Only)",
        "file": None,  # No additional file, just .agent/
        "template": None,
    },
    "cursor": {
        "name": "Cursor",
        "file": ".cursorrules",
        "template": "cursorrules.j2",
    },
    "copilot": {
        "name": "GitHub Copilot",
        "file": ".github/copilot-instructions.md",
        "template": "copilot-instructions.j2",
    },
    "claude": {
        "name": "Claude Projects",
        "file": ".claude/instructions.md",
        "template": "claude-instructions.j2",
    },
    "antigravity": {
        "name": "Google Antigravity",
        "file": ".agent/rules/",  # Creates rules directory
        "template": "antigravity",
    },
}
