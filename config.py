"""Configuration module for Smart Teams Assignment Tracker.

Centralizes paths, application settings, logging setup, and authentication
configuration without hardcoding secrets.
"""

import logging
import os
from pathlib import Path

# Base Paths
BASE_DIR: Path = Path(__file__).resolve().parent
DATA_DIR: Path = BASE_DIR / "data"
LOGS_DIR: Path = BASE_DIR / "logs"
ASSETS_DIR: Path = BASE_DIR / "assets"

# Data & Log Files
ASSIGNMENTS_FILE: Path = DATA_DIR / "assignments.json"
TOKEN_CACHE_FILE: Path = DATA_DIR / "token_cache.bin"
BROWSER_PROFILE_DIR: Path = DATA_DIR / "browser_profile"
LOG_FILE: Path = LOGS_DIR / "app.log"
ICON_FILE: Path = ASSETS_DIR / "icon.ico"
ENV_FILE: Path = BASE_DIR / ".env"

# Microsoft Teams Web URLs
TEAMS_WEB_URL: str = "https://teams.microsoft.com"
TEAMS_ASSIGNMENTS_URL: str = "https://teams.microsoft.com/_#/assignments"

# Application Settings
APP_NAME: str = "Smart Teams Assignment Tracker"
APP_VERSION: str = "1.0.0"

# Sync & Notification Timing
SYNC_INTERVAL_MINUTES: int = int(os.getenv("SYNC_INTERVAL_MINUTES", "30"))
REMINDER_DAYS_BEFORE_DUE: int = int(os.getenv("REMINDER_DAYS_BEFORE_DUE", "2"))


def load_env_file() -> None:
    """Lightweight loader for .env file if present without external dependencies."""
    if ENV_FILE.exists():
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip("'\"")
                    if key and key not in os.environ:
                        os.environ[key] = val


# Load environment variables from .env if present
load_env_file()

# Microsoft Authentication Settings (Configurable via Environment Variables, .env, or CLI)
# Must be a registered Microsoft Entra (Azure AD) Application (client) ID.
# No first-party or hardcoded fallback client IDs.
AZURE_CLIENT_ID: str = os.getenv("AZURE_CLIENT_ID", "").strip()
AZURE_TENANT_ID: str = os.getenv("AZURE_TENANT_ID", "common").strip()
AZURE_AUTHORITY: str = f"https://login.microsoftonline.com/{AZURE_TENANT_ID}"

# Graph API Scopes
# EduAssignments.ReadBasic: Reads basic details (title, due date, status)
# EduAssignments.Read: Reads full assignment info including instructions and submissions
GRAPH_SCOPES: list[str] = [
    "User.Read",
    "EduAssignments.ReadBasic",
]

# Microsoft Graph Endpoints
GRAPH_ENDPOINT_ME: str = "https://graph.microsoft.com/v1.0/me"
GRAPH_ENDPOINT_ASSIGNMENTS: str = "https://graph.microsoft.com/v1.0/education/me/assignments"


def ensure_directories() -> None:
    """Ensure all required application directories exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)


def setup_logging(log_level: int = logging.INFO) -> logging.Logger:
    """Configure application-wide logging to console and log file."""
    ensure_directories()

    logger = logging.getLogger("SmartAssignmentTracker")
    logger.setLevel(log_level)

    # Avoid duplicate handlers if setup_logging is called multiple times
    if not logger.handlers:
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d): %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # File Handler
        file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Console Handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger
