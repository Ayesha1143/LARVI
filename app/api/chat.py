import uuid
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from app.graph.state import LarviState
from app.graph.workflow import larvi_workflow
from app.schemas.chat_schema import (
    ChatRequest,
    ChatResponse,
)


router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


# ==========================================
# CONVERSATION STORAGE
# ==========================================

_conversations: Dict[
    str,
    List[Dict[str, str]],
] = {}


# ==========================================
# PENDING CONFIRMATION STORAGE
# ==========================================
#
# Stores the action that is waiting for
# user's Yes / No confirmation.
#
# Example:
#
# {
#     "conversation_id": {
#         "selected_agent": "email_agent",
#         "selected_tool": "send_email",
#         "tool_arguments": {
#             "recipient": "...",
#             "subject": "...",
#             "body": "..."
#         },
#         "workflow_data": {}
#     }
# }
#

_pending_confirmations: Dict[
    str,
    Dict[str, Any],
] = {}


# ==========================================
# CONFIRMATION HELPERS
# ==========================================

def is_confirmation_yes(
    message: str,
) -> bool:
    """
    Determine whether the user's message
    approves the pending action.
    """

    normalized = message.strip().lower()

    yes_words = {
        "yes",
        "y",
        "yeah",
        "yep",
        "sure",
        "okay",
        "ok",
        "confirm",
        "confirmed",
        "send it",
        "do it",
        "go ahead",
        "proceed",
    }

    return normalized in yes_words


def is_confirmation_no(
    message: str,
) -> bool:
    """
    Determine whether the user's message
    rejects the pending action.
    """

    normalized = message.strip().lower()

    no_words = {
        "no",
        "n",
        "nope",
        "cancel",
        "cancel it",
        "don't",
        "do not",
        "stop",
        "reject",
    }

    return normalized in no_words


# ==========================================
# CHAT
# ==========================================

