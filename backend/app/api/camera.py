"""API routes — מצלמה."""

import cv2
import numpy as np
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse, Response

from app.core.deps import get_current_user
from app.models.user import User
from app.services.camera_service import camera_service

router = APIRouter(prefix="/camera", tags=["camera"])


@router.get("/stream")
def camera_stream():
    """MJPEG streaming מהמצלמה — ללא auth כדי לתמוך ב-<img> tag."""
    return StreamingResponse(
        camera_service.generate_mjpeg(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@router.get("/status")
def camera_status(current_user: User = Depends(get_current_user)):
    """סטטוס המצלמה."""
    return camera_service.get_status_dict()


@router.post("/reconnect")
def camera_reconnect(current_user: User = Depends(get_current_user)):
    """חיבור מחדש למצלמה."""
    camera_service.disconnect()
    success = camera_service.connect()
    return {"success": success, "status": camera_service.status}


@router.post("/snapshot")
def camera_snapshot(current_user: User = Depends(get_current_user)):
    """צילום snapshot מיידי."""
    frame = camera_service.grab_frame()
    if frame is None:
        return Response(content=b"", status_code=503)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray_bgr = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    _, buffer = cv2.imencode(".jpg", gray_bgr, [cv2.IMWRITE_JPEG_QUALITY, 80])
    return Response(content=buffer.tobytes(), media_type="image/jpeg")
