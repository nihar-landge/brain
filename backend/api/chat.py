"""
Chat API Endpoints.
Conversational AI interface using Gemini + RAG + Memory.
"""

from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from utils.database import get_db
from models.user import User
from models.user import ChatHistory
from services.gemini_service import gemini_service
from services.smart_memory import SmartMemoryManager
from utils.prompts import CHAT_SYSTEM_PROMPT

router = APIRouter()


# ======================== SCHEMAS ========================


class ChatMessage(BaseModel):
    message: str = Field(..., min_length=1)


class ChatResponse(BaseModel):
    response: str
    sources: Optional[list] = None
    confidence: Optional[float] = None


# ======================== ENDPOINTS ========================


@router.post("", response_model=dict)
async def chat(msg: ChatMessage, user: User = Depends(verify_api_key), db: Session = Depends(get_db)):
    """
    Send message to AI assistant.
    Uses tiered memory search (Fix #4) and Gemini for responses.
    """
    # 1. Search for relevant context using Smart Memory (Fix #4)
    memory_mgr = SmartMemoryManager(db)
    search_results = memory_mgr.smart_search_with_fallback(msg.message, user_id=user.id)

    # 2. Build context from all tiers
    context_parts = []

    if search_results["core"]:
        context_parts.append("=== Core Memory ===\n" + "\n".join(search_results["core"]))

    if search_results["archival"]:
        context_parts.append(
            "=== Relevant Past Entries ===\n" + "\n---\n".join(search_results["archival"][:3])
        )

    if search_results["sql_fallback"]:
        context_parts.append(
            "=== Additional Context ===\n" + "\n---\n".join(search_results["sql_fallback"][:2])
        )

    context = "\n\n".join(context_parts) if context_parts else "No previous context found."

    # 3. Generate response using Gemini
    system_prompt = CHAT_SYSTEM_PROMPT

    response = gemini_service.generate_stream(
        user_query=msg.message,
        context=context,
        system_prompt=system_prompt,
    )

    async def event_generator():
        full_response = ""
        for chunk in response:
            full_response += chunk
            yield chunk

        # Save to chat history after streaming completes
        user_msg = ChatHistory(
            user_id=user.id,
            role="user",
            message=msg.message,
            model_used="gemini-2.0-flash",
        )
        db.add(user_msg)

        assistant_msg = ChatHistory(
            user_id=user.id,
            role="assistant",
            message=full_response,
            sources=search_results.get("archival", [])[:3],
            model_used="gemini-2.0-flash",
        )
        db.add(assistant_msg)
        db.commit()

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/history", response_model=List[dict])
async def get_chat_history(limit: int = 20, user: User = Depends(verify_api_key), db: Session = Depends(get_db)):
    """Get recent chat history."""
    messages = (
        db.query(ChatHistory)
        .filter(ChatHistory.user_id == 1)
        .order_by(ChatHistory.created_at.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "id": m.id,
            "role": m.role,
            "message": m.message,
            "created_at": str(m.created_at),
        }
        for m in reversed(messages)
    ]


@router.delete("/clear", response_model=dict)
async def clear_chat_history(user: User = Depends(verify_api_key), db: Session = Depends(get_db)):
    """Clear all chat history for the user."""
    deleted = db.query(ChatHistory).filter(ChatHistory.user_id == 1).delete()
    db.commit()
    return {"status": "success", "message": f"Cleared {deleted} messages"}
