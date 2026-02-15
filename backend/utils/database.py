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
    from models import user, journal, habits, goals, social, context  # noqa: F401

    Base.metadata.create_all(bind=engine)
