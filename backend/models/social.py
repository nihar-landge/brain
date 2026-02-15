"""
Social Graph models: People, SocialInteraction, SocialBatteryLog.
Tracks relationships, social interactions, and their impact on mood/energy.
"""

from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Float,
    Boolean,
    Date,
    DateTime,
    JSON,
    ForeignKey,
    CheckConstraint,
    Index,
)

from utils.database import Base


class Person(Base):
    __tablename__ = "people"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    name = Column(String(200), nullable=False)
    relationship_type = Column(
        String(50), nullable=True
    )  # 'friend', 'family', 'colleague', 'mentor'
    first_mentioned_date = Column(Date, nullable=True)
    total_mentions = Column(Integer, default=0)

    # Calculated metrics
    avg_mood_impact = Column(Float, nullable=True)
    interaction_frequency = Column(
        String(20), nullable=True
    )  # 'daily', 'weekly', 'monthly', 'rare'
    energy_impact = Column(Float, nullable=True)
    stress_impact = Column(Float, nullable=True)

    # Tags
    tags = Column(JSON, nullable=True)  # ["supportive", "draining", "inspiring"]

    # Status
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (Index("idx_people_user", "user_id"),)


class SocialInteraction(Base):
    __tablename__ = "social_interactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    journal_entry_id = Column(
        Integer, ForeignKey("journal_entries.id", ondelete="SET NULL"), nullable=True
    )
    person_id = Column(
        Integer, ForeignKey("people.id", ondelete="CASCADE"), nullable=False
    )

    interaction_date = Column(Date, nullable=False)
    interaction_type = Column(
        String(50), nullable=True
    )  # 'meeting', 'call', 'text', 'social_event'
    duration_minutes = Column(Integer, nullable=True)

    # Context
    mood_before = Column(
        Integer,
        CheckConstraint("mood_before >= 1 AND mood_before <= 10"),
        nullable=True,
    )
    mood_after = Column(
        Integer, CheckConstraint("mood_after >= 1 AND mood_after <= 10"), nullable=True
    )
    energy_before = Column(
        Integer,
        CheckConstraint("energy_before >= 1 AND energy_before <= 10"),
        nullable=True,
    )
    energy_after = Column(
        Integer,
        CheckConstraint("energy_after >= 1 AND energy_after <= 10"),
        nullable=True,
    )

    # Quality
    quality_rating = Column(
        Integer,
        CheckConstraint("quality_rating >= 1 AND quality_rating <= 10"),
        nullable=True,
    )
    draining_vs_energizing = Column(
        Integer,
        CheckConstraint("draining_vs_energizing >= -5 AND draining_vs_energizing <= 5"),
        nullable=True,
    )

    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_social_interactions_date", "user_id", "interaction_date"),
        Index("idx_social_interactions_person", "person_id"),
    )


class SocialBatteryLog(Base):
    __tablename__ = "social_battery_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    log_date = Column(Date, nullable=False)

    # Time tracking
    solo_time_minutes = Column(Integer, default=0)
    social_time_minutes = Column(Integer, default=0)

    # Battery level (1-10)
    battery_level = Column(
        Integer,
        CheckConstraint("battery_level >= 1 AND battery_level <= 10"),
        nullable=True,
    )

    # Optimal ratio for this user (calculated)
    optimal_solo_ratio = Column(Float, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
