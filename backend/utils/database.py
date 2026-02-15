"""
Database Configuration and Session Management.
Uses SQLAlchemy with SQLite for structured data storage.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from config import DATABASE_URL

# Fix SQLite URL for SQLAlchemy
db_url = DATABASE_URL
if db_url.startswith("sqlite:///./"):
    import os

    db_path = db_url.replace("sqlite:///./", "")
    os.makedirs(
        os.path.dirname(db_path) if os.path.dirname(db_path) else ".", exist_ok=True
    )

# Create engine
engine = create_engine(
    db_url,
    connect_args={"check_same_thread": False},  # Required for SQLite
    echo=False,
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for ORM models
Base = declarative_base()


def get_db():
    """Dependency that provides a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all database tables."""
    # Import all models so they register with Base
    from models import user, journal, habits, goals, social, context, dopamine  # noqa: F401

    Base.metadata.create_all(bind=engine)

    # Run lightweight migrations for schema changes
    _migrate_tables()


def _migrate_tables():
    """
    Apply schema migrations that create_all() can't handle
    (adding columns to existing tables in SQLite).
    """
    from sqlalchemy import text, inspect

    inspector = inspect(engine)

    with engine.connect() as conn:
        # Migration 1: Add habit_id to context_logs (Goal → Habit → Session link)
        context_cols = {c["name"] for c in inspector.get_columns("context_logs")}
        if "habit_id" not in context_cols:
            conn.execute(
                text(
                    "ALTER TABLE context_logs ADD COLUMN habit_id INTEGER REFERENCES habits(id) ON DELETE SET NULL"
                )
            )
            conn.commit()

        if "task_id" not in context_cols:
            conn.execute(
                text(
                    "ALTER TABLE context_logs ADD COLUMN task_id INTEGER REFERENCES tasks(id) ON DELETE SET NULL"
                )
            )
            conn.commit()

        if "google_event_id" not in context_cols:
            conn.execute(
                text("ALTER TABLE context_logs ADD COLUMN google_event_id VARCHAR(255)")
            )
            conn.commit()

        # Migration 2: Rename related_goal_id → goal_id on habits (if old column exists)
        habit_cols = {c["name"] for c in inspector.get_columns("habits")}
        if "related_goal_id" in habit_cols and "goal_id" not in habit_cols:
            # SQLite doesn't support RENAME COLUMN before 3.25; add new + copy + drop
            conn.execute(
                text(
                    "ALTER TABLE habits ADD COLUMN goal_id INTEGER REFERENCES goals(id) ON DELETE CASCADE"
                )
            )
            conn.execute(text("UPDATE habits SET goal_id = related_goal_id"))
            conn.commit()
            # Note: Can't DROP old column in SQLite < 3.35, but it's harmless to leave it

        # Migration 3: Add new task columns to existing tasks table
        table_names = set(inspector.get_table_names())
        if "tasks" in table_names:
            task_cols = {c["name"] for c in inspector.get_columns("tasks")}

            if "scheduled_end" not in task_cols:
                conn.execute(
                    text("ALTER TABLE tasks ADD COLUMN scheduled_end DATETIME")
                )
                conn.commit()

            if "is_all_day" not in task_cols:
                conn.execute(
                    text("ALTER TABLE tasks ADD COLUMN is_all_day BOOLEAN DEFAULT 0")
                )
                conn.commit()

            if "estimated_minutes" not in task_cols:
                conn.execute(
                    text("ALTER TABLE tasks ADD COLUMN estimated_minutes INTEGER")
                )
                conn.commit()

            if "spent_minutes" not in task_cols:
                conn.execute(
                    text("ALTER TABLE tasks ADD COLUMN spent_minutes INTEGER DEFAULT 0")
                )
                conn.commit()

            if "google_event_id" not in task_cols:
                conn.execute(
                    text("ALTER TABLE tasks ADD COLUMN google_event_id VARCHAR(255)")
                )
                conn.commit()
