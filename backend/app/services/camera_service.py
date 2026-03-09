"""שירות מצלמה — capture, streaming, reconnect."""

import logging
import threading
import time
from collections import deque
from datetime import datetime
from typing import Optional

import cv2
import numpy as np

from app.core.config import settings

logger = logging.getLogger(__name__)


class CameraService:
    """ניהול מצלמת רשת — singleton, thread-safe."""

    def __init__(self):
        self._cap: Optional[cv2.VideoCapture] = None
        self._status = "disconnected"
        self._connected_at: Optional[datetime] = None
        self._last_frame_at: Optional[datetime] = None
        self._ring_buffer: deque = deque(maxlen=settings.CAMERA_RING_BUFFER_SIZE)
        self._lock = threading.Lock()
        self._consecutive_failures = 0
        self._max_failures_before_disconnect = 10

    @property
    def status(self) -> str:
        return self._status

    @property
    def connected_at(self) -> Optional[datetime]:
        return self._connected_at

    @property
    def last_frame_at(self) -> Optional[datetime]:
        return self._last_frame_at

    def connect(self) -> bool:
        """חיבור למצלמה."""
        with self._lock:
            try:
                if self._cap and self._cap.isOpened():
                    self._status = "connected"
                    return True
                if self._cap:
                    self._cap.release()
                self._cap = cv2.VideoCapture(0)
                if self._cap.isOpened():
                    self._status = "connected"
                    self._connected_at = datetime.utcnow()
                    self._consecutive_failures = 0
                    logger.info("מצלמה מחוברת")
                    return True
                else:
                    self._status = "disconnected"
                    self._cap = None
                    return False
            except Exception as e:
                self._status = "error"
                logger.error(f"שגיאה בחיבור מצלמה: {e}")
                return False

    def disconnect(self) -> None:
        """ניתוק מהמצלמה."""
        with self._lock:
            if self._cap:
                self._cap.release()
                self._cap = None
            self._status = "disconnected"
            self._connected_at = None

    def grab_frame(self) -> Optional[np.ndarray]:
        """שליפת פריים בודד מהמצלמה."""
        with self._lock:
            if not self._cap or not self._cap.isOpened():
                return None
            ret, frame = self._cap.read()
            if not ret or frame is None:
                self._consecutive_failures += 1
                if self._consecutive_failures >= self._max_failures_before_disconnect:
                    self._status = "disconnected"
                    self._cap.release()
                    self._cap = None
                    self._consecutive_failures = 0
                return None
            self._consecutive_failures = 0
            self._status = "connected"
            self._last_frame_at = datetime.utcnow()
            self._ring_buffer.append((frame.copy(), self._last_frame_at))
            return frame

    def get_latest_frame(self) -> Optional[tuple]:
        """קבלת הפריים האחרון מהבאפר — (frame, timestamp)."""
        if not self._ring_buffer:
            return None
        return self._ring_buffer[-1]

    def generate_mjpeg(self):
        """Generator ל-MJPEG streaming."""
        while True:
            frame = self.grab_frame()
            if frame is None:
                placeholder = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(
                    placeholder, "NO SIGNAL", (180, 250),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.5, (80, 80, 80), 3,
                )
                _, buffer = cv2.imencode(".jpg", placeholder)
            else:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                gray_bgr = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
                _, buffer = cv2.imencode(".jpg", gray_bgr, [cv2.IMWRITE_JPEG_QUALITY, 70])

            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n"
                + buffer.tobytes()
                + b"\r\n"
            )
            time.sleep(0.033)

    def get_status_dict(self) -> dict:
        """מחזיר סטטוס נוכחי כ-dict."""
        uptime = None
        if self._connected_at and self._status == "connected":
            uptime = (datetime.utcnow() - self._connected_at).total_seconds()
        return {
            "status": self._status,
            "connected_at": self._connected_at.isoformat() if self._connected_at else None,
            "last_frame_at": self._last_frame_at.isoformat() if self._last_frame_at else None,
            "uptime_seconds": uptime,
            "buffer_size": len(self._ring_buffer),
        }


camera_service = CameraService()
