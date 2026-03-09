"""נקודת כניסה ראשית — FastAPI application."""

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings, LOGS_DIR, FRAMES_DIR, COLLAGES_DIR, JOURNAL_DIR
from app.db.database import init_db, SessionLocal
from app.db.seed import seed_database

LOGS_DIR.mkdir(parents=True, exist_ok=True)
FRAMES_DIR.mkdir(parents=True, exist_ok=True)
COLLAGES_DIR.mkdir(parents=True, exist_ok=True)
JOURNAL_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(str(LOGS_DIR / "ghost_brain.log")),
    ],
)
logger = logging.getLogger("ghost_brain")

_supervisor = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """אתחול ו-shutdown של האפליקציה."""
    global _supervisor

    logger.info("Ghost Brain Demo — אתחול מערכת")
    init_db()

    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()

    from app.services.journal_service import log_event
    log_event("app_start", {"environment": settings.ENVIRONMENT})

    from app.workers.supervisor import Supervisor
    _supervisor = Supervisor()
    await _supervisor.start()

    logger.info("Ghost Brain Demo — מוכן לפעולה")
    yield

    logger.info("Ghost Brain Demo — כיבוי מערכת")
    if _supervisor:
        await _supervisor.stop()
    log_event("shutdown", {})
    logger.info("Ghost Brain Demo — כיבוי הושלם")


def get_supervisor():
    """גישה ל-supervisor מתוך ה-API."""
    return _supervisor


app = FastAPI(
    title="Ghost Brain Demo",
    description="Local-first surveillance memory system",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api.auth import router as auth_router
from app.api.admin import router as admin_router
from app.api.health import router as health_router
from app.api.camera import router as camera_router
from app.api.alerts import router as alerts_router
from app.api.chat import router as chat_router
from app.api.history import router as history_router

app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(health_router)
app.include_router(camera_router)
app.include_router(alerts_router)
app.include_router(chat_router)
app.include_router(history_router)
