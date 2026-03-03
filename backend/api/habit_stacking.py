from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from utils.database import get_db
from models.user import User
from utils.auth_jwt import get_current_user
from ml.habit_stacker import habit_stacker

router = APIRouter()

@router.get("/stacking-suggestions")
async def get_habit_stacking_suggestions(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Analyze active habits and completion logs to suggest natural pairings
    or 'anchor stacking' (piggybacking a weak habit onto a strong one).
    """
    result = habit_stacker.get_stacking_suggestions(db, user.id)
    return result
