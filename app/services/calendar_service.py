from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials

from app.config.constants import DEFAULT_EVENT_DURATION_MINUTES
from app.services.oauth_service import oauth_service


# ==========================================
# DEFAULT CALENDAR TIMEZONE
# ==========================================

DEFAULT_CALENDAR_TIMEZONE = "Asia/Karachi"


class CalendarService:
    """
    Handles all Google Calendar API operations for Larvi.
    """

    def __init__(self) -> None:
        self._credentials: Optional[Credentials] = None
        self._service = None

    # ==========================================
    # AUTHENTICATION
    # ==========================================

    def set_credentials(
        self,
        credentials: Credentials,
    ) -> None:
        """
        Set Google credentials and initialize
        the Google Calendar API client.
        """

        credentials = oauth_service.refresh_credentials(
            credentials
        )

        if not oauth_service.credentials_are_valid(
            credentials
        ):
            raise ValueError(
                "Invalid or expired Google credentials."
            )

        self._credentials = credentials

        self._service = build(
            "calendar",
            "v3",
            credentials=credentials,
            cache_discovery=False,
        )

    def is_authenticated(self) -> bool:
        """
        Check whether Google Calendar is connected.
        """

        return (
            self._service is not None
            and self._credentials is not None
            and oauth_service.credentials_are_valid(
                self._credentials
            )
        )

    def _get_service(self):
        """
        Return the Google Calendar API client.
        """

        if not self.is_authenticated():
            raise RuntimeError(
                "Google Calendar is not connected. "
                "Please connect your Google account first."
            )

        return self._service

    # ==========================================
    # GET EVENTS
    # ==========================================

    def get_events(
        self,
        time_min: Optional[str] = None,
        time_max: Optional[str] = None,
        max_results: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve upcoming calendar events.
        """

        if max_results < 1:
            raise ValueError(
                "max_results must be greater than zero."
            )

        service = self._get_service()

        if time_min is None:
            time_min = self._current_utc_time()

        try:
            response = (
                service.events()
                .list(
                    calendarId="primary",
                    timeMin=time_min,
                    timeMax=time_max,
                    maxResults=max_results,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )

            return [
                self._parse_event(event)
                for event in response.get(
                    "items",
                    [],
                )
            ]

        except HttpError as exc:
            raise RuntimeError(
                f"Unable to retrieve calendar events: {exc}"
            ) from exc

    # ==========================================
    # SEARCH EVENTS
    # ==========================================

    def search_events(
        self,
        query: str,
        time_min: Optional[str] = None,
        time_max: Optional[str] = None,
        max_results: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Search calendar events by text.
        """

        if not query.strip():
            raise ValueError(
                "Calendar search query cannot be empty."
            )

        service = self._get_service()

        if time_min is None:
            time_min = self._current_utc_time()

        try:
            response = (
                service.events()
                .list(
                    calendarId="primary",
                    q=query,
                    timeMin=time_min,
                    timeMax=time_max,
                    maxResults=max_results,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )

            return [
                self._parse_event(event)
                for event in response.get(
                    "items",
                    [],
                )
            ]

        except HttpError as exc:
            raise RuntimeError(
                f"Calendar event search failed: {exc}"
            ) from exc

    # ==========================================
    # GET EVENT
    # ==========================================

    def get_event(
        self,
        event_id: str,
    ) -> Dict[str, Any]:
        """
        Retrieve a specific calendar event.
        """

        if not event_id.strip():
            raise ValueError(
                "Event ID is required."
            )

        service = self._get_service()

        try:
            event = (
                service.events()
                .get(
                    calendarId="primary",
                    eventId=event_id,
                )
                .execute()
            )

            return self._parse_event(event)

        except HttpError as exc:
            raise RuntimeError(
                f"Unable to retrieve calendar event: {exc}"
            ) from exc

    # ==========================================
    # CHECK AVAILABILITY
    # ==========================================

    def check_availability(
        self,
        start: str,
        end: str,
    ) -> Dict[str, Any]:
        """
        Check whether the user's primary calendar
        is free during a specified time range.
        """

        self._validate_datetime_range(
            start,
            end,
        )

        # Normalize naive datetimes before sending
        # them to Google Calendar.
        start = self._normalize_datetime(start)
        end = self._normalize_datetime(end)

        service = self._get_service()

        request_body = {
            "timeMin": start,
            "timeMax": end,
            "items": [
                {
                    "id": "primary",
                }
            ],
        }

        try:
            response = (
                service.freebusy()
                .query(
                    body=request_body
                )
                .execute()
            )

            calendar_data = (
                response.get(
                    "calendars",
                    {},
                )
                .get(
                    "primary",
                    {},
                )
            )

            conflicts = calendar_data.get(
                "busy",
                []
            )

            return {
                "available": len(conflicts) == 0,
                "start": start,
                "end": end,
                "conflicts": conflicts,
            }

        except HttpError as exc:
            raise RuntimeError(
                f"Unable to check calendar availability: {exc}"
            ) from exc

    # ==========================================
    # CREATE EVENT
    # ==========================================

    def create_event(
        self,
        summary: str,
        start: str,
        end: Optional[str] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
        timezone: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create an event in the user's primary calendar.
        """

        if not summary.strip():
            raise ValueError(
                "Event title is required."
            )

        if end is None:
            end = self._calculate_end_time(
                start
            )

        self._validate_datetime_range(
            start,
            end,
        )

        service = self._get_service()

        event_body = {
            "summary": summary.strip(),
            "start": self._build_datetime_field(
                start,
                timezone,
            ),
            "end": self._build_datetime_field(
                end,
                timezone,
            ),
        }

        if description:
            event_body["description"] = (
                description.strip()
            )

        if location:
            event_body["location"] = (
                location.strip()
            )

        try:
            event = (
                service.events()
                .insert(
                    calendarId="primary",
                    body=event_body,
                )
                .execute()
            )

            return {
                "status": "success",
                **self._parse_event(event),
            }

        except HttpError as exc:
            raise RuntimeError(
                f"Unable to create calendar event: {exc}"
            ) from exc

    # ==========================================
    # RESOLVE EVENT ID
    # ==========================================

    def _resolve_event_id(
        self,
        event_id: str,
    ) -> str:
        """
        Resolve a real Google Calendar event ID.

        Larvi sometimes receives an event title from the
        LLM instead of Google's actual event ID. Google
        Calendar requires the real event ID for update/delete,
        so if the supplied value is not a valid ID, search by
        title and return the matching event's real ID.
        """

        candidate = event_id.strip()

        if not candidate:
            raise ValueError(
                "Event ID or event title is required."
            )

        service = self._get_service()

        # A real Google event ID normally contains no spaces.
        # Try it directly first for callers that already provide
        # the correct ID.
        if " " not in candidate:
            try:
                (
                    service.events()
                    .get(
                        calendarId="primary",
                        eventId=candidate,
                    )
                    .execute()
                )
                return candidate
            except HttpError as exc:
                if getattr(exc, "resp", None) is None or exc.resp.status != 404:
                    raise

        # Fallback: treat the supplied value as the event title.
        try:
            response = (
                service.events()
                .list(
                    calendarId="primary",
                    q=candidate,
                    maxResults=50,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
        except HttpError as exc:
            raise RuntimeError(
                f"Unable to search calendar events while resolving '{candidate}': {exc}"
            ) from exc

        events = response.get("items", [])
        candidate_lower = candidate.casefold()

        # Prefer an exact title match.
        for event in events:
            summary = str(event.get("summary", "")).strip()
            if summary.casefold() == candidate_lower:
                real_id = event.get("id")
                if real_id:
                    return real_id

        # If there is no exact match, allow a single search result
        # to be used. This keeps natural-language title references
        # useful without guessing between multiple events.
        if len(events) == 1 and events[0].get("id"):
            return events[0]["id"]

        raise ValueError(
            f"Could not find a calendar event named '{candidate}'."
        )

    # ==========================================
    # UPDATE EVENT
    # ==========================================

    def update_event(
        self,
        event_id: str,
        summary: Optional[str] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
        timezone: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update an existing calendar event.
        """

        if not event_id.strip():
            raise ValueError(
                "Event ID is required."
            )

        if start is not None and end is None:
            end = self._calculate_end_time(
                start
            )

        if start is not None and end is not None:
            self._validate_datetime_range(
                start,
                end,
            )

        service = self._get_service()
        resolved_event_id = self._resolve_event_id(event_id)

        try:
            event = (
                service.events()
                .get(
                    calendarId="primary",
                    eventId=resolved_event_id,
                )
                .execute()
            )

            if summary is not None:
                if not summary.strip():
                    raise ValueError(
                        "Event title cannot be empty."
                    )

                event["summary"] = summary.strip()

            if start is not None:
                event["start"] = (
                    self._build_datetime_field(
                        start,
                        timezone,
                    )
                )

            if end is not None:
                event["end"] = (
                    self._build_datetime_field(
                        end,
                        timezone,
                    )
                )

            if description is not None:
                event["description"] = (
                    description.strip()
                )

            if location is not None:
                event["location"] = (
                    location.strip()
                )

            updated_event = (
                service.events()
                .update(
                    calendarId="primary",
                    eventId=resolved_event_id,
                    body=event,
                )
                .execute()
            )

            return {
                "status": "success",
                **self._parse_event(
                    updated_event
                ),
            }

        except HttpError as exc:
            raise RuntimeError(
                f"Unable to update calendar event: {exc}"
            ) from exc

    # ==========================================
    # DELETE EVENT
    # ==========================================

    def delete_event(
        self,
        event_id: str,
    ) -> bool:
        """
        Delete an event from the user's primary calendar.
        """

        if not event_id.strip():
            raise ValueError(
                "Event ID is required."
            )

        service = self._get_service()
        resolved_event_id = self._resolve_event_id(event_id)

        try:
            (
                service.events()
                .delete(
                    calendarId="primary",
                    eventId=resolved_event_id,
                )
                .execute()
            )

            return True

        except HttpError as exc:
            raise RuntimeError(
                f"Unable to delete calendar event: {exc}"
            ) from exc

    # ==========================================
    # PARSE EVENT
    # ==========================================

    @staticmethod
    def _parse_event(
        event: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Convert Google's event response into a clean
        dictionary for Larvi.
        """

        start_data = event.get(
            "start",
            {},
        )

        end_data = event.get(
            "end",
            {},
        )

        return {
            "id": event.get(
                "id"
            ),
            "summary": event.get(
                "summary",
                "",
            ),
            "description": event.get(
                "description",
                "",
            ),
            "location": event.get(
                "location",
                "",
            ),
            "start": (
                start_data.get(
                    "dateTime"
                )
                or start_data.get(
                    "date"
                )
            ),
            "end": (
                end_data.get(
                    "dateTime"
                )
                or end_data.get(
                    "date"
                )
            ),
            "timezone": (
                start_data.get(
                    "timeZone"
                )
                or end_data.get(
                    "timeZone"
                )
            ),
            "status": event.get(
                "status",
                "",
            ),
            "html_link": event.get(
                "htmlLink",
                "",
            ),
            "organizer": event.get(
                "organizer",
                {},
            ),
            "attendees": event.get(
                "attendees",
                [],
            ),
        }

    # ==========================================
    # DATETIME HELPERS
    # ==========================================

    @staticmethod
    def _current_utc_time() -> str:
        """
        Return the current UTC time in ISO format.
        """

        return (
            datetime.now(
                timezone.utc
            )
            .isoformat()
            .replace(
                "+00:00",
                "Z",
            )
        )

    @staticmethod
    def _calculate_end_time(
        start: str,
    ) -> str:
        """
        Calculate an event end time using the default
        event duration.
        """

        try:
            start_datetime = (
                CalendarService
                ._parse_datetime(
                    start
                )
            )

            end_datetime = (
                start_datetime
                + timedelta(
                    minutes=(
                        DEFAULT_EVENT_DURATION_MINUTES
                    )
                )
            )

            return end_datetime.isoformat()

        except ValueError as exc:
            raise ValueError(
                "Invalid event start datetime."
            ) from exc

    @staticmethod
    def _build_datetime_field(
        value: str,
        timezone_name: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Build the datetime object expected by
        Google Calendar API.

        The datetime is converted to the requested
        timezone and sent with an explicit RFC3339
        UTC offset. The Calendar API does not need
        the optional timeZone field for single events.
        """

        normalized_value = value.strip()

        # ------------------------------------------
        # DEFAULT TIMEZONE
        # ------------------------------------------

        timezone_name = (
            timezone_name
            or DEFAULT_CALENDAR_TIMEZONE
        )

        if timezone_name == DEFAULT_CALENDAR_TIMEZONE:
            zone = timezone(timedelta(hours=5))
        else:
            try:
                from zoneinfo import ZoneInfo
                zone = ZoneInfo(timezone_name)
            except Exception as exc:
                raise ValueError(
                    f"Invalid timezone: {timezone_name}"
                ) from exc

        # ------------------------------------------
        # PARSE DATETIME
        # ------------------------------------------

        parsed = CalendarService._parse_datetime(
            normalized_value
        )

        # ------------------------------------------
        # CONVERT TO REQUESTED TIMEZONE
        # ------------------------------------------

        parsed = parsed.astimezone(zone)

        # ------------------------------------------
        # GOOGLE CALENDAR DATETIME
        # ------------------------------------------
        # Send the explicit +05:00 offset instead of
        # sending "Asia/Karachi" in the timeZone field.
        # This avoids the current Calendar API timezone
        # error while preserving the correct local time.

        return {
            "dateTime": parsed.isoformat(),
        }

    @staticmethod
    def _normalize_datetime(
        value: str,
    ) -> str:
        """
        Normalize a datetime for Google Calendar API.

        Naive datetimes are interpreted as Asia/Karachi.
        """

        parsed = CalendarService._parse_datetime(
            value
        )

        return parsed.isoformat()

    @staticmethod
    def _parse_datetime(
        value: str,
    ) -> datetime:
        """
        Parse an ISO datetime string.

        Naive datetimes are treated as Asia/Karachi
        instead of UTC.
        """

        normalized = value.strip()

        if normalized.endswith("Z"):
            normalized = (
                normalized[:-1]
                + "+00:00"
            )

        parsed = datetime.fromisoformat(
            normalized
        )

        if parsed.tzinfo is None:
            parsed = parsed.replace(
                tzinfo=timezone(
                    timedelta(hours=5)
                )
            )

        return parsed

    @staticmethod
    def _validate_datetime_range(
        start: str,
        end: str,
    ) -> None:
        """
        Validate that start and end are valid
        datetimes and that end occurs after start.
        """

        try:
            start_datetime = (
                CalendarService
                ._parse_datetime(
                    start
                )
            )

            end_datetime = (
                CalendarService
                ._parse_datetime(
                    end
                )
            )

        except ValueError as exc:
            raise ValueError(
                "Invalid calendar datetime format."
            ) from exc

        if end_datetime <= start_datetime:
            raise ValueError(
                "Event end time must be after start time."
            )


calendar_service = CalendarService()
