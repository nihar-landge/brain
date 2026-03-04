"""
Test Configuration & Fixtures.
Provides in-memory SQLite database and FastAPI TestClient for all tests.
"""

import os
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from utils.database import Base, get_db
from main import app
from models import user, journal, habits, goals  # noqa: F401
from models import social, context, dopamine  # noqa: F401
from models import sleep, location, nudges, reports, anomalies  # noqa: F401

from sqlalchemy.pool import StaticPool

# In-memory SQLite for tests
TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_database():
    """Create tables before each test, drop after."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture()
def client():
    """FastAPI test client with overridden DB dependency."""
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def db_session():
    """Direct DB session for test data setup."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture()
def test_user(db_session, setup_database):
    """Create a default test user."""
    from models.user import User
    from utils.auth_jwt import hash_password
    
    user = db_session.query(User).filter(User.email == "test@example.com").first()
    if not user:
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password=hash_password("testpassword"),
            full_name="Test User",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    return user

@pytest.fixture()
def auth_headers(test_user):
    """Return valid JWT authorization headers for test_user."""
    from utils.auth_jwt import create_access_token
    
    access_token = create_access_token(
        user_id=test_user.id,
        email=test_user.email
    )
    return {"Authorization": f"Bearer {access_token}"}

@pytest.fixture()
def test_goal(client, auth_headers):
    """Create a default test goal for habits to link to."""
    resp = client.post("/api/goals", headers=auth_headers, json={
        "goal_title": "Default Test Goal",
        "start_date": "2023-01-01"
    })
    return resp.json()["id"]
