"""
Handoff serialization for saving and loading handoff packages.

This module handles persistence of handoff packages and chains to disk.

Classes:
    HandoffSerializer: Manages saving/loading handoff packages and chains

Extracted from handoff.py as part of EPIC-005 module decomposition.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

from .package_builder import EnhancedHandoffPackage, HandoffChain

logger = logging.getLogger(__name__)


class HandoffSerializer:
    """
    Handles saving and loading handoff packages to/from disk.

    Saves to .paircoder/handoffs/{handoff_id}.json by default.
    Chain files are saved as chain-{task_id}.json.

    Attributes:
        handoffs_dir: Directory for handoff files

    Example:
        >>> serializer = HandoffSerializer()
        >>> serializer.save(package)
        >>> loaded = serializer.load("handoff-abc123")
    """

    def __init__(self, handoffs_dir: Optional[Path] = None):
        """
        Initialize the serializer.

        Args:
            handoffs_dir: Directory for handoff files.
                         Defaults to .paircoder/handoffs
        """
        self.handoffs_dir = handoffs_dir or Path(".paircoder/handoffs")

    def _ensure_dir(self) -> None:
        """Ensure the handoffs directory exists."""
        self.handoffs_dir.mkdir(parents=True, exist_ok=True)

    def save(self, package: EnhancedHandoffPackage) -> Path:
        """
        Save a handoff package to disk.

        Args:
            package: The handoff package to save

        Returns:
            Path to the saved file
        """
        self._ensure_dir()

        path = self.handoffs_dir / f"{package.handoff_id}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(package.to_dict(), f, indent=2)

        logger.info(f"Saved handoff: {package.handoff_id} -> {path}")
        return path

    def load(self, handoff_id: str) -> EnhancedHandoffPackage:
        """
        Load a handoff package from disk.

        Args:
            handoff_id: ID of the handoff to load

        Returns:
            The loaded handoff package

        Raises:
            FileNotFoundError: If handoff file doesn't exist
        """
        path = self.handoffs_dir / f"{handoff_id}.json"
        if not path.exists():
            raise FileNotFoundError(f"Handoff not found: {handoff_id}")

        with open(path, encoding='utf-8') as f:
            data = json.load(f)

        return EnhancedHandoffPackage.from_dict(data)

    def list_all(self) -> list[EnhancedHandoffPackage]:
        """
        List all saved handoffs.

        Returns:
            List of all handoff packages
        """
        if not self.handoffs_dir.exists():
            return []

        handoffs = []
        for path in self.handoffs_dir.glob("*.json"):
            if path.name.startswith("chain-"):
                continue  # Skip chain files
            try:
                with open(path, encoding='utf-8') as f:
                    data = json.load(f)
                handoffs.append(EnhancedHandoffPackage.from_dict(data))
            except Exception as e:
                logger.warning(f"Failed to load handoff {path}: {e}")

        return handoffs

    def save_chain(self, chain: HandoffChain) -> Path:
        """
        Save a handoff chain to disk.

        Args:
            chain: The handoff chain to save

        Returns:
            Path to the saved file
        """
        self._ensure_dir()

        path = self.handoffs_dir / f"chain-{chain.task_id}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(chain.to_dict(), f, indent=2)

        logger.info(f"Saved handoff chain: {chain.task_id} -> {path}")
        return path

    def load_chain(self, task_id: str) -> HandoffChain:
        """
        Load or create a handoff chain for a task.

        If a chain file exists, loads it. Otherwise, creates a new chain
        by aggregating individual handoffs for the task.

        Args:
            task_id: ID of the task

        Returns:
            The handoff chain (new or existing)
        """
        path = self.handoffs_dir / f"chain-{task_id}.json"

        if path.exists():
            with open(path, encoding='utf-8') as f:
                data = json.load(f)
            chain = HandoffChain.from_dict(data)

            # Deduplicate by handoff_id (in case of concurrent saves)
            seen_ids: set[str] = set()
            unique_handoffs = []
            for h in chain.handoffs:
                if h.handoff_id not in seen_ids:
                    seen_ids.add(h.handoff_id)
                    unique_handoffs.append(h)
            chain.handoffs = unique_handoffs

            return chain

        # Create new chain from individual handoffs
        chain = HandoffChain(task_id=task_id)
        for handoff in self.list_all():
            if handoff.task_id == task_id:
                chain.add(handoff)

        # Sort by created_at
        chain.handoffs.sort(key=lambda h: h.created_at)

        return chain
