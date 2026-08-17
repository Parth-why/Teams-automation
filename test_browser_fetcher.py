"""Unit test for browser_fetcher date parsing and assignment normalization."""

import unittest
from datetime import datetime, timedelta
from browser_fetcher import parse_teams_due_date, extract_time_component, extract_title_and_subject


class TestBrowserFetcher(unittest.TestCase):
    """Test suite for Selenium Browser Fetcher parsing logic."""

    def test_extract_title_and_subject_with_initials(self) -> None:
        """Test filtering out avatar initials ('S', 'A', 'E', 'EQ')."""
        lines_s = [
            "S",
            "Student Activity : Laplace Transform in Real Engineering",
            "EM-III-A-B-EXCS-2026-27-Vishwas Patil",
            "Due at 11:59 PM",
        ]
        title, subject = extract_title_and_subject(lines_s)
        self.assertEqual(title, "Student Activity : Laplace Transform in Real Engineering")
        self.assertEqual(subject, "EM-III-A-B-EXCS-2026-27-Vishwas Patil")

        lines_a = [
            "A",
            "Assignment-3",
            "EXCS_SE_PP_DIVB_2026-27",
            "Due Aug 10 at 11:59 PM",
        ]
        title, subject = extract_title_and_subject(lines_a)
        self.assertEqual(title, "Assignment-3")
        self.assertEqual(subject, "EXCS_SE_PP_DIVB_2026-27")

    def test_extract_time_component(self) -> None:
        """Test time string extraction."""
        t12, t24 = extract_time_component("Due at 11:59 PM")
        self.assertEqual(t12, "11:59 PM")
        self.assertEqual(t24, "23:59:00")

    def test_parse_explicit_dates(self) -> None:
        """Test explicit calendar dates."""
        d1, t1, iso1, _ = parse_teams_due_date("Due 15 Aug 2026 at 5:00 PM")
        self.assertEqual(d1, "2026-08-15")
        self.assertEqual(t1, "5:00 PM")
        self.assertEqual(iso1, "2026-08-15T17:00:00")

    def test_no_date_indicator_returns_empty(self) -> None:
        """Test that plain text without dates returns empty strings."""
        d, t, iso, _ = parse_teams_due_date("Technical & Business Writing-EXCS-B")
        self.assertEqual(d, "")
        self.assertEqual(t, "")
        self.assertEqual(iso, "")


if __name__ == "__main__":
    unittest.main()
