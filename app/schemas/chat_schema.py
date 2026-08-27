from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        description="Natural-language instruction for Larvi.",
    )

    conversation_id: Optional[str] = Field(
        default=None,
        description="Existing conversation ID for context.",
    )

    confirmation: Optional[bool] = Field(
        default=None,
        description="User confirmation for sensitive actions.",
    )


class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    status: str = "success"
    requires_confirmation: bool = False
    data: Dict[str, Any] = Field(
        default_factory=dict
    )