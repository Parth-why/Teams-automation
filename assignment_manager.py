"""Central assignment business logic and normalization manager.

Manages sorting, state synchronization, deduplication, and completion status.
"""

import logging
from datetime import datetime
from typing import Any, Optional

from storage import AssignmentStorage

logger = logging.getLogger("SmartAssignmentTracker.manager")


class AssignmentManager:
    """Orchestrates assignment state, sorting, and synchronization."""

    def __init__(self, storage: Optional[AssignmentStorage] = None) -> None:
        self.storage = storage or AssignmentStorage()

    def get_all_assignments(self, sort_by_due: bool = True, active_only: bool = True) -> list[dict[str, Any]]:
        """Retrieve stored assignments, optionally filtering out past assignments and sorting by due date."""
        assignments = self.storage.load_assignments()
        if active_only:
            today_str = datetime.now().strftime("%Y-%m-%d")
            assignments = [a for a in assignments if not a.get("due_date") or a.get("due_date") >= today_str]

        if sort_by_due:
            return self.sort_assignments_by_due_date(assignments)
        return assignments

    def sync_new_assignments(self, incoming: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Merge incoming assignments from Teams with stored assignments.

        Preserves user's local completion status, reminder status, and Google Calendar/Task IDs.
        Filters out past assignments.
        Returns (all_merged_assignments, newly_added_assignments).
        """
        today_str = datetime.now().strftime("%Y-%m-%d")
        existing = {
            asg["id"]: asg for asg in self.storage.load_assignments()
            if not asg.get("due_date") or asg.get("due_date") >= today_str
        }
        newly_added: list[dict[str, Any]] = []

        for item in incoming:
            # Skip past assignments
            if item.get("due_date") and item.get("due_date") < today_str:
                continue

            item_id = item["id"]
            if item_id in existing:
                prev = existing[item_id]
                item["completed"] = prev.get("completed", False)
                item["reminder_sent"] = prev.get("reminder_sent", False)
                item["gcal_event_id"] = prev.get("gcal_event_id", "")
                item["gcal_synced"] = prev.get("gcal_synced", False)
                item["gcal_task_id"] = prev.get("gcal_task_id", "")
                item["gcal_task_synced"] = prev.get("gcal_task_synced", False)
                existing[item_id] = item
            else:
                item["completed"] = False
                item["reminder_sent"] = False
                item["gcal_event_id"] = ""
                item["gcal_synced"] = False
                item["gcal_task_id"] = ""
                item["gcal_task_synced"] = False
                existing[item_id] = item
                newly_added.append(item)

        merged_list = list(existing.values())
        sorted_list = self.sort_assignments_by_due_date(merged_list)
        self.storage.save_assignments(sorted_list)

        logger.info(
            "Sync complete. Total active: %d, Newly added: %d",
            len(sorted_list),
            len(newly_added),
        )
        return sorted_list, newly_added

    def set_completion_status(self, assignment_id: str, completed: bool) -> bool:
        """Toggle local completion state for an assignment."""
        return self.storage.update_assignment_status(assignment_id, completed=completed)

    def clear_all_assignments(self) -> bool:
        """Clear all stored assignments from local database."""
        return self.storage.clear_assignments()

    @staticmethod
    def sort_assignments_by_due_date(assignments: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Sort assignments with nearest deadline first, missing dates at the bottom."""
        def get_sort_key(asg: dict[str, Any]) -> tuple[int, str, str]:
            iso_datetime = asg.get("due_datetime_iso") or ""
            due_date = asg.get("due_date") or ""
            key_str = iso_datetime or due_date
            if not key_str:
                return (1, "9999-12-31", asg.get("title", ""))
            return (0, key_str, asg.get("title", ""))

        return sorted(assignments, key=get_sort_key)
