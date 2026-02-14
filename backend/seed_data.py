"""
Seed Data Script - Populate database with sample data for testing.
"""

import os
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime, timedelta, time
import random

from utils.database import create_tables, SessionLocal
from models.user import User
from models.journal import JournalEntry, MoodLog
from models.habits import Habit, HabitLog
from models.goals import Goal, GoalMilestone


def seed():
    """Seed database with sample data."""
    create_tables()
    db = SessionLocal()

    try:
        # Check if already seeded
        if db.query(User).first():
            print("⚠️ Database already seeded. Skipping.")
            return

        print("🌱 Seeding database...")

        # Create default user
        user = User(username="user", email="user@personal-ai.local")
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"✅ User created: {user.username}")

        # Create journal entries for last 60 days
        moods_data = []
        for i in range(60):
            date = datetime.now() - timedelta(days=i)
            day = date.weekday()

            # Simulate patterns: weekends are better
            base_mood = 7 if day >= 5 else 6
            mood = max(1, min(10, base_mood + random.randint(-2, 2)))
            energy = max(1, min(10, (7 if day >= 5 else 5) + random.randint(-2, 2)))
            stress = max(1, min(10, (3 if day >= 5 else 6) + random.randint(-2, 2)))

            contents = [
                f"Had a productive day today. Felt {['great', 'good', 'okay', 'tired'][random.randint(0, 3)]}.",
                f"Morning was slow but afternoon picked up. Energy was {'high' if energy > 6 else 'moderate'}.",
                f"Worked on personal projects. {'Really enjoyable' if mood > 7 else 'Made some progress'}.",
                f"{'Relaxing weekend' if day >= 5 else 'Busy workday'}. {['Did some reading', 'Went for a walk', 'Cooked a new recipe', 'Watched a documentary'][random.randint(0, 3)]}.",
            ]

            entry = JournalEntry(
                user_id=user.id,
                content=contents[random.randint(0, 3)],
                title=f"Day {60 - i}",
                mood=mood,
                energy_level=energy,
                stress_level=stress,
                entry_date=date.date(),
                entry_time=time(random.randint(19, 22), random.randint(0, 59)),
                tags=random.sample(["work", "health", "social", "learning", "exercise"], k=random.randint(1, 3)),
                category=random.choice(["daily", "reflection", "gratitude"]),
            )
            db.add(entry)

            moods_data.append((date, mood, energy, stress, entry))

        db.commit()
        print(f"✅ Created 60 journal entries")

        # Create mood logs from entries
        for date, mood, energy, stress, entry in moods_data:
            db.refresh(entry)
            mood_log = MoodLog(
                user_id=user.id,
                journal_entry_id=entry.id,
                log_date=date.date(),
                log_time=time(random.randint(19, 22), random.randint(0, 59)),
                mood_value=mood,
                energy_level=energy,
                stress_level=stress,
            )
            db.add(mood_log)

        db.commit()
        print(f"✅ Created 60 mood logs")

        # Create habits
        habits_config = [
            ("Morning Meditation", "wellness", "daily"),
            ("Exercise", "health", "daily"),
            ("Read 30 mins", "learning", "daily"),
            ("Code Practice", "career", "daily"),
        ]

        created_habits = []
        for name, category, freq in habits_config:
            habit = Habit(
                user_id=user.id,
                habit_name=name,
                habit_category=category,
                target_frequency=freq,
                start_date=(datetime.now() - timedelta(days=45)).date(),
                status="active",
            )
            db.add(habit)
            created_habits.append(habit)

        db.commit()

        # Create habit logs
        for habit in created_habits:
            db.refresh(habit)
            success_rate = random.uniform(0.6, 0.85)
            for i in range(45):
                date = datetime.now() - timedelta(days=i)
                completed = random.random() < success_rate
                log = HabitLog(
                    habit_id=habit.id,
                    user_id=user.id,
                    log_date=date.date(),
                    log_time=time(random.randint(6, 10), random.randint(0, 59)),
                    completed=completed,
                    difficulty=random.randint(1, 5) if completed else None,
                    satisfaction=random.randint(3, 5) if completed else None,
                )
                db.add(log)

        db.commit()
        print(f"✅ Created {len(created_habits)} habits with 45 days of logs each")

        # Create goals
        goals_config = [
            ("Get fit", "Run 5K without stopping", "health", 65),
            ("Learn ML", "Complete ML course and build project", "career", 40),
            ("Read 24 books", "Read 2 books per month this year", "learning", 30),
        ]

        for title, desc, category, progress in goals_config:
            goal = Goal(
                user_id=user.id,
                goal_title=title,
                goal_description=desc,
                goal_category=category,
                start_date=(datetime.now() - timedelta(days=60)).date(),
                target_date=(datetime.now() + timedelta(days=120)).date(),
                progress=progress,
                priority=random.randint(2, 5),
            )
            db.add(goal)
            db.commit()
            db.refresh(goal)

            # Add milestones
            for j, ms in enumerate(["Phase 1", "Phase 2", "Phase 3"]):
                milestone = GoalMilestone(
                    goal_id=goal.id,
                    milestone_title=f"{ms}: {title}",
                    completed=j < (progress // 35),
                    completed_date=datetime.now().date() if j < (progress // 35) else None,
                )
                db.add(milestone)

        db.commit()
        print(f"✅ Created {len(goals_config)} goals with milestones")

        print("\n🎉 Seeding complete!")
        print(f"   📝 60 journal entries")
        print(f"   😊 60 mood logs")
        print(f"   ✅ {len(created_habits)} habits × 45 days = {len(created_habits) * 45} habit logs")
        print(f"   🎯 {len(goals_config)} goals with milestones")

    except Exception as e:
        db.rollback()
        print(f"❌ Seeding failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
