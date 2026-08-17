"""Desktop GUI Checklist Widget for Smart Teams Assignment Tracker.

Built with CustomTkinter for a modern dark-mode responsive desktop interface.
Allows interactive checklist completion, Teams assignment fetching, Google Calendar/Tasks sync,
and local filtering.
"""

import logging
import threading
import tkinter as tk
from datetime import datetime, timedelta
from pathlib import Path
from tkinter import messagebox
from typing import Any, Optional

import customtkinter as ctk

import config
from assignment_manager import AssignmentManager
from browser_fetcher import TeamsBrowserFetcher
from google_calendar_sync import GoogleCalendarSync, clean_subject_name, generate_ics_calendar

logger = logging.getLogger("SmartAssignmentTracker.widget")

# Appearance Configuration
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class AssignmentCard(ctk.CTkFrame):
    """Interactive card representation for a single assignment."""

    def __init__(
        self,
        master: Any,
        assignment: dict[str, Any],
        on_toggle_completion: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(master, corner_radius=10, fg_color=("#2b2d30", "#1e1f22"), **kwargs)
        self.assignment = assignment
        self.on_toggle_completion = on_toggle_completion
        self.is_completed = assignment.get("completed", False)

        self._build_ui()

    def _build_ui(self) -> None:
        self.grid_columnconfigure(1, weight=1)

        # 1. Interactive Checkbox
        self.check_var = ctk.BooleanVar(value=self.is_completed)
        self.checkbox = ctk.CTkCheckBox(
            self,
            text="",
            variable=self.check_var,
            width=24,
            height=24,
            corner_radius=6,
            command=self._handle_check_toggle,
        )
        self.checkbox.grid(row=0, column=0, rowspan=2, padx=(14, 10), pady=12, sticky="w")

        # 2. Subject Badge & Metadata Row
        clean_subj = clean_subject_name(self.assignment.get("subject", ""))
        self.badge_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.badge_frame.grid(row=0, column=1, padx=0, pady=(10, 2), sticky="w")

        self.subject_pill = ctk.CTkLabel(
            self.badge_frame,
            text=f"  {clean_subj}  ",
            font=ctk.CTkFont(size=11, weight="bold"),
            corner_radius=6,
            fg_color=("#1976D2", "#1565C0"),
            text_color="#FFFFFF",
            height=20,
        )
        self.subject_pill.pack(side="left", padx=(0, 8))

        # Google Sync Status Badge
        if self.assignment.get("gcal_synced") or self.assignment.get("gcal_task_synced"):
            self.sync_pill = ctk.CTkLabel(
                self.badge_frame,
                text=" 📅 Synced to Google ",
                font=ctk.CTkFont(size=10, weight="bold"),
                corner_radius=6,
                fg_color=("#2E7D32", "#1B5E20"),
                text_color="#C8E6C9",
                height=18,
            )
            self.sync_pill.pack(side="left", padx=4)

        # 3. Assignment Title
        title_text = self.assignment.get("title", "Untitled Assignment")
        self.title_label = ctk.CTkLabel(
            self,
            text=title_text,
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w",
            justify="left",
            wraplength=520,
        )
        self.title_label.grid(row=1, column=1, padx=0, pady=(0, 10), sticky="w")

        # 4. Due Date & Time Badge (Right side)
        self.due_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.due_frame.grid(row=0, column=2, rowspan=2, padx=16, pady=10, sticky="e")

        due_text = self._format_due_display()
        due_bg, due_fg = self._get_due_color_theme()

        self.due_label = ctk.CTkLabel(
            self.due_frame,
            text=due_text,
            font=ctk.CTkFont(size=12, weight="bold"),
            corner_radius=8,
            fg_color=due_bg,
            text_color=due_fg,
            height=28,
            padx=10,
        )
        self.due_label.pack(side="right")

        self._apply_completion_visuals()

    def _format_due_display(self) -> str:
        """Format clean due date and time string."""
        due_date = self.assignment.get("due_date", "")
        due_time = self.assignment.get("due_time", "11:59 PM")
        if not due_date:
            return "No Due Date"

        try:
            dt = datetime.strptime(due_date, "%Y-%m-%d")
            formatted_date = dt.strftime("%b %d")
            return f"Due: {formatted_date} at {due_time}"
        except Exception:
            return f"Due: {due_date} {due_time}"

    def _get_due_color_theme(self) -> tuple[str, str]:
        """Determine color coding based on deadline urgency."""
        if self.is_completed:
            return ("#2E7D32", "#FFFFFF")

        due_date = self.assignment.get("due_date", "")
        if not due_date:
            return ("#424242", "#E0E0E0")

        try:
            dt = datetime.strptime(due_date, "%Y-%m-%d").date()
            today = datetime.now().date()
            diff_days = (dt - today).days

            if diff_days < 0:
                # Overdue
                return ("#B71C1C", "#FFCDD2")
            elif diff_days == 0:
                # Due Today
                return ("#C62828", "#FFCDD2")
            elif diff_days <= 3:
                # Due Soon (≤ 3 Days)
                return ("#E65100", "#FFE0B2")
            else:
                return ("#37474F", "#ECEFF1")
        except Exception:
            return ("#37474F", "#ECEFF1")

    def _handle_check_toggle(self) -> None:
        """Handle user clicking checkbox."""
        new_state = self.check_var.get()
        self.is_completed = new_state
        self.assignment["completed"] = new_state
        self._apply_completion_visuals()
        self.on_toggle_completion(self.assignment["id"], new_state)

    def _apply_completion_visuals(self) -> None:
        """Update styling for completed vs pending states."""
        if self.is_completed:
            self.title_label.configure(text_color="#888888")
            self.due_label.configure(
                text="✓ Completed",
                fg_color="#2E7D32",
                text_color="#FFFFFF",
            )
        else:
            self.title_label.configure(text_color=("#000000", "#FFFFFF"))
            due_text = self._format_due_display()
            due_bg, due_fg = self._get_due_color_theme()
            self.due_label.configure(text=due_text, fg_color=due_bg, text_color=due_fg)


class TrackerApp(ctk.CTk):
    """Main Desktop UI Application for Teams Assignment Tracker."""

    def __init__(self) -> None:
        super().__init__()

        self.manager = AssignmentManager()
        self.gcal_sync = GoogleCalendarSync()
        self.assignments: list[dict[str, Any]] = []
        self.filtered_assignments: list[dict[str, Any]] = []

        # Configure Main Window
        self.title("Smart Teams Assignment Tracker")
        self.geometry("980x740")
        self.minsize(860, 600)

        self._create_layout()
        self.load_data()

    def _create_layout(self) -> None:
        """Build responsive UI layout structure."""
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # -------------------------------------------------------------
        # Section 1: Header Bar & Stats
        # -------------------------------------------------------------
        self.header_frame = ctk.CTkFrame(self, corner_radius=0, fg_color=("#1f1f23", "#141416"), height=80)
        self.header_frame.grid(row=0, column=0, sticky="ew")
        self.header_frame.grid_columnconfigure(1, weight=1)

        # Left: App Icon & Title
        title_box = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        title_box.grid(row=0, column=0, padx=20, pady=14, sticky="w")

        app_title = ctk.CTkLabel(
            title_box,
            text="🎓 Smart Teams Tracker",
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        app_title.pack(anchor="w")

        app_subtitle = ctk.CTkLabel(
            title_box,
            text="Microsoft Teams Assignments & Google Calendar Sync",
            font=ctk.CTkFont(size=12),
            text_color="#9E9E9E",
        )
        app_subtitle.pack(anchor="w")

        # Right: Stat Pills
        self.stats_box = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.stats_box.grid(row=0, column=1, padx=20, pady=14, sticky="e")

        self.pill_total = self._create_stat_pill(self.stats_box, "Total: 0", "#37474F")
        self.pill_pending = self._create_stat_pill(self.stats_box, "Pending: 0", "#1565C0")
        self.pill_due_soon = self._create_stat_pill(self.stats_box, "Due Soon: 0", "#E65100")
        self.pill_done = self._create_stat_pill(self.stats_box, "Completed: 0", "#2E7D32")

        # -------------------------------------------------------------
        # Section 2: Action Toolbar & Search / Filters
        # -------------------------------------------------------------
        self.toolbar_frame = ctk.CTkFrame(self, corner_radius=0, fg_color=("#2b2d30", "#1a1b1e"))
        self.toolbar_frame.grid(row=1, column=0, sticky="ew", padx=0, pady=0)
        self.toolbar_frame.grid_columnconfigure(4, weight=1)

        # Fetch Button
        self.btn_fetch = ctk.CTkButton(
            self.toolbar_frame,
            text="🔄 Fetch from Teams",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#1976D2",
            hover_color="#1565C0",
            width=160,
            height=36,
            command=self._handle_fetch_teams_threaded,
        )
        self.btn_fetch.grid(row=0, column=0, padx=(16, 8), pady=12)

        # Sync Calendar & Tasks Button
        self.btn_sync_gcal = ctk.CTkButton(
            self.toolbar_frame,
            text="📅 Sync to Google",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#2E7D32",
            hover_color="#1B5E20",
            width=160,
            height=36,
            command=self._handle_sync_gcal_threaded,
        )
        self.btn_sync_gcal.grid(row=0, column=1, padx=8, pady=12)

        # Clear All Button
        self.btn_clear = ctk.CTkButton(
            self.toolbar_frame,
            text="🧹 Clear All",
            font=ctk.CTkFont(size=12),
            fg_color="#424242",
            hover_color="#616161",
            width=100,
            height=36,
            command=self._handle_clear_assignments,
        )
        self.btn_clear.grid(row=0, column=2, padx=8, pady=12)

        # Export .ICS Button
        self.btn_export_ics = ctk.CTkButton(
            self.toolbar_frame,
            text="📥 Export .ICS",
            font=ctk.CTkFont(size=12),
            fg_color="#37474F",
            hover_color="#455A64",
            width=110,
            height=36,
            command=self._handle_export_ics,
        )
        self.btn_export_ics.grid(row=0, column=3, padx=8, pady=12)

        # Search Bar & Filter (Right aligned)
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._apply_filters())
        self.search_entry = ctk.CTkEntry(
            self.toolbar_frame,
            placeholder_text="🔍 Search subject or title...",
            textvariable=self.search_var,
            width=220,
            height=36,
        )
        self.search_entry.grid(row=0, column=4, padx=(8, 16), pady=12, sticky="e")

        # Filter Segmented Button
        self.filter_var = ctk.StringVar(value="All")
        self.filter_seg = ctk.CTkSegmentedButton(
            self.toolbar_frame,
            values=["All", "Pending", "Completed", "Due Soon"],
            variable=self.filter_var,
            command=lambda _: self._apply_filters(),
            height=32,
        )
        self.filter_seg.grid(row=0, column=5, padx=(0, 16), pady=12, sticky="e")

        # -------------------------------------------------------------
        # Section 3: Scrollable Assignment Card List
        # -------------------------------------------------------------
        self.scroll_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            corner_radius=0,
        )
        self.scroll_frame.grid(row=2, column=0, sticky="nsew", padx=16, pady=12)
        self.scroll_frame.grid_columnconfigure(0, weight=1)

        # -------------------------------------------------------------
        # Section 4: Status Bar at Bottom
        # -------------------------------------------------------------
        self.status_frame = ctk.CTkFrame(self, corner_radius=0, height=28, fg_color=("#1f1f23", "#141416"))
        self.status_frame.grid(row=3, column=0, sticky="ew")
        self.status_frame.grid_columnconfigure(0, weight=1)

        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Ready | Storage: data/assignments.json",
            font=ctk.CTkFont(size=11),
            text_color="#B0BEC5",
            anchor="w",
        )
        self.status_label.grid(row=0, column=0, padx=16, pady=4, sticky="w")

    def _create_stat_pill(self, parent: Any, text: str, color: str) -> ctk.CTkLabel:
        pill = ctk.CTkLabel(
            parent,
            text=f"  {text}  ",
            font=ctk.CTkFont(size=11, weight="bold"),
            corner_radius=8,
            fg_color=color,
            text_color="#FFFFFF",
            height=26,
        )
        pill.pack(side="left", padx=4)
        return pill

    def load_data(self) -> None:
        """Load assignments from local storage and render."""
        self.assignments = self.manager.get_all_assignments(sort_by_due=True)
        self._update_stats()
        self._apply_filters()

    def _update_stats(self) -> None:
        """Update top bar stat pills."""
        total = len(self.assignments)
        completed = sum(1 for a in self.assignments if a.get("completed", False))
        pending = total - completed

        today = datetime.now().date()
        due_soon = 0
        for a in self.assignments:
            if not a.get("completed", False) and a.get("due_date"):
                try:
                    dt = datetime.strptime(a["due_date"], "%Y-%m-%d").date()
                    if 0 <= (dt - today).days <= 3:
                        due_soon += 1
                except Exception:
                    pass

        self.pill_total.configure(text=f"  Total: {total}  ")
        self.pill_pending.configure(text=f"  Pending: {pending}  ")
        self.pill_due_soon.configure(text=f"  Due Soon: {due_soon}  ")
        self.pill_done.configure(text=f"  Completed: {completed}  ")
        self.status_label.configure(text=f"Ready | {total} assignments loaded from {config.ASSIGNMENTS_FILE}")

    def _apply_filters(self) -> None:
        """Filter and render assignments matching search text and selected filter category."""
        query = self.search_var.get().lower().strip()
        filter_mode = self.filter_var.get()

        today = datetime.now().date()
        filtered: list[dict[str, Any]] = []

        for asg in self.assignments:
            title = asg.get("title", "").lower()
            subject = asg.get("subject", "").lower()
            clean_sub = clean_subject_name(asg.get("subject", "")).lower()
            is_done = asg.get("completed", False)

            # Search match
            if query and (query not in title and query not in subject and query not in clean_sub):
                continue

            # Category filter
            if filter_mode == "Pending" and is_done:
                continue
            elif filter_mode == "Completed" and not is_done:
                continue
            elif filter_mode == "Due Soon":
                if is_done or not asg.get("due_date"):
                    continue
                try:
                    dt = datetime.strptime(asg["due_date"], "%Y-%m-%d").date()
                    if not (0 <= (dt - today).days <= 3):
                        continue
                except Exception:
                    continue

            filtered.append(asg)

        self.filtered_assignments = filtered
        self._render_cards()

    def _render_cards(self) -> None:
        """Clear and re-render assignment cards in scroll container."""
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        if not self.filtered_assignments:
            empty_box = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
            empty_box.pack(pady=60)

            empty_label = ctk.CTkLabel(
                empty_box,
                text="🎉 No assignments found in this view!",
                font=ctk.CTkFont(size=16, weight="bold"),
                text_color="#B0BEC5",
            )
            empty_label.pack(pady=8)

            hint_label = ctk.CTkLabel(
                empty_box,
                text="Click 'Fetch from Teams' to pull your active school assignments.",
                font=ctk.CTkFont(size=12),
                text_color="#78909C",
            )
            hint_label.pack()
            return

        for idx, asg in enumerate(self.filtered_assignments):
            card = AssignmentCard(
                self.scroll_frame,
                assignment=asg,
                on_toggle_completion=self._on_assignment_toggle,
            )
            card.pack(fill="x", padx=4, pady=6)

    def _on_assignment_toggle(self, assignment_id: str, is_completed: bool) -> None:
        """Handle local checkbox toggle."""
        self.manager.set_completion_status(assignment_id, is_completed)
        self._update_stats()

    def _handle_fetch_teams_threaded(self) -> None:
        """Run Selenium browser fetcher in a background thread to prevent UI freezing."""
        self.btn_fetch.configure(state="disabled", text="⏳ Fetching...")
        self.status_label.configure(text="Opening Microsoft Teams session in browser. Please sign in...")

        def target() -> None:
            try:
                with TeamsBrowserFetcher() as fetcher:
                    success = fetcher.login_and_navigate(interactive_wait=True)
                    if success:
                        raw = fetcher.fetch_assignments()
                        self.manager.sync_new_assignments(raw)
                        self.after(0, lambda: self._on_fetch_complete(len(raw)))
                    else:
                        self.after(0, lambda: self._on_fetch_error("Teams session was cancelled or timed out."))
            except Exception as e:
                logger.error("Teams fetch error: %s", e)
                self.after(0, lambda: self._on_fetch_error(str(e)))

        thread = threading.Thread(target=target, daemon=True)
        thread.start()

    def _on_fetch_complete(self, count: int) -> None:
        self.btn_fetch.configure(state="normal", text="🔄 Fetch from Teams")
        self.load_data()
        messagebox.showinfo("Fetch Complete", f"Successfully retrieved {count} assignments from Microsoft Teams!")

    def _on_fetch_error(self, err_msg: str) -> None:
        self.btn_fetch.configure(state="normal", text="🔄 Fetch from Teams")
        self.status_label.configure(text=f"Fetch failed: {err_msg}")
        messagebox.showerror("Fetch Error", f"Could not fetch assignments:\n{err_msg}")

    def _handle_sync_gcal_threaded(self) -> None:
        """Run Google Calendar & Tasks sync in background thread."""
        if not self.gcal_sync.is_available():
            messagebox.showwarning(
                "Credentials Missing",
                "Please ensure 'credentials.json' is placed in the project folder to sync with Google Calendar.",
            )
            return

        self.btn_sync_gcal.configure(state="disabled", text="⏳ Syncing...")
        self.status_label.configure(text="Syncing assignments with Google Calendar & Google Tasks...")

        def target() -> None:
            try:
                stats = self.gcal_sync.sync_assignments(self.assignments)
                self.after(0, lambda: self._on_sync_complete(stats))
            except Exception as e:
                logger.error("Google Sync error: %s", e)
                self.after(0, lambda: self._on_sync_error(str(e)))

        thread = threading.Thread(target=target, daemon=True)
        thread.start()

    def _on_sync_complete(self, stats: dict[str, Any]) -> None:
        self.btn_sync_gcal.configure(state="normal", text="📅 Sync to Google")
        self.load_data()
        msg = (
            f"Google Calendar & Tasks Synced!\n\n"
            f"• Calendar 1-Day Advance Events: {stats.get('events_created', 0)} created, {stats.get('events_updated', 0)} updated\n"
            f"• Google Tasks 9 AM Checklists: {stats.get('tasks_created', 0)} created, {stats.get('tasks_updated', 0)} updated"
        )
        messagebox.showinfo("Sync Success", msg)

    def _on_sync_error(self, err_msg: str) -> None:
        self.btn_sync_gcal.configure(state="normal", text="📅 Sync to Google")
        self.status_label.configure(text=f"Sync failed: {err_msg}")
        messagebox.showerror("Sync Error", f"Google Calendar Sync failed:\n{err_msg}")

    def _handle_clear_assignments(self) -> None:
        """Clear all stored assignments upon confirmation."""
        confirm = messagebox.askyesno(
            "Clear All Assignments",
            "Are you sure you want to clear all stored assignments from your local database?\n(This will reset your checklist)",
        )
        if confirm:
            self.manager.clear_all_assignments()
            self.load_data()
            messagebox.showinfo("Cleared", "All local assignments have been cleared.")

    def _handle_export_ics(self) -> None:
        """Export current assignments to standard iCalendar feed."""
        out = generate_ics_calendar(self.assignments)
        messagebox.showinfo(
            "iCalendar Exported",
            f"Calendar feed exported successfully to:\n{out}\n\nYou can import this directly into Google Calendar or Outlook.",
        )


def launch_gui() -> None:
    """Launch the CustomTkinter desktop checklist widget."""
    app = TrackerApp()
    app.mainloop()


if __name__ == "__main__":
    launch_gui()
