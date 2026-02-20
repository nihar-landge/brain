"""
Data Management API Endpoints.
Export, import, and backup user data.
"""

import os
import json
import shutil
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session

from utils.database import get_db
from models.journal import JournalEntry, MoodLog
from models.habits import Habit, HabitLog
from models.goals import Goal, GoalMilestone
from models.user import ChatHistory, User
from utils.auth import verify_api_key

router = APIRouter()

BACKUP_DIR = "./data/backups"


# ======================== EXPORT ========================


@router.get("/export", response_model=dict)
async def export_data(user: User = Depends(verify_api_key), db: Session = Depends(get_db)):
    """Export all user data as JSON."""
    user_id = user.id

    entries = db.query(JournalEntry).filter(JournalEntry.user_id == user_id).all()
    moods = db.query(MoodLog).filter(MoodLog.user_id == user_id).all()
    habits = db.query(Habit).filter(Habit.user_id == user_id).all()
    habit_logs = db.query(HabitLog).filter(HabitLog.user_id == user_id).all()
    goals = db.query(Goal).filter(Goal.user_id == user_id).all()
    milestones = db.query(GoalMilestone).filter(
        GoalMilestone.goal_id.in_([g.id for g in goals])
    ).all() if goals else []

    export = {
        "exported_at": datetime.now().isoformat(),
        "version": "1.0",
        "journal_entries": [
            {
                "id": e.id, "content": e.content, "title": e.title,
                "mood": e.mood, "energy_level": e.energy_level,
                "stress_level": e.stress_level, "tags": e.tags,
                "category": e.category, "entry_date": str(e.entry_date),
            }
            for e in entries
        ],
        "mood_logs": [
            {
                "id": m.id, "mood_value": m.mood_value,
                "energy_level": m.energy_level, "stress_level": m.stress_level,
                "log_date": str(m.log_date),
            }
            for m in moods
        ],
        "habits": [
            {
                "id": h.id, "name": h.habit_name,
                "description": h.habit_description,
                "category": h.habit_category,
                "frequency": h.target_frequency,
                "status": h.status, "start_date": str(h.start_date),
            }
            for h in habits
        ],
        "habit_logs": [
            {
                "id": l.id, "habit_id": l.habit_id,
                "completed": l.completed, "log_date": str(l.log_date),
                "difficulty": l.difficulty, "satisfaction": l.satisfaction,
                "notes": l.notes,
            }
            for l in habit_logs
        ],
        "goals": [
            {
                "id": g.id, "title": g.goal_title,
                "description": g.goal_description,
                "category": g.goal_category, "status": g.status,
                "progress": g.progress, "priority": g.priority,
                "start_date": str(g.start_date),
                "target_date": str(g.target_date) if g.target_date else None,
            }
            for g in goals
        ],
        "milestones": [
            {
                "id": m.id, "goal_id": m.goal_id,
                "title": m.milestone_title,
                "completed": m.completed,
            }
            for m in milestones
        ],
        "stats": {
            "total_entries": len(entries),
            "total_moods": len(moods),
            "total_habits": len(habits),
            "total_habit_logs": len(habit_logs),
            "total_goals": len(goals),
        },
    }

    return export


# ======================== IMPORT ========================


@router.post("/import", response_model=dict)
async def import_data(data: dict, user: User = Depends(verify_api_key), db: Session = Depends(get_db)):
    """Import data from JSON export."""
    imported = {"entries": 0, "habits": 0, "goals": 0}

    # Import journal entries
    for entry_data in data.get("journal_entries", []):
        entry = JournalEntry(
            user_id=user.id,
            content=entry_data["content"],
            title=entry_data.get("title"),
            mood=entry_data.get("mood"),
            energy_level=entry_data.get("energy_level"),
            stress_level=entry_data.get("stress_level"),
            tags=entry_data.get("tags"),
            category=entry_data.get("category"),
            entry_date=(
                datetime.strptime(entry_data["entry_date"], "%Y-%m-%d").date()
                if entry_data.get("entry_date")
                else datetime.now().date()
            ),
        )
        db.add(entry)
        imported["entries"] += 1

    # Import habits
    for habit_data in data.get("habits", []):
        habit = Habit(
            user_id=user.id,
            habit_name=habit_data["name"],
            habit_description=habit_data.get("description"),
            habit_category=habit_data.get("category"),
            target_frequency=habit_data.get("frequency", "daily"),
            status=habit_data.get("status", "active"),
            start_date=datetime.now().date(),
        )
        db.add(habit)
        imported["habits"] += 1

    # Import goals
    for goal_data in data.get("goals", []):
        goal = Goal(
            user_id=user.id,
            goal_title=goal_data["title"],
            goal_description=goal_data.get("description"),
            goal_category=goal_data.get("category"),
            status=goal_data.get("status", "active"),
            progress=goal_data.get("progress", 0),
            priority=goal_data.get("priority", 3),
            start_date=datetime.now().date(),
        )
        db.add(goal)
        imported["goals"] += 1

    db.commit()
    return {"status": "success", "imported": imported}


# ======================== BACKUP ========================


@router.post("/backup", response_model=dict)
async def create_backup(db: Session = Depends(get_db)):
    """Create a local backup of the database."""
    os.makedirs(BACKUP_DIR, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    db_path = "./data/database.db"

    if not os.path.exists(db_path):
        return {"status": "error", "message": "Database file not found"}

    backup_path = os.path.join(BACKUP_DIR, f"backup_{timestamp}.db")
    shutil.copy2(db_path, backup_path)

    # Also save a JSON export
    json_path = os.path.join(BACKUP_DIR, f"backup_{timestamp}.json")
    export = await export_data(db)
    with open(json_path, "w") as f:
        json.dump(export, f, indent=2, default=str)

    return {
        "status": "success",
        "message": "Backup created",
        "backup_file": backup_path,
        "json_file": json_path,
        "timestamp": timestamp,
    }


@router.get("/backup/list", response_model=dict)
async def list_backups():
    """List available backups."""
    os.makedirs(BACKUP_DIR, exist_ok=True)

    backups = []
    for f in sorted(os.listdir(BACKUP_DIR), reverse=True):
        if f.endswith(".db"):
            path = os.path.join(BACKUP_DIR, f)
            backups.append({
                "filename": f,
                "size_mb": round(os.path.getsize(path) / 1024 / 1024, 2),
                "created": datetime.fromtimestamp(os.path.getmtime(path)).isoformat(),
            })

    return {"backups": backups, "total": len(backups)}
