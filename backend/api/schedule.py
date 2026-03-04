from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from utils.database import get_db
from models.user import User
from utils.auth import verify_api_key
from ml.schedule_optimizer import schedule_optimizer

router = APIRouter()

@router.get("/optimal")
async def get_optimal_schedule(
    user: User = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """
    Get recommended daily chunks (deep work, shallow work, rest) 
    based on historical productivity patterns.
    """
    result = schedule_optimizer.get_optimal_schedule(db, user.id)
    return result

@router.get("/recommendations")
async def get_schedule_recommendations(
    user: User = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """
    Slightly different view focusing purely on actionable insights.
    """
    result = schedule_optimizer.get_optimal_schedule(db, user.id)
    return {
        "status": result["status"],
        "insight": result["insight"],
        "peak_hour": result["peak_productivity_hour"]
    }
