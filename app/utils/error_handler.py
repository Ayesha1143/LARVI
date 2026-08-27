from typing import Any, Dict

from fastapi import HTTPException
from googleapiclient.errors import HttpError


def handle_exception(
    exc: Exception,
) -> Dict[str, Any]:
    """
    Convert internal exceptions into a consistent
    Larvi error response.
    """

    if isinstance(exc, HTTPException):
        return {
            "status": "error",
            "error_type": "http_error",
            "message": str(
                exc.detail
            ),
        }

    if isinstance(exc, HttpError):
        status_code = getattr(
            exc.resp,
            "status",
            None,
        )

        if status_code == 401:
            message = (
                "Google authentication has expired. "
                "Please reconnect your Google account."
            )

        elif status_code == 403:
            message = (
                "Larvi does not have permission to "
                "perform this Google operation."
            )

        elif status_code == 404:
            message = (
                "The requested Google resource "
                "could not be found."
            )

        elif status_code == 429:
            message = (
                "Google API rate limit was reached. "
                "Please try again later."
            )

        else:
            message = (
                "The Google API could not complete "
                "the requested operation."
            )

        return {
            "status": "error",
            "error_type": "google_api_error",
            "message": message,
            "status_code": status_code,
        }

    if isinstance(exc, ValueError):
        return {
            "status": "error",
            "error_type": "validation_error",
            "message": str(exc),
        }

    if isinstance(exc, RuntimeError):
        return {
            "status": "error",
            "error_type": "runtime_error",
            "message": str(exc),
        }

    return {
        "status": "error",
        "error_type": "internal_error",
        "message": (
            "An unexpected error occurred "
            "while processing the request."
        ),
    }


def get_user_friendly_error(
    exc: Exception,
) -> str:
    """
    Return only the user-facing error message.
    """

    result = handle_exception(exc)

    return result.get(
        "message",
        "An unexpected error occurred.",
    )