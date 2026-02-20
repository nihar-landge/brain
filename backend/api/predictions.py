"""
Prediction API Endpoints.
ML-powered predictions with adaptive confidence scoring (Fix #5).
"""

from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from utils.database import get_db
from models.user import User
from utils.auth import verify_api_key
from services.ml_service import MLService

router = APIRouter()


# ======================== SCHEMAS ========================


class MoodPredictionRequest(BaseModel):
    date: str = Field(..., description="Target date in YYYY-MM-DD format")


class HabitPredictionRequest(BaseModel):
    habit: str = Field(..., description="Habit name")
    date: str = Field(..., description="Target date in YYYY-MM-DD format")
    time: Optional[str] = Field(None, description="Target time in HH:MM format")


class GoalPredictionRequest(BaseModel):
    goal_id: int


# ======================== ENDPOINTS ========================


@router.post("/mood", response_model=dict)
async def predict_mood(req: MoodPredictionRequest, user: User = Depends(verify_api_key), db: Session = Depends(get_db)):
    """
    Predict mood for a specific date.
    Uses adaptive ML with confidence scoring (Fix #5).
    """
    ml_service = MLService(db)
    return ml_service.predict_mood(user_id=user.id, target_date=req.date)


@router.post("/habit", response_model=dict)
async def predict_habit_success(
    req: HabitPredictionRequest, user: User = Depends(verify_api_key), db: Session = Depends(get_db)
):
    """
    Predict success probability for a habit.
    Uses adaptive ML with baselines for limited data (Fix #5).
    """
    ml_service = MLService(db)
    return ml_service.predict_habit_success(
        user_id=user.id,
        habit_name=req.habit,
        target_date=req.date,
        target_time=req.time,
    )


@router.get("/energy", response_model=dict)
async def predict_energy(days_ahead: int = 7, user: User = Depends(verify_api_key), db: Session = Depends(get_db)):
    """Forecast energy levels for the next N days."""
    ml_service = MLService(db)
    return ml_service.get_energy_forecast(user_id=user.id, days_ahead=days_ahead)


@router.get("/status", response_model=dict)
async def get_prediction_status(user: User = Depends(verify_api_key), db: Session = Depends(get_db)):
    """Get ML data availability status and prediction readiness."""
    from ml.adaptive_predictor import AdaptiveMLPredictor

    predictor = AdaptiveMLPredictor(db)
    return predictor.get_data_status(user_id=user.id)


@router.post("/retrain", response_model=dict)
async def retrain_models(model_name: str = "all", user: User = Depends(verify_api_key), db: Session = Depends(get_db)):
    """Trigger model retraining."""
    ml_service = MLService(db)
    return ml_service.retrain_models(user_id=user.id, model_name=model_name)


@router.get("/performance", response_model=dict)
async def get_model_performance(user: User = Depends(verify_api_key), db: Session = Depends(get_db)):
    """Get ML model performance metrics."""
    ml_service = MLService(db)
    return ml_service.get_model_performance(user_id=user.id)
