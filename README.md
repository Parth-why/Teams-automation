# Smart Teams Assignment Tracker

<p align="center">
  <strong>A Python desktop project for bringing Microsoft Teams assignments and deadlines into one place.</strong>
</p>

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img alt="Microsoft Teams" src="https://img.shields.io/badge/Microsoft%20Teams-6264A7?style=for-the-badge&logo=microsoftteams&logoColor=white" />
  <img alt="Desktop app" src="https://img.shields.io/badge/Desktop-CustomTkinter-2563EB?style=for-the-badge" />
</p>

---

## Overview

**Smart Teams Assignment Tracker** is a modular Python desktop project intended to retrieve assignment information from Microsoft Teams, organise deadlines, and notify students before work is due.

The intended workflow is:

1. Authenticate with an authorised Microsoft account.
2. Retrieve assignment information from Teams.
3. Normalise assignment titles, classes, due dates, and links.
4. Display upcoming work in a desktop checklist.
5. Cache assignment data for temporary network interruptions.
6. Send a reminder two days before a deadline while preventing duplicate notifications.

> **Development status:** The existing project notes identify environment/setup as the completed stage. The integrations and application features below are part of the project plan; do not assume every feature is already implemented.

## Planned capabilities

- Microsoft account authentication using MSAL.
- Microsoft Graph Education API integration, subject to tenant permissions and API availability.
- An authorised browser-automation fallback where appropriate.
- Local JSON persistence and cached assignment data.
- A CustomTkinter desktop checklist.
- Periodic synchronisation with APScheduler.
- Desktop deadline notifications.
- Error handling for authentication, network failures, and incomplete assignment data.

## Architecture

| Module | Responsibility |
|---|---|
| `main.py` | Application entry point and orchestration |
| `config.py` | Configuration and logging |
| `auth.py` | Microsoft authentication |
| `teams_api.py` | Teams / Microsoft Graph retrieval |
| `browser_fetcher.py` | Browser retrieval fallback |
| `assignment_manager.py` | Assignment normalisation and business logic |
| `storage.py` | Local persistence and caching |
| `widget.py` | Desktop checklist interface |
| `scheduler.py` | Periodic background synchronisation |
| `notifications.py` | Deadline notification handling |

Check the source code before relying on the implementation status of an individual module.

## Requirements

- Python 3.10 or newer
- Windows (the current setup targets Windows)
- An authorised Microsoft account
- Microsoft tenant/API permissions when using Microsoft Graph

## Setup

```powershell
git clone https://github.com/Parth-why/Teams-automation.git
cd Teams-automation

python -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
python main.py
```

The current README identifies `main.py` as the project entry point / environment check.

## Development roadmap

- [x] Stage 1 — Project setup and environment check
- [ ] Stage 2 — Microsoft Graph feasibility and authentication
- [ ] Stage 3 — Assignment normalisation and local storage
- [ ] Stage 4 — Browser fallback, if required and permitted
- [ ] Stage 5 — Desktop checklist interface
- [ ] Stage 6 — Scheduler and notifications
- [ ] Stage 7 — Integration, offline handling, and polish

Update this checklist as each milestone is implemented and tested.

## Privacy and security

- Use only accounts and Teams data you are authorised to access.
- Never commit credentials, access tokens, client secrets, or personal assignment data.
- Keep local runtime data and logs out of tracked source files where possible.
- Review Microsoft tenant policies before enabling API or browser automation.

## Project goal

Make assignment tracking less dependent on repeatedly checking Teams manually, while keeping the application modular, understandable, and maintainable.

---

<p align="center">Built by <a href="https://github.com/Parth-why">Parth</a></p>
