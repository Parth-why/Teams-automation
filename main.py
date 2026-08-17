"""Main Controller for Smart Teams Assignment Tracker.

Defaults to launching the Web Application Dashboard in your browser.
Also provides CLI flags for direct terminal execution.
"""

import argparse
import sys
from typing import Optional

import config
from app import run_web_app
from assignment_manager import AssignmentManager
from auth import MicrosoftAuthenticator
from browser_fetcher import TeamsBrowserFetcher
from google_calendar_sync import GoogleCalendarSync, generate_ics_calendar
from storage import AssignmentStorage


def verify_environment() -> bool:
    """Verify that execution environment and project structure are valid."""
    logger = config.setup_logging()
    config.ensure_directories()

    try:
        import flask
        import googleapiclient
        import msal
        import requests
        import selenium
    except ImportError as e:
        logger.error("Dependency verification failed: %s", e)
        print(f"[!] Missing required dependency: {e}")
        return False

    return True


def run_sync_pipeline(timeout: int = 180) -> None:
    """Fetch assignments from Teams automatically and push to Google Tasks."""
    logger = config.setup_logging()
    manager = AssignmentManager()
    gcal = GoogleCalendarSync()

    print("\n" + "=" * 70)
    print(" 🚀 TEAMS ASSIGNMENT TRACKER -> GOOGLE TASKS SYNC")
    print("=" * 70)

    try:
        with TeamsBrowserFetcher(timeout=timeout) as fetcher:
            success = fetcher.login_and_navigate(auto_navigate=True)
            if not success:
                print("\n[!] Teams session was cancelled or timed out.")
                return

            print("\nExtracting visible assignments from Microsoft Teams...")
            raw_assignments = fetcher.fetch_assignments()

            if not raw_assignments:
                print("\n[!] No active assignments detected on screen.")
                return

            all_assignments, newly_added = manager.sync_new_assignments(raw_assignments)

            print("\n" + "-" * 70)
            print(f"[✓] {len(all_assignments)} Active Assignment(s) Extracted:")
            print("-" * 70)

            for idx, asg in enumerate(all_assignments, 1):
                due_date = asg.get("due_date") or "No Date"
                due_time = asg.get("due_time") or "11:59 PM"
                print(f" [{idx}] {asg.get('title')}")
                print(f"     Subject: {asg.get('subject')}")
                print(f"     Due:     {due_date} at {due_time}")

            if gcal.is_available():
                stats = gcal.sync_assignments(all_assignments)
                print("\n" + "=" * 70)
                print(f" [✓] Google Tasks: {stats['tasks_created']} created, {stats['tasks_updated']} updated (9:00 AM Checklist)")
                print("=" * 70)

            ics_path = generate_ics_calendar(all_assignments)
            print(f" [✓] Offline iCalendar Feed: {ics_path}")

    except Exception as e:
        logger.error("Sync error: %s", e, exc_info=True)
        print(f"\n[X] Error during sync: {e}")


def run_clear_pipeline() -> None:
    """Delete all synced tasks from Google Tasks while preserving local assignments."""
    logger = config.setup_logging()
    manager = AssignmentManager()
    gcal = GoogleCalendarSync()

    assignments = manager.get_all_assignments()

    print("\n" + "=" * 70)
    print(" 🧹 CLEARING GOOGLE TASKS")
    print("=" * 70)
    print(f" Target: {len(assignments)} tracked assignments")

    if gcal.is_available() and assignments:
        print(" Connecting to Google Tasks API to remove cloud checklist tasks...")
        del_stats = gcal.clear_all_synced_items(assignments)
        print(f" [✓] Google Tasks: Deleted {del_stats['tasks_deleted']} checklist task(s)")
    else:
        print(" [i] No Google sync items to delete or credentials not configured.")

    print(f" [✓] Preserved {len(assignments)} assignments in local database for future syncs.")
    print("=" * 70)
    print(" [✓] Google Tasks checklist decongested successfully!")
    print("=" * 70 + "\n")


def main() -> None:
    """Main application entry point."""
    parser = argparse.ArgumentParser(description="Smart Teams Assignment Tracker & Google Tasks Sync Hub")
    parser.add_argument("--sync", action="store_true", help="Run automated CLI fetch & sync to Google Tasks")
    parser.add_argument("--clear", action="store_true", help="Delete all synced tasks from Google Tasks (CLI)")
    parser.add_argument("--export-ics", action="store_true", help="Export assignments to .ics file")
    parser.add_argument("--clear-cache", action="store_true", help="Clear MSAL cache")

    args = parser.parse_args()

    if not verify_environment():
        sys.exit(1)

    if args.clear_cache:
        auth = MicrosoftAuthenticator()
        auth.clear_cache()
        print("[OK] Cache cleared.")
        return

    if args.clear:
        run_clear_pipeline()
        return

    if args.sync:
        run_sync_pipeline()
        return

    if args.export_ics:
        manager = AssignmentManager()
        asgs = manager.get_all_assignments()
        out = generate_ics_calendar(asgs)
        print(f"[OK] Exported {len(asgs)} assignments to {out}")
        return

    # DEFAULT ACTION: Start Web Server and Open Web Application in Browser!
    run_web_app()


if __name__ == "__main__":
    main()
