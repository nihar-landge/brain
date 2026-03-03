from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import List

from utils.database import get_db
from models.user import User
from utils.auth_jwt import get_current_user
from models.anomalies import AnomalyAlert
from ml.anomaly_detector import anomaly_detector

router = APIRouter()

@router.get("")
async def get_active_anomalies(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all unacknowledged anomaly alerts.
    Also triggers a background detection run to ensure alerts are up-to-date.
    """
    # In a real system, this runs via cron job at midnight
    # For now, evaluate on-demand
    anomaly_detector.detect_anomalies(db, user.id)
    
    alerts = db.query(AnomalyAlert).filter(
        AnomalyAlert.user_id == user.id,
        AnomalyAlert.is_acknowledged == False,
        AnomalyAlert.is_false_positive == False
    ).order_by(AnomalyAlert.detected_at.desc()).all()
    
    return [_format_alert(a) for a in alerts]

@router.post("/{alert_id}/acknowledge")
async def acknowledge_anomaly(
    alert_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    alert = db.query(AnomalyAlert).filter(
        AnomalyAlert.id == alert_id,
        AnomalyAlert.user_id == user.id
    ).first()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Anomaly alert not found")
        
    alert.is_acknowledged = True
    db.commit()
    return {"status": "success", "message": "Alert acknowledged"}

@router.post("/{alert_id}/false-positive")
async def mark_false_positive(
    alert_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    alert = db.query(AnomalyAlert).filter(
        AnomalyAlert.id == alert_id,
        AnomalyAlert.user_id == user.id
    ).first()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Anomaly alert not found")
        
    alert.is_false_positive = True
    alert.is_acknowledged = True
    db.commit()
    return {"status": "success", "message": "Alert marked as false positive"}

@router.get("/history")
async def get_anomaly_history(
    limit: int = 10,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    alerts = db.query(AnomalyAlert).filter(
        AnomalyAlert.user_id == user.id
    ).order_by(AnomalyAlert.detected_at.desc()).limit(limit).all()
    
    return [_format_alert(a) for a in alerts]

def _format_alert(a: AnomalyAlert) -> dict:
    return {
        "id": a.id,
        "type": a.anomaly_type,
        "severity": a.severity,
        "title": a.title,
        "description": a.description,
        "metric_name": a.metric_name,
        "baseline_value": a.baseline_value,
        "current_value": a.current_value,
        "suggested_action": a.suggested_action or {},
        "is_acknowledged": a.is_acknowledged,
        "detected_at": str(a.detected_at)
    }
