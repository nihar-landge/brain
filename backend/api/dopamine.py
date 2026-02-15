"""
Dopamine Menu API.
CRUD for user-defined dopamine menu items + suggestion/event logging.
Suggestion flow: rules first, then AI re-ranking over user items.
"""

import json
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from utils.database import get_db
from models.dopamine import DopamineItem, DopamineEvent
from config import GEMINI_API_KEY
from services.gemini_service import gemini_service

router = APIRouter()


class DopamineItemCreate(BaseModel):
    category: str = Field(..., pattern="^(starter|main|sides|dessert|specials)$")
    title: str = Field(..., min_length=1, max_length=120)
    description: Optional[str] = None
    duration_min: Optional[int] = Field(None, ge=1, le=120)
    energy_type: Optional[str] = Field(None, pattern="^(mental|physical|relax)$")
    is_active: bool = True


class DopamineItemUpdate(BaseModel):
    category: Optional[str] = Field(
        None, pattern="^(starter|main|sides|dessert|specials)$"
    )
    title: Optional[str] = Field(None, min_length=1, max_length=120)
    description: Optional[str] = None
    duration_min: Optional[int] = Field(None, ge=1, le=120)
    energy_type: Optional[str] = Field(None, pattern="^(mental|physical|relax)$")
    is_active: Optional[bool] = None


class SuggestRequest(BaseModel):
    trigger_type: str = Field(
        ..., pattern="^(pre_start|long_session|exhausted|manual)$"
    )
    session_minutes: Optional[int] = Field(None, ge=0)
    energy_after: Optional[int] = Field(None, ge=1, le=10)
    productivity_rating: Optional[int] = Field(None, ge=1, le=10)
    context_log_id: Optional[int] = None


class EventCreate(BaseModel):
    trigger_type: str = Field(
        ..., pattern="^(pre_start|long_session|exhausted|manual)$"
    )
    dopamine_item_id: Optional[int] = None
    context_log_id: Optional[int] = None
    accepted: bool = False
    completed: bool = False


class EventUpdate(BaseModel):
    accepted: Optional[bool] = None
    completed: Optional[bool] = None


def _seed_default_items(db: Session, user_id: int = 1):
    existing_count = (
        db.query(DopamineItem).filter(DopamineItem.user_id == user_id).count()
    )
    if existing_count > 0:
        return

    defaults = [
        {
            "category": "starter",
            "title": "2-min breathing reset",
            "description": "Stand up, inhale for 4s, exhale for 6s for 2 minutes.",
            "duration_min": 2,
            "energy_type": "relax",
        },
        {
            "category": "main",
            "title": "10-min focused walk",
            "description": "Walk without phone and return with one concrete next action.",
            "duration_min": 10,
            "energy_type": "physical",
        },
        {
            "category": "sides",
            "title": "Tea + stretch",
            "description": "Make tea/coffee and do quick neck-shoulder stretches.",
            "duration_min": 6,
            "energy_type": "relax",
        },
        {
            "category": "dessert",
            "title": "Reward playlist song",
            "description": "Play one favorite track after session completion.",
            "duration_min": 4,
            "energy_type": "mental",
        },
        {
            "category": "specials",
            "title": "Celebration break",
            "description": "Short celebration ritual + write one win in notes.",
            "duration_min": 8,
            "energy_type": "mental",
        },
    ]

    for item in defaults:
        db.add(DopamineItem(user_id=user_id, is_active=True, **item))
    db.commit()


@router.get("/items", response_model=List[dict])
async def get_dopamine_items(active_only: bool = True, db: Session = Depends(get_db)):
    """List user dopamine items (auto-seeded on first use)."""
    _seed_default_items(db, user_id=1)

    query = db.query(DopamineItem).filter(DopamineItem.user_id == 1)
    if active_only:
        query = query.filter(DopamineItem.is_active.is_(True))

    items = query.order_by(DopamineItem.category, DopamineItem.created_at.desc()).all()
    return [
        {
            "id": i.id,
            "category": i.category,
            "title": i.title,
            "description": i.description,
            "duration_min": i.duration_min,
            "energy_type": i.energy_type,
            "is_active": i.is_active,
            "created_at": str(i.created_at),
        }
        for i in items
    ]


@router.post("/items", response_model=dict)
async def create_dopamine_item(data: DopamineItemCreate, db: Session = Depends(get_db)):
    item = DopamineItem(user_id=1, **data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"id": item.id, "status": "success", "message": "Dopamine item created"}


