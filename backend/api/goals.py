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
    """Get user goals."""
    query = db.query(Goal).filter(Goal.user_id == 1)
    if status != "all":
        query = query.filter(Goal.status == status)

    goals = query.order_by(Goal.created_at.desc()).all()

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
        }
        for g in goals
    ]


@router.get("/{goal_id}", response_model=dict)
async def get_goal(goal_id: int, db: Session = Depends(get_db)):
    """Get specific goal with milestones."""
    goal = db.query(Goal).get(goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    milestones = (
        db.query(GoalMilestone)
        .filter(GoalMilestone.goal_id == goal_id)
        .order_by(GoalMilestone.created_at)
        .all()
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
    all_milestones = db.query(GoalMilestone).filter(GoalMilestone.goal_id == goal_id).all()
    completed = sum(1 for m in all_milestones if m.completed)
    if all_milestones:
        goal.progress = int((completed / len(all_milestones)) * 100)
        db.commit()

    return {"status": "success", "message": "Milestone completed", "goal_progress": goal.progress}
