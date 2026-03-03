"""
Sleep-Mood Engine.
Finds correlations between sleep duration/quality and next-day mood/energy.
"""

from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from models.sleep import SleepLog
from models.journal import JournalEntry

class SleepMoodEngine:
    def __init__(self):
        pass

    def calculate_correlations(self, db: Session, user_id: int, days_back: int = 30) -> dict:
        """Calculate how sleep metrics affect next-day mood and energy."""
        start_date = datetime.utcnow().date() - timedelta(days=days_back)

        # 1. Get Sleep Logs
        sleep_logs = db.query(SleepLog).filter(
            SleepLog.user_id == user_id,
            func.date(SleepLog.bed_time) >= start_date # Approximate "sleep date" by bed_time date
        ).all()

        if len(sleep_logs) < 5:
            return {"status": "insufficient_data", "message": "Need at least 5 days of sleep data"}

        # 2. Get next-day Journals
        journals = db.query(JournalEntry).filter(
            JournalEntry.user_id == user_id,
            JournalEntry.entry_date >= start_date,
            JournalEntry.mood != None
        ).all()
        
        journal_map = {j.entry_date: j for j in journals}

        # 3. Pair them up
        pairs = []
        for sleep in sleep_logs:
            # The "next day" mood is the date of the wake_time (or day after bed_time)
            wake_date = sleep.wake_time.date()
            if wake_date in journal_map:
                pairs.append({
                    "duration": sleep.duration_hours,
                    "quality": sleep.quality_score or 50, # fallback
                    "mood": journal_map[wake_date].mood,
                    "energy": journal_map[wake_date].energy_level or 5 # fallback 
                })

        if len(pairs) < 5:
            return {"status": "insufficient_data", "message": "Need at least 5 days of paired sleep-mood data"}

        # 4. Simple Analysis (A real ML model would use Pearson correlation/regression)
        # Here we just find averages based on buckets
        
        # Bucket by duration
        short_sleep = [p for p in pairs if p["duration"] < 6.5]
        good_sleep = [p for p in pairs if 6.5 <= p["duration"] <= 8.5]
        
        avg_mood_short = sum(p["mood"] for p in short_sleep) / max(len(short_sleep), 1)
        avg_mood_good = sum(p["mood"] for p in good_sleep) / max(len(good_sleep), 1)
        
        # Calculate optimal duration
        # Find the duration that yields the highest average mood
        from collections import defaultdict
        duration_moods = defaultdict(list)
        for p in pairs:
            rounded_dur = round(p["duration"] * 2) / 2 # Round to nearest 0.5 hour
            duration_moods[rounded_dur].append(p["mood"])
            
        optimal_duration = max(duration_moods.keys(), key=lambda d: sum(duration_moods[d])/len(duration_moods[d]))

        return {
            "status": "success",
            "pairs_analyzed": len(pairs),
            "correlation_strength": "strong" if (avg_mood_good - avg_mood_short) > 1.5 else "moderate",
            "avg_mood_when_short_sleep": round(avg_mood_short, 1),
            "avg_mood_when_good_sleep": round(avg_mood_good, 1),
            "optimal_sleep_duration": optimal_duration,
            "insight": f"You average a {round(avg_mood_good, 1)} mood with 7-8 hours, dropping to {round(avg_mood_short, 1)} under 6.5 hours."
        }
        
    def generate_quality_score(self, duration: float, awakenings: int, rem_minutes: int = 0, deep_minutes: int = 0) -> int:
        """Heuristic calculation of sleep quality 1-100."""
        score = 100
        
        # Duration penalty (optimal is 7.5 to 8.5)
        if duration < 6:
            score -= (6 - duration) * 15
        elif duration > 9:
            score -= (duration - 9) * 10
            
        # Awakenings penalty
        score -= (awakenings * 5)
        
        # Deep/REM bonus (if tracked by wearable)
        if deep_minutes > 0 and rem_minutes > 0:
            total_sleep_mins = duration * 60
            deep_pct = deep_minutes / total_sleep_mins
            rem_pct = rem_minutes / total_sleep_mins
            
            if deep_pct < 0.15: score -= 10
            elif deep_pct > 0.20: score += 5
            
            if rem_pct < 0.20: score -= 10
            elif rem_pct > 0.25: score += 5
            
        return max(1, min(100, int(score)))

sleep_mood_engine = SleepMoodEngine()
