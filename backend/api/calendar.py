"""
Calendar API.
Internal calendar feed + Google Calendar OAuth/sync + timezone settings.
"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from models.context import ContextLog
from models.dopamine import Task, CalendarIntegration
from models.goals import Goal
from models.habits import Habit
from models.user import User
from services.google_calendar_service import google_calendar_service
from utils.database import get_db

router = APIRouter()
public_router = APIRouter()


class TimezoneUpdate(BaseModel):
    timezone: str = Field(..., min_length=2, max_length=100)


@router.get("/events", response_model=dict)
async def get_calendar_events(
    start: Optional[str] = Query(None, description="ISO datetime start"),
    end: Optional[str] = Query(None, description="ISO datetime end"),
    db: Session = Depends(get_db),
):
    """Return merged calendar events from tasks + context sessions."""
    now = datetime.utcnow()
    start_dt = datetime.fromisoformat(start) if start else (now - timedelta(days=7))
    end_dt = datetime.fromisoformat(end) if end else (now + timedelta(days=21))

    tasks = (
        db.query(Task)
        .filter(
            Task.user_id == 1,
            (
                (
                    Task.scheduled_at.isnot(None)
                    & (Task.scheduled_at >= start_dt)
                    & (Task.scheduled_at <= end_dt)
                )
                | (
                    Task.due_date.isnot(None)
                    & (Task.due_date >= start_dt.date())
                    & (Task.due_date <= end_dt.date())
                )
            ),
        )
        .all()
    )

    contexts = (
        db.query(ContextLog)
        .filter(
            ContextLog.user_id == 1,
            ContextLog.started_at >= start_dt,
            ContextLog.started_at <= end_dt,
        )
        .all()
    )

    goal_ids = {t.goal_id for t in tasks if t.goal_id}
    habit_ids = {t.habit_id for t in tasks if t.habit_id}
    context_task_ids = {c.task_id for c in contexts if c.task_id}
    all_task_ids = {t.id for t in tasks} | context_task_ids

    goal_map = {}
    if goal_ids:
        goals = db.query(Goal).filter(Goal.id.in_(goal_ids)).all()
        goal_map = {g.id: g.goal_title for g in goals}

    habit_map = {}
    if habit_ids:
        habits = db.query(Habit).filter(Habit.id.in_(habit_ids)).all()
        habit_map = {h.id: h.habit_name for h in habits}

    task_map = {}
    if all_task_ids:
        linked_tasks = db.query(Task).filter(Task.id.in_(all_task_ids)).all()
        task_map = {t.id: t for t in linked_tasks}

    events = []

    # Planned task events
    for t in tasks:
        if t.scheduled_at:
            end_ts = t.scheduled_end or (t.scheduled_at + timedelta(minutes=30))
            events.append(
                {
                    "id": f"task-{t.id}",
                    "type": "task_planned",
                    "title": t.title,
                    "start": t.scheduled_at.isoformat(),
                    "end": end_ts.isoformat(),
                    "all_day": False,
                    "status": t.status,
                    "priority": t.priority,
                    "goal_title": goal_map.get(t.goal_id),
                    "habit_name": habit_map.get(t.habit_id),
                    "spent_minutes": t.spent_minutes or 0,
                    "estimated_minutes": t.estimated_minutes,
                }
            )
        elif t.due_date:
            start_day = datetime.combine(t.due_date, datetime.min.time())
            end_day = start_day + timedelta(days=1)
            events.append(
                {
                    "id": f"task-{t.id}",
                    "type": "task_all_day",
                    "title": t.title,
                    "start": start_day.isoformat(),
                    "end": end_day.isoformat(),
                    "all_day": True,
                    "status": t.status,
                    "priority": t.priority,
                    "goal_title": goal_map.get(t.goal_id),
                    "habit_name": habit_map.get(t.habit_id),
                    "spent_minutes": t.spent_minutes or 0,
                    "estimated_minutes": t.estimated_minutes,
                }
            )

    # Actual logged timer sessions
    for c in contexts:
        task = task_map.get(c.task_id)
        title = c.context_name or (task.title if task else "Focus Session")
        events.append(
            {
                "id": f"context-{c.id}",
                "type": "session_logged",
                "title": title,
                "start": c.started_at.isoformat() if c.started_at else None,
                "end": c.ended_at.isoformat() if c.ended_at else None,
                "all_day": False,
                "duration_minutes": c.duration_minutes,
                "context_type": c.context_type,
                "task_id": c.task_id,
                "task_title": task.title if task else None,
            }
        )

    events.sort(key=lambda e: e.get("start") or "")

    return {
        "start": start_dt.isoformat(),
        "end": end_dt.isoformat(),
        "events": events,
    }


@router.get("/timezone", response_model=dict)
async def get_timezone(db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == 1).first()
    if not user:
        user = User(id=1, username="default_user", timezone="UTC")
        db.add(user)
        db.commit()
        db.refresh(user)

    return {"timezone": user.timezone or "UTC"}


@router.put("/timezone", response_model=dict)
async def update_timezone(data: TimezoneUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == 1).first()
    if not user:
        user = User(id=1, username="default_user")
        db.add(user)

    user.timezone = data.timezone
    user.last_active_at = datetime.utcnow()
    db.commit()
    return {"status": "success", "timezone": user.timezone}


@router.get("/google/status", response_model=dict)
async def google_status(db: Session = Depends(get_db)):
    integration = (
        db.query(CalendarIntegration)
        .filter(
            CalendarIntegration.user_id == 1,
            CalendarIntegration.provider == "google",
        )
        .first()
    )
    return {
        "configured": google_calendar_service.is_configured(),
        "connected": bool(integration and integration.is_connected),
        "calendar_id": integration.calendar_id if integration else None,
        "last_sync_at": str(integration.last_sync_at)
        if integration and integration.last_sync_at
        else None,
    }


@router.get("/google/auth-url", response_model=dict)
async def google_auth_url():
    if not google_calendar_service.is_configured():
        raise HTTPException(status_code=400, detail="Google Calendar is not configured")
    return {"auth_url": google_calendar_service.get_auth_url(user_id=1)}


@public_router.get("/google/callback", response_model=dict)
async def google_callback(
    code: str, state: Optional[str] = None, db: Session = Depends(get_db)
):
    if not google_calendar_service.is_configured():
        raise HTTPException(status_code=400, detail="Google Calendar is not configured")

    user_id = int(state) if state and state.isdigit() else 1
    await google_calendar_service.exchange_code(db, code, user_id=user_id)
    return {"status": "success", "message": "Google Calendar connected"}


@router.post("/google/disconnect", response_model=dict)
async def google_disconnect(db: Session = Depends(get_db)):
    await google_calendar_service.disconnect(db, user_id=1)
    return {"status": "success", "message": "Google Calendar disconnected"}


@router.post("/google/sync", response_model=dict)
async def google_sync(db: Session = Depends(get_db)):
    if not google_calendar_service.is_configured():
        raise HTTPException(status_code=400, detail="Google Calendar is not configured")

    result = await google_calendar_service.sync_all(db, user_id=1)
    return {"status": "success", **result}
