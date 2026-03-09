"""API routes — אימות משתמשים."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.services.auth_service import authenticate_user

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict


class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    is_active: bool


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    """התחברות למערכת."""
    result = authenticate_user(db, body.username, body.password)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="שם משתמש או סיסמה שגויים",
        )
    return result


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    """התנתקות מהמערכת."""
    return {"message": "התנתקות בוצעה בהצלחה"}


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """קבלת פרטי המשתמש הנוכחי."""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        role=current_user.role,
        is_active=current_user.is_active,
    )
