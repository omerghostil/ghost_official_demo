"""Camera worker — ניהול חיבור מצלמה ו-reconnect אוטומטי."""

import logging

from app.workers.base_worker import BaseWorker
from app.services.camera_service import camera_service
from app.services.journal_service import log_event

logger = logging.getLogger(__name__)


class CameraWorker(BaseWorker):
    """worker שמוודא שהמצלמה מחוברת ומבצע reconnect."""

    def __init__(self):
        super().__init__(name="camera_worker", interval_seconds=3.0)
        self._was_connected = False

    async def tick(self) -> None:
        if camera_service.status == "connected":
            if not self._was_connected:
                self._was_connected = True
                log_event("camera_connected", {})
            return

        self._was_connected = False
        logger.info("מנסה לחבר מצלמה...")
        success = camera_service.connect()

        if success:
            self._was_connected = True
            log_event("camera_connected", {})
        else:
            log_event("reconnect_attempt", {"success": False})
