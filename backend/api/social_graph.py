"""
Social Graph API Endpoints.
People management, interaction tracking, social battery, and graph analysis.
"""

from typing import Optional, List
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from utils.database import get_db
from models.user import User
from utils.auth import verify_api_key
from models.social import Person, SocialInteraction, SocialBatteryLog
from services.social_graph_service import social_graph_service

router = APIRouter()


# ======================== SCHEMAS ========================


class PersonCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    relationship_type: Optional[str] = None
    tags: Optional[list] = None


class PersonUpdate(BaseModel):
    name: Optional[str] = None
    relationship_type: Optional[str] = None
    tags: Optional[list] = None
    is_active: Optional[bool] = None


class InteractionCreate(BaseModel):
    person_id: int
    interaction_date: str  # YYYY-MM-DD
    interaction_type: Optional[str] = None
    duration_minutes: Optional[int] = None
    mood_before: Optional[int] = Field(None, ge=1, le=10)
    mood_after: Optional[int] = Field(None, ge=1, le=10)
    energy_before: Optional[int] = Field(None, ge=1, le=10)
    energy_after: Optional[int] = Field(None, ge=1, le=10)
    quality_rating: Optional[int] = Field(None, ge=1, le=10)
    draining_vs_energizing: Optional[int] = Field(None, ge=-5, le=5)
    notes: Optional[str] = None


class SocialBatteryCreate(BaseModel):
    battery_level: int = Field(..., ge=1, le=10)
    solo_time_minutes: int = 0
    social_time_minutes: int = 0


class ProcessEntryRequest(BaseModel):
    entry_id: int


# ======================== PEOPLE ENDPOINTS ========================


@router.get("/people", response_model=list)
async def list_people(active_only: bool = True, user: User = Depends(verify_api_key), db: Session = Depends(get_db)):
    """List all tracked people."""
    query = db.query(Person).filter(Person.user_id == 1)
    if active_only:
        query = query.filter(Person.is_active == True)
    people = query.order_by(Person.total_mentions.desc()).all()

    return [
        {
            "id": p.id,
            "name": p.name,
            "relationship_type": p.relationship_type,
            "total_mentions": p.total_mentions or 0,
            "avg_mood_impact": p.avg_mood_impact,
            "energy_impact": p.energy_impact,
            "interaction_frequency": p.interaction_frequency,
            "tags": p.tags or [],
            "is_active": p.is_active,
            "first_mentioned_date": str(p.first_mentioned_date)
            if p.first_mentioned_date
            else None,
        }
        for p in people
    ]


@router.post("/people", response_model=dict)
async def create_person(data: PersonCreate, user: User = Depends(verify_api_key), db: Session = Depends(get_db)):
    """Manually add a person to the social graph."""
    from datetime import datetime

    person = Person(
        user_id=user.id,
        name=data.name,
        relationship_type=data.relationship_type,
        tags=data.tags,
        first_mentioned_date=datetime.now().date(),
        total_mentions=0,
    )
    db.add(person)
    db.commit()
    db.refresh(person)
    return {"id": person.id, "name": person.name, "status": "created"}


@router.put("/people/{person_id}", response_model=dict)
async def update_person(
    person_id: int, data: PersonUpdate, user: User = Depends(verify_api_key), db: Session = Depends(get_db)
):
    """Update a person's details."""
    person = (
        db.query(Person).filter(Person.id == person_id, Person.user_id == 1).first()
    )
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")

    if data.name is not None:
        person.name = data.name
    if data.relationship_type is not None:
        person.relationship_type = data.relationship_type
    if data.tags is not None:
        person.tags = data.tags
    if data.is_active is not None:
        person.is_active = data.is_active

    db.commit()
    return {"id": person.id, "status": "updated"}


@router.delete("/people/{person_id}", response_model=dict)
async def delete_person(person_id: int, user: User = Depends(verify_api_key), db: Session = Depends(get_db)):
    """Deactivate a person (soft delete)."""
    person = (
        db.query(Person).filter(Person.id == person_id, Person.user_id == 1).first()
    )
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")

    person.is_active = False
    db.commit()
    return {"id": person_id, "status": "deactivated"}


# ======================== INTERACTION ENDPOINTS ========================


