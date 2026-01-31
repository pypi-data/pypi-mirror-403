"""Containment manager for contained autonomy mode.

This module provides three-tier filesystem access control for autonomous
agent sessions:

- Tier 1 (Blocked): No read, no write - for secrets, credentials, .env files
- Tier 2 (Read-only): Can read, cannot write - for CLAUDE.md, skills, enforcement code
- Tier 3 (Read-write): Normal access - everything else (the working area)

Note: This is separate from the Docker sandbox system (security.sandbox).
The Docker sandbox provides process isolation, while containment provides
filesystem access control for autonomous agent sessions.
"""
from __future__ import annotations

import fnmatch
from pathlib import Path
from typing import TYPE_CHECKING, Set, List

if TYPE_CHECKING:
    from bpsai_pair.core.config import ContainmentConfig


class ContainmentViolationError(Exception):
    """Raised when attempting to access protected resources.

    This exception indicates that an operation was attempted on a path
    that is protected in contained autonomy mode.
    """

    pass


class ContainmentReadError(ContainmentViolationError):
    """Raised when attempting to read a blocked path.

    Blocked paths cannot be read or written - they contain secrets,
    credentials, or other sensitive data.
    """

    pass


class ContainmentWriteError(ContainmentViolationError):
    """Raised when attempting to write to a protected path.

    This covers both blocked paths (no read/write) and read-only paths
    (read ok, no write).
    """

    pass


