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

# Create engine options
connect_args = {}
if db_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False

# Create engine
engine = create_engine(
    db_url,
    connect_args=connect_args,
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
    from models import sleep, location, nudges, reports, anomalies  # noqa: F401

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


        # Migration 4: Add new columns to users table
        if "users" in table_names:
            user_cols = {c["name"] for c in inspector.get_columns("users")}

            if "hashed_password" not in user_cols:
                conn.execute(
                    text("ALTER TABLE users ADD COLUMN hashed_password VARCHAR(255)")
                )
                conn.commit()

            if "google_id" not in user_cols:
                conn.execute(
                    text("ALTER TABLE users ADD COLUMN google_id VARCHAR(255)")
                )
                conn.commit()

            if "google_access_token" not in user_cols:
                conn.execute(
                    text("ALTER TABLE users ADD COLUMN google_access_token VARCHAR(255)")
                )
                conn.commit()

            if "google_refresh_token" not in user_cols:
                conn.execute(
                    text("ALTER TABLE users ADD COLUMN google_refresh_token VARCHAR(255)")
                )
                conn.commit()

            if "google_token_expiry" not in user_cols:
                conn.execute(
                    text("ALTER TABLE users ADD COLUMN google_token_expiry DATETIME")
                )
                conn.commit()

            if "avatar_url" not in user_cols:
                conn.execute(
                    text("ALTER TABLE users ADD COLUMN avatar_url VARCHAR(500)")
                )
                conn.commit()

            if "preferences" not in user_cols:
                conn.execute(
                    text("ALTER TABLE users ADD COLUMN preferences JSON")
                )
                conn.commit()

        # Migration 5: Add new columns to journal_entries table
        if "journal_entries" in table_names:
            journal_cols = {c["name"] for c in inspector.get_columns("journal_entries")}

            new_journal_cols = [
                ("sentiment_score", "FLOAT"),
                ("sentiment_label", "VARCHAR(20)"),
                ("emotions", "JSON"),
                ("topics", "JSON"),
                ("cognitive_distortions", "JSON"),
                ("dream_type", "VARCHAR(50)"),
                ("dream_symbols", "JSON"),
                ("dream_interpretation", "TEXT"),
                ("dream_recurring_pattern", "BOOLEAN")
            ]

            for col_name, col_type in new_journal_cols:
                if col_name not in journal_cols:
                    conn.execute(
                        text(f"ALTER TABLE journal_entries ADD COLUMN {col_name} {col_type}")
                    )
                    conn.commit()

        # Migration 6: Explicitly create new tables if they were missed by create_all()
        # This happens in SQLite when the database file already exists but the models weren't imported yet.
        from models import sleep, location, nudges, reports, anomalies, dopamine
        
        models_to_ensure = [
            sleep.SleepLog,
            location.LocationLog,
            nudges.Nudge,
            nudges.NudgeSettings,
            reports.LifeReport,
            anomalies.AnomalyAlert,
            dopamine.DopamineItem,
            dopamine.DopamineEvent
        ]
        
        for model in models_to_ensure:
            try:
                model.__table__.create(engine, checkfirst=True)
            except Exception as e:
                # Catch errors if table already exists or other dialect issues
                print(f"Schema warning for {model.__tablename__}: {e}")
