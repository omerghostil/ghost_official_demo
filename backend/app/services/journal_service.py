"""שירות יומן אירועים — append-only JSONL."""

import json
import logging
from datetime import datetime
from pathlib import Path

from app.core.config import JOURNAL_DIR

logger = logging.getLogger(__name__)

JOURNAL_FILE = JOURNAL_DIR / "events.jsonl"


def log_event(event_type: str, details: dict = None) -> None:
    """כתיבת אירוע ליומן JSONL."""
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "details": details or {},
    }
    try:
        JOURNAL_DIR.mkdir(parents=True, exist_ok=True)
        with open(JOURNAL_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:
        logger.error(f"כשל בכתיבת יומן: {e}")
