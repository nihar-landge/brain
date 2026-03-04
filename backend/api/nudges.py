from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from pydantic import BaseModel

from utils.database import get_db
from models.user import User
from utils.auth import verify_api_key
from services.nudge_service import nudge_engine
from models.nudges import Nudge, NudgeSettings

router = APIRouter()

class NudgeSettingsUpdate(BaseModel):
    habits_enabled: bool = None
    mood_enabled: bool = None
    burnout_warnings_enabled: bool = None
    sleep_suggestions_enabled: bool = None
    insight_enabled: bool = None
    max_nudges_per_day: int = None
    quiet_hours_start: str = None
    quiet_hours_end: str = None

@router.get("")
async def get_active_nudges(
    user: User = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """
    Get all active, unread nudges for the user.
    Also triggers a background evaluation to generate new nudges if needed.
    """
    # In a real app, this evaluation should happen in a cron job (Celery/APScheduler)
    # For now, we evaluate on-demand when they check for nudges
    nudge_engine.evaluate_user(db, user.id)
    
    now = datetime.now(timezone.utc)
    
    # Delete expired nudges
    db.query(Nudge).filter(
        Nudge.user_id == user.id,
        Nudge.expires_at < now
    ).delete(synchronize_session=False)
    db.commit()
    
    nudges = db.query(Nudge).filter(
        Nudge.user_id == user.id,
        Nudge.is_read == False,
        Nudge.is_dismissed == False
    ).order_by(Nudge.created_at.desc()).all()
    
    return [_format_nudge(n) for n in nudges]

@router.post("/{nudge_id}/dismiss")
async def dismiss_nudge(
    nudge_id: int,
    user: User = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    nudge = db.query(Nudge).filter(
        Nudge.id == nudge_id,
        Nudge.user_id == user.id
    ).first()
    
    if not nudge:
        raise HTTPException(status_code=404, detail="Nudge not found")
        
    nudge.is_dismissed = True
    nudge.is_read = True
    db.commit()
    return {"status": "success", "message": "Nudge dismissed"}

@router.post("/{nudge_id}/interact")
async def interact_nudge(
    nudge_id: int,
    user: User = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    nudge = db.query(Nudge).filter(
        Nudge.id == nudge_id,
        Nudge.user_id == user.id
    ).first()
    
    if not nudge:
        raise HTTPException(status_code=404, detail="Nudge not found")
        
    nudge.is_acted_upon = True
    nudge.is_read = True
    db.commit()
    return {"status": "success", "message": "Nudge interaction recorded"}

@router.get("/settings")
async def get_nudge_settings(
    user: User = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    settings = nudge_engine.get_or_create_settings(db, user.id)
    return {
        "habits_enabled": settings.habits_enabled,
        "mood_enabled": settings.mood_enabled,
        "burnout_warnings_enabled": settings.burnout_warnings_enabled,
        "sleep_suggestions_enabled": settings.sleep_suggestions_enabled,
        "insight_enabled": settings.insight_enabled,
        "max_nudges_per_day": settings.max_nudges_per_day,
        "quiet_hours_start": settings.quiet_hours_start,
        "quiet_hours_end": settings.quiet_hours_end
    }

@router.put("/settings")
async def update_nudge_settings(
    updates: NudgeSettingsUpdate,
    user: User = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    settings = nudge_engine.get_or_create_settings(db, user.id)
    
    data = updates.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(settings, key, value)
        
    db.commit()
    return {"status": "success", "message": "Nudge settings updated"}

def _format_nudge(n: Nudge) -> dict:
    return {
        "id": n.id,
        "type": n.nudge_type,
        "title": n.title,
        "message": n.message,
        "action_data": n.action_data or {},
        "created_at": str(n.created_at),
        "expires_at": str(n.expires_at) if n.expires_at else None
    }
