"""בדיקות פילטר שינוי משמעותי."""

import unittest

import numpy as np

from app.services.significant_change import is_significant_change
from app.services.detection_service import DetectionResult, BoundingBox


class TestSignificantChange(unittest.TestCase):
    def _make_frame(self, value: int = 128) -> np.ndarray:
        return np.full((480, 640, 3), value, dtype=np.uint8)

    def _make_detections(self, persons: int = 0, vehicles: int = 0) -> DetectionResult:
        return DetectionResult(
            persons=persons,
            vehicles=vehicles,
            has_person=persons > 0,
            has_vehicle=vehicles > 0,
        )

    def test_first_frame_always_significant(self):
        frame = self._make_frame()
        detections = self._make_detections(persons=1)
        is_sig, score = is_significant_change(None, frame, None, detections)
        self.assertTrue(is_sig)
        self.assertEqual(score, 1.0)

    def test_identical_frames_no_detection_change(self):
        frame = self._make_frame(128)
        det = self._make_detections(persons=1)
        is_sig, score = is_significant_change(frame, frame.copy(), det, det)
        self.assertFalse(is_sig)

    def test_person_appeared(self):
        frame1 = self._make_frame(100)
        frame2 = self._make_frame(100)
        det1 = self._make_detections(persons=0)
        det2 = self._make_detections(persons=1)
        is_sig, score = is_significant_change(frame1, frame2, det1, det2)
        self.assertTrue(is_sig)

    def test_person_left(self):
        frame1 = self._make_frame(100)
        frame2 = self._make_frame(100)
        det1 = self._make_detections(persons=1)
        det2 = self._make_detections(persons=0)
        is_sig, score = is_significant_change(frame1, frame2, det1, det2)
        self.assertTrue(is_sig)

    def test_big_visual_change(self):
        frame1 = self._make_frame(0)
        frame2 = self._make_frame(255)
        det = self._make_detections(persons=1)
        is_sig, score = is_significant_change(frame1, frame2, det, det)
        self.assertTrue(is_sig)


if __name__ == "__main__":
    unittest.main()
