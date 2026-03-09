"""שירות זיכרון — שמירה ושליפה של רשומות זיכרון."""

import json
import logging
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.memory import MemoryEntry, Analysis

logger = logging.getLogger(__name__)


def save_analysis_to_memory(
    db: Session,
    analysis_id: int,
    collage_start_ts: datetime,
    collage_end_ts: datetime,
    summary_text: str,
    detected_entities: list = None,
    people_count: int = 0,
    vehicle_count: int = 0,
    critical_matches: list = None,
) -> MemoryEntry:
    """שמירת תוצאת ניתוח כרשומת זיכרון."""
    entry = MemoryEntry(
        source_type="collage_analysis",
        source_id=analysis_id,
        timestamp_start=collage_start_ts,
        timestamp_end=collage_end_ts,
        text_summary=summary_text,
        objects_json=json.dumps(detected_entities or [], ensure_ascii=False),
        people_count=people_count,
        vehicle_count=vehicle_count,
        critical_matches_json=json.dumps(critical_matches or [], ensure_ascii=False),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    logger.info(f"נשמרה רשומת זיכרון #{entry.id}")
    return entry


def retrieve_memory(
    db: Session,
    from_ts: Optional[datetime] = None,
    to_ts: Optional[datetime] = None,
    query: Optional[str] = None,
    objects_filter: Optional[str] = None,
    limit: int = 20,
) -> List[MemoryEntry]:
    """שליפת רשומות זיכרון לפי פילטרים."""
    q = db.query(MemoryEntry).order_by(MemoryEntry.timestamp_start.desc())

    if from_ts:
        q = q.filter(MemoryEntry.timestamp_start >= from_ts)
    if to_ts:
        q = q.filter(MemoryEntry.timestamp_end <= to_ts)
    if query:
        q = q.filter(MemoryEntry.text_summary.contains(query))
    if objects_filter:
        q = q.filter(MemoryEntry.objects_json.contains(objects_filter))

    return q.limit(limit).all()


def get_recent_context(db: Session, count: int = 5) -> str:
    """קבלת הקשר אחרון מהזיכרון — לשימוש בצ'אט."""
    entries = (
        db.query(MemoryEntry)
        .order_by(MemoryEntry.timestamp_start.desc())
        .limit(count)
        .all()
    )
    if not entries:
        return "אין רשומות זיכרון עדיין"

    lines = []
    for e in reversed(entries):
        ts = e.timestamp_start.strftime("%H:%M:%S")
        lines.append(f"[{ts}] {e.text_summary}")
    return "\n".join(lines)
