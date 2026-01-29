"""Tests for the ML modules."""

import tempfile
from pathlib import Path

import pytest

from code_weaver.issues.base import Issue, IssueType, Severity
from code_weaver.ml.features import (
    extract_features,
    extract_feature_vector,
    get_feature_names,
)
from code_weaver.ml.feedback import Feedback, FeedbackStore
from code_weaver.ml.model import FixPredictor


def create_test_issue(
    issue_type: IssueType = IssueType.UNDEFINED_VAR,
    severity: Severity = Severity.ERROR,
    filepath: str = "test.py",
    line: int = 10,
    message: str = "Test issue",
    suggested_fix: str | None = "Fix it",
    confidence: float = 0.8,
) -> Issue:
    """Create a test issue."""
    return Issue(
        type=issue_type,
        severity=severity,
        filepath=filepath,
        line=line,
        column=0,
        message=message,
        suggested_fix=suggested_fix,
        confidence=confidence,
    )


class TestFeatureExtraction:
    """Tests for feature extraction."""

    def test_extract_features_basic(self):
        issue = create_test_issue()
        features = extract_features(issue)

        assert "issue_type" in features
        assert "severity" in features
        assert "confidence" in features
        assert features["confidence"] == 0.8

    def test_extract_features_test_file(self):
        issue = create_test_issue(filepath="tests/test_something.py")
        features = extract_features(issue)
        assert features["is_test_file"] == 1

    def test_extract_features_init_file(self):
        issue = create_test_issue(filepath="package/__init__.py")
        features = extract_features(issue)
        assert features["is_init_file"] == 1

    def test_extract_feature_vector(self):
        issue = create_test_issue()
        vector = extract_feature_vector(issue)

        assert isinstance(vector, list)
        assert len(vector) == len(get_feature_names())
        assert all(isinstance(v, (int, float)) for v in vector)

    def test_feature_names(self):
        names = get_feature_names()
        assert "issue_type" in names
        assert "severity" in names
        assert "confidence" in names


