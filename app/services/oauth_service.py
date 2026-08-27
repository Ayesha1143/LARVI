import os

# LOCAL DEVELOPMENT ONLY
# Allows OAuth callback on http://127.0.0.1
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

import json
import secrets
from pathlib import Path
from typing import Any, Dict, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

from app.config.constants import (
    CALENDAR_SCOPES,
    GMAIL_SCOPES,
    GOOGLE_AUTH_URI,
    GOOGLE_TOKEN_URI,
)
from app.config.settings import settings


class OAuthService:
    """
    Handles Google OAuth 2.0 authentication for Gmail
    and Google Calendar.
    """

    def __init__(self) -> None:
        self.client_config = {
            "web": {
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "auth_uri": GOOGLE_AUTH_URI,
                "token_uri": GOOGLE_TOKEN_URI,
                "redirect_uris": [
                    settings.google_redirect_uri
                ],
            }
        }

        # Store PKCE code verifiers temporarily.
        # Key = OAuth state
        self._code_verifiers: dict[str, str] = {}

    # ==========================================
    # AUTHORIZATION URL
    # ==========================================

    def create_authorization_url(self) -> Dict[str, str]:
        """
        Create Google's OAuth authorization URL
        and generate a PKCE code verifier.
        """

        state = secrets.token_urlsafe(32)

        flow = Flow.from_client_config(
            self.client_config,
            scopes=self._get_all_scopes(),
            state=state,
        )

        flow.redirect_uri = settings.google_redirect_uri

        # Generate PKCE verifier manually.
        code_verifier = secrets.token_urlsafe(64)

        # Save verifier using OAuth state.
        self._code_verifiers[state] = code_verifier

        authorization_url, returned_state = (
            flow.authorization_url(
                access_type="offline",
                include_granted_scopes="true",
                prompt="consent",
                code_challenge_method="S256",
                code_challenge=self._create_code_challenge(
                    code_verifier
                ),
            )
        )

        return {
            "authorization_url": authorization_url,
            "state": returned_state,
        }

    # ==========================================
    # PKCE CODE CHALLENGE
    # ==========================================

    @staticmethod
    def _create_code_challenge(
        code_verifier: str,
    ) -> str:
        """
        Create an S256 PKCE code challenge.
        """

        import base64
        import hashlib

        digest = hashlib.sha256(
            code_verifier.encode("ascii")
        ).digest()

        return (
            base64.urlsafe_b64encode(
                digest
            )
            .decode("ascii")
            .rstrip("=")
        )

    # ==========================================
    # AUTHORIZATION CALLBACK
    # ==========================================

    def exchange_code_for_credentials(
        self,
        authorization_response: str,
        state: Optional[str] = None,
    ) -> Credentials:
        """
        Exchange Google's authorization code for
        access and refresh credentials.
        """

        if not state:
            raise ValueError(
                "OAuth state is required."
            )

        code_verifier = self._code_verifiers.get(
            state
        )

        if not code_verifier:
            raise ValueError(
                "OAuth code verifier was not found "
                "for this authentication request."
            )

        flow = Flow.from_client_config(
            self.client_config,
            scopes=self._get_all_scopes(),
            state=state,
        )

        flow.redirect_uri = settings.google_redirect_uri

        flow.fetch_token(
            authorization_response=authorization_response,
            code_verifier=code_verifier,
        )

        # Authentication succeeded.
        # Remove the verifier so it cannot be reused.
        self._code_verifiers.pop(
            state,
            None,
        )

        return flow.credentials

    # ==========================================
    # FRONTEND URL
    # ==========================================

    def get_frontend_url(self) -> str:
        """
        Return the frontend URL to redirect the user
        after successful authentication.
        """

        return settings.frontend_url

    # ==========================================
    # CREDENTIAL SERIALIZATION
    # ==========================================

    def credentials_to_dict(
        self,
        credentials: Credentials,
    ) -> Dict[str, Any]:
        """
        Convert Google credentials into a serializable
        dictionary.
        """

        return {
            "token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_uri": credentials.token_uri,
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "scopes": list(
                credentials.scopes or []
            ),
        }

    # ==========================================
    # CREDENTIAL DESERIALIZATION
    # ==========================================

    def credentials_from_dict(
        self,
        data: Dict[str, Any],
    ) -> Credentials:
        """
        Recreate Google Credentials from a dictionary.
        """

        return Credentials(
            token=data.get("token"),
            refresh_token=data.get("refresh_token"),
            token_uri=data.get(
                "token_uri",
                GOOGLE_TOKEN_URI,
            ),
            client_id=data.get(
                "client_id",
                settings.google_client_id,
            ),
            client_secret=data.get(
                "client_secret",
                settings.google_client_secret,
            ),
            scopes=data.get("scopes"),
        )

    # ==========================================
    # TOKEN REFRESH
    # ==========================================

    def refresh_credentials(
        self,
        credentials: Credentials,
    ) -> Credentials:
        """
        Refresh an expired Google access token.
        """

        if (
            credentials.expired
            and credentials.refresh_token
        ):
            credentials.refresh(Request())

        return credentials

    # ==========================================
    # CREDENTIAL VALIDATION
    # ==========================================

    def credentials_are_valid(
        self,
        credentials: Optional[Credentials],
    ) -> bool:
        """
        Check whether Google credentials are valid.
        """

        if credentials is None:
            return False

        if credentials.valid:
            return True

        if (
            credentials.expired
            and credentials.refresh_token
        ):
            try:
                credentials.refresh(Request())
                return credentials.valid

            except Exception:
                return False

        return False

    # ==========================================
    # GOOGLE SCOPES
    # ==========================================

    def _get_all_scopes(self) -> list[str]:
        """
        Return unique Gmail and Calendar scopes.
        """

        return list(
            dict.fromkeys(
                GMAIL_SCOPES + CALENDAR_SCOPES
            )
        )

    # ==========================================
    # LOCAL CREDENTIAL STORAGE
    # ==========================================

    def save_credentials_to_file(
        self,
        credentials: Credentials,
        file_path: str,
    ) -> None:
        """
        Save credentials to a local file.

        Intended for local development/testing.
        """

        path = Path(file_path)

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with path.open(
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                self.credentials_to_dict(
                    credentials
                ),
                file,
                indent=2,
            )

    # ==========================================
    # LOAD LOCAL CREDENTIALS
    # ==========================================

    def load_credentials_from_file(
        self,
        file_path: str,
    ) -> Optional[Credentials]:
        """
        Load credentials from a local file and
        refresh them when necessary.
        """

        path = Path(file_path)

        if not path.exists():
            return None

        try:
            with path.open(
                "r",
                encoding="utf-8",
            ) as file:

                data = json.load(file)

            credentials = (
                self.credentials_from_dict(data)
            )

            return self.refresh_credentials(
                credentials
            )

        except Exception:
            return None


# ==========================================
# GLOBAL OAUTH SERVICE
# ==========================================

oauth_service = OAuthService()