"""
Session management module for PairCoder.

Tracks session state to detect new sessions and prompt for context reload.
This helps enforce the methodology of always reviewing state.md at session start.
"""

import json
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import yaml

logger = logging.getLogger(__name__)


@dataclass
class SessionState:
    """Represents the current session state."""

    session_id: str
    last_activity: datetime
    is_new: bool = False

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "session_id": self.session_id,
            "last_activity": self.last_activity.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SessionState":
        """Create from dictionary."""
        return cls(
            session_id=data["session_id"],
            last_activity=datetime.fromisoformat(data["last_activity"]),
            is_new=False,
        )


@dataclass
class SessionContext:
    """Context information to display on new session."""

    active_plan: Optional[str] = None
    plan_status: Optional[str] = None
    current_task_id: Optional[str] = None
    current_task_title: Optional[str] = None
    progress: Optional[str] = None
    last_done: Optional[str] = None
    whats_next: Optional[str] = None


class SessionManager:
    """Manages session detection and context loading."""

    DEFAULT_TIMEOUT_MINUTES = 30

    def __init__(self, paircoder_dir: Path):
        """
        Initialize session manager.

        Args:
            paircoder_dir: Path to .paircoder directory
        """
        self.paircoder_dir = Path(paircoder_dir)
        self.cache_dir = self.paircoder_dir / "cache"
        self.history_dir = self.paircoder_dir / "history"
        self.session_file = self.cache_dir / "session.json"
        self.sessions_log = self.history_dir / "sessions.log"

        # Ensure directories exist
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.history_dir.mkdir(parents=True, exist_ok=True)

        # Load timeout from config
        self.timeout_minutes = self._load_timeout()

    def _load_timeout(self) -> int:
        """Load session timeout from config."""
        config_path = self.paircoder_dir / "config.yaml"
        if config_path.exists():
            try:
                with open(config_path, encoding='utf-8') as f:
                    config = yaml.safe_load(f) or {}
                session_config = config.get("session", {})
                return session_config.get("timeout_minutes", self.DEFAULT_TIMEOUT_MINUTES)
            except (yaml.YAMLError, IOError):
                pass
        return self.DEFAULT_TIMEOUT_MINUTES

    def check_session(self) -> SessionState:
        """
        Check if this is a new session or continuing session.

        Returns:
            SessionState with is_new=True if new session, False if continuing
        """
        now = datetime.now()

        # Try to load existing session
        existing = self._load_session()

        if existing is None:
            # No previous session - this is new
            return self._create_new_session(now)

        # Check if session has timed out
        gap = now - existing.last_activity
        timeout = timedelta(minutes=self.timeout_minutes)

        if gap > timeout:
            # Session timed out - this is new
            return self._create_new_session(now)

        # Continuing session - update timestamp
        existing.last_activity = now
        self._save_session(existing)
        return existing

    def _load_session(self) -> Optional[SessionState]:
        """Load session state from cache."""
        if not self.session_file.exists():
            return None

        try:
            with open(self.session_file, encoding='utf-8') as f:
                data = json.load(f)
            return SessionState.from_dict(data)
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"Failed to load session cache: {e}")
            return None

    def _save_session(self, state: SessionState) -> None:
        """Save session state to cache."""
        try:
            with open(self.session_file, "w", encoding="utf-8") as f:
                json.dump(state.to_dict(), f, indent=2)
        except IOError as e:
            logger.warning(f"Failed to save session cache: {e}")

    def _create_new_session(self, start_time: datetime) -> SessionState:
        """Create a new session and log it."""
        session = SessionState(
            session_id=str(uuid.uuid4())[:8],
            last_activity=start_time,
            is_new=True,
        )

        self._save_session(session)
        self._log_session_start(session)

        return session

    def _log_session_start(self, session: SessionState) -> None:
        """Log session start to history."""
        try:
            with open(self.sessions_log, "a", encoding="utf-8") as f:
                timestamp = session.last_activity.isoformat()
                f.write(f"{timestamp} session_start id={session.session_id}\n")
        except IOError as e:
            logger.warning(f"Failed to log session start: {e}")

    def get_context(self) -> SessionContext:
        """
        Read state.md and extract context summary.

        Returns:
            SessionContext with current state information
        """
        state_path = self.paircoder_dir / "context" / "state.md"
        context = SessionContext()

        if not state_path.exists():
            return context

        try:
            content = state_path.read_text(encoding="utf-8")
            context = self._parse_state_md(content)
        except IOError as e:
            logger.warning(f"Failed to read state.md: {e}")

        return context

    def _parse_state_md(self, content: str) -> SessionContext:
        """Parse state.md content to extract context."""
        context = SessionContext()
        lines = content.split("\n")

        current_section = None
        in_table = False

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Detect sections
            if stripped.startswith("## "):
                current_section = stripped[3:].lower()
                in_table = False
                continue

            # Parse Active Plan section
            if current_section == "active plan":
                if stripped.startswith("**Plan:**"):
                    context.active_plan = stripped.replace("**Plan:**", "").strip()
                elif stripped.startswith("**Status:**"):
                    context.plan_status = stripped.replace("**Status:**", "").strip()

            # Parse task table
            if current_section and "sprint" in current_section and "task" in current_section:
                if "|" in stripped and "in_progress" in stripped.lower():
                    # Parse task row
                    parts = [p.strip() for p in stripped.split("|") if p.strip()]
                    if len(parts) >= 2:
                        context.current_task_id = parts[0] if parts[0] != "ID" else None
                        context.current_task_title = parts[1] if len(parts) > 1 and parts[1] != "Title" else None

            # Parse Progress line
            if stripped.startswith("**Progress:**"):
                context.progress = stripped.replace("**Progress:**", "").strip()

            # Parse What Was Just Done
            if current_section == "what was just done":
                if stripped.startswith("- ") and not context.last_done:
                    context.last_done = stripped[2:]

            # Parse What's Next
            if current_section == "what's next":
                if (stripped.startswith("1. ") or stripped.startswith("- ")) and not context.whats_next:
                    context.whats_next = stripped.lstrip("1.- ")

        return context

    def format_context_output(self, context: SessionContext) -> str:
        """
        Format context for display on new session.

        Args:
            context: SessionContext to format

        Returns:
            Formatted string for display
        """
        lines = []
        lines.append("New session detected. Loading context...")
        lines.append("")
        lines.append("Current state from .paircoder/context/state.md:")

        if context.active_plan:
            lines.append(f"  - Active plan: {context.active_plan}")

        if context.current_task_id:
            task_info = f"{context.current_task_id}"
            if context.current_task_title:
                task_info += f": {context.current_task_title}"
            lines.append(f"  - Current task: {task_info} (in_progress)")

        if context.progress:
            lines.append(f"  - Progress: {context.progress}")

        if context.last_done:
            lines.append(f"  - Last session: {context.last_done}")

        if context.whats_next:
            lines.append(f"  - Next: {context.whats_next}")

        if not any([context.active_plan, context.current_task_id, context.progress]):
            lines.append("  - No active plan or task found")

        lines.append("")
        lines.append("Run `bpsai-pair status` for full context.")

        return "\n".join(lines)
