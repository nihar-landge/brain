"""
Personal AI Memory & Prediction System - FastAPI Application
Main entry point for the backend server.
"""

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware

from config import APP_TITLE, APP_VERSION, APP_DESCRIPTION, CORS_ORIGINS
from utils.database import create_tables
from utils.logger import log

# Import API routers
from api.journal import router as journal_router
from api.chat import router as chat_router
from api.predictions import router as predictions_router
from api.analytics import router as analytics_router
from api.goals import router as goals_router
from api.habits import router as habits_router
from api.search import router as search_router
from utils.auth import verify_api_key
from api.data_management import router as data_router
from api.social_graph import router as social_graph_router
from api.context_switching import router as context_router
from api.multi_agent import router as multi_agent_router
from api.causal_inference import router as causal_router
from api.dopamine import router as dopamine_router
from api.tasks import router as tasks_router
from api.calendar import (
    router as calendar_router,
    public_router as calendar_public_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    # Startup
    log.info(f"🚀 Starting {APP_TITLE} v{APP_VERSION}")

    # Initialize database tables
    create_tables()
    log.info("✅ Database initialized")

    # Create data directories
    import os

    os.makedirs("./data/chromadb", exist_ok=True)
    os.makedirs("./data/models", exist_ok=True)
    os.makedirs("./data/backups", exist_ok=True)
    os.makedirs("./ml/models", exist_ok=True)
    os.makedirs("./logs", exist_ok=True)
    log.info("✅ Data directories ready")

    log.info("🎉 System ready!")

    yield

    # Shutdown
    log.info("👋 Shutting down...")


# Create FastAPI app
app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    description=APP_DESCRIPTION,
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all API requests with timing."""
    start = time.time()
    response = await call_next(request)
    duration = round((time.time() - start) * 1000, 1)

    if not request.url.path.startswith("/api/health"):
        log.info(
            f"{request.method} {request.url.path} → {response.status_code} ({duration}ms)"
        )

    return response


from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch all unhandled exceptions and return a consistent JSON response."""
    log.error(f"Unhandled exception at {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred.",
            "path": request.url.path,
        },
    )



# Auth dependency applied to all protected routers
auth_dep = [Depends(verify_api_key)]

# Register API routers (all protected)
app.include_router(
    journal_router, prefix="/api/journal", tags=["Journal"], dependencies=auth_dep
)
app.include_router(
    chat_router, prefix="/api/chat", tags=["Chat"], dependencies=auth_dep
)
app.include_router(
    predictions_router,
    prefix="/api/predict",
    tags=["Predictions"],
    dependencies=auth_dep,
)
app.include_router(
    analytics_router, prefix="/api/analytics", tags=["Analytics"], dependencies=auth_dep
)
app.include_router(
    goals_router, prefix="/api/goals", tags=["Goals"], dependencies=auth_dep
)
app.include_router(
    habits_router, prefix="/api/habits", tags=["Habits"], dependencies=auth_dep
)
app.include_router(
    search_router, prefix="/api/search", tags=["Search"], dependencies=auth_dep
)
app.include_router(
    data_router, prefix="/api/data", tags=["Data Management"], dependencies=auth_dep
)
app.include_router(
    social_graph_router,
    prefix="/api/social",
    tags=["Social Graph"],
    dependencies=auth_dep,
)
app.include_router(
    context_router,
    prefix="/api/context",
    tags=["Context Switching"],
    dependencies=auth_dep,
)
app.include_router(
    multi_agent_router,
    prefix="/api/agents",
    tags=["Multi-Agent"],
    dependencies=auth_dep,
)
app.include_router(
    causal_router,
    prefix="/api/causal",
    tags=["Causal Inference"],
    dependencies=auth_dep,
)
app.include_router(
    dopamine_router,
    prefix="/api/dopamine",
    tags=["Dopamine Menu"],
    dependencies=auth_dep,
)
app.include_router(
    tasks_router,
    prefix="/api/tasks",
    tags=["Tasks"],
    dependencies=auth_dep,
)
app.include_router(
    calendar_router,
    prefix="/api/calendar",
    tags=["Calendar"],
    dependencies=auth_dep,
)
app.include_router(
    calendar_public_router,
    prefix="/api/calendar",
    tags=["Calendar Public"],
)


# ======================== SYSTEM ENDPOINTS ========================


@app.get("/api/health")
async def health_check():
    """System health check."""
    return {
        "status": "healthy",
        "version": APP_VERSION,
        "service": APP_TITLE,
    }


@app.get("/api/stats", dependencies=auth_dep)
async def get_stats():
    """Get system statistics."""
    import os
    from utils.database import get_db
    from models.journal import JournalEntry
    from models.habits import Habit, HabitLog
    from models.goals import Goal
    from models.user import ChatHistory

    db = next(get_db())
    try:
        db_path = "./data/database.db"
        db_size = (
            round(os.path.getsize(db_path) / 1024, 1) if os.path.exists(db_path) else 0
        )

        return {
            "total_journal_entries": db.query(JournalEntry).count(),
            "total_habits": db.query(Habit).count(),
            "total_habit_logs": db.query(HabitLog).count(),
            "total_goals": db.query(Goal).count(),
            "total_chat_messages": db.query(ChatHistory).count(),
            "database_size_kb": db_size,
            "embedding_model": "gemini-embedding-001",
            "llm_model": "gemini-2.0-flash",
            "version": APP_VERSION,
        }
    finally:
        db.close()
