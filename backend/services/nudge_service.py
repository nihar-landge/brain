"""
Proactive Nudge Engine.
Evaluates user state (mood, habits, sleep) and generates timely nudges.
"""

from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from models.user import User
from models.nudges import Nudge, NudgeSettings
from models.journal import JournalEntry
from models.habits import Habit, HabitLog
from models.sleep import SleepLog


class NudgeEngine:
    def __init__(self):
        # We can eventually use Gemini to personalize the message text,
        # but the decision logic should be rule-based for reliability.
        pass

    def get_or_create_settings(self, db: Session, user_id: int) -> NudgeSettings:
        settings = db.query(NudgeSettings).filter(NudgeSettings.user_id == user_id).first()
        if not settings:
            settings = NudgeSettings(user_id=user_id)
            db.add(settings)
            db.commit()
            db.refresh(settings)
        return settings

    def evaluate_user(self, db: Session, user_id: int):
        """Run all nudge rules for a specific user."""
        settings = self.get_or_create_settings(db, user_id)

        # Check quiet hours (simple check using UTC hour for now)
        current_hour = datetime.now(timezone.utc).hour
        try:
            quiet_start = int(settings.quiet_hours_start.split(':')[0])
            quiet_end = int(settings.quiet_hours_end.split(':')[0])
            if quiet_start > quiet_end:
                if current_hour >= quiet_start or current_hour < quiet_end:
                    return # In quiet hours
            else:
                if quiet_start <= current_hour < quiet_end:
                    return # In quiet hours
        except Exception:
            pass # Invalid config, proceed anyway

        # Check max nudges per day
        today = datetime.now(timezone.utc).date()
        nudges_today = db.query(Nudge).filter(
            Nudge.user_id == user_id,
            func.date(Nudge.created_at) == today
        ).count()

        if nudges_today >= settings.max_nudges_per_day:
            return

        # 1. Habit Reminder (late in day, habit not done)
        if settings.habits_enabled and current_hour >= 18:
            self._check_habit_reminders(db, user_id)

        # 2. Mood Checkin (if no journal entry for > 2 days)
        if settings.mood_enabled:
            self._check_mood_absence(db, user_id)

        # 3. Burnout Warning (consecutive high stress)
        if settings.burnout_warnings_enabled:
            self._check_burnout_signs(db, user_id)

        # 4. Sleep Suggestion (late night, low sleep prior night)
        if settings.sleep_suggestions_enabled and current_hour >= 23:
            self._check_sleep_hygiene(db, user_id)

    def _check_habit_reminders(self, db: Session, user_id: int):
        """Suggest completing an active top habit if missed today."""
        today = datetime.now(timezone.utc).date()
        active_habits = db.query(Habit).filter(Habit.user_id == user_id, Habit.status == "active").all()
        
        for habit in active_habits:
            log = db.query(HabitLog).filter(
                HabitLog.habit_id == habit.id, 
                HabitLog.log_date == today
            ).first()
            
            if not log or not log.completed:
                self._create_nudge(
                    db, user_id, 
                    "habit_reminder", 
                    f"Don't forget: {habit.habit_name}",
                    f"You still have time to complete '{habit.habit_name}' today to keep your momentum going.",
                    action_data={"action": "log_habit", "habit_id": habit.id},
                    expires_in_hours=6
                )
                return # Just send one habit reminder max

    def _check_mood_absence(self, db: Session, user_id: int):
        two_days_ago = datetime.now(timezone.utc).date() - timedelta(days=2)
        recent_entry = db.query(JournalEntry).filter(
            JournalEntry.user_id == user_id,
            JournalEntry.entry_date >= two_days_ago
        ).first()

        if not recent_entry:
            # Check if we already nudged about this today
            recent_nudge = db.query(Nudge).filter(
                Nudge.user_id == user_id,
                Nudge.nudge_type == "mood_checkin",
                Nudge.created_at >= datetime.now(timezone.utc) - timedelta(days=1)
            ).first()
            
            if not recent_nudge:
                self._create_nudge(
                    db, user_id,
                    "mood_checkin",
                    "Time for a Check-in",
                    "It's been a few days since your last journal entry. How are you feeling today?",
                    action_data={"action": "create_journal"},
                    expires_in_hours=12
                )

    def _check_burnout_signs(self, db: Session, user_id: int):
        # Look for 3 consecutive days of stress >= 7
        three_days_ago = datetime.now(timezone.utc).date() - timedelta(days=3)
        entries = db.query(JournalEntry).filter(
            JournalEntry.user_id == user_id,
            JournalEntry.entry_date >= three_days_ago,
            JournalEntry.stress_level != None
        ).order_by(JournalEntry.entry_date.desc()).limit(3).all()

        if len(entries) == 3 and all(e.stress_level >= 7 for e in entries):
            self._create_nudge(
                db, user_id,
                "burnout_warning",
                "High Stress Alert",
                "Your stress levels have been high for 3 days in a row. Consider taking a break or scheduling some downtime.",
                action_data={"action": "schedule_break"},
                expires_in_hours=24
            )

    def _check_sleep_hygiene(self, db: Session, user_id: int):
        # Simple for now: just remind them to sleep if it's late
        self._create_nudge(
            db, user_id,
            "sleep_suggestion",
            "Time to Wind Down",
            "It's getting late. Getting consistent sleep is the #1 factor for good mood tomorrow.",
            action_data={"action": "log_sleep"},
            expires_in_hours=6 # Expires by morning
        )

    def _create_nudge(self, db: Session, user_id: int, type: str, title: str, message: str, action_data: dict, expires_in_hours: int = 24):
        # Prevent exact duplicate active nudges
        existing = db.query(Nudge).filter(
            Nudge.user_id == user_id,
            Nudge.title == title,
            Nudge.is_read == False,
            Nudge.is_dismissed == False
        ).first()
        
        if existing:
            return

        expires = datetime.now(timezone.utc) + timedelta(hours=expires_in_hours)
        nudge = Nudge(
            user_id=user_id,
            nudge_type=type,
            title=title,
            message=message,
            action_data=action_data,
            expires_at=expires
        )
        db.add(nudge)
        db.commit()

nudge_engine = NudgeEngine()