class ContainmentManager:
    """Manages three-tier filesystem access control for contained autonomy mode.

    Access tiers:
    - Blocked: No read, no write (secrets, credentials, .env files)
    - Read-only: Can read, cannot write (CLAUDE.md, skills, enforcement code)
    - Read-write: Normal access (everything else)

    The manager must be activated for enforcement to take effect.
    When inactive, all operations are permitted.

    Attributes:
        config: The ContainmentConfig specifying path restrictions.
        project_root: The project root directory (resolved to absolute).
        _active: Whether containment is currently enforced.
        _blocked_dirs: Set of resolved blocked directory paths.
        _blocked_paths: Set of resolved blocked file paths.
        _readonly_dirs: Set of resolved read-only directory paths.
        _readonly_paths: Set of resolved read-only file paths.
    """

    def __init__(self, config: "ContainmentConfig", project_root: Path) -> None:
        """Initialize the containment manager.

        Args:
            config: The ContainmentConfig specifying path restrictions.
            project_root: The project root directory.
        """
        self.config = config
        self.project_root = project_root.resolve()
        self._active = False

        # Tier 1: Blocked (no read, no write)
        self._blocked_dirs: Set[Path] = set()
        self._blocked_paths: Set[Path] = set()

        # Tier 2: Read-only (can read, cannot write)
        self._readonly_dirs: Set[Path] = set()
        self._readonly_paths: Set[Path] = set()

        self._build_path_sets()

    def _build_path_sets(self) -> None:
        """Build the sets of resolved paths for each tier.

        Processes the blocked and readonly directories/files from the config,
        resolving them to absolute paths and expanding any glob patterns.
        """
        # Process blocked directories (Tier 1)
        for dir_pattern in self.config.blocked_directories:
            self._process_dir_pattern(dir_pattern, self._blocked_dirs)

        # Process blocked files (Tier 1)
        for file_path in self.config.blocked_files:
            path = self.project_root / file_path
            self._blocked_paths.add(path.resolve() if path.exists() else path)

        # Process readonly directories (Tier 2)
        for dir_pattern in self.config.readonly_directories:
            self._process_dir_pattern(dir_pattern, self._readonly_dirs)

        # Process readonly files (Tier 2)
        for file_path in self.config.readonly_files:
            path = self.project_root / file_path
            self._readonly_paths.add(path.resolve() if path.exists() else path)

    def _process_dir_pattern(self, dir_pattern: str, target_set: Set[Path]) -> None:
        """Process a directory pattern and add resolved paths to target set.

        Args:
            dir_pattern: Directory path or glob pattern.
            target_set: The set to add resolved paths to.
        """
        if "*" in dir_pattern or "?" in dir_pattern or "[" in dir_pattern:
            self._expand_dir_glob(dir_pattern, target_set)
        else:
            path = self.project_root / dir_pattern.rstrip("/")
            target_set.add(path.resolve() if path.exists() else path)

    def _expand_dir_glob(self, pattern: str, target_set: Set[Path]) -> None:
        """Expand a glob pattern for directories.

        Args:
            pattern: Glob pattern like '.claude/*/' or 'protected/**/'
            target_set: The set to add resolved paths to.
        """
        pattern = pattern.rstrip("/")

        if "**" in pattern:
            for match in self.project_root.glob(pattern):
                if match.is_dir():
                    target_set.add(match.resolve())
            # Also add the base pattern for non-existent paths
            base = pattern.split("**")[0].rstrip("/")
            if base:
                base_path = self.project_root / base
                if base_path.exists():
                    target_set.add(base_path.resolve())
        else:
            for match in self.project_root.glob(pattern):
                if match.is_dir():
                    target_set.add(match.resolve())

    def _resolve_path(self, path: Path) -> Path:
        """Resolve a path to absolute, following symlinks.

        Args:
            path: The path to resolve (can be relative or absolute).

        Returns:
            The resolved absolute path with symlinks followed.
        """
        if not path.is_absolute():
            path = self.project_root / path

        try:
            return path.resolve()
        except (OSError, RuntimeError):
            return Path(path).absolute()

    def _is_path_in_set(
        self, resolved: Path, dirs: Set[Path], files: Set[Path], patterns: List[str]
    ) -> bool:
        """Check if a resolved path is in the given directory/file sets.

        Args:
            resolved: The resolved absolute path to check.
            dirs: Set of directory paths to check against.
            files: Set of file paths to check against.
            patterns: Original patterns from config for glob matching.

        Returns:
            True if path matches any entry in the sets.
        """
        # Check if path is an exact file match
        if resolved in files:
            return True

        # Check for non-existent files (relative match)
        for locked_file in files:
            if not locked_file.exists():
                try:
                    rel_locked = (
                        locked_file.relative_to(self.project_root)
                        if locked_file.is_relative_to(self.project_root)
                        else locked_file
                    )
                    rel_path = resolved.relative_to(self.project_root)
                    if rel_path == rel_locked:
                        return True
                except ValueError:
                    pass

        # Check if path is within a directory
        for locked_dir in dirs:
            if resolved == locked_dir:
                return True
            try:
                resolved.relative_to(locked_dir)
                return True
            except ValueError:
                pass

        # Handle non-existent directories
        for locked_dir in dirs:
            if not locked_dir.exists():
                try:
                    rel_locked = locked_dir.relative_to(self.project_root)
                    rel_path = resolved.relative_to(self.project_root)
                    rel_locked_parts = rel_locked.parts
                    rel_path_parts = rel_path.parts
                    if len(rel_path_parts) >= len(rel_locked_parts):
                        if rel_path_parts[: len(rel_locked_parts)] == rel_locked_parts:
                            return True
                except ValueError:
                    pass

        # Check for glob pattern matches
        for dir_pattern in patterns:
            if "**" in dir_pattern:
                try:
                    rel_path = resolved.relative_to(self.project_root)
                    pattern = dir_pattern.rstrip("/")
                    if self._matches_glob_pattern(str(rel_path), pattern):
                        return True
                except ValueError:
                    pass

        return False

    def _matches_glob_pattern(self, path_str: str, pattern: str) -> bool:
        """Check if a path matches a glob pattern.

        Args:
            path_str: The path string to check.
            pattern: The glob pattern.

        Returns:
            True if the path matches the pattern.
        """
        if "**" in pattern:
            prefix = pattern.split("**")[0].rstrip("/")
            if prefix:
                return path_str.startswith(prefix + "/") or path_str == prefix
        return fnmatch.fnmatch(path_str, pattern)

    def is_path_blocked(self, path: Path) -> bool:
        """Check if a path is in the blocked tier (no read, no write).

        Blocked paths contain secrets, credentials, or other sensitive data
        that should not be accessible at all during contained autonomy.

        Args:
            path: The path to check (can be relative or absolute).

        Returns:
            True if the path is blocked, False otherwise.
        """
        resolved = self._resolve_path(path)
        return self._is_path_in_set(
            resolved,
            self._blocked_dirs,
            self._blocked_paths,
            self.config.blocked_directories,
        )

    def is_path_readonly(self, path: Path) -> bool:
        """Check if a path is in the read-only tier (can read, cannot write).

        Read-only paths contain enforcement code, skills, and configuration
        that Claude should be able to read but not modify.

        Args:
            path: The path to check (can be relative or absolute).

        Returns:
            True if the path is read-only, False otherwise.
        """
        resolved = self._resolve_path(path)
        return self._is_path_in_set(
            resolved,
            self._readonly_dirs,
            self._readonly_paths,
            self.config.readonly_directories,
        )

    def is_path_write_protected(self, path: Path) -> bool:
        """Check if a path is write-protected (blocked OR read-only).

        This is the union of blocked and read-only paths - all paths
        that cannot be written to.

        Args:
            path: The path to check (can be relative or absolute).

        Returns:
            True if the path cannot be written, False otherwise.
        """
        return self.is_path_blocked(path) or self.is_path_readonly(path)

    # Backward compatibility alias
    is_path_locked = is_path_write_protected

    def check_read_allowed(self, path: Path) -> None:
        """Check if reading from a path is allowed.

        Args:
            path: The path to check.

        Raises:
            ContainmentReadError: If the path is blocked and manager is active.
        """
        if not self._active:
            return

        if self.is_path_blocked(path):
            raise ContainmentReadError(
                f"Cannot read blocked path: {path}\n"
                "This path contains sensitive data and is blocked in contained autonomy mode."
            )

    def check_write_allowed(self, path: Path) -> None:
        """Check if writing to a path is allowed.

        Args:
            path: The path to check.

        Raises:
            ContainmentWriteError: If the path is blocked or read-only and manager is active.
        """
        if not self._active:
            return

        if self.is_path_blocked(path):
            raise ContainmentWriteError(
                f"Cannot write to blocked path: {path}\n"
                "This path contains sensitive data and is blocked in contained autonomy mode."
            )

        if self.is_path_readonly(path):
            raise ContainmentWriteError(
                f"Cannot write to read-only path: {path}\n"
                "This path is protected in contained autonomy mode."
            )

    def get_path_tier(self, path: Path) -> str:
        """Get the access tier for a path.

        Args:
            path: The path to check.

        Returns:
            One of: "blocked", "readonly", or "readwrite"
        """
        if self.is_path_blocked(path):
            return "blocked"
        if self.is_path_readonly(path):
            return "readonly"
        return "readwrite"

    def activate(self) -> None:
        """Activate containment enforcement.

        When active, check_read_allowed() and check_write_allowed() will
        raise exceptions for protected paths.
        """
        self._active = True

    def deactivate(self) -> None:
        """Deactivate containment enforcement.

        When inactive, all operations are permitted.
        """
        self._active = False

    @property
    def is_active(self) -> bool:
        """Check if containment is currently active.

        Returns:
            True if containment is enforced, False otherwise.
        """
        return self._active

    @property
    def blocked_directories(self) -> List[Path]:
        """Get the list of blocked directories.

        Returns:
            List of resolved blocked directory paths.
        """
        return list(self._blocked_dirs)

    @property
    def blocked_files(self) -> List[Path]:
        """Get the list of blocked files.

        Returns:
            List of resolved blocked file paths.
        """
        return list(self._blocked_paths)

    @property
    def readonly_directories(self) -> List[Path]:
        """Get the list of read-only directories.

        Returns:
            List of resolved read-only directory paths.
        """
        return list(self._readonly_dirs)

    @property
    def readonly_files(self) -> List[Path]:
        """Get the list of read-only files.

        Returns:
            List of resolved read-only file paths.
        """
        return list(self._readonly_paths)

    # Backward compatibility aliases
    @property
    def locked_directories(self) -> List[Path]:
        """Get all write-protected directories (blocked + readonly).

        Returns:
            List of all directories that cannot be written to.
        """
        return self.blocked_directories + self.readonly_directories

    @property
    def locked_files(self) -> List[Path]:
        """Get all write-protected files (blocked + readonly).

        Returns:
            List of all files that cannot be written to.
        """
        return self.blocked_files + self.readonly_files
