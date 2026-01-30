"""Protocol sync and diff utilities."""

import json
import shutil
from pathlib import Path
from typing import NamedTuple

from cokodo_agent.fetcher import get_protocol
from cokodo_agent.linter import ProtocolLinter


class DiffResult(NamedTuple):
    """Diff result for a single file."""

    path: str
    status: str  # "added", "removed", "modified", "unchanged"
    local_hash: str | None = None
    remote_hash: str | None = None


class SyncResult(NamedTuple):
    """Sync result."""

    updated: list[str]
    skipped: list[str]
    errors: list[str]


def get_protocol_version(agent_dir: Path) -> str | None:
    """Get current protocol version from manifest.json."""
    manifest_path = agent_dir / "manifest.json"
    if not manifest_path.exists():
        return None

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        version = manifest.get("version")
        return str(version) if version is not None else None
    except (OSError, json.JSONDecodeError):
        return None


def diff_protocol(agent_dir: Path, offline: bool = False) -> tuple[list[DiffResult], str, str]:
    """
    Compare local .agent with latest protocol.

    Returns:
        Tuple of (diff_results, local_version, remote_version)
    """
    # Get latest protocol
    protocol_path, remote_version = get_protocol(offline=offline)

    # Get local version
    local_version = get_protocol_version(agent_dir) or "unknown"

    # Build checksums for remote protocol
    remote_linter = ProtocolLinter(protocol_path)
    remote_checksums = remote_linter.generate_checksums()

    # Build checksums for local protocol
    local_linter = ProtocolLinter(agent_dir)
    local_checksums = local_linter.generate_checksums()

    # Compare
    all_files = set(remote_checksums.keys()) | set(local_checksums.keys())
    results = []

    for file_path in sorted(all_files):
        local_hash = local_checksums.get(file_path)
        remote_hash = remote_checksums.get(file_path)

        if local_hash is None:
            status = "added"  # New file in remote
        elif remote_hash is None:
            status = "removed"  # File removed in remote
        elif local_hash != remote_hash:
            status = "modified"
        else:
            status = "unchanged"

        results.append(
            DiffResult(
                path=file_path,
                status=status,
                local_hash=local_hash,
                remote_hash=remote_hash,
            )
        )

    return results, local_version, remote_version


def sync_protocol(
    agent_dir: Path,
    offline: bool = False,
    dry_run: bool = False,
) -> tuple[SyncResult, str, str]:
    """
    Sync local .agent with latest protocol.

    Only updates locked files (core/, adapters/, meta/, scripts/, etc.)
    Preserves project/ directory.

    Returns:
        Tuple of (sync_result, local_version, remote_version)
    """
    # Get diff first
    diff_results, local_version, remote_version = diff_protocol(agent_dir, offline=offline)

    # Get protocol source
    protocol_path, _ = get_protocol(offline=offline)

    updated = []
    skipped = []
    errors = []

    for diff in diff_results:
        # Skip unchanged files
        if diff.status == "unchanged":
            continue

        # Skip project/ files - they are user-managed
        if diff.path.startswith("project/"):
            skipped.append(f"{diff.path} (user-managed)")
            continue

        source_file = protocol_path / diff.path
        target_file = agent_dir / diff.path

        try:
            if diff.status == "removed":
                # File was removed in new protocol
                if not dry_run and target_file.exists():
                    target_file.unlink()
                updated.append(f"{diff.path} (removed)")

            elif diff.status in ("added", "modified"):
                # Copy from remote
                if not dry_run:
                    target_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source_file, target_file)
                updated.append(f"{diff.path} ({diff.status})")

        except Exception as e:
            errors.append(f"{diff.path}: {e}")

    # Update manifest version if not dry run
    if not dry_run and not errors:
        manifest_path = agent_dir / "manifest.json"
        if manifest_path.exists():
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                manifest["version"] = remote_version

                # Regenerate checksums
                linter = ProtocolLinter(agent_dir)
                manifest["checksums"] = linter.generate_checksums()

                manifest_path.write_text(
                    json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
                )
            except Exception as e:
                errors.append(f"manifest.json: {e}")

    return SyncResult(updated, skipped, errors), local_version, remote_version


def get_context_files(
    agent_dir: Path,
    stack: str | None = None,
    task: str | None = None,
) -> list[str]:
    """
    Get context files based on stack and task type.

    Uses manifest.json loading_strategy to determine which files to load.
    """
    manifest_path = agent_dir / "manifest.json"
    if not manifest_path.exists():
        return []

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []

    loading_strategy = manifest.get("loading_strategy", {})
    layers = loading_strategy.get("layers", {})
    task_profiles = loading_strategy.get("task_profiles", {})

    files = []

    # Always include essential files
    essential = layers.get("essential", {})
    files.extend(essential.get("files", []))

    # Include context files
    context = layers.get("context", {})
    files.extend(context.get("files", []))

    # Stack-specific files
    if stack:
        stack_specs = layers.get("stack_specs", {})
        options = stack_specs.get("options", {})
        if stack in options:
            files.extend(options[stack])

    # Task-specific files
    if task:
        # Check task profiles first
        if task in task_profiles:
            profile = task_profiles[task]

            # Add workflow files
            workflows = layers.get("workflows", {})
            mappings = workflows.get("mappings", {})
            for workflow in profile.get("workflows", []):
                if workflow in mappings:
                    files.extend(mappings[workflow])

            # Add skill files
            skills = layers.get("skills", {})
            modules = skills.get("modules", {})
            for skill in profile.get("skills", []):
                if skill in modules:
                    module = modules[skill]
                    if "entry" in module:
                        files.append(module["entry"])
                    files.extend(module.get("files", []))

        # Also check direct workflow mappings
        else:
            workflows = layers.get("workflows", {})
            mappings = workflows.get("mappings", {})
            if task in mappings:
                files.extend(mappings[task])

    # Remove duplicates while preserving order
    seen = set()
    unique_files = []
    for f in files:
        if f not in seen:
            seen.add(f)
            unique_files.append(f)

    return unique_files
