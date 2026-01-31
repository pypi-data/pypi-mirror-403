"""General utilities.

Consolidated from bpsai_pair/utils.py, bpsai_pair/pyutils.py, and bpsai_pair/jsonio.py
as part of T24.7 (Sprint 24 - CLI Refactor Phase 3).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


# === Path utilities (from utils.py) ===

def repo_root() -> Path:
    """Get the repository root directory.

    Returns:
        Path to the repository root (directory containing .git or .paircoder)

    Raises:
        SystemExit: If not run from within a git repository
    """
    from .ops import find_project_root, ProjectRootNotFoundError

    try:
        return find_project_root()
    except ProjectRootNotFoundError:
        raise SystemExit("Run from repo root (where .git or .paircoder exists).")


def ensure_executable(path: Path) -> None:
    """Make a file executable (chmod +x).

    Args:
        path: Path to the file to make executable
    """
    mode = path.stat().st_mode
    path.chmod(mode | 0o111)


# === Project file utilities (from pyutils.py) ===

def project_files(root: Path, excludes: Iterable[str] | None = None) -> List[Path]:
    """Return project files relative to root, respecting simple directory/file excludes.

    Excludes are glob-like segments (e.g., '.git/', '.venv/', '__pycache__/').
    This is intentionally minimal and cross-platform safe.

    Args:
        root: Root directory to search from
        excludes: Iterable of patterns to exclude

    Returns:
        List of relative paths to project files
    """
    ex = list(excludes or [])
    out: List[Path] = []
    for p in root.rglob("*"):
        rel = p.relative_to(root)
        # skip directories that match excludes early
        if any(str(rel).startswith(e.rstrip("/")) for e in ex):
            # if it's a dir, skip its subtree
            if p.is_dir():
                # rely on rglob: cannot prune; filtering below suffices
                pass
        if p.is_file():
            s = str(rel)
            if any(s.startswith(e.rstrip("/")) for e in ex):
                continue
            out.append(rel)
    return out


# === JSON utilities (from jsonio.py) ===

def dump(data: Dict[str, Any]) -> str:
    """Dump data to a formatted JSON string.

    Args:
        data: Dictionary to serialize

    Returns:
        Formatted JSON string
    """
    return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True)
