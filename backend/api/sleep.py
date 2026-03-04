from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from pydantic import BaseModel
from typing import Optional, List

from utils.database import get_db
from models.user import User
from models.sleep import SleepLog
from utils.auth import verify_api_key
from ml.sleep_mood_engine import sleep_mood_engine

router = APIRouter()

class SleepLogCreate(BaseModel):
    bed_time: str # ISO
    wake_time: str # ISO
    deep_sleep_minutes: Optional[int] = None
    rem_sleep_minutes: Optional[int] = None
    light_sleep_minutes: Optional[int] = None
    awake_minutes: Optional[int] = 0
    subjective_rating: Optional[int] = None # 1-5
    factors: List[str] = []
    notes: Optional[str] = None
    source: str = "manual"

@router.post("/log")
async def log_sleep(
    data: SleepLogCreate,
    user: User = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    try:
        bed = datetime.fromisoformat(data.bed_time.replace('Z', '+00:00'))
        wake = datetime.fromisoformat(data.wake_time.replace('Z', '+00:00'))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ISO datetime format")
        
    duration = (wake - bed).total_seconds() / 3600.0
    
    if duration <= 0 or duration > 24:
        raise HTTPException(status_code=400, detail="Invalid sleep duration")

    quality = sleep_mood_engine.generate_quality_score(
        duration, 
        awakenings=1 if data.awake_minutes > 15 else 0, # Rough heuristic
        rem_minutes=data.rem_sleep_minutes or 0,
        deep_minutes=data.deep_sleep_minutes or 0
    )

    log = SleepLog(
        user_id=user.id,
        bed_time=bed,
        wake_time=wake,
        duration_hours=duration,
        deep_sleep_minutes=data.deep_sleep_minutes,
        rem_sleep_minutes=data.rem_sleep_minutes,
        light_sleep_minutes=data.light_sleep_minutes,
        awake_minutes=data.awake_minutes,
        quality_score=quality,
        subjective_rating=data.subjective_rating,
        factors=data.factors,
        notes=data.notes,
        source=data.source
    )
    
    db.add(log)
    db.commit()
    db.refresh(log)
    
    return {"status": "success", "id": log.id, "quality_score": quality, "duration": round(duration, 2)}

@router.get("/correlations")
async def get_sleep_correlations(
    days: int = 30,
    user: User = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Get the calculated correlation between sleep and mood."""
    return sleep_mood_engine.calculate_correlations(db, user.id, days_back=days)

@router.get("/history")
async def get_sleep_history(
    limit: int = 7,
    user: User = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    logs = db.query(SleepLog).filter(
        SleepLog.user_id == user.id
    ).order_by(SleepLog.wake_time.desc()).limit(limit).all()
    
    return [
        {
            "id": l.id,
            "bed_time": str(l.bed_time),
            "wake_time": str(l.wake_time),
            "duration": round(l.duration_hours, 2),
            "quality_score": l.quality_score,
            "subjective_rating": l.subjective_rating,
            "factors": l.factors or []
        }
        for l in logs
    ]
