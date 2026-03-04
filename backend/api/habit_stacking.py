from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from utils.database import get_db
from models.user import User
from utils.auth import verify_api_key
from ml.habit_stacker import habit_stacker

router = APIRouter()

@router.get("/stacking-suggestions")
async def get_habit_stacking_suggestions(
    user: User = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """
    Analyze active habits and completion logs to suggest natural pairings
    or 'anchor stacking' (piggybacking a weak habit onto a strong one).
    """
    result = habit_stacker.get_stacking_suggestions(db, user.id)
    return result
