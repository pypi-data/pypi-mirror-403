"""
Code Weaver - A proactive code healer for Python.

This package provides tools for detecting and fixing common Python issues,
with ML-based learning from user feedback.

Quick Start:
    >>> from code_weaver import analyze_file, analyze_code
    >>> issues = analyze_file("mycode.py")
    >>> issues = analyze_code("x = undefined_var")

Full Control:
    >>> from code_weaver import Weaver
    >>> weaver = Weaver(auto_heal=False, learn=True)
    >>> issues = weaver.analyze("src/")
"""

from pathlib import Path
from typing import Callable

from code_weaver.core.detector import Detector
from code_weaver.core.fixer import Fixer
from code_weaver.healing.applier import FixApplier
from code_weaver.healing.history import HistoryManager
from code_weaver.issues.base import Issue, IssueType, Severity
from code_weaver.ml.feedback import FeedbackStore
from code_weaver.ml.model import FixPredictor
from code_weaver.watcher.monitor import FileWatcher

__version__ = "1.0.1"
__all__ = [
    "Weaver",
    "analyze_file",
    "analyze_code",
    "Issue",
    "IssueType",
    "Severity",
    "Detector",
    "Fixer",
    "FixApplier",
    "HistoryManager",
    "FeedbackStore",
    "FixPredictor",
    "FileWatcher",
]


def analyze_file(filepath: str | Path) -> list[Issue]:
    """
    Analyze a Python file for issues.

    Args:
        filepath: Path to the Python file to analyze

    Returns:
        List of detected issues

    Example:
        >>> issues = analyze_file("mycode.py")
        >>> for issue in issues:
        ...     print(f"{issue.line}: {issue.message}")
    """
    detector = Detector()
    return detector.analyze_file(filepath)


def analyze_code(source_code: str, filepath: str = "<string>") -> list[Issue]:
    """
    Analyze Python source code for issues.

    Args:
        source_code: Python source code to analyze
        filepath: Virtual filepath for error messages

    Returns:
        List of detected issues

    Example:
        >>> issues = analyze_code("x = undefined_var")
        >>> print(issues[0].message)
        "Undefined variable 'undefined_var'"
    """
    detector = Detector()
    return detector.analyze(source_code, filepath)


class Weaver:
    """
    Main interface for the Code Weaver library.

    Provides comprehensive control over code analysis, fix application,
    and ML-based learning.

    Example:
        >>> weaver = Weaver(auto_heal=False, learn=True)
        >>> issues = weaver.analyze("src/")
        >>> for issue in issues:
        ...     if issue.suggested_fix:
        ...         weaver.apply_fix(issue)
    """

    def __init__(
        self,
        auto_heal: bool = False,
        confidence_threshold: float = 0.8,
        learn: bool = True,
    ):
        """
        Initialize the Weaver.

        Args:
            auto_heal: If True, automatically apply high-confidence fixes
            confidence_threshold: Minimum confidence for auto-heal (0.0-1.0)
            learn: If True, enable ML feedback learning
        """
        self.auto_heal = auto_heal
        self.confidence_threshold = confidence_threshold
        self.learn = learn

        self.detector = Detector()
        self.fixer = Fixer()
        self.history = HistoryManager()
        self.applier = FixApplier(history_manager=self.history)
        self.predictor = FixPredictor() if learn else None
        self.feedback_store = FeedbackStore() if learn else None

        self._watcher: FileWatcher | None = None

    def analyze(self, path: str | Path) -> list[Issue]:
        """
        Analyze a file or directory for issues.

        Args:
            path: Path to file or directory

        Returns:
            List of detected issues
        """
        path = Path(path)

        if path.is_file():
            return self.detector.analyze_file(path)
        else:
            all_issues = self.detector.analyze_directory(path)
            return [issue for issues in all_issues.values() for issue in issues]

    def analyze_code(self, source_code: str, filepath: str = "<string>") -> list[Issue]:
        """
        Analyze source code directly.

        Args:
            source_code: Python source code
            filepath: Virtual filepath for messages

        Returns:
            List of detected issues
        """
        return self.detector.analyze(source_code, filepath)

    def apply_fix(self, issue: Issue, force: bool = False) -> bool:
        """
        Apply a fix for an issue.

        If auto_heal is disabled and force is False, this will check
        the ML model's prediction before applying.

        Args:
            issue: The issue to fix
            force: If True, apply without checking confidence

        Returns:
            True if fix was applied
        """
        if issue.suggested_fix is None:
            return False

        # Check ML prediction if not forcing
        if not force and not self.auto_heal and self.predictor:
            decision, confidence = self.predictor.predict(issue)
            if decision != "yes" or confidence < self.confidence_threshold:
                return False

        success = self.applier.apply_fix(issue)

        # Record feedback if learning
        if success and self.feedback_store:
            self.feedback_store.record_feedback(issue, accepted=True)
            if self.predictor:
                self.predictor.maybe_retrain()

        return success

    def preview_fix(self, issue: Issue) -> str | None:
        """
        Generate a diff preview of a fix.

        Args:
            issue: The issue to preview

        Returns:
            Unified diff string, or None if no fix available
        """
        return self.applier.preview_fix(issue)

    def rollback(self, filepath: str | Path) -> bool:
        """
        Rollback the last fix applied to a file.

        Args:
            filepath: Path to the file

        Returns:
            True if rollback succeeded
        """
        return self.applier.rollback(filepath)

    def watch(
        self,
        path: str | Path,
        callback: Callable[[str, list[Issue]], None] | None = None,
        blocking: bool = False,
    ):
        """
        Watch a directory for changes and detect issues.

        Args:
            path: Directory to watch
            callback: Function called with (filepath, issues) on detection
            blocking: If True, block until interrupted
        """
        if callback is None:
            callback = self._default_watch_callback

        self._watcher = FileWatcher(callback=callback)
        self._watcher.start(path)

        if blocking:
            self._watcher.wait()

    def stop_watching(self):
        """Stop the file watcher."""
        if self._watcher:
            self._watcher.stop()
            self._watcher = None

    def record_feedback(self, issue: Issue, accepted: bool, modified: bool = False):
        """
        Record user feedback on a fix suggestion.

        Args:
            issue: The issue that was suggested
            accepted: Whether the user accepted the fix
            modified: Whether the user modified the fix
        """
        if self.feedback_store:
            self.feedback_store.record_feedback(issue, accepted, modified)
            if self.predictor:
                self.predictor.maybe_retrain()

    def get_model_status(self) -> dict:
        """
        Get the status of the ML model.

        Returns:
            Dictionary with model status information
        """
        if self.predictor:
            return self.predictor.get_status()
        return {"trained": False, "learning_enabled": False}

    def _default_watch_callback(self, filepath: str, issues: list[Issue]):
        """Default callback that prints issues."""
        print(f"\nIssues in {filepath}:")
        for issue in issues:
            print(f"  {issue.line}:{issue.column} {issue.severity.value}: {issue.message}")
