"""
CLI Update Cache - Tracks when CLI last updated task status.

Used to detect manual task file edits that bypass CLI hooks.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class CLIUpdateCache:
    """Tracks CLI task status updates for manual edit detection.

    Stores:
    - Last CLI update timestamp per task
    - Last status set via CLI

    Used by detection logic to identify when task files
    were modified outside the CLI (bypassing hooks).
    """

    def __init__(self, cache_path: Path):
        """Initialize cache.

        Args:
            cache_path: Path to cache JSON file
        """
        self.cache_path = Path(cache_path)
        self._data: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        """Load cache from disk."""
        if self.cache_path.exists():
            try:
                self._data = json.loads(self.cache_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load CLI update cache: {e}")
                self._data = {}
        else:
            self._data = {}

    def _save(self) -> None:
        """Save cache to disk."""
        try:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            self.cache_path.write_text(json.dumps(self._data, indent=2), encoding="utf-8")
        except IOError as e:
            logger.warning(f"Failed to save CLI update cache: {e}")

    def record_update(self, task_id: str, status: str) -> None:
        """Record a CLI status update.

        Args:
            task_id: Task ID (e.g., T19.1)
            status: New status set via CLI
        """
        self._data[task_id] = {
            "last_cli_update": datetime.now().isoformat(),
            "last_status": status,
        }
        self._save()

    def get_last_update(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get last CLI update info for a task.

        Args:
            task_id: Task ID to lookup

        Returns:
            Dict with 'last_cli_update' and 'last_status', or None if not found
        """
        return self._data.get(task_id)

    def get_all(self) -> Dict[str, Dict[str, Any]]:
        """Get all cached update info.

        Returns:
            Dict mapping task_id to update info
        """
        return self._data.copy()


def detect_manual_edit(
    cache: CLIUpdateCache,
    task_id: str,
    file_mtime: datetime,
    current_status: str,
) -> Dict[str, Any]:
    """Detect if a task file was manually edited outside CLI.

    Detection criteria:
    1. Task has a CLI update record
    2. File was modified after CLI update
    3. Current status differs from CLI-set status

    Args:
        cache: CLIUpdateCache instance
        task_id: Task ID to check
        file_mtime: File modification time
        current_status: Current status from task file

    Returns:
        Dict with:
        - detected: bool - True if manual edit detected
        - last_cli_update: str - ISO timestamp of last CLI update (if detected)
        - last_cli_status: str - Status set by CLI (if detected)
        - current_status: str - Current status in file (if detected)
        - file_mtime: str - File modification time (if detected)
    """
    info = cache.get_last_update(task_id)

    if not info:
        # No CLI record - can't detect manual edit
        return {"detected": False}

    last_cli_update = datetime.fromisoformat(info["last_cli_update"])
    last_cli_status = info["last_status"]

    # Check if file was modified after CLI update
    if file_mtime <= last_cli_update:
        return {"detected": False}

    # Check if status changed
    if current_status == last_cli_status:
        return {"detected": False}

    # Manual edit detected
    return {
        "detected": True,
        "last_cli_update": info["last_cli_update"],
        "last_cli_status": last_cli_status,
        "current_status": current_status,
        "file_mtime": file_mtime.isoformat(),
    }


def get_cli_update_cache(paircoder_dir: Path) -> CLIUpdateCache:
    """Get CLIUpdateCache instance for a project.

    Args:
        paircoder_dir: Path to .paircoder directory

    Returns:
        CLIUpdateCache instance
    """
    cache_path = paircoder_dir / "cache" / "cli-update-cache.json"
    return CLIUpdateCache(cache_path)
