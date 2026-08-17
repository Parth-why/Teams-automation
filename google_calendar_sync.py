"""Google Tasks integration module for Smart Teams Assignment Tracker.

Synchronizes Microsoft Teams assignments as interactive checklist items
in a dedicated 'Teams Assignments' list on Google Tasks.
"""

import json
import logging
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

import config
from storage import AssignmentStorage

logger = logging.getLogger("SmartAssignmentTracker.gcal")

GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/tasks",
]
GOOGLE_TOKEN_FILE = config.DATA_DIR / "google_token.json"
ICAL_EXPORT_FILE = config.DATA_DIR / "teams_assignments.ics"


def clean_subject_name(raw_subject: str) -> str:
    """Simplify verbose university course codes into clean readable subject names."""
    if not raw_subject or raw_subject.lower() == "general":
        return "Assignment"

    s = raw_subject.strip()
    s_upper = s.upper()

    if "ROBOTICS" in s_upper:
        return "Robotics"
    if "PYTHON" in s_upper and "LAB" in s_upper:
        return "Python Lab"
    if "EM-III" in s_upper or "EM3" in s_upper:
        return "EM-III"
    if "DATA STRUCTURE" in s_upper or "DSA" in s_upper:
        if "PR" in s_upper or "LAB" in s_upper:
            return "DSA Lab"
        return "DSA"
    if "ECA" in s_upper:
        return "ECA"
    if "EDC" in s_upper:
        return "EDC"
    if "EXCS_SE_PP" in s_upper or "PP" in s_upper:
        return "Python Prog"
    if "WRITING" in s_upper or "TECHNICAL" in s_upper:
        return "Tech Writing"

    cleaned = re.sub(r"[-_](202\d|DIV|Sem|July|Vishwas|Patil|Anuradha|Joshi).*", "", s, flags=re.IGNORECASE).strip()
    return cleaned or s


def get_credentials_file() -> Optional[Path]:
    """Find Google credentials file regardless of hidden Windows extension."""
    for candidate in [config.BASE_DIR / "credentials.json", config.BASE_DIR / "credentials.json.json"]:
        if candidate.exists():
            return candidate
    return None


def generate_ics_calendar(assignments: list[dict[str, Any]], output_file: Optional[Path] = None) -> Path:
    """Generate a standard iCalendar (.ics) file with clean titles and 1-day deadline alarms."""
    out_path = output_file or ICAL_EXPORT_FILE
    out_path.parent.mkdir(parents=True, exist_ok=True)

    now_utc = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    ics_lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Smart Teams Assignment Tracker//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:Teams Assignments",
        "X-WR-TIMEZONE:Asia/Kolkata",
    ]

    for asg in assignments:
        due_iso = asg.get("due_datetime_iso") or ""
        if not due_iso:
            continue

        try:
            dt = datetime.fromisoformat(due_iso)
        except ValueError:
            continue

        dt_start = (dt - timedelta(hours=1)).strftime("%Y%m%dT%H%M%S")
        dt_end = dt.strftime("%Y%m%dT%H%M%S")
        uid = f"{asg.get('id', 'uid')}@teams.assignment.tracker"
        clean_subj = clean_subject_name(asg.get("subject", ""))
        summary = f"[{clean_subj}] {asg.get('title', 'Assignment Deadline')}"
        description = f"Subject: {clean_subj}\\nAssignment: {asg.get('title')}\\nDue: {asg.get('due_date')} at {asg.get('due_time', '11:59 PM')}"
        if asg.get("link"):
            description += f"\\nLink: {asg.get('link')}"

        ics_lines.extend([
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{now_utc}",
            f"DTSTART:{dt_start}",
            f"DTEND:{dt_end}",
            f"SUMMARY:{summary}",
            f"DESCRIPTION:{description}",
            "STATUS:CONFIRMED",
            "BEGIN:VALARM",
            "ACTION:DISPLAY",
            f"DESCRIPTION:Reminder: 1 day until {asg.get('title')} deadline",
            "TRIGGER:-P1D",
            "END:VALARM",
            "END:VEVENT",
        ])

    ics_lines.append("END:VCALENDAR")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\r\n".join(ics_lines))

    logger.info("Generated iCalendar feed with %d events at %s", len(assignments), out_path)
    return out_path


