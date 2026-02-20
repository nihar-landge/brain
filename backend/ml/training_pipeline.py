"""
Training Pipeline - Automated model training and retraining.
"""

from datetime import datetime, timezone, timezone

from sqlalchemy.orm import Session

from ml.mood_predictor import MoodPredictor
from ml.habit_predictor import HabitPredictor


class TrainingPipeline:
    """Manages model training and retraining."""

    def __init__(self, db: Session):
        self.db = db

    def retrain(self, user_id: int, model_name: str = "all") -> dict:
        """Retrain specified model(s)."""
        results = {}

        if model_name in ("all", "mood_predictor"):
            mood = MoodPredictor(self.db)
            results["mood_predictor"] = mood.train(user_id)

        if model_name in ("all", "habit_predictor"):
            habit = HabitPredictor(self.db)
            results["habit_predictor"] = habit.train(user_id)

        return {
            "status": "completed",
            "trained_at": datetime.now(timezone.utc).isoformat(),
            "results": results,
        }
