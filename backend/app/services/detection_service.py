"""שירות זיהוי אובייקטים — ONNX YOLOv8n עם fallback."""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import cv2
import numpy as np

from app.core.config import settings, BASE_DIR

logger = logging.getLogger(__name__)

MODEL_PATH = BASE_DIR / "models" / "yolov8n.onnx"

PERSON_CLASS_ID = 0
VEHICLE_CLASS_IDS = {2, 3, 5, 7}
CLASS_NAMES = {0: "person", 2: "car", 3: "motorcycle", 5: "bus", 7: "truck"}

INPUT_SIZE = 640


@dataclass
class BoundingBox:
    x1: float
    y1: float
    x2: float
    y2: float
    class_id: int
    class_name: str
    confidence: float


@dataclass
class DetectionResult:
    persons: int = 0
    vehicles: int = 0
    has_person: bool = False
    has_vehicle: bool = False
    boxes: List[BoundingBox] = field(default_factory=list)


class DetectionService:
    """שירות detection — ONNX אם זמין, אחרת fallback stub."""

    def __init__(self):
        self._session = None
        self._is_stub = True
        self._load_model()

    def _load_model(self) -> None:
        """טעינת מודל ONNX אם קיים."""
        if not MODEL_PATH.exists():
            logger.warning(f"מודל ONNX לא נמצא ב-{MODEL_PATH} — שימוש ב-fallback stub")
            return
        try:
            import onnxruntime as ort
            self._session = ort.InferenceSession(
                str(MODEL_PATH),
                providers=["CPUExecutionProvider"],
            )
            self._is_stub = False
            logger.info("מודל ONNX נטען בהצלחה")
        except Exception as e:
            logger.error(f"שגיאה בטעינת מודל ONNX: {e}")

    @property
    def is_stub(self) -> bool:
        return self._is_stub

    def detect(self, frame: np.ndarray) -> DetectionResult:
        """זיהוי אובייקטים בפריים."""
        if self._is_stub:
            return self._stub_detect(frame)
        return self._onnx_detect(frame)

    def _stub_detect(self, frame: np.ndarray) -> DetectionResult:
        """Fallback — תמיד מחזיר שיש person (לצורך testing של ה-pipeline)."""
        return DetectionResult(
            persons=1,
            vehicles=0,
            has_person=True,
            has_vehicle=False,
            boxes=[
                BoundingBox(
                    x1=0.2, y1=0.2, x2=0.8, y2=0.8,
                    class_id=0, class_name="person", confidence=0.5,
                )
            ],
        )

    def _onnx_detect(self, frame: np.ndarray) -> DetectionResult:
        """זיהוי באמצעות ONNX YOLOv8n."""
        try:
            h, w = frame.shape[:2]
            blob = self._preprocess(frame)

            input_name = self._session.get_inputs()[0].name
            outputs = self._session.run(None, {input_name: blob})

            return self._postprocess(outputs[0], w, h)
        except Exception as e:
            logger.error(f"שגיאה ב-inference: {e}")
            return DetectionResult()

    def _preprocess(self, frame: np.ndarray) -> np.ndarray:
        """הכנת תמונה ל-inference."""
        resized = cv2.resize(frame, (INPUT_SIZE, INPUT_SIZE))
        blob = resized.astype(np.float32) / 255.0
        blob = blob.transpose(2, 0, 1)
        blob = np.expand_dims(blob, axis=0)
        return blob

    def _postprocess(
        self, output: np.ndarray, orig_w: int, orig_h: int
    ) -> DetectionResult:
        """עיבוד תוצאות YOLOv8 output."""
        predictions = output[0].T
        result = DetectionResult()

        for pred in predictions:
            scores = pred[4:]
            class_id = int(np.argmax(scores))
            confidence = float(scores[class_id])

            if confidence < settings.DETECTION_CONFIDENCE_THRESHOLD:
                continue
            if class_id != PERSON_CLASS_ID and class_id not in VEHICLE_CLASS_IDS:
                continue

            cx, cy, bw, bh = pred[:4]
            x1 = (cx - bw / 2) / INPUT_SIZE * orig_w
            y1 = (cy - bh / 2) / INPUT_SIZE * orig_h
            x2 = (cx + bw / 2) / INPUT_SIZE * orig_w
            y2 = (cy + bh / 2) / INPUT_SIZE * orig_h

            class_name = CLASS_NAMES.get(class_id, "unknown")
            if class_id in VEHICLE_CLASS_IDS:
                class_name = "vehicle"

            box = BoundingBox(
                x1=x1, y1=y1, x2=x2, y2=y2,
                class_id=class_id, class_name=class_name,
                confidence=confidence,
            )
            result.boxes.append(box)

            if class_id == PERSON_CLASS_ID:
                result.persons += 1
                result.has_person = True
            elif class_id in VEHICLE_CLASS_IDS:
                result.vehicles += 1
                result.has_vehicle = True

        return result


detection_service = DetectionService()
