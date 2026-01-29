"""Issue detection modules."""

from code_weaver.issues.base import Issue, IssueType, Severity
from code_weaver.issues.syntax_issues import SyntaxIssueAnalyzer
from code_weaver.issues.type_errors import TypeErrorAnalyzer
from code_weaver.issues.undefined_vars import UndefinedVariableAnalyzer
from code_weaver.issues.unused_imports import UnusedImportAnalyzer

__all__ = [
    "Issue",
    "IssueType",
    "Severity",
    "UndefinedVariableAnalyzer",
    "UnusedImportAnalyzer",
    "TypeErrorAnalyzer",
    "SyntaxIssueAnalyzer",
]
