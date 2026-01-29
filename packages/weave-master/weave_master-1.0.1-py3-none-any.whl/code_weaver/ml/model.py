"""ML model for predicting fix acceptance."""

import pickle
from pathlib import Path
from typing import Any

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score

from code_weaver.issues.base import Issue
from code_weaver.ml.features import extract_feature_vector, get_feature_names
from code_weaver.ml.feedback import FeedbackStore


class FixPredictor:
    """
    ML model that predicts whether a fix should be auto-applied.

    Uses a RandomForest classifier trained on user feedback.
    """

    # Minimum number of samples before training
    MIN_SAMPLES = 10

    # Retrain after this many new feedback items
    RETRAIN_THRESHOLD = 20

    def __init__(self, model_path: str | Path | None = None):
        """
        Initialize the predictor.

        Args:
            model_path: Path to save/load model. Defaults to ~/.config/code_weaver/model.pkl
        """
        if model_path is None:
            config_dir = Path.home() / ".config" / "code_weaver"
            config_dir.mkdir(parents=True, exist_ok=True)
            self.model_path = config_dir / "model.pkl"
        else:
            self.model_path = Path(model_path)

        self.model: RandomForestClassifier | None = None
        self.feedback_store = FeedbackStore()
        self._last_training_count = 0

        # Try to load existing model
        self._load_model()

    def predict(self, issue: Issue) -> tuple[str, float]:
        """
        Predict whether a fix should be applied.

        Args:
            issue: The issue with a suggested fix

        Returns:
            Tuple of (decision, confidence) where decision is "yes", "no", or "ask"
        """
        if self.model is None:
            # No model trained yet, always ask
            return "ask", 0.5

        features = extract_feature_vector(issue)
        proba = self.model.predict_proba([features])[0]

        # proba[1] is probability of acceptance
        acceptance_prob = proba[1] if len(proba) > 1 else 0.5

        # Decision thresholds
        if acceptance_prob >= 0.85:
            return "yes", acceptance_prob
        elif acceptance_prob <= 0.15:
            return "no", 1.0 - acceptance_prob
        else:
            return "ask", acceptance_prob

    def should_auto_apply(self, issue: Issue, threshold: float = 0.85) -> bool:
        """
        Determine if a fix should be auto-applied.

        Args:
            issue: The issue with a suggested fix
            threshold: Confidence threshold for auto-apply

        Returns:
            True if the fix should be auto-applied
        """
        if self.model is None:
            return False

        features = extract_feature_vector(issue)
        proba = self.model.predict_proba([features])[0]
        acceptance_prob = proba[1] if len(proba) > 1 else 0.0

        return acceptance_prob >= threshold

    def train(self, force: bool = False) -> dict[str, Any]:
        """
        Train the model on collected feedback.

        Args:
            force: If True, train even if below minimum samples

        Returns:
            Training statistics
        """
        X, y = self.feedback_store.get_training_data()

        if len(X) < self.MIN_SAMPLES and not force:
            return {
                "status": "insufficient_data",
                "samples": len(X),
                "required": self.MIN_SAMPLES,
            }

        if len(X) == 0:
            return {
                "status": "no_data",
                "samples": 0,
            }

        # Check for class balance
        positive = sum(y)
        negative = len(y) - positive

        if positive == 0 or negative == 0:
            return {
                "status": "imbalanced",
                "samples": len(X),
                "positive": positive,
                "negative": negative,
            }

        # Train the model
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=2,
            min_samples_leaf=1,
            random_state=42,
            class_weight="balanced",
        )

        self.model.fit(X, y)
        self._last_training_count = len(X)

        # Calculate cross-validation score if enough samples
        cv_score = None
        if len(X) >= 10:
            try:
                scores = cross_val_score(self.model, X, y, cv=min(5, len(X)))
                cv_score = scores.mean()
            except Exception:
                pass

        # Save the model
        self._save_model()

        # Get feature importances
        importances = dict(zip(get_feature_names(), self.model.feature_importances_))

        return {
            "status": "trained",
            "samples": len(X),
            "positive": positive,
            "negative": negative,
            "cv_score": cv_score,
            "feature_importances": importances,
        }

    def maybe_retrain(self) -> dict[str, Any] | None:
        """
        Retrain if enough new feedback has been collected.

        Returns:
            Training statistics if retrained, None otherwise
        """
        current_count = self.feedback_store.count()

        if current_count - self._last_training_count >= self.RETRAIN_THRESHOLD:
            return self.train()

        return None

    def reset(self):
        """Reset the model to untrained state."""
        self.model = None
        self._last_training_count = 0

        if self.model_path.exists():
            self.model_path.unlink()

    def get_status(self) -> dict[str, Any]:
        """
        Get the current status of the model.

        Returns:
            Dictionary with model status
        """
        feedback_stats = self.feedback_store.get_statistics()

        return {
            "trained": self.model is not None,
            "model_path": str(self.model_path),
            "model_exists": self.model_path.exists(),
            "feedback_count": feedback_stats["total"],
            "acceptance_rate": feedback_stats["acceptance_rate"],
            "last_training_count": self._last_training_count,
            "needs_retraining": feedback_stats["total"] - self._last_training_count >= self.RETRAIN_THRESHOLD,
            "feedback_by_type": feedback_stats["by_type"],
        }

    def _save_model(self):
        """Save the model to disk."""
        if self.model is not None:
            with open(self.model_path, "wb") as f:
                pickle.dump(
                    {
                        "model": self.model,
                        "training_count": self._last_training_count,
                    },
                    f,
                )

    def _load_model(self):
        """Load the model from disk."""
        if self.model_path.exists():
            try:
                with open(self.model_path, "rb") as f:
                    data = pickle.load(f)
                    self.model = data.get("model")
                    self._last_training_count = data.get("training_count", 0)
            except Exception:
                # If loading fails, start fresh
                self.model = None
                self._last_training_count = 0
