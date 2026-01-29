"""Tests for issue detection modules."""

import ast
import pytest

from code_weaver.issues.base import Issue, IssueType, Severity
from code_weaver.issues.undefined_vars import UndefinedVariableAnalyzer
from code_weaver.issues.unused_imports import UnusedImportAnalyzer
from code_weaver.issues.type_errors import TypeErrorAnalyzer
from code_weaver.issues.syntax_issues import SyntaxIssueAnalyzer


class TestIssue:
    """Tests for the Issue dataclass."""

    def test_issue_creation(self):
        issue = Issue(
            type=IssueType.UNDEFINED_VAR,
            severity=Severity.ERROR,
            filepath="test.py",
            line=10,
            column=5,
            message="Test message",
        )
        assert issue.type == IssueType.UNDEFINED_VAR
        assert issue.severity == Severity.ERROR
        assert issue.line == 10

    def test_issue_location(self):
        issue = Issue(
            type=IssueType.UNDEFINED_VAR,
            severity=Severity.ERROR,
            filepath="test.py",
            line=10,
            column=5,
            message="Test",
        )
        assert issue.location == "test.py:10:5"

    def test_issue_confidence_validation(self):
        with pytest.raises(ValueError):
            Issue(
                type=IssueType.UNDEFINED_VAR,
                severity=Severity.ERROR,
                filepath="test.py",
                line=1,
                column=0,
                message="Test",
                confidence=1.5,  # Invalid
            )

    def test_issue_to_dict(self):
        issue = Issue(
            type=IssueType.UNDEFINED_VAR,
            severity=Severity.ERROR,
            filepath="test.py",
            line=1,
            column=0,
            message="Test",
            suggested_fix="Fix it",
        )
        d = issue.to_dict()
        assert d["type"] == "undefined_var"
        assert d["severity"] == "error"
        assert d["suggested_fix"] == "Fix it"

    def test_issue_from_dict(self):
        data = {
            "type": "unused_import",
            "severity": "warning",
            "filepath": "test.py",
            "line": 1,
            "column": 0,
            "message": "Unused",
        }
        issue = Issue.from_dict(data)
        assert issue.type == IssueType.UNUSED_IMPORT
        assert issue.severity == Severity.WARNING


class TestUndefinedVariableAnalyzer:
    """Tests for undefined variable detection."""

    def setup_method(self):
        self.analyzer = UndefinedVariableAnalyzer()

    def _analyze(self, code: str) -> list[Issue]:
        tree = ast.parse(code)
        return self.analyzer.detect(tree, code, "test.py")

    def test_simple_undefined(self):
        issues = self._analyze("x = undefined")
        assert len(issues) == 1
        assert "undefined" in issues[0].message

    def test_defined_before_use(self):
        issues = self._analyze("x = 1\ny = x")
        undefined = [i for i in issues if i.type == IssueType.UNDEFINED_VAR]
        assert len(undefined) == 0

    def test_function_parameters(self):
        code = """
def foo(x, y):
    return x + y
"""
        issues = self._analyze(code)
        undefined = [i for i in issues if i.type == IssueType.UNDEFINED_VAR]
        assert len(undefined) == 0

    def test_for_loop_variable(self):
        code = """
for i in range(10):
    print(i)
"""
        issues = self._analyze(code)
        undefined = [i for i in issues if i.type == IssueType.UNDEFINED_VAR]
        assert len(undefined) == 0

    def test_with_statement(self):
        code = """
with open('file') as f:
    print(f)
"""
        issues = self._analyze(code)
        undefined = [i for i in issues if i.type == IssueType.UNDEFINED_VAR]
        assert len(undefined) == 0

    def test_import_defines_name(self):
        code = """
import os
os.path.exists('/')
"""
        issues = self._analyze(code)
        undefined = [i for i in issues if i.type == IssueType.UNDEFINED_VAR]
        assert len(undefined) == 0

    def test_from_import(self):
        code = """
from os import path
path.exists('/')
"""
        issues = self._analyze(code)
        undefined = [i for i in issues if i.type == IssueType.UNDEFINED_VAR]
        assert len(undefined) == 0

    def test_walrus_operator(self):
        code = """
if (n := 10) > 5:
    print(n)
"""
        issues = self._analyze(code)
        undefined = [i for i in issues if i.type == IssueType.UNDEFINED_VAR]
        assert len(undefined) == 0

    def test_similar_name_suggestion(self):
        code = """
my_variable = 1
x = my_varaible
"""
        issues = self._analyze(code)
        assert len(issues) == 1
        assert issues[0].suggested_fix == "my_variable"


