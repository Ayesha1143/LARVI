from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4


def generate_conversation_id() -> str:
    """
    Generate a unique conversation ID.
    """

    return str(uuid4())


def get_current_utc_time() -> str:
    """
    Return the current UTC time in ISO 8601 format.
    """

    return (
        datetime.now(timezone.utc)
        .isoformat()
        .replace("+00:00", "Z")
    )


def calculate_end_time(
    start: str,
    duration_minutes: int = 60,
) -> str:
    """
    Calculate an event end time from a start time.
    """

    if duration_minutes <= 0:
        raise ValueError(
            "Duration must be greater than zero."
        )

    normalized = start.strip()

    if normalized.endswith("Z"):
        normalized = (
            normalized[:-1]
            + "+00:00"
        )

    try:
        start_datetime = datetime.fromisoformat(
            normalized
        )
    except ValueError as exc:
        raise ValueError(
            "Invalid datetime format."
        ) from exc

    if start_datetime.tzinfo is None:
        start_datetime = start_datetime.replace(
            tzinfo=timezone.utc
        )

    end_datetime = (
        start_datetime
        + timedelta(
            minutes=duration_minutes
        )
    )

    return end_datetime.isoformat()


def normalize_datetime(
    value: str,
) -> str:
    """
    Normalize an ISO datetime into a consistent
    format accepted by Google APIs.
    """

    if not value or not value.strip():
        raise ValueError(
            "Datetime value is required."
        )

    normalized = value.strip()

    if normalized.endswith("Z"):
        normalized = (
            normalized[:-1]
            + "+00:00"
        )

    try:
        parsed = datetime.fromisoformat(
            normalized
        )
    except ValueError as exc:
        raise ValueError(
            "Invalid datetime format."
        ) from exc

    if parsed.tzinfo is None:
        parsed = parsed.replace(
            tzinfo=timezone.utc
        )

    return (
        parsed.isoformat()
    )


def trim_conversation_history(
    history: List[Dict[str, str]],
    max_messages: int = 20,
) -> List[Dict[str, str]]:
    """
    Keep only the most recent conversation messages.
    """

    if max_messages <= 0:
        return []

    return history[-max_messages:]


def safe_string(
    value: Optional[Any],
) -> str:
    """
    Convert a value safely into a string.
    """

    if value is None:
        return ""

    return str(value).strip()


def is_successful_result(
    result: Any,
) -> bool:
    """
    Determine whether a tool/service result explicitly
    indicates successful execution.
    """

    if result is True:
        return True

    if not isinstance(result, dict):
        return False

    return result.get(
        "status"
    ) == "success"


def build_error_result(
    message: str,
    error_type: str = "operation_error",
) -> Dict[str, Any]:
    """
    Create a consistent error result.
    """

    return {
        "status": "error",
        "error_type": error_type,
        "message": message,
    }