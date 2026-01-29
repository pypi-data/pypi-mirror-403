"""History tracking and rollback support."""

import hashlib
import json
import shutil
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class Snapshot:
    """A snapshot of a file before modification."""

    filepath: str
    content_hash: str
    timestamp: str
    issue_type: str
    issue_message: str
    snapshot_path: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Snapshot":
        """Create from dictionary."""
        return cls(**data)


class HistoryManager:
    """
    Manages file history for rollback support.

    Stores snapshots of files before fixes are applied,
    allowing users to undo changes.
    """

    # Maximum snapshots per file
    MAX_SNAPSHOTS_PER_FILE = 50

    def __init__(self, storage_dir: str | Path | None = None):
        """
        Initialize the history manager.

        Args:
            storage_dir: Directory to store history. Defaults to .code_weaver/history in cwd.
        """
        if storage_dir is None:
            self.storage_dir = Path.cwd() / ".code_weaver" / "history"
        else:
            self.storage_dir = Path(storage_dir)

        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.storage_dir / "index.json"

        # Load existing index
        self._index: dict[str, list[dict]] = self._load_index()

    def save_snapshot(
        self,
        filepath: str | Path,
        issue_type: str,
        issue_message: str,
    ) -> Snapshot:
        """
        Save a snapshot of a file before modification.

        Args:
            filepath: Path to the file to snapshot
            issue_type: Type of issue being fixed
            issue_message: Description of the issue

        Returns:
            Snapshot object
        """
        filepath = Path(filepath).resolve()
        file_key = str(filepath)

        # Read current content
        content = filepath.read_text(encoding="utf-8")
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

        # Create snapshot filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        snapshot_name = f"{filepath.stem}_{timestamp}.py"
        snapshot_path = self.storage_dir / snapshot_name

        # Save content
        snapshot_path.write_text(content, encoding="utf-8")

        # Create snapshot record
        snapshot = Snapshot(
            filepath=file_key,
            content_hash=content_hash,
            timestamp=datetime.now().isoformat(),
            issue_type=issue_type,
            issue_message=issue_message,
            snapshot_path=str(snapshot_path),
        )

        # Update index
        if file_key not in self._index:
            self._index[file_key] = []

        self._index[file_key].append(snapshot.to_dict())

        # Prune old snapshots
        self._prune_snapshots(file_key)

        # Save index
        self._save_index()

        return snapshot

    def get_snapshots(self, filepath: str | Path) -> list[Snapshot]:
        """
        Get all snapshots for a file.

        Args:
            filepath: Path to the file

        Returns:
            List of snapshots, newest first
        """
        file_key = str(Path(filepath).resolve())
        snapshots_data = self._index.get(file_key, [])

        snapshots = [Snapshot.from_dict(d) for d in snapshots_data]
        snapshots.sort(key=lambda s: s.timestamp, reverse=True)

        return snapshots

    def get_latest_snapshot(self, filepath: str | Path) -> Snapshot | None:
        """
        Get the most recent snapshot for a file.

        Args:
            filepath: Path to the file

        Returns:
            Latest snapshot, or None if no snapshots exist
        """
        snapshots = self.get_snapshots(filepath)
        return snapshots[0] if snapshots else None

    def rollback(self, filepath: str | Path, snapshot: Snapshot | None = None) -> bool:
        """
        Rollback a file to a previous state.

        Args:
            filepath: Path to the file to rollback
            snapshot: Specific snapshot to restore. If None, uses latest.

        Returns:
            True if rollback succeeded
        """
        filepath = Path(filepath).resolve()

        if snapshot is None:
            snapshot = self.get_latest_snapshot(filepath)

        if snapshot is None:
            return False

        snapshot_path = Path(snapshot.snapshot_path)
        if not snapshot_path.exists():
            return False

        # Read snapshot content
        content = snapshot_path.read_text(encoding="utf-8")

        # Restore file
        filepath.write_text(content, encoding="utf-8")

        # Remove the used snapshot from index
        file_key = str(filepath)
        if file_key in self._index:
            self._index[file_key] = [
                s for s in self._index[file_key]
                if s["snapshot_path"] != snapshot.snapshot_path
            ]
            self._save_index()

        # Optionally remove the snapshot file
        try:
            snapshot_path.unlink()
        except OSError:
            pass

        return True

    def clear_history(self, filepath: str | Path | None = None):
        """
        Clear history for a file or all files.

        Args:
            filepath: If provided, clear only this file's history.
                     If None, clear all history.
        """
        if filepath is not None:
            file_key = str(Path(filepath).resolve())
            if file_key in self._index:
                # Remove snapshot files
                for snapshot_data in self._index[file_key]:
                    try:
                        Path(snapshot_data["snapshot_path"]).unlink()
                    except OSError:
                        pass
                del self._index[file_key]
        else:
            # Clear all
            for file_key in list(self._index.keys()):
                for snapshot_data in self._index[file_key]:
                    try:
                        Path(snapshot_data["snapshot_path"]).unlink()
                    except OSError:
                        pass
            self._index = {}

        self._save_index()

    def get_statistics(self) -> dict[str, Any]:
        """
        Get statistics about stored history.

        Returns:
            Dictionary with history statistics
        """
        total_snapshots = sum(len(snapshots) for snapshots in self._index.values())
        total_files = len(self._index)

        # Calculate storage size
        total_size = 0
        for file_key, snapshots in self._index.items():
            for snapshot_data in snapshots:
                try:
                    total_size += Path(snapshot_data["snapshot_path"]).stat().st_size
                except OSError:
                    pass

        return {
            "total_files": total_files,
            "total_snapshots": total_snapshots,
            "total_size_bytes": total_size,
            "storage_dir": str(self.storage_dir),
        }

    def _prune_snapshots(self, file_key: str):
        """Remove old snapshots if over the limit."""
        if file_key not in self._index:
            return

        snapshots = self._index[file_key]
        if len(snapshots) <= self.MAX_SNAPSHOTS_PER_FILE:
            return

        # Sort by timestamp (oldest first)
        snapshots.sort(key=lambda s: s["timestamp"])

        # Remove oldest snapshots
        to_remove = snapshots[:-self.MAX_SNAPSHOTS_PER_FILE]
        for snapshot_data in to_remove:
            try:
                Path(snapshot_data["snapshot_path"]).unlink()
            except OSError:
                pass

        self._index[file_key] = snapshots[-self.MAX_SNAPSHOTS_PER_FILE:]

    def _load_index(self) -> dict[str, list[dict]]:
        """Load the index from disk."""
        if not self.index_file.exists():
            return {}

        try:
            with open(self.index_file, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    def _save_index(self):
        """Save the index to disk."""
        with open(self.index_file, "w") as f:
            json.dump(self._index, f, indent=2)
