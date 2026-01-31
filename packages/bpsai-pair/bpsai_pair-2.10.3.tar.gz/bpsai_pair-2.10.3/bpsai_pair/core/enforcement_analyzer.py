"""Split analyzer for architecture enforcement.

Analyzes Python files and suggests how to split them into smaller modules.

Location: tools/cli/bpsai_pair/core/enforcement_analyzer.py
"""
from __future__ import annotations

import ast
from pathlib import Path

from .enforcement_models import (
    ArchitectureViolation,
    ComponentInfo,
    SplitAnalysisResult,
    SplitSuggestion,
)
from .enforcement_utils import class_to_filename, get_ast_end_line, group_functions_by_prefix


class SplitAnalyzer:
    """Analyzes Python files and suggests how to split them.

    This class provides detailed analysis of large files, identifying
    logical components (classes, function groups) and suggesting how
    to extract them into separate modules.
    """

    DEFAULT_SPLIT_THRESHOLD = 200  # Suggest split above this

    def __init__(self, split_threshold: int = DEFAULT_SPLIT_THRESHOLD):
        """Initialize the analyzer.

        Args:
            split_threshold: Line count above which to suggest splitting
        """
        self.split_threshold = split_threshold

    def analyze(self, path: Path) -> SplitAnalysisResult:
        """Analyze a file and return split suggestions.

        Args:
            path: Path to the Python file to analyze

        Returns:
            SplitAnalysisResult with components and recommendations
        """
        # Read file
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return SplitAnalysisResult(
                source_file=path,
                total_lines=0,
                components=[],
                needs_split=False,
                hub_recommendation="",
            )

        lines = content.splitlines()
        total_lines = len(lines)

        # Parse AST
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return SplitAnalysisResult(
                source_file=path,
                total_lines=total_lines,
                components=[],
                needs_split=total_lines > self.split_threshold,
                hub_recommendation="",
            )

        # Analyze components
        components = self._analyze_components(tree, path.stem)

        # Determine if split is needed
        needs_split = total_lines > self.split_threshold

        # Generate hub recommendation
        hub_recommendation = self._generate_hub_recommendation(path, components)

        return SplitAnalysisResult(
            source_file=path,
            total_lines=total_lines,
            components=components,
            needs_split=needs_split,
            hub_recommendation=hub_recommendation,
        )

    def _analyze_components(
        self, tree: ast.AST, module_name: str
    ) -> list[ComponentInfo]:
        """Analyze AST and identify logical components.

        Args:
            tree: Parsed AST
            module_name: Name of the module (for filename suggestions)

        Returns:
            List of ComponentInfo objects
        """
        components: list[ComponentInfo] = []
        standalone_functions = []

        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef):
                start = node.lineno
                end = get_ast_end_line(node)
                line_count = end - start + 1

                # Get method names
                methods = [
                    n.name
                    for n in ast.iter_child_nodes(node)
                    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                ]

                # Suggest filename based on class name
                suggested_name = class_to_filename(node.name)

                components.append(
                    ComponentInfo(
                        name=node.name,
                        component_type="class",
                        start_line=start,
                        end_line=end,
                        line_count=line_count,
                        suggested_filename=suggested_name,
                        functions=methods,
                    )
                )

            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                start = node.lineno
                end = get_ast_end_line(node)
                standalone_functions.append((node.name, start, end))

        # Group standalone functions by prefix
        func_groups = group_functions_by_prefix(standalone_functions)

        for prefix, funcs in func_groups.items():
            if len(funcs) >= 2:
                # Group has multiple functions
                start = min(f[1] for f in funcs)
                end = max(f[2] for f in funcs)
                line_count = end - start + 1

                if prefix:
                    suggested_name = f"{prefix}_utils.py"
                    group_name = f"{prefix}_* functions"
                else:
                    suggested_name = "utils.py"
                    group_name = "utility functions"

                components.append(
                    ComponentInfo(
                        name=group_name,
                        component_type="function_group",
                        start_line=start,
                        end_line=end,
                        line_count=line_count,
                        suggested_filename=suggested_name,
                        functions=[f[0] for f in funcs],
                    )
                )
            else:
                # Single standalone function
                for func_name, start, end in funcs:
                    line_count = end - start + 1
                    components.append(
                        ComponentInfo(
                            name=func_name,
                            component_type="standalone",
                            start_line=start,
                            end_line=end,
                            line_count=line_count,
                            suggested_filename="helpers.py",
                            functions=[func_name],
                        )
                    )

        # Sort by start line
        components.sort(key=lambda c: c.start_line)

        return components

    def _generate_hub_recommendation(
        self, path: Path, components: list[ComponentInfo]
    ) -> str:
        """Generate recommendation for hub file structure.

        Args:
            path: Original file path
            components: List of detected components

        Returns:
            String describing recommended hub file
        """
        if not components:
            return ""

        hub_lines = [
            f'"""Hub module for {path.stem}.',
            "",
            "Re-exports public API from decomposed modules.",
            '"""',
            "",
        ]

        # Add imports for each component
        for comp in components:
            if comp.component_type == "class":
                module = comp.suggested_filename.replace(".py", "")
                hub_lines.append(f"from .{module} import {comp.name}")
            elif comp.component_type == "function_group" and comp.functions:
                module = comp.suggested_filename.replace(".py", "")
                funcs = ", ".join(comp.functions[:3])
                if len(comp.functions) > 3:
                    funcs += ", ..."
                hub_lines.append(f"from .{module} import {funcs}")

        hub_lines.extend(
            [
                "",
                "# Public API",
                "__all__ = [",
            ]
        )

        for comp in components:
            if comp.component_type == "class":
                hub_lines.append(f'    "{comp.name}",')
            elif comp.component_type == "function_group":
                for func in comp.functions[:3]:
                    hub_lines.append(f'    "{func}",')

        hub_lines.append("]")

        return "\n".join(hub_lines)

    def suggest_split(self, violation: ArchitectureViolation) -> SplitSuggestion:
        """Generate suggestions for splitting a file based on a violation.

        Args:
            violation: The violation to generate suggestions for

        Returns:
            SplitSuggestion with recommended modules and extraction hints
        """
        file_path = violation.file

        # Read and parse the file
        try:
            content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(content)
        except (OSError, SyntaxError):
            return SplitSuggestion(
                source_file=file_path,
                suggested_modules=["extracted.py"],
                extraction_hints={},
            )

        # Analyze file structure
        classes = []
        functions = []

        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef):
                classes.append(
                    (node.name, node.lineno, get_ast_end_line(node))
                )
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append(
                    (node.name, node.lineno, get_ast_end_line(node))
                )

        # Generate suggestions based on content
        suggestions = []
        hints = {}

        # Suggest extracting classes to their own modules
        for class_name, start, end in classes:
            module_name = f"{class_name.lower()}.py"
            suggestions.append(module_name)
            hints[module_name] = (start, end)

        # Group functions by common prefixes
        func_groups = group_functions_by_prefix(functions)
        for prefix, funcs in func_groups.items():
            if len(funcs) > 1:
                module_name = f"{prefix}_utils.py" if prefix else "utils.py"
                if module_name not in suggestions:
                    suggestions.append(module_name)
                    start = min(f[1] for f in funcs)
                    end = max(f[2] for f in funcs)
                    hints[module_name] = (start, end)

        # Ensure at least one suggestion
        if not suggestions:
            suggestions = ["extracted.py"]

        return SplitSuggestion(
            source_file=file_path,
            suggested_modules=suggestions,
            extraction_hints=hints,
        )
