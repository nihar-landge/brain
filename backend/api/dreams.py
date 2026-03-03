from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from pydantic import BaseModel

from utils.database import get_db
from models.user import User
from models.journal import JournalEntry
from utils.auth_jwt import get_current_user
from services.dream_service import dream_analyzer

router = APIRouter()

class InterpretRequest(BaseModel):
    content: str

@router.post("/interpret")
async def interpret_dream(
    req: InterpretRequest,
    user: User = Depends(get_current_user)
):
    """
    Analyze raw dream text for symbols and meaning.
    Does not save to DB; meant for real-time preview before saving a JournalEntry.
    """
    if not req.content.strip():
        raise HTTPException(status_code=400, detail="Content cannot be empty")
        
    result = dream_analyzer.analyze_dream(req.content)
    return result

@router.get("/patterns")
async def get_recurring_patterns(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Analyze a user's recent dreams to find overarching narrative or symbol patterns.
    """
    result = dream_analyzer.detect_recurring_patterns(db, user.id)
    return result

@router.get("/history")
async def get_dream_history(
    limit: int = 10,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get past journal entries that contain dreams."""
    entries = db.query(JournalEntry).filter(
        JournalEntry.user_id == user.id,
        JournalEntry.dream_symbols != None
    ).order_by(JournalEntry.entry_date.desc()).limit(limit).all()
    
    dreams = []
    for e in entries:
        dreams.append({
            "id": e.id,
            "date": str(e.entry_date),
            "content_preview": e.content[:100] + "..." if len(e.content) > 100 else e.content,
            "dream_type": e.dream_type,
            "symbols": e.dream_symbols or [],
            "interpretation": e.dream_interpretation
        })
        
    return dreams
