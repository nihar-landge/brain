"""
Goals API Endpoints.
Goal management and tracking.
"""

from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from utils.database import get_db
from models.goals import Goal, GoalMilestone
from models.habits import Habit
from models.context import ContextLog

router = APIRouter()


# ======================== SCHEMAS ========================


class GoalCreate(BaseModel):
    goal_title: str = Field(..., min_length=1)
    goal_description: Optional[str] = None
    goal_category: Optional[str] = None
    start_date: str
    target_date: Optional[str] = None
    priority: Optional[int] = Field(None, ge=1, le=5)
    is_recurring: bool = False


class GoalUpdate(BaseModel):
    goal_title: Optional[str] = None
    goal_description: Optional[str] = None
    status: Optional[str] = None
    progress: Optional[int] = Field(None, ge=0, le=100)
    priority: Optional[int] = Field(None, ge=1, le=5)
    completion_notes: Optional[str] = None


class MilestoneCreate(BaseModel):
    milestone_title: str = Field(..., min_length=1)
    milestone_description: Optional[str] = None
    target_date: Optional[str] = None


# ======================== ENDPOINTS ========================


@router.post("", response_model=dict)
async def create_goal(goal: GoalCreate, db: Session = Depends(get_db)):
    """Create a new goal."""
    new_goal = Goal(
        user_id=1,
        goal_title=goal.goal_title,
        goal_description=goal.goal_description,
        goal_category=goal.goal_category,
        start_date=datetime.strptime(goal.start_date, "%Y-%m-%d").date(),
        target_date=(
            datetime.strptime(goal.target_date, "%Y-%m-%d").date()
            if goal.target_date
            else None
        ),
        priority=goal.priority,
        is_recurring=goal.is_recurring,
    )
    db.add(new_goal)
    db.commit()
    db.refresh(new_goal)

    return {"id": new_goal.id, "status": "success", "message": "Goal created"}


@router.get("", response_model=List[dict])
async def get_goals(status: str = "active", db: Session = Depends(get_db)):
    """Get user goals with habit counts."""
    query = db.query(Goal).filter(Goal.user_id == 1)
    if status != "all":
        query = query.filter(Goal.status == status)

    goals = query.order_by(Goal.created_at.desc()).all()

    # Get habit counts per goal
    goal_ids = [g.id for g in goals]
    habit_counts = {}
    if goal_ids:
        from sqlalchemy import func

        counts = (
            db.query(Habit.goal_id, func.count(Habit.id))
            .filter(Habit.goal_id.in_(goal_ids), Habit.status == "active")
            .group_by(Habit.goal_id)
            .all()
        )
        habit_counts = dict(counts)

    return [
        {
            "id": g.id,
            "title": g.goal_title,
            "description": g.goal_description,
            "category": g.goal_category,
            "status": g.status,
            "progress": g.progress,
            "priority": g.priority,
            "start_date": str(g.start_date),
            "target_date": str(g.target_date) if g.target_date else None,
            "created_at": str(g.created_at),
            "habit_count": habit_counts.get(g.id, 0),
        }
        for g in goals
    ]


