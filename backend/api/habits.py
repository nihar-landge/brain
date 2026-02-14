"""
Habits API Endpoints.
CRUD operations for habits, logging completions, and stats.
"""

from typing import Optional, List
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func

from utils.database import get_db
from models.habits import Habit, HabitLog

router = APIRouter()


# ======================== SCHEMAS ========================


class HabitCreate(BaseModel):
    habit_name: str = Field(..., min_length=1)
    habit_description: Optional[str] = None
    habit_category: Optional[str] = None
    target_frequency: Optional[str] = "daily"
    target_days: Optional[List[int]] = None
    target_time: Optional[str] = None


class HabitUpdate(BaseModel):
    habit_name: Optional[str] = None
    habit_description: Optional[str] = None
    habit_category: Optional[str] = None
    target_frequency: Optional[str] = None
    status: Optional[str] = None


class HabitLogCreate(BaseModel):
    completed: bool = True
    difficulty: Optional[int] = Field(None, ge=1, le=5)
    satisfaction: Optional[int] = Field(None, ge=1, le=5)
    notes: Optional[str] = None
    skip_reason: Optional[str] = None


# ======================== ENDPOINTS ========================


@router.post("", response_model=dict)
async def create_habit(habit: HabitCreate, db: Session = Depends(get_db)):
    """Create a new habit."""
    new_habit = Habit(
        user_id=1,
        habit_name=habit.habit_name,
        habit_description=habit.habit_description,
        habit_category=habit.habit_category,
        target_frequency=habit.target_frequency,
        target_days=habit.target_days,
        start_date=datetime.now().date(),
    )
    db.add(new_habit)
    db.commit()
    db.refresh(new_habit)
    return {"id": new_habit.id, "status": "success", "message": "Habit created"}


@router.get("", response_model=List[dict])
async def get_habits(status: str = "active", db: Session = Depends(get_db)):
    """List habits."""
    query = db.query(Habit).filter(Habit.user_id == 1)
    if status != "all":
        query = query.filter(Habit.status == status)

    habits = query.order_by(Habit.created_at.desc()).all()
    return [
        {
            "id": h.id,
            "name": h.habit_name,
            "description": h.habit_description,
            "category": h.habit_category,
            "frequency": h.target_frequency,
            "target_days": h.target_days,
            "status": h.status,
            "start_date": str(h.start_date),
            "created_at": str(h.created_at),
        }
        for h in habits
    ]


@router.get("/{habit_id}", response_model=dict)
async def get_habit(habit_id: int, db: Session = Depends(get_db)):
    """Get habit details."""
    habit = db.query(Habit).get(habit_id)
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")

    return {
        "id": habit.id,
        "name": habit.habit_name,
        "description": habit.habit_description,
        "category": habit.habit_category,
        "frequency": habit.target_frequency,
        "target_days": habit.target_days,
        "status": habit.status,
        "start_date": str(habit.start_date),
    }


@router.put("/{habit_id}", response_model=dict)
async def update_habit(habit_id: int, updates: HabitUpdate, db: Session = Depends(get_db)):
    """Update habit."""
    habit = db.query(Habit).get(habit_id)
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")

    update_data = updates.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if hasattr(habit, key):
            setattr(habit, key, value)

    db.commit()
    return {"status": "success", "message": "Habit updated"}


@router.delete("/{habit_id}", response_model=dict)
async def delete_habit(habit_id: int, db: Session = Depends(get_db)):
    """Delete habit."""
    habit = db.query(Habit).get(habit_id)
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")

    db.delete(habit)
    db.commit()
    return {"status": "success", "message": "Habit deleted"}


@router.post("/{habit_id}/log", response_model=dict)
async def log_habit(habit_id: int, log: HabitLogCreate, db: Session = Depends(get_db)):
    """Log habit completion for today."""
    habit = db.query(Habit).get(habit_id)
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")

    today = datetime.now().date()

    # Check if already logged today
    existing = (
        db.query(HabitLog)
        .filter(HabitLog.habit_id == habit_id, HabitLog.log_date == today)
        .first()
    )
    if existing:
        existing.completed = log.completed
        existing.difficulty = log.difficulty
        existing.satisfaction = log.satisfaction
        existing.notes = log.notes
        existing.skip_reason = log.skip_reason
        db.commit()
        return {"status": "success", "message": "Habit log updated"}

    new_log = HabitLog(
        habit_id=habit_id,
        user_id=1,
        log_date=today,
        completed=log.completed,
        difficulty=log.difficulty,
        satisfaction=log.satisfaction,
        notes=log.notes,
        skip_reason=log.skip_reason,
    )
    db.add(new_log)
    db.commit()
    return {"status": "success", "message": "Habit logged"}


@router.get("/{habit_id}/stats", response_model=dict)
async def get_habit_stats(habit_id: int, db: Session = Depends(get_db)):
    """Get habit statistics including streaks and completion rates."""
    habit = db.query(Habit).get(habit_id)
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")

    # All logs ordered by date
    logs = (
        db.query(HabitLog)
        .filter(HabitLog.habit_id == habit_id)
        .order_by(HabitLog.log_date.desc())
        .all()
    )

    total = len(logs)
    completed = sum(1 for l in logs if l.completed)
    rate = round(completed / total, 2) if total > 0 else 0

    # Current streak
    streak = 0
    today = datetime.now().date()
    for i in range(60):  # Check last 60 days
        day = today - timedelta(days=i)
        day_log = next((l for l in logs if l.log_date == day and l.completed), None)
        if day_log:
            streak += 1
        elif i == 0:
            continue  # today might not be logged yet
        else:
            break

    # Last 30 days
    month_ago = today - timedelta(days=30)
    recent_logs = [l for l in logs if l.log_date >= month_ago]
    recent_completed = sum(1 for l in recent_logs if l.completed)
    recent_rate = round(recent_completed / len(recent_logs), 2) if recent_logs else 0

    return {
        "habit_id": habit_id,
        "habit_name": habit.habit_name,
        "total_logs": total,
        "total_completed": completed,
        "completion_rate": rate,
        "current_streak": streak,
        "recent_30d_rate": recent_rate,
        "recent_30d_completed": recent_completed,
    }
