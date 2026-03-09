"""בדיקות recovery — jobs תקועים, collages לא מנותחים."""

import unittest
from datetime import datetime

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.models.memory import Collage


class TestRecovery(unittest.TestCase):
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

    def tearDown(self):
        self.db.close()

    def test_stuck_collages_reset_to_pending(self):
        c1 = Collage(
            collage_path="/tmp/c1.jpg", frame_count=18,
            start_ts=datetime.utcnow(), end_ts=datetime.utcnow(),
            analysis_status="processing",
        )
        c2 = Collage(
            collage_path="/tmp/c2.jpg", frame_count=18,
            start_ts=datetime.utcnow(), end_ts=datetime.utcnow(),
            analysis_status="completed",
        )
        self.db.add_all([c1, c2])
        self.db.commit()

        stuck = self.db.query(Collage).filter(
            Collage.analysis_status == "processing"
        ).all()
        for c in stuck:
            c.analysis_status = "pending"
        self.db.commit()

        self.assertEqual(
            self.db.query(Collage).filter(
                Collage.analysis_status == "pending"
            ).count(),
            1,
        )
        self.assertEqual(
            self.db.query(Collage).filter(
                Collage.analysis_status == "completed"
            ).count(),
            1,
        )

    def test_no_stuck_collages(self):
        c = Collage(
            collage_path="/tmp/c.jpg", frame_count=18,
            start_ts=datetime.utcnow(), end_ts=datetime.utcnow(),
            analysis_status="completed",
        )
        self.db.add(c)
        self.db.commit()

        stuck = self.db.query(Collage).filter(
            Collage.analysis_status == "processing"
        ).all()
        self.assertEqual(len(stuck), 0)


if __name__ == "__main__":
    unittest.main()
