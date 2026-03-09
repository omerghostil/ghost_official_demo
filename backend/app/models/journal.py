"""מודל יומן אירועים."""

from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Text

from app.db.database import Base


class EventJournal(Base):
    __tablename__ = "event_journal"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_type = Column(String(50), nullable=False, index=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
