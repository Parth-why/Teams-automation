"""Unit test for Stage 2 modules: auth.py, teams_api.py, and normalization."""

import unittest
from teams_api import TeamsGraphClient
from auth import AuthResult, MicrosoftAuthenticator


class TestStage2Modules(unittest.TestCase):
    """Test suite for Stage 2 components."""

    def test_normalization_complete_data(self) -> None:
        """Test normalization when all Graph fields are provided."""
        raw_graph_data = {
            "id": "asg-101",
            "displayName": "Machine Learning Assignment 1",
            "classId": "CS401",
            "dueDateTime": "2026-08-20T23:59:59Z",
            "instructions": {"content": "Complete exercises 1 to 5."},
            "webUrl": "https://teams.microsoft.com/l/assignment/asg-101",
        }

        normalized = TeamsGraphClient.normalize_assignment(raw_graph_data)

        self.assertEqual(normalized["id"], "asg-101")
        self.assertEqual(normalized["title"], "Machine Learning Assignment 1")
        self.assertEqual(normalized["subject"], "CS401")
        self.assertEqual(normalized["due_date"], "2026-08-20")
        self.assertEqual(normalized["details"], "Complete exercises 1 to 5.")
        self.assertEqual(normalized["link"], "https://teams.microsoft.com/l/assignment/asg-101")
        self.assertFalse(normalized["completed"])
        self.assertFalse(normalized["reminder_sent"])
        self.assertEqual(normalized["source"], "graph_api")

    def test_normalization_missing_fields(self) -> None:
        """Test normalization resilience when fields are missing."""
        raw_graph_data = {
            "id": 12345,
        }

        normalized = TeamsGraphClient.normalize_assignment(raw_graph_data)

        self.assertEqual(normalized["id"], "12345")
        self.assertEqual(normalized["title"], "Untitled Assignment")
        self.assertEqual(normalized["subject"], "General")
        self.assertEqual(normalized["due_date"], "")
        self.assertEqual(normalized["details"], "")
        self.assertEqual(normalized["link"], "")
        self.assertFalse(normalized["completed"])

    def test_auth_result_initialization(self) -> None:
        """Test AuthResult encapsulation."""
        res = AuthResult(success=True, access_token="sample_token")
        self.assertTrue(res.success)
        self.assertEqual(res.access_token, "sample_token")
        self.assertFalse(res.requires_admin_consent)


if __name__ == "__main__":
    unittest.main()
