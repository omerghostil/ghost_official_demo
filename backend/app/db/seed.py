"""Seed — יצירת נתוני בסיס ראשוניים."""

import logging

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User
from app.models.camera import Camera

logger = logging.getLogger(__name__)

SEED_USERS = [
    {"username": "ghost_admin", "password": "GhostDemo2024!", "role": "admin"},
    {"username": "ghost_viewer", "password": "ViewOnly1!", "role": "client"},
]


def seed_database(db: Session) -> None:
    """יצירת נתוני seed אם לא קיימים."""
    _seed_users(db)
    _seed_camera(db)
    logger.info("Seed הושלם בהצלחה")


def _seed_users(db: Session) -> None:
    for user_data in SEED_USERS:
        existing = db.query(User).filter(User.username == user_data["username"]).first()
        if existing:
            continue
        user = User(
            username=user_data["username"],
            password_hash=hash_password(user_data["password"]),
            role=user_data["role"],
        )
        db.add(user)
        logger.info(f"נוצר משתמש: {user_data['username']} ({user_data['role']})")
    db.commit()


def _seed_camera(db: Session) -> None:
    existing = db.query(Camera).first()
    if existing:
        return
    camera = Camera(name="main_webcam", source="0", status="disconnected")
    db.add(camera)
    db.commit()
    logger.info("נוצרה מצלמה ראשית: main_webcam")
