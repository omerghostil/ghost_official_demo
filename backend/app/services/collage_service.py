"""שירות יצירת קולאז'ים — grid של פריימים עם timestamps."""

import logging
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

import cv2
import numpy as np

from app.core.config import settings, COLLAGES_DIR

logger = logging.getLogger(__name__)


def create_collage(
    frames_with_timestamps: List[Tuple[np.ndarray, datetime]],
) -> str:
    """יצירת קולאז' grid מרשימת פריימים עם timestamps.

    מחזיר את הנתיב לקובץ הקולאז'.
    """
    cols = settings.COLLAGE_GRID_COLS
    rows = settings.COLLAGE_GRID_ROWS
    tile_w = settings.COLLAGE_TILE_WIDTH
    tile_h = settings.COLLAGE_TILE_HEIGHT

    canvas = np.zeros((rows * tile_h, cols * tile_w, 3), dtype=np.uint8)

    for idx, (frame, ts) in enumerate(frames_with_timestamps):
        if idx >= cols * rows:
            break

        row = idx // cols
        col = idx % cols

        tile = cv2.resize(frame, (tile_w, tile_h))

        ts_text = ts.strftime("%H:%M:%S")
        cv2.putText(
            tile, ts_text, (5, tile_h - 8),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1,
        )

        y_start = row * tile_h
        x_start = col * tile_w
        canvas[y_start:y_start + tile_h, x_start:x_start + tile_w] = tile

    COLLAGES_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"collage_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.jpg"
    filepath = COLLAGES_DIR / filename

    cv2.imwrite(
        str(filepath), canvas,
        [cv2.IMWRITE_JPEG_QUALITY, settings.COLLAGE_JPEG_QUALITY],
    )
    logger.info(f"קולאז' נוצר: {filepath}")
    return str(filepath)
