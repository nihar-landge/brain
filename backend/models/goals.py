"""
Goal and GoalMilestone models.
"""

from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    CheckConstraint,
)

from utils.database import Base


class Goal(Base):
    __tablename__ = "goals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    parent_goal_id = Column(Integer, ForeignKey("goals.id", ondelete="SET NULL"), nullable=True)

    goal_title = Column(String(200), nullable=False)
    goal_description = Column(Text, nullable=True)
    goal_category = Column(String(50), nullable=True)

    # Timeline
    start_date = Column(Date, nullable=False)
    target_date = Column(Date, nullable=True)
    completed_date = Column(Date, nullable=True)

    # Status
    status = Column(String(20), default="active")  # "active", "completed", "abandoned"
    progress = Column(Integer, CheckConstraint("progress >= 0 AND progress <= 100"), default=0)

    # Metadata
    priority = Column(Integer, CheckConstraint("priority >= 1 AND priority <= 5"), nullable=True)
    is_recurring = Column(Boolean, default=False)
    recurrence_pattern = Column(String(50), nullable=True)

    # Complexity & Planning
    complexity = Column(Integer, CheckConstraint("complexity >= 1 AND complexity <= 10"), nullable=True)
    estimated_hours = Column(Integer, nullable=True)

    # Motivation
    motivation_level = Column(Integer, CheckConstraint("motivation_level >= 1 AND motivation_level <= 10"), nullable=True)
    why_important = Column(Text, nullable=True)

    # Outcome
    achievement_level = Column(Integer, CheckConstraint("achievement_level >= 1 AND achievement_level <= 5"), nullable=True)
    satisfaction = Column(Integer, CheckConstraint("satisfaction >= 1 AND satisfaction <= 10"), nullable=True)
    completion_notes = Column(Text, nullable=True)
    lessons_learned = Column(Text, nullable=True)

    last_progress_update = Column(Date, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class GoalMilestone(Base):
    __tablename__ = "goal_milestones"

    id = Column(Integer, primary_key=True, autoincrement=True)
    goal_id = Column(Integer, ForeignKey("goals.id", ondelete="CASCADE"), nullable=False)

    milestone_title = Column(String(200), nullable=False)
    milestone_description = Column(Text, nullable=True)
    milestone_order = Column(Integer, nullable=True)

    target_date = Column(Date, nullable=True)
    completed_date = Column(Date, nullable=True)
    completed = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
