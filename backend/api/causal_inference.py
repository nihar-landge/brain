"""
Causal Inference API Endpoints.
Correlations, causal analysis, counterfactuals, and A/B test suggestions.
"""

from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from utils.database import get_db
from services.causal_inference_service import causal_inference_service

router = APIRouter()


# ======================== SCHEMAS ========================


class CausalAnalysisRequest(BaseModel):
    treatment: str = "sleep_hours"  # The variable we're testing as cause
    outcome: str = "mood"  # The outcome variable


# ======================== ENDPOINTS ========================


@router.get("/correlations", response_model=dict)
async def get_correlations(days: int = 90, db: Session = Depends(get_db)):
    """
    Get correlations between all tracked variables and mood.
    Returns sorted correlations with significance indicators.
    """
    return causal_inference_service.get_correlations(db, user_id=1, days=days)


@router.post("/analyze", response_model=dict)
async def run_causal_analysis(
    data: CausalAnalysisRequest, db: Session = Depends(get_db)
):
    """
    Run causal inference analysis for a specific treatment -> outcome pair.
    Uses DoWhy if available, otherwise stratified analysis.
    """
    return causal_inference_service.get_causal_analysis(
        db,
        user_id=1,
        treatment=data.treatment,
        outcome=data.outcome,
    )


@router.get("/counterfactuals", response_model=list)
async def get_counterfactuals(db: Session = Depends(get_db)):
    """
    Generate "what if" counterfactual scenarios based on user data.
    E.g., "If you slept 8 hours instead of 6, mood would be ~7.2 instead of 5.8"
    """
    return causal_inference_service.generate_counterfactuals(db, user_id=1)


@router.get("/experiments", response_model=list)
async def suggest_experiments(db: Session = Depends(get_db)):
    """
    Suggest self-experiments based on significant correlations.
    Each experiment has a hypothesis, protocol, and duration.
    """
    return causal_inference_service.suggest_experiments(db, user_id=1)
