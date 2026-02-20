"""
Analytics API Endpoints.
Dashboard data, patterns, and AI-generated insights.
"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from utils.database import get_db
from models.journal import JournalEntry, MoodLog, Insight
from models.habits import Habit, HabitLog
from models.goals import Goal
from services.gemini_service import gemini_service

from models.user import User
from utils.auth import verify_api_key

router = APIRouter()


@router.get("/dashboard", response_model=dict)
async def get_dashboard_data(user: User = Depends(verify_api_key), db: Session = Depends(get_db)):
    """Get complete dashboard analytics."""
    user_id = user.id
    now = datetime.now()
    week_ago = now.date() - timedelta(days=7)
    month_ago = now.date() - timedelta(days=30)

    # Mood trend (last 30 days)
    mood_entries = (
        db.query(MoodLog)
        .filter(MoodLog.user_id == user_id, MoodLog.log_date >= month_ago)
        .order_by(MoodLog.log_date)
        .all()
    )
    mood_trend = [
        {"date": str(m.log_date), "mood": m.mood_value, "energy": m.energy_level}
        for m in mood_entries
    ]

    avg_mood = (
        sum(m.mood_value for m in mood_entries) / len(mood_entries) if mood_entries else 0
    )

    # Habit stats
    habits = db.query(Habit).filter(Habit.user_id == user_id, Habit.status == "active").all()
    habit_stats = []
    for habit in habits:
        logs = (
            db.query(HabitLog)
            .filter(HabitLog.habit_id == habit.id, HabitLog.log_date >= month_ago)
            .all()
        )
        completed = sum(1 for log in logs if log.completed)
        total = len(logs)
        habit_stats.append({
            "name": habit.habit_name,
            "completed": completed,
            "total": total,
            "rate": round(completed / total, 2) if total > 0 else 0,
        })

    # Goal progress
    goals = db.query(Goal).filter(Goal.user_id == user_id, Goal.status == "active").all()
    goal_progress = [
        {
            "title": g.goal_title,
            "progress": g.progress,
            "target_date": str(g.target_date) if g.target_date else None,
        }
        for g in goals
    ]

    # Recent entries count
    recent_entries = (
        db.query(JournalEntry)
        .filter(JournalEntry.user_id == user_id, JournalEntry.entry_date >= week_ago)
        .count()
    )

    return {
        "mood_trend": mood_trend,
        "average_mood": round(avg_mood, 1),
        "habit_stats": habit_stats,
        "goal_progress": goal_progress,
        "entries_this_week": recent_entries,
        "total_entries": db.query(JournalEntry).filter(JournalEntry.user_id == user_id).count(),
    }


@router.get("/patterns", response_model=dict)
async def analyze_patterns(
    category: str = "mood",
    lookback_days: int = 90,
    user: User = Depends(verify_api_key),
    db: Session = Depends(get_db),
):
    """Analyze behavioral patterns."""
    user_id = user.id
    start_date = datetime.now().date() - timedelta(days=lookback_days)

    if category == "mood":
        moods = (
            db.query(MoodLog)
            .filter(MoodLog.user_id == user_id, MoodLog.log_date >= start_date)
            .all()
        )

        # Day-of-week patterns
        dow_moods = {}
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for m in moods:
            dow = m.log_date.weekday()
            if dow not in dow_moods:
                dow_moods[dow] = []
            dow_moods[dow].append(m.mood_value)

        day_averages = {
            days[dow]: round(sum(vals) / len(vals), 1)
            for dow, vals in dow_moods.items()
        }

        return {
            "category": category,
            "period_days": lookback_days,
            "data_points": len(moods),
            "day_of_week_averages": day_averages,
            "best_day": max(day_averages, key=day_averages.get) if day_averages else None,
            "worst_day": min(day_averages, key=day_averages.get) if day_averages else None,
        }

    return {"category": category, "message": "Pattern analysis available for: mood"}


@router.get("/insights", response_model=list)
async def get_insights(user: User = Depends(verify_api_key), db: Session = Depends(get_db)):
    """Get AI-generated insights."""
    user_id = user.id

    # Get existing insights
    insights = (
        db.query(Insight)
        .filter(Insight.user_id == user_id, Insight.dismissed == False)
        .order_by(Insight.created_at.desc())
        .limit(10)
        .all()
    )

    return [
        {
            "id": i.id,
            "type": i.insight_type,
            "category": i.insight_category,
            "title": i.title,
            "description": i.description,
            "confidence": i.confidence,
            "actionable": i.actionable,
            "created_at": str(i.created_at),
        }
        for i in insights
    ]


@router.post("/generate-insights", response_model=dict)
async def generate_insights(user: User = Depends(verify_api_key), db: Session = Depends(get_db)):
    """Generate new AI insights from recent data."""
    user_id = user.id
    week_ago = datetime.now().date() - timedelta(days=7)

    entries = (
        db.query(JournalEntry)
        .filter(JournalEntry.user_id == user_id, JournalEntry.entry_date >= week_ago)
        .all()
    )

    if not entries:
        return {"message": "No recent entries to analyze", "insights_generated": 0}

    # Build summary for Gemini
    summary = "\n".join(
        f"[{e.entry_date}] Mood: {e.mood}/10, Energy: {e.energy_level}/10 - {e.content[:100]}"
        for e in entries
    )

    insight_text = gemini_service.generate_insight(summary)

    # Save insight
    insight = Insight(
        user_id=user_id,
        insight_type="pattern",
        insight_category="weekly",
        title="Weekly Pattern Analysis",
        description=insight_text,
        confidence=0.7,
        importance=3,
        actionable=True,
    )
    db.add(insight)
    db.commit()

    return {"message": "Insights generated", "insights_generated": 1, "insight": insight_text}
