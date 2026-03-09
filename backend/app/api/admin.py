"""API routes — ניהול משתמשים ובריאות מערכת (admin בלבד)."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.deps import require_admin
from app.models.user import User
from app.services.auth_service import (
    create_user, reset_user_password, toggle_user_active, soft_delete_user,
)

router = APIRouter(prefix="/admin", tags=["admin"])


class CreateUserRequest(BaseModel):
    username: str
    password: str
    role: str = "client"


class ResetPasswordRequest(BaseModel):
    new_password: str


class ToggleActiveRequest(BaseModel):
    is_active: bool


class UserListItem(BaseModel):
    id: int
    username: str
    role: str
    is_active: bool
    is_deleted: bool
    failed_login_attempts: int


@router.get("/users", response_model=List[UserListItem])
def list_users(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """רשימת כל המשתמשים."""
    users = db.query(User).filter(User.is_deleted == False).all()
    return [
        UserListItem(
            id=u.id, username=u.username, role=u.role,
            is_active=u.is_active, is_deleted=u.is_deleted,
            failed_login_attempts=u.failed_login_attempts,
        )
        for u in users
    ]


@router.post("/users", response_model=UserListItem, status_code=status.HTTP_201_CREATED)
def admin_create_user(
    body: CreateUserRequest,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """יצירת משתמש חדש."""
    existing = db.query(User).filter(User.username == body.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="שם משתמש כבר קיים")
    user = create_user(db, body.username, body.password, body.role)
    return UserListItem(
        id=user.id, username=user.username, role=user.role,
        is_active=user.is_active, is_deleted=user.is_deleted,
        failed_login_attempts=user.failed_login_attempts,
    )


@router.post("/users/{user_id}/reset-password")
def admin_reset_password(
    user_id: int,
    body: ResetPasswordRequest,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """איפוס סיסמה למשתמש."""
    if not reset_user_password(db, user_id, body.new_password):
        raise HTTPException(status_code=404, detail="משתמש לא נמצא")
    return {"message": "סיסמה אופסה בהצלחה"}


@router.patch("/users/{user_id}")
def admin_toggle_user(
    user_id: int,
    body: ToggleActiveRequest,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """הפעלה/השבתה של משתמש."""
    if not toggle_user_active(db, user_id, body.is_active):
        raise HTTPException(status_code=404, detail="משתמש לא נמצא")
    return {"message": "סטטוס עודכן"}


@router.delete("/users/{user_id}")
def admin_delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """מחיקה לוגית של משתמש."""
    if not soft_delete_user(db, user_id):
        raise HTTPException(status_code=404, detail="משתמש לא נמצא")
    return {"message": "משתמש נמחק"}


@router.get("/health")
def admin_health(
    _admin: User = Depends(require_admin),
):
    """סטטוס בריאות כללי (admin בלבד)."""
    from app.main import get_supervisor
    supervisor = get_supervisor()
    supervisor_health = supervisor.get_all_health() if supervisor else {}
    return {
        "supervisor": supervisor_health,
    }
