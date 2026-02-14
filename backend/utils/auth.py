"""
Simple API Key Authentication.
Protects all API routes with an X-API-Key header.
When API_SECRET_KEY is empty, auth is disabled (dev mode).
"""

from fastapi import Request, HTTPException, Security
from fastapi.security import APIKeyHeader

from config import API_SECRET_KEY

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Security(api_key_header)):
    """
    Dependency that checks X-API-Key header.
    Skips validation when API_SECRET_KEY is not set (dev mode).
    """
    # If no key configured, skip auth (dev mode)
    if not API_SECRET_KEY:
        return None

    if not api_key or api_key != API_SECRET_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    return api_key
