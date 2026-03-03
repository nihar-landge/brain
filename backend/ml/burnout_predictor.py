"""
Burnout Predictor Engine.
Analyzes stress, energy, task completion, and context logs to assess burnout risk.
"""

from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from models.journal import JournalEntry
from models.dopamine import Task
from models.context import ContextLog

class BurnoutPredictor:
    def __init__(self):
        pass

    def calculate_risk(self, db: Session, user_id: int) -> dict:
        """
        Calculate burnout risk (0-100) based on recent stress, energy, and work hours.
        """
        now = datetime.now(timezone.utc)
        fourteen_days_ago = now - timedelta(days=14)
        
        # 1. Stress & Energy (from Journals)
        journals = db.query(JournalEntry).filter(
            JournalEntry.user_id == user_id,
            JournalEntry.entry_date >= fourteen_days_ago.date()
        ).all()
        
        avg_stress = 5.0
        avg_energy = 5.0
        if journals:
            valid_stress = [j.stress_level for j in journals if j.stress_level is not None]
            valid_energy = [j.energy_level for j in journals if j.energy_level is not None]
            
            if valid_stress:
                avg_stress = sum(valid_stress) / len(valid_stress)
            if valid_energy:
                avg_energy = sum(valid_energy) / len(valid_energy)
                
        # 2. Workload (from ContextLogs)
        # Calculate total focused work hours in the last 14 days
        work_logs = db.query(ContextLog).filter(
            ContextLog.user_id == user_id,
            ContextLog.started_at >= fourteen_days_ago,
            ContextLog.ended_at != None
        ).all()
        
        total_work_minutes = 0
        for log in work_logs:
            if log.ended_at and log.started_at:
                diff = log.ended_at - log.started_at
                total_work_minutes += diff.total_seconds() / 60
                
        avg_daily_work_hours = (total_work_minutes / 60) / 14
        
        # 3. Task Completion Rate (overwhelm indicator)
        tasks = db.query(Task).filter(
            Task.user_id == user_id,
            Task.created_at >= fourteen_days_ago
        ).all()
        
        completed_tasks = [t for t in tasks if t.status == "done"]
        completion_rate = len(completed_tasks) / max(len(tasks), 1)
        
        # Calculate Risk Score (0 = great, 100 = critical)
        # Weights: Stress (40%), Energy drop (30%), Workload (20%), Overwhelm/Task rate (10%)
        
        stress_factor = (avg_stress / 10) * 40 # Up to 40 points
        
        energy_factor = ((10 - avg_energy) / 10) * 30 # Up to 30 points (lower energy = higher risk)
        
        # Assume >8 hours average tracked focused work is high
        workload_factor = min(avg_daily_work_hours / 8.0, 1.0) * 20 # Up to 20 points
        
        # Lower completion rate = higher overwhelm
        overwhelm_factor = (1.0 - completion_rate) * 10 # Up to 10 points
        
        risk_score = int(stress_factor + energy_factor + workload_factor + overwhelm_factor)
        
        # Determine risk level
        if risk_score >= 75:
            level = "Critical"
            insight = "High stress and low energy combined with heavy workload. Immediate rest is strongly advised."
        elif risk_score >= 55:
            level = "High"
            insight = "You are showing strong signs of impending burnout. Consider reducing your workload this week."
        elif risk_score >= 35:
            level = "Moderate"
            insight = "Stress levels are slightly elevated. Monitor your energy and ensure you are taking adequate breaks."
        else:
            level = "Low"
            insight = "Your workload and stress levels are balanced. Keep up the good work."
            
        factors = []
        if avg_stress >= 7: factors.append("chronically high stress")
        if avg_energy <= 4: factors.append("persistent low energy")
        if avg_daily_work_hours >= 7: factors.append("heavy tracked work hours")
        if completion_rate <= 0.4: factors.append("low task completion rate (overwhelm)")

        return {
            "risk_score": risk_score,
            "risk_level": level,
            "primary_insight": insight,
            "contributing_factors": factors,
            "metrics": {
                "avg_stress_14d": round(avg_stress, 1),
                "avg_energy_14d": round(avg_energy, 1),
                "avg_daily_work_hours_14d": round(avg_daily_work_hours, 1),
                "task_completion_rate": round(completion_rate * 100, 1)
            }
        }

burnout_predictor = BurnoutPredictor()
