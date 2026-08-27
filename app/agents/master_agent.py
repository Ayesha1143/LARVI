from typing import Any, Dict, List, Optional
import json
import re
from datetime import datetime

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama

from app.agents.calendar_agent import calendar_agent
from app.agents.email_agent import email_agent
from app.services.calendar_service import calendar_service

from app.config.constants import (
    CALENDAR_AGENT,
    EMAIL_AGENT,
    MULTI_AGENT,
)

from app.config.settings import settings


class MasterAgent:
    """
    Central controller for Larvi.

    Responsibilities:
    - Understand the user's request
    - Select the correct agent
    - Select the correct tool
    - Generate tool arguments
    - Identify multi-agent workflows
    - Plan calendar actions from email results
    - Generate final responses
    """

    name = "master_agent"

    def __init__(self) -> None:

        self.llm = ChatOllama(
            model=settings.ollama_model,
            base_url="https://ollama.com",
            client_kwargs={
                "headers": {
                    "Authorization": (
                        f"Bearer {settings.ollama_api_key}"
                    )
                }
            },
            temperature=0,
        )

        self.agents = {
            EMAIL_AGENT: email_agent,
            CALENDAR_AGENT: calendar_agent,
        }

    # ==========================================
    # REQUEST ANALYSIS
    # ==========================================

    def analyze_request(
        self,
        user_message: str,
        conversation_history: Optional[
            List[Dict[str, str]]
        ] = None,
    ) -> Dict[str, Any]:
        """
        Analyze the user's request and determine
        the correct agent, tool, and arguments.
        """

        if not user_message.strip():
            raise ValueError(
                "User message cannot be empty."
            )

        history_text = self._format_history(
            conversation_history or []
        )

        system_prompt = """
You are Larvi's Master Agent.

Your job is to understand the user's request and
select the correct agent and exact tool.

AVAILABLE AGENTS:

1. email_agent
   Handles Gmail operations.

2. calendar_agent
   Handles Google Calendar operations.

3. multi_agent
   Used when BOTH Gmail and Google Calendar
   are required.

==========================================
AVAILABLE EMAIL TOOLS
==========================================

get_recent_emails
- Get the user's recent emails.

Arguments:
{
    "max_results": 20
}

search_emails
- Search Gmail using a Gmail search query.

Arguments:
{
    "query": "...",
    "max_results": 20
}

read_email
- Read one email.

Arguments:
{
    "message_id": "..."
}

create_draft
- Create an email draft.

Arguments:
{
    "recipient": "...",
    "subject": "...",
    "body": "..."
}

send_email
- Send an email.

Arguments:
{
    "recipient": "...",
    "subject": "...",
    "body": "..."
}

reply_email
- Reply to an email.

Arguments:
{
    "message_id": "...",
    "body": "..."
}

==========================================
AVAILABLE CALENDAR TOOLS
==========================================

get_events
- Get calendar events.

Arguments:
{
    "time_min": null,
    "time_max": null,
    "max_results": 20
}

search_events
- Search calendar events.

Arguments:
{
    "query": "...",
    "time_min": null,
    "time_max": null,
    "max_results": 20
}

check_availability
- Check whether the user is free.

Arguments:
{
    "start": "...",
    "end": "..."
}

create_event
- Create a calendar event.

Arguments:
{
    "summary": "...",
    "start": "...",
    "end": "...",
    "description": null,
    "location": null,
    "timezone": null
}

update_event
- Update an existing calendar event.
- The event_id MUST be the real Google Calendar event ID.
- Never invent, guess, or use a placeholder event ID.
- If the user gives an event name instead of an ID, the system will
  resolve the real event ID before executing the update.

Arguments:
{
    "event_id": "...",
    "summary": null,
    "start": null,
    "end": null,
    "description": null,
    "location": null,
    "timezone": null
}

delete_event
- Delete an existing calendar event.
- The event_id MUST be the real Google Calendar event ID.
- Never invent, guess, or use a placeholder event ID.
- If the user gives an event name instead of an ID, the system will
  resolve the real event ID before executing the delete.

Arguments:
{
    "event_id": "..."
}

==========================================
IMPORTANT TOOL NAMES
==========================================

Never invent tool names.

Valid EMAIL tools:
get_recent_emails
search_emails
read_email
create_draft
send_email
reply_email

Valid CALENDAR tools:
get_events
search_events
check_availability
create_event
update_event
delete_event

There is NO tool called:
get_today_events

For today's calendar use:
get_events

==========================================
ROUTING RULES
==========================================

LATEST EMAILS

For requests such as:

"show my latest emails"
"show recent emails"
"show my emails"
"what are my latest emails"

Use:

selected_agent = email_agent
selected_tool = get_recent_emails

==========================================
EMAIL SEARCH
==========================================

For requests such as:

"find emails about meeting"
"find my meeting email"
"search my emails for project"
"find Ahmed's email"

Use:

selected_agent = email_agent
selected_tool = search_emails

Example:

"find the latest email about a meeting"

Use:

{
    "query": "meeting",
    "max_results": 20
}

==========================================
UNREAD EMAILS
==========================================

For unread emails:

selected_agent = email_agent
selected_tool = search_emails

Arguments:

{
    "query": "is:unread",
    "max_results": 20
}

==========================================
TODAY'S CALENDAR
==========================================

For:

"what's on my calendar today?"
"show today's calendar"
"calendar today"

Use:

selected_agent = calendar_agent
selected_tool = get_events

Arguments:

{
    "time_min": null,
    "time_max": null,
    "max_results": 20
}

==========================================
CALENDAR SEARCH
==========================================

For calendar searches:

selected_agent = calendar_agent
selected_tool = search_events

==========================================
CREATE CALENDAR EVENT
==========================================

For requests explicitly asking to create an event:

selected_agent = calendar_agent
selected_tool = create_event

==========================================
SEND EMAIL
==========================================

For sending an email:

selected_agent = email_agent
selected_tool = send_email

==========================================
CREATE DRAFT
==========================================

For drafting an email:

selected_agent = email_agent
selected_tool = create_draft

==========================================
REPLY
==========================================

For replying to an email:

selected_agent = email_agent
selected_tool = reply_email

==========================================
MULTI-AGENT WORKFLOW
==========================================

If a request requires BOTH Gmail and Calendar,
use:

selected_agent = multi_agent

Example:

"Find the latest email about a meeting and
add the meeting to my calendar."

First phase:

selected_tool = search_emails

tool_arguments = {
    "query": "meeting",
    "max_results": 20
}

The Email Agent must first search the email.

After the email result is available, Larvi will
extract the meeting information and determine
the Calendar action.

==========================================
OUTPUT
==========================================

Return ONLY valid JSON.

Use exactly:

{
    "intent": "short description",
    "selected_agent": "email_agent | calendar_agent | multi_agent",
    "selected_tool": "exact tool name or null",
    "tool_arguments": {},
    "reason": "short explanation"
}

Do not execute tools.
Only analyze and route the request.
"""

        # Keep the system prompt only in SystemMessage.
        # The previous implementation duplicated it in the HumanMessage,
        # unnecessarily increasing Ollama context usage.
        prompt = (
            f"Conversation history:\n{history_text}\n\n"
            f"Current user request:\n{user_message[:4000]}"
        )

        # ==========================================
        # LLM ANALYSIS
        # ==========================================

        try:

            response = self.llm.invoke(
                [
                    SystemMessage(
                        content=system_prompt
                    ),
                    HumanMessage(
                        content=prompt
                    ),
                ]
            )

            result = self._parse_json_response(
                response.content
            )

        except Exception:

            result = {}

        # ==========================================
        # LLM RESULT
        # ==========================================

        selected_agent = result.get(
            "selected_agent"
        )

        selected_tool = result.get(
            "selected_tool"
        )

        tool_arguments = result.get(
            "tool_arguments",
            {},
        )

        if not isinstance(
            tool_arguments,
            dict,
        ):
            tool_arguments = {}

        valid_agents = {
            EMAIL_AGENT,
            CALENDAR_AGENT,
            MULTI_AGENT,
        }

        if selected_agent not in valid_agents:
            selected_agent = None

        # ==========================================
        # DETERMINISTIC FALLBACK
        # ==========================================

        fallback = self._deterministic_route(
            user_message
        )

        if selected_agent is None:

            selected_agent = fallback[
                "selected_agent"
            ]

        if not selected_tool:

            selected_tool = fallback.get(
                "selected_tool"
            )

        if not tool_arguments:

            tool_arguments = fallback.get(
                "tool_arguments",
                {},
            )

        # ==========================================
        # RESOLVE CALENDAR EVENT ID
        # ==========================================
        #
        # update_event/delete_event require the real
        # Google Calendar event ID. Users normally provide
        # an event title instead. Resolve the ID with a
        # READ-ONLY search before the mutation.
        #
        # This does NOT execute update/delete and therefore
        # does not bypass the existing confirmation logic.

        if (
            selected_agent == CALENDAR_AGENT
            and selected_tool in {
                "update_event",
                "delete_event",
            }
        ):
            tool_arguments = self._resolve_calendar_mutation(
                user_message=user_message,
                tool=selected_tool,
                tool_arguments=tool_arguments,
            )

        return {
            "current_intent": result.get(
                "intent",
                fallback.get(
                    "intent",
                    user_message,
                ),
            ),
            "selected_agent": selected_agent,
            "selected_tool": selected_tool,
            "tool_arguments": tool_arguments,
            "reason": result.get(
                "reason",
                fallback.get(
                    "reason",
                    "",
                ),
            ),
        }

    # ==========================================
    # RESOLVE CALENDAR MUTATION
    # ==========================================

    @staticmethod
    def _resolve_calendar_mutation(
        user_message: str,
        tool: str,
        tool_arguments: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Resolve a real Google Calendar event ID for
        update/delete requests.

        Only a READ-ONLY calendar search is performed here.
        The actual mutation remains in the Calendar Agent
        and is still protected by confirmation.
        """

        arguments = dict(tool_arguments or {})

        # ------------------------------------------
        # KEEP A REAL EVENT ID
        # ------------------------------------------

        event_id = str(
            arguments.get("event_id", "")
        ).strip()

        invalid_ids = {
            "",
            "event_id_placeholder",
            "event-id-placeholder",
            "event_id",
            "placeholder",
            "unknown",
            "null",
            "none",
        }

        if event_id.casefold() not in invalid_ids:
            return arguments

        # ------------------------------------------
        # DETERMINE EVENT TITLE
        # ------------------------------------------

        summary = str(
            arguments.get("summary", "")
        ).strip()

        if not summary:
            summary = MasterAgent._extract_calendar_event_name(
                user_message
            )

        if not summary:
            return arguments

        # ------------------------------------------
        # READ-ONLY SEARCH
        # ------------------------------------------

        try:
            matches = calendar_service.search_events(
                query=summary,
                max_results=20,
            )
        except Exception:
            matches = []

        if not matches:
            return arguments

        # ------------------------------------------
        # FIND EXACT TITLE FIRST
        # ------------------------------------------

        summary_lower = summary.casefold()
        selected_event = None

        for event in matches:
            if not isinstance(event, dict):
                continue

            event_summary = str(
                event.get("summary", "")
            ).strip()

            if event_summary.casefold() == summary_lower:
                selected_event = event
                break

        # ------------------------------------------
        # FIND PARTIAL TITLE
        # ------------------------------------------

        if selected_event is None:
            for event in matches:
                if not isinstance(event, dict):
                    continue

                event_summary = str(
                    event.get("summary", "")
                ).strip()

                if (
                    summary_lower in event_summary.casefold()
                    or event_summary.casefold()
                    in summary_lower
                ):
                    selected_event = event
                    break

        if selected_event is None:
            return arguments

        resolved_id = str(
            selected_event.get("id", "")
        ).strip()

        if not resolved_id:
            return arguments

        arguments["event_id"] = resolved_id

        # Preserve the real event title for update requests.
        if (
            tool == "update_event"
            and not arguments.get("summary")
        ):
            actual_summary = str(
                selected_event.get("summary", "")
            ).strip()

            if actual_summary:
                arguments["summary"] = actual_summary

        return arguments

    @staticmethod
    def _extract_calendar_event_name(
        user_message: str,
    ) -> str:
        """
        Extract the event title from a natural-language
        update/delete request.
        """

        text = user_message.strip()

        summary = re.sub(
            r"^\s*(?:please\s+)?"
            r"(?:update|edit|change|modify|delete|remove|cancel)"
            r"\s+(?:my\s+|the\s+|an?\s+)?",
            "",
            text,
            flags=re.IGNORECASE,
        ).strip()

        summary = re.sub(
            r"^(?:event|meeting)\s+",
            "",
            summary,
            flags=re.IGNORECASE,
        ).strip()

        summary = re.split(
            r"\s+(?:to|at|on|from|for|with|"
            r"starting|start|ending|end|timing|time|"
            r"date|schedule|location|description)\b",
            summary,
            maxsplit=1,
            flags=re.IGNORECASE,
        )[0].strip()

        return summary

    # ==========================================
    # DETERMINISTIC ROUTING
    # ==========================================

    @staticmethod
    def _deterministic_route(
        user_message: str,
    ) -> Dict[str, Any]:
        """
        Deterministic fallback routing.
        """

        text = user_message.lower().strip()

        # ==========================================
        # KEYWORDS
        # ==========================================

        email_words = {
            "email",
            "emails",
            "mail",
            "gmail",
            "inbox",
            "message",
            "messages",
            "sender",
            "unread",
            "draft",
            "reply",
        }

        calendar_words = {
            "calendar",
            "event",
            "events",
            "meeting",
            "meetings",
            "schedule",
            "scheduled",
            "appointment",
            "availability",
            "free",
        }

        has_email = any(
            word in text
            for word in email_words
        )

        has_calendar = any(
            word in text
            for word in calendar_words
        )

        # ==========================================
        # MULTI AGENT
        # ==========================================

        if has_email and has_calendar:

            if (
                "meeting" in text
                or "meetings" in text
            ):

                query = "meeting"

                if "ahmed" in text:
                    query = (
                        "from:Ahmed meeting"
                    )

                return {
                    "intent": (
                        "Find a meeting email "
                        "and add it to the calendar."
                    ),
                    "selected_agent": MULTI_AGENT,
                    "selected_tool": (
                        "search_emails"
                    ),
                    "tool_arguments": {
                        "query": query,
                        "max_results": 20,
                    },
                    "reason": (
                        "The request requires "
                        "both Gmail and Calendar."
                    ),
                }

            return {
                "intent": user_message,
                "selected_agent": MULTI_AGENT,
                "selected_tool": None,
                "tool_arguments": {},
                "reason": (
                    "The request requires both "
                    "Gmail and Calendar."
                ),
            }

        # ==========================================
        # LATEST EMAILS
        # ==========================================

        latest_email_phrases = [
            "latest emails",
            "latest email",
            "recent emails",
            "recent email",
            "show my emails",
            "show emails",
            "show my latest emails",
            "show recent emails",
            "my latest mail",
            "latest mail",
            "recent mail",
        ]

        if any(
            phrase in text
            for phrase in latest_email_phrases
        ):

            return {
                "intent": (
                    "View recent emails."
                ),
                "selected_agent": EMAIL_AGENT,
                "selected_tool": (
                    "get_recent_emails"
                ),
                "tool_arguments": {
                    "max_results": 20,
                },
                "reason": (
                    "The user wants to "
                    "see recent emails."
                ),
            }

        # ==========================================
        # UNREAD EMAILS
        # ==========================================

        if (
            "unread" in text
            and (
                "email" in text
                or "mail" in text
                or "message" in text
            )
        ):

            return {
                "intent": (
                    "View unread emails."
                ),
                "selected_agent": EMAIL_AGENT,
                "selected_tool": (
                    "search_emails"
                ),
                "tool_arguments": {
                    "query": "is:unread",
                    "max_results": 20,
                },
                "reason": (
                    "The user wants "
                    "unread emails."
                ),
            }

        # ==========================================
        # EMAIL SEARCH
        # ==========================================

        if (
            (
                "find" in text
                or "search" in text
            )
            and has_email
        ):

            query = text

            if "ahmed" in text:
                query = "from:Ahmed"

                if "meeting" in text:
                    query += " meeting"

            elif "meeting" in text:
                query = "meeting"

            elif "project" in text:
                query = "project"

            return {
                "intent": (
                    "Search emails."
                ),
                "selected_agent": EMAIL_AGENT,
                "selected_tool": (
                    "search_emails"
                ),
                "tool_arguments": {
                    "query": query,
                    "max_results": 20,
                },
                "reason": (
                    "The user wants to "
                    "search Gmail."
                ),
            }

        # ==========================================
        # READ EMAIL
        # ==========================================

        if (
            "read email" in text
            or "open email" in text
        ):

            return {
                "intent": (
                    "Read an email."
                ),
                "selected_agent": EMAIL_AGENT,
                "selected_tool": (
                    "read_email"
                ),
                "tool_arguments": {},
                "reason": (
                    "The user wants to "
                    "read an email."
                ),
            }

        # ==========================================
        # DRAFT EMAIL
        # ==========================================

        if (
            "draft email" in text
            or "create draft" in text
            or "write an email" in text
            or "compose email" in text
        ):

            return {
                "intent": (
                    "Create an email draft."
                ),
                "selected_agent": EMAIL_AGENT,
                "selected_tool": (
                    "create_draft"
                ),
                "tool_arguments": {},
                "reason": (
                    "The user wants to "
                    "draft an email."
                ),
            }

        # ==========================================
        # REPLY EMAIL
        # ==========================================

        if (
            "reply to email" in text
            or "reply email" in text
        ):

            return {
                "intent": (
                    "Reply to an email."
                ),
                "selected_agent": EMAIL_AGENT,
                "selected_tool": (
                    "reply_email"
                ),
                "tool_arguments": {},
                "reason": (
                    "The user wants to "
                    "reply to an email."
                ),
            }

        # ==========================================
        # SEND EMAIL
        # ==========================================

        if (
            "send email" in text
            or "send an email" in text
        ):

            return {
                "intent": (
                    "Send an email."
                ),
                "selected_agent": EMAIL_AGENT,
                "selected_tool": (
                    "send_email"
                ),
                "tool_arguments": {},
                "reason": (
                    "The user wants to "
                    "send an email."
                ),
            }

        # ==========================================
        # CALENDAR TODAY
        # ==========================================

        if (
            "calendar today" in text
            or "today's calendar" in text
            or "todays calendar" in text
            or "what's on my calendar" in text
            or "whats on my calendar" in text
            or "calendar for today" in text
        ):

            return {
                "intent": (
                    "View today's calendar."
                ),
                "selected_agent": (
                    CALENDAR_AGENT
                ),
                "selected_tool": (
                    "get_events"
                ),
                "tool_arguments": {
                    "time_min": None,
                    "time_max": None,
                    "max_results": 20,
                },
                "reason": (
                    "The user wants "
                    "today's calendar events."
                ),
            }

        # ==========================================
        # CALENDAR SEARCH
        # ==========================================

        if (
            "search calendar" in text
            or "find event" in text
            or "find an event" in text
        ):

            return {
                "intent": (
                    "Search calendar events."
                ),
                "selected_agent": (
                    CALENDAR_AGENT
                ),
                "selected_tool": (
                    "search_events"
                ),
                "tool_arguments": {
                    "query": text,
                    "time_min": None,
                    "time_max": None,
                    "max_results": 20,
                },
                "reason": (
                    "The user wants to "
                    "search calendar events."
                ),
            }

        # ==========================================
        # CHECK AVAILABILITY
        # ==========================================

        if (
            "am i free" in text
            or "am i available" in text
            or "check availability" in text
            or "check if i'm free" in text
        ):

            return {
                "intent": (
                    "Check calendar availability."
                ),
                "selected_agent": (
                    CALENDAR_AGENT
                ),
                "selected_tool": (
                    "check_availability"
                ),
                "tool_arguments": {},
                "reason": (
                    "The user wants to "
                    "check availability."
                ),
            }

        # ==========================================
        # UPDATE CALENDAR EVENT
        # ==========================================

        if (
            "update event" in text
            or "update my event" in text
            or "update my meeting" in text
            or "edit event" in text
            or "edit my event" in text
            or "change event" in text
            or "change my event" in text
            or "modify event" in text
            or "modify my event" in text
        ):
            return {
                "intent": (
                    "Update an existing calendar event."
                ),
                "selected_agent": CALENDAR_AGENT,
                "selected_tool": "update_event",
                "tool_arguments": {},
                "reason": (
                    "The user wants to update "
                    "an existing calendar event."
                ),
            }

        # ==========================================
        # DELETE CALENDAR EVENT
        # ==========================================

        if (
            "delete event" in text
            or "delete my event" in text
            or "delete meeting" in text
            or "delete my meeting" in text
            or "remove event" in text
            or "remove my event" in text
            or "remove meeting" in text
            or "remove my meeting" in text
            or "cancel event" in text
            or "cancel my event" in text
            or "cancel meeting" in text
            or "cancel my meeting" in text
        ):
            return {
                "intent": (
                    "Delete an existing calendar event."
                ),
                "selected_agent": CALENDAR_AGENT,
                "selected_tool": "delete_event",
                "tool_arguments": {},
                "reason": (
                    "The user wants to delete "
                    "an existing calendar event."
                ),
            }

        # ==========================================
        # CREATE EVENT
        # ==========================================

        if (
            "create event" in text
            or "create a meeting" in text
            or "add event" in text
            or "add a meeting" in text
        ):

            return {
                "intent": (
                    "Create a calendar event."
                ),
                "selected_agent": (
                    CALENDAR_AGENT
                ),
                "selected_tool": (
                    "create_event"
                ),
                "tool_arguments": {},
                "reason": (
                    "The user wants to "
                    "create a calendar event."
                ),
            }

        # ==========================================
        # CALENDAR DEFAULT
        # ==========================================

        if has_calendar:

            return {
                "intent": user_message,
                "selected_agent": (
                    CALENDAR_AGENT
                ),
                "selected_tool": None,
                "tool_arguments": {},
                "reason": (
                    "The request concerns "
                    "Google Calendar."
                ),
            }

        # ==========================================
        # EMAIL DEFAULT
        # ==========================================

        if has_email:

            return {
                "intent": user_message,
                "selected_agent": EMAIL_AGENT,
                "selected_tool": (
                    "get_recent_emails"
                ),
                "tool_arguments": {
                    "max_results": 20,
                },
                "reason": (
                    "The request concerns Gmail."
                ),
            }

        # ==========================================
        # DEFAULT
        # ==========================================

        return {
            "intent": user_message,
            "selected_agent": EMAIL_AGENT,
            "selected_tool": (
                "get_recent_emails"
            ),
            "tool_arguments": {
                "max_results": 20,
            },
            "reason": (
                "No specific operation was "
                "detected; defaulting to emails."
            ),
        }

    # ==========================================
    # PLAN CALENDAR ACTION FROM EMAIL
    # ==========================================

    def plan_calendar_action(
        self,
        user_message: str,
        email_result: Any,
    ) -> Dict[str, Any]:
        """
        Convert a meeting email into a calendar
        create_event action.

        IMPORTANT:
        This function is deterministic.

        It does NOT call the LLM.

        Meeting information is extracted directly
        from the Gmail result.
        """

        # ==========================================
        # CHECK EMAIL RESULT
        # ==========================================

        if not email_result:

            return {
                "selected_tool": None,
                "tool_arguments": {},
                "reason": (
                    "No email result was provided."
                ),
            }

        # ==========================================
        # NORMALIZE RESULT
        # ==========================================

        if isinstance(
            email_result,
            list,
        ):

            emails = email_result

        elif isinstance(
            email_result,
            dict,
        ):

            emails = [
                email_result
            ]

        else:

            return {
                "selected_tool": None,
                "tool_arguments": {},
                "reason": (
                    "Invalid email result format."
                ),
            }

        if not emails:

            return {
                "selected_tool": None,
                "tool_arguments": {},
                "reason": (
                    "No emails were found."
                ),
            }

        # ==========================================
        # FIND MEETING EMAIL
        # ==========================================

        meeting_email = None

        for email in emails:

            if not isinstance(
                email,
                dict,
            ):
                continue

            subject = str(
                email.get(
                    "subject",
                    "",
                )
            ).strip()

            body = str(
                email.get(
                    "body",
                    "",
                )
            ).strip()

            combined_text = (
                f"{subject}\n{body}"
            ).lower()

            if (
                "meeting" in combined_text
                or "schedule" in combined_text
            ):

                meeting_email = email
                break

        if meeting_email is None:

            return {
                "selected_tool": None,
                "tool_arguments": {},
                "reason": (
                    "No meeting email was found "
                    "in the email results."
                ),
            }

        # ==========================================
        # GET EMAIL INFORMATION
        # ==========================================

        subject = str(
            meeting_email.get(
                "subject",
                "",
            )
        ).strip()

        body = str(
            meeting_email.get(
                "body",
                "",
            )
        ).strip()

        sender = str(
            meeting_email.get(
                "sender",
                "",
            )
        ).strip()

        # ==========================================
        # EXTRACT DATE
        # ==========================================

        date_match = re.search(
            r"Date\s*:\s*\*?\s*"
            r"([A-Za-z]+\s+\d{1,2},\s+\d{4})",
            body,
            re.IGNORECASE,
        )

        if not date_match:

            return {
                "selected_tool": None,
                "tool_arguments": {},
                "reason": (
                    "Meeting date could not be "
                    "extracted from the email."
                ),
            }

        date_text = (
            date_match
            .group(1)
            .strip()
        )

        # ==========================================
        # EXTRACT TIME
        # ==========================================

        time_match = re.search(
            r"Time\s*:\s*\*?\s*"
            r"(\d{1,2}:\d{2}\s*[AP]M)"
            r"\s*[–-]\s*"
            r"(\d{1,2}:\d{2}\s*[AP]M)",
            body,
            re.IGNORECASE,
        )

        if not time_match:

            return {
                "selected_tool": None,
                "tool_arguments": {},
                "reason": (
                    "Meeting start/end time could "
                    "not be extracted from the email."
                ),
            }

        start_time_text = (
            time_match
            .group(1)
            .strip()
        )

        end_time_text = (
            time_match
            .group(2)
            .strip()
        )

        # ==========================================
        # CONVERT DATE/TIME
        # ==========================================

        try:

            start_dt = datetime.strptime(
                (
                    f"{date_text} "
                    f"{start_time_text}"
                ),
                "%B %d, %Y %I:%M %p",
            )

            end_dt = datetime.strptime(
                (
                    f"{date_text} "
                    f"{end_time_text}"
                ),
                "%B %d, %Y %I:%M %p",
            )

        except ValueError as exc:

            return {
                "selected_tool": None,
                "tool_arguments": {},
                "reason": (
                    "Unable to convert the meeting "
                    f"date/time: {exc}"
                ),
            }

        # ==========================================
        # EXTRACT MEETING TITLE
        # ==========================================

        meeting_match = re.search(
            r"Meeting\s*:\s*\*?\s*"
            r"(.+?)(?:\r?\n|$)",
            body,
            re.IGNORECASE,
        )

        if meeting_match:

            summary = (
                meeting_match
                .group(1)
                .strip()
            )

            summary = summary.strip(
                "* "
            )

        else:

            summary = subject

            summary = re.sub(
                r"^Meeting Scheduled\s*[–-]\s*",
                "",
                summary,
                flags=re.IGNORECASE,
            ).strip()

        if not summary:

            return {
                "selected_tool": None,
                "tool_arguments": {},
                "reason": (
                    "Meeting title could not "
                    "be extracted."
                ),
            }

        # ==========================================
        # EXTRACT LOCATION
        # ==========================================

        location_match = re.search(
            r"Location\s*:\s*\*?\s*"
            r"(.+?)(?:\r?\n|$)",
            body,
            re.IGNORECASE,
        )

        location = None

        if location_match:

            location = (
                location_match
                .group(1)
                .strip()
            )

            location = location.strip(
                "* "
            )

        # ==========================================
        # DESCRIPTION
        # ==========================================

        # Never store the complete email body in the event.
        # Large email bodies can later explode the LLM context.
        description = (
            "Meeting extracted from Gmail. "
            f"Sender: {sender}. "
            f"Subject: {subject}."
        )

        # ==========================================
        # CALENDAR TOOL ARGUMENTS
        # ==========================================

        tool_arguments = {
            "summary": summary,
            "start": start_dt.isoformat(),
            "end": end_dt.isoformat(),
            "description": description,
            "location": location,
            "timezone": "Asia/Karachi",
        }

        # ==========================================
        # FINAL CALENDAR PLAN
        # ==========================================

        return {
            "selected_tool": "create_event",
            "tool_arguments": tool_arguments,
            "reason": (
                "Meeting title, date, start time, "
                "end time, and location were "
                "successfully extracted from Gmail."
            ),
        }

    # ==========================================
    # FINAL RESPONSE
    # ==========================================

    def generate_final_response(
        self,
        user_message: str,
        result: Any,
        conversation_history: Optional[
            List[Dict[str, str]]
        ] = None,
    ) -> str:
        """
        Generate a concise final response.

        Only a small, sanitized version of the tool result is
        sent to Ollama. This prevents large Gmail/Calendar
        results from exceeding the model context window.
        """

        history_text = self._format_history(
            conversation_history or []
        )

        compact_result = self._compact_result(
            result
        )

        system_prompt = """
You are Larvi, an autonomous Email and Calendar AI assistant.

Generate a concise and helpful response.

Rules:
- Never claim an action succeeded unless the supplied result confirms success.
- Never invent email information.
- Never invent calendar information.
- If an operation failed, explain the failure briefly.
- Mention only important details.
- Do not repeat raw tool output.
- Keep the response under 100 words.
- If a calendar event was created successfully, say it was added to the calendar.
- If an email was sent/replied to successfully, say it was sent/replied.
""".strip()

        prompt = (
            f"Conversation history:\n{history_text}\n\n"
            f"User request:\n{user_message[:2000]}\n\n"
            f"Verified tool result:\n{compact_result}"
        )

        try:
            response = self.llm.invoke(
                [
                    SystemMessage(
                        content=system_prompt
                    ),
                    HumanMessage(
                        content=prompt
                    ),
                ]
            )

            text = str(
                response.content
            ).strip()

            if text:
                return text

        except Exception:
            # Do not expose the context-window error to the user.
            # Use the deterministic fallback below.
            pass

        return self._fallback_final_response(
            result
        )

    # ==========================================
    # RESULT COMPACTION
    # ==========================================

    @staticmethod
    def _compact_result(
        result: Any,
    ) -> str:
        """
        Keep only the fields needed to generate a final answer.
        Never send the complete Gmail result/history to Ollama.
        """

        if result is None:
            return "No result was returned."

        try:
            if isinstance(result, dict):
                # LangGraph may pass the complete state. Prefer the
                # actual tool result instead of the whole state.
                if "tool_result" in result:
                    result = result.get("tool_result")

                elif "workflow_data" in result:
                    workflow_data = result.get("workflow_data")
                    if isinstance(workflow_data, dict):
                        for key in (
                            "tool_result",
                            "email_result",
                            "calendar_result",
                        ):
                            if key in workflow_data:
                                result = workflow_data[key]
                                break

            if isinstance(result, dict):
                useful_keys = {
                    "success",
                    "status",
                    "message",
                    "error",
                    "sender",
                    "recipient",
                    "subject",
                    "summary",
                    "title",
                    "start",
                    "end",
                    "date",
                    "time",
                    "timezone",
                    "event_id",
                    "message_id",
                    "location",
                }

                compact = {
                    key: value
                    for key, value in result.items()
                    if key in useful_keys
                }

                if compact:
                    return json.dumps(
                        compact,
                        default=str,
                    )[:6000]

                return json.dumps(
                    result,
                    default=str,
                )[:6000]

            if isinstance(result, list):
                # Only a few records are enough for final wording.
                return json.dumps(
                    result[:5],
                    default=str,
                )[:6000]

            return str(result)[:6000]

        except Exception:
            return str(result)[:6000]

    # ==========================================
    # DETERMINISTIC FINAL RESPONSE
    # ==========================================

    @staticmethod
    def _fallback_final_response(
        result: Any,
    ) -> str:
        """Safe response if the final LLM call fails."""

        if isinstance(result, dict):
            if "tool_result" in result:
                result = result.get("tool_result")

            if isinstance(result, dict):
                if result.get("error"):
                    return (
                        "The operation failed: "
                        f"{str(result.get('error'))[:500]}"
                    )

                if result.get("event_id"):
                    return (
                        "Done. The meeting was added "
                        "to your calendar."
                    )

                if result.get("message_id"):
                    return (
                        "Done. The email operation "
                        "was completed successfully."
                    )

                if result.get("success") is True:
                    message = result.get("message")
                    if message:
                        return str(message)[:500]
                    return (
                        "Done. The requested action "
                        "was completed successfully."
                    )

        if isinstance(result, list):
            if not result:
                return "I couldn't find anything matching your request."
            return f"I found {len(result)} matching result(s)."

        return "I completed the operation successfully."

    # ==========================================
    # AGENT ACCESS
    # ==========================================

    def get_agent(
        self,
        agent_name: str,
    ):

        agent = self.agents.get(
            agent_name
        )

        if agent is None:

            raise ValueError(
                f"Agent '{agent_name}' was not found."
            )

        return agent

    # ==========================================
    # HISTORY FORMATTER
    # ==========================================

    @staticmethod
    def _format_history(
        history: List[Dict[str, str]],
    ) -> str:

        if not history:

            return (
                "No previous conversation."
            )

        lines = []

        for message in history[-4:]:

            role = message.get(
                "role",
                "unknown",
            )

            content = str(message.get(
                "content",
                "",
            ))[:1200]

            lines.append(
                f"{role}: {content}"
            )

        return "\n".join(lines)

    # ==========================================
    # JSON PARSER
    # ==========================================

    @staticmethod
    def _parse_json_response(
        content: Any,
    ) -> Dict[str, Any]:

        if isinstance(
            content,
            list,
        ):

            content = "".join(
                str(item)
                for item in content
            )

        text = str(
            content
        ).strip()

        if text.startswith(
            "```"
        ):

            text = (
                text.replace(
                    "```json",
                    "",
                )
                .replace(
                    "```",
                    "",
                )
                .strip()
            )

        try:

            parsed = json.loads(
                text
            )

            if isinstance(
                parsed,
                dict,
            ):

                return parsed

        except json.JSONDecodeError:

            pass

        return {}


# ==========================================
# MASTER AGENT INSTANCE
# ==========================================

master_agent = MasterAgent()
