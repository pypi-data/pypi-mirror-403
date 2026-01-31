"""Benchmark validation utilities."""

import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of benchmark validation."""
    passed: bool
    passed_checks: List[str] = field(default_factory=list)
    failed_checks: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)


class BenchmarkValidator:
    """Validates benchmark execution results."""

    def __init__(self, workspace: Path):
        self.workspace = workspace

    def validate(self, checks: List[Dict[str, str]]) -> ValidationResult:
        """Run all validation checks."""
        passed_checks = []
        failed_checks = []
        details = {}

        for check in checks:
            check_type = list(check.keys())[0]
            check_value = check[check_type]

            try:
                if check_type == "test":
                    result = self._run_test(check_value)
                elif check_type == "assert":
                    result = self._evaluate_assert(check_value)
                elif check_type == "exists":
                    result = self._check_exists(check_value)
                elif check_type == "contains":
                    result = self._check_contains(check_value, check.get("text", ""))
                elif check_type == "lint":
                    result = self._run_lint(check_value)
                else:
                    logger.warning(f"Unknown check type: {check_type}")
                    result = False

                check_name = f"{check_type}:{check_value}"
                if result:
                    passed_checks.append(check_name)
                else:
                    failed_checks.append(check_name)
                details[check_name] = result

            except Exception as e:
                check_name = f"{check_type}:{check_value}"
                failed_checks.append(check_name)
                details[check_name] = str(e)

        return ValidationResult(
            passed=len(failed_checks) == 0,
            passed_checks=passed_checks,
            failed_checks=failed_checks,
            details=details,
        )

    def _run_test(self, command: str) -> bool:
        """Run a test command and check exit code."""
        try:
            result = subprocess.run(
                command.split(),
                cwd=self.workspace,
                capture_output=True,
                timeout=60,
            )
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            logger.warning(f"Test timeout: {command}")
            return False
        except Exception as e:
            logger.error(f"Test error: {e}")
            return False

    def _evaluate_assert(self, assertion: str) -> bool:
        """Evaluate an assertion expression."""
        # Simple assertion parser: "exit_code == 0", "file_count > 0"
        parts = assertion.split()
        if len(parts) != 3:
            return False

        var, op, expected = parts

        # Get actual value
        if var == "exit_code":
            actual = 0  # Would need context from previous command
        elif var == "file_count":
            actual = len(list(self.workspace.glob("*")))
        else:
            return False

        # Compare
        try:
            expected = int(expected)
            if op == "==":
                return actual == expected
            elif op == "!=":
                return actual != expected
            elif op == ">":
                return actual > expected
            elif op == ">=":
                return actual >= expected
            elif op == "<":
                return actual < expected
            elif op == "<=":
                return actual <= expected
        except ValueError:
            return False

        return False

    def _check_exists(self, path: str) -> bool:
        """Check if a file or directory exists."""
        target = self.workspace / path
        return target.exists()

    def _check_contains(self, path: str, text: str) -> bool:
        """Check if a file contains specified text."""
        target = self.workspace / path
        if not target.exists():
            return False

        try:
            content = target.read_text(encoding="utf-8")
            return text.lower() in content.lower()
        except Exception:
            return False

    def _run_lint(self, command: str) -> bool:
        """Run a linting command."""
        try:
            result = subprocess.run(
                command.split(),
                cwd=self.workspace,
                capture_output=True,
                timeout=60,
            )
            return result.returncode == 0
        except Exception:
            return False


def parse_validation_spec(spec: str) -> Dict[str, str]:
    """Parse a validation spec string like 'test: pytest tests/'."""
    if ":" in spec:
        parts = spec.split(":", 1)
        return {parts[0].strip(): parts[1].strip()}
    return {"assert": spec}
