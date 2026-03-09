"""API routes — היסטוריה וזיכרון."""

from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.memory import MemoryEntry

router = APIRouter(prefix="/history", tags=["history"])


class MemoryEntryResponse(BaseModel):
    id: int
    source_type: str
    timestamp_start: str
    timestamp_end: str
    text_summary: str
    people_count: int
    vehicle_count: int
    motion_level: Optional[str] = None
    created_at: str


@router.get("/memory", response_model=List[MemoryEntryResponse])
def get_memory(
    from_ts: Optional[str] = Query(None, alias="from"),
    to_ts: Optional[str] = Query(None, alias="to"),
    query: Optional[str] = None,
    objects: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """שליפת רשומות זיכרון."""
    q = db.query(MemoryEntry).order_by(MemoryEntry.timestamp_start.desc())

    if from_ts:
        try:
            dt = datetime.fromisoformat(from_ts)
            q = q.filter(MemoryEntry.timestamp_start >= dt)
        except ValueError:
            pass

    if to_ts:
        try:
            dt = datetime.fromisoformat(to_ts)
            q = q.filter(MemoryEntry.timestamp_end <= dt)
        except ValueError:
            pass

    if query:
        q = q.filter(MemoryEntry.text_summary.contains(query))

    if objects:
        q = q.filter(MemoryEntry.objects_json.contains(objects))

    entries = q.limit(limit).all()
    return [
        MemoryEntryResponse(
            id=e.id, source_type=e.source_type,
            timestamp_start=e.timestamp_start.isoformat(),
            timestamp_end=e.timestamp_end.isoformat(),
            text_summary=e.text_summary,
            people_count=e.people_count or 0,
            vehicle_count=e.vehicle_count or 0,
            motion_level=e.motion_level,
            created_at=e.created_at.isoformat(),
        )
        for e in entries
    ]


@router.get("/timeline", response_model=List[MemoryEntryResponse])
def get_timeline(
    limit: int = 100,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """תצוגת timeline של אירועים."""
    entries = (
        db.query(MemoryEntry)
        .order_by(MemoryEntry.timestamp_start.asc())
        .limit(limit)
        .all()
    )
    return [
        MemoryEntryResponse(
            id=e.id, source_type=e.source_type,
            timestamp_start=e.timestamp_start.isoformat(),
            timestamp_end=e.timestamp_end.isoformat(),
            text_summary=e.text_summary,
            people_count=e.people_count or 0,
            vehicle_count=e.vehicle_count or 0,
            motion_level=e.motion_level,
            created_at=e.created_at.isoformat(),
        )
        for e in entries
    ]