@router.get("/{goal_id}", response_model=dict)
async def get_goal(goal_id: int, db: Session = Depends(get_db)):
    """Get specific goal with milestones, habits, and recent sessions."""
    goal = db.query(Goal).get(goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    milestones = (
        db.query(GoalMilestone)
        .filter(GoalMilestone.goal_id == goal_id)
        .order_by(GoalMilestone.created_at)
        .all()
    )

    # Get habits linked to this goal
    habits = (
        db.query(Habit)
        .filter(Habit.goal_id == goal_id, Habit.status == "active")
        .order_by(Habit.created_at)
        .all()
    )

    # Get recent sessions (context logs) for each habit
    habit_ids = [h.id for h in habits]
    sessions_by_habit = {}
    if habit_ids:
        recent_sessions = (
            db.query(ContextLog)
            .filter(
                ContextLog.habit_id.in_(habit_ids),
                ContextLog.ended_at.isnot(None),
            )
            .order_by(ContextLog.started_at.desc())
            .limit(50)
            .all()
        )
        for s in recent_sessions:
            sessions_by_habit.setdefault(s.habit_id, []).append(
                {
                    "id": s.id,
                    "context_name": s.context_name,
                    "started_at": str(s.started_at),
                    "ended_at": str(s.ended_at) if s.ended_at else None,
                    "duration_minutes": s.duration_minutes,
                    "productivity_rating": s.productivity_rating,
                }
            )

    return {
        "id": goal.id,
        "title": goal.goal_title,
        "description": goal.goal_description,
        "category": goal.goal_category,
        "status": goal.status,
        "progress": goal.progress,
        "priority": goal.priority,
        "start_date": str(goal.start_date),
        "target_date": str(goal.target_date) if goal.target_date else None,
        "milestones": [
            {
                "id": m.id,
                "title": m.milestone_title,
                "description": m.milestone_description,
                "completed": m.completed,
                "target_date": str(m.target_date) if m.target_date else None,
            }
            for m in milestones
        ],
        "habits": [
            {
                "id": h.id,
                "name": h.habit_name,
                "description": h.habit_description,
                "category": h.habit_category,
                "frequency": h.target_frequency,
                "sessions": sessions_by_habit.get(h.id, [])[:10],
                "total_sessions": len(sessions_by_habit.get(h.id, [])),
                "total_minutes": sum(
                    s["duration_minutes"] or 0 for s in sessions_by_habit.get(h.id, [])
                ),
            }
            for h in habits
        ],
    }


@router.put("/{goal_id}", response_model=dict)
async def update_goal(goal_id: int, updates: GoalUpdate, db: Session = Depends(get_db)):
    """Update goal."""
    goal = db.query(Goal).get(goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    update_data = updates.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if hasattr(goal, key):
            setattr(goal, key, value)

    if updates.status == "completed":
        goal.completed_date = datetime.now().date()

    goal.updated_at = datetime.utcnow()
    db.commit()

    return {"status": "success", "message": "Goal updated"}


@router.delete("/{goal_id}", response_model=dict)
async def delete_goal(goal_id: int, db: Session = Depends(get_db)):
    """Delete goal."""
    goal = db.query(Goal).get(goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    db.delete(goal)
    db.commit()
    return {"status": "success", "message": "Goal deleted"}


@router.post("/{goal_id}/milestones", response_model=dict)
async def add_milestone(
    goal_id: int, milestone: MilestoneCreate, db: Session = Depends(get_db)
):
    """Add milestone to a goal."""
    goal = db.query(Goal).get(goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    new_milestone = GoalMilestone(
        goal_id=goal_id,
        milestone_title=milestone.milestone_title,
        milestone_description=milestone.milestone_description,
        target_date=(
            datetime.strptime(milestone.target_date, "%Y-%m-%d").date()
            if milestone.target_date
            else None
        ),
    )
    db.add(new_milestone)
    db.commit()

    return {"id": new_milestone.id, "status": "success", "message": "Milestone added"}


@router.put("/{goal_id}/milestones/{milestone_id}/complete", response_model=dict)
async def complete_milestone(
    goal_id: int, milestone_id: int, db: Session = Depends(get_db)
):
    """Mark milestone as completed."""
    milestone = db.query(GoalMilestone).get(milestone_id)
    if not milestone or milestone.goal_id != goal_id:
        raise HTTPException(status_code=404, detail="Milestone not found")

    milestone.completed = True
    milestone.completed_date = datetime.now().date()
    db.commit()

    # Update goal progress
    goal = db.query(Goal).get(goal_id)
    all_milestones = (
        db.query(GoalMilestone).filter(GoalMilestone.goal_id == goal_id).all()
    )
    completed = sum(1 for m in all_milestones if m.completed)
    if all_milestones:
        goal.progress = int((completed / len(all_milestones)) * 100)
        db.commit()

    return {
        "status": "success",
        "message": "Milestone completed",
        "goal_progress": goal.progress,
    }
