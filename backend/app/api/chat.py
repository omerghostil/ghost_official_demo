"""API routes — צ'אט."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.chat import ChatMessage
from app.services.chat_service import process_chat_message

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    role: str
    content: str
    intent: str = ""
    timestamp: str = ""


@router.post("/message", response_model=ChatResponse)
async def send_message(
    body: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """שליחת הודעה לצ'אט."""
    user_msg = ChatMessage(
        user_id=current_user.id,
        role="user",
        content=body.message,
    )
    db.add(user_msg)
    db.commit()

    response = await process_chat_message(db, current_user.id, body.message)

    assistant_msg = ChatMessage(
        user_id=current_user.id,
        role="assistant",
        content=response["content"],
        intent=response.get("intent", ""),
    )
    db.add(assistant_msg)
    db.commit()

    return ChatResponse(
        role="assistant",
        content=response["content"],
        intent=response.get("intent", ""),
        timestamp=assistant_msg.created_at.isoformat(),
    )


@router.get("/history", response_model=List[ChatResponse])
def get_history(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """היסטוריית הודעות צ'אט."""
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == current_user.id)
        .order_by(ChatMessage.created_at.desc())
        .limit(limit)
        .all()
    )
    messages.reverse()
    return [
        ChatResponse(
            role=m.role,
            content=m.content,
            intent=m.intent or "",
            timestamp=m.created_at.isoformat(),
        )
        for m in messages
    ]
