"""Background memory worker — דגימת פריימים, detection, significant change, collage."""

import json
import logging
from datetime import datetime
from typing import Optional, List, Tuple

import cv2
import numpy as np

from app.core.config import settings, FRAMES_DIR
from app.db.database import SessionLocal
from app.models.memory import BackgroundFrame, Collage
from app.services.camera_service import camera_service
from app.services.detection_service import detection_service, DetectionResult
from app.services.significant_change import is_significant_change
from app.services.collage_service import create_collage
from app.services.journal_service import log_event
from app.services.watch_task_service import get_active_tasks_now, check_frame_against_tasks
from app.workers.base_worker import BaseWorker

logger = logging.getLogger(__name__)

FRAMES_DIR.mkdir(parents=True, exist_ok=True)


class MemoryWorker(BaseWorker):
    """worker דגימת זיכרון רקע — כל 2 שניות."""

    def __init__(self):
        super().__init__(
            name="memory_worker",
            interval_seconds=settings.FRAME_SAMPLE_INTERVAL_SECONDS,
        )
        self._buffer: List[Tuple[np.ndarray, datetime, DetectionResult]] = []
        self._last_accepted_frame: Optional[np.ndarray] = None
        self._last_accepted_detections: Optional[DetectionResult] = None

    async def tick(self) -> None:
        frame = camera_service.grab_frame()
        if frame is None:
            return

        detections = detection_service.detect(frame)

        if not detections.has_person and not detections.has_vehicle:
            log_event("frame_skipped", {"reason": "no_person_or_vehicle"})
            return

        significant, score = is_significant_change(
            self._last_accepted_frame,
            frame,
            self._last_accepted_detections,
            detections,
        )

        if not significant:
            log_event("frame_skipped", {"reason": "no_significant_change", "score": score})
            return

        now = datetime.utcnow()
        frame_filename = f"frame_{now.strftime('%Y%m%d_%H%M%S_%f')}.jpg"
        frame_path = FRAMES_DIR / frame_filename
        cv2.imwrite(str(frame_path), frame, [cv2.IMWRITE_JPEG_QUALITY, 70])

        self._save_frame_record(frame_path, now, detections, score)
        self._buffer.append((frame.copy(), now, detections))
        self._last_accepted_frame = frame.copy()
        self._last_accepted_detections = detections

        log_event("frame_sampled", {
            "persons": detections.persons,
            "vehicles": detections.vehicles,
            "change_score": score,
            "buffer_size": len(self._buffer),
        })

        await self._check_watch_tasks(frame, str(frame_path))

        if len(self._buffer) >= settings.COLLAGE_FRAME_COUNT:
            await self._create_collage()

    def _save_frame_record(
        self, frame_path, timestamp, detections: DetectionResult, score: float,
    ) -> None:
        """שמירת רשומת פריים ב-DB."""
        db = SessionLocal()
        try:
            record = BackgroundFrame(
                frame_path=str(frame_path),
                timestamp=timestamp,
                has_person=detections.has_person,
                has_vehicle=detections.has_vehicle,
                person_count=detections.persons,
                vehicle_count=detections.vehicles,
                detections_json=json.dumps(
                    [{"class": b.class_name, "conf": round(b.confidence, 2)} for b in detections.boxes],
                    ensure_ascii=False,
                ),
                is_accepted=True,
                change_score=score,
            )
            db.add(record)
            db.commit()
        finally:
            db.close()

    async def _create_collage(self) -> None:
        """יצירת קולאז' מהבאפר ושליחה לניתוח."""
        frames_with_ts = [(f, ts) for f, ts, _ in self._buffer]
        start_ts = frames_with_ts[0][1]
        end_ts = frames_with_ts[-1][1]

        collage_path = create_collage(frames_with_ts)

        db = SessionLocal()
        try:
            collage = Collage(
                collage_path=collage_path,
                frame_count=len(self._buffer),
                start_ts=start_ts,
                end_ts=end_ts,
                analysis_status="pending",
            )
            db.add(collage)
            db.commit()
            db.refresh(collage)
            log_event("collage_created", {
                "collage_id": collage.id,
                "frame_count": len(self._buffer),
            })
        finally:
            db.close()

        self._buffer.clear()
        logger.info(f"קולאז' נוצר: {collage_path}")

    async def _check_watch_tasks(self, frame: np.ndarray, frame_path: str) -> None:
        """בדיקת פריים מול משימות ניטור פעילות."""
        try:
            active_tasks = get_active_tasks_now()
            if not active_tasks:
                return
            await check_frame_against_tasks(frame, frame_path, active_tasks)
        except Exception as e:
            logger.error(f"שגיאה בבדיקת משימות ניטור: {e}")
