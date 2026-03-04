from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel

from utils.database import get_db
from models.user import User
from utils.auth import verify_api_key
from services.location_service import location_service
from models.location import LocationLog

router = APIRouter()

class LocationCreate(BaseModel):
    latitude: float
    longitude: float
    place_name: str = None
    place_category: str = None
    source: str = "gps"

@router.post("/log")
async def log_current_location(
    data: LocationCreate,
    user: User = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    if data.place_name:
        # Save explicitly named location
        log = LocationLog(
            user_id=user.id,
            latitude=data.latitude,
            longitude=data.longitude,
            place_name=data.place_name,
            place_category=data.place_category,
            source=data.source
        )
        db.add(log)
        db.commit()
        db.refresh(log)
    else:
        # Auto-resolve using service logic
        log = location_service.log_location(db, user.id, data.latitude, data.longitude, data.source)
        
    return {"status": "success", "id": log.id, "place_name": log.place_name}

@router.get("/timeline")
async def get_location_timeline(
    days: int = 7,
    user: User = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    start_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    logs = db.query(LocationLog).filter(
        LocationLog.user_id == user.id,
        LocationLog.timestamp >= start_date
    ).order_by(LocationLog.timestamp.desc()).all()
    
    return [
        {
            "id": l.id,
            "latitude": l.latitude,
            "longitude": l.longitude,
            "place_name": l.place_name,
            "category": l.place_category,
            "timestamp": str(l.timestamp),
            "source": l.source
        }
        for l in logs
    ]

@router.get("/patterns")
async def get_location_patterns(
    user: User = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    return location_service.get_location_patterns(db, user.id)
