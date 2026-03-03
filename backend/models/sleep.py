"""
Sleep Log model with quality metrics and correlations.
"""

from datetime import datetime, timezone, timedelta
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Boolean,
    JSON,
    ForeignKey,
    Index,
)
from utils.database import Base


class SleepLog(Base):
    __tablename__ = "sleep_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    
    # Core Times
    bed_time = Column(DateTime, nullable=False)
    wake_time = Column(DateTime, nullable=False)
    
    # Metrics
    duration_hours = Column(Float, nullable=False)  # Usually wake - bed
    deep_sleep_minutes = Column(Integer, nullable=True)
    rem_sleep_minutes = Column(Integer, nullable=True)
    light_sleep_minutes = Column(Integer, nullable=True)
    awake_minutes = Column(Integer, default=0)
    
    # Subjective/Calculated Quality
    quality_score = Column(Integer, nullable=True)  # 1-100 score
    subjective_rating = Column(Integer, nullable=True)  # 1-5 stars

    # Context & Factors
    factors = Column(JSON, nullable=True)  # e.g., ["caffeine_late", "alcohol", "exercise", "screen_time"]
    notes = Column(String(500), nullable=True)
    source = Column(String(50), default="manual")  # "manual", "apple_health", "ouraring"
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_sleep_user_dates", "user_id", "bed_time", "wake_time"),
    )

    @property
    def formatted_duration(self) -> str:
        hours = int(self.duration_hours)
        minutes = int((self.duration_hours - hours) * 60)
        return f"{hours}h {minutes}m"
