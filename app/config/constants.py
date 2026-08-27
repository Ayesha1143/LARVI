# =========================
# Application
# =========================

APP_NAME = "Larvi"
APP_VERSION = "1.0.0"


# =========================
# Agent Names
# =========================

EMAIL_AGENT = "email_agent"
CALENDAR_AGENT = "calendar_agent"
MULTI_AGENT = "multi_agent"
MASTER_AGENT = "master_agent"


# =========================
# Workflow Status
# =========================

WORKFLOW_STARTED = "started"
WORKFLOW_IN_PROGRESS = "in_progress"
WORKFLOW_COMPLETED = "completed"
WORKFLOW_FAILED = "failed"


# =========================
# Workflow Steps
# =========================

STEP_REQUEST_ANALYZED = "request_analyzed"
STEP_AGENT_SELECTED = "agent_selected"
STEP_EMAIL_AGENT = "email_agent"
STEP_CALENDAR_AGENT = "calendar_agent"
STEP_MULTI_AGENT = "multi_agent"
STEP_TOOL_EXECUTED = "tool_executed"
STEP_COMPLETED = "completed"
STEP_FAILED = "failed"


# =========================
# Confirmation
# =========================

CONFIRMATION_REQUIRED = "confirmation_required"
CONFIRMATION_APPROVED = "confirmation_approved"
CONFIRMATION_REJECTED = "confirmation_rejected"


# =========================
# Gmail
# =========================

GMAIL_SERVICE = "gmail"
GMAIL_MAX_RESULTS = 20


# =========================
# Google Calendar
# =========================

CALENDAR_SERVICE = "calendar"
CALENDAR_MAX_RESULTS = 20


# =========================
# OAuth
# =========================

OAUTH_STATE_KEY = "oauth_state"

GOOGLE_AUTH_URI = (
    "https://accounts.google.com/o/oauth2/v2/auth"
)

GOOGLE_TOKEN_URI = (
    "https://oauth2.googleapis.com/token"
)

GOOGLE_USERINFO_URI = (
    "https://www.googleapis.com/oauth2/v2/userinfo"
)


# =========================
# Google OAuth Scopes
# =========================

GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.modify",
]

CALENDAR_SCOPES = [
    "https://www.googleapis.com/auth/calendar",
]


# =========================
# API Response Status
# =========================

STATUS_SUCCESS = "success"
STATUS_ERROR = "error"


# =========================
# Confirmation-Sensitive Tools
# =========================

CONFIRMATION_REQUIRED_TOOLS = {
    "send_email",
    "reply_email",
    "delete_event",
}


# =========================
# Date & Time
# =========================

DEFAULT_TIMEZONE = "UTC"
DEFAULT_EVENT_DURATION_MINUTES = 60