class GoogleCalendarSync:
    """Syncs assignments as interactive checklists inside Google Tasks."""

    def __init__(self, storage: Optional[AssignmentStorage] = None) -> None:
        self.storage = storage or AssignmentStorage()
        self.tasks_service: Optional[Any] = None

    def is_available(self) -> bool:
        """Check if Google OAuth client credentials exist."""
        creds_file = get_credentials_file()
        return (creds_file is not None and creds_file.exists()) or GOOGLE_TOKEN_FILE.exists()

    def authenticate(self) -> bool:
        """Authenticate with Google OAuth2 for Google Tasks API."""
        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build

            creds = None
            if GOOGLE_TOKEN_FILE.exists():
                try:
                    creds = Credentials.from_authorized_user_file(str(GOOGLE_TOKEN_FILE), GOOGLE_SCOPES)
                except Exception:
                    creds = None

            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    try:
                        creds.refresh(Request())
                    except Exception:
                        creds = None

                if not creds:
                    creds_file = get_credentials_file()
                    if not creds_file or not creds_file.exists():
                        logger.warning("Google credentials.json not found. Tasks sync unavailable.")
                        return False

                    flow = InstalledAppFlow.from_client_secrets_file(str(creds_file), GOOGLE_SCOPES)
                    creds = flow.run_local_server(port=0)

                with open(GOOGLE_TOKEN_FILE, "w", encoding="utf-8") as token_f:
                    token_f.write(creds.to_json())

            self.tasks_service = build("tasks", "v1", credentials=creds)
            logger.info("Google Tasks service initialized successfully.")
            return True
        except Exception as e:
            logger.error("Google Tasks authentication failed: %s", e)
            return False

    def _get_or_create_teams_task_list(self) -> Optional[str]:
        """Find or create a dedicated 'Teams Assignments' list in Google Tasks with full pagination."""
        if not self.tasks_service:
            return None

        try:
            page_token = None
            while True:
                lists_res = self.tasks_service.tasklists().list(maxResults=100, pageToken=page_token).execute()
                items = lists_res.get("items", [])
                for tlist in items:
                    if tlist.get("title") == "Teams Assignments":
                        return tlist.get("id")
                page_token = lists_res.get("nextPageToken")
                if not page_token:
                    break

            # Create new list if none matched
            new_list = self.tasks_service.tasklists().insert(body={"title": "Teams Assignments"}).execute()
            logger.info("Created new Google Task list: 'Teams Assignments' (ID: %s)", new_list.get("id"))
            return new_list.get("id")
        except Exception as e:
            logger.warning("Could not access Google Tasks list: %s", e)
            return None

    def sync_assignments(self, assignments: list[dict[str, Any]]) -> dict[str, Any]:
        """Create or update interactive 9:00 AM checklist tasks in Google Tasks with resilient 404 fallback."""
        if not self.tasks_service:
            if not self.authenticate():
                generate_ics_calendar(assignments)
                return {"tasks_created": 0, "tasks_updated": 0, "skipped": len(assignments)}

        tasks_created = 0
        tasks_updated = 0
        skipped = 0

        teams_task_list_id = self._get_or_create_teams_task_list()
        if not teams_task_list_id:
            logger.error("Could not obtain 'Teams Assignments' task list ID.")
            return {"tasks_created": 0, "tasks_updated": 0, "skipped": len(assignments)}

        today_str = datetime.now().strftime("%Y-%m-%d")

        for asg in assignments:
            due_iso = asg.get("due_datetime_iso")
            due_date = asg.get("due_date")
            now = datetime.now()

            # Skip past assignments!
            if due_date and due_date < today_str:
                logger.debug("Skipping past assignment in Google sync: %s (Due: %s)", asg.get("title"), due_date)
                continue

            try:
                if due_iso:
                    dt_due = datetime.fromisoformat(due_iso)
                elif due_date:
                    dt_due = datetime.strptime(due_date, "%Y-%m-%d")
                else:
                    dt_due = now
            except ValueError:
                dt_due = now

            clean_subj = clean_subject_name(asg.get("subject", ""))
            clean_title = f"[{clean_subj}] {asg.get('title')}"
            clean_desc = f"Subject: {clean_subj}\nAssignment: {asg.get('title')}\nDue: {asg.get('due_date', dt_due.strftime('%Y-%m-%d'))} at {asg.get('due_time', '11:59 PM')}"
            if asg.get("link"):
                clean_desc += f"\nLink: {asg.get('link')}"

            due_task_rfc = f"{dt_due.strftime('%Y-%m-%d')}T03:30:00.000Z"
            existing_task_id = asg.get("gcal_task_id")
            synced_successfully = False

            # Try updating existing task
            if existing_task_id:
                try:
                    task_body = {
                        "id": existing_task_id,
                        "title": clean_title,
                        "notes": clean_desc,
                        "due": due_task_rfc,
                        "status": "completed" if asg.get("completed") else "needsAction",
                    }
                    self.tasks_service.tasks().update(
                        tasklist=teams_task_list_id,
                        task=existing_task_id,
                        body=task_body,
                    ).execute()
                    tasks_updated += 1
                    asg["gcal_task_synced"] = True
                    synced_successfully = True
                except Exception as update_err:
                    logger.debug("Task update failed (%s), falling back to insert...", update_err)
                    existing_task_id = ""

            # Insert as new task if update didn't run or failed
            if not synced_successfully:
                try:
                    task_body = {
                        "title": clean_title,
                        "notes": clean_desc,
                        "due": due_task_rfc,
                        "status": "completed" if asg.get("completed") else "needsAction",
                    }
                    new_task = self.tasks_service.tasks().insert(
                        tasklist=teams_task_list_id,
                        body=task_body,
                    ).execute()
                    asg["gcal_task_id"] = new_task.get("id", "")
                    asg["gcal_task_synced"] = True
                    tasks_created += 1
                    synced_successfully = True
                except Exception as insert_err:
                    logger.warning("Error creating Google Task for %s: %s", asg.get("title"), insert_err)
                    skipped += 1

            if synced_successfully:
                self.storage.update_assignment_status(
                    asg["id"],
                    gcal_task_id=asg.get("gcal_task_id"),
                    gcal_task_synced=True,
                )

        generate_ics_calendar(assignments)

        return {
            "tasks_created": tasks_created,
            "tasks_updated": tasks_updated,
            "skipped": skipped,
        }

    def clear_all_synced_items(self, assignments: list[dict[str, Any]]) -> dict[str, int]:
        """Delete all synced tasks from Google Tasks while preserving local assignments."""
        tasks_deleted = 0

        if not self.tasks_service:
            self.authenticate()

        teams_task_list_id = self._get_or_create_teams_task_list()

        for asg in assignments:
            task_id = asg.get("gcal_task_id")
            if task_id and self.tasks_service and teams_task_list_id:
                try:
                    self.tasks_service.tasks().delete(tasklist=teams_task_list_id, task=task_id).execute()
                    tasks_deleted += 1
                except Exception as e:
                    logger.debug("Could not delete Google Task %s: %s", task_id, e)

            asg["gcal_task_id"] = ""
            asg["gcal_task_synced"] = False
            self.storage.update_assignment_status(
                asg["id"],
                gcal_task_id="",
                gcal_task_synced=False,
            )

        generate_ics_calendar([])

        return {"tasks_deleted": tasks_deleted}
