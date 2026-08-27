from typing import List, Optional

from pydantic import BaseModel, Field


class Email(BaseModel):
    message_id: str
    thread_id: Optional[str] = None
    sender: str = ""
    reply_to: Optional[str] = None
    recipient: Optional[str] = None
    subject: str = ""
    date: Optional[str] = None
    body: str = ""
    snippet: str = ""
    label_ids: List[str] = Field(
        default_factory=list
    )


class EmailSearchRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=1,
        description="Gmail search query.",
    )

    max_results: int = Field(
        default=20,
        ge=1,
        le=100,
    )


class EmailDraftRequest(BaseModel):
    recipient: str = Field(
        ...,
        min_length=1,
    )

    subject: str = Field(
        default="",
    )

    body: str = Field(
        ...,
        min_length=1,
    )


class EmailSendRequest(BaseModel):
    recipient: str = Field(
        ...,
        min_length=1,
    )

    subject: str = Field(
        default="",
    )

    body: str = Field(
        ...,
        min_length=1,
    )


class EmailReplyRequest(BaseModel):
    message_id: str = Field(
        ...,
        min_length=1,
    )

    body: str = Field(
        ...,
        min_length=1,
    )