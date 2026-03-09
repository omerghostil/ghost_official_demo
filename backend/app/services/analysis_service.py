"""שירות ניתוח קולאז'ים באמצעות OpenAI Vision."""

import base64
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import cv2
import httpx
from openai import AsyncOpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)

COLLAGE_ANALYSIS_PROMPT = """Analyze this collage of sequential webcam frames ordered chronologically.
Each tile contains a timestamp.
Describe the events that happened across the sequence in clear chronological order.
Focus only on observable facts.
Mention appearances, movement, entrances, exits, vehicle presence, and notable scene changes.
If there are periods with no meaningful change, mention them as quiet/dead periods.
Return structured JSON with:
- summary_text
- timeline_events
- detected_entities
- dead_periods
- confidence_notes
- critical_alert_matches"""


class AnalysisResult:
    """תוצאת ניתוח מובנית."""

    def __init__(self):
        self.success = False
        self.summary_text = ""
        self.timeline_events = []
        self.detected_entities = []
        self.dead_periods = []
        self.critical_alert_matches = []
        self.confidence_notes = ""
        self.raw_response = ""
        self.error = ""


class CircuitBreaker:
    """circuit breaker פשוט — עוצר אחרי כמה כשלונות רצופים."""

    def __init__(self, threshold: int, pause_seconds: int):
        self._threshold = threshold
        self._pause_seconds = pause_seconds
        self._consecutive_failures = 0
        self._paused_until: Optional[datetime] = None

    @property
    def is_open(self) -> bool:
        if self._paused_until and datetime.utcnow() < self._paused_until:
            return True
        if self._paused_until and datetime.utcnow() >= self._paused_until:
            self._paused_until = None
            self._consecutive_failures = 0
        return False

    def record_success(self) -> None:
        self._consecutive_failures = 0
        self._paused_until = None

    def record_failure(self) -> None:
        self._consecutive_failures += 1
        if self._consecutive_failures >= self._threshold:
            from datetime import timedelta
            self._paused_until = datetime.utcnow() + timedelta(seconds=self._pause_seconds)
            logger.warning(
                f"Circuit breaker פתוח — עצירה ל-{self._pause_seconds} שניות"
            )


_circuit_breaker = CircuitBreaker(
    threshold=settings.OPENAI_CIRCUIT_BREAKER_THRESHOLD,
    pause_seconds=settings.OPENAI_CIRCUIT_BREAKER_PAUSE_SECONDS,
)


def _prepare_image_base64(image_path: str) -> Optional[str]:
    """הכנת תמונה לשליחה ל-OpenAI — resize, compress, base64."""
    try:
        img = cv2.imread(image_path)
        if img is None:
            return None

        max_bytes = settings.OPENAI_MAX_IMAGE_BYTES
        quality = 80

        while quality >= 20:
            _, buffer = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, quality])
            if len(buffer) <= max_bytes:
                break
            quality -= 10
            h, w = img.shape[:2]
            img = cv2.resize(img, (int(w * 0.8), int(h * 0.8)))

        return base64.b64encode(buffer.tobytes()).decode("utf-8")
    except Exception as e:
        logger.error(f"שגיאה בהכנת תמונה: {e}")
        return None


async def analyze_collage(
    image_path: str,
    alert_rules_text: str = "",
) -> AnalysisResult:
    """ניתוח קולאז' באמצעות OpenAI Vision."""
    result = AnalysisResult()

    if _circuit_breaker.is_open:
        result.error = "circuit breaker פתוח — OpenAI זמנית מושהה"
        logger.warning(result.error)
        return result

    if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "your-key-here":
        result.error = "מפתח OpenAI לא מוגדר"
        result.summary_text = "ניתוח לא זמין — מפתח API חסר"
        return result

    image_b64 = _prepare_image_base64(image_path)
    if not image_b64:
        result.error = "לא ניתן לקרוא את התמונה"
        return result

    prompt = COLLAGE_ANALYSIS_PROMPT
    if alert_rules_text:
        prompt += f"\n\nAlso check for these critical alert conditions:\n{alert_rules_text}"

    try:
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
                                "detail": "low",
                            },
                        },
                    ],
                }
            ],
            max_tokens=1500,
            timeout=30.0,
        )

        raw_text = response.choices[0].message.content or ""
        result.raw_response = raw_text
        _parse_response(result, raw_text)
        _circuit_breaker.record_success()

    except Exception as e:
        _circuit_breaker.record_failure()
        result.error = str(e)
        logger.error(f"שגיאה בניתוח OpenAI: {e}")

    return result


def _parse_response(result: AnalysisResult, raw_text: str) -> None:
    """פרסור תשובת OpenAI ל-AnalysisResult."""
    json_text = raw_text.strip()
    if json_text.startswith("```"):
        lines = json_text.split("\n")
        json_text = "\n".join(lines[1:-1]) if len(lines) > 2 else json_text

    try:
        data = json.loads(json_text)
        result.success = True
        result.summary_text = data.get("summary_text", "")
        result.timeline_events = data.get("timeline_events", [])
        result.detected_entities = data.get("detected_entities", [])
        result.dead_periods = data.get("dead_periods", [])
        result.critical_alert_matches = data.get("critical_alert_matches", [])
        result.confidence_notes = data.get("confidence_notes", "")
    except json.JSONDecodeError:
        result.success = True
        result.summary_text = raw_text
        logger.warning("תשובת OpenAI אינה JSON תקין — נשמר כטקסט גולמי")


async def analyze_snapshot_with_question(
    frame, question: str, context: str = "",
) -> str:
    """ניתוח snapshot עם שאלת משתמש — לצ'אט."""
    if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "your-key-here":
        return "ניתוח לא זמין — מפתח API חסר"

    if _circuit_breaker.is_open:
        return "שירות הניתוח מושהה זמנית, נסה שוב מאוחר יותר"

    try:
        _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
        image_b64 = base64.b64encode(buffer.tobytes()).decode("utf-8")

        prompt = f"User question: {question}"
        if context:
            prompt += f"\n\nRecent context:\n{context}"

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
                                "detail": "low",
                            },
                        },
                    ],
                }
            ],
            max_tokens=800,
            timeout=30.0,
        )
        _circuit_breaker.record_success()
        return response.choices[0].message.content or "אין תשובה"
    except Exception as e:
        _circuit_breaker.record_failure()
        logger.error(f"שגיאה בניתוח snapshot: {e}")
        return f"שגיאה בניתוח: {str(e)}"
