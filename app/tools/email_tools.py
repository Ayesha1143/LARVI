from typing import Any, Dict, List

from langchain_core.tools import tool

from app.services.gmail_service import gmail_service


@tool
def search_emails(
    query: str,
    max_results: int = 20,
) -> List[Dict[str, Any]]:
    """
    Search the user's Gmail using a Gmail search query.

    Examples:
    - from:ahmed@example.com
    - subject:meeting
    - project update
    - is:unread
    """

    return gmail_service.search_emails(
        query=query,
        max_results=max_results,
    )


@tool
def read_email(
    message_id: str,
) -> Dict[str, Any]:
    """
    Read a specific email using its Gmail message ID.
    """

    return gmail_service.get_email(
        message_id=message_id,
    )


@tool
def get_recent_emails(
    max_results: int = 20,
) -> List[Dict[str, Any]]:
    """
    Retrieve the user's most recent Gmail messages.
    """

    return gmail_service.get_recent_emails(
        max_results=max_results,
    )


@tool
def create_draft(
    recipient: str,
    subject: str,
    body: str,
) -> Dict[str, Any]:
    """
    Create an email draft in Gmail.

    This does not send the email.
    """

    return gmail_service.create_draft(
        recipient=recipient,
        subject=subject,
        body=body,
    )


@tool
def send_email(
    recipient: str,
    subject: str,
    body: str,
) -> Dict[str, Any]:
    """
    Send an email through Gmail.

    This is an external action and should only be
    executed after Larvi's confirmation logic approves it.
    """

    return gmail_service.send_email(
        recipient=recipient,
        subject=subject,
        body=body,
    )


@tool
def reply_email(
    message_id: str,
    body: str,
) -> Dict[str, Any]:
    """
    Reply to an existing Gmail message.

    This is an external action and should only be
    executed after Larvi's confirmation logic approves it.
    """

    return gmail_service.reply_to_email(
        message_id=message_id,
        body=body,
    )


EMAIL_TOOLS = [
    search_emails,
    read_email,
    get_recent_emails,
    create_draft,
    send_email,
    reply_email,
]