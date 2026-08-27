from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse

from app.services.calendar_service import calendar_service
from app.services.gmail_service import gmail_service
from app.services.oauth_service import oauth_service


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


_oauth_states: set[str] = set()


@router.get("/login")
async def google_login():
    """
    Start Google OAuth 2.0 authentication.
    """

    try:
        auth_data = oauth_service.create_authorization_url()

        state = auth_data["state"]

        _oauth_states.add(state)

        return RedirectResponse(
            url=auth_data["authorization_url"]
        )

    except Exception as exc:
        print("GOOGLE LOGIN ERROR:", repr(exc))

        raise HTTPException(
            status_code=500,
            detail=f"Unable to start Google authentication: {str(exc)}",
        ) from exc


@router.get("/callback")
async def google_callback(
    request: Request,
):
    """
    Handle Google's OAuth callback and initialize
    Gmail and Calendar services.
    """

    error = request.query_params.get("error")

    if error:
        raise HTTPException(
            status_code=400,
            detail=f"Google authentication failed: {error}",
        )

    code = request.query_params.get("code")

    state = request.query_params.get("state")

    if not code:
        raise HTTPException(
            status_code=400,
            detail="Google authorization code was not provided.",
        )

    if not state:
        raise HTTPException(
            status_code=400,
            detail="OAuth state was not provided.",
        )

    if state not in _oauth_states:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired OAuth state.",
        )

    try:
        print("GOOGLE CALLBACK STARTED")
        print("STATE:", state)
        print("CODE RECEIVED:", bool(code))

        credentials = (
            oauth_service.exchange_code_for_credentials(
                authorization_response=str(request.url),
                state=state,
            )
        )

        print("CREDENTIALS RECEIVED")

        if not oauth_service.credentials_are_valid(
            credentials
        ):
            raise ValueError(
                "Google credentials are invalid."
            )

        print("CREDENTIALS VALID")

        gmail_service.set_credentials(
            credentials
        )

        print("GMAIL CREDENTIALS SET")

        calendar_service.set_credentials(
            credentials
        )

        print("CALENDAR CREDENTIALS SET")

        _oauth_states.discard(state)

        frontend_url = (
            oauth_service.get_frontend_url()
        )

        print(
            "GOOGLE AUTHENTICATION SUCCESSFUL"
        )

        return RedirectResponse(
            url=frontend_url
        )

    except Exception as exc:
        print(
            "GOOGLE CALLBACK ERROR:",
            repr(exc)
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Google authentication failed: "
                f"{str(exc)}"
            ),
        ) from exc


@router.get("/status")
async def authentication_status():
    """
    Return the current Gmail and Calendar
    connection status.
    """

    gmail_connected = (
        gmail_service.is_authenticated()
    )

    calendar_connected = (
        calendar_service.is_authenticated()
    )

    return {
        "authenticated": (
            gmail_connected
            and calendar_connected
        ),
        "gmail_connected": gmail_connected,
        "calendar_connected": calendar_connected,
    }