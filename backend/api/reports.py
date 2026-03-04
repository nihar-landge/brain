from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone, date
from pydantic import BaseModel

from utils.database import get_db
from models.user import User
from utils.auth import verify_api_key
from services.report_service import report_service
from models.reports import LifeReport

router = APIRouter()

class GenerateReportRequest(BaseModel):
    report_type: str # "weekly", "monthly"
    start_date: str # YYYY-MM-DD
    end_date: str # YYYY-MM-DD

@router.post("/generate")
async def generate_report(
    req: GenerateReportRequest,
    user: User = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Generate or retrieve a LifeReport for the specific period."""
    if req.report_type not in ["weekly", "monthly"]:
        raise HTTPException(status_code=400, detail="Invalid report type")
        
    try:
        start_date = datetime.strptime(req.start_date, "%Y-%m-%d").date()
        end_date = datetime.strptime(req.end_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Dates must be YYYY-MM-DD")
        
    if start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date must be before end_date")
        
    # Check existing first
    existing = db.query(LifeReport).filter(
        LifeReport.user_id == user.id,
        LifeReport.report_type == req.report_type,
        LifeReport.period_start == start_date
    ).first()
    
    if existing:
        return _format_report(existing)
        
    # Generate new
    report = report_service.generate_report(db, user.id, req.report_type, start_date, end_date)
    return _format_report(report)

@router.get("/{report_type}")
async def get_reports(
    report_type: str,
    limit: int = 5,
    user: User = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Get history of generated reports."""
    if report_type not in ["weekly", "monthly"]:
        raise HTTPException(status_code=400, detail="Invalid report type")
        
    reports = db.query(LifeReport).filter(
        LifeReport.user_id == user.id,
        LifeReport.report_type == report_type
    ).order_by(LifeReport.period_start.desc()).limit(limit).all()
    
    return [_format_report(r) for r in reports]

@router.get("/{report_id}/detail")
async def get_report_detail(
    report_id: int,
    user: User = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    report = db.query(LifeReport).filter(
        LifeReport.id == report_id,
        LifeReport.user_id == user.id
    ).first()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
        
    return _format_report(report)

def _format_report(r: LifeReport) -> dict:
    return {
        "id": r.id,
        "type": r.report_type,
        "period": f"{r.period_start} to {r.period_end}",
        "title": r.title,
        "summary": r.summary,
        "achievements": r.achievements or [],
        "challenges": r.challenges or [],
        "mood_trend": r.mood_trend,
        "habit_performance": r.habit_performance or {},
        "recommendations": r.recommendations or [],
        "full_markdown": r.full_markdown,
        "created_at": str(r.created_at)
    }
