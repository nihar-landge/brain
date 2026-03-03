"""
Report Service for generating Weekly and Monthly AI reports.
"""

import json
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session

from models.reports import LifeReport
from models.journal import JournalEntry
from models.habits import Habit, HabitLog
from services.gemini_service import gemini_service

class ReportService:
    def __init__(self):
        self.system_prompt = """
        You are an insightful AI life coach and psychologist.
        Analyze the provided user data (journal entries, habit logs, mood scores) for the given period.
        Generate a comprehensive, encouraging, and highly personalized report.
        
        Return exactly ONE JSON object with this schema, and NO markdown blocks or text outside it:
        {
            "title": string, // Catchy title for the period (e.g., "A Week of Growth and Consistency")
            "summary": string, // 2-3 sentence high-level summary
            "achievements": [string], // 2-4 key wins or positives
            "challenges": [string], // 1-3 challenges faced or areas of friction
            "mood_trend": string, // "improving", "declining", "stable", or "volatile"
            "habit_performance": dict, // Key insights about habits (e.g. {"best_habit": "Reading", "needs_focus": "Meditation"})
            "recommendations": [string], // 2-3 actionable advice for next period
            "full_markdown": string // A full, beautifully formatted markdown report (use headings, bullet points, bold text)
        }
        """

    def _collect_data(self, db: Session, user_id: int, start_date: date, end_date: date) -> str:
        """Gather all relevant user data for the period to feed to Gemini."""
        # 1. Journals
        entries = db.query(JournalEntry).filter(
            JournalEntry.user_id == user_id,
            JournalEntry.entry_date >= start_date,
            JournalEntry.entry_date <= end_date
        ).order_by(JournalEntry.entry_date).all()
        
        journal_data = []
        for e in entries:
            journal_data.append({
                "date": str(e.entry_date),
                "mood": e.mood,
                "energy": e.energy_level,
                "stress": e.stress_level,
                "content": e.content,
                "emotions": e.emotions if hasattr(e, "emotions") else []
            })
            
        # 2. Habits
        logs = db.query(HabitLog).filter(
            HabitLog.user_id == user_id,
            HabitLog.log_date >= start_date,
            HabitLog.log_date <= end_date
        ).all()
        
        habit_ids = {l.habit_id for l in logs}
        habits = db.query(Habit).filter(Habit.id.in_(habit_ids)).all()
        habit_map = {h.id: h.habit_name for h in habits}
        
        habit_stats = {}
        for l in logs:
            name = habit_map.get(l.habit_id, "Unknown Habit")
            if name not in habit_stats:
                habit_stats[name] = {"completed": 0, "missed": 0}
            if l.completed:
                habit_stats[name]["completed"] += 1
            else:
                habit_stats[name]["missed"] += 1

        # 3. Compile context
        context = {
            "period": f"{start_date} to {end_date}",
            "journals": journal_data,
            "habit_summaries": habit_stats
        }
        return json.dumps(context, indent=2)

    def generate_report(self, db: Session, user_id: int, report_type: str, start_date: date, end_date: date) -> LifeReport:
        """Generate a summarized AI report and save it to the DB."""
        # Check if report already exists for this exact period
        existing = db.query(LifeReport).filter(
            LifeReport.user_id == user_id,
            LifeReport.report_type == report_type,
            LifeReport.period_start == start_date
        ).first()
        
        if existing:
            return existing
            
        # Gather context
        context_json = self._collect_data(db, user_id, start_date, end_date)
        
        # Generate via Gemini
        prompt = f"User Data for {report_type.capitalize()} Report:\n{context_json}"
        
        try:
            response_text = gemini_service.generate_completion(
                user_query=prompt,
                system_prompt=self.system_prompt,
                temperature=0.4
            )
            
            cleaned = response_text.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
                
            result = json.loads(cleaned.strip())
            
            # Save to DB
            report = LifeReport(
                user_id=user_id,
                report_type=report_type,
                period_start=start_date,
                period_end=end_date,
                title=result.get("title", f"{report_type.capitalize()} Report"),
                summary=result.get("summary", "No summary available."),
                achievements=result.get("achievements", []),
                challenges=result.get("challenges", []),
                mood_trend=result.get("mood_trend", "stable"),
                habit_performance=result.get("habit_performance", {}),
                recommendations=result.get("recommendations", []),
                full_markdown=result.get("full_markdown", "Report generation failed formatting."),
                model_used="gemini-2.0-flash"
            )
            db.add(report)
            db.commit()
            db.refresh(report)
            return report
            
        except Exception as e:
            # Create a fallback error report
            report = LifeReport(
                user_id=user_id,
                report_type=report_type,
                period_start=start_date,
                period_end=end_date,
                title=f"Error Generating {report_type.capitalize()} Report",
                summary="There was an issue generating your report due to an AI service error.",
                full_markdown=f"**Error Details:**\n{str(e)}"
            )
            db.add(report)
            db.commit()
            db.refresh(report)
            return report

report_service = ReportService()
