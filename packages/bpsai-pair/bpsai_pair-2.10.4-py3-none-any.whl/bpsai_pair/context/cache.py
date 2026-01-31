"""Context cache for static files."""

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from hashlib import sha256
from pathlib import Path
from typing import Optional, Tuple, Dict, Any


@dataclass
class CacheEntry:
    """Cache entry metadata."""
    path: str
    mtime: float
    cached_at: str
    size_bytes: int
    content_hash: str


class ContextCache:
    """Cache for static context files.

    Caches file content with mtime-based invalidation and TTL expiry.
    """

    def __init__(self, cache_dir: Path, ttl_hours: int = 24):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl = timedelta(hours=ttl_hours)
        self.index_file = cache_dir / "index.json"
        self._index: Dict[str, Dict[str, Any]] = self._load_index()

    def _load_index(self) -> Dict[str, Dict[str, Any]]:
        """Load cache index from disk."""
        if self.index_file.exists():
            try:
                return json.loads(self.index_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                return {}
        return {}

    def _save_index(self) -> None:
        """Save cache index to disk."""
        self.index_file.write_text(json.dumps(self._index, indent=2), encoding="utf-8")

    def _cache_key(self, file_path: Path) -> str:
        """Generate cache key from file path."""
        return sha256(str(file_path.resolve()).encode()).hexdigest()[:16]

    def get(self, file_path: Path) -> Optional[Tuple[str, CacheEntry]]:
        """Get cached content if valid.

        Returns:
            Tuple of (content, entry) or None if cache miss
        """
        key = self._cache_key(file_path)

        if key not in self._index:
            return None

        entry_data = self._index[key]

        # Check file mtime
        if file_path.exists():
            current_mtime = file_path.stat().st_mtime
            if current_mtime > entry_data["mtime"]:
                return None  # File changed

        # Check TTL
        try:
            cached_at = datetime.fromisoformat(entry_data["cached_at"])
            if datetime.now() - cached_at > self.ttl:
                return None  # Expired
        except (KeyError, ValueError):
            return None

        # Read cached content
        cache_file = self.cache_dir / f"{key}.txt"
        if not cache_file.exists():
            return None

        entry = CacheEntry(
            path=entry_data["path"],
            mtime=entry_data["mtime"],
            cached_at=entry_data["cached_at"],
            size_bytes=entry_data["size_bytes"],
            content_hash=entry_data["content_hash"],
        )
        return cache_file.read_text(encoding="utf-8"), entry

    def set(self, file_path: Path, content: str) -> CacheEntry:
        """Cache content for file.

        Returns:
            Cache entry metadata
        """
        key = self._cache_key(file_path)

        # Write content
        cache_file = self.cache_dir / f"{key}.txt"
        cache_file.write_text(content, encoding="utf-8")

        # Create entry
        entry = CacheEntry(
            path=str(file_path),
            mtime=file_path.stat().st_mtime if file_path.exists() else 0,
            cached_at=datetime.now().isoformat(),
            size_bytes=len(content.encode("utf-8")),
            content_hash=sha256(content.encode()).hexdigest()[:16],
        )

        # Update index
        self._index[key] = asdict(entry)
        self._save_index()

        return entry

    def invalidate(self, file_path: Path) -> bool:
        """Invalidate cache for file."""
        key = self._cache_key(file_path)
        if key in self._index:
            del self._index[key]
            cache_file = self.cache_dir / f"{key}.txt"
            cache_file.unlink(missing_ok=True)
            self._save_index()
            return True
        return False

    def clear(self) -> int:
        """Clear entire cache. Returns count of cleared entries."""
        count = len(self._index)
        for key in list(self._index.keys()):
            cache_file = self.cache_dir / f"{key}.txt"
            cache_file.unlink(missing_ok=True)
        self._index = {}
        self._save_index()
        return count

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if not self._index:
            return {
                "entries": 0,
                "total_bytes": 0,
                "oldest": None,
                "newest": None,
            }

        cached_times = [e.get("cached_at") for e in self._index.values() if e.get("cached_at")]

        return {
            "entries": len(self._index),
            "total_bytes": sum(e.get("size_bytes", 0) for e in self._index.values()),
            "oldest": min(cached_times) if cached_times else None,
            "newest": max(cached_times) if cached_times else None,
        }