class TestFeedbackStore:
    """Tests for the FeedbackStore."""

    def test_record_and_retrieve_feedback(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FeedbackStore(Path(tmpdir) / "feedback.jsonl")
            issue = create_test_issue()

            store.record_feedback(issue, accepted=True)

            feedback_list = store.get_all_feedback()
            assert len(feedback_list) == 1
            assert feedback_list[0].accepted is True

    def test_multiple_feedback(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FeedbackStore(Path(tmpdir) / "feedback.jsonl")

            for i in range(5):
                issue = create_test_issue(line=i)
                store.record_feedback(issue, accepted=i % 2 == 0)

            feedback_list = store.get_all_feedback()
            assert len(feedback_list) == 5

    def test_get_training_data(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FeedbackStore(Path(tmpdir) / "feedback.jsonl")

            issue1 = create_test_issue(line=1)
            issue2 = create_test_issue(line=2)
            store.record_feedback(issue1, accepted=True)
            store.record_feedback(issue2, accepted=False)

            X, y = store.get_training_data()
            assert len(X) == 2
            assert len(y) == 2
            assert y == [1, 0]

    def test_statistics(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FeedbackStore(Path(tmpdir) / "feedback.jsonl")

            for i in range(10):
                issue = create_test_issue(line=i)
                store.record_feedback(issue, accepted=i < 7)

            stats = store.get_statistics()
            assert stats["total"] == 10
            assert stats["accepted"] == 7
            assert stats["rejected"] == 3
            assert stats["acceptance_rate"] == 0.7

    def test_clear(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FeedbackStore(Path(tmpdir) / "feedback.jsonl")

            issue = create_test_issue()
            store.record_feedback(issue, accepted=True)
            assert store.count() == 1

            store.clear()
            assert store.count() == 0


class TestFeedback:
    """Tests for the Feedback dataclass."""

    def test_to_dict(self):
        feedback = Feedback(
            issue_type="undefined_var",
            severity="error",
            filepath="test.py",
            line=10,
            message="Test",
            suggested_fix="Fix",
            accepted=True,
            modified=False,
            timestamp="2024-01-01T00:00:00",
            features=[1.0, 2.0, 3.0],
        )
        d = feedback.to_dict()
        assert d["issue_type"] == "undefined_var"
        assert d["accepted"] is True

    def test_from_dict(self):
        data = {
            "issue_type": "unused_import",
            "severity": "warning",
            "filepath": "test.py",
            "line": 1,
            "message": "Unused",
            "suggested_fix": None,
            "accepted": False,
            "modified": False,
            "timestamp": "2024-01-01T00:00:00",
            "features": [1.0],
        }
        feedback = Feedback.from_dict(data)
        assert feedback.issue_type == "unused_import"
        assert feedback.accepted is False


class TestFixPredictor:
    """Tests for the ML predictor."""

    def test_predict_without_training(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            predictor = FixPredictor(Path(tmpdir) / "model.pkl")
            issue = create_test_issue()

            decision, confidence = predictor.predict(issue)
            assert decision == "ask"  # No model, always ask
            assert confidence == 0.5

    def test_should_auto_apply_without_training(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            predictor = FixPredictor(Path(tmpdir) / "model.pkl")
            issue = create_test_issue()

            assert predictor.should_auto_apply(issue) is False

    def test_train_insufficient_data(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            predictor = FixPredictor(Path(tmpdir) / "model.pkl")
            result = predictor.train()

            assert result["status"] in ("no_data", "insufficient_data")

    def test_train_with_data(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create feedback store with enough data
            store_path = Path(tmpdir) / "feedback.jsonl"
            store = FeedbackStore(store_path)

            # Add training data
            for i in range(15):
                issue = create_test_issue(
                    line=i,
                    issue_type=IssueType.UNDEFINED_VAR if i % 2 == 0 else IssueType.UNUSED_IMPORT,
                )
                store.record_feedback(issue, accepted=i % 3 != 0)

            # Train the model
            predictor = FixPredictor(Path(tmpdir) / "model.pkl")
            predictor.feedback_store = store
            result = predictor.train()

            assert result["status"] == "trained"
            assert result["samples"] == 15

    def test_get_status(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            predictor = FixPredictor(Path(tmpdir) / "model.pkl")
            status = predictor.get_status()

            assert "trained" in status
            assert "feedback_count" in status
            assert status["trained"] is False

    def test_reset(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            model_path = Path(tmpdir) / "model.pkl"
            predictor = FixPredictor(model_path)

            # Create a dummy model file
            model_path.write_text("dummy")
            assert model_path.exists()

            predictor.reset()
            assert not model_path.exists()

    def test_model_persistence(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            model_path = Path(tmpdir) / "model.pkl"
            store_path = Path(tmpdir) / "feedback.jsonl"

            # Create and train a model
            store = FeedbackStore(store_path)
            for i in range(15):
                issue = create_test_issue(line=i)
                store.record_feedback(issue, accepted=i % 2 == 0)

            predictor1 = FixPredictor(model_path)
            predictor1.feedback_store = store
            predictor1.train()

            # Load the model in a new predictor
            predictor2 = FixPredictor(model_path)
            assert predictor2.model is not None

            # Should make predictions
            issue = create_test_issue()
            decision, confidence = predictor2.predict(issue)
            assert decision in ("yes", "no", "ask")


class TestIntegration:
    """Integration tests for the ML pipeline."""

    def test_full_feedback_loop(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store_path = Path(tmpdir) / "feedback.jsonl"
            model_path = Path(tmpdir) / "model.pkl"

            store = FeedbackStore(store_path)
            predictor = FixPredictor(model_path)
            predictor.feedback_store = store

            # Simulate user interactions
            issues = [
                create_test_issue(issue_type=IssueType.UNUSED_IMPORT, line=i)
                for i in range(20)
            ]

            # User accepts most unused import fixes
            for i, issue in enumerate(issues):
                store.record_feedback(issue, accepted=i < 16)  # 80% accept rate

            # Train the model
            result = predictor.train()
            assert result["status"] == "trained"

            # New unused import issue should have high acceptance prediction
            new_issue = create_test_issue(issue_type=IssueType.UNUSED_IMPORT)
            decision, confidence = predictor.predict(new_issue)

            # The model should learn to suggest acceptance
            assert decision in ("yes", "ask")
