"""שירות התראות — הערכה, cooldown, trigger."""

import json
import logging
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.alert import AlertRule, Alert

logger = logging.getLogger(__name__)


def evaluate_alerts(
    db: Session,
    critical_matches: list,
    analysis_id: int,
) -> list:
    """הערכת התראות מול חוקים פעילים.

    מחזיר רשימת alerts שנוצרו.
    """
    if not critical_matches:
        return []

    rules = db.query(AlertRule).filter(AlertRule.is_enabled == True).all()
    if not rules:
        return []

    now = datetime.utcnow()
    created_alerts = []

    for rule in rules:
        if not _is_in_schedule(rule, now):
            continue

        if _is_in_cooldown(rule, now):
            continue

        match_text = _find_match(rule.target_text, critical_matches)
        if not match_text:
            continue

        alert = Alert(
            rule_id=rule.id,
            analysis_id=analysis_id,
            match_text=match_text,
            severity="critical",
        )
        db.add(alert)

        rule.last_triggered_at = now
        created_alerts.append(alert)
        logger.info(f"התראה קריטית: {rule.label} — {match_text}")

    if created_alerts:
        db.commit()

    return created_alerts


def _is_in_schedule(rule: AlertRule, now: datetime) -> bool:
    """בדיקה אם החוק פעיל בזמן הנוכחי."""
    current_day = str(now.weekday())
    allowed_days = rule.days_of_week.split(",")
    if current_day not in allowed_days:
        return False

    current_time = now.strftime("%H:%M")
    return rule.start_time <= current_time <= rule.end_time


def _is_in_cooldown(rule: AlertRule, now: datetime) -> bool:
    """בדיקה אם החוק בתקופת cooldown."""
    if not rule.last_triggered_at:
        return False
    cooldown_end = rule.last_triggered_at + timedelta(seconds=rule.cooldown_seconds)
    return now < cooldown_end


def _find_match(target_text: str, critical_matches: list) -> str:
    """חיפוש התאמה בין target_text של חוק לתוצאות הניתוח."""
    target_lower = target_text.lower()
    for match in critical_matches:
        match_str = str(match).lower() if not isinstance(match, str) else match.lower()
        if target_lower in match_str or match_str in target_lower:
            return str(match)
    return ""


def get_active_rules_text(db: Session) -> str:
    """קבלת טקסט חוקים פעילים לשליחה ל-OpenAI."""
    rules = db.query(AlertRule).filter(AlertRule.is_enabled == True).all()
    if not rules:
        return ""
    lines = [f"- {r.label}: {r.target_text}" for r in rules]
    return "\n".join(lines)
