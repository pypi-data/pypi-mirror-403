"""Base analyzer class and AST utilities."""

from __future__ import annotations

import ast
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from code_weaver.issues.base import Issue


class BaseAnalyzer(ABC):
    """Abstract base class for code analyzers."""

    @abstractmethod
    def detect(self, tree: ast.AST, source_code: str, filepath: str) -> list["Issue"]:
        """
        Analyze AST and detect issues.

        Args:
            tree: Parsed AST of the source code
            source_code: Original source code string
            filepath: Path to the source file

        Returns:
            List of detected issues
        """
        pass


class ScopeTracker(ast.NodeVisitor):
    """
    AST visitor that tracks variable scopes.

    Maintains a stack of scopes for tracking variable definitions
    and references at different nesting levels.
    """

    def __init__(self):
        self.scopes: list[dict[str, ast.AST]] = [{}]  # Stack of scopes
        self.global_names: set[str] = set()
        self.nonlocal_names: set[str] = set()

    @property
    def current_scope(self) -> dict[str, ast.AST]:
        """Get the current (innermost) scope."""
        return self.scopes[-1]

    def push_scope(self):
        """Enter a new scope level."""
        self.scopes.append({})

    def pop_scope(self) -> dict[str, ast.AST]:
        """Exit the current scope level."""
        if len(self.scopes) > 1:
            return self.scopes.pop()
        return {}

    def define(self, name: str, node: ast.AST):
        """Define a variable in the current scope."""
        self.current_scope[name] = node

    def lookup(self, name: str) -> ast.AST | None:
        """Look up a variable in all accessible scopes."""
        # Check from innermost to outermost scope
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None

    def is_defined(self, name: str) -> bool:
        """Check if a variable is defined in any accessible scope."""
        for scope in self.scopes:
            if name in scope:
                return True
        return False

    def get_all_defined_names(self) -> set[str]:
        """Get all names defined in any scope."""
        names = set()
        for scope in self.scopes:
            names.update(scope.keys())
        return names


def get_source_segment(source_code: str, node: ast.AST) -> str | None:
    """Extract the source code segment for an AST node."""
    try:
        return ast.get_source_segment(source_code, node)
    except (AttributeError, TypeError):
        return None


def get_line_content(source_code: str, line_number: int) -> str:
    """Get the content of a specific line from source code."""
    lines = source_code.splitlines()
    if 1 <= line_number <= len(lines):
        return lines[line_number - 1]
    return ""


def find_similar_names(target: str, candidates: set[str], threshold: float = 0.6) -> list[str]:
    """
    Find names similar to target using simple similarity metric.

    Args:
        target: The name to find matches for
        candidates: Set of candidate names to compare against
        threshold: Minimum similarity score (0.0 to 1.0)

    Returns:
        List of similar names, sorted by similarity (most similar first)
    """
    def similarity(a: str, b: str) -> float:
        """Calculate simple similarity ratio between two strings."""
        if not a or not b:
            return 0.0

        # Normalize case for comparison
        a_lower = a.lower()
        b_lower = b.lower()

        # Exact match (case insensitive)
        if a_lower == b_lower:
            return 1.0

        # Calculate Levenshtein-like similarity
        len_a, len_b = len(a_lower), len(b_lower)
        if len_a == 0 or len_b == 0:
            return 0.0

        # Simple character overlap ratio
        common = sum(1 for c in a_lower if c in b_lower)
        max_len = max(len_a, len_b)

        return common / max_len

    results = []
    for candidate in candidates:
        score = similarity(target, candidate)
        if score >= threshold:
            results.append((candidate, score))

    # Sort by score descending
    results.sort(key=lambda x: x[1], reverse=True)
    return [name for name, _ in results]


def extract_context(source_code: str, line: int, context_lines: int = 2) -> dict[str, Any]:
    """
    Extract code context around a specific line.

    Args:
        source_code: Full source code
        line: Line number (1-indexed)
        context_lines: Number of lines before/after to include

    Returns:
        Dictionary with context information
    """
    lines = source_code.splitlines()
    start = max(0, line - 1 - context_lines)
    end = min(len(lines), line + context_lines)

    return {
        "before": lines[start:line - 1],
        "target": lines[line - 1] if line - 1 < len(lines) else "",
        "after": lines[line:end],
        "start_line": start + 1,
        "end_line": end,
    }
