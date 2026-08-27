import base64
from email.mime.text import MIMEText
from email.utils import parseaddr
from typing import Any, Dict, List, Optional

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials

from app.services.oauth_service import oauth_service


class GmailService:
    """
    Handles all Gmail API operations for Larvi.
    """

    def __init__(self) -> None:
        self._credentials: Optional[Credentials] = None
        self._service = None

    # ==========================================
    # AUTHENTICATION
    # ==========================================

    def set_credentials(
        self,
        credentials: Credentials,
    ) -> None:
        """
        Set Google credentials and initialize
        the Gmail API client.
        """

        credentials = oauth_service.refresh_credentials(
            credentials
        )

        if not oauth_service.credentials_are_valid(
            credentials
        ):
            raise ValueError(
                "Invalid or expired Google credentials."
            )

        self._credentials = credentials

        self._service = build(
            "gmail",
            "v1",
            credentials=credentials,
            cache_discovery=False,
        )

    def is_authenticated(self) -> bool:
        """
        Check whether Gmail is connected.
        """

        return (
            self._service is not None
            and self._credentials is not None
            and oauth_service.credentials_are_valid(
                self._credentials
            )
        )

    def _get_service(self):
        """
        Return the Gmail API client.
        """

        if not self.is_authenticated():
            raise RuntimeError(
                "Gmail is not connected. "
                "Please connect your Google account first."
            )

        return self._service

    # ==========================================
    # SEARCH EMAILS
    # ==========================================

    def search_emails(
        self,
        query: str,
        max_results: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Search Gmail using Gmail search syntax.
        """

        if not query or not query.strip():
            raise ValueError("Gmail search query cannot be empty.")

        service = self._get_service()

        try:
            response = (
                service.users()
                .messages()
                .list(
                    userId="me",
                    q=query,
                    maxResults=max_results,
                )
                .execute()
            )

            messages = response.get("messages", [])
            results = []

            for message in messages:
                parsed_email = self.get_email(
                    message_id=message["id"]
                )

                if parsed_email:
                    results.append(parsed_email)

            return results

        except HttpError as exc:
            raise RuntimeError(
                f"Gmail search failed: {exc}"
            ) from exc

    # ==========================================
    # GET RECENT EMAILS
    # ==========================================

    def get_recent_emails(
        self,
        max_results: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve the user's most recent emails.
        """

        service = self._get_service()

        try:
            response = (
                service.users()
                .messages()
                .list(
                    userId="me",
                    maxResults=max_results,
                )
                .execute()
            )

            messages = response.get("messages", [])
            results = []

            for message in messages:
                parsed_email = self.get_email(
                    message_id=message["id"]
                )

                if parsed_email:
                    results.append(parsed_email)

            return results

        except HttpError as exc:
            raise RuntimeError(
                f"Unable to retrieve recent emails: {exc}"
            ) from exc

    # ==========================================
    # READ EMAIL
    # ==========================================

    def get_email(
        self,
        message_id: str,
    ) -> Dict[str, Any]:
        """
        Retrieve and parse a complete email.
        """

        if not message_id:
            raise ValueError(
                "Email message ID is required."
            )

        service = self._get_service()

        try:
            message = (
                service.users()
                .messages()
                .get(
                    userId="me",
                    id=message_id,
                    format="full",
                )
                .execute()
            )

            return self._parse_message(message)

        except HttpError as exc:
            raise RuntimeError(
                f"Unable to read email: {exc}"
            ) from exc

    # ==========================================
    # CREATE DRAFT
    # ==========================================

    def create_draft(
        self,
        recipient: str,
        subject: str,
        body: str,
    ) -> Dict[str, Any]:
        """
        Create an email draft in Gmail.
        """

        self._validate_email_data(
            recipient,
            body,
        )

        service = self._get_service()

        message = self._create_message(
            recipient=recipient,
            subject=subject,
            body=body,
        )

        try:
            draft = (
                service.users()
                .drafts()
                .create(
                    userId="me",
                    body={
                        "message": message
                    },
                )
                .execute()
            )

            return {
                "status": "success",
                "draft_id": draft.get("id"),
                "message_id": (
                    draft.get("message", {}).get("id")
                ),
            }

        except HttpError as exc:
            raise RuntimeError(
                f"Unable to create email draft: {exc}"
            ) from exc

    # ==========================================
    # SEND EMAIL
    # ==========================================

    def send_email(
        self,
        recipient: str,
        subject: str,
        body: str,
    ) -> Dict[str, Any]:
        """
        Send an email through Gmail.
        """

        self._validate_email_data(
            recipient,
            body,
        )

        service = self._get_service()

        message = self._create_message(
            recipient=recipient,
            subject=subject,
            body=body,
        )

        try:
            response = (
                service.users()
                .messages()
                .send(
                    userId="me",
                    body=message,
                )
                .execute()
            )

            sent_message_id = response.get("id")
            thread_id = response.get("threadId")

            # Verify that Gmail actually created the sent message.
            verification = self._verify_sent_message(
                sent_message_id
            )

            if not verification["verified"]:
                raise RuntimeError(
                    "Gmail accepted the send request, "
                    "but the sent message could not be verified."
                )

            return {
                "status": "success",
                "message_id": sent_message_id,
                "thread_id": thread_id,
                "verified": True,
                "label_ids": verification["label_ids"],
            }

        except HttpError as exc:
            raise RuntimeError(
                f"Unable to send email: {exc}"
            ) from exc

    # ==========================================
    # REPLY TO EMAIL
    # ==========================================

    def reply_to_email(
        self,
        message_id: str,
        body: str,
    ) -> Dict[str, Any]:
        """
        Reply to an existing Gmail message.

        Uses the original Gmail thread ID and the
        original RFC Message-ID header so Gmail can
        correctly treat the new message as a reply.
        """

        if not message_id:
            raise ValueError(
                "Email message ID is required."
            )

        if not body or not body.strip():
            raise ValueError(
                "Reply body cannot be empty."
            )

        service = self._get_service()

        # Fetch the ORIGINAL message directly from Gmail.
        original_message = (
            service.users()
            .messages()
            .get(
                userId="me",
                id=message_id,
                format="full",
            )
            .execute()
        )

        original_email = self._parse_message(
            original_message
        )

        # ------------------------------------------
        # DETERMINE RECIPIENT
        # ------------------------------------------

        reply_to = original_email.get("reply_to", "")
        sender = original_email.get("sender", "")

        recipient_raw = reply_to or sender

        if not recipient_raw:
            raise ValueError(
                "Unable to determine the email recipient."
            )

        # Convert:
        # "Ayesha Imran <ayesha@example.com>"
        # into:
        # "ayesha@example.com"
        _, recipient = parseaddr(recipient_raw)

        if not recipient or "@" not in recipient:
            raise ValueError(
                f"Invalid reply recipient: {recipient_raw}"
            )

        # ------------------------------------------
        # SUBJECT
        # ------------------------------------------

        subject = original_email.get(
            "subject",
            "",
        ).strip()

        if not subject:
            subject = "Reply"

        if not subject.lower().startswith("re:"):
            subject = f"Re: {subject}"

        # ------------------------------------------
        # THREAD + RFC MESSAGE ID
        # ------------------------------------------

        thread_id = original_message.get(
            "threadId"
        )

        if not thread_id:
            raise ValueError(
                "Original Gmail message does not contain a thread ID."
            )

        # IMPORTANT:
        # Gmail's internal message ID is NOT the same
        # as the RFC Message-ID used by In-Reply-To.
        rfc_message_id = original_email.get(
            "message_id_header"
        )

        message = self._create_message(
            recipient=recipient,
            subject=subject,
            body=body.strip(),
            thread_id=thread_id,
            in_reply_to=rfc_message_id,
            references=rfc_message_id,
        )

        try:
            response = (
                service.users()
                .messages()
                .send(
                    userId="me",
                    body=message,
                )
                .execute()
            )

            sent_message_id = response.get("id")
            sent_thread_id = response.get("threadId")

            if not sent_message_id:
                raise RuntimeError(
                    "Gmail returned no message ID after sending the reply."
                )

            # ------------------------------------------
            # VERIFY ACTUAL SENT MESSAGE
            # ------------------------------------------

            verification = self._verify_sent_message(
                sent_message_id
            )

            if not verification["verified"]:
                raise RuntimeError(
                    "Gmail accepted the reply request, "
                    "but the sent reply could not be verified."
                )

            # Verify the message belongs to the same thread.
            if (
                sent_thread_id
                and sent_thread_id != thread_id
            ):
                raise RuntimeError(
                    "Reply was sent, but Gmail returned "
                    "a different thread ID."
                )

            return {
                "status": "success",
                "message_id": sent_message_id,
                "thread_id": sent_thread_id or thread_id,
                "recipient": recipient,
                "subject": subject,
                "verified": True,
                "label_ids": verification["label_ids"],
                "original_message_id": message_id,
            }

        except HttpError as exc:
            raise RuntimeError(
                f"Unable to reply to email: {exc}"
            ) from exc

    # ==========================================
    # VERIFY SENT MESSAGE
    # ==========================================

    def _verify_sent_message(
        self,
        message_id: Optional[str],
    ) -> Dict[str, Any]:
        """
        Verify that Gmail created the sent message
        and that it has the SENT label.
        """

        if not message_id:
            return {
                "verified": False,
                "label_ids": [],
            }

        service = self._get_service()

        try:
            message = (
                service.users()
                .messages()
                .get(
                    userId="me",
                    id=message_id,
                    format="metadata",
                    metadataHeaders=[
                        "To",
                        "Subject",
                        "Message-ID",
                    ],
                )
                .execute()
            )

            label_ids = message.get(
                "labelIds",
                [],
            )

            verified = (
                message.get("id") == message_id
                and "SENT" in label_ids
            )

            return {
                "verified": verified,
                "label_ids": label_ids,
            }

        except HttpError:
            return {
                "verified": False,
                "label_ids": [],
            }

    # ==========================================
    # CREATE MIME MESSAGE
    # ==========================================

    def _create_message(
        self,
        recipient: str,
        subject: str,
        body: str,
        thread_id: Optional[str] = None,
        in_reply_to: Optional[str] = None,
        references: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a Gmail API-compatible MIME message.
        """

        mime_message = MIMEText(
            body,
            "plain",
            "utf-8",
        )

        mime_message["To"] = recipient
        mime_message["Subject"] = subject

        if in_reply_to:
            mime_message["In-Reply-To"] = in_reply_to

        if references:
            mime_message["References"] = references

        encoded_message = (
            base64.urlsafe_b64encode(
                mime_message.as_bytes()
            )
            .decode("utf-8")
        )

        message = {
            "raw": encoded_message
        }

        if thread_id:
            message["threadId"] = thread_id

        return message

    # ==========================================
    # PARSE GMAIL MESSAGE
    # ==========================================

    def _parse_message(
        self,
        message: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Convert Gmail's raw API response into a
        clean dictionary for Larvi.
        """

        payload = message.get(
            "payload",
            {}
        )

        headers = payload.get(
            "headers",
            []
        )

        header_map = {
            header.get(
                "name",
                ""
            ).lower(): header.get(
                "value",
                ""
            )
            for header in headers
        }

        body = self._extract_body(
            payload
        )

        sender = header_map.get(
            "from",
            ""
        )

        return {
            # Gmail internal message ID.
            "message_id": message.get(
                "id"
            ),

            # Gmail internal thread ID.
            "thread_id": message.get(
                "threadId"
            ),

            "sender": sender,

            "reply_to": header_map.get(
                "reply-to",
                sender,
            ),

            "recipient": header_map.get(
                "to",
                ""
            ),

            "subject": header_map.get(
                "subject",
                ""
            ),

            "date": header_map.get(
                "date",
                ""
            ),

            "body": body,

            "snippet": message.get(
                "snippet",
                ""
            ),

            "label_ids": message.get(
                "labelIds",
                []
            ),

            # IMPORTANT:
            # This is the RFC Message-ID, NOT Gmail's
            # internal message ID.
            "message_id_header": header_map.get(
                "message-id",
                ""
            ),
        }

    # ==========================================
    # EXTRACT EMAIL BODY
    # ==========================================

    def _extract_body(
        self,
        payload: Dict[str, Any],
    ) -> str:
        """
        Extract plain-text content from Gmail's
        potentially nested MIME structure.
        """

        body_data = (
            payload.get(
                "body",
                {}
            ).get(
                "data"
            )
        )

        if body_data:
            return self._decode_body(
                body_data
            )

        parts = payload.get(
            "parts",
            []
        )

        collected_text = []

        for part in parts:
            mime_type = part.get(
                "mimeType",
                ""
            )

            if mime_type == "text/plain":
                data = (
                    part.get(
                        "body",
                        {}
                    ).get(
                        "data"
                    )
                )

                if data:
                    collected_text.append(
                        self._decode_body(
                            data
                        )
                    )

            elif part.get("parts"):
                nested_body = (
                    self._extract_body(
                        part
                    )
                )

                if nested_body:
                    collected_text.append(
                        nested_body
                    )

        return "\n".join(
            collected_text
        ).strip()

    # ==========================================
    # DECODE EMAIL BODY
    # ==========================================

    @staticmethod
    def _decode_body(
        data: str,
    ) -> str:
        """
        Decode Gmail's URL-safe Base64 body.
        """

        try:
            decoded = (
                base64.urlsafe_b64decode(
                    data
                )
            )

            return decoded.decode(
                "utf-8",
                errors="replace",
            )

        except Exception:
            return ""

    # ==========================================
    # VALIDATE EMAIL DATA
    # ==========================================

    @staticmethod
    def _validate_email_data(
        recipient: str,
        body: str,
    ) -> None:
        """
        Validate basic email input before sending
        or creating a draft.
        """

        if not recipient or not recipient.strip():
            raise ValueError(
                "Email recipient is required."
            )

        _, email_address = parseaddr(
            recipient
        )

        if not email_address or "@" not in email_address:
            raise ValueError(
                "Invalid email recipient."
            )

        if not body or not body.strip():
            raise ValueError(
                "Email body cannot be empty."
            )


gmail_service = GmailService()
