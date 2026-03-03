"""
Schedule Optimizer Engine.
Recommends optimal times for tasks based on historical productivity and energy patterns.
"""

from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from models.context import ContextLog
from models.dopamine import Task
from models.journal import JournalEntry

class ScheduleOptimizer:
    def __init__(self):
        pass

    def get_optimal_schedule(self, db: Session, user_id: int) -> dict:
        """Recommend daily chunks based on historical energy/productivity."""
        # 1. Analyze Context Logs to find highly productive hours
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        logs = db.query(ContextLog).filter(
            ContextLog.user_id == user_id,
            ContextLog.productivity_score >= 4,
            ContextLog.ended_at != None,
            ContextLog.started_at >= thirty_days_ago
        ).all()

        # Bucket by hour
        from collections import defaultdict
        hour_scores = defaultdict(list)
        
        for log in logs:
            if log.started_at:
                hour = log.started_at.hour
                hour_scores[hour].append(log.productivity_score)

        if not hour_scores:
            # Fallback to general advice
            return self._get_fallback_schedule()

        # Average score per hour
        avg_by_hour = {h: sum(scores)/len(scores) for h, scores in hour_scores.items()}
        
        # Find peak hour
        peak_hour = max(avg_by_hour.keys(), key=lambda k: avg_by_hour[k])
        
        # Categorize hours
        deep_work_hours = [h for h, s in avg_by_hour.items() if s >= 4.5]
        shallow_work_hours = [h for h, s in avg_by_hour.items() if 3 <= s < 4.5]
        
        if not deep_work_hours:
            deep_work_hours = [peak_hour] # At least one

        return {
            "status": "success",
            "peak_productivity_hour": f"{peak_hour}:00",
            "recommended_schedule": {
                "deep_work": [f"{h}:00 - {h+1}:00" for h in sorted(deep_work_hours[:2])],
                "shallow_work": [f"{h}:00 - {h+1}:00" for h in sorted(shallow_work_hours[:2])],
                "rest": ["12:00 - 13:00", "20:00 - 22:00"] # Static for now
            },
            "insight": f"You historically do your best work around {peak_hour}:00. Try scheduling difficult tasks then."
        }
        
    def _get_fallback_schedule(self):
        return {
            "status": "fallback",
            "peak_productivity_hour": "10:00",
            "recommended_schedule": {
                "deep_work": ["09:00 - 11:30"],
                "shallow_work": ["14:00 - 16:00"],
                "rest": ["12:00 - 13:00", "18:00 - 22:00"]
            },
            "insight": "We need more context logs and completed tasks to personalize your schedule."
        }

schedule_optimizer = ScheduleOptimizer()
