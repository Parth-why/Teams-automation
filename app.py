"""Flask Web Application - Command & Sync Hub for Teams & Google Tasks.

Provides clean reset state on startup so the dashboard, graphs, and urgency radar
populate only after an active scan is performed in the session.
"""

import logging
import threading
from datetime import datetime
from typing import Any

from flask import Flask, jsonify, render_template, request, send_file

import config
from assignment_manager import AssignmentManager
from browser_fetcher import TeamsBrowserFetcher
from google_calendar_sync import GoogleCalendarSync, clean_subject_name, generate_ics_calendar

logger = config.setup_logging()

app = Flask(
    __name__,
    template_folder=str(config.BASE_DIR / "templates"),
    static_folder=str(config.BASE_DIR / "static"),
)

manager = AssignmentManager()
gcal_sync = GoogleCalendarSync()

# State Tracking
fetch_lock = threading.Lock()
is_fetching = False
has_scanned_in_session = False  # Starts clean on launch
activity_logs: list[dict[str, str]] = []


def add_log(msg: str, level: str = "info") -> None:
    """Add a timestamped entry to the web activity log."""
    now_str = datetime.now().strftime("%I:%M:%S %p")
    activity_logs.insert(0, {"time": now_str, "message": msg, "level": level})
    if len(activity_logs) > 50:
        activity_logs.pop()


# Initial log
add_log("Dashboard initialized in clean state. Ready for scanning.", "info")


@app.route("/")
def index() -> Any:
    """Render the executive Command & Sync Hub dashboard."""
    return render_template("index.html")


@app.route("/api/status", methods=["GET"])
def get_status() -> Any:
    """Return high-level analytics, subject distribution, and sync status."""
    assignments = manager.get_all_assignments(sort_by_due=True)
    today = datetime.now().date()

    total = len(assignments)
    synced_tasks = sum(1 for a in assignments if a.get("gcal_task_synced", False))

    if total == 0:
        return jsonify({
            "success": True,
            "has_scanned": False,
            "is_fetching": is_fetching,
            "gcal_ready": gcal_sync.is_available(),
            "stats": {
                "total_tracked": 0,
                "synced_tasks": 0,
                "urgent_48h": 0,
                "this_week": 0,
                "later": 0,
            },
            "subject_breakdown": {},
            "activity_logs": activity_logs,
        })

    # Subject Workload Breakdown
    subject_counts: dict[str, int] = {}
    for a in assignments:
        s_name = clean_subject_name(a.get("subject", ""))
        subject_counts[s_name] = subject_counts.get(s_name, 0) + 1

    # Urgency Breakdown
    due_48h = 0
    due_this_week = 0
    due_later = 0

    for a in assignments:
        due_date = a.get("due_date")
        if due_date:
            try:
                dt = datetime.strptime(due_date, "%Y-%m-%d").date()
                diff = (dt - today).days
                if diff <= 2:
                    due_48h += 1
                elif diff <= 7:
                    due_this_week += 1
                else:
                    due_later += 1
            except Exception:
                due_later += 1
        else:
            due_later += 1

    return jsonify({
        "success": True,
        "has_scanned": True,
        "is_fetching": is_fetching,
        "gcal_ready": gcal_sync.is_available(),
        "stats": {
            "total_tracked": total,
            "synced_tasks": synced_tasks,
            "urgent_48h": due_48h,
            "this_week": due_this_week,
            "later": due_later,
        },
        "subject_breakdown": subject_counts,
        "activity_logs": activity_logs,
    })


@app.route("/api/scan-teams", methods=["POST"])
def scan_teams() -> Any:
    """Scan and extract visible assignments from Microsoft Teams into local database ONLY."""
    global is_fetching, has_scanned_in_session

    if is_fetching:
        return jsonify({"success": False, "message": "Scan is already in progress."}), 409

    def run_process() -> None:
        global is_fetching, has_scanned_in_session
        with fetch_lock:
            is_fetching = True
            add_log("Opening Microsoft Teams browser session to scan assignments...", "info")
            try:
                with TeamsBrowserFetcher() as fetcher:
                    ok = fetcher.login_and_navigate(auto_navigate=True)
                    if ok:
                        raw = fetcher.fetch_assignments()
                        all_asgs, newly_added = manager.sync_new_assignments(raw)
                        has_scanned_in_session = True
                        add_log(f"Scanned {len(all_asgs)} active assignments from Teams ({len(newly_added)} new).", "success")
                        generate_ics_calendar(all_asgs)
                    else:
                        add_log("Teams session cancelled or timed out.", "warning")
            except Exception as e:
                logger.error("Scan error: %s", e)
                add_log(f"Error scanning Teams: {e}", "error")
            finally:
                is_fetching = False

    t = threading.Thread(target=run_process, daemon=True)
    t.start()

    return jsonify({"success": True, "message": "Teams automated scanning started in browser."})


@app.route("/api/sync-google", methods=["POST"])
def sync_google() -> Any:
    """Explicitly sync tracked assignments to Google Tasks."""
    global has_scanned_in_session

    if not gcal_sync.is_available():
        add_log("Sync failed: Google credentials.json not found.", "error")
        return jsonify({"success": False, "error": "credentials.json not found."}), 400

    assignments = manager.get_all_assignments()
    if not assignments:
        add_log("No assignments found in local database to sync. Please click 'Scan Teams' first.", "warning")
        return jsonify({"success": False, "error": "No assignments to sync. Scan Teams first."}), 400

    has_scanned_in_session = True
    add_log(f"Starting Google Tasks sync for {len(assignments)} assignments...", "info")
    stats = gcal_sync.sync_assignments(assignments)
    add_log(f"Google Tasks synced: {stats['tasks_created']} created, {stats['tasks_updated']} updated.", "success")

    return jsonify({"success": True, "stats": stats})


@app.route("/api/clear-google", methods=["POST"])
def clear_google() -> Any:
    """Delete all synced tasks from Google Tasks while preserving local scanned assignments in database."""
    assignments = manager.get_all_assignments()
    add_log("Clearing synced tasks from Google Tasks / Calendar...", "info")

    del_stats = gcal_sync.clear_all_synced_items(assignments)

    add_log(f"Cleared Google Tasks: Deleted {del_stats['tasks_deleted']} cloud task(s). All {len(assignments)} scanned assignments safely preserved in local database.", "success")

    return jsonify({
        "success": True,
        "message": f"Deleted {del_stats['tasks_deleted']} task(s) from Google Calendar/Tasks. Scanned assignments preserved in database.",
        "stats": del_stats,
    })


@app.route("/api/export-ics", methods=["GET"])
def export_ics() -> Any:
    """Download standard iCalendar feed."""
    assignments = manager.get_all_assignments()
    out_path = generate_ics_calendar(assignments)
    add_log("Exported offline iCalendar (.ics) feed.", "info")
    return send_file(
        out_path,
        as_attachment=True,
        download_name="teams_assignments.ics",
        mimetype="text/calendar",
    )


def run_web_app(host: str = "127.0.0.1", port: int = 5000) -> None:
    """Start the Flask web server and open browser."""
    import webbrowser
    url = f"http://{host}:{port}"
    print("\n" + "=" * 70)
    print(" 🚀 SMART TEAMS & GOOGLE TASKS SYNC HUB - WEB APPLICATION")
    print("=" * 70)
    print(f" URL: {url}")
    print(" Press Ctrl+C in terminal to stop server.")
    print("=" * 70 + "\n")
    webbrowser.open(url)
    app.run(host=host, port=port, debug=False)


if __name__ == "__main__":
    run_web_app()
