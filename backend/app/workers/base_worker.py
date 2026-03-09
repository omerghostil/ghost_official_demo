"""מחלקת בסיס ל-worker — heartbeat, start/stop, error handling."""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class BaseWorker(ABC):
    """בסיס לכל worker — כולל heartbeat, restart, status tracking."""

    def __init__(self, name: str, interval_seconds: float = 1.0):
        self.name = name
        self.interval = interval_seconds
        self._task: Optional[asyncio.Task] = None
        self._running = False
        self._status = "stopped"
        self._last_heartbeat: Optional[datetime] = None
        self._failure_count = 0
        self._last_error: Optional[str] = None
        self._started_at: Optional[datetime] = None

    @property
    def status(self) -> str:
        return self._status

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def failure_count(self) -> int:
        return self._failure_count

    @property
    def last_error(self) -> Optional[str]:
        return self._last_error

    async def start(self) -> None:
        """הפעלת ה-worker."""
        if self._running:
            return
        self._running = True
        self._status = "running"
        self._started_at = datetime.utcnow()
        self._task = asyncio.create_task(self._run_loop())
        logger.info(f"Worker {self.name} הופעל")

    async def stop(self) -> None:
        """עצירת ה-worker."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self._status = "stopped"
        logger.info(f"Worker {self.name} נעצר")

    async def _run_loop(self) -> None:
        """לולאת ריצה עם טיפול בשגיאות."""
        while self._running:
            try:
                self._last_heartbeat = datetime.utcnow()
                await self.tick()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._failure_count += 1
                self._last_error = str(e)
                self._status = "error"
                logger.error(f"Worker {self.name} — שגיאה #{self._failure_count}: {e}")
                await asyncio.sleep(min(self._failure_count * 2, 30))
                self._status = "running"
                continue
            await asyncio.sleep(self.interval)

    @abstractmethod
    async def tick(self) -> None:
        """פעולה אחת של ה-worker — לממש בכל worker."""
        pass

    def get_health(self) -> dict:
        """מצב בריאות ה-worker."""
        return {
            "name": self.name,
            "status": self._status,
            "running": self._running,
            "last_heartbeat": self._last_heartbeat.isoformat() if self._last_heartbeat else None,
            "failure_count": self._failure_count,
            "last_error": self._last_error,
            "started_at": self._started_at.isoformat() if self._started_at else None,
        }
