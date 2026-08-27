from unittest.mock import patch

from app.agents.calendar_agent import CalendarAgent
from app.agents.email_agent import EmailAgent


def test_email_agent_has_required_tools():
    agent = EmailAgent()

    tool_names = {
        tool.name
        for tool in agent.get_tools()
    }

    expected_tools = {
        "search_emails",
        "read_email",
        "get_recent_emails",
        "create_draft",
        "send_email",
        "reply_email",
    }

    assert expected_tools.issubset(tool_names)


def test_calendar_agent_has_required_tools():
    agent = CalendarAgent()

    tool_names = {
        tool.name
        for tool in agent.get_tools()
    }

    expected_tools = {
        "get_events",
        "search_events",
        "check_availability",
        "create_event",
        "update_event",
        "delete_event",
    }

    assert expected_tools.issubset(tool_names)


def test_email_agent_execute_tool():
    agent = EmailAgent()

    expected = [
        {
            "message_id": "123",
            "subject": "Project Meeting",
        }
    ]

    with patch(
        "app.agents.email_agent.search_emails",
        return_value=expected,
    ):

        result = agent.execute_tool(
            tool_name="search_emails",
            arguments={
                "query": "project meeting",
                "max_results": 10,
            },
        )

        assert result == expected


def test_calendar_agent_execute_tool():
    agent = CalendarAgent()

    expected = {
        "available": True,
        "start": "2026-08-25T16:00:00Z",
        "end": "2026-08-25T17:00:00Z",
        "conflicts": [],
    }

    with patch(
        "app.agents.calendar_agent.check_availability",
        return_value=expected,
    ):

        result = agent.execute_tool(
            tool_name="check_availability",
            arguments={
                "start": "2026-08-25T16:00:00Z",
                "end": "2026-08-25T17:00:00Z",
            },
        )

        assert result == expected


def test_email_agent_invalid_tool():
    agent = EmailAgent()

    try:
        agent.execute_tool(
            tool_name="invalid_email_tool",
            arguments={},
        )
        assert False

    except ValueError as exc:
        assert "was not found" in str(exc)


def test_calendar_agent_invalid_tool():
    agent = CalendarAgent()

    try:
        agent.execute_tool(
            tool_name="invalid_calendar_tool",
            arguments={},
        )
        assert False

    except ValueError as exc:
        assert "was not found" in str(exc)