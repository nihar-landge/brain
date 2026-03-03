"""
Anomaly Alert model for detecting abrupt changes in habits, mood, and sleep.
"""

from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    Float,
    JSON,
    ForeignKey,
    Index,
)
from utils.database import Base


class AnomalyAlert(Base):
    __tablename__ = "anomaly_alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    
    anomaly_type = Column(String(50), nullable=False)  # "mood_drop", "sleep_disruption", "streak_broken", "schedule_drift"
    severity = Column(String(20), nullable=False)  # "low", "medium", "high", "critical"
    
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    
    # Metric details
    detected_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    metric_name = Column(String(50), nullable=True)  # e.g., "avg_mood_7d"
    baseline_value = Column(Float, nullable=True)
    current_value = Column(Float, nullable=True)
    
    # AI Analysis & Nudging
    ai_explanation = Column(Text, nullable=True)
    suggested_action = Column(JSON, nullable=True)  # Similar to Nudge action_data
    
    is_acknowledged = Column(Boolean, default=False)
    is_false_positive = Column(Boolean, default=False)
    resolution_notes = Column(Text, nullable=True)
    
    __table_args__ = (
        Index("idx_anomalies_user_type", "user_id", "anomaly_type", "detected_at"),
    )
