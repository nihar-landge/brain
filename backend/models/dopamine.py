"""
Dopamine and Task models for gamification/productivity workflows.
"""

from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Date,
    DateTime,
    Boolean,
    JSON,
    ForeignKey,
    Index,
)

from utils.database import Base


class DopamineItem(Base):
    __tablename__ = "dopamine_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    category = Column(
        String(30), nullable=False
    )  # starter, main, sides, dessert, specials
    title = Column(String(120), nullable=False)
    description = Column(Text, nullable=True)
    duration_min = Column(Integer, nullable=True)
    energy_type = Column(String(20), nullable=True)  # mental, physical, relax
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (Index("idx_dopamine_items_user_cat", "user_id", "category"),)


class DopamineEvent(Base):
    __tablename__ = "dopamine_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    context_log_id = Column(
        Integer, ForeignKey("context_logs.id", ondelete="SET NULL"), nullable=True
    )
    dopamine_item_id = Column(
        Integer, ForeignKey("dopamine_items.id", ondelete="SET NULL"), nullable=True
    )

    trigger_type = Column(
        String(30), nullable=False
    )  # pre_start, long_session, exhausted, manual
    accepted = Column(Boolean, default=False)
    completed = Column(Boolean, default=False)

    shown_at = Column(DateTime, default=datetime.utcnow)
    acted_at = Column(DateTime, nullable=True)

    __table_args__ = (Index("idx_dopamine_events_user_shown", "user_id", "shown_at"),)


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(20), default="todo")  # todo, in_progress, done
    priority = Column(String(20), default="medium")  # low, medium, high, critical

    due_date = Column(Date, nullable=True)
    scheduled_at = Column(DateTime, nullable=True)

    goal_id = Column(
        Integer, ForeignKey("goals.id", ondelete="SET NULL"), nullable=True
    )
    habit_id = Column(
        Integer, ForeignKey("habits.id", ondelete="SET NULL"), nullable=True
    )
    tags = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_tasks_user_status", "user_id", "status"),
        Index("idx_tasks_user_due", "user_id", "due_date"),
    )
