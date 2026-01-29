"""Toggl time tracking provider."""

import base64
from datetime import datetime, timedelta, timezone
from typing import List, Optional
import logging

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

from .time_tracking import TimeTrackingProvider, TimerEntry, LocalTimeCache

logger = logging.getLogger(__name__)


class TogglProvider(TimeTrackingProvider):
    """Toggl Track API provider."""

    BASE_URL = "https://api.track.toggl.com/api/v9"

    def __init__(self, api_key: str, workspace_id: Optional[str] = None,
                 cache: Optional[LocalTimeCache] = None):
        if not HAS_REQUESTS:
            raise ImportError("requests library required for Toggl integration")

        self.api_key = api_key
        self.workspace_id = workspace_id
        self.cache = cache
        self._session = self._create_session()
        self._current_entry: Optional[dict] = None

        # Get workspace_id if not provided
        if not self.workspace_id:
            self._fetch_workspace_id()

    def _create_session(self) -> "requests.Session":
        """Create authenticated session."""
        session = requests.Session()
        # Toggl uses basic auth with API key as username, "api_token" as password
        auth_str = f"{self.api_key}:api_token"
        auth_bytes = base64.b64encode(auth_str.encode()).decode()
        session.headers.update({
            "Authorization": f"Basic {auth_bytes}",
            "Content-Type": "application/json",
        })
        return session

    def _fetch_workspace_id(self) -> None:
        """Fetch default workspace ID from API."""
        try:
            response = self._session.get(f"{self.BASE_URL}/me")
            response.raise_for_status()
            data = response.json()
            self.workspace_id = str(data.get("default_workspace_id"))
            logger.debug(f"Using workspace ID: {self.workspace_id}")
        except Exception as e:
            logger.error(f"Failed to fetch workspace ID: {e}")

    def start_timer(self, task_id: str, description: str,
                    project_id: Optional[str] = None) -> str:
        """Start a timer on Toggl."""
        now = datetime.now(timezone.utc)

        payload = {
            "description": description,
            "start": now.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "duration": -1,  # Running timer
            "workspace_id": int(self.workspace_id) if self.workspace_id else None,
            "created_with": "paircoder",
            "tags": [task_id],
        }

        if project_id:
            payload["project_id"] = int(project_id)

        try:
            response = self._session.post(
                f"{self.BASE_URL}/workspaces/{self.workspace_id}/time_entries",
                json=payload
            )
            response.raise_for_status()
            data = response.json()

            self._current_entry = data
            timer_id = str(data["id"])

            if self.cache:
                self.cache.set_active_timer(task_id, timer_id)

            logger.info(f"Started timer {timer_id} for {task_id}")
            return timer_id

        except Exception as e:
            logger.error(f"Failed to start Toggl timer: {e}")
            raise

    def stop_timer(self, timer_id: str) -> TimerEntry:
        """Stop a running timer on Toggl."""
        try:
            response = self._session.patch(
                f"{self.BASE_URL}/workspaces/{self.workspace_id}/time_entries/{timer_id}/stop"
            )
            response.raise_for_status()
            data = response.json()

            # Parse response
            start = datetime.fromisoformat(data["start"].replace("Z", "+00:00"))
            end = datetime.fromisoformat(data["stop"].replace("Z", "+00:00")) if data.get("stop") else datetime.now(timezone.utc)
            duration = timedelta(seconds=data.get("duration", 0))

            # Extract task_id from tags
            tags = data.get("tags", [])
            task_id = tags[0] if tags else None

            entry = TimerEntry(
                id=str(data["id"]),
                task_id=task_id,
                description=data.get("description", ""),
                start=start.replace(tzinfo=None),
                end=end.replace(tzinfo=None),
                duration=duration,
                provider_id=str(data["id"]),
            )

            # Cache the entry
            if self.cache and task_id:
                self.cache.add_entry(task_id, entry)
                self.cache.clear_active_timer()

            self._current_entry = None
            logger.info(f"Stopped timer {timer_id}")
            return entry

        except Exception as e:
            logger.error(f"Failed to stop Toggl timer: {e}")
            raise

    def get_entries(self, task_id: str) -> List[TimerEntry]:
        """Get entries from Toggl for a task (via tag)."""
        # First check cache
        if self.cache:
            cached = self.cache.get_entries(task_id)
            if cached:
                return cached

        # Fetch from API
        try:
            # Get entries from the last 30 days tagged with task_id
            end = datetime.now(timezone.utc)
            start = end - timedelta(days=30)

            response = self._session.get(
                f"{self.BASE_URL}/me/time_entries",
                params={
                    "start_date": start.strftime("%Y-%m-%d"),
                    "end_date": end.strftime("%Y-%m-%d"),
                }
            )
            response.raise_for_status()
            data = response.json()

            entries = []
            for item in data:
                tags = item.get("tags", [])
                if task_id in tags:
                    entry_start = datetime.fromisoformat(item["start"].replace("Z", "+00:00"))
                    entry_end = None
                    if item.get("stop"):
                        entry_end = datetime.fromisoformat(item["stop"].replace("Z", "+00:00"))

                    entries.append(TimerEntry(
                        id=str(item["id"]),
                        task_id=task_id,
                        description=item.get("description", ""),
                        start=entry_start.replace(tzinfo=None),
                        end=entry_end.replace(tzinfo=None) if entry_end else None,
                        duration=timedelta(seconds=item.get("duration", 0)) if item.get("duration", 0) > 0 else None,
                        provider_id=str(item["id"]),
                    ))

            return entries

        except Exception as e:
            logger.error(f"Failed to fetch Toggl entries: {e}")
            return []

    def get_total(self, task_id: str) -> timedelta:
        """Get total time for a task."""
        entries = self.get_entries(task_id)
        total = timedelta(0)

        for entry in entries:
            if entry.duration:
                total += entry.duration

        return total

    def get_current_timer(self) -> Optional[TimerEntry]:
        """Get the currently running timer."""
        try:
            response = self._session.get(f"{self.BASE_URL}/me/time_entries/current")
            response.raise_for_status()
            data = response.json()

            if not data:
                return None

            start = datetime.fromisoformat(data["start"].replace("Z", "+00:00"))
            tags = data.get("tags", [])
            task_id = tags[0] if tags else None

            return TimerEntry(
                id=str(data["id"]),
                task_id=task_id,
                description=data.get("description", ""),
                start=start.replace(tzinfo=None),
                provider_id=str(data["id"]),
            )

        except Exception as e:
            logger.error(f"Failed to get current timer: {e}")
            return None
