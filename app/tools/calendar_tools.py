from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from langchain_core.tools import tool

from app.services.calendar_service import calendar_service


# ==========================================
# GET TODAY'S EVENTS
# ==========================================

@tool
def get_today_events(
    max_results: int = 20,
) -> List[Dict[str, Any]]:
    """
    Retrieve all events from the user's primary
    Google Calendar for today.
    """

    now = datetime.now(timezone.utc)

    start_of_day = now.replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )

    end_of_day = start_of_day.replace(
        hour=23,
        minute=59,
        second=59,
        microsecond=999999,
    )

    return calendar_service.get_events(
        time_min=start_of_day.isoformat(),
        time_max=end_of_day.isoformat(),
        max_results=max_results,
    )


# ==========================================
# GET EVENTS
# ==========================================

@tool
def get_events(
    time_min: Optional[str] = None,
    time_max: Optional[str] = None,
    max_results: int = 20,
) -> List[Dict[str, Any]]:
    """
    Retrieve upcoming events from the user's primary
    Google Calendar.
    """

    return calendar_service.get_events(
        time_min=time_min,
        time_max=time_max,
        max_results=max_results,
    )


# ==========================================
# SEARCH EVENTS
# ==========================================

@tool
def search_events(
    query: str,
    time_min: Optional[str] = None,
    time_max: Optional[str] = None,
    max_results: int = 20,
) -> List[Dict[str, Any]]:
    """
    Search the user's Google Calendar for events
    matching the given query.
    """

    return calendar_service.search_events(
        query=query,
        time_min=time_min,
        time_max=time_max,
        max_results=max_results,
    )


# ==========================================
# CHECK AVAILABILITY
# ==========================================

@tool
def check_availability(
    start: str,
    end: str,
) -> Dict[str, Any]:
    """
    Check whether the user's primary calendar is free
    during the specified time range.
    """

    return calendar_service.check_availability(
        start=start,
        end=end,
    )


# ==========================================
# CREATE EVENT
# ==========================================

@tool
def create_event(
    summary: str,
    start: str,
    end: Optional[str] = None,
    description: Optional[str] = None,
    location: Optional[str] = None,
    timezone: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a new event in the user's Google Calendar.

    This is an external action and should only be
    executed after Larvi's confirmation/safety logic
    determines that execution is appropriate.
    """

    return calendar_service.create_event(
        summary=summary,
        start=start,
        end=end,
        description=description,
        location=location,
        timezone=timezone,
    )


# ==========================================
# UPDATE EVENT
# ==========================================

@tool
def update_event(
    event_id: str,
    summary: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    description: Optional[str] = None,
    location: Optional[str] = None,
    timezone: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Update an existing Google Calendar event.

    This is an external action and should only be
    executed after Larvi's confirmation/safety logic
    determines that execution is appropriate.
    """

    return calendar_service.update_event(
        event_id=event_id,
        summary=summary,
        start=start,
        end=end,
        description=description,
        location=location,
        timezone=timezone,
    )


# ==========================================
# DELETE EVENT
# ==========================================

@tool
def delete_event(
    event_id: str,
) -> bool:
    """
    Delete an existing Google Calendar event.

    This is a destructive external action and should
    only be executed after explicit confirmation.
    """

    return calendar_service.delete_event(
        event_id=event_id,
    )


# ==========================================
# CALENDAR TOOLS
# ==========================================

CALENDAR_TOOLS = [
    get_today_events,
    get_events,
    search_events,
    check_availability,
    create_event,
    update_event,
    delete_event,
]