"""API routes — בריאות מערכת."""

import os
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.config import DATA_DIR, DB_DIR
from app.models.camera import WorkerState

router = APIRouter(tags=["health"])

_app_start_time = datetime.utcnow()


@router.get("/health")
def health_check():
    """בדיקת תקינות בסיסית."""
    return {
        "status": "ok",
        "uptime_seconds": (datetime.utcnow() - _app_start_time).total_seconds(),
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/health/workers")
def workers_health():
    """סטטוס כל ה-workers מה-supervisor."""
    from app.main import get_supervisor
    supervisor = get_supervisor()
    if supervisor:
        return supervisor.get_all_health()
    return {"degraded_mode": False, "workers": {}}


@router.get("/health/storage")
def storage_health():
    """מידע על שימוש באחסון."""
    def _dir_size(path: str) -> int:
        total = 0
        if os.path.exists(path):
            for dirpath, _dirnames, filenames in os.walk(path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    total += os.path.getsize(fp)
        return total

    db_size = _dir_size(str(DB_DIR))
    frames_size = _dir_size(str(DATA_DIR / "frames"))
    collages_size = _dir_size(str(DATA_DIR / "collages"))

    return {
        "db_size_mb": round(db_size / 1024 / 1024, 2),
        "frames_size_mb": round(frames_size / 1024 / 1024, 2),
        "collages_size_mb": round(collages_size / 1024 / 1024, 2),
        "total_size_mb": round((db_size + frames_size + collages_size) / 1024 / 1024, 2),
    }