@router.post(
    "",
    response_model=ChatResponse,
)
async def chat(
    request: ChatRequest,
) -> ChatResponse:
    """
    Process a natural-language request through
    the Larvi LangGraph workflow.

    Handles confirmation for external actions
    such as sending emails and modifying calendar
    events.
    """

    message = request.message.strip()

    if not message:

        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty.",
        )

    # ==========================================
    # CONVERSATION ID
    # ==========================================

    conversation_id = (
        request.conversation_id
        or str(uuid.uuid4())
    )

    history = _conversations.get(
        conversation_id,
        [],
    )

    # ==========================================
    # CHECK PENDING CONFIRMATION
    # ==========================================

    pending_action = (
        _pending_confirmations.get(
            conversation_id
        )
    )

    confirmation_value = (
        request.confirmation
    )

    # ------------------------------------------
    # If API explicitly provides confirmation,
    # use it.
    # ------------------------------------------

    if (
        pending_action
        and confirmation_value is None
    ):

        if is_confirmation_yes(
            message
        ):

            confirmation_value = True

        elif is_confirmation_no(
            message
        ):

            confirmation_value = False

    # ==========================================
    # RESTORE PENDING ACTION
    # ==========================================

    if (
        pending_action
        and confirmation_value is not None
    ):

        state: LarviState = {

            "user_message": message,

            "conversation_id": (
                conversation_id
            ),

            "conversation_history": history,

            # ----------------------------------
            # Restore original request
            # ----------------------------------

            "selected_agent": (
                pending_action.get(
                    "selected_agent",
                    "",
                )
            ),

            "selected_tool": (
                pending_action.get(
                    "selected_tool",
                    "",
                )
            ),

            "tool_arguments": (
                pending_action.get(
                    "tool_arguments",
                    {},
                )
            ),

            "workflow_data": (
                pending_action.get(
                    "workflow_data",
                    {},
                )
            ),

            "current_intent": (
                pending_action.get(
                    "current_intent",
                    "",
                )
            ),

            "routing_reason": (
                pending_action.get(
                    "routing_reason",
                    "",
                )
            ),

            # ----------------------------------
            # Confirmation
            # ----------------------------------

            "confirmation_required": False,

            "confirmation_approved": (
                confirmation_value
            ),

            "confirmation_message": None,

            # ----------------------------------
            # Workflow
            # ----------------------------------

            "workflow_status": "started",

            "workflow_step": (
                pending_action.get(
                    "workflow_step",
                    "confirmation_pending",
                )
            ),

            "tool_result": None,

            "error": None,

            "final_response": "",
        }

    else:

        # ==========================================
        # NORMAL NEW REQUEST
        # ==========================================

        state = {

            "user_message": message,

            "conversation_id": (
                conversation_id
            ),

            "conversation_history": history,

            "confirmation_required": False,

            "confirmation_approved": (
                confirmation_value
            ),

            "confirmation_message": None,

            "tool_arguments": {},

            "workflow_data": {},

            "workflow_status": "started",

            "workflow_step": "",

            "selected_agent": "",

            "selected_tool": "",

            "tool_result": None,

            "current_intent": "",

            "routing_reason": "",

            "error": None,

            "final_response": "",
        }

    # ==========================================
    # RUN LANGGRAPH
    # ==========================================

    try:

        result = await larvi_workflow.ainvoke(
            state
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                "Larvi could not process "
                "the request."
            ),
        ) from exc

    # ==========================================
    # FINAL RESPONSE
    # ==========================================

    final_response = result.get(
        "final_response",
        "I couldn't complete your request.",
    )

    workflow_status = result.get(
        "workflow_status",
        "failed",
    )

    requires_confirmation = result.get(
        "confirmation_required",
        False,
    )

    # ==========================================
    # SAVE / CLEAR PENDING CONFIRMATION
    # ==========================================

    if requires_confirmation:

        # --------------------------------------
        # Store the exact action waiting for
        # user confirmation.
        # --------------------------------------

        _pending_confirmations[
            conversation_id
        ] = {

            "selected_agent": (
                result.get(
                    "selected_agent",
                    state.get(
                        "selected_agent",
                        "",
                    ),
                )
            ),

            "selected_tool": (
                result.get(
                    "selected_tool",
                    state.get(
                        "selected_tool",
                        "",
                    ),
                )
            ),

            "tool_arguments": (
                result.get(
                    "tool_arguments",
                    state.get(
                        "tool_arguments",
                        {},
                    ),
                )
            ),

            "workflow_data": (
                result.get(
                    "workflow_data",
                    state.get(
                        "workflow_data",
                        {},
                    ),
                )
            ),

            "current_intent": (
                result.get(
                    "current_intent",
                    state.get(
                        "current_intent",
                        "",
                    ),
                )
            ),

            "routing_reason": (
                result.get(
                    "routing_reason",
                    state.get(
                        "routing_reason",
                        "",
                    ),
                )
            ),

            "workflow_step": (
                result.get(
                    "workflow_step",
                    "confirmation_pending",
                )
            ),
        }

    else:

        # --------------------------------------
        # Action completed or cancelled.
        # No pending confirmation remains.
        # --------------------------------------

        if conversation_id in (
            _pending_confirmations
        ):

            del _pending_confirmations[
                conversation_id
            ]

    # ==========================================
    # SAVE CONVERSATION
    # ==========================================

    history.append(
        {
            "role": "user",
            "content": message,
        }
    )

    history.append(
        {
            "role": "assistant",
            "content": final_response,
        }
    )

    _conversations[
        conversation_id
    ] = history[-20:]

    # ==========================================
    # RESPONSE DATA
    # ==========================================

    response_data = {

        "selected_agent": result.get(
            "selected_agent"
        ),

        "current_intent": result.get(
            "current_intent"
        ),

        "routing_reason": result.get(
            "routing_reason"
        ),

        "workflow_step": result.get(
            "workflow_step"
        ),

        "selected_tool": result.get(
            "selected_tool"
        ),

        "tool_arguments": result.get(
            "tool_arguments",
            {},
        ),

        "tool_result": result.get(
            "tool_result"
        ),

        "workflow_data": result.get(
            "workflow_data",
            {},
        ),
    }

    # ==========================================
    # ERROR
    # ==========================================

    if result.get("error"):

        response_data["error"] = result.get(
            "error"
        )

    # ==========================================
    # CONFIRMATION DATA
    # ==========================================

    if requires_confirmation:

        response_data[
            "confirmation_message"
        ] = result.get(
            "confirmation_message"
        )

    # ==========================================
    # RETURN
    # ==========================================

    return ChatResponse(
        response=final_response,

        conversation_id=conversation_id,

        status=workflow_status,

        requires_confirmation=(
            requires_confirmation
        ),

        data=response_data,
    )


# ==========================================
# GET HISTORY
# ==========================================

@router.get(
    "/history/{conversation_id}"
)
async def get_conversation_history(
    conversation_id: str,
):
    """
    Return conversation history.
    """

    history = _conversations.get(
        conversation_id
    )

    if history is None:

        raise HTTPException(
            status_code=404,
            detail="Conversation not found.",
        )

    return {
        "conversation_id": conversation_id,
        "messages": history,
    }


# ==========================================
# CLEAR HISTORY
# ==========================================

@router.delete(
    "/history/{conversation_id}"
)
async def clear_conversation_history(
    conversation_id: str,
):
    """
    Clear a conversation from memory.
    """

    if conversation_id not in _conversations:

        raise HTTPException(
            status_code=404,
            detail="Conversation not found.",
        )

    del _conversations[
        conversation_id
    ]

    # Also clear any pending confirmation.

    if conversation_id in (
        _pending_confirmations
    ):

        del _pending_confirmations[
            conversation_id
        ]

    return {
        "status": "success",
        "message": (
            "Conversation history cleared."
        ),
    }