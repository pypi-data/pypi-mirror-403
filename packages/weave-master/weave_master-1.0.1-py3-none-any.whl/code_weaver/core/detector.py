"""Issue detection orchestrator."""

import ast
from pathlib import Path

from code_weaver.core.analyzer import BaseAnalyzer
from code_weaver.issues.base import Issue
from code_weaver.issues.syntax_issues import SyntaxIssueAnalyzer
from code_weaver.issues.type_errors import TypeErrorAnalyzer
from code_weaver.issues.undefined_vars import UndefinedVariableAnalyzer
from code_weaver.issues.unused_imports import UnusedImportAnalyzer


class Detector:
    """
    Orchestrates all issue detectors.

    Each detector is a plugin-style class that analyzes the AST
    and source code to find specific types of issues.
    """

    def __init__(self, analyzers: list[BaseAnalyzer] | None = None):
        """
        Initialize the detector with analyzers.

        Args:
            analyzers: List of analyzers to use. If None, uses default set.
        """
        if analyzers is None:
            self.analyzers = [
                UndefinedVariableAnalyzer(),
                UnusedImportAnalyzer(),
                TypeErrorAnalyzer(),
                SyntaxIssueAnalyzer(),
            ]
        else:
            self.analyzers = analyzers

    def analyze(self, source_code: str, filepath: str) -> list[Issue]:
        """
        Analyze source code for issues.

        Args:
            source_code: Python source code to analyze
            filepath: Path to the source file (for error messages)

        Returns:
            List of detected issues
        """
        issues: list[Issue] = []

        # Try to parse the AST
        try:
            tree = ast.parse(source_code)
        except SyntaxError as e:
            # Return a syntax error issue
            issues.append(Issue(
                type=issues_module.IssueType.SYNTAX_ISSUE,
                severity=issues_module.Severity.ERROR,
                filepath=filepath,
                line=e.lineno or 1,
                column=e.offset or 0,
                message=f"Syntax error: {e.msg}",
                suggested_fix=None,
                confidence=1.0,
                context={"error_type": "parse_error", "text": e.text},
            ))
            return issues

        # Run each analyzer
        for analyzer in self.analyzers:
            try:
                analyzer_issues = analyzer.detect(tree, source_code, filepath)
                issues.extend(analyzer_issues)
            except Exception as e:
                # Don't let one analyzer failure stop others
                pass

        # Sort by line number, then column
        issues.sort(key=lambda i: (i.line, i.column))

        return issues

    def analyze_file(self, filepath: str | Path) -> list[Issue]:
        """
        Analyze a file for issues.

        Args:
            filepath: Path to the Python file to analyze

        Returns:
            List of detected issues
        """
        filepath = Path(filepath)

        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        if not filepath.suffix == ".py":
            raise ValueError(f"Not a Python file: {filepath}")

        source_code = filepath.read_text(encoding="utf-8")
        return self.analyze(source_code, str(filepath))

    def analyze_directory(
        self,
        directory: str | Path,
        recursive: bool = True,
        ignore_patterns: list[str] | None = None,
    ) -> dict[str, list[Issue]]:
        """
        Analyze all Python files in a directory.

        Args:
            directory: Path to the directory to analyze
            recursive: Whether to recursively search subdirectories
            ignore_patterns: Glob patterns to ignore

        Returns:
            Dictionary mapping filepath to list of issues
        """
        directory = Path(directory)

        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        if not directory.is_dir():
            raise ValueError(f"Not a directory: {directory}")

        if ignore_patterns is None:
            ignore_patterns = [
                ".git", "__pycache__", "venv", ".venv",
                "node_modules", ".tox", ".eggs", "*.egg-info",
                "build", "dist",
            ]

        results: dict[str, list[Issue]] = {}

        # Find all Python files
        pattern = "**/*.py" if recursive else "*.py"
        for filepath in directory.glob(pattern):
            # Check ignore patterns
            should_ignore = False
            for pattern in ignore_patterns:
                if pattern in str(filepath):
                    should_ignore = True
                    break

            if should_ignore:
                continue

            try:
                issues = self.analyze_file(filepath)
                if issues:
                    results[str(filepath)] = issues
            except Exception:
                # Skip files that can't be analyzed
                pass

        return results


# Import for the syntax error handling above
from code_weaver.issues import base as issues_module
