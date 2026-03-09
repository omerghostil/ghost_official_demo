"""Supervisor — ניהול כל ה-workers, heartbeat, restart, degraded mode."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List

from app.workers.base_worker import BaseWorker
from app.workers.camera_worker import CameraWorker
from app.workers.memory_worker import MemoryWorker
from app.workers.analysis_worker import AnalysisWorker
from app.services.journal_service import log_event
from app.db.database import SessionLocal
from app.models.memory import Collage

logger = logging.getLogger(__name__)

MAX_FAILURES_BEFORE_DEGRADED = 3
HEARTBEAT_CHECK_INTERVAL = 10.0
HEARTBEAT_TIMEOUT = 30.0


class Supervisor:
    """מנהל workers מרכזי — restart, monitoring, recovery."""

    def __init__(self):
        self._workers: Dict[str, BaseWorker] = {}
        self._degraded_mode = False
        self._monitor_task = None

    @property
    def is_degraded(self) -> bool:
        return self._degraded_mode

    async def start(self) -> None:
        """הפעלת כל ה-workers ו-recovery."""
        logger.info("Supervisor — אתחול")
        self._run_recovery()

        camera_worker = CameraWorker()
        memory_worker = MemoryWorker()
        analysis_worker = AnalysisWorker()

        self._workers = {
            "camera_worker": camera_worker,
            "memory_worker": memory_worker,
            "analysis_worker": analysis_worker,
        }

        for worker in self._workers.values():
            await worker.start()

        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("Supervisor — כל ה-workers הופעלו")

    async def stop(self) -> None:
        """עצירת כל ה-workers."""
        logger.info("Supervisor — כיבוי")
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass

        for worker in self._workers.values():
            await worker.stop()
        logger.info("Supervisor — כל ה-workers נעצרו")

    async def _monitor_loop(self) -> None:
        """לולאת ניטור — בדיקת heartbeat ו-restart."""
        while True:
            try:
                await asyncio.sleep(HEARTBEAT_CHECK_INTERVAL)
                now = datetime.utcnow()
                any_degraded = False

                for name, worker in self._workers.items():
                    if not worker.is_running:
                        continue

                    if worker.failure_count >= MAX_FAILURES_BEFORE_DEGRADED:
                        any_degraded = True
                        logger.warning(f"Worker {name} — מצב degraded ({worker.failure_count} כשלונות)")

                    if (
                        worker._last_heartbeat
                        and (now - worker._last_heartbeat).total_seconds() > HEARTBEAT_TIMEOUT
                    ):
                        logger.warning(f"Worker {name} — heartbeat timeout, restart")
                        await worker.stop()
                        await worker.start()
                        log_event("worker_restart", {"worker": name, "reason": "heartbeat_timeout"})

                if any_degraded != self._degraded_mode:
                    self._degraded_mode = any_degraded
                    mode_str = "DEGRADED" if any_degraded else "NORMAL"
                    logger.info(f"Supervisor — מצב מערכת: {mode_str}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Supervisor monitor — שגיאה: {e}")

    def _run_recovery(self) -> None:
        """recovery באתחול — collages שלא נותחו, jobs תקועים."""
        logger.info("Supervisor — הרצת recovery")
        db = SessionLocal()
        try:
            stuck = (
                db.query(Collage)
                .filter(Collage.analysis_status == "processing")
                .all()
            )
            for c in stuck:
                c.analysis_status = "pending"
                logger.info(f"Recovery: collage #{c.id} הוחזר ל-pending")

            db.commit()
            log_event("recovery_run", {"stuck_collages": len(stuck)})
        finally:
            db.close()

    def get_all_health(self) -> dict:
        """קבלת מצב בריאות כל ה-workers."""
        return {
            "degraded_mode": self._degraded_mode,
            "workers": {
                name: worker.get_health()
                for name, worker in self._workers.items()
            },
        }
