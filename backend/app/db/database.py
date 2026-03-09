"""חיבור למסד הנתונים SQLite עם WAL mode."""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import settings, DB_DIR

DB_DIR.mkdir(parents=True, exist_ok=True)

db_path = DB_DIR / "ghost_brain.db"
engine = create_engine(
    f"sqlite:///{db_path}",
    connect_args={"check_same_thread": False},
    echo=False,
)


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, _connection_record):
    """הגדרת פרמטרי SQLite ליציבות מקסימלית."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=FULL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()


def get_db():
    """Generator ל-dependency injection של session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """יצירת כל הטבלאות אם לא קיימות."""
    import app.models  # noqa: F401
    Base.metadata.create_all(bind=engine)
