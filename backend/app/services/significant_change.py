"""זיהוי שינוי משמעותי בין פריימים — histogram + SSIM + detections."""

import logging
from typing import Optional

import cv2
import numpy as np

from app.core.config import settings
from app.services.detection_service import DetectionResult

logger = logging.getLogger(__name__)


def is_significant_change(
    previous_frame: Optional[np.ndarray],
    current_frame: np.ndarray,
    previous_detections: Optional[DetectionResult],
    current_detections: DetectionResult,
) -> tuple:
    """בדיקה אם יש שינוי משמעותי בין שני פריימים.

    מחזיר (is_significant: bool, score: float).
    """
    if previous_frame is None:
        return True, 1.0

    score = 0.0
    weights = {"histogram": 0.25, "pixel_diff": 0.25, "detection_delta": 0.5}

    hist_score = _histogram_diff(previous_frame, current_frame)
    score += hist_score * weights["histogram"]

    pixel_score = _pixel_diff(previous_frame, current_frame)
    score += pixel_score * weights["pixel_diff"]

    det_score = _detection_delta(previous_detections, current_detections)
    score += det_score * weights["detection_delta"]

    is_significant = score >= settings.SIGNIFICANT_CHANGE_THRESHOLD
    return is_significant, round(score, 3)


def _histogram_diff(frame1: np.ndarray, frame2: np.ndarray) -> float:
    """השוואת היסטוגרמות."""
    gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)

    hist1 = cv2.calcHist([gray1], [0], None, [64], [0, 256])
    hist2 = cv2.calcHist([gray2], [0], None, [64], [0, 256])

    cv2.normalize(hist1, hist1)
    cv2.normalize(hist2, hist2)

    correlation = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
    return max(0.0, 1.0 - correlation)


def _pixel_diff(frame1: np.ndarray, frame2: np.ndarray) -> float:
    """השוואת פיקסלים — motion diff."""
    gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)

    h = min(gray1.shape[0], gray2.shape[0])
    w = min(gray1.shape[1], gray2.shape[1])
    gray1 = cv2.resize(gray1, (w, h))
    gray2 = cv2.resize(gray2, (w, h))

    diff = cv2.absdiff(gray1, gray2)
    _, thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)
    change_ratio = np.count_nonzero(thresh) / thresh.size
    return min(change_ratio * 3.0, 1.0)


def _detection_delta(
    prev: Optional[DetectionResult],
    curr: DetectionResult,
) -> float:
    """שינוי במספר האובייקטים שזוהו."""
    if prev is None:
        if curr.has_person or curr.has_vehicle:
            return 1.0
        return 0.0

    person_delta = abs(curr.persons - prev.persons)
    vehicle_delta = abs(curr.vehicles - prev.vehicles)

    person_appeared = not prev.has_person and curr.has_person
    vehicle_appeared = not prev.has_vehicle and curr.has_vehicle
    person_left = prev.has_person and not curr.has_person
    vehicle_left = prev.has_vehicle and not curr.has_vehicle

    if person_appeared or person_left or vehicle_appeared or vehicle_left:
        return 1.0

    total_delta = person_delta + vehicle_delta
    return min(total_delta * 0.5, 1.0)
