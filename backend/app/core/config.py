"""הגדרות מרכזיות של האפליקציה — נטענות מ-.env"""

from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"

FRAMES_DIR = DATA_DIR / "frames"
COLLAGES_DIR = DATA_DIR / "collages"
LOGS_DIR = DATA_DIR / "logs"
JOURNAL_DIR = DATA_DIR / "journal"
DB_DIR = DATA_DIR / "db"


class Settings(BaseSettings):
    SECRET_KEY: str = "ghost-brain-demo-secret-key-change-in-production"
    OPENAI_API_KEY: str = ""
    DATABASE_URL: str = f"sqlite:///{DB_DIR / 'ghost_brain.db'}"
    ENVIRONMENT: str = "dev"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    LOGIN_MAX_ATTEMPTS: int = 5
    LOGIN_LOCKOUT_MINUTES: int = 5

    FRAME_SAMPLE_INTERVAL_SECONDS: float = 2.0
    COLLAGE_FRAME_COUNT: int = 18
    COLLAGE_GRID_COLS: int = 3
    COLLAGE_GRID_ROWS: int = 6
    COLLAGE_TILE_WIDTH: int = 320
    COLLAGE_TILE_HEIGHT: int = 240
    COLLAGE_JPEG_QUALITY: int = 60

    MAX_ALERT_RULES: int = 4
    CAMERA_RECONNECT_INTERVAL: float = 3.0
    CAMERA_RING_BUFFER_SIZE: int = 30

    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_MAX_RETRIES: int = 3
    OPENAI_CIRCUIT_BREAKER_THRESHOLD: int = 5
    OPENAI_CIRCUIT_BREAKER_PAUSE_SECONDS: int = 60
    OPENAI_MAX_IMAGE_BYTES: int = 1_048_576

    DETECTION_CONFIDENCE_THRESHOLD: float = 0.4
    SIGNIFICANT_CHANGE_THRESHOLD: float = 0.3

    model_config = {
        "env_file": str(BASE_DIR / ".env"),
        "env_file_encoding": "utf-8",
    }


settings = Settings()
