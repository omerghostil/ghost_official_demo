"""מודל משימות ניטור — בדיקת פריימים מיידית לפי לוח זמנים."""

from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, DateTime, Text, Boolean,
)

from app.db.database import Base


class WatchTask(Base):
    __tablename__ = "watch_tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    label = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    is_enabled = Column(Boolean, default=True, nullable=False)
    days_of_week = Column(String(50), default="0,1,2,3,4,5,6", nullable=False)
    start_time = Column(String(10), default="00:00", nullable=False)
    end_time = Column(String(10), default="23:59", nullable=False)
    cooldown_seconds = Column(Integer, default=60, nullable=False)
    last_checked_at = Column(DateTime, nullable=True)
    last_match_at = Column(DateTime, nullable=True)
    total_matches = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class WatchTaskEvent(Base):
    __tablename__ = "watch_task_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, nullable=False, index=True)
    frame_path = Column(String(500), nullable=True)
    match_description = Column(Text, nullable=False)
    confidence = Column(String(20), default="medium", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
