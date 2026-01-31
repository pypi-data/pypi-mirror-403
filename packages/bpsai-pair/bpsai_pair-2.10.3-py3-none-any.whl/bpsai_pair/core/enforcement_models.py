"""Data models for architecture enforcement.

Contains dataclasses and enums used by the enforcement system.

Location: tools/cli/bpsai_pair/core/enforcement_models.py
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional


class ViolationType(Enum):
    """Types of architecture violations."""

    FILE_TOO_LARGE = "file_too_large"
    FUNCTION_TOO_LONG = "function_too_long"
    TOO_MANY_FUNCTIONS = "too_many_functions"
    TOO_MANY_IMPORTS = "too_many_imports"


@dataclass
class ArchitectureViolation:
    """Represents a single architecture violation.

    Attributes:
        file: Path to the file with the violation
        violation_type: Type of violation
        current_value: Current value that exceeds threshold
        threshold: The threshold that was exceeded
        severity: "warning" or "error"
        line_numbers: Optional list of relevant line numbers
        details: Optional dictionary with additional details
    """

    file: Path
    violation_type: ViolationType
    current_value: int
    threshold: int
    severity: str
    line_numbers: Optional[list[int]] = None
    details: Optional[dict[str, Any]] = None


@dataclass
class SplitSuggestion:
    """Suggestion for how to split a file.

    Attributes:
        source_file: Path to the file to split
        suggested_modules: List of suggested module names
        extraction_hints: Dict mapping module name to (start_line, end_line)
    """

    source_file: Path
    suggested_modules: list[str]
    extraction_hints: dict[str, tuple[int, int]] = field(default_factory=dict)


@dataclass
class ComponentInfo:
    """Information about a detected component in a file.

    Attributes:
        name: Name of the component (class name, function group prefix)
        component_type: Type of component ("class", "function_group", "standalone")
        start_line: Starting line number
        end_line: Ending line number
        line_count: Number of lines in the component
        suggested_filename: Suggested filename for extraction
        functions: List of function names in this component
    """

    name: str
    component_type: str
    start_line: int
    end_line: int
    line_count: int
    suggested_filename: str
    functions: list[str] = field(default_factory=list)


@dataclass
class SplitAnalysisResult:
    """Result of analyzing a file for splitting.

    Attributes:
        source_file: Path to the analyzed file
        total_lines: Total number of lines in the file
        components: List of detected components
        needs_split: Whether the file exceeds thresholds
        hub_recommendation: Suggested hub file structure
    """

    source_file: Path
    total_lines: int
    components: list[ComponentInfo]
    needs_split: bool
    hub_recommendation: str = ""
