"""
Location Service.
Handles importing timeline data and mapping coordinates to known places/contexts.
"""

from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func

from models.location import LocationLog
from models.user import User

class LocationService:
    def __init__(self):
        # Could integrate with actual Google Maps Geocoding API here
        pass

    def log_location(self, db: Session, user_id: int, lat: float, lng: float, source: str = "gps") -> LocationLog:
        """Create a new location log, optionally attempting to resolve the place name."""
        # Simple clustering: if within a tiny radius of last known named place, use that name
        last_named = db.query(LocationLog).filter(
            LocationLog.user_id == user_id,
            LocationLog.place_name != None
        ).order_by(LocationLog.timestamp.desc()).first()

        place_name = None
        category = None
        
        if last_named:
            # Very rough distance check (not accurate for real geo, but works for mock clustering)
            diff = abs(last_named.latitude - lat) + abs(last_named.longitude - lng)
            if diff < 0.001: # Roughly 100 meters
                place_name = last_named.place_name
                category = last_named.place_category

        log = LocationLog(
            user_id=user_id,
            latitude=lat,
            longitude=lng,
            place_name=place_name,
            place_category=category,
            source=source
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    def get_location_patterns(self, db: Session, user_id: int) -> dict:
        """Analyze where the user spends their time."""
        logs = db.query(LocationLog).filter(
            LocationLog.user_id == user_id,
            LocationLog.place_name != None
        ).all()
        
        if not logs:
            return {"status": "insufficient_data"}
            
        from collections import defaultdict
        visits = defaultdict(int)
        
        for l in logs:
            visits[l.place_name] += 1
            
        top_places = sorted(visits.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "status": "success",
            "top_places": [{"place": p, "visits": c} for p, c in top_places],
            "total_logs": len(logs)
        }

location_service = LocationService()
