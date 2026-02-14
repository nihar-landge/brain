"""
Mood Predictor - RandomForest model for mood prediction.
"""

import pickle
import os
from datetime import datetime

import numpy as np
from sqlalchemy.orm import Session

from models.journal import MoodLog, MLModel
from ml.feature_engineering import extract_mood_features
from config import ML_MODELS_DIR


class MoodPredictor:
    """RandomForest-based mood predictor."""

    MODEL_NAME = "mood_predictor"

    def __init__(self, db: Session):
        self.db = db
        self.model = None

    def train(self, user_id: int) -> dict:
        """Train mood prediction model."""
        from sklearn.ensemble import RandomForestRegressor
        from sklearn.model_selection import cross_val_score

        moods = (
            self.db.query(MoodLog)
            .filter(MoodLog.user_id == user_id)
            .order_by(MoodLog.log_date)
            .all()
        )

        if len(moods) < 30:
            return {"status": "error", "message": f"Need 30+ mood logs. Currently: {len(moods)}"}

        # Extract features
        X, y = [], []
        for mood in moods:
            features = extract_mood_features(self.db, user_id, datetime.combine(mood.log_date, mood.log_time))
            X.append(list(features.values()))
            y.append(mood.mood_value)

        X = np.array(X)
        y = np.array(y)

        # Train
        self.model = RandomForestRegressor(
            n_estimators=50, max_depth=5, min_samples_split=5, random_state=42
        )
        self.model.fit(X, y)

        # Evaluate
        cv_folds = min(5, len(X) // 5) if len(X) >= 10 else 2
        scores = cross_val_score(self.model, X, y, cv=cv_folds, scoring="neg_mean_absolute_error")
        mae = -scores.mean()

        # Save model
        os.makedirs(ML_MODELS_DIR, exist_ok=True)
        model_path = os.path.join(ML_MODELS_DIR, f"{self.MODEL_NAME}_v1.pkl")
        with open(model_path, "wb") as f:
            pickle.dump(self.model, f)

        # Save metadata
        ml_model = MLModel(
            user_id=user_id,
            model_name=self.MODEL_NAME,
            model_version="1.0",
            model_type="RandomForest",
            training_date=datetime.utcnow(),
            training_samples=len(X),
            mae=float(mae),
            model_file_path=model_path,
            is_active=True,
        )
        self.db.add(ml_model)
        self.db.commit()

        return {
            "status": "success",
            "model": self.MODEL_NAME,
            "samples": len(X),
            "mae": float(mae),
        }

    def predict(self, user_id: int, target_date: datetime) -> dict:
        """Predict mood for a date."""
        if self.model is None:
            self._load_model()

        if self.model is None:
            return {"prediction": None, "error": "Model not trained"}

        features = extract_mood_features(self.db, user_id, target_date)
        X = np.array([list(features.values())])
        prediction = self.model.predict(X)[0]

        return {
            "prediction": round(float(prediction), 1),
            "features": features,
        }

    def _load_model(self):
        """Load saved model."""
        model_path = os.path.join(ML_MODELS_DIR, f"{self.MODEL_NAME}_v1.pkl")
        if os.path.exists(model_path):
            with open(model_path, "rb") as f:
                self.model = pickle.load(f)