@router.post("/interactions", response_model=dict)
async def create_interaction(data: InteractionCreate, user: User = Depends(verify_api_key), db: Session = Depends(get_db)):
    """Log a social interaction."""
    from datetime import datetime

    person = (
        db.query(Person)
        .filter(Person.id == data.person_id, Person.user_id == 1)
        .first()
    )
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")

    interaction = SocialInteraction(
        user_id=user.id,
        person_id=data.person_id,
        interaction_date=datetime.strptime(data.interaction_date, "%Y-%m-%d").date(),
        interaction_type=data.interaction_type,
        duration_minutes=data.duration_minutes,
        mood_before=data.mood_before,
        mood_after=data.mood_after,
        energy_before=data.energy_before,
        energy_after=data.energy_after,
        quality_rating=data.quality_rating,
        draining_vs_energizing=data.draining_vs_energizing,
        notes=data.notes,
    )
    db.add(interaction)

    # Update person mention count
    person.total_mentions = (person.total_mentions or 0) + 1

    db.commit()
    db.refresh(interaction)

    # Refresh person metrics
    social_graph_service.refresh_person_metrics(db, data.person_id)

    return {"id": interaction.id, "status": "created"}


@router.get("/interactions", response_model=list)
async def list_interactions(
    person_id: Optional[int] = None,
    limit: int = 50,
    user: User = Depends(verify_api_key), db: Session = Depends(get_db),
):
    """List social interactions, optionally filtered by person."""
    query = db.query(SocialInteraction).filter(SocialInteraction.user_id == 1)
    if person_id:
        query = query.filter(SocialInteraction.person_id == person_id)

    interactions = (
        query.order_by(SocialInteraction.interaction_date.desc()).limit(limit).all()
    )

    return [
        {
            "id": i.id,
            "person_id": i.person_id,
            "interaction_date": str(i.interaction_date),
            "interaction_type": i.interaction_type,
            "duration_minutes": i.duration_minutes,
            "mood_before": i.mood_before,
            "mood_after": i.mood_after,
            "energy_before": i.energy_before,
            "energy_after": i.energy_after,
            "quality_rating": i.quality_rating,
            "draining_vs_energizing": i.draining_vs_energizing,
            "notes": i.notes,
        }
        for i in interactions
    ]


# ======================== GRAPH & ANALYSIS ========================


@router.get("/graph", response_model=dict)
async def get_social_graph(user: User = Depends(verify_api_key), db: Session = Depends(get_db)):
    """Get the full social graph data for visualization."""
    return social_graph_service.get_social_graph(db, user_id=user.id)


@router.get("/analysis", response_model=dict)
async def get_network_analysis(user: User = Depends(verify_api_key), db: Session = Depends(get_db)):
    """Get NetworkX-based network analysis metrics."""
    return social_graph_service.get_network_analysis(db, user_id=user.id)


@router.get("/toxic-patterns", response_model=list)
async def get_toxic_patterns(user: User = Depends(verify_api_key), db: Session = Depends(get_db)):
    """Detect potentially toxic or draining relationship patterns."""
    return social_graph_service.detect_toxic_patterns(db, user_id=user.id)


# ======================== SOCIAL BATTERY ========================


@router.post("/battery", response_model=dict)
async def log_battery(data: SocialBatteryCreate, user: User = Depends(verify_api_key), db: Session = Depends(get_db)):
    """Log current social battery level."""
    log_entry = social_graph_service.log_social_battery(
        db,
        user_id=user.id,
        battery_level=data.battery_level,
        solo_minutes=data.solo_time_minutes,
        social_minutes=data.social_time_minutes,
    )
    return {
        "id": log_entry.id,
        "battery_level": log_entry.battery_level,
        "date": str(log_entry.log_date),
    }


@router.get("/battery/history", response_model=list)
async def get_battery_history(days: int = 30, user: User = Depends(verify_api_key), db: Session = Depends(get_db)):
    """Get social battery history."""
    return social_graph_service.get_social_battery_history(db, user_id=user.id, days=days)


# ======================== AUTO-EXTRACTION ========================


@router.post("/process-entry", response_model=dict)
async def process_journal_entry(
    data: ProcessEntryRequest, user: User = Depends(verify_api_key), db: Session = Depends(get_db)
):
    """Process a journal entry to extract people and interactions via Gemini NER."""
    social_graph_service.process_journal_entry(db, entry_id=data.entry_id, user_id=user.id)
    return {"status": "processed", "entry_id": data.entry_id}
