"""Release engineering module for PairCoder.

This module provides CLI commands for release management:
- release plan: Create release plan
- release checklist: Show release checklist
- release prep: Run release preparation checks

And template management:
- template check: Check cookiecutter template drift
- template list: List template files
- template fix: Auto-sync template from source (via --fix flag)

Part of EPIC-003 Phase 2: CLI Architecture Refactor.
"""

from .commands import app as release_app
from .template import app as template_app

__all__ = ["release_app", "template_app"]
