"""Shared helpers for tool implementations."""

from functools import lru_cache
from pathlib import Path

import pathspec


def _safe_path(workspace: Path, rel: str) -> Path:
    """Resolve a relative path and ensure it stays within the workspace."""
    resolved = (workspace / rel).resolve()
    if not str(resolved).startswith(str(workspace.resolve())):
        raise ValueError(f"Path escapes workspace: {rel}")
    return resolved


@lru_cache(maxsize=4)
def _load_gitignore(workspace: Path) -> pathspec.PathSpec | None:
    """Load .gitignore patterns from workspace root. Cached for performance."""
    gitignore_path = workspace / ".gitignore"
    if gitignore_path.exists():
        lines = gitignore_path.read_text().splitlines()
        return pathspec.PathSpec.from_lines("gitignore", lines)
    return None


def is_ignored(workspace: Path, rel_path: Path | str) -> bool:
    """Check if a path should be ignored based on .gitignore rules."""
    spec = _load_gitignore(workspace)
    if spec is None:
        return False
    return spec.match_file(str(rel_path))
