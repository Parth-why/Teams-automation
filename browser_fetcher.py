"""Browser-based Microsoft Teams assignment fetcher using Selenium.

Provides fallback retrieval for Microsoft Teams Assignments when Microsoft Graph
delegated permissions are restricted by institutional tenant policy.
Automates Teams navigation directly into the Assignments tab and extracts all assignments
with robust date detection across multi-task sections.
"""

import hashlib
import logging
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    SessionNotCreatedException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

import config

logger = logging.getLogger("SmartAssignmentTracker.browser_fetcher")


def extract_time_component(text: str) -> tuple[str, str]:
    """Extract (12hr_formatted, 24hr_formatted) from text if explicitly present."""
    match = re.search(r"\b(\d{1,2}):(\d{2})(?:\s*(AM|PM|am|pm))?\b", text)
    if match:
        hours = int(match.group(1))
        minutes = int(match.group(2))
        meridiem = match.group(3)
        if meridiem:
            meridiem = meridiem.upper()
            if meridiem == "PM" and hours < 12:
                hours_24 = hours + 12
            elif meridiem == "AM" and hours == 12:
                hours_24 = 0
            else:
                hours_24 = hours
            time_12hr = f"{hours}:{minutes:02d} {meridiem}"
        else:
            hours_24 = hours
            meridiem = "PM" if hours >= 12 else "AM"
            hours_12 = hours % 12 or 12
            time_12hr = f"{hours_12}:{minutes:02d} {meridiem}"

        time_24hr = f"{hours_24:02d}:{minutes:02d}:00"
        return time_12hr, time_24hr

    return "", ""


def parse_teams_due_date(raw_text: str, context_header: str = "") -> tuple[str, str, str, str]:
    """Parse Teams date and time into (YYYY-MM-DD, due_time, ISO_datetime, raw_text)."""
    if not raw_text and not context_header:
        return "", "", "", ""

    combined = f"{context_header} {raw_text}".strip() if context_header else raw_text.strip()
    cleaned = raw_text.strip() if raw_text else context_header.strip()

    has_date_indicator = any(
        kw in combined.lower()
        for kw in [
            "due", "past due", "expires", "deadline", "closes", "tomorrow", "today",
            "yesterday", "jan", "feb", "mar", "apr", "may", "jun", "jul", "aug",
            "sep", "oct", "nov", "dec",
        ]
    )
    if not has_date_indicator:
        return "", "", "", cleaned

    time_12hr, time_24hr = extract_time_component(combined)
    if not time_12hr:
        time_12hr = "11:59 PM"
        time_24hr = "23:59:00"

    text = re.sub(
        r"^(Due|Past due|Due by|Due on|Expires|Deadline:?|Closes:?)\s*[-:,]?\s*",
        "",
        combined,
        flags=re.IGNORECASE,
    ).strip()
    now = datetime.now()

    date_str = ""

    # Relative days: today, tomorrow, yesterday
    if re.search(r"\btomorrow\b", text, re.IGNORECASE):
        target = now + timedelta(days=1)
        date_str = target.strftime("%Y-%m-%d")
    elif re.search(r"\btoday\b", text, re.IGNORECASE):
        date_str = now.strftime("%Y-%m-%d")
    elif re.search(r"\byesterday\b", text, re.IGNORECASE):
        target = now - timedelta(days=1)
        date_str = target.strftime("%Y-%m-%d")

    months_pattern = (
        r"(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|"
        r"Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
    )

    if not date_str:
        # Format: "15 Aug 2026" or "15 Aug" or "15th Aug" or "15 August"
        match_d_m = re.search(
            rf"\b(\d{{1,2}})(?:st|nd|rd|th)?\s+{months_pattern}(?:,?\s+(\d{{4}}))?",
            text,
            re.IGNORECASE,
        )
        if match_d_m:
            day = int(match_d_m.group(1))
            month_str = match_d_m.group(2)[:3].capitalize()
            year = int(match_d_m.group(3)) if match_d_m.group(3) else now.year
            try:
                dt = datetime.strptime(f"{day} {month_str} {year}", "%d %b %Y")
                if not match_d_m.group(3) and dt < (now - timedelta(days=180)):
                    dt = datetime.strptime(f"{day} {month_str} {year + 1}", "%d %b %Y")
                date_str = dt.strftime("%Y-%m-%d")
            except ValueError:
                pass

    if not date_str:
        # Format: "Aug 15, 2026" or "Aug 15" or "August 15th"
        match_m_d = re.search(
            rf"\b{months_pattern}\s+(\d{{1,2}})(?:st|nd|rd|th)?(?:,?\s+(\d{{4}}))?",
            text,
            re.IGNORECASE,
        )
        if match_m_d:
            month_str = match_m_d.group(1)[:3].capitalize()
            day = int(match_m_d.group(2))
            year = int(match_m_d.group(3)) if match_m_d.group(3) else now.year
            try:
                dt = datetime.strptime(f"{month_str} {day} {year}", "%b %d %Y")
                if not match_m_d.group(3) and dt < (now - timedelta(days=180)):
                    dt = datetime.strptime(f"{month_str} {day} {year + 1}", "%b %d %Y")
                date_str = dt.strftime("%Y-%m-%d")
            except ValueError:
                pass

    if not date_str:
        # Format: "YYYY-MM-DD"
        match_iso = re.search(r"\b(\d{4})[-/](\d{1,2})[-/](\d{1,2})\b", text)
        if match_iso:
            try:
                dt = datetime(int(match_iso.group(1)), int(match_iso.group(2)), int(match_iso.group(3)))
                date_str = dt.strftime("%Y-%m-%d")
            except ValueError:
                pass

    if not date_str:
        # Format: "DD-MM-YYYY" or "DD/MM/YYYY"
        match_dmy = re.search(r"\b(\d{1,2})[-/](\d{1,2})[-/](\d{4})\b", text)
        if match_dmy:
            try:
                dt = datetime(int(match_dmy.group(3)), int(match_dmy.group(2)), int(match_dmy.group(1)))
                date_str = dt.strftime("%Y-%m-%d")
            except ValueError:
                pass

    # If past due section without specific date, default to yesterday
    if not date_str and context_header and "past due" in context_header.lower():
        date_str = (now - timedelta(days=1)).strftime("%Y-%m-%d")

    if not date_str:
        return "", "", "", cleaned

    iso_datetime = f"{date_str}T{time_24hr}"
    return date_str, time_12hr, iso_datetime, cleaned


