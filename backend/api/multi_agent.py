"""
Multi-Agent Chat API Endpoints.
Routes for single-agent and multi-agent chat, plus agent listing.
"""

from typing import Optional, List

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from utils.database import get_db
from models.user import ChatHistory, User
from utils.auth import verify_api_key
from services.multi_agent_service import multi_agent_service

router = APIRouter()


# ======================== SCHEMAS ========================


class AgentChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    agent: str = "therapist"  # therapist, coach, analyst


class MultiAgentChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    agents: Optional[List[str]] = None  # None = all agents


# ======================== ENDPOINTS ========================


@router.get("/agents", response_model=list)
async def list_agents():
    """List available AI agents and their descriptions."""
    return multi_agent_service.get_available_agents()


@router.post("/chat", response_model=dict)
async def single_agent_chat(data: AgentChatRequest, user: User = Depends(verify_api_key), db: Session = Depends(get_db)):
    """
    Chat with a single specialized agent.
    Choose from: therapist, coach, analyst.
    """
    result = multi_agent_service.chat_single_agent(
        db,
        user_query=data.message,
        agent_name=data.agent,
        user_id=user.id,
    )

    # Save to chat history
    user_msg = ChatHistory(
        user_id=user.id,
        role="user",
        message=data.message,
        model_used=f"gemini-2.0-flash ({data.agent})",
    )
    db.add(user_msg)

    assistant_msg = ChatHistory(
        user_id=user.id,
        role="assistant",
        message=f"[{data.agent.upper()}] {result.response}",
        model_used=f"gemini-2.0-flash ({data.agent})",
    )
    db.add(assistant_msg)
    db.commit()

    return result.to_dict()


@router.post("/multi-chat", response_model=dict)
async def multi_agent_chat(data: MultiAgentChatRequest, user: User = Depends(verify_api_key), db: Session = Depends(get_db)):
    """
    Chat with all agents simultaneously and get a synthesized response.
    Returns individual agent perspectives + unified synthesis.
    """
    result = multi_agent_service.chat_multi_agent(
        db,
        user_query=data.message,
        user_id=user.id,
        agents=data.agents,
    )

    # Save synthesized response to chat history
    user_msg = ChatHistory(
        user_id=user.id,
        role="user",
        message=data.message,
        model_used="gemini-2.0-flash (multi-agent)",
    )
    db.add(user_msg)

    assistant_msg = ChatHistory(
        user_id=user.id,
        role="assistant",
        message=f"[SYNTHESIS] {result['synthesis']}",
        model_used="gemini-2.0-flash (multi-agent)",
    )
    db.add(assistant_msg)
    db.commit()

    return result
