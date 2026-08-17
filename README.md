# Smart Teams Assignment Tracker

A modular, desktop checklist application that automatically retrieves assignments from Microsoft Teams (using Microsoft Graph Education APIs or authorized browser fallback), tracks deadlines, and provides desktop notifications.

---

## Features (Planned & Incremental)

- **Microsoft Account Authentication**: Secure OAuth2 via MSAL (VIT Microsoft account).
- **Dual Data Source Support**:
  - Primary: Microsoft Graph API (`/education/me/assignments`).
  - Fallback: Legitimate Selenium browser session if tenant consent restricts Graph access.
- **Local Persistence & Offline Access**: Caches assignments locally in `data/assignments.json`.
- **Deadline Reminders**: Sends desktop notifications 2 days prior to assignment deadlines.
- **Desktop Checklist Widget**: Modern, responsive UI built with `CustomTkinter`.
- **Periodic Background Sync**: Automatically checks for updates via `APScheduler`.

---

## Project Structure

```text
SmartAssignmentTracker/
│
├── main.py                   # Application entry point and orchestrator
├── config.py                 # Centralized configuration and logging setup
├── auth.py                   # (Stage 2) Microsoft Authentication via MSAL
├── teams_api.py              # (Stage 3) Microsoft Graph assignment retrieval
├── browser_fetcher.py        # (Stage 4) Selenium browser fallback fetcher
├── assignment_manager.py     # Central business logic and normalization
├── storage.py                # Local JSON persistence and caching
├── widget.py                 # CustomTkinter desktop checklist GUI
├── scheduler.py              # APScheduler background sync engine
├── notifications.py          # Desktop notification handler
│
├── data/                     # Local data storage (assignments.json)
├── logs/                     # Application logs (app.log)
├── assets/                   # Icons and UI assets
│
├── requirements.txt          # Project dependencies
├── .gitignore                # Git ignore configuration
└── README.md                 # Project documentation
```

---

## Setup & Installation

### 1. Prerequisites
- Python 3.10+ (Tested on Python 3.12)
- Windows OS

### 2. Setup Virtual Environment
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 4. Run Stage 1 Environment Check
```powershell
python main.py
```

---

## Development Status

- [x] **Stage 1**: Project Setup & Environment Check
- [ ] **Stage 2**: Microsoft Graph Feasibility Test & Authentication (`auth.py`, `teams_api.py`)
- [ ] **Stage 3**: Assignment Data Normalization & Local Storage (`storage.py`, `assignment_manager.py`)
- [ ] **Stage 4**: Browser Fallback (if Graph restricted) (`browser_fetcher.py`)
- [ ] **Stage 5**: Desktop Widget GUI (`widget.py`)
- [ ] **Stage 6**: Scheduler & Notifications (`scheduler.py`, `notifications.py`)
- [ ] **Stage 7**: Integration, Offline Handling, and Final Polishing
