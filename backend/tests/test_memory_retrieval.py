"""בדיקות שליפת זיכרון."""

import unittest
from datetime import datetime, timedelta

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.models.memory import MemoryEntry
from app.services.memory_service import retrieve_memory


class TestMemoryRetrieval(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")

        @event.listens_for(self.engine, "connect")
        def _set_pragma(dbapi_connection, _):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.db = Session()

        now = datetime.utcnow()
        for i in range(5):
            ts = now - timedelta(minutes=i * 10)
            entry = MemoryEntry(
                source_type="collage_analysis",
                source_id=i + 1,
                timestamp_start=ts,
                timestamp_end=ts + timedelta(minutes=5),
                text_summary=f"Person walking in hallway at time {i}",
                people_count=1,
                vehicle_count=0,
            )
            self.db.add(entry)
        self.db.commit()

    def tearDown(self):
        self.db.close()

    def test_retrieve_all(self):
        results = retrieve_memory(self.db, limit=10)
        self.assertEqual(len(results), 5)

    def test_retrieve_by_query(self):
        results = retrieve_memory(self.db, query="Person", limit=10)
        self.assertEqual(len(results), 5)

    def test_retrieve_empty_query(self):
        results = retrieve_memory(self.db, query="vehicle driving", limit=10)
        self.assertEqual(len(results), 0)

    def test_retrieve_limit(self):
        results = retrieve_memory(self.db, limit=2)
        self.assertEqual(len(results), 2)

    def test_retrieve_by_time_range(self):
        now = datetime.utcnow()
        results = retrieve_memory(
            self.db,
            from_ts=now - timedelta(minutes=25),
            limit=10,
        )
        self.assertGreater(len(results), 0)
        self.assertLessEqual(len(results), 5)


if __name__ == "__main__":
    unittest.main()
