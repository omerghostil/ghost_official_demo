"""שירות משימות ניטור — בדיקה מיידית של פריימים מול משימות מתוזמנות."""

import base64
import json
import logging
from datetime import datetime, timedelta
from typing import List, Optional

import cv2
import numpy as np
from openai import AsyncOpenAI

from app.core.config import settings
from app.db.database import SessionLocal
from app.models.watch_task import WatchTask, WatchTaskEvent
from app.services.journal_service import log_event

logger = logging.getLogger(__name__)

WATCH_TASK_PROMPT_TEMPLATE = """אתה מערכת ניטור אבטחה. בדוק את התמונה הזו מול המשימה הבאה:

משימה: {description}

האם אתה רואה בתמונה משהו שתואם את המשימה?

ענה בפורמט JSON בלבד:
{{
  "match": true/false,
  "confidence": "high"/"medium"/"low",
  "description": "תיאור מפורט בעברית של מה שנמצא (או למה אין התאמה)"
}}

אסור לתאר פנים. אסור לדווח מספרי רישוי.
ענה בעברית בלבד."""


def get_active_tasks_now() -> List[WatchTask]:
    """קבלת משימות פעילות כרגע — לפי לוח זמנים."""
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        tasks = db.query(WatchTask).filter(WatchTask.is_enabled == True).all()

        active = []
        for task in tasks:
            if not _is_in_schedule(task, now):
                continue
            if _is_in_cooldown(task, now):
                continue
            active.append(task)
        return active
    finally:
        db.close()


def _is_in_schedule(task: WatchTask, now: datetime) -> bool:
    """בדיקה אם המשימה פעילה כרגע."""
    current_day = str(now.weekday())
    allowed_days = task.days_of_week.split(",")
    if current_day not in allowed_days:
        return False
    current_time = now.strftime("%H:%M")
    return task.start_time <= current_time <= task.end_time


def _is_in_cooldown(task: WatchTask, now: datetime) -> bool:
    """בדיקה אם המשימה בתקופת cooldown."""
    if not task.last_checked_at:
        return False
    cooldown_end = task.last_checked_at + timedelta(seconds=task.cooldown_seconds)
    return now < cooldown_end


async def check_frame_against_tasks(
    frame: np.ndarray,
    frame_path: str,
    tasks: List[WatchTask],
) -> List[dict]:
    """בדיקת פריים מול רשימת משימות — שליחה מיידית ל-OpenAI."""
    if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "your-key-here":
        return []

    results = []
    for task in tasks:
        result = await _check_single_task(frame, frame_path, task)
        if result:
            results.append(result)
    return results


async def _check_single_task(
    frame: np.ndarray,
    frame_path: str,
    task: WatchTask,
) -> Optional[dict]:
    """בדיקת פריים מול משימה בודדת."""
    try:
        _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        image_b64 = base64.b64encode(buffer.tobytes()).decode("utf-8")

        prompt = WATCH_TASK_PROMPT_TEMPLATE.format(description=task.description)

        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_b64}",
                                "detail": "high",
                            },
                        },
                    ],
                }
            ],
            max_tokens=400,
            timeout=20.0,
        )

        raw = response.choices[0].message.content or ""
        parsed = _parse_task_response(raw)

        db = SessionLocal()
        try:
            db_task = db.query(WatchTask).filter(WatchTask.id == task.id).first()
            if db_task:
                db_task.last_checked_at = datetime.utcnow()

            if parsed.get("match"):
                if db_task:
                    db_task.last_match_at = datetime.utcnow()
                    db_task.total_matches += 1

                event = WatchTaskEvent(
                    task_id=task.id,
                    frame_path=frame_path,
                    match_description=parsed.get("description", ""),
                    confidence=parsed.get("confidence", "medium"),
                )
                db.add(event)

                log_event("watch_task_match", {
                    "task_id": task.id,
                    "label": task.label,
                    "description": parsed.get("description", ""),
                })
                logger.info(f"משימת ניטור #{task.id} '{task.label}' — נמצאה התאמה!")

            db.commit()
        finally:
            db.close()

        if parsed.get("match"):
            return {
                "task_id": task.id,
                "label": task.label,
                "match": True,
                "confidence": parsed.get("confidence", "medium"),
                "description": parsed.get("description", ""),
            }

    except Exception as e:
        logger.error(f"שגיאה בבדיקת משימה #{task.id}: {e}")

    return None


def _parse_task_response(raw: str) -> dict:
    """פרסור תשובת OpenAI למשימת ניטור."""
    text = raw.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1]) if len(lines) > 2 else text

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        is_match = "true" in text.lower() and "match" in text.lower()
        return {
            "match": is_match,
            "confidence": "low",
            "description": text,
        }
