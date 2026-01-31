"""Changelog generation from archived tasks."""

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

from .archiver import ArchivedTask


# Tag to changelog category mapping
TAG_CATEGORY_MAP = {
    "feature": "Added",
    "enhancement": "Changed",
    "fix": "Fixed",
    "bugfix": "Fixed",
    "infrastructure": "Infrastructure",
    "docs": "Documentation",
    "documentation": "Documentation",
    "deprecation": "Deprecated",
    "removal": "Removed",
    "security": "Security",
}

# Category display order
CATEGORY_ORDER = [
    "Added",
    "Changed",
    "Fixed",
    "Infrastructure",
    "Documentation",
    "Deprecated",
    "Removed",
    "Security",
]


@dataclass
class ChangelogEntry:
    """Single changelog entry."""
    task_id: str
    description: str
    category: str


class ChangelogGenerator:
    """Generates changelog entries from archived tasks."""

    def __init__(self, changelog_path: Path):
        self.changelog_path = changelog_path

    def generate_entry(self, tasks: List[ArchivedTask], version: str,
                       date: Optional[datetime] = None) -> str:
        """Generate a changelog version section from archived tasks."""
        if not tasks:
            return ""

        date = date or datetime.now()
        date_str = date.strftime("%Y-%m-%d")

        categorized = self._categorize_tasks(tasks)
        return self._format_section(version, date_str, categorized)

    def _categorize_tasks(self, tasks: List[ArchivedTask]) -> Dict[str, List[str]]:
        """Group tasks by changelog category based on tags."""
        categories: Dict[str, List[str]] = defaultdict(list)

        for task in tasks:
            category = self._determine_category(task)
            entry_text = task.changelog_entry or task.title
            categories[category].append(f"- {entry_text} ({task.id})")

        return categories

    def _determine_category(self, task: ArchivedTask) -> str:
        """Determine changelog category from task tags."""
        for tag in task.tags:
            tag_lower = tag.lower().strip()
            if tag_lower in TAG_CATEGORY_MAP:
                return TAG_CATEGORY_MAP[tag_lower]

        # Default based on task type inference
        title_lower = task.title.lower() if task.title else ""
        if any(word in title_lower for word in ["add", "create", "implement", "new"]):
            return "Added"
        elif any(word in title_lower for word in ["fix", "bug", "error"]):
            return "Fixed"
        elif any(word in title_lower for word in ["update", "improve", "enhance", "refactor"]):
            return "Changed"

        return "Changed"  # Default

    def _format_section(self, version: str, date_str: str,
                        categorized: Dict[str, List[str]]) -> str:
        """Format a version section."""
        lines = [f"## [{version}] - {date_str}", ""]

        for category in CATEGORY_ORDER:
            if category in categorized and categorized[category]:
                lines.append(f"### {category}")
                for entry in sorted(categorized[category]):
                    lines.append(entry)
                lines.append("")

        return "\n".join(lines)

    def update_changelog(self, tasks: List[ArchivedTask], version: str,
                         date: Optional[datetime] = None) -> None:
        """Update changelog file with new version section."""
        new_section = self.generate_entry(tasks, version, date)

        if not new_section:
            return

        existing = ""
        if self.changelog_path.exists():
            existing = self.changelog_path.read_text(encoding="utf-8")

        # Ensure proper header
        if existing.startswith("# Changelog"):
            # Find first version entry (## [)
            first_version = existing.find("\n## [")
            if first_version != -1:
                # Insert before first version entry
                updated = existing[:first_version + 1] + new_section + existing[first_version + 1:]
            else:
                # No existing versions, append after entire content
                updated = existing.rstrip() + "\n\n" + new_section
        else:
            header = "# Changelog\n\nAll notable changes to this project are documented in this file.\n\n"
            updated = header + new_section + "\n" + existing

        self.changelog_path.write_text(updated, encoding="utf-8")

    def preview(self, tasks: List[ArchivedTask], version: str) -> str:
        """Preview changelog entry without writing."""
        return self.generate_entry(tasks, version)

    def get_latest_version(self) -> Optional[str]:
        """Get the latest version from changelog."""
        if not self.changelog_path.exists():
            return None

        content = self.changelog_path.read_text(encoding="utf-8")

        for line in content.split("\n"):
            if line.startswith("## ["):
                # Extract version from "## [v1.2.3] - date"
                start = line.find("[") + 1
                end = line.find("]")
                if start > 0 and end > start:
                    return line[start:end]

        return None

    def increment_version(self, version: str, bump: str = "patch") -> str:
        """Increment version number."""
        # Handle v prefix
        has_v = version.startswith("v")
        v = version[1:] if has_v else version

        parts = v.split(".")
        if len(parts) != 3:
            parts = ["0", "0", "0"]

        major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])

        if bump == "major":
            major += 1
            minor = 0
            patch = 0
        elif bump == "minor":
            minor += 1
            patch = 0
        else:  # patch
            patch += 1

        new_version = f"{major}.{minor}.{patch}"
        return f"v{new_version}" if has_v else new_version
