"""
ML Service - Machine learning predictions coordinator.
"""

from typing import Optional
from datetime import datetime

from sqlalchemy.orm import Session

from models.journal import JournalEntry, MoodLog, Prediction
from services.gemini_service import gemini_service


class MLService:
    """
    Coordinates ML predictions across all model types.
    Delegates to individual predictors and the AdaptiveMLPredictor.
    """

    def __init__(self, db: Session):
        self.db = db

    def predict_mood(self, user_id: int, target_date: str) -> dict:
        """Predict mood for a target date."""
        from ml.adaptive_predictor import AdaptiveMLPredictor

        predictor = AdaptiveMLPredictor(self.db)
        result = predictor.predict_mood(user_id, target_date)

        # Store prediction
        if result.get("prediction") is not None:
            pred = Prediction(
                user_id=user_id,
                prediction_type="mood",
                prediction_date=datetime.now().date(),
                target_date=datetime.strptime(target_date, "%Y-%m-%d").date(),
                predicted_value=result["prediction"],
                confidence=result.get("confidence", 0),
                model_name=result.get("method", "adaptive"),
                model_version="1.0",
            )
            self.db.add(pred)
            self.db.commit()

        # Add natural language explanation
        if result.get("use_prediction", True) and result.get("prediction") is not None:
            result["explanation"] = gemini_service.explain_prediction(
                "mood",
                result["prediction"],
                result.get("confidence", 0),
                result.get("factors", ["Historical patterns"]),
            )

        return result

    def predict_habit_success(
        self,
        user_id: int,
        habit_name: str,
        target_date: str,
        target_time: Optional[str] = None,
    ) -> dict:
        """Predict habit success probability."""
        from ml.adaptive_predictor import AdaptiveMLPredictor

        predictor = AdaptiveMLPredictor(self.db)
        result = predictor.predict_habit_success(
            user_id, habit_name, target_date, target_time
        )

        # Store prediction
        if result.get("prediction") is not None:
            pred = Prediction(
                user_id=user_id,
                prediction_type="habit",
                prediction_target=habit_name,
                prediction_date=datetime.now().date(),
                target_date=datetime.strptime(target_date, "%Y-%m-%d").date(),
                predicted_value=result["prediction"],
                confidence=result.get("confidence", 0),
                model_name=result.get("method", "baseline"),
                model_version="1.0",
            )
            self.db.add(pred)
            self.db.commit()

        return result

    def get_energy_forecast(self, user_id: int, days_ahead: int = 7) -> dict:
        """Forecast energy levels."""
        from ml.adaptive_predictor import AdaptiveMLPredictor

        predictor = AdaptiveMLPredictor(self.db)
        return predictor.forecast_energy(user_id, days_ahead)

    def get_model_performance(self, user_id: int) -> dict:
        """Get ML model performance metrics."""
        from models.journal import MLModel

        models = (
            self.db.query(MLModel)
            .filter(MLModel.user_id == user_id, MLModel.is_active == True)
            .all()
        )

        return {
            "models": [
                {
                    "name": m.model_name,
                    "version": m.model_version,
                    "type": m.model_type,
                    "accuracy": m.accuracy,
                    "mae": m.mae,
                    "training_date": str(m.training_date) if m.training_date else None,
                    "training_samples": m.training_samples,
                }
                for m in models
            ],
            "total_models": len(models),
        }

    def retrain_models(self, user_id: int, model_name: str = "all") -> dict:
        """Trigger model retraining."""
        from ml.training_pipeline import TrainingPipeline

        pipeline = TrainingPipeline(self.db)
        return pipeline.retrain(user_id, model_name)
