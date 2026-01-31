"""
Compaction detection and recovery module for PairCoder.

Handles context compaction events in Claude Code:
- Creates snapshots before compaction (via PreCompact hook)
- Detects when compaction has occurred
- Recovers context from state.md and snapshots
- Logs compaction events to history
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, List


logger = logging.getLogger(__name__)


@dataclass
class CompactionSnapshot:
    """A snapshot of context taken before compaction."""

    timestamp: datetime
    trigger: str  # "auto" or "manual"
    active_plan: Optional[str] = None
    current_task_id: Optional[str] = None
    current_task_title: Optional[str] = None
    progress: Optional[str] = None
    last_done: Optional[str] = None
    whats_next: Optional[str] = None
    recent_files: Optional[List[str]] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "trigger": self.trigger,
            "active_plan": self.active_plan,
            "current_task_id": self.current_task_id,
            "current_task_title": self.current_task_title,
            "progress": self.progress,
            "last_done": self.last_done,
            "whats_next": self.whats_next,
            "recent_files": self.recent_files,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CompactionSnapshot":
        """Create from dictionary."""
        return cls(
            timestamp=datetime.fromisoformat(data["timestamp"]),
            trigger=data.get("trigger", "unknown"),
            active_plan=data.get("active_plan"),
            current_task_id=data.get("current_task_id"),
            current_task_title=data.get("current_task_title"),
            progress=data.get("progress"),
            last_done=data.get("last_done"),
            whats_next=data.get("whats_next"),
            recent_files=data.get("recent_files"),
        )


@dataclass
class CompactionMarker:
    """Marker indicating a compaction event occurred."""

    timestamp: datetime
    trigger: str  # "auto" or "manual"
    recovered: bool = False
    snapshot_file: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "trigger": self.trigger,
            "recovered": self.recovered,
            "snapshot_file": self.snapshot_file,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CompactionMarker":
        """Create from dictionary."""
        return cls(
            timestamp=datetime.fromisoformat(data["timestamp"]),
            trigger=data.get("trigger", "unknown"),
            recovered=data.get("recovered", False),
            snapshot_file=data.get("snapshot_file"),
        )


class CompactionManager:
    """Manages compaction detection and recovery."""

    def __init__(self, paircoder_dir: Path):
        """
        Initialize compaction manager.

        Args:
            paircoder_dir: Path to .paircoder directory
        """
        self.paircoder_dir = Path(paircoder_dir)
        self.cache_dir = self.paircoder_dir / "cache"
        self.history_dir = self.paircoder_dir / "history"
        self.context_dir = self.paircoder_dir / "context"
        self.marker_file = self.cache_dir / "compaction_marker.json"
        self.compaction_log = self.history_dir / "compaction.log"

        # Ensure directories exist
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.history_dir.mkdir(parents=True, exist_ok=True)

    def save_snapshot(self, trigger: str = "manual", reason: Optional[str] = None) -> Path:
        """
        Save a compaction snapshot with current context.

        Called by PreCompact hook before compaction occurs.

        Args:
            trigger: "auto" or "manual" compaction
            reason: Optional reason/description for the snapshot

        Returns:
            Path to the created snapshot file
        """
        now = datetime.now()

        # Read current state from state.md
        snapshot = self._create_snapshot_from_state(now, trigger)

        # Get recent file changes
        snapshot.recent_files = self._get_recent_files()

        # Save snapshot
        filename = f"compaction_snapshot_{now.strftime('%Y%m%d_%H%M%S')}.json"
        snapshot_path = self.cache_dir / filename

        with open(snapshot_path, "w", encoding="utf-8") as f:
            json.dump(snapshot.to_dict(), f, indent=2)

        # Create compaction marker
        marker = CompactionMarker(
            timestamp=now,
            trigger=trigger,
            recovered=False,
            snapshot_file=filename,
        )
        self._save_marker(marker)

        # Log the event
        self._log_compaction(trigger, reason, snapshot_path)

        return snapshot_path

    def _create_snapshot_from_state(self, timestamp: datetime, trigger: str) -> CompactionSnapshot:
        """Create a snapshot by parsing state.md."""
        snapshot = CompactionSnapshot(timestamp=timestamp, trigger=trigger)

        state_path = self.context_dir / "state.md"
        if not state_path.exists():
            return snapshot

        try:
            content = state_path.read_text(encoding="utf-8")
            snapshot = self._parse_state_for_snapshot(content, timestamp, trigger)
        except IOError as e:
            logger.warning(f"Failed to read state.md: {e}")

        return snapshot

    def _parse_state_for_snapshot(self, content: str, timestamp: datetime, trigger: str) -> CompactionSnapshot:
        """Parse state.md content for snapshot."""
        snapshot = CompactionSnapshot(timestamp=timestamp, trigger=trigger)
        lines = content.split("\n")

        current_section = None

        for line in lines:
            stripped = line.strip()

            # Detect sections
            if stripped.startswith("## "):
                current_section = stripped[3:].lower()
                continue

            # Parse Active Plan section
            if current_section == "active plan":
                if stripped.startswith("**Plan:**"):
                    snapshot.active_plan = stripped.replace("**Plan:**", "").strip()

            # Parse task table
            if current_section and "sprint" in current_section and "task" in current_section:
                if "|" in stripped and "in_progress" in stripped.lower():
                    parts = [p.strip() for p in stripped.split("|") if p.strip()]
                    if len(parts) >= 2:
                        snapshot.current_task_id = parts[0] if parts[0] != "ID" else None
                        snapshot.current_task_title = parts[1] if len(parts) > 1 else None

            # Parse Progress line
            if stripped.startswith("**Progress:**"):
                snapshot.progress = stripped.replace("**Progress:**", "").strip()

            # Parse What Was Just Done
            if current_section == "what was just done":
                if stripped.startswith("- ") and not snapshot.last_done:
                    snapshot.last_done = stripped[2:]

            # Parse What's Next
            if current_section == "what's next":
                if (stripped.startswith("1. ") or stripped.startswith("- ")) and not snapshot.whats_next:
                    snapshot.whats_next = stripped.lstrip("1.- ")

        return snapshot

    def _get_recent_files(self) -> List[str]:
        """Get list of recently changed files from changes.log."""
        changes_log = self.history_dir / "changes.log"
        if not changes_log.exists():
            return []

        try:
            lines = changes_log.read_text(encoding="utf-8").strip().split("\n")
            # Get last 10 unique files
            files = []
            seen = set()
            for line in reversed(lines[-20:]):
                parts = line.split(" ", 1)
                if len(parts) == 2:
                    filepath = parts[1].strip()
                    if filepath not in seen:
                        seen.add(filepath)
                        files.append(filepath)
                        if len(files) >= 10:
                            break
            return files
        except IOError:
            return []

    def _save_marker(self, marker: CompactionMarker) -> None:
        """Save compaction marker."""
        try:
            with open(self.marker_file, "w", encoding="utf-8") as f:
                json.dump(marker.to_dict(), f, indent=2)
        except IOError as e:
            logger.warning(f"Failed to save compaction marker: {e}")

    def _log_compaction(self, trigger: str, reason: Optional[str], snapshot_path: Path) -> None:
        """Log compaction event to history."""
        try:
            timestamp = datetime.now().isoformat()
            log_entry = f"{timestamp} compaction trigger={trigger}"
            if reason:
                log_entry += f" reason=\"{reason}\""
            log_entry += f" snapshot={snapshot_path.name}\n"

            with open(self.compaction_log, "a", encoding="utf-8") as f:
                f.write(log_entry)
        except IOError as e:
            logger.warning(f"Failed to log compaction: {e}")

    def check_compaction(self) -> Optional[CompactionMarker]:
        """
        Check if compaction recently occurred and needs recovery.

        Returns:
            CompactionMarker if unrecovered compaction detected, None otherwise
        """
        if not self.marker_file.exists():
            return None

        try:
            with open(self.marker_file, encoding='utf-8') as f:
                data = json.load(f)
            marker = CompactionMarker.from_dict(data)

            if not marker.recovered:
                return marker
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"Failed to read compaction marker: {e}")

        return None

    def recover_context(self) -> str:
        """
        Recover context after compaction.

        Reads state.md and any available snapshots to restore context.

        Returns:
            Formatted context recovery message for Claude
        """
        lines = []
        lines.append("Context compaction detected. Restoring from state.md...")
        lines.append("")

        # Read state.md
        state_path = self.context_dir / "state.md"
        if state_path.exists():
            snapshot = self._create_snapshot_from_state(datetime.now(), "recovery")

            lines.append("Recovered context:")
            if snapshot.active_plan:
                lines.append(f"  - Active plan: {snapshot.active_plan}")
            if snapshot.current_task_id:
                task_info = snapshot.current_task_id
                if snapshot.current_task_title:
                    task_info += f" ({snapshot.current_task_title})"
                lines.append(f"  - Current task: {task_info}")
            if snapshot.progress:
                lines.append(f"  - Progress: {snapshot.progress}")
            if snapshot.last_done:
                lines.append(f"  - Last done: {snapshot.last_done}")
            if snapshot.whats_next:
                lines.append(f"  - Next: {snapshot.whats_next}")

        # Check for recent snapshot
        marker = self.check_compaction()
        if marker and marker.snapshot_file:
            snapshot_path = self.cache_dir / marker.snapshot_file
            if snapshot_path.exists():
                try:
                    with open(snapshot_path, encoding='utf-8') as f:
                        snap_data = json.load(f)
                    snapshot = CompactionSnapshot.from_dict(snap_data)
                    if snapshot.recent_files:
                        lines.append("")
                        lines.append("Recent files from pre-compaction snapshot:")
                        for f in snapshot.recent_files[:5]:
                            lines.append(f"  - {f}")
                except (json.JSONDecodeError, KeyError):
                    pass

        lines.append("")
        lines.append("Note: Some conversation details were compacted.")
        lines.append("Run `bpsai-pair status` for full project status.")

        # Mark as recovered
        if marker:
            marker.recovered = True
            self._save_marker(marker)

        return "\n".join(lines)

    def list_snapshots(self) -> List[CompactionSnapshot]:
        """List all available compaction snapshots."""
        snapshots = []
        for path in sorted(self.cache_dir.glob("compaction_snapshot_*.json"), reverse=True):
            try:
                with open(path, encoding='utf-8') as f:
                    data = json.load(f)
                snapshots.append(CompactionSnapshot.from_dict(data))
            except (json.JSONDecodeError, KeyError):
                continue
        return snapshots

    def cleanup_old_snapshots(self, keep: int = 5) -> int:
        """
        Remove old compaction snapshots, keeping the most recent.

        Args:
            keep: Number of snapshots to keep

        Returns:
            Number of snapshots removed
        """
        snapshot_files = sorted(self.cache_dir.glob("compaction_snapshot_*.json"), reverse=True)
        removed = 0

        for path in snapshot_files[keep:]:
            try:
                path.unlink()
                removed += 1
            except IOError:
                pass

        return removed
