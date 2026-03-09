"""API routes — משימות ניטור."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.watch_task import WatchTask, WatchTaskEvent

router = APIRouter(prefix="/watch-tasks", tags=["watch-tasks"])


class WatchTaskCreate(BaseModel):
    label: str
    description: str
    days_of_week: str = "0,1,2,3,4,5,6"
    start_time: str = "00:00"
    end_time: str = "23:59"
    cooldown_seconds: int = 60


class WatchTaskUpdate(BaseModel):
    label: Optional[str] = None
    description: Optional[str] = None
    is_enabled: Optional[bool] = None
    days_of_week: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    cooldown_seconds: Optional[int] = None


class WatchTaskResponse(BaseModel):
    id: int
    label: str
    description: str
    is_enabled: bool
    days_of_week: str
    start_time: str
    end_time: str
    cooldown_seconds: int
    total_matches: int
    last_match_at: Optional[str] = None


class WatchTaskEventResponse(BaseModel):
    id: int
    task_id: int
    match_description: str
    confidence: str
    created_at: str


def _task_to_response(t: WatchTask) -> WatchTaskResponse:
    return WatchTaskResponse(
        id=t.id, label=t.label, description=t.description,
        is_enabled=t.is_enabled, days_of_week=t.days_of_week,
        start_time=t.start_time, end_time=t.end_time,
        cooldown_seconds=t.cooldown_seconds,
        total_matches=t.total_matches,
        last_match_at=t.last_match_at.isoformat() if t.last_match_at else None,
    )


@router.get("/", response_model=List[WatchTaskResponse])
def list_tasks(
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """רשימת כל משימות הניטור."""
    tasks = db.query(WatchTask).all()
    return [_task_to_response(t) for t in tasks]


@router.post("/", response_model=WatchTaskResponse, status_code=201)
def create_task(
    body: WatchTaskCreate,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """יצירת משימת ניטור חדשה."""
    task = WatchTask(**body.dict())
    db.add(task)
    db.commit()
    db.refresh(task)
    return _task_to_response(task)


@router.patch("/{task_id}", response_model=WatchTaskResponse)
def update_task(
    task_id: int,
    body: WatchTaskUpdate,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """עדכון משימת ניטור."""
    task = db.query(WatchTask).filter(WatchTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="משימה לא נמצאה")
    for key, value in body.dict(exclude_unset=True).items():
        setattr(task, key, value)
    db.commit()
    db.refresh(task)
    return _task_to_response(task)


@router.delete("/{task_id}")
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """מחיקת משימת ניטור."""
    task = db.query(WatchTask).filter(WatchTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="משימה לא נמצאה")
    db.delete(task)
    db.commit()
    return {"message": "משימה נמחקה"}


@router.get("/events", response_model=List[WatchTaskEventResponse])
def list_events(
    limit: int = 30,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """רשימת אירועי התאמה אחרונים."""
    events = (
        db.query(WatchTaskEvent)
        .order_by(WatchTaskEvent.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        WatchTaskEventResponse(
            id=e.id, task_id=e.task_id,
            match_description=e.match_description,
            confidence=e.confidence,
            created_at=e.created_at.isoformat(),
        )
        for e in events
    ]