class TestUnusedImportAnalyzer:
    """Tests for unused import detection."""

    def setup_method(self):
        self.analyzer = UnusedImportAnalyzer()

    def _analyze(self, code: str) -> list[Issue]:
        tree = ast.parse(code)
        return self.analyzer.detect(tree, code, "test.py")

    def test_unused_import(self):
        issues = self._analyze("import os")
        assert len(issues) == 1
        assert "os" in issues[0].message

    def test_used_import(self):
        code = """
import os
os.getcwd()
"""
        issues = self._analyze(code)
        assert len(issues) == 0

    def test_unused_from_import(self):
        issues = self._analyze("from os import path")
        assert len(issues) == 1
        assert "path" in issues[0].message

    def test_used_from_import(self):
        code = """
from os import path
path.exists('/')
"""
        issues = self._analyze(code)
        assert len(issues) == 0

    def test_import_used_in_annotation(self):
        code = """
from typing import List
def foo() -> List[int]:
    return []
"""
        issues = self._analyze(code)
        assert len(issues) == 0

    def test_import_used_in_decorator(self):
        code = """
import functools

@functools.lru_cache
def foo():
    pass
"""
        issues = self._analyze(code)
        assert len(issues) == 0

    def test_aliased_import(self):
        code = """
import numpy as np
x = np.array([1, 2, 3])
"""
        issues = self._analyze(code)
        assert len(issues) == 0

    def test_unused_aliased_import(self):
        issues = self._analyze("import numpy as np")
        assert len(issues) == 1
        assert "np" in issues[0].message


class TestTypeErrorAnalyzer:
    """Tests for type error detection."""

    def setup_method(self):
        self.analyzer = TypeErrorAnalyzer()

    def _analyze(self, code: str) -> list[Issue]:
        tree = ast.parse(code)
        return self.analyzer.detect(tree, code, "test.py")

    def test_string_int_addition(self):
        issues = self._analyze('x = "hello" + 5')
        assert len(issues) == 1
        assert issues[0].type == IssueType.TYPE_ERROR

    def test_valid_string_concat(self):
        issues = self._analyze('x = "hello" + " world"')
        assert len(issues) == 0

    def test_valid_int_addition(self):
        issues = self._analyze("x = 1 + 2")
        assert len(issues) == 0

    def test_string_multiplication(self):
        issues = self._analyze('x = "hello" * 3')
        assert len(issues) == 0

    def test_len_on_int(self):
        issues = self._analyze("x = len(5)")
        assert len(issues) == 1

    def test_dict_addition(self):
        issues = self._analyze("x = {'a': 1} + {'b': 2}")
        assert len(issues) == 1


class TestSyntaxIssueAnalyzer:
    """Tests for syntax issue detection."""

    def setup_method(self):
        self.analyzer = SyntaxIssueAnalyzer()

    def _analyze(self, code: str) -> list[Issue]:
        tree = ast.parse(code)
        return self.analyzer.detect(tree, code, "test.py")

    def test_mixed_indentation(self):
        code = "def foo():\n\t x = 1"  # Tab then space
        issues = self._analyze(code)
        indent_issues = [i for i in issues if "indentation" in i.message.lower()]
        assert len(indent_issues) >= 1

    def test_empty_fstring_braces(self):
        # Note: Empty f-string braces `{}` are a syntax error in Python 3.12+
        # so we can't test this through AST analysis. The SyntaxIssueAnalyzer
        # handles this case through source code inspection before parsing.
        # For now, test that valid f-strings don't raise issues
        code = 'x = f"hello {name}"'
        issues = self._analyze(code)
        fstring_issues = [i for i in issues if "f-string" in i.message.lower()]
        # Should not have f-string issues for valid f-strings
        assert len(fstring_issues) == 0

    def test_assert_tuple(self):
        code = "assert (1, 2)"
        issues = self._analyze(code)
        assert_issues = [i for i in issues if "tuple" in i.message.lower()]
        assert len(assert_issues) == 1

    def test_is_with_literal(self):
        code = 'x = "hello"\nif x is "hello":\n    pass'
        issues = self._analyze(code)
        is_issues = [i for i in issues if "==" in i.message]
        assert len(is_issues) >= 1

    def test_comparison_as_statement(self):
        code = "x = 1\nx == 2"
        issues = self._analyze(code)
        no_effect = [i for i in issues if "no effect" in i.message.lower()]
        assert len(no_effect) == 1
