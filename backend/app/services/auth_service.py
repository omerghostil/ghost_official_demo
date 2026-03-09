"""שירות אימות — login, logout, ניהול ניסיונות כושלים."""

from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import verify_password, hash_password, create_access_token
from app.models.user import User


def authenticate_user(db: Session, username: str, password: str) -> Optional[dict]:
    """אימות משתמש — מחזיר token אם הצליח, None אם נכשל."""
    user = db.query(User).filter(
        User.username == username,
        User.is_deleted == False,
    ).first()

    if not user:
        return None

    if not user.is_active:
        return None

    if user.locked_until and user.locked_until > datetime.utcnow():
        return None

    if not verify_password(password, user.password_hash):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= settings.LOGIN_MAX_ATTEMPTS:
            user.locked_until = datetime.utcnow() + timedelta(
                minutes=settings.LOGIN_LOCKOUT_MINUTES
            )
        db.commit()
        return None

    user.failed_login_attempts = 0
    user.locked_until = None
    db.commit()

    token = create_access_token(subject=user.username, role=user.role)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "role": user.role,
        },
    }


def create_user(
    db: Session,
    username: str,
    password: str,
    role: str = "client",
) -> User:
    """יצירת משתמש חדש."""
    user = User(
        username=username,
        password_hash=hash_password(password),
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def reset_user_password(db: Session, user_id: int, new_password: str) -> bool:
    """איפוס סיסמה למשתמש."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False
    user.password_hash = hash_password(new_password)
    user.failed_login_attempts = 0
    user.locked_until = None
    db.commit()
    return True


def toggle_user_active(db: Session, user_id: int, is_active: bool) -> bool:
    """הפעלה/השבתה של משתמש."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False
    user.is_active = is_active
    db.commit()
    return True


def soft_delete_user(db: Session, user_id: int) -> bool:
    """מחיקה לוגית של משתמש."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False
    user.is_deleted = True
    user.is_active = False
    db.commit()
    return True
