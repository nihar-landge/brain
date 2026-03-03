"""
Life Reports model for AI-generated weekly and monthly summaries.
"""

from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Date,
    JSON,
    ForeignKey,
    Index,
)
from utils.database import Base


class LifeReport(Base):
    __tablename__ = "life_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    
    report_type = Column(String(20), nullable=False)  # "weekly", "monthly", "yearly"
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    
    title = Column(String(200), nullable=False)
    summary = Column(Text, nullable=False)
    
    # Structured analysis from AI
    achievements = Column(JSON, nullable=True)  # List of strings
    challenges = Column(JSON, nullable=True)     # List of strings
    mood_trend = Column(String(50), nullable=True) # "improving", "declining", "stable", "volatile"
    habit_performance = Column(JSON, nullable=True) # Key habit stats
    recommendations = Column(JSON, nullable=True)   # AI recommendations for next period
    
    # Full markdown report body
    full_markdown = Column(Text, nullable=False)
    
    model_used = Column(String(50), nullable=True)  # E.g., "gemini-2.0-flash"
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_reports_user_period", "user_id", "report_type", "period_start"),
    )
