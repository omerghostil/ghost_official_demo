"""ייבוא כל המודלים כדי שהם יירשמו ב-metadata."""

from app.models.user import User, Session
from app.models.camera import Camera, WorkerState, CaptureJob
from app.models.memory import (
    BackgroundFrame, Collage, Detection, Analysis, MemoryEntry,
)
from app.models.alert import AlertRule, Alert
from app.models.chat import ChatMessage
from app.models.journal import EventJournal

__all__ = [
    "User", "Session",
    "Camera", "WorkerState", "CaptureJob",
    "BackgroundFrame", "Collage", "Detection", "Analysis", "MemoryEntry",
    "AlertRule", "Alert",
    "ChatMessage",
    "EventJournal",
]