@router.put("/items/{item_id}", response_model=dict)
async def update_dopamine_item(
    item_id: int, updates: DopamineItemUpdate, db: Session = Depends(get_db)
):
    item = (
        db.query(DopamineItem)
        .filter(DopamineItem.id == item_id, DopamineItem.user_id == 1)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Dopamine item not found")

    for key, value in updates.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    item.updated_at = datetime.utcnow()
    db.commit()
    return {"status": "success", "message": "Dopamine item updated"}


@router.delete("/items/{item_id}", response_model=dict)
async def delete_dopamine_item(item_id: int, db: Session = Depends(get_db)):
    item = (
        db.query(DopamineItem)
        .filter(DopamineItem.id == item_id, DopamineItem.user_id == 1)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Dopamine item not found")

    db.delete(item)
    db.commit()
    return {"status": "success", "message": "Dopamine item deleted"}


def _categories_for_trigger(
    trigger_type: str,
    session_minutes: Optional[int],
    energy_after: Optional[int],
    productivity_rating: Optional[int],
) -> list[str]:
    if trigger_type == "pre_start":
        return ["starter", "sides"]

    if trigger_type == "long_session":
        if (session_minutes or 0) >= 90:
            return ["main", "dessert"]
        return ["starter", "main"]

    if trigger_type == "exhausted":
        if energy_after is not None and energy_after <= 4:
            return ["starter", "main"]
        if (session_minutes or 0) >= 90:
            return ["main", "sides"]
        return ["starter"]

    if trigger_type == "manual":
        if productivity_rating is not None and productivity_rating >= 8:
            return ["dessert", "specials"]
        return ["starter", "main", "sides", "dessert", "specials"]

    return ["starter"]


def _ai_rerank_options(
    trigger_type: str,
    session_minutes: Optional[int],
    energy_after: Optional[int],
    productivity_rating: Optional[int],
    options: list[dict],
) -> tuple[list[dict], str, str]:
    """
    AI layer over user-defined options.
    Returns: (ranked_options, selection_mode, reason)
    selection_mode: "ai" | "rules"
    """
    if not GEMINI_API_KEY or len(options) <= 1:
        return options, "rules", "Rule-based selection"

    options_text = "\n".join(
        [
            (
                f"id={o['id']}; category={o['category']}; title={o['title']}; "
                f"duration_min={o.get('duration_min')}; energy_type={o.get('energy_type')}; "
                f"description={o.get('description') or ''}"
            )
            for o in options
        ]
    )

    prompt = (
        "You are a productivity coach. Re-rank these user-created dopamine-break options "
        "to minimize doom-scrolling and maximize fast return-to-focus. "
        "Prefer short, actionable, non-digital breaks when exhausted.\n\n"
        f"Trigger: {trigger_type}\n"
        f"Session minutes: {session_minutes}\n"
        f"Energy after: {energy_after}\n"
        f"Productivity rating: {productivity_rating}\n\n"
        "Options:\n"
        f"{options_text}\n\n"
        "Return strict JSON only:\n"
        '{"ranked_ids": [<ids in best-first order>], "reason": "one short sentence"}'
    )

    try:
        response_text = gemini_service.generate_response(
            user_query=prompt,
            system_prompt="Return only valid JSON. No markdown.",
        )
        parsed = json.loads(response_text.strip())
        ranked_ids = parsed.get("ranked_ids") or []
        reason = parsed.get("reason") or "AI-ranked for focus"

        if not ranked_ids:
            return options, "rules", "Rule-based selection"

        by_id = {o["id"]: o for o in options}
        ranked = [by_id[i] for i in ranked_ids if i in by_id]
        ranked += [o for o in options if o["id"] not in ranked_ids]
        return ranked, "ai", reason
    except Exception:
        return options, "rules", "Rule-based selection"


@router.post("/suggest", response_model=dict)
async def suggest_dopamine_item(data: SuggestRequest, db: Session = Depends(get_db)):
    """Suggest dopamine-menu choices based on trigger and current state."""
    _seed_default_items(db, user_id=1)

    preferred_categories = _categories_for_trigger(
        data.trigger_type,
        data.session_minutes,
        data.energy_after,
        data.productivity_rating,
    )

    items = (
        db.query(DopamineItem)
        .filter(
            DopamineItem.user_id == 1,
            DopamineItem.is_active.is_(True),
            DopamineItem.category.in_(preferred_categories),
        )
        .order_by(DopamineItem.created_at.desc())
        .all()
    )

    if not items:
        fallback = (
            db.query(DopamineItem)
            .filter(DopamineItem.user_id == 1, DopamineItem.is_active.is_(True))
            .order_by(DopamineItem.created_at.desc())
            .all()
        )
        items = fallback

    options = [
        {
            "id": i.id,
            "category": i.category,
            "title": i.title,
            "description": i.description,
            "duration_min": i.duration_min,
            "energy_type": i.energy_type,
        }
        for i in items[:3]
    ]

    ranked_options, selection_mode, reason = _ai_rerank_options(
        trigger_type=data.trigger_type,
        session_minutes=data.session_minutes,
        energy_after=data.energy_after,
        productivity_rating=data.productivity_rating,
        options=options,
    )

    event = DopamineEvent(
        user_id=1,
        trigger_type=data.trigger_type,
        context_log_id=data.context_log_id,
        accepted=False,
        completed=False,
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    return {
        "event_id": event.id,
        "trigger_type": data.trigger_type,
        "suggested_categories": preferred_categories,
        "selection_mode": selection_mode,
        "reason": reason,
        "options": ranked_options,
    }


@router.post("/events", response_model=dict)
async def create_event(data: EventCreate, db: Session = Depends(get_db)):
    event = DopamineEvent(
        user_id=1,
        trigger_type=data.trigger_type,
        context_log_id=data.context_log_id,
        dopamine_item_id=data.dopamine_item_id,
        accepted=data.accepted,
        completed=data.completed,
        acted_at=datetime.utcnow() if (data.accepted or data.completed) else None,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return {"id": event.id, "status": "success"}


@router.put("/events/{event_id}", response_model=dict)
async def update_event(
    event_id: int, updates: EventUpdate, db: Session = Depends(get_db)
):
    event = (
        db.query(DopamineEvent)
        .filter(DopamineEvent.id == event_id, DopamineEvent.user_id == 1)
        .first()
    )
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    update_data = updates.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(event, key, value)

    if update_data.get("accepted") is True or update_data.get("completed") is True:
        event.acted_at = datetime.utcnow()

    db.commit()
    return {"status": "success", "message": "Event updated"}
