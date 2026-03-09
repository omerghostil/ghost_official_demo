"""מודלים של זיכרון רקע, קולאז'ים, פריימים וניתוחים."""

from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, DateTime, Float, Text, Boolean, JSON,
)

from app.db.database import Base


class BackgroundFrame(Base):
    __tablename__ = "background_frames"

    id = Column(Integer, primary_key=True, autoincrement=True)
    camera_id = Column(Integer, default=1, nullable=False)
    frame_path = Column(String(500), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    has_person = Column(Boolean, default=False, nullable=False)
    has_vehicle = Column(Boolean, default=False, nullable=False)
    person_count = Column(Integer, default=0, nullable=False)
    vehicle_count = Column(Integer, default=0, nullable=False)
    detections_json = Column(Text, nullable=True)
    is_accepted = Column(Boolean, default=False, nullable=False)
    change_score = Column(Float, nullable=True)
    collage_id = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Collage(Base):
    __tablename__ = "collages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    collage_path = Column(String(500), nullable=False)
    frame_count = Column(Integer, nullable=False)
    start_ts = Column(DateTime, nullable=False)
    end_ts = Column(DateTime, nullable=False)
    analysis_status = Column(String(30), default="pending", nullable=False)
    mode = Column(String(50), default="background_memory_default", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Detection(Base):
    __tablename__ = "detections"

    id = Column(Integer, primary_key=True, autoincrement=True)
    frame_id = Column(Integer, nullable=False, index=True)
    class_name = Column(String(50), nullable=False)
    confidence = Column(Float, nullable=False)
    x1 = Column(Float, nullable=False)
    y1 = Column(Float, nullable=False)
    x2 = Column(Float, nullable=False)
    y2 = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    collage_id = Column(Integer, nullable=False, index=True)
    status = Column(String(30), default="pending", nullable=False)
    summary_text = Column(Text, nullable=True)
    timeline_events_json = Column(Text, nullable=True)
    detected_entities_json = Column(Text, nullable=True)
    dead_periods_json = Column(Text, nullable=True)
    critical_matches_json = Column(Text, nullable=True)
    confidence_notes = Column(Text, nullable=True)
    raw_response = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)


class MemoryEntry(Base):
    __tablename__ = "memory_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_type = Column(String(50), nullable=False, index=True)
    source_id = Column(Integer, nullable=True)
    timestamp_start = Column(DateTime, nullable=False, index=True)
    timestamp_end = Column(DateTime, nullable=False, index=True)
    text_summary = Column(Text, nullable=False)
    objects_json = Column(Text, nullable=True)
    people_count = Column(Integer, default=0)
    vehicle_count = Column(Integer, default=0)
    motion_level = Column(String(20), nullable=True)
    critical_matches_json = Column(Text, nullable=True)
    tags_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
