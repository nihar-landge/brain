"""
Context Switching / Time Tracking API Endpoints.
Start/stop timers, log interruptions, deep work analysis, productivity insights.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from utils.database import get_db
from models.user import User
from utils.auth import verify_api_key
from services.context_switching_service import context_switching_service
from models.habits import Habit
from models.dopamine import Task
from services.google_calendar_service import google_calendar_service

router = APIRouter()


# ======================== SCHEMAS ========================


class StartContextRequest(BaseModel):
    context_name: str = Field(..., min_length=1, max_length=200)
    context_type: str = "deep_work"  # deep_work, communication, admin, personal, coding, writing, studying
    task_complexity: Optional[int] = Field(None, ge=1, le=10)
    habit_id: Optional[int] = None  # Link session to a habit (Goal → Habit → Session)
    task_id: Optional[int] = (
        None  # Optional task linkage for spent time + calendar sync
    )


class EndContextRequest(BaseModel):
    context_id: Optional[int] = None
    mood_after: Optional[int] = Field(None, ge=1, le=10)
    energy_after: Optional[int] = Field(None, ge=1, le=10)
    productivity_rating: Optional[int] = Field(None, ge=1, le=10)


class InterruptionRequest(BaseModel):
    interrupted_by: str = "unknown"


# ======================== TIMER ENDPOINTS ========================


@router.post("/start", response_model=dict)
async def start_context(data: StartContextRequest, user: User = Depends(verify_api_key), db: Session = Depends(get_db)):
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

    task = None
    if data.task_id:
        task = db.query(Task).filter(Task.id == data.task_id, Task.user_id == 1).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

    ctx = context_switching_service.start_context(
        db,
        user_id=user.id,
        context_name=data.context_name,
        context_type=data.context_type,
        task_complexity=data.task_complexity,
        habit_id=data.habit_id,
        task_id=data.task_id,
    )
    result = {
        "id": ctx.id,
        "context_name": ctx.context_name,
        "context_type": ctx.context_type,
        "started_at": str(ctx.started_at),
        "status": "started",
        "habit_id": ctx.habit_id,
        "task_id": ctx.task_id,
    }
    if habit:
        result["habit_name"] = habit.habit_name
        result["goal_id"] = habit.goal_id
    if task:
        result["task_title"] = task.title
    return result


@router.post("/stop", response_model=dict)
async def stop_context(data: EndContextRequest, user: User = Depends(verify_api_key), db: Session = Depends(get_db)):
    """Stop the current or specified context timer."""
    ctx = context_switching_service.end_context(
        db,
        user_id=user.id,
        context_id=data.context_id,
        mood_after=data.mood_after,
        energy_after=data.energy_after,
        productivity_rating=data.productivity_rating,
    )
    if not ctx:
        raise HTTPException(status_code=404, detail="No active context found")

    # Auto-sync ended session to Google Calendar if connected and duration >= 5 min
    if (ctx.duration_minutes or 0) >= 5:
        try:
            event_id = await google_calendar_service.create_session_event(
                db, ctx, user_id=user.id
            )
            if event_id:
                ctx.google_event_id = event_id
                db.commit()
        except Exception:
            # Keep timer flow resilient even if calendar sync fails
            pass

    return {
        "id": ctx.id,
        "context_name": ctx.context_name,
        "duration_minutes": ctx.duration_minutes,
        "cognitive_load": ctx.estimated_cognitive_load,
        "status": "stopped",
        "task_id": ctx.task_id,
    }


@router.get("/active", response_model=dict)
async def get_active_context(user: User = Depends(verify_api_key), db: Session = Depends(get_db)):
    """Get the currently active context (for the floating timer widget)."""
    active = context_switching_service.get_active_context(db, user_id=user.id)
    if not active:
        return {"active": False}
    return {"active": True, **active}


@router.post("/interrupt", response_model=dict)
async def log_interruption(data: InterruptionRequest, user: User = Depends(verify_api_key), db: Session = Depends(get_db)):
    """Log an interruption to the current context."""
    ctx = context_switching_service.log_interruption(
        db,
        user_id=user.id,
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
async def get_daily_summary(date: Optional[str] = None, user: User = Depends(verify_api_key), db: Session = Depends(get_db)):
    """Get context switching summary for a specific day (default: today)."""
    return context_switching_service.get_daily_summary(db, user_id=user.id, date=date)


@router.get("/deep-work", response_model=list)
async def get_deep_work_blocks(days: int = 30, user: User = Depends(verify_api_key), db: Session = Depends(get_db)):
    """Get deep work blocks for the last N days."""
    return context_switching_service.get_deep_work_blocks(db, user_id=user.id, days=days)


@router.get("/optimal-times", response_model=dict)
async def get_optimal_work_times(days: int = 30, user: User = Depends(verify_api_key), db: Session = Depends(get_db)):
    """Analyze historical data to find optimal work times by hour."""
    return context_switching_service.get_optimal_work_times(db, user_id=user.id, days=days)


@router.get("/attention-residue", response_model=dict)
async def get_attention_residue(days: int = 30, user: User = Depends(verify_api_key), db: Session = Depends(get_db)):
    """Analyze context switching costs and attention residue."""
    return context_switching_service.get_attention_residue_analysis(
        db, user_id=user.id, days=days
    )
