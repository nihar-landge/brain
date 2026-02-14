"""
Feature Engineering Pipeline.
Extracts features from journal data for ML models.
"""

from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from models.journal import JournalEntry, MoodLog
from models.habits import HabitLog


def extract_mood_features(db: Session, user_id: int, date: datetime) -> dict:
    """Extract features for mood prediction."""
    features = {
        "day_of_week": date.weekday(),
        "hour": date.hour if hasattr(date, "hour") else 12,
        "month": date.month,
        "is_weekend": 1 if date.weekday() >= 5 else 0,
    }

    # Historical mood averages
    week_ago = date.date() - timedelta(days=7) if hasattr(date, 'date') else date - timedelta(days=7)
    recent_moods = (
        db.query(MoodLog)
        .filter(MoodLog.user_id == user_id, MoodLog.log_date >= week_ago)
        .all()
    )

    if recent_moods:
        features["avg_mood_last_week"] = sum(m.mood_value for m in recent_moods) / len(
            recent_moods
        )
        features["mood_variance"] = (
            sum((m.mood_value - features["avg_mood_last_week"]) ** 2 for m in recent_moods)
            / len(recent_moods)
        )
    else:
        features["avg_mood_last_week"] = 5.0
        features["mood_variance"] = 0.0

    # Recent entries
    recent_entries = (
        db.query(JournalEntry)
        .filter(JournalEntry.user_id == user_id, JournalEntry.entry_date >= week_ago)
        .all()
    )

    if recent_entries:
        energies = [e.energy_level for e in recent_entries if e.energy_level]
        features["avg_energy_last_week"] = sum(energies) / len(energies) if energies else 5.0

        stresses = [e.stress_level for e in recent_entries if e.stress_level]
        features["avg_stress_last_week"] = sum(stresses) / len(stresses) if stresses else 5.0
    else:
        features["avg_energy_last_week"] = 5.0
        features["avg_stress_last_week"] = 5.0

    # Habit completion yesterday
    yesterday = (date.date() if hasattr(date, 'date') else date) - timedelta(days=1)
    habits_yesterday = (
        db.query(HabitLog)
        .filter(HabitLog.user_id == user_id, HabitLog.log_date == yesterday)
        .all()
    )
    features["habits_completed_yesterday"] = sum(1 for h in habits_yesterday if h.completed)

    return features


def extract_habit_features(db: Session, user_id: int, habit_id: int, date: datetime) -> dict:
    """Extract features for habit success prediction."""
    features = {
        "day_of_week": date.weekday(),
        "hour": date.hour if hasattr(date, "hour") else 12,
        "is_weekend": 1 if date.weekday() >= 5 else 0,
    }

    # Historical success rate
    all_logs = (
        db.query(HabitLog)
        .filter(HabitLog.habit_id == habit_id, HabitLog.user_id == user_id)
        .all()
    )

    if all_logs:
        features["historical_success_rate"] = sum(1 for l in all_logs if l.completed) / len(all_logs)
        features["total_logs"] = len(all_logs)

        # Day-of-week success rate
        dow_logs = [l for l in all_logs if l.log_date.weekday() == date.weekday()]
        if dow_logs:
            features["dow_success_rate"] = sum(1 for l in dow_logs if l.completed) / len(dow_logs)
        else:
            features["dow_success_rate"] = features["historical_success_rate"]

        # Current streak
        sorted_logs = sorted(all_logs, key=lambda x: x.log_date, reverse=True)
        streak = 0
        for log in sorted_logs:
            if log.completed:
                streak += 1
            else:
                break
        features["current_streak"] = streak

        # Days since last completion
        completed_logs = sorted(
            [l for l in all_logs if l.completed], key=lambda x: x.log_date, reverse=True
        )
        if completed_logs:
            last_date = completed_logs[0].log_date
            target = date.date() if hasattr(date, 'date') else date
            features["days_since_last"] = (target - last_date).days
        else:
            features["days_since_last"] = 999
    else:
        features["historical_success_rate"] = 0.5
        features["total_logs"] = 0
        features["dow_success_rate"] = 0.5
        features["current_streak"] = 0
        features["days_since_last"] = 999

    # Current mood/energy
    today_mood = (
        db.query(MoodLog)
        .filter(MoodLog.user_id == user_id)
        .order_by(MoodLog.log_date.desc())
        .first()
    )
    if today_mood:
        features["current_mood"] = today_mood.mood_value
        features["current_energy"] = today_mood.energy_level or 5
    else:
        features["current_mood"] = 5
        features["current_energy"] = 5

    return features
