"""
Simple API Key Authentication.
Protects all API routes with an X-API-Key header.
When API_SECRET_KEY is empty, auth is disabled (dev mode).
"""

from fastapi import Request, HTTPException, Security, Depends
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

from config import API_SECRET_KEY
from utils.database import get_db
from models.user import User

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Security(api_key_header), db: Session = Depends(get_db)) -> User:
    """
    Dependency that checks X-API-Key header.
    Skips validation when API_SECRET_KEY is not set (dev mode).
    Returns the current User object.
    """
    if API_SECRET_KEY:
        if not api_key or api_key != API_SECRET_KEY:
            raise HTTPException(
                status_code=401,
                detail="Invalid or missing API key",
                headers={"WWW-Authenticate": "ApiKey"},
            )

    # Return the first user (or create a default one if DB is empty)
    user = db.query(User).first()
    if not user:
        user = User(username="default", email="default@brain.local")
        db.add(user)
        db.commit()
        db.refresh(user)

    return user
