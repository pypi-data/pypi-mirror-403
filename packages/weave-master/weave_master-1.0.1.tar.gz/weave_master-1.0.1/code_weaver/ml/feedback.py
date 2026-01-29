"""User feedback collection and storage."""

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from code_weaver.issues.base import Issue
from code_weaver.ml.features import extract_feature_vector, get_feature_names


@dataclass
class Feedback:
    """Represents user feedback on a suggested fix."""

    issue_type: str
    severity: str
    filepath: str
    line: int
    message: str
    suggested_fix: str | None
    accepted: bool  # True if user accepted, False if rejected
    modified: bool  # True if user modified the fix
    timestamp: str
    features: list[float]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Feedback":
        """Create from dictionary."""
        return cls(**data)


class FeedbackStore:
    """
    Stores and manages user feedback for ML training.

    Feedback is stored in a JSON lines file for easy appending
    and streaming reads.
    """

    def __init__(self, storage_path: str | Path | None = None):
        """
        Initialize the feedback store.

        Args:
            storage_path: Path to store feedback. Defaults to ~/.config/code_weaver/feedback.jsonl
        """
        if storage_path is None:
            config_dir = Path.home() / ".config" / "code_weaver"
            config_dir.mkdir(parents=True, exist_ok=True)
            self.storage_path = config_dir / "feedback.jsonl"
        else:
            self.storage_path = Path(storage_path)
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)

    def record_feedback(
        self,
        issue: Issue,
        accepted: bool,
        modified: bool = False,
    ) -> Feedback:
        """
        Record user feedback on a fix.

        Args:
            issue: The issue that was suggested
            accepted: Whether the user accepted the fix
            modified: Whether the user modified the fix

        Returns:
            The recorded Feedback object
        """
        feedback = Feedback(
            issue_type=issue.type.value,
            severity=issue.severity.value,
            filepath=issue.filepath,
            line=issue.line,
            message=issue.message,
            suggested_fix=issue.suggested_fix,
            accepted=accepted,
            modified=modified,
            timestamp=datetime.now().isoformat(),
            features=extract_feature_vector(issue),
        )

        # Append to file
        with open(self.storage_path, "a") as f:
            f.write(json.dumps(feedback.to_dict()) + "\n")

        return feedback

    def get_all_feedback(self) -> list[Feedback]:
        """
        Load all recorded feedback.

        Returns:
            List of all feedback records
        """
        if not self.storage_path.exists():
            return []

        feedback_list = []
        with open(self.storage_path, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        data = json.loads(line)
                        feedback_list.append(Feedback.from_dict(data))
                    except json.JSONDecodeError:
                        continue

        return feedback_list

    def get_training_data(self) -> tuple[list[list[float]], list[int]]:
        """
        Get training data in format suitable for sklearn.

        Returns:
            Tuple of (feature_matrix, labels) where labels are 1 for accepted, 0 for rejected
        """
        feedback_list = self.get_all_feedback()

        if not feedback_list:
            return [], []

        X = [fb.features for fb in feedback_list]
        y = [1 if fb.accepted else 0 for fb in feedback_list]

        return X, y

    def get_statistics(self) -> dict[str, Any]:
        """
        Get statistics about collected feedback.

        Returns:
            Dictionary with feedback statistics
        """
        feedback_list = self.get_all_feedback()

        if not feedback_list:
            return {
                "total": 0,
                "accepted": 0,
                "rejected": 0,
                "modified": 0,
                "acceptance_rate": 0.0,
                "by_type": {},
            }

        accepted = sum(1 for fb in feedback_list if fb.accepted)
        rejected = len(feedback_list) - accepted
        modified = sum(1 for fb in feedback_list if fb.modified)

        # Group by issue type
        by_type: dict[str, dict[str, int]] = {}
        for fb in feedback_list:
            if fb.issue_type not in by_type:
                by_type[fb.issue_type] = {"accepted": 0, "rejected": 0}
            if fb.accepted:
                by_type[fb.issue_type]["accepted"] += 1
            else:
                by_type[fb.issue_type]["rejected"] += 1

        return {
            "total": len(feedback_list),
            "accepted": accepted,
            "rejected": rejected,
            "modified": modified,
            "acceptance_rate": accepted / len(feedback_list) if feedback_list else 0.0,
            "by_type": by_type,
        }

    def clear(self):
        """Clear all stored feedback."""
        if self.storage_path.exists():
            self.storage_path.unlink()

    def count(self) -> int:
        """Get the number of feedback records."""
        if not self.storage_path.exists():
            return 0

        count = 0
        with open(self.storage_path, "r") as f:
            for line in f:
                if line.strip():
                    count += 1
        return count