def extract_title_and_subject(lines: list[str], aria_label: str = "") -> tuple[str, str]:
    """Extract clean (title, subject) separating avatar initials, class names, and points."""
    clean_lines: list[str] = []
    avatar_tokens = {"a", "e", "s", "p", "eq", "mc", "l5", "l1", "l2", "l3", "l4", "p1", "p2", "p3", "p4", "p5"}

    for line in lines:
        l_str = line.strip()
        if not l_str:
            continue
        if l_str.lower() in avatar_tokens or (len(l_str) <= 2 and not l_str.isdigit()):
            continue
        if re.search(r"^\d+\s*(?:points|pts|point)$", l_str, re.IGNORECASE):
            continue
        if re.search(r"^(?:due|past due|closes|expires)\b", l_str, re.IGNORECASE):
            continue
        clean_lines.append(l_str)

    if not clean_lines:
        return "Untitled Assignment", "General"

    if len(clean_lines) == 1:
        if aria_label:
            parts = [p.strip() for p in aria_label.split(",") if p.strip()]
            valid_parts = [
                p for p in parts
                if len(p) > 2 and not any(kw in p.lower() for kw in ["due", "past due", "points", "turned in", "returned"])
            ]
            if len(valid_parts) >= 2:
                return valid_parts[0], valid_parts[1]
        return clean_lines[0], "General"

    title = clean_lines[0]
    subject = clean_lines[1]

    return title, subject


