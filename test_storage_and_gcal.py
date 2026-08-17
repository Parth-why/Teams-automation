"""Unit tests for storage, assignment_manager, and google_calendar_sync."""

import unittest
from pathlib import Path
from storage import AssignmentStorage
from assignment_manager import AssignmentManager
from google_calendar_sync import generate_ics_calendar


class TestStorageAndGCal(unittest.TestCase):
    """Test suite for storage and calendar generation."""

    def setUp(self) -> None:
        self.test_storage_path = Path(__file__).resolve().parent / "data" / "test_assignments.json"
        self.storage = AssignmentStorage(file_path=self.test_storage_path)

    def tearDown(self) -> None:
        if self.test_storage_path.exists():
            self.test_storage_path.unlink()

    def test_save_and_load_assignments(self) -> None:
        """Test persisting and loading assignments."""
        sample_data = [
            {
                "id": "test_1",
                "title": "Robotics Lab 1",
                "subject": "Robotics",
                "due_date": "2026-08-20",
                "due_time": "11:59 PM",
                "due_datetime_iso": "2026-08-20T23:59:00",
                "completed": False,
                "gcal_task_id": "task_123",
                "gcal_task_synced": True,
            }
        ]
        self.storage.save_assignments(sample_data)
        loaded = self.storage.load_assignments()
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0]["title"], "Robotics Lab 1")
        self.assertEqual(loaded[0]["gcal_task_id"], "task_123")

    def test_manager_sorting(self) -> None:
        """Test sorting assignments with nearest deadline first."""
        items = [
            {"id": "2", "title": "Later", "due_datetime_iso": "2026-08-25T23:59:00"},
            {"id": "1", "title": "Earlier", "due_datetime_iso": "2026-08-12T23:59:00"},
            {"id": "3", "title": "No date", "due_datetime_iso": ""},
        ]
        sorted_items = AssignmentManager.sort_assignments_by_due_date(items)
        self.assertEqual(sorted_items[0]["id"], "1")
        self.assertEqual(sorted_items[1]["id"], "2")
        self.assertEqual(sorted_items[2]["id"], "3")

    def test_ics_generation(self) -> None:
        """Test generating .ics file with 1-day reminder alarm."""
        items = [
            {
                "id": "asg_101",
                "title": "Math Assignment",
                "subject": "Mathematics",
                "due_datetime_iso": "2026-08-15T23:59:00",
            }
        ]
        ics_test_file = Path(__file__).resolve().parent / "data" / "test_feed.ics"
        out_path = generate_ics_calendar(items, output_file=ics_test_file)
        self.assertTrue(out_path.exists())

        with open(out_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("BEGIN:VCALENDAR", content)
        self.assertIn("TRIGGER:-P1D", content)
        self.assertIn("[Mathematics] Math Assignment", content)

        if ics_test_file.exists():
            ics_test_file.unlink()


if __name__ == "__main__":
    unittest.main()
