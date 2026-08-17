"""Unit tests for the Flask Web Application and REST API."""

import json
import unittest
from app import app


class TestWebApp(unittest.TestCase):
    """Test suite for Web Application API endpoints."""

    def setUp(self) -> None:
        self.client = app.test_client()

    def test_index_page(self) -> None:
        """Test GET / renders HTML dashboard."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Teams & Google Tasks Sync Hub", response.data)

    def test_get_status_api(self) -> None:
        """Test GET /api/status returns valid JSON with statistics and subject breakdown."""
        response = self.client.get("/api/status")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data.get("success"))
        self.assertIn("stats", data)
        self.assertIn("subject_breakdown", data)
        self.assertIn("activity_logs", data)


if __name__ == "__main__":
    unittest.main()