def find_section_date_header(card: WebElement) -> str:
    """Find the enclosing section date header for a card, avoiding single-letter avatar buttons."""
    date_keywords = [
        "due", "past due", "today", "tomorrow", "yesterday", "jan", "feb", "mar",
        "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec",
    ]

    # Strategy 1: Check ancestor section / group header
    try:
        ancestor_headers = card.find_elements(
            By.XPATH,
            "./ancestor::*[contains(@role, 'group') or contains(@class, 'section') or contains(@class, 'group')][1]//*[self::h2 or self::h3 or self::h4 or contains(@role, 'heading') or contains(@class, 'header') or contains(@class, 'title') or contains(@class, 'accordion')]",
        )
        for h in ancestor_headers:
            t = h.text.strip()
            if len(t) > 2 and any(kw in t.lower() for kw in date_keywords):
                return t
    except Exception:
        pass

    # Strategy 2: Preceding headers search (skipping pure <button> to avoid avatars)
    try:
        headers = card.find_elements(
            By.XPATH,
            "./preceding::*[self::h2 or self::h3 or self::h4 or contains(@role, 'heading') or contains(@class, 'header') or contains(@class, 'title') or contains(@class, 'accordion') or contains(@data-tid, 'header')]",
        )
        for h in reversed(headers):
            t = h.text.strip()
            if len(t) > 2 and any(kw in t.lower() for kw in date_keywords):
                return t
    except Exception:
        pass

    return ""


