"""Feature extraction for ML model."""

import hashlib
from datetime import datetime
from pathlib import Path

from code_weaver.issues.base import Issue, IssueType, Severity


# Feature indices for vectorization
ISSUE_TYPE_MAP = {
    IssueType.UNDEFINED_VAR: 0,
    IssueType.UNUSED_IMPORT: 1,
    IssueType.TYPE_ERROR: 2,
    IssueType.SYNTAX_ISSUE: 3,
}

SEVERITY_MAP = {
    Severity.ERROR: 0,
    Severity.WARNING: 1,
    Severity.HINT: 2,
}


def extract_features(issue: Issue) -> dict:
    """
    Extract features from an issue for ML prediction.

    Features extracted:
    - Issue type (categorical)
    - Severity level (categorical)
    - File extension / location hints
    - Confidence score
    - Line number (normalized)
    - Time of day (hour, for user patterns)
    - Has suggested fix
    - Context length

    Args:
        issue: The issue to extract features from

    Returns:
        Dictionary of feature names to values
    """
    filepath = Path(issue.filepath)

    # File location features
    is_test_file = "test" in filepath.name.lower() or "tests" in str(filepath).lower()
    is_init_file = filepath.name == "__init__.py"
    path_depth = len(filepath.parts)

    # Time features (for learning user patterns)
    now = datetime.now()
    hour = now.hour

    # Context features
    context = issue.context or {}
    context_keys = len(context)

    return {
        # Issue characteristics
        "issue_type": ISSUE_TYPE_MAP.get(issue.type, -1),
        "severity": SEVERITY_MAP.get(issue.severity, -1),
        "confidence": issue.confidence,
        "has_fix": 1 if issue.suggested_fix else 0,

        # Location features
        "line_number": min(issue.line / 1000, 1.0),  # Normalized
        "column": min(issue.column / 100, 1.0),  # Normalized
        "is_test_file": 1 if is_test_file else 0,
        "is_init_file": 1 if is_init_file else 0,
        "path_depth": min(path_depth / 10, 1.0),  # Normalized

        # Time features
        "hour": hour / 24,  # Normalized
        "is_business_hours": 1 if 9 <= hour <= 17 else 0,

        # Context features
        "context_richness": min(context_keys / 5, 1.0),  # Normalized

        # Hash of filepath for per-file patterns (hashed to float)
        "file_hash": _hash_to_float(str(filepath)),
    }


def extract_feature_vector(issue: Issue) -> list[float]:
    """
    Extract features as a flat vector for sklearn.

    Args:
        issue: The issue to extract features from

    Returns:
        List of float features
    """
    features = extract_features(issue)
    return [
        float(features["issue_type"]),
        float(features["severity"]),
        features["confidence"],
        float(features["has_fix"]),
        features["line_number"],
        features["column"],
        float(features["is_test_file"]),
        float(features["is_init_file"]),
        features["path_depth"],
        features["hour"],
        float(features["is_business_hours"]),
        features["context_richness"],
        features["file_hash"],
    ]


def get_feature_names() -> list[str]:
    """Get the names of features in order."""
    return [
        "issue_type",
        "severity",
        "confidence",
        "has_fix",
        "line_number",
        "column",
        "is_test_file",
        "is_init_file",
        "path_depth",
        "hour",
        "is_business_hours",
        "context_richness",
        "file_hash",
    ]


def _hash_to_float(s: str) -> float:
    """Hash a string to a float between 0 and 1."""
    h = hashlib.md5(s.encode()).hexdigest()
    return int(h[:8], 16) / (16 ** 8)
