"""
Habit and HabitLog models.
"""

from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    Date,
    Time,
    DateTime,
    JSON,
    ForeignKey,
    CheckConstraint,
    Index,
)

from utils.database import Base


class Habit(Base):
    __tablename__ = "habits"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    habit_name = Column(String(100), nullable=False)
    habit_description = Column(Text, nullable=True)
    habit_category = Column(String(50), nullable=True)

    # Configuration
    target_frequency = Column(String(50), nullable=True)  # "daily", "3x_per_week", etc.
    target_days = Column(JSON, nullable=True)  # [1, 3, 5] for Mon, Wed, Fri
    target_time = Column(Time, nullable=True)
    reminder_enabled = Column(Boolean, default=True)

    # Status
    status = Column(String(20), default="active")  # "active", "paused", "completed"
    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)

    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)

    # Relations — every habit must belong to a goal (Goal → Habit → Session hierarchy)
    goal_id = Column(Integer, ForeignKey("goals.id", ondelete="CASCADE"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)


class HabitLog(Base):
    __tablename__ = "habit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    habit_id = Column(
        Integer, ForeignKey("habits.id", ondelete="CASCADE"), nullable=False
    )
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    journal_entry_id = Column(
        Integer, ForeignKey("journal_entries.id", ondelete="SET NULL"), nullable=True
    )

    log_date = Column(Date, nullable=False)
    log_time = Column(Time, nullable=True)

    completed = Column(Boolean, nullable=False)

    # Context
    difficulty = Column(
        Integer, CheckConstraint("difficulty >= 1 AND difficulty <= 5"), nullable=True
    )
    satisfaction = Column(
        Integer,
        CheckConstraint("satisfaction >= 1 AND satisfaction <= 5"),
        nullable=True,
    )
    notes = Column(Text, nullable=True)

    # Why if not completed
    skip_reason = Column(String(100), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_habit_logs_date", "log_date"),
        Index("idx_habit_logs_habit", "habit_id"),
    )
