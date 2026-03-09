"""מודלים של חוקי התראה ואירועי התראה."""

from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, DateTime, Float, Text, Boolean,
)

from app.db.database import Base


class AlertRule(Base):
    __tablename__ = "alert_rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    label = Column(String(200), nullable=False)
    target_text = Column(String(500), nullable=False)
    is_enabled = Column(Boolean, default=True, nullable=False)
    days_of_week = Column(String(50), default="0,1,2,3,4,5,6", nullable=False)
    start_time = Column(String(10), default="00:00", nullable=False)
    end_time = Column(String(10), default="23:59", nullable=False)
    cooldown_seconds = Column(Integer, default=300, nullable=False)
    last_triggered_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    rule_id = Column(Integer, nullable=False, index=True)
    analysis_id = Column(Integer, nullable=True)
    match_text = Column(Text, nullable=True)
    severity = Column(String(20), default="critical", nullable=False)
    is_acknowledged = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
