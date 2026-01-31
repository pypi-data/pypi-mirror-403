"""Context loader with caching support."""

from pathlib import Path
from typing import Dict, Optional, Set

from .cache import ContextCache


class ContextLoader:
    """Load context files with caching.

    Static context files (project.md, workflow.md, etc.) are cached
    to reduce I/O and enable future prompt caching optimizations.
    """

    # Files eligible for caching (static, rarely change)
    CACHEABLE: Set[str] = {
        ".paircoder/context/project.md",
        ".paircoder/context/workflow.md",
        ".paircoder/capabilities.yaml",
        ".paircoder/config.yaml",
        "AGENTS.md",
        "CLAUDE.md",
    }

    # Files that should NOT be cached (dynamic, change frequently)
    NON_CACHEABLE: Set[str] = {
        ".paircoder/context/state.md",
        ".paircoder/history/metrics.jsonl",
    }

    def __init__(self, project_root: Path, cache: Optional[ContextCache] = None):
        self.project_root = project_root
        self.cache = cache or ContextCache(project_root / ".paircoder" / "cache")
        self.hits = 0
        self.misses = 0

    def load(self, relative_path: str) -> str:
        """Load file content, using cache if eligible.

        Args:
            relative_path: Path relative to project root

        Returns:
            File content as string

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        file_path = self.project_root / relative_path

        if not file_path.exists():
            raise FileNotFoundError(f"Context file not found: {relative_path}")

        # Check if cacheable
        if relative_path not in self.CACHEABLE:
            return file_path.read_text(encoding="utf-8")

        # Try cache
        cached = self.cache.get(file_path)
        if cached:
            self.hits += 1
            return cached[0]

        # Cache miss - load and cache
        self.misses += 1
        content = file_path.read_text(encoding="utf-8")
        self.cache.set(file_path, content)
        return content

    def load_all_context(self) -> Dict[str, str]:
        """Load all standard context files.

        Returns:
            Dict mapping relative paths to content
        """
        context = {}
        for path in self.CACHEABLE:
            full_path = self.project_root / path
            if full_path.exists():
                context[path] = self.load(path)
        return context

    def get_stats(self) -> Dict:
        """Get loader statistics."""
        total = self.hits + self.misses
        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": self.hits / total if total > 0 else 0,
            "cache": self.cache.stats(),
        }

    def reset_stats(self) -> None:
        """Reset hit/miss counters."""
        self.hits = 0
        self.misses = 0
