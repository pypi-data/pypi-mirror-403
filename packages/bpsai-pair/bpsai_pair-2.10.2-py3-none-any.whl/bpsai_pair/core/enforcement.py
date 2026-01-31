"""Architecture enforcement for PairCoder.

Hub module that re-exports the public API from decomposed modules:
- enforcement_models: Data classes and enums
- enforcement_utils: Shared utility functions
- enforcement_analyzer: SplitAnalyzer class
- enforcement_checker: ArchitectureEnforcer class

Location: tools/cli/bpsai_pair/core/enforcement.py
"""
from __future__ import annotations

# Re-export models
from .enforcement_models import (
    ArchitectureViolation,
    ComponentInfo,
    SplitAnalysisResult,
    SplitSuggestion,
    ViolationType,
)

# Re-export analyzer
from .enforcement_analyzer import SplitAnalyzer

# Re-export checker
from .enforcement_checker import ArchitectureEnforcer

# Re-export utilities (for backwards compatibility)
from .enforcement_utils import (
    class_to_filename,
    get_ast_end_line,
    group_functions_by_prefix,
)


__all__ = [
    # Enums
    "ViolationType",
    # Data classes
    "ArchitectureViolation",
    "SplitSuggestion",
    "ComponentInfo",
    "SplitAnalysisResult",
    # Classes
    "SplitAnalyzer",
    "ArchitectureEnforcer",
    # Utilities
    "get_ast_end_line",
    "class_to_filename",
    "group_functions_by_prefix",
]
