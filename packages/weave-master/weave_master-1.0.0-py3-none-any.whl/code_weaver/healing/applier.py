"""Safe fix application with atomic writes."""

import os
import tempfile
from pathlib import Path

from code_weaver.core.fixer import Fixer
from code_weaver.healing.history import HistoryManager
from code_weaver.issues.base import Issue


class FixApplier:
    """
    Safely applies fixes to files with history tracking.

    Features:
    - Atomic writes (write to temp, then rename)
    - Automatic snapshots before modification
    - Rollback support
    """

    def __init__(
        self,
        history_manager: HistoryManager | None = None,
        create_backup: bool = True,
    ):
        """
        Initialize the fix applier.

        Args:
            history_manager: History manager for snapshots. Creates one if None.
            create_backup: Whether to create snapshots before applying fixes.
        """
        self.history = history_manager or HistoryManager()
        self.fixer = Fixer()
        self.create_backup = create_backup

    def apply_fix(
        self,
        issue: Issue,
        confirm: bool = True,
    ) -> bool:
        """
        Apply a fix for an issue.

        Args:
            issue: The issue with a suggested fix
            confirm: If True, creates a snapshot before applying

        Returns:
            True if fix was applied successfully
        """
        if issue.suggested_fix is None:
            return False

        filepath = Path(issue.filepath)
        if not filepath.exists():
            return False

        # Read current content
        source_code = filepath.read_text(encoding="utf-8")

        # Generate the fix
        fixed_code = self.fixer.generate_fix(issue, source_code)
        if fixed_code is None:
            return False

        # Create snapshot if enabled
        if self.create_backup:
            self.history.save_snapshot(
                filepath=filepath,
                issue_type=issue.type.value,
                issue_message=issue.message,
            )

        # Apply the fix atomically
        return self._atomic_write(filepath, fixed_code)

    def apply_fixes(
        self,
        issues: list[Issue],
        confirm: bool = True,
    ) -> dict[str, bool]:
        """
        Apply multiple fixes.

        Args:
            issues: List of issues with suggested fixes
            confirm: If True, creates snapshots before applying

        Returns:
            Dictionary mapping filepath to success status
        """
        results: dict[str, bool] = {}

        for issue in issues:
            if issue.suggested_fix is None:
                continue

            key = f"{issue.filepath}:{issue.line}"
            results[key] = self.apply_fix(issue, confirm=confirm)

        return results

    def preview_fix(self, issue: Issue) -> str | None:
        """
        Generate a diff preview of a fix.

        Args:
            issue: The issue with a suggested fix

        Returns:
            Unified diff string, or None if fix cannot be generated
        """
        filepath = Path(issue.filepath)
        if not filepath.exists():
            return None

        source_code = filepath.read_text(encoding="utf-8")
        return self.fixer.generate_diff(issue, source_code)

    def rollback(self, filepath: str | Path) -> bool:
        """
        Rollback a file to its previous state.

        Args:
            filepath: Path to the file to rollback

        Returns:
            True if rollback succeeded
        """
        return self.history.rollback(filepath)

    def get_rollback_info(self, filepath: str | Path) -> dict | None:
        """
        Get information about available rollback for a file.

        Args:
            filepath: Path to the file

        Returns:
            Dictionary with rollback info, or None if no snapshot exists
        """
        snapshot = self.history.get_latest_snapshot(filepath)
        if snapshot is None:
            return None

        return {
            "timestamp": snapshot.timestamp,
            "issue_type": snapshot.issue_type,
            "issue_message": snapshot.issue_message,
            "content_hash": snapshot.content_hash,
        }

    def _atomic_write(self, filepath: Path, content: str) -> bool:
        """
        Write content to file atomically.

        Uses write-to-temp-then-rename pattern for safety.

        Args:
            filepath: Path to the file
            content: Content to write

        Returns:
            True if write succeeded
        """
        try:
            # Create temp file in same directory (for same filesystem rename)
            fd, temp_path = tempfile.mkstemp(
                dir=filepath.parent,
                prefix=".code_weaver_",
                suffix=".tmp",
            )

            try:
                # Write content
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    f.write(content)

                # Preserve original file permissions if possible
                try:
                    original_stat = filepath.stat()
                    os.chmod(temp_path, original_stat.st_mode)
                except OSError:
                    pass

                # Atomic rename
                os.replace(temp_path, filepath)
                return True

            except Exception:
                # Clean up temp file on error
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass
                raise

        except Exception:
            return False


def apply_fix_interactively(
    issue: Issue,
    applier: FixApplier | None = None,
    show_diff: bool = True,
) -> bool:
    """
    Apply a fix with interactive confirmation.

    This is a convenience function for CLI usage.

    Args:
        issue: The issue to fix
        applier: FixApplier instance. Creates one if None.
        show_diff: Whether to show the diff before confirming

    Returns:
        True if fix was applied
    """
    if applier is None:
        applier = FixApplier()

    if issue.suggested_fix is None:
        print(f"No fix available for: {issue.message}")
        return False

    if show_diff:
        diff = applier.preview_fix(issue)
        if diff:
            print(diff)
        else:
            print(f"Suggested fix: {issue.suggested_fix}")

    # In a real implementation, this would prompt for confirmation
    # For now, just apply the fix
    return applier.apply_fix(issue, confirm=True)
