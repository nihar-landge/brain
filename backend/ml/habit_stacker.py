"""
Habit Stacker Engine.
Analyzes co-occurrence of habits to suggest natural pairings (synergy-based stacking).
"""

from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from itertools import combinations

from models.habits import Habit, HabitLog

class HabitStacker:
    def __init__(self):
        pass

    def get_stacking_suggestions(self, db: Session, user_id: int) -> dict:
        """
        Analyze habit logs to find habits that are frequently done together,
        or suggest pairing a weak habit with a strong habit.
        """
        thirty_days_ago = datetime.now(timezone.utc).date() - timedelta(days=30)
        
        # 1. Get all active habits
        active_habits = db.query(Habit).filter(
            Habit.user_id == user_id,
            Habit.status == "active"
        ).all()
        
        if len(active_habits) < 2:
            return {"status": "insufficient_habits", "message": "Need at least 2 active habits"}
            
        habit_map = {h.id: h for h in active_habits}
        habit_ids = list(habit_map.keys())
        
        # 2. Get all successful logs in the last 30 days
        logs = db.query(HabitLog).filter(
            HabitLog.habit_id.in_(habit_ids),
            HabitLog.log_date >= thirty_days_ago,
            HabitLog.completed == True
        ).all()
        
        # Group logs by date
        from collections import defaultdict
        logs_by_date = defaultdict(set)
        for log in logs:
            logs_by_date[log.log_date].add(log.habit_id)
            
        # 3. Calculate habit strength (completion rate)
        habit_strength = {}
        for hid in habit_ids:
            completed_days = sum(1 for date, h_set in logs_by_date.items() if hid in h_set)
            habit_strength[hid] = completed_days / 30.0
            
        # Sort habits by strength
        sorted_habits = sorted(habit_strength.items(), key=lambda x: x[1], reverse=True)
        strong_habits = [hid for hid, strength in sorted_habits if strength >= 0.7] # > 70% completion
        weak_habits = [hid for hid, strength in sorted_habits if 0.2 <= strength < 0.7] # 20-70% completion
        
        # 4. Find natural pairings (co-occurrence)
        pair_counts = defaultdict(int)
        for date, completed_set in logs_by_date.items():
            if len(completed_set) >= 2:
                # Add all pairs completed on this day
                for h1, h2 in combinations(sorted(list(completed_set)), 2):
                    pair_counts[(h1, h2)] += 1
                    
        # Find top natural pairs
        top_pairs = sorted(pair_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        
        suggestions = []
        
        # Suggestion Type 1: Natural Synergies
        for (h1, h2), count in top_pairs:
            if count >= 5: # Completed together at least 5 times
                n1 = habit_map[h1].habit_name
                n2 = habit_map[h2].habit_name
                suggestions.append({
                    "type": "natural_synergy",
                    "habits": [n1, n2],
                    "habit_ids": [h1, h2],
                    "insight": f"You naturally do '{n1}' and '{n2}' on the same day. Try deliberately linking them: 'After I {n1}, I will {n2}.'"
                })
                
        # Suggestion Type 2: Anchor Habit Stacking (piggyback weak onto strong)
        if strong_habits and weak_habits:
            s_id = strong_habits[0]
            w_id = weak_habits[0]
            s_name = habit_map[s_id].habit_name
            w_name = habit_map[w_id].habit_name
            
            suggestions.append({
                "type": "anchor_stacking",
                "habits": [s_name, w_name],
                "habit_ids": [s_id, w_id],
                "insight": f"Piggyback a struggling habit onto a strong one: Use '{s_name}' as the trigger to immediately start '{w_name}'."
            })
            
        return {
            "status": "success",
            "active_habit_count": len(active_habits),
            "suggestions": suggestions
        }

habit_stacker = HabitStacker()
