"""
Journal API Endpoints.
CRUD operations for journal entries with data consistency (Fix #3).
"""

from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from utils.database import get_db
from models.user import User
from utils.auth import verify_api_key
from models.journal import JournalEntry
from services.data_manager import DataManager

router = APIRouter()


# ======================== SCHEMAS ========================


class JournalEntryCreate(BaseModel):
    content: str = Field(..., min_length=1)
    title: Optional[str] = None
    mood: Optional[int] = Field(None, ge=1, le=10)
    energy_level: Optional[int] = Field(None, ge=1, le=10)
    stress_level: Optional[int] = Field(None, ge=1, le=10)
    tags: Optional[List[str]] = None
    category: Optional[str] = None


class JournalEntryUpdate(BaseModel):
    content: Optional[str] = None
    title: Optional[str] = None
    mood: Optional[int] = Field(None, ge=1, le=10)
    energy_level: Optional[int] = Field(None, ge=1, le=10)
    stress_level: Optional[int] = Field(None, ge=1, le=10)
    tags: Optional[List[str]] = None
    category: Optional[str] = None


class JournalEntryResponse(BaseModel):
    id: int
    content: str
    title: Optional[str]
    mood: Optional[int]
    energy_level: Optional[int]
    stress_level: Optional[int]
    tags: Optional[list]
    category: Optional[str]
    entry_date: str
    created_at: str

    class Config:
        from_attributes = True


# ======================== ENDPOINTS ========================


@router.post("", response_model=dict)
async def create_journal_entry(entry: JournalEntryCreate, user: User = Depends(verify_api_key), db: Session = Depends(get_db)):
    """Create a new journal entry with full data consistency."""
    data_mgr = DataManager(db)
    new_entry = data_mgr.create_journal_entry(
        user_id=user.id,  # Default user
        content=entry.content,
        mood=entry.mood,
        energy_level=entry.energy_level,
        stress_level=entry.stress_level,
        title=entry.title,
        tags=entry.tags,
        category=entry.category,
    )
    return {"id": new_entry.id, "status": "success", "message": "Journal entry created"}


@router.get("", response_model=List[dict])
async def get_journal_entries(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 50,
    user: User = Depends(verify_api_key), db: Session = Depends(get_db),
):
    """Get journal entries with optional date filtering."""
    query = db.query(JournalEntry).filter(JournalEntry.user_id == 1)

    if start_date:
        query = query.filter(JournalEntry.entry_date >= start_date)
    if end_date:
        query = query.filter(JournalEntry.entry_date <= end_date)

    entries = query.order_by(JournalEntry.entry_date.desc()).limit(limit).all()

    return [
        {
            "id": e.id,
            "content": e.content,
            "title": e.title,
            "mood": e.mood,
            "energy_level": e.energy_level,
            "stress_level": e.stress_level,
            "tags": e.tags,
            "category": e.category,
            "entry_date": str(e.entry_date),
            "created_at": str(e.created_at),
        }
        for e in entries
    ]


@router.get("/{entry_id}", response_model=dict)
async def get_journal_entry(entry_id: int, user: User = Depends(verify_api_key), db: Session = Depends(get_db)):
    """Get specific journal entry."""
    entry = db.query(JournalEntry).get(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    return {
        "id": entry.id,
        "content": entry.content,
        "title": entry.title,
        "mood": entry.mood,
        "energy_level": entry.energy_level,
        "stress_level": entry.stress_level,
        "tags": entry.tags,
        "category": entry.category,
        "entry_date": str(entry.entry_date),
        "created_at": str(entry.created_at),
    }


@router.put("/{entry_id}", response_model=dict)
async def update_journal_entry(
    entry_id: int, entry: JournalEntryUpdate, user: User = Depends(verify_api_key), db: Session = Depends(get_db)
):
    """Update existing journal entry with data consistency."""
    data_mgr = DataManager(db)
    updates = entry.model_dump(exclude_unset=True)
    updated = data_mgr.update_journal_entry(entry_id, **updates)

    if not updated:
        raise HTTPException(status_code=404, detail="Entry not found")

    return {"status": "success", "message": "Entry updated"}


@router.delete("/{entry_id}", response_model=dict)
async def delete_journal_entry(entry_id: int, user: User = Depends(verify_api_key), db: Session = Depends(get_db)):
    """Delete journal entry with cascade to all stores."""
    data_mgr = DataManager(db)
    deleted = data_mgr.delete_journal_entry(entry_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Entry not found")

    return {"status": "success", "message": "Entry deleted"}


@router.post("/search", response_model=List[dict])
async def search_entries(
    query: str,
    limit: int = 10,
    mood_min: Optional[int] = None,
    user: User = Depends(verify_api_key), db: Session = Depends(get_db),
):
    """Semantic search across journal entries using gemini-embedding-001."""
    data_mgr = DataManager(db)
    results = data_mgr.search_similar(query, n_results=limit, mood_min=mood_min)

    return [
        {
            "id": r["entry"].id,
            "content": r["entry"].content,
            "title": r["entry"].title,
            "mood": r["entry"].mood,
            "entry_date": str(r["entry"].entry_date),
            "distance": r.get("distance"),
        }
        for r in results
    ]
