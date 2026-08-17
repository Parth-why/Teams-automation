"""Microsoft Graph API client module for Smart Teams Assignment Tracker.

Retrieves assignments from Microsoft Teams Education Graph endpoints, parses
responses, handles API errors, and normalizes data into the common format.
"""

import logging
from typing import Any, Optional

import requests

import config

logger = logging.getLogger("SmartAssignmentTracker.teams_api")


class GraphAPIResult:
    """Encapsulates the response of a Graph API operation."""

    def __init__(
        self,
        success: bool,
        status_code: int = 0,
        data: Optional[Any] = None,
        assignments: Optional[list[dict[str, Any]]] = None,
        error: Optional[str] = None,
        error_details: Optional[str] = None,
        requires_admin_consent: bool = False,
    ) -> None:
        self.success = success
        self.status_code = status_code
        self.data = data
        self.assignments = assignments or []
        self.error = error
        self.error_details = error_details
        self.requires_admin_consent = requires_admin_consent

    def __repr__(self) -> str:
        return f"<GraphAPIResult success={self.success} status={self.status_code} items={len(self.assignments)}>"


class TeamsGraphClient:
    """Client for Microsoft Graph Education API."""

    def __init__(self, access_token: str) -> None:
        self.access_token = access_token
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": f"{config.APP_NAME}/{config.APP_VERSION}",
        })

    def get_user_profile(self) -> GraphAPIResult:
        """Fetch basic profile of the authenticated user to verify token validity."""
        url = config.GRAPH_ENDPOINT_ME
        logger.debug("Fetching user profile from %s", url)

        try:
            response = self.session.get(url, timeout=15)
            if response.status_code == 200:
                data = response.json()
                logger.info("Retrieved profile for %s (%s)", data.get("displayName"), data.get("userPrincipalName"))
                return GraphAPIResult(success=True, status_code=200, data=data)

            return self._handle_error_response(response, "get_user_profile")
        except requests.exceptions.RequestException as e:
            logger.error("Network exception fetching user profile: %s", e)
            return GraphAPIResult(
                success=False,
                error="NetworkError",
                error_details=str(e),
            )

    def get_assignments(self) -> GraphAPIResult:
        """Retrieve education assignments assigned to the current user."""
        url = config.GRAPH_ENDPOINT_ASSIGNMENTS
        logger.info("Querying Microsoft Graph Education assignments: %s", url)

        try:
            response = self.session.get(url, timeout=20)
            if response.status_code == 200:
                raw_data = response.json()
                raw_items = raw_data.get("value", [])
                logger.info("Graph API returned %d raw assignment item(s)", len(raw_items))

                normalized = [self.normalize_assignment(item) for item in raw_items]
                return GraphAPIResult(
                    success=True,
                    status_code=200,
                    data=raw_data,
                    assignments=normalized,
                )

            return self._handle_error_response(response, "get_assignments")
        except requests.exceptions.RequestException as e:
            logger.error("Network exception querying assignments: %s", e)
            return GraphAPIResult(
                success=False,
                error="NetworkError",
                error_details=str(e),
            )

    def _handle_error_response(self, response: requests.Response, operation: str) -> GraphAPIResult:
        """Parse error status codes and JSON payloads from Microsoft Graph."""
        status_code = response.status_code
        error_msg = f"HTTP {status_code} Error"
        error_details = response.text

        requires_consent = False
        try:
            err_json = response.json()
            inner_error = err_json.get("error", {})
            error_code = inner_error.get("code", "")
            error_details = inner_error.get("message", response.text)
            error_msg = f"{error_code}: {error_details}" if error_code else error_details

            # Identify permissions / admin consent denial
            if status_code in (401, 403) and any(
                term in error_details.lower()
                for term in ["consent", "accessdenied", "forbidden", "permission", "unauthorized", "privilege"]
            ):
                requires_consent = True
        except Exception:
            pass

        logger.warning(
            "Graph API operation '%s' failed with status %d: %s",
            operation,
            status_code,
            error_msg,
        )

        return GraphAPIResult(
            success=False,
            status_code=status_code,
            error=error_msg,
            error_details=error_details,
            requires_admin_consent=requires_consent,
        )

    @staticmethod
    def normalize_assignment(raw: dict[str, Any]) -> dict[str, Any]:
        """Normalize Microsoft Graph Education assignment into common tracker format."""
        assignment_id = str(raw.get("id", "")).strip()
        title = raw.get("displayName") or raw.get("title") or "Untitled Assignment"

        # Due date parsing
        due_raw = raw.get("dueDateTime") or raw.get("due_date") or ""
        due_date = str(due_raw).split("T")[0] if due_raw else ""

        # Subject or class information
        subject = raw.get("classId") or raw.get("subject") or "General"

        # Instructions / details
        instructions = raw.get("instructions", {})
        details = instructions.get("content", "") if isinstance(instructions, dict) else str(instructions or "")

        # Web URL
        web_url = raw.get("webUrl") or ""

        return {
            "id": assignment_id,
            "title": title,
            "subject": subject,
            "due_date": due_date,
            "details": details,
            "link": web_url,
            "completed": False,
            "reminder_sent": False,
            "raw_due_datetime": due_raw,
            "source": "graph_api",
        }
