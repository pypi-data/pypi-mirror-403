"""Base Issue class and types for code analysis."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Severity(Enum):
    """Issue severity levels."""
    ERROR = "error"
    WARNING = "warning"
    HINT = "hint"


class IssueType(Enum):
    """Types of issues that can be detected."""
    UNDEFINED_VAR = "undefined_var"
    UNUSED_IMPORT = "unused_import"
    TYPE_ERROR = "type_error"
    SYNTAX_ISSUE = "syntax_issue"


@dataclass
class Issue:
    """Represents a detected code issue with optional fix suggestion."""

    type: IssueType
    severity: Severity
    filepath: str
    line: int
    column: int
    message: str
    suggested_fix: str | None = None
    confidence: float = 0.5
    context: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate confidence is in valid range."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {self.confidence}")

    @property
    def location(self) -> str:
        """Return formatted location string."""
        return f"{self.filepath}:{self.line}:{self.column}"

    def to_dict(self) -> dict[str, Any]:
        """Convert issue to dictionary for serialization."""
        return {
            "type": self.type.value,
            "severity": self.severity.value,
            "filepath": self.filepath,
            "line": self.line,
            "column": self.column,
            "message": self.message,
            "suggested_fix": self.suggested_fix,
            "confidence": self.confidence,
            "context": self.context,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Issue":
        """Create Issue from dictionary."""
        return cls(
            type=IssueType(data["type"]),
            severity=Severity(data["severity"]),
            filepath=data["filepath"],
            line=data["line"],
            column=data["column"],
            message=data["message"],
            suggested_fix=data.get("suggested_fix"),
            confidence=data.get("confidence", 0.5),
            context=data.get("context", {}),
        )
