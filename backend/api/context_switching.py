"""
Context Switching / Time Tracking API Endpoints.
Start/stop timers, log interruptions, deep work analysis, productivity insights.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from utils.database import get_db
from services.context_switching_service import context_switching_service
from models.habits import Habit

router = APIRouter()


# ======================== SCHEMAS ========================


class StartContextRequest(BaseModel):
    context_name: str = Field(..., min_length=1, max_length=200)
    context_type: str = "deep_work"  # deep_work, communication, admin, personal, coding, writing, studying
    task_complexity: Optional[int] = Field(None, ge=1, le=10)
    habit_id: Optional[int] = None  # Link session to a habit (Goal → Habit → Session)


class EndContextRequest(BaseModel):
    context_id: Optional[int] = None
    mood_after: Optional[int] = Field(None, ge=1, le=10)
    energy_after: Optional[int] = Field(None, ge=1, le=10)
    productivity_rating: Optional[int] = Field(None, ge=1, le=10)


class InterruptionRequest(BaseModel):
    interrupted_by: str = "unknown"


# ======================== TIMER ENDPOINTS ========================


@router.post("/start", response_model=dict)
async def start_context(data: StartContextRequest, db: Session = Depends(get_db)):
    """Start a new context/task timer. Automatically ends previous active context."""
    # Validate habit exists if provided
    habit = None
    if data.habit_id:
        habit = (
            db.query(Habit)
            .filter(Habit.id == data.habit_id, Habit.user_id == 1)
            .first()
        )
        if not habit:
            raise HTTPException(status_code=404, detail="Habit not found")

    ctx = context_switching_service.start_context(
        db,
        user_id=1,
        context_name=data.context_name,
        context_type=data.context_type,
        task_complexity=data.task_complexity,
        habit_id=data.habit_id,
    )
    result = {
        "id": ctx.id,
        "context_name": ctx.context_name,
        "context_type": ctx.context_type,
        "started_at": str(ctx.started_at),
        "status": "started",
        "habit_id": ctx.habit_id,
    }
    if habit:
        result["habit_name"] = habit.habit_name
        result["goal_id"] = habit.goal_id
    return result


@router.post("/stop", response_model=dict)
async def stop_context(data: EndContextRequest, db: Session = Depends(get_db)):
    """Stop the current or specified context timer."""
    ctx = context_switching_service.end_context(
        db,
        user_id=1,
        context_id=data.context_id,
        mood_after=data.mood_after,
        energy_after=data.energy_after,
        productivity_rating=data.productivity_rating,
    )
    if not ctx:
        raise HTTPException(status_code=404, detail="No active context found")

    return {
        "id": ctx.id,
        "context_name": ctx.context_name,
        "duration_minutes": ctx.duration_minutes,
        "cognitive_load": ctx.estimated_cognitive_load,
        "status": "stopped",
    }


@router.get("/active", response_model=dict)
async def get_active_context(db: Session = Depends(get_db)):
    """Get the currently active context (for the floating timer widget)."""
    active = context_switching_service.get_active_context(db, user_id=1)
    if not active:
        return {"active": False}
    return {"active": True, **active}


@router.post("/interrupt", response_model=dict)
async def log_interruption(data: InterruptionRequest, db: Session = Depends(get_db)):
    """Log an interruption to the current context."""
    ctx = context_switching_service.log_interruption(
        db,
        user_id=1,
        interrupted_by=data.interrupted_by,
    )
    if not ctx:
        raise HTTPException(status_code=404, detail="No active context to interrupt")
    return {
        "id": ctx.id,
        "status": "interrupted",
        "interrupted_by": data.interrupted_by,
    }


# ======================== ANALYTICS ENDPOINTS ========================


@router.get("/summary", response_model=dict)
async def get_daily_summary(date: Optional[str] = None, db: Session = Depends(get_db)):
    """Get context switching summary for a specific day (default: today)."""
    return context_switching_service.get_daily_summary(db, user_id=1, date=date)


@router.get("/deep-work", response_model=list)
async def get_deep_work_blocks(days: int = 30, db: Session = Depends(get_db)):
    """Get deep work blocks for the last N days."""
    return context_switching_service.get_deep_work_blocks(db, user_id=1, days=days)


@router.get("/optimal-times", response_model=dict)
async def get_optimal_work_times(days: int = 30, db: Session = Depends(get_db)):
    """Analyze historical data to find optimal work times by hour."""
    return context_switching_service.get_optimal_work_times(db, user_id=1, days=days)


@router.get("/attention-residue", response_model=dict)
async def get_attention_residue(days: int = 30, db: Session = Depends(get_db)):
    """Analyze context switching costs and attention residue."""
    return context_switching_service.get_attention_residue_analysis(
        db, user_id=1, days=days
    )
