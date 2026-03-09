"""מודל הודעות צ'אט."""

from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Text

from app.db.database import Base


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    intent = Column(String(30), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
