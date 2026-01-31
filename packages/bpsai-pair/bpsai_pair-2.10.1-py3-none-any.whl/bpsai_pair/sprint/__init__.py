"""Sprint lifecycle management for PairCoder.

This module provides CLI commands for managing sprints:
- sprint list: List sprints with status
- sprint complete: Complete a sprint with checklist

Part of EPIC-003 Phase 2: CLI Architecture Refactor.
"""

from .commands import app as sprint_app

__all__ = ["sprint_app"]
