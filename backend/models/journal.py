"""
Journal Entry, Event, Decision, Mood Log, Prediction, and Insight models.
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
    Time,
    DateTime,
    JSON,
    ForeignKey,
    CheckConstraint,
    Index,
)

from utils.database import Base


class JournalEntry(Base):
    __tablename__ = "journal_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    entry_date = Column(Date, nullable=False)
    entry_time = Column(Time, nullable=True)

    # Content
    title = Column(String(200), nullable=True)
    content = Column(Text, nullable=False)

    # Structured data
    mood = Column(Integer, CheckConstraint("mood >= 1 AND mood <= 10"), nullable=True)
    energy_level = Column(Integer, CheckConstraint("energy_level >= 1 AND energy_level <= 10"), nullable=True)
    stress_level = Column(Integer, CheckConstraint("stress_level >= 1 AND stress_level <= 10"), nullable=True)

    # Tags and categories
    tags = Column(JSON, nullable=True)
    category = Column(String(50), nullable=True)

    # Context
    location = Column(String(200), nullable=True)
    weather = Column(String(50), nullable=True)
    sleep_hours = Column(Float, nullable=True)

    # Embeddings Reference
    embedding_id = Column(String(100), nullable=True)
    embedding_generated_at = Column(DateTime, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)  # Soft delete

    __table_args__ = (
        Index("idx_journal_date", "entry_date"),
        Index("idx_journal_user", "user_id"),
        Index("idx_journal_deleted", "deleted_at"),
    )


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    journal_entry_id = Column(Integer, ForeignKey("journal_entries.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    event_title = Column(String(200), nullable=False)
    event_description = Column(Text, nullable=True)
    event_type = Column(String(50), nullable=True)
    importance = Column(Integer, CheckConstraint("importance >= 1 AND importance <= 5"), nullable=True)

    event_date = Column(Date, nullable=False)
    event_time = Column(Time, nullable=True)
    duration_minutes = Column(Integer, nullable=True)

    outcome = Column(String(20), nullable=True)  # "positive", "negative", "neutral"

    people = Column(JSON, nullable=True)  # Added missing field

    created_at = Column(DateTime, default=datetime.utcnow)


class Decision(Base):
    __tablename__ = "decisions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    journal_entry_id = Column(Integer, ForeignKey("journal_entries.id", ondelete="SET NULL"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    decision_title = Column(String(200), nullable=False)
    decision_description = Column(Text, nullable=True)
    decision_category = Column(String(50), nullable=True)

    decision_date = Column(Date, nullable=False)
    decision_time = Column(Time, nullable=True)

    # Decision metadata
    importance = Column(Integer, CheckConstraint("importance >= 1 AND importance <= 5"), nullable=True)
    confidence = Column(Integer, CheckConstraint("confidence >= 1 AND confidence <= 10"), nullable=True)
    emotional_state = Column(String(50), nullable=True)

    # Process
    time_to_decide_hours = Column(Integer, nullable=True)
    alternatives_considered = Column(Integer, nullable=True)
    consulted_people = Column(JSON, nullable=True)

    # Outcome tracking
    outcome_expected = Column(Text, nullable=True)
    success_criteria = Column(Text, nullable=True)
    outcome_actual = Column(Text, nullable=True)
    satisfaction = Column(Integer, CheckConstraint("satisfaction >= 1 AND satisfaction <= 10"), nullable=True)
    outcome_date = Column(Date, nullable=True)

    # Analysis
    reversed = Column(Boolean, default=False)
    reversal_date = Column(Date, nullable=True)
    reversal_reason = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MoodLog(Base):
    __tablename__ = "mood_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    journal_entry_id = Column(Integer, ForeignKey("journal_entries.id", ondelete="SET NULL"), nullable=True)

    log_date = Column(Date, nullable=False)
    log_time = Column(Time, nullable=False)

    mood_value = Column(Integer, CheckConstraint("mood_value >= 1 AND mood_value <= 10"), nullable=False)
    energy_level = Column(Integer, CheckConstraint("energy_level >= 1 AND energy_level <= 10"), nullable=True)
    stress_level = Column(Integer, CheckConstraint("stress_level >= 1 AND stress_level <= 10"), nullable=True)

    # Context
    mood_tags = Column(JSON, nullable=True)
    trigger = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_mood_logs_date", "log_date"),
    )


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    prediction_type = Column(String(50), nullable=False)  # "mood", "habit", "energy", "goal"
    prediction_target = Column(String(100), nullable=True)
    prediction_date = Column(Date, nullable=False)
    target_date = Column(Date, nullable=False)

    # Prediction details
    predicted_value = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)

    # Verification
    actual_value = Column(Float, nullable=True)
    actual_date = Column(Date, nullable=True)
    prediction_accuracy = Column(Float, nullable=True)

    # Model info
    model_name = Column(String(50), nullable=True)
    model_version = Column(String(20), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)


class Insight(Base):
    __tablename__ = "insights"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    insight_type = Column(String(50), nullable=False)  # "pattern", "anomaly", "suggestion", "warning"
    insight_category = Column(String(50), nullable=True)

    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)

    confidence = Column(Float, nullable=False)
    importance = Column(Integer, CheckConstraint("importance >= 1 AND importance <= 5"), nullable=True)

    actionable = Column(Boolean, default=False)
    action_taken = Column(Boolean, default=False)
    action_date = Column(Date, nullable=True)

    supporting_data = Column(JSON, nullable=True)

    dismissed = Column(Boolean, default=False)
    helpful_rating = Column(Integer, CheckConstraint("helpful_rating >= 1 AND helpful_rating <= 5"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)


class MLModel(Base):
    __tablename__ = "ml_models"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    model_name = Column(String(100), nullable=False)
    model_version = Column(String(20), nullable=False)
    model_type = Column(String(50), nullable=True)

    # Training metadata
    training_date = Column(DateTime, nullable=False)
    training_samples = Column(Integer, nullable=True)

    # Performance metrics
    accuracy = Column(Float, nullable=True)
    precision_score = Column(Float, nullable=True)
    recall_score = Column(Float, nullable=True)
    f1_score = Column(Float, nullable=True)
    mae = Column(Float, nullable=True)
    rmse = Column(Float, nullable=True)

    model_file_path = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)


class MLFeature(Base):
    __tablename__ = "ml_features"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    feature_date = Column(Date, nullable=False)
    features = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_ml_features_date", "feature_date"),
    )
