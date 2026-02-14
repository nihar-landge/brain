"""
Habit Success Predictor - XGBoost model for habit prediction.
"""

import pickle
import os
from datetime import datetime

import numpy as np
from sqlalchemy.orm import Session

from models.habits import Habit, HabitLog
from models.journal import MLModel
from ml.feature_engineering import extract_habit_features
from config import ML_MODELS_DIR


class HabitPredictor:
    """XGBoost-based habit success predictor."""

    MODEL_NAME = "habit_predictor"

    def __init__(self, db: Session):
        self.db = db
        self.model = None

    def train(self, user_id: int) -> dict:
        """Train habit success model."""
        try:
            import xgboost as xgb
        except ImportError:
            return {"status": "error", "message": "XGBoost not installed"}

        logs = (
            self.db.query(HabitLog)
            .filter(HabitLog.user_id == user_id)
            .all()
        )

        if len(logs) < 20:
            return {"status": "error", "message": f"Need 20+ habit logs. Currently: {len(logs)}"}

        # Extract features
        X, y = [], []
        for log in logs:
            features = extract_habit_features(
                self.db, user_id, log.habit_id,
                datetime.combine(log.log_date, log.log_time or datetime.now().time())
            )
            X.append(list(features.values()))
            y.append(1 if log.completed else 0)

        X = np.array(X)
        y = np.array(y)

        # Train
        dtrain = xgb.DMatrix(X, label=y)
        params = {
            "objective": "binary:logistic",
            "max_depth": 6,
            "learning_rate": 0.1,
            "eval_metric": "logloss",
        }
        self.model = xgb.train(params, dtrain, num_boost_round=100)

        # Save
        os.makedirs(ML_MODELS_DIR, exist_ok=True)
        model_path = os.path.join(ML_MODELS_DIR, f"{self.MODEL_NAME}_v1.pkl")
        with open(model_path, "wb") as f:
            pickle.dump(self.model, f)

        # Metadata
        ml_model = MLModel(
            user_id=user_id,
            model_name=self.MODEL_NAME,
            model_version="1.0",
            model_type="XGBoost",
            training_date=datetime.utcnow(),
            training_samples=len(X),
            model_file_path=model_path,
            is_active=True,
        )
        self.db.add(ml_model)
        self.db.commit()

        return {
            "status": "success",
            "model": self.MODEL_NAME,
            "samples": len(X),
        }

    def predict(self, user_id: int, habit_id: int, target_date: datetime) -> dict:
        """Predict habit success probability."""
        try:
            import xgboost as xgb
        except ImportError:
            return {"prediction": None, "error": "XGBoost not installed"}

        if self.model is None:
            self._load_model()

        if self.model is None:
            return {"prediction": None, "error": "Model not trained"}

        features = extract_habit_features(self.db, user_id, habit_id, target_date)
        X = np.array([list(features.values())])
        dtest = xgb.DMatrix(X)
        prediction = self.model.predict(dtest)[0]

        return {
            "prediction": round(float(prediction), 2),
            "features": features,
        }

    def _load_model(self):
        """Load saved model."""
        model_path = os.path.join(ML_MODELS_DIR, f"{self.MODEL_NAME}_v1.pkl")
        if os.path.exists(model_path):
            with open(model_path, "rb") as f:
                self.model = pickle.load(f)
