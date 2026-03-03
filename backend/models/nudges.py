"""
Proactive Nudge and Suggestion models.
"""

from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    JSON,
    ForeignKey,
    Index,
)
from utils.database import Base


class Nudge(Base):
    __tablename__ = "nudges"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    nudge_type = Column(
        String(50), nullable=False
    )  # "habit_reminder", "mood_checkin", "burnout_warning", "schedule_optimization", "sleep_suggestion", "insight"
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)

    # Actionable links (e.g., {"action": "log_habit", "habit_id": 123})
    action_data = Column(JSON, nullable=True)

    is_read = Column(Boolean, default=False)
    is_dismissed = Column(Boolean, default=False)
    is_acted_upon = Column(Boolean, default=False)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_nudges_user_unread", "user_id", "is_read", "is_dismissed"),
    )


class NudgeSettings(Base):
    __tablename__ = "nudge_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )

    # Opt-ins for different nudge types
    habits_enabled = Column(Boolean, default=True)
    mood_enabled = Column(Boolean, default=True)
    burnout_warnings_enabled = Column(Boolean, default=True)
    sleep_suggestions_enabled = Column(Boolean, default=True)
    insight_enabled = Column(Boolean, default=True)

    # Preferences
    max_nudges_per_day = Column(Integer, default=3)
    quiet_hours_start = Column(String(5), default="22:00")  # HH:MM format
    quiet_hours_end = Column(String(5), default="08:00")  # HH:MM format

    updated_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc)
    )
