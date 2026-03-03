from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from pydantic import BaseModel

from utils.database import get_db
from models.user import User
from utils.auth_jwt import get_current_user
from services.sentiment_service import sentiment_service

router = APIRouter()

class AnalyzeRequest(BaseModel):
    content: str
    
class AnalyzeResponse(BaseModel):
    sentiment_score: float
    sentiment_label: str
    emotions: list[str]
    topics: list[str]
    cognitive_distortions: list[str]

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_entry_text(
    request: AnalyzeRequest,
    user: User = Depends(get_current_user)
):
    """
    Analyze raw journal text for sentiment and NLP traits.
    Does not save to DB; meant for real-time preview before saving a JournalEntry.
    """
    if not request.content.strip():
        raise HTTPException(status_code=400, detail="Content cannot be empty")
        
    result = sentiment_service.analyze_entry(request.content)
    return result

@router.get("/timeline")
async def get_emotion_timeline(
    days: int = 30,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a timeline of sentiment scores and dominant emotions over the past X days.
    """
    from models.journal import JournalEntry
    from datetime import timedelta, timezone
    
    start_date = datetime.now(timezone.utc).date() - timedelta(days=days)
    
    entries = db.query(JournalEntry).filter(
        JournalEntry.user_id == user.id,
        JournalEntry.entry_date >= start_date,
        JournalEntry.sentiment_score != None
    ).order_by(JournalEntry.entry_date).all()
    
    timeline = []
    for e in entries:
        timeline.append({
            "date": str(e.entry_date),
            "score": e.sentiment_score,
            "label": e.sentiment_label,
            "emotions": e.emotions
        })
        
    return {
        "period_days": days,
        "entry_count": len(timeline),
        "timeline": timeline
    }
