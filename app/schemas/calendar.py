from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class CalendarEvent(BaseModel):
    id: str
    summary: str = ""
    description: str = ""
    location: str = ""
    start: Optional[str] = None
    end: Optional[str] = None
    timezone: Optional[str] = None
    status: str = ""
    html_link: str = ""
    organizer: Dict[str, Any] = Field(
        default_factory=dict
    )
    attendees: List[Dict[str, Any]] = Field(
        default_factory=list
    )


class EventSearchRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=1,
        description="Calendar event search query.",
    )

    time_min: Optional[str] = None
    time_max: Optional[str] = None

    max_results: int = Field(
        default=20,
        ge=1,
        le=100,
    )


class AvailabilityRequest(BaseModel):
    start: str = Field(
        ...,
        min_length=1,
    )

    end: str = Field(
        ...,
        min_length=1,
    )


class EventCreateRequest(BaseModel):
    summary: str = Field(
        ...,
        min_length=1,
    )

    start: str = Field(
        ...,
        min_length=1,
    )

    end: Optional[str] = None

    description: Optional[str] = None
    location: Optional[str] = None
    timezone: Optional[str] = None


class EventUpdateRequest(BaseModel):
    event_id: str = Field(
        ...,
        min_length=1,
    )

    summary: Optional[str] = None
    start: Optional[str] = None
    end: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    timezone: Optional[str] = None


class EventDeleteRequest(BaseModel):
    event_id: str = Field(
        ...,
        min_length=1,
    )