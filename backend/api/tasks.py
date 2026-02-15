"""
Tasks API Endpoints.
Task planning with goal/habit tagging, scheduling, and priorities.
"""

from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from utils.database import get_db
from models.dopamine import Task
from models.goals import Goal
from models.habits import Habit
from services.google_calendar_service import google_calendar_service

router = APIRouter()


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    status: str = Field("todo", pattern="^(todo|in_progress|done)$")
    priority: str = Field("medium", pattern="^(low|medium|high|critical)$")
    due_date: Optional[str] = None  # YYYY-MM-DD
    scheduled_at: Optional[str] = None  # YYYY-MM-DDTHH:MM
    scheduled_end: Optional[str] = None
    is_all_day: bool = False
    estimated_minutes: Optional[int] = Field(None, ge=1, le=1440)
    goal_id: Optional[int] = None
    habit_id: Optional[int] = None
    tags: Optional[List[str]] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(todo|in_progress|done)$")
    priority: Optional[str] = Field(None, pattern="^(low|medium|high|critical)$")
    due_date: Optional[str] = None
    scheduled_at: Optional[str] = None
    scheduled_end: Optional[str] = None
    is_all_day: Optional[bool] = None
    estimated_minutes: Optional[int] = Field(None, ge=1, le=1440)
    spent_minutes: Optional[int] = Field(None, ge=0)
    goal_id: Optional[int] = None
    habit_id: Optional[int] = None
    tags: Optional[List[str]] = None


def _parse_date(value: Optional[str]):
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d").date()


def _parse_datetime(value: Optional[str]):
    if not value:
        return None
    # Accept both "YYYY-MM-DDTHH:MM" and full ISO timestamp
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M")
    except ValueError:
        return datetime.fromisoformat(value)


def _validate_links(db: Session, goal_id: Optional[int], habit_id: Optional[int]):
    if goal_id is not None:
        goal = db.query(Goal).filter(Goal.id == goal_id, Goal.user_id == 1).first()
        if not goal:
            raise HTTPException(status_code=404, detail="Goal not found")

    if habit_id is not None:
        habit = db.query(Habit).filter(Habit.id == habit_id, Habit.user_id == 1).first()
        if not habit:
            raise HTTPException(status_code=404, detail="Habit not found")


@router.post("", response_model=dict)
async def create_task(data: TaskCreate, db: Session = Depends(get_db)):
    _validate_links(db, data.goal_id, data.habit_id)

    task = Task(
        user_id=1,
        title=data.title,
        description=data.description,
        status=data.status,
        priority=data.priority,
        due_date=_parse_date(data.due_date),
        scheduled_at=_parse_datetime(data.scheduled_at),
        scheduled_end=_parse_datetime(data.scheduled_end),
        is_all_day=data.is_all_day,
        estimated_minutes=data.estimated_minutes,
        spent_minutes=0,
        goal_id=data.goal_id,
        habit_id=data.habit_id,
        tags=data.tags,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    # Auto-sync to Google Calendar if connected
    try:
        await google_calendar_service.upsert_task_event(db, task, user_id=1)
    except Exception:
        pass

    return {"id": task.id, "status": "success", "message": "Task created"}


@router.get("", response_model=List[dict])
async def get_tasks(
    status: str = "all",
    priority: str = "all",
    goal_id: Optional[int] = None,
    habit_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Task).filter(Task.user_id == 1)

    if status != "all":
        query = query.filter(Task.status == status)
    if priority != "all":
        query = query.filter(Task.priority == priority)
    if goal_id is not None:
        query = query.filter(Task.goal_id == goal_id)
    if habit_id is not None:
        query = query.filter(Task.habit_id == habit_id)

    tasks = query.order_by(Task.created_at.desc()).all()

    goal_ids = {t.goal_id for t in tasks if t.goal_id}
    habit_ids = {t.habit_id for t in tasks if t.habit_id}

    goal_map = {}
    if goal_ids:
        goals = db.query(Goal).filter(Goal.id.in_(goal_ids)).all()
        goal_map = {g.id: g.goal_title for g in goals}

    habit_map = {}
    if habit_ids:
        habits = db.query(Habit).filter(Habit.id.in_(habit_ids)).all()
        habit_map = {h.id: h.habit_name for h in habits}

    return [
        {
            "id": t.id,
            "title": t.title,
            "description": t.description,
            "status": t.status,
            "priority": t.priority,
            "due_date": str(t.due_date) if t.due_date else None,
            "scheduled_at": str(t.scheduled_at) if t.scheduled_at else None,
            "scheduled_end": str(t.scheduled_end) if t.scheduled_end else None,
            "is_all_day": t.is_all_day,
            "estimated_minutes": t.estimated_minutes,
            "spent_minutes": t.spent_minutes or 0,
            "goal_id": t.goal_id,
            "goal_title": goal_map.get(t.goal_id),
            "habit_id": t.habit_id,
            "habit_name": habit_map.get(t.habit_id),
            "tags": t.tags or [],
            "google_event_id": t.google_event_id,
            "created_at": str(t.created_at),
            "updated_at": str(t.updated_at),
        }
        for t in tasks
    ]


@router.get("/{task_id}", response_model=dict)
async def get_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == 1).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "priority": task.priority,
        "due_date": str(task.due_date) if task.due_date else None,
        "scheduled_at": str(task.scheduled_at) if task.scheduled_at else None,
        "scheduled_end": str(task.scheduled_end) if task.scheduled_end else None,
        "is_all_day": task.is_all_day,
        "estimated_minutes": task.estimated_minutes,
        "spent_minutes": task.spent_minutes or 0,
        "goal_id": task.goal_id,
        "habit_id": task.habit_id,
        "tags": task.tags or [],
        "google_event_id": task.google_event_id,
    }


@router.put("/{task_id}", response_model=dict)
async def update_task(task_id: int, updates: TaskUpdate, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == 1).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    data = updates.model_dump(exclude_unset=True)

    _validate_links(
        db, data.get("goal_id", task.goal_id), data.get("habit_id", task.habit_id)
    )

    for key, value in data.items():
        if key == "due_date":
            task.due_date = _parse_date(value)
        elif key == "scheduled_at":
            task.scheduled_at = _parse_datetime(value)
        elif key == "scheduled_end":
            task.scheduled_end = _parse_datetime(value)
        else:
            setattr(task, key, value)

    task.updated_at = datetime.utcnow()
    db.commit()

    # Auto-sync updates to Google Calendar if connected
    try:
        await google_calendar_service.upsert_task_event(db, task, user_id=1)
    except Exception:
        pass

    return {"status": "success", "message": "Task updated"}


@router.delete("/{task_id}", response_model=dict)
async def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == 1).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # If linked to Google Calendar event, try deleting remotely first
    if task.google_event_id:
        try:
            service, integration = google_calendar_service._get_service(db, user_id=1)
            if service and integration and integration.calendar_id:
                service.events().delete(
                    calendarId=integration.calendar_id, eventId=task.google_event_id
                ).execute()
        except Exception:
            pass

    db.delete(task)
    db.commit()
    return {"status": "success", "message": "Task deleted"}
