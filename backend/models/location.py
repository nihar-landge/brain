"""
Location Log model (integrate with Google Timeline or manual check-ins).
"""

from datetime import datetime, timezone
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


class LocationLog(Base):
    __tablename__ = "location_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    
    # Resolved context
    place_name = Column(String(200), nullable=True)  # e.g., "Home", "Central Park", "Starbucks"
    place_category = Column(String(50), nullable=True)  # e.g., "gym", "office", "park"
    address = Column(String(500), nullable=True)
    
    # Timing
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    duration_minutes = Column(Integer, nullable=True)  # If part of a visit
    
    # Links
    journal_entry_id = Column(Integer, ForeignKey("journal_entries.id", ondelete="SET NULL"), nullable=True)
    context_log_id = Column(Integer, ForeignKey("context_logs.id", ondelete="SET NULL"), nullable=True)
    
    source = Column(String(50), default="gps")  # "gps", "timeline_import", "manual"
    
    __table_args__ = (
        Index("idx_location_user_time", "user_id", "timestamp"),
        Index("idx_location_coords", "latitude", "longitude"),
    )
