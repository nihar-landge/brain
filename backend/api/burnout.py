from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from utils.database import get_db
from models.user import User
from utils.auth import verify_api_key
from ml.burnout_predictor import burnout_predictor

router = APIRouter()

@router.get("/risk")
async def get_burnout_risk(
    user: User = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Calculate current burnout risk based on recent data."""
    # Burnout predictor analyzes the last 14 days
    result = burnout_predictor.calculate_risk(db, user.id)
    return result

@router.get("/factors")
async def get_burnout_factors(
    user: User = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Detail specific metrics driving the burnout risk."""
    result = burnout_predictor.calculate_risk(db, user.id)
    return {
        "metrics": result["metrics"],
        "primary_insight": result["primary_insight"]
    }
