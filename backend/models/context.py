"""
Context Switching models: ContextLog, DeepWorkBlock.
Tracks task/context switches, cognitive load, and deep work sessions.
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


class ContextLog(Base):
    __tablename__ = "context_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    # Context info
    context_name = Column(String(200), nullable=True)
    context_type = Column(
        String(50), nullable=True
    )  # 'deep_work', 'communication', 'admin', 'personal'

    # Timing
    started_at = Column(DateTime, nullable=False)
    ended_at = Column(DateTime, nullable=True)
    duration_minutes = Column(Integer, nullable=True)

    # Classification
    is_interruption = Column(Boolean, default=False)
    interrupted_by = Column(String(200), nullable=True)

    # Cognitive load
    estimated_cognitive_load = Column(
        Integer,
        CheckConstraint(
            "estimated_cognitive_load >= 1 AND estimated_cognitive_load <= 10"
        ),
        nullable=True,
    )
    task_complexity = Column(
        Integer,
        CheckConstraint("task_complexity >= 1 AND task_complexity <= 10"),
        nullable=True,
    )

    # Context before this
    previous_context_id = Column(
        Integer, ForeignKey("context_logs.id", ondelete="SET NULL"), nullable=True
    )
    switch_cost_minutes = Column(Integer, nullable=True)

    # Subsequent metrics
    mood_after = Column(
        Integer, CheckConstraint("mood_after >= 1 AND mood_after <= 10"), nullable=True
    )
    energy_after = Column(
        Integer,
        CheckConstraint("energy_after >= 1 AND energy_after <= 10"),
        nullable=True,
    )
    productivity_rating = Column(
        Integer,
        CheckConstraint("productivity_rating >= 1 AND productivity_rating <= 10"),
        nullable=True,
    )

    # Notes
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (Index("idx_context_logs_user_date", "user_id", "started_at"),)


class DeepWorkBlock(Base):
    __tablename__ = "deep_work_blocks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    context_log_id = Column(
        Integer, ForeignKey("context_logs.id", ondelete="CASCADE"), nullable=False
    )

    block_date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    duration_minutes = Column(Integer, nullable=False)

    # Quality metrics
    interruptions_count = Column(Integer, default=0)
    flow_state_achieved = Column(Boolean, default=False)
    output_quality = Column(
        Integer,
        CheckConstraint("output_quality >= 1 AND output_quality <= 10"),
        nullable=True,
    )

    # What made it work
    success_factors = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (Index("idx_deep_work_user_date", "user_id", "block_date"),)
