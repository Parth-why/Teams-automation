"""Local JSON storage module for Smart Teams Assignment Tracker.

Handles reading, saving, and updating assignment persistence in data/assignments.json.
Maintains offline cache, completion tracking, and sync state.
"""

import json
import logging
from pathlib import Path
from typing import Any, Optional

import config

logger = logging.getLogger("SmartAssignmentTracker.storage")


class AssignmentStorage:
    """Manages local JSON persistence for assignments."""

    def __init__(self, file_path: Optional[Path] = None) -> None:
        self.file_path = file_path or config.ASSIGNMENTS_FILE
        self._ensure_storage_exists()

    def _ensure_storage_exists(self) -> None:
        """Ensure parent directory and JSON file exist."""
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            try:
                with open(self.file_path, "w", encoding="utf-8") as f:
                    json.dump([], f, indent=2)
                logger.info("Initialized empty assignments storage at %s", self.file_path)
            except Exception as e:
                logger.error("Failed to initialize assignments storage: %s", e)

    def load_assignments(self) -> list[dict[str, Any]]:
        """Load assignments from local JSON file."""
        if not self.file_path.exists():
            return []

        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
                logger.warning("Storage file %s did not contain a list. Returning empty list.", self.file_path)
                return []
        except json.JSONDecodeError as e:
            logger.error("Corrupted JSON in %s: %s. Attempting recovery.", self.file_path, e)
            return []
        except Exception as e:
            logger.error("Failed to read assignments file: %s", e)
            return []

    def save_assignments(self, assignments: list[dict[str, Any]]) -> bool:
        """Persist list of assignments to local JSON storage."""
        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            temp_file = self.file_path.with_suffix(".tmp")
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(assignments, f, indent=2, ensure_ascii=False)

            # Atomic rename to prevent partial writes
            temp_file.replace(self.file_path)
            logger.info("Saved %d assignment(s) to %s", len(assignments), self.file_path)
            return True
        except Exception as e:
            logger.error("Failed to write assignments to %s: %s", self.file_path, e)
            return False

    def update_assignment_status(
        self,
        assignment_id: str,
        completed: Optional[bool] = None,
        reminder_sent: Optional[bool] = None,
        gcal_event_id: Optional[str] = None,
        gcal_synced: Optional[bool] = None,
        gcal_task_id: Optional[str] = None,
        gcal_task_synced: Optional[bool] = None,
    ) -> bool:
        """Update fields of an existing assignment by ID."""
        assignments = self.load_assignments()
        updated = False

        for asg in assignments:
            if asg.get("id") == assignment_id:
                if completed is not None:
                    asg["completed"] = completed
                if reminder_sent is not None:
                    asg["reminder_sent"] = reminder_sent
                if gcal_event_id is not None:
                    asg["gcal_event_id"] = gcal_event_id
                if gcal_synced is not None:
                    asg["gcal_synced"] = gcal_synced
                if gcal_task_id is not None:
                    asg["gcal_task_id"] = gcal_task_id
                if gcal_task_synced is not None:
                    asg["gcal_task_synced"] = gcal_task_synced
                updated = True
                break

        if updated:
            return self.save_assignments(assignments)

        logger.warning("Assignment with ID %s not found in storage for update.", assignment_id)
        return False

    def clear_assignments(self) -> bool:
        """Clear all stored assignments."""
        return self.save_assignments([])
