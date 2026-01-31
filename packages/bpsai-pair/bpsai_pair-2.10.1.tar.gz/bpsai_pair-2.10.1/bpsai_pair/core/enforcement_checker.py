"""Architecture checker for enforcement.

Main ArchitectureEnforcer class that checks files against constraints.

Location: tools/cli/bpsai_pair/core/enforcement_checker.py
"""
from __future__ import annotations

import ast
import fnmatch
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import yaml

from .enforcement_analyzer import SplitAnalyzer
from .enforcement_models import (
    ArchitectureViolation,
    SplitSuggestion,
    ViolationType,
)
from .enforcement_utils import get_ast_end_line

if TYPE_CHECKING:
    from .config_validator import ArchitectureConfig


class ArchitectureEnforcer:
    """Enforce modular architecture constraints.

    This class checks Python files against configurable thresholds for:
    - File length (lines)
    - Function length (lines)
    - Number of functions per file
    - Number of imports

    Default thresholds follow the guidelines in the architecting-modules skill:
    - max_file_lines: 400 (error)
    - warning_file_lines: 200 (warning)
    - max_function_lines: 50
    - max_functions_per_file: 15
    - max_imports: 20
    """

    DEFAULT_THRESHOLDS = {
        "max_file_lines": 400,
        "warning_file_lines": 200,
        "max_function_lines": 50,
        "max_functions_per_file": 15,
        "max_imports": 20,
    }

    DEFAULT_EXCLUDE_PATTERNS = [
        "__pycache__",
        ".git",
        ".venv",
        "venv",
        "node_modules",
        ".tox",
        ".eggs",
        "*.egg-info",
        "dist",
        "build",
        ".pytest_cache",
        ".mypy_cache",
    ]

    def __init__(
        self,
        max_file_lines: int = DEFAULT_THRESHOLDS["max_file_lines"],
        warning_file_lines: int = DEFAULT_THRESHOLDS["warning_file_lines"],
        max_function_lines: int = DEFAULT_THRESHOLDS["max_function_lines"],
        max_functions_per_file: int = DEFAULT_THRESHOLDS["max_functions_per_file"],
        max_imports: int = DEFAULT_THRESHOLDS["max_imports"],
        exclude_patterns: Optional[list[str]] = None,
        enabled: bool = True,
    ):
        """Initialize the enforcer with thresholds.

        Args:
            max_file_lines: Maximum lines before error (default: 400)
            warning_file_lines: Lines before warning (default: 200)
            max_function_lines: Maximum lines per function (default: 50)
            max_functions_per_file: Maximum functions per file (default: 15)
            max_imports: Maximum import statements (default: 20)
            exclude_patterns: Patterns to exclude from checks
            enabled: Whether enforcement is enabled (default: True)
        """
        self.enabled = enabled
        self.max_file_lines = max_file_lines
        self.warning_file_lines = warning_file_lines
        self.max_function_lines = max_function_lines
        self.max_functions_per_file = max_functions_per_file
        self.max_imports = max_imports

        if exclude_patterns is not None:
            self.exclude_patterns = list(exclude_patterns)
        else:
            self.exclude_patterns = list(self.DEFAULT_EXCLUDE_PATTERNS)

    @classmethod
    def from_architecture_config(
        cls, config: "ArchitectureConfig"
    ) -> "ArchitectureEnforcer":
        """Create an enforcer from an ArchitectureConfig dataclass.

        Args:
            config: ArchitectureConfig instance

        Returns:
            ArchitectureEnforcer with settings from config
        """
        # Combine default exclude patterns with custom ones
        exclude_patterns = list(cls.DEFAULT_EXCLUDE_PATTERNS)
        if config.exclude_patterns:
            exclude_patterns.extend(config.exclude_patterns)

        return cls(
            max_file_lines=config.max_file_lines,
            warning_file_lines=config.warning_file_lines,
            max_function_lines=config.max_function_lines,
            max_functions_per_file=config.max_functions_per_file,
            max_imports=config.max_imports,
            exclude_patterns=exclude_patterns,
            enabled=config.enabled,
        )

    @classmethod
    def from_config(cls, root: Path) -> "ArchitectureEnforcer":
        """Create an enforcer from configuration file.

        Looks for .paircoder/config.yaml and reads architecture settings from
        the 'architecture' section.

        Args:
            root: Project root directory

        Returns:
            ArchitectureEnforcer with settings from config or defaults
        """
        # Import here to avoid circular imports
        from .config_validator import ArchitectureConfig

        config_file = root / ".paircoder" / "config.yaml"
        if not config_file.exists():
            config_file = root / ".paircoder" / "config.yml"

        if not config_file.exists():
            return cls()

        try:
            with open(config_file, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        except (yaml.YAMLError, OSError):
            return cls()

        arch_data = data.get("architecture", {})

        # If no architecture section, return default
        if not arch_data:
            return cls()

        # Create ArchitectureConfig and use it
        try:
            arch_config = ArchitectureConfig.from_dict(arch_data)
            return cls.from_architecture_config(arch_config)
        except (ValueError, TypeError):
            # Invalid config, return defaults
            return cls()

    def check_file(self, path: Path) -> list[ArchitectureViolation]:
        """Check a single file for architecture violations.

        Args:
            path: Path to the Python file to check

        Returns:
            List of violations found in the file
        """
        violations: list[ArchitectureViolation] = []

        # Skip non-Python files
        if path.suffix != ".py":
            return violations

        # Skip nonexistent files
        if not path.exists():
            return violations

        # Read file content
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return violations

        lines = content.splitlines()
        line_count = len(lines)

        # Check file size
        if line_count > self.max_file_lines:
            violations.append(
                ArchitectureViolation(
                    file=path,
                    violation_type=ViolationType.FILE_TOO_LARGE,
                    current_value=line_count,
                    threshold=self.max_file_lines,
                    severity="error",
                )
            )
        elif line_count > self.warning_file_lines:
            violations.append(
                ArchitectureViolation(
                    file=path,
                    violation_type=ViolationType.FILE_TOO_LARGE,
                    current_value=line_count,
                    threshold=self.warning_file_lines,
                    severity="warning",
                )
            )

        # Parse AST for detailed checks
        try:
            tree = ast.parse(content)
        except SyntaxError:
            # Can't parse - skip detailed checks
            return violations

        # Count imports
        import_count = self._count_imports(tree)
        if import_count > self.max_imports:
            violations.append(
                ArchitectureViolation(
                    file=path,
                    violation_type=ViolationType.TOO_MANY_IMPORTS,
                    current_value=import_count,
                    threshold=self.max_imports,
                    severity="error",
                )
            )

        # Check function counts and lengths
        functions = self._find_functions(tree)

        if len(functions) > self.max_functions_per_file:
            violations.append(
                ArchitectureViolation(
                    file=path,
                    violation_type=ViolationType.TOO_MANY_FUNCTIONS,
                    current_value=len(functions),
                    threshold=self.max_functions_per_file,
                    severity="error",
                )
            )

        # Check each function's length
        for func_name, start_line, end_line in functions:
            func_length = end_line - start_line + 1
            if func_length > self.max_function_lines:
                violations.append(
                    ArchitectureViolation(
                        file=path,
                        violation_type=ViolationType.FUNCTION_TOO_LONG,
                        current_value=func_length,
                        threshold=self.max_function_lines,
                        severity="error",
                        line_numbers=[start_line, end_line],
                        details={"function_name": func_name},
                    )
                )

        return violations

    def _count_imports(self, tree: ast.AST) -> int:
        """Count import statements in AST."""
        count = 0
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                count += 1
        return count

    def _find_functions(self, tree: ast.AST) -> list[tuple[str, int, int]]:
        """Find all functions in AST with their line ranges.

        This counts both top-level functions and class methods.

        Returns:
            List of (function_name, start_line, end_line) tuples
        """
        functions = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                start_line = node.lineno
                end_line = get_ast_end_line(node)
                functions.append((node.name, start_line, end_line))

        return functions

    def check_directory(self, path: Path) -> list[ArchitectureViolation]:
        """Check all Python files in a directory for violations.

        Args:
            path: Directory to check

        Returns:
            List of all violations found
        """
        violations: list[ArchitectureViolation] = []

        if not path.exists() or not path.is_dir():
            return violations

        for file_path in path.rglob("*.py"):
            # Check if file matches any exclude pattern
            if self._should_exclude(file_path):
                continue

            violations.extend(self.check_file(file_path))

        return violations

    def _should_exclude(self, path: Path) -> bool:
        """Check if a path should be excluded."""
        path_str = str(path)
        for pattern in self.exclude_patterns:
            # Check if pattern matches any part of the path (simple substring)
            if pattern in path_str:
                return True
            # Use Path.match for glob patterns with directory components
            if path.match(pattern):
                return True
            # Also check fnmatch style patterns against basename
            if fnmatch.fnmatch(path.name, pattern):
                return True
            # Check fnmatch against individual path components
            for part in path.parts:
                if fnmatch.fnmatch(part, pattern):
                    return True
        return False

    def check_staged_files(self) -> list[ArchitectureViolation]:
        """Check git staged files for violations.

        Returns:
            List of violations in staged Python files
        """
        violations: list[ArchitectureViolation] = []

        try:
            result = subprocess.run(
                ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
                capture_output=True,
                text=True,
                check=False,
            )
        except FileNotFoundError:
            # Git not installed
            return violations

        if result.returncode != 0:
            # Not in a git repo or other error
            return violations

        staged_files = result.stdout.strip().splitlines()

        for file_name in staged_files:
            file_path = Path(file_name)
            if file_path.suffix == ".py" and file_path.exists():
                violations.extend(self.check_file(file_path))

        return violations

    def suggest_split(self, violation: ArchitectureViolation) -> SplitSuggestion:
        """Generate suggestions for splitting a file.

        Delegates to SplitAnalyzer for the actual analysis.

        Args:
            violation: The violation to generate suggestions for

        Returns:
            SplitSuggestion with recommended modules and extraction hints
        """
        analyzer = SplitAnalyzer()
        return analyzer.suggest_split(violation)
