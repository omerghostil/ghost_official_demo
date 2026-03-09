"""API routes — חוקי התראה ואירועי התראה."""

from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.deps import get_current_user
from app.core.config import settings
from app.models.user import User
from app.models.alert import AlertRule, Alert

router = APIRouter(prefix="/alerts", tags=["alerts"])


class AlertRuleCreate(BaseModel):
    label: str
    target_text: str
    days_of_week: str = "0,1,2,3,4,5,6"
    start_time: str = "00:00"
    end_time: str = "23:59"
    cooldown_seconds: int = 300


class AlertRuleUpdate(BaseModel):
    label: Optional[str] = None
    target_text: Optional[str] = None
    is_enabled: Optional[bool] = None
    days_of_week: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    cooldown_seconds: Optional[int] = None


class AlertRuleResponse(BaseModel):
    id: int
    label: str
    target_text: str
    is_enabled: bool
    days_of_week: str
    start_time: str
    end_time: str
    cooldown_seconds: int
    last_triggered_at: Optional[str] = None


class AlertEventResponse(BaseModel):
    id: int
    rule_id: int
    match_text: Optional[str]
    severity: str
    is_acknowledged: bool
    created_at: str


@router.get("/rules", response_model=List[AlertRuleResponse])
def list_rules(
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """רשימת כל חוקי ההתראה."""
    rules = db.query(AlertRule).all()
    return [
        AlertRuleResponse(
            id=r.id, label=r.label, target_text=r.target_text,
            is_enabled=r.is_enabled, days_of_week=r.days_of_week,
            start_time=r.start_time, end_time=r.end_time,
            cooldown_seconds=r.cooldown_seconds,
            last_triggered_at=r.last_triggered_at.isoformat() if r.last_triggered_at else None,
        )
        for r in rules
    ]


@router.post("/rules", response_model=AlertRuleResponse, status_code=201)
def create_rule(
    body: AlertRuleCreate,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """יצירת חוק התראה חדש (מקסימום 4)."""
    count = db.query(AlertRule).count()
    if count >= settings.MAX_ALERT_RULES:
        raise HTTPException(status_code=400, detail=f"מקסימום {settings.MAX_ALERT_RULES} חוקים")

    rule = AlertRule(**body.dict())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return AlertRuleResponse(
        id=rule.id, label=rule.label, target_text=rule.target_text,
        is_enabled=rule.is_enabled, days_of_week=rule.days_of_week,
        start_time=rule.start_time, end_time=rule.end_time,
        cooldown_seconds=rule.cooldown_seconds, last_triggered_at=None,
    )


@router.patch("/rules/{rule_id}", response_model=AlertRuleResponse)
def update_rule(
    rule_id: int,
    body: AlertRuleUpdate,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """עדכון חוק התראה."""
    rule = db.query(AlertRule).filter(AlertRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="חוק לא נמצא")

    update_data = body.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(rule, key, value)
    db.commit()
    db.refresh(rule)
    return AlertRuleResponse(
        id=rule.id, label=rule.label, target_text=rule.target_text,
        is_enabled=rule.is_enabled, days_of_week=rule.days_of_week,
        start_time=rule.start_time, end_time=rule.end_time,
        cooldown_seconds=rule.cooldown_seconds,
        last_triggered_at=rule.last_triggered_at.isoformat() if rule.last_triggered_at else None,
    )


@router.delete("/rules/{rule_id}")
def delete_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """מחיקת חוק התראה."""
    rule = db.query(AlertRule).filter(AlertRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="חוק לא נמצא")
    db.delete(rule)
    db.commit()
    return {"message": "חוק נמחק"}


@router.get("/events", response_model=List[AlertEventResponse])
def list_events(
    limit: int = 50,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """רשימת אירועי התראה אחרונים."""
    alerts = db.query(Alert).order_by(Alert.created_at.desc()).limit(limit).all()
    return [
        AlertEventResponse(
            id=a.id, rule_id=a.rule_id, match_text=a.match_text,
            severity=a.severity, is_acknowledged=a.is_acknowledged,
            created_at=a.created_at.isoformat(),
        )
        for a in alerts
    ]
