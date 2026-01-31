"""Time tracking provider interface and common utilities."""

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


@dataclass
class TimerEntry:
    """A time entry record."""
    id: str
    task_id: Optional[str]
    description: str
    start: datetime
    end: Optional[datetime] = None
    duration: Optional[timedelta] = None
    provider_id: Optional[str] = None  # ID from external provider

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "task_id": self.task_id,
            "description": self.description,
            "start": self.start.isoformat(),
            "end": self.end.isoformat() if self.end else None,
            "duration_seconds": self.duration.total_seconds() if self.duration else None,
            "provider_id": self.provider_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TimerEntry":
        return cls(
            id=data["id"],
            task_id=data.get("task_id"),
            description=data.get("description", ""),
            start=datetime.fromisoformat(data["start"]),
            end=datetime.fromisoformat(data["end"]) if data.get("end") else None,
            duration=timedelta(seconds=data["duration_seconds"]) if data.get("duration_seconds") else None,
            provider_id=data.get("provider_id"),
        )


@dataclass
class TimeTrackingConfig:
    """Configuration for time tracking."""
    provider: str = "none"  # toggl, clockify, none
    auto_start: bool = True
    auto_stop: bool = True
    workspace_id: Optional[str] = None
    api_key_env: str = "TOGGL_API_KEY"
    task_pattern: str = "{task_id}: {task_title}"
    project_mapping: Dict[str, str] = field(default_factory=dict)


class TimeTrackingProvider(ABC):
    """Abstract base class for time tracking providers."""

    @abstractmethod
    def start_timer(self, task_id: str, description: str,
                    project_id: Optional[str] = None) -> str:
        """Start a timer and return the timer ID."""
        pass

    @abstractmethod
    def stop_timer(self, timer_id: str) -> TimerEntry:
        """Stop a running timer and return the entry."""
        pass

    @abstractmethod
    def get_entries(self, task_id: str) -> List[TimerEntry]:
        """Get all entries for a task."""
        pass

    @abstractmethod
    def get_total(self, task_id: str) -> timedelta:
        """Get total time for a task."""
        pass

    @abstractmethod
    def get_current_timer(self) -> Optional[TimerEntry]:
        """Get the currently running timer, if any."""
        pass


class LocalTimeCache:
    """Local cache for time entries."""

    def __init__(self, cache_path: Path):
        self.cache_path = cache_path
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self._data: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        """Load cache from disk."""
        if self.cache_path.exists():
            try:
                with open(self.cache_path, encoding='utf-8') as f:
                    self._data = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load time cache: {e}")
                self._data = {}

    def _save(self) -> None:
        """Save cache to disk."""
        try:
            with open(self.cache_path, 'w', encoding="utf-8") as f:
                json.dump(self._data, f, indent=2)
        except IOError as e:
            logger.warning(f"Failed to save time cache: {e}")

    def add_entry(self, task_id: str, entry: TimerEntry) -> None:
        """Add an entry to the cache."""
        if task_id not in self._data:
            self._data[task_id] = {"entries": [], "total_seconds": 0}

        self._data[task_id]["entries"].append(entry.to_dict())

        if entry.duration:
            self._data[task_id]["total_seconds"] += entry.duration.total_seconds()

        self._save()

    def get_entries(self, task_id: str) -> List[TimerEntry]:
        """Get all entries for a task."""
        if task_id not in self._data:
            return []
        return [TimerEntry.from_dict(e) for e in self._data[task_id]["entries"]]

    def get_total(self, task_id: str) -> timedelta:
        """Get total time for a task."""
        if task_id not in self._data:
            return timedelta(0)
        return timedelta(seconds=self._data[task_id]["total_seconds"])

    def get_all_tasks(self) -> List[str]:
        """Get all task IDs with time entries."""
        return list(self._data.keys())

    def set_active_timer(
        self,
        task_id: str,
        timer_id: str,
        description: str = "",
        start: Optional[datetime] = None,
    ) -> None:
        """Set the currently active timer with full state for persistence."""
        self._data["_active"] = {
            "task_id": task_id,
            "timer_id": timer_id,
            "description": description,
            "start": (start or datetime.now()).isoformat(),
        }
        self._save()

    def get_active_timer(self) -> Optional[Dict[str, Any]]:
        """Get the currently active timer info.

        Returns dict with: task_id, timer_id, description, start (as datetime)
        """
        active = self._data.get("_active")
        if active and "start" in active:
            # Convert start back to datetime if stored as string
            if isinstance(active["start"], str):
                active = active.copy()
                active["start"] = datetime.fromisoformat(active["start"])
        return active

    def clear_active_timer(self) -> None:
        """Clear the active timer."""
        if "_active" in self._data:
            del self._data["_active"]
            self._save()


