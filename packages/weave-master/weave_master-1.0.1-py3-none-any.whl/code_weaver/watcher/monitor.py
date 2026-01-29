"""File system monitoring for automatic issue detection."""

import threading
import time
from pathlib import Path
from typing import Callable

from watchdog.events import FileSystemEventHandler, FileModifiedEvent
from watchdog.observers import Observer

from code_weaver.core.detector import Detector
from code_weaver.issues.base import Issue


class CodeWeaverEventHandler(FileSystemEventHandler):
    """
    Watchdog event handler for Python file changes.

    Debounces rapid file saves and ignores non-Python files.
    """

    def __init__(
        self,
        callback: Callable[[str, list[Issue]], None],
        detector: Detector,
        debounce_ms: int = 300,
        ignore_patterns: list[str] | None = None,
    ):
        """
        Initialize the event handler.

        Args:
            callback: Function to call with (filepath, issues) when issues are detected
            detector: Detector instance to use for analysis
            debounce_ms: Milliseconds to wait before processing (debounce rapid saves)
            ignore_patterns: Patterns to ignore (e.g., [".git", "__pycache__"])
        """
        super().__init__()
        self.callback = callback
        self.detector = detector
        self.debounce_ms = debounce_ms
        self.ignore_patterns = ignore_patterns or [
            ".git", "__pycache__", "venv", ".venv",
            "node_modules", ".tox", ".eggs", "*.egg-info",
            "build", "dist", ".code_weaver",
        ]

        # Debounce tracking
        self._pending: dict[str, threading.Timer] = {}
        self._lock = threading.Lock()

    def on_modified(self, event: FileModifiedEvent):
        """Handle file modification events."""
        if event.is_directory:
            return

        filepath = event.src_path

        # Only handle Python files
        if not filepath.endswith(".py"):
            return

        # Check ignore patterns
        for pattern in self.ignore_patterns:
            if pattern in filepath:
                return

        # Debounce the processing
        self._schedule_processing(filepath)

    def _schedule_processing(self, filepath: str):
        """Schedule file processing with debouncing."""
        with self._lock:
            # Cancel any pending timer for this file
            if filepath in self._pending:
                self._pending[filepath].cancel()

            # Schedule new processing
            timer = threading.Timer(
                self.debounce_ms / 1000,
                self._process_file,
                args=[filepath],
            )
            self._pending[filepath] = timer
            timer.start()

    def _process_file(self, filepath: str):
        """Process a file and call the callback with issues."""
        with self._lock:
            self._pending.pop(filepath, None)

        try:
            path = Path(filepath)
            if not path.exists():
                return

            issues = self.detector.analyze_file(path)
            if issues:
                self.callback(filepath, issues)
        except Exception:
            # Silently ignore processing errors
            pass


class FileWatcher:
    """
    Watches directories for Python file changes and detects issues.

    Uses watchdog for efficient file system monitoring.
    """

    def __init__(
        self,
        callback: Callable[[str, list[Issue]], None],
        debounce_ms: int = 300,
        ignore_patterns: list[str] | None = None,
    ):
        """
        Initialize the file watcher.

        Args:
            callback: Function to call when issues are detected
            debounce_ms: Milliseconds to wait before processing
            ignore_patterns: Patterns to ignore
        """
        self.callback = callback
        self.debounce_ms = debounce_ms
        self.ignore_patterns = ignore_patterns
        self.detector = Detector()

        self._observer: Observer | None = None
        self._running = False

    def start(self, path: str | Path, recursive: bool = True):
        """
        Start watching a directory.

        Args:
            path: Directory to watch
            recursive: Whether to watch subdirectories
        """
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(f"Path not found: {path}")

        if not path.is_dir():
            raise ValueError(f"Path must be a directory: {path}")

        handler = CodeWeaverEventHandler(
            callback=self.callback,
            detector=self.detector,
            debounce_ms=self.debounce_ms,
            ignore_patterns=self.ignore_patterns,
        )

        self._observer = Observer()
        self._observer.schedule(handler, str(path), recursive=recursive)
        self._observer.start()
        self._running = True

    def stop(self):
        """Stop watching."""
        if self._observer is not None:
            self._observer.stop()
            self._observer.join()
            self._observer = None
        self._running = False

    def is_running(self) -> bool:
        """Check if the watcher is running."""
        return self._running

    def wait(self):
        """Wait for the watcher to stop (blocking)."""
        if self._observer is not None:
            try:
                while self._running:
                    time.sleep(0.5)
            except KeyboardInterrupt:
                self.stop()

    def __enter__(self) -> "FileWatcher":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()


def watch_directory(
    path: str | Path,
    callback: Callable[[str, list[Issue]], None],
    debounce_ms: int = 300,
    ignore_patterns: list[str] | None = None,
    blocking: bool = True,
) -> FileWatcher:
    """
    Convenience function to watch a directory.

    Args:
        path: Directory to watch
        callback: Function to call when issues are detected
        debounce_ms: Debounce delay in milliseconds
        ignore_patterns: Patterns to ignore
        blocking: If True, blocks until interrupted

    Returns:
        FileWatcher instance
    """
    watcher = FileWatcher(
        callback=callback,
        debounce_ms=debounce_ms,
        ignore_patterns=ignore_patterns,
    )

    watcher.start(path)

    if blocking:
        watcher.wait()

    return watcher
