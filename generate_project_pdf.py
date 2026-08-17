"""Script to generate a comprehensive, presentation-ready PDF report.

Documents all libraries used, their exact use cases, how they work under the hood,
end-to-end workflow architecture, and project defense viva questions.
"""

from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


class NumberedCanvas(canvas.Canvas):
    """Canvas for adding professional headers and page numbers."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))

        # Top Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 11 * inch - 36, "Smart Teams Assignment Tracker & Google Tasks Sync — Project Documentation")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(54, 11 * inch - 42, 8.5 * inch - 54, 11 * inch - 42)

        # Bottom Footer
        footer_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(8.5 * inch - 54, 36, footer_text)
        self.drawString(54, 36, "Confidential — Academic Project Documentation")
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(54, 48, 8.5 * inch - 54, 48)

        self.restoreState()


def build_project_pdf(output_path: Path) -> Path:
    """Generate the complete project documentation PDF."""
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()

    # Custom Color Palette
    c_primary = colors.HexColor("#1e3a8a")     # Deep Navy Blue
    c_secondary = colors.HexColor("#0284c7")   # Bright Ocean Blue
    c_dark = colors.HexColor("#0f172a")        # Dark Slate
    c_text = colors.HexColor("#334155")        # Body text slate
    c_accent_bg = colors.HexColor("#f8fafc")    # Light slate background
    c_box_bg = colors.HexColor("#f1f5f9")       # Box background
    c_border = colors.HexColor("#e2e8f0")

    # Typography Styles
    title_style = ParagraphStyle(
        "CoverTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=30,
        textColor=c_primary,
        alignment=0,
        spaceAfter=6,
    )

    subtitle_style = ParagraphStyle(
        "CoverSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=12,
        leading=16,
        textColor=c_secondary,
        spaceAfter=14,
    )

    h1_style = ParagraphStyle(
        "SectionH1",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=19,
        textColor=c_primary,
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True,
    )

    h2_style = ParagraphStyle(
        "SectionH2",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=c_secondary,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True,
    )

    body_style = ParagraphStyle(
        "BodyDark",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=14,
        textColor=c_text,
        spaceAfter=6,
    )

    body_bold = ParagraphStyle(
        "BodyBold",
        parent=body_style,
        fontName="Helvetica-Bold",
        textColor=c_dark,
    )

    bullet_style = ParagraphStyle(
        "BulletText",
        parent=body_style,
        leftIndent=14,
        firstLineIndent=-10,
        spaceAfter=4,
    )

    code_block_style = ParagraphStyle(
        "CodeText",
        parent=styles["Normal"],
        fontName="Courier",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#0f172a"),
    )

    callout_style = ParagraphStyle(
        "CalloutText",
        parent=body_style,
        fontName="Helvetica-Oblique",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#1e293b"),
    )

    story = []

    # =========================================================================
    # COVER / HEADER
    # =========================================================================
    story.append(Paragraph("Smart Microsoft Teams Assignment Tracker & Google Tasks Sync", title_style))
    story.append(Paragraph("Comprehensive Technical Documentation, Python Libraries Reference & System Architecture", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=c_primary, spaceAfter=14))

    # Meta Table
    meta_data = [
        [
            Paragraph("<b>Project Domain:</b> Automation & Cloud Sync", body_style),
            Paragraph("<b>Technology Stack:</b> Python 3.12, Flask, Selenium, Google Cloud APIs", body_style),
        ],
        [
            Paragraph("<b>Interface:</b> Web Dashboard (Flask + Chart.js)", body_style),
            Paragraph("<b>Cloud Integrations:</b> Microsoft Teams & Google Tasks API v1", body_style),
        ],
    ]
    t_meta = Table(meta_data, colWidths=[3.5 * inch, 3.5 * inch])
    t_meta.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), c_accent_bg),
        ("BOX", (0, 0), (-1, -1), 1, c_border),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, c_border),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 14))

    # =========================================================================
    # SECTION 1: EXECUTIVE PROJECT SUMMARY
    # =========================================================================
    story.append(Paragraph("1. Executive Project Summary", h1_style))
    story.append(Paragraph(
        "The <b>Smart Teams Assignment Tracker & Google Tasks Sync</b> is an end-to-end Python automation "
        "and productivity solution designed for college students. It bridges the gap between institutional learning "
        "management systems (Microsoft Teams) and personal daily task management (Google Tasks & Google Calendar).",
        body_style,
    ))
    story.append(Paragraph(
        "<b>Core Problem Solved:</b> University students often have assignments scattered across multiple Microsoft Teams "
        "classes (e.g. Robotics, Data Structures, Mathematics, Electronics). Microsoft Teams does not provide a native, "
        "one-click synchronization to personal Google Tasks checklists. Furthermore, institutional security policies frequently "
        "block standard Microsoft Graph API delegated permissions. This project solves both issues using an automated browser "
        "extraction engine combined with the official Google Tasks Cloud API.",
        body_style,
    ))
    story.append(Spacer(1, 10))

    # =========================================================================
    # SECTION 2: PYTHON LIBRARIES USED (DETAILED EXPLANATION)
    # =========================================================================
    story.append(Paragraph("2. Python Libraries Used & Technical Breakdown", h1_style))
    story.append(Paragraph(
        "Below is the complete reference of every major Python library integrated into this project, "
        "explaining its role, how it operates internally, and why it was chosen.",
        body_style,
    ))

    # Library 1: Flask
    story.append(Paragraph("2.1. Flask (v3.1.3) — Web Server & REST API Backend", h2_style))
    story.append(Paragraph("• <b>What is it?</b> A lightweight, WSGI-compliant micro web framework for Python.", bullet_style))
    story.append(Paragraph("• <b>Use Case in Project:</b> Powers the local web dashboard (<code>http://127.0.0.1:5000</code>). Serves the frontend HTML/CSS/JS user interface and provides REST API endpoints for scanning Teams (<code>/api/scan-teams</code>), syncing Google Tasks (<code>/api/sync-google</code>), and clearing tasks (<code>/api/clear-google</code>).", bullet_style))
    story.append(Paragraph("• <b>How it works:</b> Uses Werkzeug's routing system to match incoming HTTP requests to Python controller functions. Runs a local HTTP server that communicates with the browser asynchronously via JSON payloads.", bullet_style))
    story.append(Spacer(1, 6))

    # Library 2: Selenium
    story.append(Paragraph("2.2. Selenium WebDriver (v4.46.0) — Browser Automation Engine", h2_style))
    story.append(Paragraph("• <b>What is it?</b> An industry-standard browser automation framework that programmatically controls real web browsers (Chrome, Edge).", bullet_style))
    story.append(Paragraph("• <b>Use Case in Project:</b> Automatically launches Microsoft Teams, navigates into the student's Assignments view, waits for single-page application (SPA) elements to render, and scrapes active assignment cards, subjects, points, and deadlines.", bullet_style))
    story.append(Paragraph("• <b>How it works:</b> Uses Chrome/Edge WebDriver with a persistent user data profile (<code>data/browser_profile</code>). By preserving browser cookies and localStorage, the student only logs in once (supporting 2FA/SSO), and all subsequent scans run 100% autonomously without prompting for passwords.", bullet_style))
    story.append(Spacer(1, 6))

    # Library 3: Google Client Libraries
    story.append(Paragraph("2.3. google-api-python-client (v2.198) & google-auth-oauthlib — Cloud Integration", h2_style))
    story.append(Paragraph("• <b>What is it?</b> The official Google Cloud SDK for Python to interact with Google APIs using OAuth 2.0.", bullet_style))
    story.append(Paragraph("• <b>Use Case in Project:</b> Authenticates with Google Cloud and manages the student's <b>'Teams Assignments'</b> checklist list in Google Tasks (inserting, updating, and deleting tasks with 9:00 AM due dates).", bullet_style))
    story.append(Paragraph("• <b>How it works:</b> Reads <code>credentials.json</code> to launch a local loopback server for Google OAuth consent. Upon authorization, stores the access/refresh token in <code>data/google_token.json</code> and constructs a secure <code>tasks(v1)</code> service client.", bullet_style))
    story.append(Spacer(1, 6))

    # Library 4: MSAL & Requests
    story.append(Paragraph("2.4. msal (v1.37.0) & requests (v2.34.2) — Microsoft Authentication & HTTP", h2_style))
    story.append(Paragraph("• <b>What is it?</b> Microsoft Authentication Library (MSAL) handles Azure AD OAuth 2.0 device code flows; Requests handles fast HTTP communication.", bullet_style))
    story.append(Paragraph("• <b>Use Case in Project:</b> Provides the Microsoft Graph API authentication module (Method A) with token caching. If Graph permissions are allowed by the university, it pulls assignments via direct REST calls.", bullet_style))
    story.append(Spacer(1, 6))

    # Library 5: Built-in Python Standard Libraries
    story.append(Paragraph("2.5. Python Standard Libraries (Built-in)", h2_style))
    story.append(Paragraph("• <b>datetime & timedelta:</b> Parses raw date strings into standard ISO 8601 timestamps and schedules Google Tasks for exactly 9:00 AM on deadline days.", bullet_style))
    story.append(Paragraph("• <b>re (Regular Expressions):</b> Extracts clean subjects (e.g. mapping <code>MDM-Fundamentals of Robotics:2026</code> to <code>Robotics</code>) and parses relative dates (<code>Due tomorrow</code>, <code>15 Aug</code>, <code>Past due</code>).", bullet_style))
    story.append(Paragraph("• <b>threading:</b> Runs Teams browser extraction and Google Cloud API sync in background daemon threads, keeping the Flask web UI fast and responsive.", bullet_style))
    story.append(Paragraph("• <b>pathlib & json:</b> Provides cross-platform file storage and handles local assignment persistence in <code>data/assignments.json</code>.", bullet_style))
    story.append(Spacer(1, 10))

    # =========================================================================
    # SECTION 3: SYSTEM ARCHITECTURE & WORKFLOW
    # =========================================================================
    story.append(PageBreak())
    story.append(Paragraph("3. End-to-End System Workflow (Step-by-Step)", h1_style))
    story.append(Paragraph(
        "The project follows a clean, 2-step modular workflow designed for maximum student control and simplicity:",
        body_style,
    ))

    workflow_steps = [
        [
            Paragraph("<b>Step</b>", body_bold),
            Paragraph("<b>Action / Module</b>", body_bold),
            Paragraph("<b>Behind-the-Scenes Technical Process</b>", body_bold),
        ],
        [
            Paragraph("<b>1. Start</b>", body_style),
            Paragraph("Launch Application (<code>main.py</code>)", body_style),
            Paragraph("Starts local Flask server at <code>http://127.0.0.1:5000</code> and automatically opens default browser. Dashboard initializes in a clean 0-count reset state.", body_style),
        ],
        [
            Paragraph("<b>2. Scan</b>", body_style),
            Paragraph("Click <b>'1. Scan Teams Assignments'</b>", body_style),
            Paragraph("Selenium launches Chrome with saved profile, navigates to Teams Assignments, parses active cards & dates, deduplicates, and saves locally in <code>data/assignments.json</code>. Does NOT touch Google Cloud yet.", body_style),
        ],
        [
            Paragraph("<b>3. Visualize</b>", body_style),
            Paragraph("Dashboard Analytics & Radar", body_style),
            Paragraph("Chart.js renders interactive Dual-View Workload Graph (Horizontal Bars ⇄ Donut distribution). Deadline Urgency Radar calculates items due in ≤ 48h, this week, or later.", body_style),
        ],
        [
            Paragraph("<b>4. Sync</b>", body_style),
            Paragraph("Click <b>'2. Sync to Google Tasks'</b>", body_style),
            Paragraph("Connects to Google Tasks API v1. Finds or creates the <b>'Teams Assignments'</b> task list. Pushes each assignment as an interactive checklist task scheduled for 9:00 AM due date.", body_style),
        ],
        [
            Paragraph("<b>5. Decongest</b>", body_style),
            Paragraph("Click <b>'Clear Google Tasks'</b>", body_style),
            Paragraph("Deletes all synced tasks from Google Tasks cloud list to prevent clutter, while preserving the local assignment database and resetting dashboard metrics to 0.", body_style),
        ],
    ]

    t_flow = Table(workflow_steps, colWidths=[0.8 * inch, 2.2 * inch, 4.0 * inch])
    t_flow.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), c_primary),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("TOPPADDING", (0, 0), (-1, 0), 6),
        ("BACKGROUND", (0, 1), (-1, -1), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, c_border),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, c_accent_bg]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t_flow)
    story.append(Spacer(1, 14))

    # =========================================================================
    # SECTION 4: KEY ENGINEERING CHALLENGES & INNOVATIONS
    # =========================================================================
    story.append(Paragraph("4. Key Technical Challenges & Solutions", h1_style))

    story.append(Paragraph("4.1. Multi-Assignment Section Date Parsing (Avatar Collision Fix)", h2_style))
    story.append(Paragraph(
        "<b>Challenge:</b> In Microsoft Teams, when multiple assignments share the same deadline section (e.g. 3 tasks due on Aug 10), "
        "generic DOM queries mistook the avatar initial buttons (<code>A</code>, <code>E</code>, <code>P</code>) of preceding cards as section headers, "
        "causing subsequent cards to lose their due date.<br/>"
        "<b>Solution:</b> Engineered a hierarchical header locator that skips single-letter interactive elements and walks up "
        "ancestor container groups to bind every card in a multi-task section accurately to its parent date.",
        body_style,
    ))
    story.append(Spacer(1, 6))

    story.append(Paragraph("4.2. Resilient Google Tasks API Sync (404 Fallback)", h2_style))
    story.append(Paragraph(
        "<b>Challenge:</b> If a user modified or deleted tasks directly inside Google Tasks on their phone, updating tasks by ID threw HTTP 404.<br/>"
        "<b>Solution:</b> Implemented a resilient try-update-catch-insert mechanism with tasklist pagination. If an update fails, the system automatically "
        "inserts a new task and updates the local ID without interrupting the synchronization pipeline.",
        body_style,
    ))
    story.append(Spacer(1, 10))

    # =========================================================================
    # SECTION 5: EXAMINER / VIVA DEFENSE GUIDE
    # =========================================================================
    story.append(Paragraph("5. Project Defense & Examiner Q&A Guide", h1_style))

    viva_qa = [
        ("Q1: Why use Selenium WebDriver instead of calling Microsoft Graph API directly?",
         "Many universities and institutional Microsoft 365 tenants restrict student API access with admin-consent policies. Selenium acts as an intelligent browser client, allowing legitimate, authenticated access using the student's existing web session while supporting institutional Multi-Factor Authentication (MFA)."),
        ("Q2: How does OAuth 2.0 work in the Google Tasks synchronization?",
         "The app uses the OAuth 2.0 Authorization Code flow for desktop apps. It requests the 'https://www.googleapis.com/auth/tasks' scope. Once granted, a refresh token is saved securely in data/google_token.json for subsequent automated access without repeated login prompts."),
        ("Q3: Why synchronize as Google Tasks instead of Google Calendar Events?",
         "Calendar events clutter the student's schedule grid with static blocks. Google Tasks provides interactive checklist items with checkmark circles that display in the Google Tasks mobile app, home screen widgets, and Google Calendar side-panel, perfectly matching assignment workflows."),
        ("Q4: How does the application avoid duplicate tasks during repeated scans?",
         "Every assignment is uniquely identified via a composite SHA-256/MD5 hash of its Title, Subject, and Due Date. The local AssignmentManager merges incoming scans and updates existing records rather than creating duplicate entries."),
    ]

    for q, a in viva_qa:
        box_data = [
            [Paragraph(f"<b>{q}</b>", ParagraphStyle("QA_Q", parent=body_style, textColor=c_primary, fontName="Helvetica-Bold"))],
            [Paragraph(a, body_style)],
        ]
        t_qa = Table(box_data, colWidths=[7.0 * inch])
        t_qa.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), c_box_bg),
            ("BOX", (0, 0), (-1, -1), 1, c_border),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(t_qa)
        story.append(Spacer(1, 6))

    # Build Document with NumberedCanvas
    doc.build(story, canvasmaker=NumberedCanvas)
    return output_path


if __name__ == "__main__":
    out_file = Path("D:/CLG/Python Project/Smart_Teams_Assignment_Tracker_Documentation.pdf")
    build_project_pdf(out_file)
    print(f"[OK] Generated documentation PDF at: {out_file}")