class NullProvider(TimeTrackingProvider):
    """Null provider when time tracking is disabled."""

    def __init__(self, cache: LocalTimeCache):
        self.cache = cache
        self._current_timer: Optional[Dict[str, Any]] = None
        # Restore active timer from cache (for session persistence)
        self._restore_active_timer()

    def _restore_active_timer(self) -> None:
        """Restore active timer from cache if one exists."""
        active = self.cache.get_active_timer()
        if active and all(k in active for k in ("timer_id", "task_id", "start")):
            self._current_timer = {
                "id": active["timer_id"],
                "task_id": active["task_id"],
                "description": active.get("description", ""),
                "start": active["start"],  # Already a datetime from cache
            }

    def start_timer(self, task_id: str, description: str,
                    project_id: Optional[str] = None) -> str:
        """Start a local-only timer."""
        start_time = datetime.now()
        timer_id = f"local-{start_time.strftime('%Y%m%d%H%M%S')}"
        self._current_timer = {
            "id": timer_id,
            "task_id": task_id,
            "description": description,
            "start": start_time,
        }
        # Store full timer data for session persistence
        self.cache.set_active_timer(task_id, timer_id, description, start_time)
        return timer_id

    def stop_timer(self, timer_id: str) -> TimerEntry:
        """Stop the timer and save to cache."""
        if not self._current_timer or self._current_timer["id"] != timer_id:
            raise ValueError(f"Timer {timer_id} not found")

        end = datetime.now()
        start = self._current_timer["start"]
        duration = end - start

        entry = TimerEntry(
            id=timer_id,
            task_id=self._current_timer["task_id"],
            description=self._current_timer["description"],
            start=start,
            end=end,
            duration=duration,
        )

        self.cache.add_entry(entry.task_id, entry)
        self.cache.clear_active_timer()
        self._current_timer = None

        return entry

    def get_entries(self, task_id: str) -> List[TimerEntry]:
        """Get entries from cache."""
        return self.cache.get_entries(task_id)

    def get_total(self, task_id: str) -> timedelta:
        """Get total from cache."""
        return self.cache.get_total(task_id)

    def get_current_timer(self) -> Optional[TimerEntry]:
        """Get current timer if running."""
        if not self._current_timer:
            return None

        return TimerEntry(
            id=self._current_timer["id"],
            task_id=self._current_timer["task_id"],
            description=self._current_timer["description"],
            start=self._current_timer["start"],
        )


class TimeTrackingManager:
    """Manages time tracking across providers."""

    def __init__(self, config: TimeTrackingConfig, cache_path: Path):
        self.config = config
        self.cache = LocalTimeCache(cache_path)
        self.provider = self._create_provider()

    def _create_provider(self) -> TimeTrackingProvider:
        """Create the configured provider."""
        if self.config.provider == "toggl":
            from .toggl import TogglProvider
            import os
            api_key = os.getenv(self.config.api_key_env)
            if not api_key:
                logger.warning(f"Toggl API key not found in {self.config.api_key_env}, using local provider")
                return NullProvider(self.cache)
            return TogglProvider(
                api_key=api_key,
                workspace_id=self.config.workspace_id,
                cache=self.cache,
            )
        else:
            return NullProvider(self.cache)

    def start_task(self, task_id: str, task_title: str) -> Optional[str]:
        """Start timer for a task if auto_start is enabled."""
        if not self.config.auto_start:
            return None

        description = self.config.task_pattern.format(
            task_id=task_id,
            task_title=task_title,
        )

        project_id = self.config.project_mapping.get(task_id.split("-")[0])

        try:
            return self.provider.start_timer(task_id, description, project_id)
        except Exception as e:
            logger.error(f"Failed to start timer: {e}")
            return None

    def stop_task(self, timer_id: str) -> Optional[TimerEntry]:
        """Stop timer for a task if auto_stop is enabled."""
        if not self.config.auto_stop:
            return None

        try:
            return self.provider.stop_timer(timer_id)
        except Exception as e:
            logger.error(f"Failed to stop timer: {e}")
            return None

    def get_task_time(self, task_id: str) -> timedelta:
        """Get total time for a task."""
        return self.provider.get_total(task_id)

    def get_task_entries(self, task_id: str) -> List[TimerEntry]:
        """Get all entries for a task."""
        return self.provider.get_entries(task_id)

    def get_status(self) -> Optional[TimerEntry]:
        """Get current timer status."""
        return self.provider.get_current_timer()

    def format_duration(self, duration: timedelta) -> str:
        """Format duration as human-readable string."""
        total_seconds = int(duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60

        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"
