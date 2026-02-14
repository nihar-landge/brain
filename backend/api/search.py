"""
Search API Endpoints.
Semantic search across journal entries using ChromaDB + gemini-embedding-001.
"""

from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from utils.database import get_db
from services.data_manager import DataManager
from services.rag_service import rag_service

router = APIRouter()


# ======================== SCHEMAS ========================


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    limit: int = Field(10, ge=1, le=50)
    mood_min: Optional[int] = Field(None, ge=1, le=10)


class SimilarRequest(BaseModel):
    entry_id: int
    limit: int = Field(5, ge=1, le=20)


# ======================== ENDPOINTS ========================


@router.post("", response_model=dict)
async def semantic_search(req: SearchRequest, db: Session = Depends(get_db)):
    """Semantic search across all journal entries."""
    data_mgr = DataManager(db)
    results = data_mgr.search_similar(req.query, n_results=req.limit, mood_min=req.mood_min)

    return {
        "query": req.query,
        "total_results": len(results),
        "results": [
            {
                "id": r["entry"].id,
                "content": r["entry"].content,
                "title": r["entry"].title,
                "mood": r["entry"].mood,
                "energy_level": r["entry"].energy_level,
                "entry_date": str(r["entry"].entry_date),
                "distance": r.get("distance"),
            }
            for r in results
        ],
    }


@router.post("/similar", response_model=dict)
async def find_similar(req: SimilarRequest, db: Session = Depends(get_db)):
    """Find entries similar to a given journal entry."""
    from models.journal import JournalEntry

    entry = db.query(JournalEntry).get(req.entry_id)
    if not entry:
        return {"error": "Entry not found", "results": []}

    # Use RAG service to find similar documents
    similar = rag_service.find_similar(f"journal_{req.entry_id}", n_results=req.limit)

    # Map back to journal entries
    results = []
    for doc_id, doc, dist in zip(
        similar.get("ids", []),
        similar.get("documents", []),
        similar.get("distances", []),
    ):
        try:
            eid = int(doc_id.replace("journal_", ""))
            e = db.query(JournalEntry).get(eid)
            if e and e.id != req.entry_id:
                results.append({
                    "id": e.id,
                    "content": e.content[:200],
                    "title": e.title,
                    "mood": e.mood,
                    "entry_date": str(e.entry_date),
                    "distance": dist,
                })
        except (ValueError, AttributeError):
            continue

    return {
        "source_entry_id": req.entry_id,
        "total_results": len(results),
        "results": results,
    }