class TeamsBrowserFetcher:
    """Automated browser session for retrieving visible Teams assignments."""

    def __init__(
        self,
        user_data_dir: Optional[Path] = None,
        headless: bool = False,
        timeout: int = 180,
    ) -> None:
        self.user_data_dir = user_data_dir or config.BROWSER_PROFILE_DIR
        self.headless = headless
        self.timeout = timeout
        self.driver: Optional[WebDriver] = None

    def __enter__(self) -> "TeamsBrowserFetcher":
        self.start()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()

    def start(self) -> None:
        """Initialize WebDriver with dedicated profile persistence."""
        self.user_data_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Initializing browser with profile at %s", self.user_data_dir)

        try:
            self.driver = self._create_chrome_driver()
            logger.info("Chrome WebDriver initialized successfully.")
            return
        except Exception as chrome_err:
            logger.warning("Could not start Chrome WebDriver (%s). Attempting Microsoft Edge...", chrome_err)

        try:
            self.driver = self._create_edge_driver()
            logger.info("Edge WebDriver initialized successfully.")
            return
        except Exception as edge_err:
            logger.error("Could not start Edge WebDriver (%s).", edge_err)
            raise RuntimeError(
                "Failed to initialize Chrome or Edge browser. Please ensure Google Chrome "
                "or Microsoft Edge is installed on your system."
            ) from edge_err

    def _create_chrome_driver(self) -> WebDriver:
        """Create a configured Chrome WebDriver instance."""
        options = ChromeOptions()
        options.add_argument(f"--user-data-dir={self.user_data_dir.resolve()}")
        options.add_argument("--profile-directory=Default")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-notifications")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        if self.headless:
            options.add_argument("--headless=new")

        service = ChromeService()
        return webdriver.Chrome(service=service, options=options)

    def _create_edge_driver(self) -> WebDriver:
        """Create a configured Edge WebDriver instance."""
        options = EdgeOptions()
        options.add_argument(f"--user-data-dir={self.user_data_dir.resolve()}")
        options.add_argument("--profile-directory=Default")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-notifications")

        if self.headless:
            options.add_argument("--headless=new")

        service = EdgeService()
        return webdriver.Edge(service=service, options=options)

    def login_and_navigate(self, auto_navigate: bool = True, interactive_wait: bool = False) -> bool:
        """Navigate to Teams, automatically click Assignments, and wait for assignment cards to load."""
        if not self.driver:
            raise RuntimeError("Browser driver is not running. Call start() first.")

        target_url = "https://teams.microsoft.com"
        logger.info("Opening Teams URL: %s", target_url)
        self.driver.get(target_url)

        if not auto_navigate:
            return True

        logger.info("Waiting for Teams application to load...")
        time.sleep(3)

        start_time = time.time()
        while time.time() - start_time < 45:
            current_url = self.driver.current_url.lower()
            if "login.microsoftonline.com" in current_url:
                logger.info("Waiting for user MFA / login completion...")
                time.sleep(2)
                continue

            sidebar_selectors = [
                "button[aria-label*='Assignments' i]",
                "a[aria-label*='Assignments' i]",
                "[data-tid*='app-bar-assignments']",
                "[data-tid*='assignments']",
                "button[id*='assignments']",
                "div[aria-label*='Assignments' i]",
            ]

            clicked_nav = False
            for selector in sidebar_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for el in elements:
                        if el.is_displayed():
                            logger.info("Found Assignments navigation button: %s. Clicking...", selector)
                            self.driver.execute_script("arguments[0].click();", el)
                            clicked_nav = True
                            time.sleep(3)
                            break
                    if clicked_nav:
                        break
                except Exception:
                    pass

            cards = self._check_if_cards_exist()
            if cards:
                logger.info("Assignment cards detected successfully (%d cards visible). Ready for extraction.", cards)
                time.sleep(2)
                return True

            time.sleep(2)

        logger.info("Reached navigation timeout. Attempting extraction on current view.")
        return True

    def _check_if_cards_exist(self) -> int:
        """Check current context or iframes for visible cards."""
        card_selectors = [
            "[data-tid*='assignment-item']",
            "[data-tid*='assignment-card']",
            "div[role='listitem']",
            "div[class*='fui-Card']",
        ]
        for sel in card_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, sel)
                if len(elements) >= 1 and any(el.is_displayed() for el in elements):
                    return len(elements)
            except Exception:
                pass

        try:
            iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
            for iframe in iframes:
                try:
                    self.driver.switch_to.frame(iframe)
                    for sel in card_selectors:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, sel)
                        if len(elements) >= 1 and any(el.is_displayed() for el in elements):
                            self.driver.switch_to.default_content()
                            return len(elements)
                    self.driver.switch_to.default_content()
                except Exception:
                    self.driver.switch_to.default_content()
        except Exception:
            pass

        return 0

    def fetch_assignments(self) -> list[dict[str, Any]]:
        """Extract visible active assignments across top-level document and iframes."""
        if not self.driver:
            raise RuntimeError("Browser driver is not running.")

        logger.info("Starting assignment extraction. Current URL: %s", self.driver.current_url)

        assignments = self._extract_from_current_context()

        if not assignments:
            iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
            logger.info("Checking %d iframe(s) for assignments content...", len(iframes))
            for i, iframe in enumerate(iframes):
                try:
                    self.driver.switch_to.frame(iframe)
                    logger.debug("Switched into iframe %d", i)
                    iframe_assignments = self._extract_from_current_context()
                    if iframe_assignments:
                        logger.info("Found %d assignment(s) inside iframe %d", len(iframe_assignments), i)
                        assignments.extend(iframe_assignments)
                        self.driver.switch_to.default_content()
                        break
                    self.driver.switch_to.default_content()
                except Exception as frame_err:
                    logger.debug("Error inspecting iframe %d: %s", i, frame_err)
                    self.driver.switch_to.default_content()

        # Strict Deduplication by Title + Subject
        unique_assignments: dict[str, dict[str, Any]] = {}
        for asg in assignments:
            if asg["title"] == "Untitled Assignment" and asg["subject"] == "General":
                continue
            clean_key = f"{asg['title'].lower().strip()}_{asg['subject'].lower().strip()}"
            if clean_key not in unique_assignments:
                unique_assignments[clean_key] = asg

        result = list(unique_assignments.values())
        logger.info("Total unique assignments extracted: %d", len(result))
        return result

    def _extract_from_current_context(self) -> list[dict[str, Any]]:
        """Scan current DOM context for actual assignment items."""
        if not self.driver:
            return []

        card_selectors = [
            "[data-tid*='assignment-item']",
            "[data-tid*='assignment-card']",
            "[data-tid*='assignment-row']",
            "div[role='listitem']",
            "div[role='row']",
            "li[role='treeitem']",
            "div.assignment-card",
            "div[class*='assignmentItem']",
            "div[class*='assignment-item']",
            "div[class*='fui-Card']",
            "div[class*='card-layout']",
        ]

        found_cards: list[WebElement] = []
        for selector in card_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                valid = []
                for el in elements:
                    if not el.is_displayed():
                        continue
                    el_id = el.get_attribute("id") or ""
                    el_tid = el.get_attribute("data-tid") or ""
                    if "team-card" in el_id or "team-card" in el_tid or "@thread.tacv2" in el_id:
                        continue
                    try:
                        parent_txt = el.find_element(By.XPATH, "./ancestor::*[contains(@class, 'completed') or contains(@class, 'past-due') or contains(@class, 'pastDue') or contains(@aria-label, 'Completed') or contains(@aria-label, 'Returned') or contains(@aria-label, 'Past due') or contains(@aria-label, 'past due')][1]").text
                        if parent_txt:
                            continue
                    except Exception:
                        pass

                    if len(el.text.strip()) > 3:
                        valid.append(el)

                if valid:
                    found_cards = valid
                    logger.info("Found %d matching cards using selector '%s'", len(found_cards), selector)
                    break
            except Exception as e:
                logger.debug("Selector %s search failed: %s", selector, e)

        assignments: list[dict[str, Any]] = []
        today_str = datetime.now().strftime("%Y-%m-%d")

        for idx, card in enumerate(found_cards):
            try:
                raw_text = card.text.strip()
                aria_label = card.get_attribute("aria-label") or ""
                card_id_attr = card.get_attribute("data-tid") or card.get_attribute("id") or ""

                if "@thread.tacv2" in card_id_attr or "team-card" in card_id_attr:
                    continue

                combined_text = f"{raw_text}\n{aria_label}".strip()
                if not combined_text:
                    continue

                # Locate Section Date Header
                section_header_text = find_section_date_header(card)

                # Skip any cards in 'Past due' sections
                if section_header_text and "past due" in section_header_text.lower():
                    logger.debug("Skipping card under 'Past due' header: %s", section_header_text)
                    continue

                lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
                title, subject = extract_title_and_subject(lines, aria_label)

                due_date_str = ""
                due_time_str = "11:59 PM"
                due_datetime_iso = ""
                raw_due = ""

                # Step 1: Check aria-label
                if aria_label:
                    d_parsed, t_parsed, dt_iso, r_due = parse_teams_due_date(aria_label, context_header=section_header_text)
                    if d_parsed:
                        due_date_str, due_time_str, due_datetime_iso, raw_due = d_parsed, t_parsed, dt_iso, r_due

                # Step 2: Check card lines
                if not due_date_str:
                    for line in lines:
                        d_parsed, t_parsed, dt_iso, r_due = parse_teams_due_date(line, context_header=section_header_text)
                        if d_parsed:
                            due_date_str, due_time_str, due_datetime_iso, raw_due = d_parsed, t_parsed, dt_iso, r_due
                            break

                # Step 3: Check raw text + section header
                if not due_date_str:
                    d_parsed, t_parsed, dt_iso, r_due = parse_teams_due_date(raw_text, context_header=section_header_text)
                    if d_parsed:
                        due_date_str, due_time_str, due_datetime_iso, raw_due = d_parsed, t_parsed, dt_iso, r_due

                # Step 4: Fallback to section header alone
                if not due_date_str and section_header_text:
                    d_parsed, t_parsed, dt_iso, r_due = parse_teams_due_date("", context_header=section_header_text)
                    if d_parsed:
                        due_date_str, due_time_str, due_datetime_iso, raw_due = d_parsed, t_parsed, dt_iso, r_due

                # Step 5: Final fallback to today
                if not due_date_str:
                    now = datetime.now()
                    due_date_str = now.strftime("%Y-%m-%d")
                    due_datetime_iso = f"{due_date_str}T23:59:00"

                # STRICT FILTER: Skip past assignments whose due date has already passed!
                if due_date_str < today_str:
                    logger.debug("Skipping past assignment '%s' (Due: %s < Today: %s)", title, due_date_str, today_str)
                    continue

                # Extract Link
                link = ""
                try:
                    anchor = card.find_elements(By.TAG_NAME, "a")
                    if anchor:
                        link = anchor[0].get_attribute("href") or ""
                except Exception:
                    pass

                if not card_id_attr or "@thread" in card_id_attr:
                    hash_input = f"{title}_{subject}_{due_date_str}"
                    assignment_id = f"teams_{hashlib.md5(hash_input.encode('utf-8')).hexdigest()[:12]}"
                else:
                    assignment_id = str(card_id_attr)

                assignments.append({
                    "id": assignment_id,
                    "title": title,
                    "subject": subject,
                    "due_date": due_date_str,
                    "due_time": due_time_str,
                    "due_datetime_iso": due_datetime_iso,
                    "details": raw_text,
                    "link": link,
                    "completed": False,
                    "reminder_sent": False,
                    "raw_due_datetime": raw_due or due_date_str or "",
                    "source": "selenium_fetcher",
                })
            except Exception as e:
                logger.warning("Error parsing card #%d: %s", idx, e)

        return assignments

    def close(self) -> None:
        """Close WebDriver session cleanly."""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Browser session closed cleanly.")
            except Exception as e:
                logger.debug("Error while closing WebDriver: %s", e)
            finally:
                self.driver = None
