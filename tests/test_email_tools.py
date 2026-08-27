from unittest.mock import patch

from app.tools.email_tools import (
    create_draft,
    get_recent_emails,
    read_email,
    reply_email,
    search_emails,
    send_email,
)


def test_search_emails():
    expected = [
        {
            "message_id": "123",
            "subject": "Project Update",
            "sender": "ahmed@example.com",
        }
    ]

    with patch(
        "app.tools.email_tools.gmail_service.search_emails",
        return_value=expected,
    ) as mock_search:

        result = search_emails(
            query="from:ahmed@example.com",
            max_results=10,
        )

        mock_search.assert_called_once_with(
            query="from:ahmed@example.com",
            max_results=10,
        )

        assert result == expected


def test_read_email():
    expected = {
        "message_id": "123",
        "subject": "Project Update",
        "body": "Project meeting is tomorrow.",
    }

    with patch(
        "app.tools.email_tools.gmail_service.get_email",
        return_value=expected,
    ) as mock_get:

        result = read_email("123")

        mock_get.assert_called_once_with(
            message_id="123",
        )

        assert result == expected


def test_get_recent_emails():
    expected = [
        {
            "message_id": "123",
            "subject": "Latest Email",
        }
    ]

    with patch(
        "app.tools.email_tools.gmail_service.get_recent_emails",
        return_value=expected,
    ) as mock_recent:

        result = get_recent_emails(max_results=5)

        mock_recent.assert_called_once_with(
            max_results=5,
        )

        assert result == expected


def test_create_draft():
    expected = {
        "id": "draft_123",
        "message": {
            "id": "123",
        },
    }

    with patch(
        "app.tools.email_tools.gmail_service.create_draft",
        return_value=expected,
    ) as mock_draft:

        result = create_draft(
            recipient="ali@example.com",
            subject="Project Update",
            body="Here is the project update.",
        )

        mock_draft.assert_called_once_with(
            recipient="ali@example.com",
            subject="Project Update",
            body="Here is the project update.",
        )

        assert result == expected


def test_send_email():
    expected = {
        "id": "sent_123",
        "threadId": "thread_123",
    }

    with patch(
        "app.tools.email_tools.gmail_service.send_email",
        return_value=expected,
    ) as mock_send:

        result = send_email(
            recipient="ali@example.com",
            subject="Project Update",
            body="Here is the project update.",
        )

        mock_send.assert_called_once_with(
            recipient="ali@example.com",
            subject="Project Update",
            body="Here is the project update.",
        )

        assert result == expected


def test_reply_email():
    expected = {
        "id": "reply_123",
        "threadId": "thread_123",
    }

    with patch(
        "app.tools.email_tools.gmail_service.reply_to_email",
        return_value=expected,
    ) as mock_reply:

        result = reply_email(
            message_id="123",
            body="Thanks for the update.",
        )

        mock_reply.assert_called_once_with(
            message_id="123",
            body="Thanks for the update.",
        )

        assert result == expected