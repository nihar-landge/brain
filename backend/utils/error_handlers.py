"""
Global exception handlers for FastAPI.
Provides consistent JSON error responses for all exception types.
"""

from fastapi import Request
from fastapi.responses import JSONResponse
from utils.exceptions import BrainException
from utils.logger import log


async def brain_exception_handler(request: Request, exc: BrainException):
    """Handle all BrainException subclasses with structured JSON response."""
    log.error(f"{exc.status_code} | {request.method} {request.url.path} | {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.message,
            "detail": exc.detail,
            "path": str(request.url.path),
        },
    )


async def generic_exception_handler(request: Request, exc: Exception):
    """Catch-all handler for unhandled exceptions."""
    log.error(f"Unhandled: {request.method} {request.url.path} | {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": True, "message": "Internal server error"},
    )
