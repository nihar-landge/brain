"""
Anomaly Detector Engine.
Monitors daily data for abrupt changes in baseline metrics.
"""

from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from models.journal import JournalEntry
from models.habits import HabitLog
from models.sleep import SleepLog
from models.anomalies import AnomalyAlert

class AnomalyDetector:
    def __init__(self):
        # Thresholds for what constitutes an anomaly
        self.mood_drop_threshold = 2.0 # E.g., drops from 7 to 5
        self.sleep_loss_threshold = 2.0 # E.g., drops from 7h to 5h
        self.baseline_days = 7

    def detect_anomalies(self, db: Session, user_id: int):
        """Run all anomaly detection checks and create alerts if needed."""
        today = datetime.now(timezone.utc).date()
        yesterday = today - timedelta(days=1)
        
        self._check_mood_drop(db, user_id, yesterday)
        self._check_sleep_disruption(db, user_id, yesterday)
        self._check_habit_streak_broken(db, user_id, yesterday)

    def _check_mood_drop(self, db: Session, user_id: int, target_date):
        """Detect severe mood drops compared to the 7-day rolling average."""
        # 1. Get yesterday's mood
        entry = db.query(JournalEntry).filter(
            JournalEntry.user_id == user_id,
            JournalEntry.entry_date == target_date,
            JournalEntry.mood != None
        ).first()
        
        if not entry:
            return

        current_mood = entry.mood
        
        # 2. Calculate baseline (previous 7 days before yesterday)
        start_baseline = target_date - timedelta(days=self.baseline_days)
        history = db.query(JournalEntry).filter(
            JournalEntry.user_id == user_id,
            JournalEntry.entry_date >= start_baseline,
            JournalEntry.entry_date < target_date,
            JournalEntry.mood != None
        ).all()
        
        if not history:
            return
            
        avg_baseline = sum(h.mood for h in history) / len(history)

        # 3. Compare
        if (avg_baseline - current_mood) >= self.mood_drop_threshold:
            self._create_alert(
                db, user_id,
                "mood_drop",
                "Severe Mood Drop Detected",
                f"Your mood yesterday ({current_mood}) was significantly lower than your recent average ({round(avg_baseline, 1)}). Take it easy today.",
                "high",
                metric_name="avg_mood_7d",
                baseline=avg_baseline,
                current=current_mood,
                action={"action": "suggest_rest"}
            )

    def _check_sleep_disruption(self, db: Session, user_id: int, target_date):
        # 1. Get last night's sleep
        sleep = db.query(SleepLog).filter(
            SleepLog.user_id == user_id,
            func.date(SleepLog.wake_time) == target_date
        ).first()

        if not sleep:
            return
            
        current_sleep = sleep.duration_hours

        # 2. Calculate baseline
        start_baseline = target_date - timedelta(days=self.baseline_days)
        history = db.query(SleepLog).filter(
            SleepLog.user_id == user_id,
            func.date(SleepLog.wake_time) >= start_baseline,
            func.date(SleepLog.wake_time) < target_date
        ).all()

        if not history:
            return

        avg_baseline = sum(h.duration_hours for h in history) / len(history)
        
        if (avg_baseline - current_sleep) >= self.sleep_loss_threshold:
            self._create_alert(
                db, user_id,
                "sleep_disruption",
                "Significant Sleep Loss",
                f"You slept {round(current_sleep,1)}h last night, compared to your {round(avg_baseline,1)}h average. Expect lower energy today.",
                "medium",
                metric_name="avg_sleep_7d",
                baseline=avg_baseline,
                current=current_sleep,
                action={"action": "log_nap"}
            )
            
    def _check_habit_streak_broken(self, db: Session, user_id: int, target_date):
        # Check if a long streak (>7 days) was broken yesterday
        pass

    def _create_alert(self, db: Session, user_id: int, type: str, title: str, 
                      description: str, severity: str, metric_name: str, 
                      baseline: float, current: float, action: dict):
                          
        # Don't create duplicate unacknowledged alerts of the same type
        existing = db.query(AnomalyAlert).filter(
            AnomalyAlert.user_id == user_id,
            AnomalyAlert.anomaly_type == type,
            AnomalyAlert.is_acknowledged == False
        ).first()
        
        if existing:
            return
            
        alert = AnomalyAlert(
            user_id=user_id,
            anomaly_type=type,
            title=title,
            description=description,
            severity=severity,
            metric_name=metric_name,
            baseline_value=baseline,
            current_value=current,
            suggested_action=action
        )
        db.add(alert)
        db.commit()

anomaly_detector = AnomalyDetector()
