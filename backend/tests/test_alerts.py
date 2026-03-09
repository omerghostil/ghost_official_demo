"""בדיקות חוקי התראה — schedule, cooldown, matching."""

import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock

from app.services.alert_service import (
    _is_in_schedule, _is_in_cooldown, _find_match,
)


class MockRule:
    def __init__(self, **kwargs):
        self.days_of_week = kwargs.get("days_of_week", "0,1,2,3,4,5,6")
        self.start_time = kwargs.get("start_time", "00:00")
        self.end_time = kwargs.get("end_time", "23:59")
        self.cooldown_seconds = kwargs.get("cooldown_seconds", 300)
        self.last_triggered_at = kwargs.get("last_triggered_at", None)
        self.target_text = kwargs.get("target_text", "person")


class TestAlertSchedule(unittest.TestCase):
    def test_all_days_all_times(self):
        rule = MockRule()
        now = datetime(2024, 1, 15, 14, 30)
        self.assertTrue(_is_in_schedule(rule, now))

    def test_wrong_day(self):
        rule = MockRule(days_of_week="0,1")
        wednesday = datetime(2024, 1, 17, 14, 30)
        self.assertFalse(_is_in_schedule(rule, wednesday))

    def test_correct_day(self):
        rule = MockRule(days_of_week="0,1,2")
        wednesday = datetime(2024, 1, 17, 14, 30)
        self.assertTrue(_is_in_schedule(rule, wednesday))

    def test_time_before_start(self):
        rule = MockRule(start_time="08:00", end_time="18:00")
        early = datetime(2024, 1, 15, 6, 0)
        self.assertFalse(_is_in_schedule(rule, early))

    def test_time_after_end(self):
        rule = MockRule(start_time="08:00", end_time="18:00")
        late = datetime(2024, 1, 15, 20, 0)
        self.assertFalse(_is_in_schedule(rule, late))

    def test_time_in_range(self):
        rule = MockRule(start_time="08:00", end_time="18:00")
        mid = datetime(2024, 1, 15, 12, 0)
        self.assertTrue(_is_in_schedule(rule, mid))


class TestAlertCooldown(unittest.TestCase):
    def test_no_previous_trigger(self):
        rule = MockRule(last_triggered_at=None)
        self.assertFalse(_is_in_cooldown(rule, datetime.utcnow()))

    def test_in_cooldown(self):
        rule = MockRule(
            cooldown_seconds=300,
            last_triggered_at=datetime.utcnow() - timedelta(seconds=100),
        )
        self.assertTrue(_is_in_cooldown(rule, datetime.utcnow()))

    def test_after_cooldown(self):
        rule = MockRule(
            cooldown_seconds=300,
            last_triggered_at=datetime.utcnow() - timedelta(seconds=400),
        )
        self.assertFalse(_is_in_cooldown(rule, datetime.utcnow()))


class TestAlertMatching(unittest.TestCase):
    def test_direct_match(self):
        result = _find_match("person", ["person detected at entrance"])
        self.assertIn("person", result.lower())

    def test_no_match(self):
        result = _find_match("vehicle", ["person walking", "empty scene"])
        self.assertEqual(result, "")

    def test_case_insensitive(self):
        result = _find_match("Person", ["PERSON DETECTED"])
        self.assertNotEqual(result, "")


if __name__ == "__main__":
    unittest.main()
