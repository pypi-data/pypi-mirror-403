"""Utility functions for architecture enforcement.

Shared helpers used by SplitAnalyzer and ArchitectureEnforcer.

Location: tools/cli/bpsai_pair/core/enforcement_utils.py
"""
from __future__ import annotations

import ast
import re


def get_ast_end_line(node: ast.AST) -> int:
    """Get the end line of an AST node.

    Args:
        node: AST node (must have end_lineno attribute)

    Returns:
        End line number (always available in Python 3.8+)
    """
    return node.end_lineno  # type: ignore[return-value]


def class_to_filename(class_name: str) -> str:
    """Convert CamelCase class name to snake_case filename.

    Args:
        class_name: CamelCase class name

    Returns:
        snake_case filename with .py extension

    Examples:
        >>> class_to_filename("MyClass")
        'my_class.py'
        >>> class_to_filename("HTTPHandler")
        'http_handler.py'
    """
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", class_name)
    snake = re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()
    return f"{snake}.py"


def group_functions_by_prefix(
    functions: list[tuple[str, int, int]]
) -> dict[str, list[tuple[str, int, int]]]:
    """Group functions by common name prefixes.

    Groups functions that share a common prefix (first part before underscore).
    Functions without underscores are grouped under empty string prefix.

    Args:
        functions: List of (name, start_line, end_line) tuples

    Returns:
        Dict mapping prefix to list of functions

    Examples:
        >>> funcs = [("create_user", 1, 10), ("create_item", 11, 20), ("delete_user", 21, 30)]
        >>> groups = group_functions_by_prefix(funcs)
        >>> "create" in groups
        True
        >>> len(groups["create"])
        2
    """
    groups: dict[str, list[tuple[str, int, int]]] = {}

    for func_name, start, end in functions:
        # Extract prefix (e.g., "create_user" -> "create")
        parts = func_name.split("_")
        prefix = parts[0] if len(parts) > 1 else ""

        if prefix not in groups:
            groups[prefix] = []
        groups[prefix].append((func_name, start, end))

    return groups
