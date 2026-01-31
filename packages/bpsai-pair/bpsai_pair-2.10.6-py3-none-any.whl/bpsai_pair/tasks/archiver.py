"""Task archival and restoration."""

import gzip
import json
import shutil
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from .lifecycle import TaskLifecycle, TaskMetadata, TaskState


@dataclass
class ArchivedTask:
    """Archived task metadata."""
    id: str
    title: str
    sprint: Optional[str]
    status: str
    completed_at: Optional[str]
    archived_at: str
    pr: Optional[str] = None
    changelog_entry: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    original_path: Optional[str] = None


@dataclass
class ArchiveManifest:
    """Archive manifest for tracking archived tasks."""
    plan: str
    archived_at: str
    tasks: List[ArchivedTask]
    changelog_generated: bool = False
    version: Optional[str] = None


@dataclass
class ArchiveResult:
    """Result of an archive operation."""
    archived: List[ArchivedTask]
    skipped: List[str]
    errors: List[str]
    changelog_updated: bool
    archive_path: Optional[Path] = None


class TaskArchiver:
    """Handles task archival and restoration."""

    def __init__(self, root_dir: Path, compress: bool = True):
        self.root_dir = root_dir
        self.paircoder_dir = root_dir / ".paircoder"
        self.tasks_dir = self.paircoder_dir / "tasks"
        self.history_dir = self.paircoder_dir / "history"
        self.archive_dir = self.history_dir / "archived-tasks"
        self.compress = compress
        self.lifecycle = TaskLifecycle(self.tasks_dir)

    def archive_task(self, task: TaskMetadata, plan_slug: str) -> ArchivedTask:
        """Archive a single task."""
        # Create archive directory
        plan_archive_dir = self.archive_dir / plan_slug
        plan_archive_dir.mkdir(parents=True, exist_ok=True)

        # Source task file
        source_path = self.tasks_dir / plan_slug / f"{task.id}.task.md"

        if not source_path.exists():
            raise FileNotFoundError(f"Task file not found: {source_path}")

        # Archive path
        if self.compress:
            archive_path = plan_archive_dir / f"{task.id}.task.md.gz"
            with open(source_path, 'rb') as f_in:
                with gzip.open(archive_path, 'wb') as f_out:
                    f_out.writelines(f_in)
        else:
            archive_path = plan_archive_dir / f"{task.id}.task.md"
            shutil.copy2(source_path, archive_path)

        # Remove original
        source_path.unlink()

        # Create archived task record
        archived = ArchivedTask(
            id=task.id,
            title=task.title,
            sprint=task.sprint,
            status=task.status.value,
            completed_at=task.completed_at.isoformat() if task.completed_at else None,
            archived_at=datetime.now().isoformat(),
            pr=task.pr,
            changelog_entry=task.changelog_entry,
            tags=task.tags,
            original_path=str(source_path.relative_to(self.root_dir)),
        )

        # Update manifest
        self._update_manifest(plan_slug, [archived])

        return archived

    def archive_batch(self, tasks: List[TaskMetadata], plan_slug: str,
                      version: Optional[str] = None) -> ArchiveResult:
        """Archive multiple tasks."""
        archived = []
        skipped = []
        errors = []

        for task in tasks:
            # Only archive completed or cancelled tasks
            if task.status not in [TaskState.COMPLETED, TaskState.CANCELLED]:
                skipped.append(f"{task.id}: not archivable (status={task.status.value})")
                continue

            try:
                archived_task = self.archive_task(task, plan_slug)
                archived.append(archived_task)
            except Exception as e:
                errors.append(f"{task.id}: {str(e)}")

        # Update manifest
        if archived:
            self._update_manifest(plan_slug, archived, version)

        return ArchiveResult(
            archived=archived,
            skipped=skipped,
            errors=errors,
            changelog_updated=False,
            archive_path=self.archive_dir / plan_slug if archived else None,
        )

    def _update_manifest(self, plan_slug: str, new_tasks: List[ArchivedTask],
                         version: Optional[str] = None) -> None:
        """Update archive manifest with newly archived tasks."""
        manifest_path = self.archive_dir / plan_slug / "manifest.json"

        # Load existing manifest or create new
        if manifest_path.exists():
            with open(manifest_path, encoding='utf-8') as f:
                data = json.load(f)
            manifest = ArchiveManifest(
                plan=data["plan"],
                archived_at=data["archived_at"],
                tasks=[ArchivedTask(**t) for t in data["tasks"]],
                changelog_generated=data.get("changelog_generated", False),
                version=data.get("version"),
            )
        else:
            manifest = ArchiveManifest(
                plan=plan_slug,
                archived_at=datetime.now().isoformat(),
                tasks=[],
            )

        # Add new tasks
        existing_ids = {t.id for t in manifest.tasks}
        for task in new_tasks:
            if task.id not in existing_ids:
                manifest.tasks.append(task)

        # Update version if provided
        if version:
            manifest.version = version
            manifest.archived_at = datetime.now().isoformat()

        # Save manifest
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        with open(manifest_path, 'w', encoding="utf-8") as f:
            json.dump({
                "plan": manifest.plan,
                "archived_at": manifest.archived_at,
                "tasks": [asdict(t) for t in manifest.tasks],
                "changelog_generated": manifest.changelog_generated,
                "version": manifest.version,
            }, f, indent=2)

    def restore_task(self, task_id: str, plan_slug: str) -> Path:
        """Restore a task from archive."""
        plan_archive_dir = self.archive_dir / plan_slug

        # Find archived task file
        gz_path = plan_archive_dir / f"{task_id}.task.md.gz"
        plain_path = plan_archive_dir / f"{task_id}.task.md"

        if gz_path.exists():
            archive_path = gz_path
            compressed = True
        elif plain_path.exists():
            archive_path = plain_path
            compressed = False
        else:
            raise FileNotFoundError(f"Archived task not found: {task_id}")

        # Restore path
        restore_path = self.tasks_dir / plan_slug / f"{task_id}.task.md"
        restore_path.parent.mkdir(parents=True, exist_ok=True)

        if compressed:
            with gzip.open(archive_path, 'rb') as f_in:
                with open(restore_path, 'wb') as f_out:
                    f_out.write(f_in.read())
        else:
            shutil.copy2(archive_path, restore_path)

        # Remove from archive
        archive_path.unlink()

        # Update manifest
        self._remove_from_manifest(task_id, plan_slug)

        return restore_path

    def _remove_from_manifest(self, task_id: str, plan_slug: str) -> None:
        """Remove task from manifest."""
        manifest_path = self.archive_dir / plan_slug / "manifest.json"

        if not manifest_path.exists():
            return

        with open(manifest_path, encoding='utf-8') as f:
            data = json.load(f)

        data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]

        with open(manifest_path, 'w', encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def list_archived(self, plan_slug: Optional[str] = None) -> List[ArchivedTask]:
        """List archived tasks."""
        archived = []

        if plan_slug:
            plans = [plan_slug]
        else:
            if not self.archive_dir.exists():
                return []
            plans = [d.name for d in self.archive_dir.iterdir() if d.is_dir()]

        for plan in plans:
            manifest_path = self.archive_dir / plan / "manifest.json"
            if manifest_path.exists():
                with open(manifest_path, encoding='utf-8') as f:
                    data = json.load(f)
                for task_data in data["tasks"]:
                    archived.append(ArchivedTask(**task_data))

        return sorted(archived, key=lambda t: t.id)

    def cleanup(self, retention_days: int = 90, dry_run: bool = True) -> List[str]:
        """Remove archived tasks older than retention period."""
        cutoff = datetime.now().timestamp() - (retention_days * 24 * 60 * 60)
        to_remove = []

        for plan_dir in self.archive_dir.iterdir():
            if not plan_dir.is_dir():
                continue

            manifest_path = plan_dir / "manifest.json"
            if not manifest_path.exists():
                continue

            with open(manifest_path, encoding='utf-8') as f:
                data = json.load(f)

            tasks_to_keep = []
            for task_data in data["tasks"]:
                archived_at = datetime.fromisoformat(task_data["archived_at"])
                if archived_at.timestamp() < cutoff:
                    to_remove.append(f"{plan_dir.name}/{task_data['id']}")
                    if not dry_run:
                        # Remove archived file
                        for ext in [".task.md.gz", ".task.md"]:
                            path = plan_dir / f"{task_data['id']}{ext}"
                            if path.exists():
                                path.unlink()
                                break
                else:
                    tasks_to_keep.append(task_data)

            if not dry_run:
                data["tasks"] = tasks_to_keep
                with open(manifest_path, 'w', encoding="utf-8") as f:
                    json.dump(data, f, indent=2)

        return to_remove

    def get_manifest(self, plan_slug: str) -> Optional[ArchiveManifest]:
        """Get archive manifest for a plan."""
        manifest_path = self.archive_dir / plan_slug / "manifest.json"

        if not manifest_path.exists():
            return None

        with open(manifest_path, encoding='utf-8') as f:
            data = json.load(f)

        return ArchiveManifest(
            plan=data["plan"],
            archived_at=data["archived_at"],
            tasks=[ArchivedTask(**t) for t in data["tasks"]],
            changelog_generated=data.get("changelog_generated", False),
            version=data.get("version"),
        )
