"""Dependencies — dependency injection עבור FastAPI routes."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session as DbSession

from app.core.security import decode_access_token
from app.db.database import get_db
from app.models.user import User

bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: DbSession = Depends(get_db),
) -> User:
    """חילוץ המשתמש הנוכחי מה-token."""
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token לא תקין או פג תוקף",
        )
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token פגום")

    user = db.query(User).filter(
        User.username == username,
        User.is_active == True,
        User.is_deleted == False,
    ).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="משתמש לא נמצא")
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """וידוא שהמשתמש הנוכחי הוא admin."""
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="הרשאת admin נדרשת")
    return current_user
