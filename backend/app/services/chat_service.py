"""שירות צ'אט — זיהוי intent ומענה."""

import logging
from typing import Optional

from openai import AsyncOpenAI
from sqlalchemy.orm import Session

from app.core.config import settings
from app.services.camera_service import camera_service
from app.services.memory_service import retrieve_memory, get_recent_context
from app.services.analysis_service import analyze_snapshot_with_question

logger = logging.getLogger(__name__)

PRESENT_KEYWORDS = [
    "עכשיו", "כרגע", "now", "current", "right now",
    "what's happening", "מה קורה", "מה רואים", "what do you see",
    "מה יש", "תתאר", "describe", "מה זה", "what is",
    "זה", "האם", "איזה", "מי", "who", "which",
]
PAST_KEYWORDS = [
    "לפני", "אתמול", "בעבר", "earlier", "before", "ago",
    "מה קרה", "what happened", "היסטוריה", "history",
    "לאחרונה", "recently", "בשעה האחרונה", "last hour",
    "דוח", "report", "סיכום", "summary", "תרשום",
]
ALERT_KEYWORDS = [
    "תיצור התראה", "create alert", "הוסף חוק", "add rule",
    "התראה אם", "alert if", "alert when",
]


def _detect_intent(message: str) -> str:
    """זיהוי כוונת ההודעה."""
    msg_lower = message.lower()
    for kw in ALERT_KEYWORDS:
        if kw in msg_lower:
            return "create_alert"
    for kw in PAST_KEYWORDS:
        if kw in msg_lower:
            return "past"
    for kw in PRESENT_KEYWORDS:
        if kw in msg_lower:
            return "present"
    return "present"


async def process_chat_message(
    db: Session,
    user_id: int,
    message: str,
) -> dict:
    """עיבוד הודעת צ'אט ומענה."""
    intent = _detect_intent(message)

    if intent == "present":
        return await _handle_present(db, message)
    elif intent == "past":
        return await _handle_past(db, message)
    elif intent == "create_alert":
        return _handle_create_alert(message)
    else:
        return await _handle_present(db, message)


async def _handle_present(db: Session, question: str) -> dict:
    """מענה על שאלה על ההווה — snapshot + ניתוח."""
    latest = camera_service.get_latest_frame()
    context = get_recent_context(db)

    if latest:
        frame, _ = latest
        answer = await analyze_snapshot_with_question(frame, question, context)
    else:
        answer = "המצלמה לא מחוברת כרגע. אין אפשרות לנתח את המצב הנוכחי."

    return {"content": answer, "intent": "present"}


async def _handle_past(db: Session, question: str) -> dict:
    """מענה על שאלה על העבר — שליפה מהזיכרון."""
    entries = retrieve_memory(db, query=None, limit=10)

    if not entries:
        return {"content": "אין רשומות זיכרון עדיין", "intent": "past"}

    context_lines = []
    for e in entries:
        ts = e.timestamp_start.strftime("%Y-%m-%d %H:%M:%S")
        context_lines.append(f"[{ts}] {e.text_summary}")

    context_text = "\n".join(context_lines)

    if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "your-key-here":
        return {"content": f"היסטוריה אחרונה:\n{context_text}", "intent": "past"}

    try:
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "אתה Ghost Brain — מערכת זיכרון ניטור ביטחוני מקצועית. "
                        "יש לך רשומות תצפית מפורטות ממצלמות אבטחה. "
                        "ענה על שאלות לפי הרשומות למטה בפירוט מקסימלי בעברית בלבד. "
                        "כלול: תיאורי אנשים (לבוש, גיל, מין, פעולות), פרטי רכבים "
                        "(סוג, צבע, יצרן), חפצים, תנועות, אינטראקציות. "
                        "לעולם אל תסרב לענות. לעולם אל תגיד 'אני לא יכול'. תאר הכל. "
                        "אסור לתאר פנים. אסור לדווח מספרי רישוי. "
                        "אם מבקשים דוח, ספק דוח כרונולוגי מפורט של כל האירועים שנרשמו."
                    ),
                },
                {
                    "role": "user",
                    "content": f"רשומות ניטור:\n{context_text}\n\nשאלת מפעיל אבטחה: {question}",
                },
            ],
            max_tokens=1500,
            timeout=30.0,
        )
        answer = response.choices[0].message.content or "אין תשובה"
    except Exception as e:
        logger.error(f"שגיאה בצ'אט עבר: {e}")
        answer = f"שגיאה בעיבוד. היסטוריה אחרונה:\n{context_text}"

    return {"content": answer, "intent": "past"}


def _handle_create_alert(message: str) -> dict:
    """טיפול בבקשה ליצירת חוק התראה."""
    return {
        "content": (
            f"הבנתי שאתה רוצה ליצור חוק התראה. "
            f"אנא צור אותו דרך לוח ההתראות בצד המסך.\n"
            f"הטקסט שלך: \"{message}\""
        ),
        "intent": "create_alert",
    }
