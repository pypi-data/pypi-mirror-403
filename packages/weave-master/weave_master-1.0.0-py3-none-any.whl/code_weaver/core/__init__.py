"""Core analysis and detection modules."""

from code_weaver.core.analyzer import BaseAnalyzer, ScopeTracker, find_similar_names
from code_weaver.core.detector import Detector
from code_weaver.core.fixer import Fixer

__all__ = [
    "BaseAnalyzer",
    "ScopeTracker",
    "Detector",
    "Fixer",
    "find_similar_names",
]
