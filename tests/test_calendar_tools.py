from unittest.mock import patch

from app.tools.calendar_tools import (
    check_availability,
    create_event,
    delete_event,
    get_events,
    search_events,
    update_event,
)


def test_get_events():
    expected = [
        {
            "id": "event_123",
            "summary": "Project Meeting",
        }
    ]

    with patch(
        "app.tools.calendar_tools.calendar_service.get_events",
        return_value=expected,
    ) as mock_get:

        result = get_events(
            time_min="2026-08-25T00:00:00Z",
            time_max="2026-08-26T00:00:00Z",
            max_results=10,
        )

        mock_get.assert_called_once_with(
            time_min="2026-08-25T00:00:00Z",
            time_max="2026-08-26T00:00:00Z",
            max_results=10,
        )

        assert result == expected


def test_search_events():
    expected = [
        {
            "id": "event_123",
            "summary": "Project Review",
        }
    ]

    with patch(
        "app.tools.calendar_tools.calendar_service.search_events",
        return_value=expected,
    ) as mock_search:

        result = search_events(
            query="Project Review",
            max_results=10,
        )

        mock_search.assert_called_once_with(
            query="Project Review",
            time_min=None,
            time_max=None,
            max_results=10,
        )

        assert result == expected


def test_check_availability():
    expected = {
        "available": True,
        "start": "2026-08-25T16:00:00Z",
        "end": "2026-08-25T17:00:00Z",
        "conflicts": [],
    }

    with patch(
        "app.tools.calendar_tools.calendar_service.check_availability",
        return_value=expected,
    ) as mock_check:

        result = check_availability(
            start="2026-08-25T16:00:00Z",
            end="2026-08-25T17:00:00Z",
        )

        mock_check.assert_called_once_with(
            start="2026-08-25T16:00:00Z",
            end="2026-08-25T17:00:00Z",
        )

        assert result == expected


def test_create_event():
    expected = {
        "id": "event_123",
        "summary": "Project Meeting",
    }

    with patch(
        "app.tools.calendar_tools.calendar_service.create_event",
        return_value=expected,
    ) as mock_create:

        result = create_event(
            summary="Project Meeting",
            start="2026-08-25T16:00:00Z",
            end="2026-08-25T17:00:00Z",
            description="Project discussion",
            location="Online",
            timezone="UTC",
        )

        mock_create.assert_called_once_with(
            summary="Project Meeting",
            start="2026-08-25T16:00:00Z",
            end="2026-08-25T17:00:00Z",
            description="Project discussion",
            location="Online",
            timezone="UTC",
        )

        assert result == expected


def test_update_event():
    expected = {
        "id": "event_123",
        "summary": "Updated Project Meeting",
    }

    with patch(
        "app.tools.calendar_tools.calendar_service.update_event",
        return_value=expected,
    ) as mock_update:

        result = update_event(
            event_id="event_123",
            summary="Updated Project Meeting",
            start="2026-08-25T17:00:00Z",
            end="2026-08-25T18:00:00Z",
        )

        mock_update.assert_called_once_with(
            event_id="event_123",
            summary="Updated Project Meeting",
            start="2026-08-25T17:00:00Z",
            end="2026-08-25T18:00:00Z",
            description=None,
            location=None,
            timezone=None,
        )

        assert result == expected


def test_delete_event():
    with patch(
        "app.tools.calendar_tools.calendar_service.delete_event",
        return_value=True,
    ) as mock_delete:

        result = delete_event("event_123")

        mock_delete.assert_called_once_with(
            event_id="event_123",
        )

        assert result is True