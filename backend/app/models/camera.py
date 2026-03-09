"""מודלים של מצלמה ומצב workers."""

from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Float, Text, Boolean

from app.db.database import Base


class Camera(Base):
    __tablename__ = "cameras"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), default="main_webcam", nullable=False)
    source = Column(String(255), default="0", nullable=False)
    status = Column(String(30), default="disconnected", nullable=False)
    last_connected_at = Column(DateTime, nullable=True)
    last_frame_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class WorkerState(Base):
    __tablename__ = "worker_state"

    id = Column(Integer, primary_key=True, autoincrement=True)
    worker_name = Column(String(50), unique=True, nullable=False)
    status = Column(String(30), default="stopped", nullable=False)
    last_heartbeat = Column(DateTime, nullable=True)
    failure_count = Column(Integer, default=0, nullable=False)
    last_error = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CaptureJob(Base):
    __tablename__ = "capture_jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    camera_id = Column(Integer, nullable=False, index=True)
    status = Column(String(30), default="pending", nullable=False)
    frame_path = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
