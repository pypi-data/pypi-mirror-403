"""Tests for the analyzer and detector modules."""

import pytest

from code_weaver.core.analyzer import (
    ScopeTracker,
    find_similar_names,
    get_line_content,
    extract_context,
)
from code_weaver.core.detector import Detector
from code_weaver.issues.base import IssueType, Severity


class TestScopeTracker:
    """Tests for ScopeTracker."""

    def test_define_and_lookup(self):
        tracker = ScopeTracker()
        tracker.define("x", None)
        assert tracker.is_defined("x")
        assert not tracker.is_defined("y")

    def test_nested_scopes(self):
        tracker = ScopeTracker()
        tracker.define("outer", None)

        tracker.push_scope()
        tracker.define("inner", None)
        assert tracker.is_defined("outer")
        assert tracker.is_defined("inner")

        tracker.pop_scope()
        assert tracker.is_defined("outer")
        assert not tracker.is_defined("inner")

    def test_get_all_defined_names(self):
        tracker = ScopeTracker()
        tracker.define("a", None)
        tracker.push_scope()
        tracker.define("b", None)

        names = tracker.get_all_defined_names()
        assert "a" in names
        assert "b" in names


class TestFindSimilarNames:
    """Tests for the find_similar_names function."""

    def test_exact_match(self):
        similar = find_similar_names("test", {"test", "other"})
        assert similar[0] == "test"

    def test_case_insensitive_match(self):
        similar = find_similar_names("Test", {"test", "other"})
        assert "test" in similar

    def test_similar_names(self):
        similar = find_similar_names("testt", {"test", "other", "totally_different"})
        assert "test" in similar

    def test_no_matches(self):
        similar = find_similar_names("xyz", {"abc", "def"}, threshold=0.9)
        assert len(similar) == 0


class TestGetLineContent:
    """Tests for get_line_content function."""

    def test_valid_line(self):
        source = "line1\nline2\nline3"
        assert get_line_content(source, 2) == "line2"

    def test_first_line(self):
        source = "line1\nline2"
        assert get_line_content(source, 1) == "line1"

    def test_invalid_line(self):
        source = "line1\nline2"
        assert get_line_content(source, 5) == ""


class TestExtractContext:
    """Tests for extract_context function."""

    def test_context_extraction(self):
        source = "line1\nline2\nline3\nline4\nline5"
        context = extract_context(source, 3, context_lines=1)
        assert context["before"] == ["line2"]
        assert context["target"] == "line3"
        assert context["after"] == ["line4"]


class TestDetector:
    """Tests for the Detector class."""

    def test_analyze_clean_code(self):
        detector = Detector()
        code = """
def greet(name):
    return f"Hello, {name}!"

print(greet("World"))
"""
        issues = detector.analyze(code, "test.py")
        # Should have no errors (may have hints)
        errors = [i for i in issues if i.severity == Severity.ERROR]
        assert len(errors) == 0

    def test_detect_undefined_variable(self):
        detector = Detector()
        code = """
x = undefined_var
"""
        issues = detector.analyze(code, "test.py")
        undefined = [i for i in issues if i.type == IssueType.UNDEFINED_VAR]
        assert len(undefined) == 1
        assert "undefined_var" in undefined[0].message

    def test_detect_unused_import(self):
        detector = Detector()
        code = """
import os
import sys

print("hello")
"""
        issues = detector.analyze(code, "test.py")
        unused = [i for i in issues if i.type == IssueType.UNUSED_IMPORT]
        assert len(unused) == 2

    def test_detect_type_error(self):
        detector = Detector()
        code = """
x = "hello" + 5
"""
        issues = detector.analyze(code, "test.py")
        type_errors = [i for i in issues if i.type == IssueType.TYPE_ERROR]
        assert len(type_errors) == 1

    def test_syntax_error_handling(self):
        detector = Detector()
        code = """
def broken(
    print("missing close paren"
"""
        issues = detector.analyze(code, "test.py")
        assert len(issues) > 0
        assert issues[0].type == IssueType.SYNTAX_ISSUE

    def test_multiple_issues(self):
        detector = Detector()
        code = """
import unused_module

x = undefined + 5
y = "hello" + 123
"""
        issues = detector.analyze(code, "test.py")
        # Should have: unused import, undefined variable, type error
        assert len(issues) >= 2

    def test_function_scope(self):
        detector = Detector()
        code = """
def foo():
    x = 1
    return x

y = x  # x not defined here
"""
        issues = detector.analyze(code, "test.py")
        undefined = [i for i in issues if i.type == IssueType.UNDEFINED_VAR]
        assert len(undefined) == 1

    def test_class_scope(self):
        detector = Detector()
        code = """
class MyClass:
    def __init__(self):
        self.value = 1

    def get_value(self):
        return self.value
"""
        issues = detector.analyze(code, "test.py")
        errors = [i for i in issues if i.severity == Severity.ERROR]
        assert len(errors) == 0

    def test_comprehension_scope(self):
        detector = Detector()
        code = """
result = [x * 2 for x in range(10)]
# x should not be defined here in Python 3
y = x
"""
        issues = detector.analyze(code, "test.py")
        undefined = [i for i in issues if i.type == IssueType.UNDEFINED_VAR]
        assert len(undefined) == 1
