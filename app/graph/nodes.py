from typing import Any, Dict

from app.agents.calendar_agent import calendar_agent
from app.agents.email_agent import email_agent
from app.agents.master_agent import master_agent

from app.config.constants import (
    CALENDAR_AGENT,
    EMAIL_AGENT,
    MULTI_AGENT,
    WORKFLOW_COMPLETED,
)

from app.graph.state import LarviState


# ==========================================
# TOOLS REQUIRING CONFIRMATION
# ==========================================

CONFIRMATION_REQUIRED_TOOLS = {
    "send_email",
    "reply_email",
    "create_event",
    "update_event",
    "delete_event",
}


# ==========================================
# CONFIRMATION WORDS
# ==========================================

CONFIRMATION_WORDS = {
    "yes",
    "y",
    "yeah",
    "yep",
    "sure",
    "okay",
    "ok",
    "confirm",
    "confirmed",
    "proceed",
    "do it",
    "send it",
    "go ahead",
}

REJECTION_WORDS = {
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


# ==========================================
# HELPER
# ==========================================

def _get_analysis_message(
    state: LarviState,
) -> str:
    """
    Get the correct message for request analysis.

    When the user is replying to a confirmation request,
    the current message may simply be "yes" or "no".

    In that case, recover the original request from
    conversation history so the selected tool and its
    arguments can be reconstructed.
    """

    user_message = state.get(
        "user_message",
        "",
    ).strip()

    confirmation_approved = state.get(
        "confirmation_approved"
    )

    # ------------------------------------------
    # NORMAL REQUEST
    # ------------------------------------------

    if confirmation_approved is None:
        return user_message

    # ------------------------------------------
    # CONFIRMATION RESPONSE
    # ------------------------------------------

    history = state.get(
        "conversation_history",
        [],
    )

    # Find the most recent previous user request.
    for item in reversed(history):

        if item.get("role") != "user":
            continue

        previous_message = item.get(
            "content",
            "",
        ).strip()

        if not previous_message:
            continue

        # Do not accidentally reuse another
        # confirmation response.
        previous_lower = previous_message.lower()

        if previous_lower in CONFIRMATION_WORDS:
            continue

        if previous_lower in REJECTION_WORDS:
            continue

        return previous_message

    # Fallback to current message.
    return user_message


# ==========================================
# REQUEST ANALYSIS
# ==========================================

def analyze_request_node(
    state: LarviState,
) -> LarviState:
    """
    Analyze the user's request and select
    the appropriate agent.

    If the user is responding to a confirmation,
    the original request is recovered from the
    conversation history.
    """

    try:

        analysis_message = _get_analysis_message(
            state
        )

        analysis = master_agent.analyze_request(
            user_message=analysis_message,
            conversation_history=state.get(
                "conversation_history",
                [],
            ),
        )

        state["current_intent"] = analysis.get(
            "current_intent",
            analysis_message,
        )

        state["selected_agent"] = analysis.get(
            "selected_agent",
            EMAIL_AGENT,
        )

        # ------------------------------------------
        # IMPORTANT
        # ------------------------------------------
        # Recover selected tool and arguments
        # so confirmation can execute the action.
        # ------------------------------------------

        state["selected_tool"] = analysis.get(
            "selected_tool"
        )

        state["tool_arguments"] = analysis.get(
            "tool_arguments",
            {},
        )

        state["routing_reason"] = analysis.get(
            "reason",
            "",
        )

        state["workflow_step"] = (
            "request_analyzed"
        )

        state["workflow_status"] = (
            "in_progress"
        )

        return state

    except Exception as exc:

        state["workflow_status"] = "failed"

        state["error"] = str(exc)

        return state


# ==========================================
# AGENT SELECTION
# ==========================================

def select_agent_node(
    state: LarviState,
) -> LarviState:
    """
    Validate the selected agent and prepare
    the workflow.
    """

    selected_agent = state.get(
        "selected_agent",
        EMAIL_AGENT,
    )

    valid_agents = {
        EMAIL_AGENT,
        CALENDAR_AGENT,
        MULTI_AGENT,
    }

    if selected_agent not in valid_agents:

        state["selected_agent"] = (
            EMAIL_AGENT
        )

    state["workflow_step"] = (
        "agent_selected"
    )

    return state


# ==========================================
# CONFIRMATION MESSAGE
# ==========================================

def build_confirmation_message(
    tool_name: str,
    tool_arguments: Dict[str, Any],
) -> str:
    """
    Build a user-friendly confirmation message
    for actions that modify external services.
    """

    # ------------------------------------------
    # SEND EMAIL
    # ------------------------------------------

    if tool_name == "send_email":

        recipient = tool_arguments.get(
            "recipient",
            "the recipient",
        )

        subject = tool_arguments.get(
            "subject",
            "",
        )

        if subject:

            return (
                f"You're about to send an email to "
                f"{recipient} with the subject "
                f"'{subject}'. "
                f"Do you want me to send it?"
            )

        return (
            f"You're about to send an email to "
            f"{recipient}. "
            f"Do you want me to send it?"
        )

    # ------------------------------------------
    # REPLY EMAIL
    # ------------------------------------------

    if tool_name == "reply_email":

        return (
            "You're about to send a reply to an "
            "existing email. "
            "Do you want me to send it?"
        )

    # ------------------------------------------
    # CREATE EVENT
    # ------------------------------------------

    if tool_name == "create_event":

        summary = tool_arguments.get(
            "summary",
            "this event",
        )

        start = tool_arguments.get(
            "start",
            "",
        )

        end = tool_arguments.get(
            "end",
            "",
        )

        message = (
            f"You're about to create the calendar "
            f"event '{summary}'"
        )

        if start:

            message += (
                f" starting at {start}"
            )

        if end:

            message += (
                f" and ending at {end}"
            )

        message += (
            ". Do you want me to create it?"
        )

        return message

    # ------------------------------------------
    # UPDATE EVENT
    # ------------------------------------------

    if tool_name == "update_event":

        return (
            "You're about to update an existing "
            "calendar event. "
            "Do you want me to make this change?"
        )

    # ------------------------------------------
    # DELETE EVENT
    # ------------------------------------------

    if tool_name == "delete_event":

        return (
            "You're about to delete a calendar "
            "event. This action cannot be undone. "
            "Do you want me to delete it?"
        )

    # ------------------------------------------
    # FALLBACK
    # ------------------------------------------

    return (
        "This action requires your confirmation. "
        "Do you want me to continue?"
    )


# ==========================================
# CONFIRMATION CHECK
# ==========================================

def check_confirmation(
    state: LarviState,
) -> LarviState:
    """
    Check whether the selected tool requires
    user confirmation.

    The actual tool is NOT executed while
    confirmation is pending.
    """

    tool_name = state.get(
        "selected_tool"
    )

    # ------------------------------------------
    # NO TOOL SELECTED
    # ------------------------------------------

    if not tool_name:

        state["confirmation_required"] = False

        state["confirmation_message"] = None

        return state

    # ------------------------------------------
    # TOOL DOES NOT REQUIRE CONFIRMATION
    # ------------------------------------------

    if tool_name not in CONFIRMATION_REQUIRED_TOOLS:

        state["confirmation_required"] = False

        state["confirmation_message"] = None

        return state

    # ------------------------------------------
    # CHECK USER DECISION
    # ------------------------------------------

    confirmation_approved = state.get(
        "confirmation_approved"
    )

    # ------------------------------------------
    # USER APPROVED
    # ------------------------------------------

    if confirmation_approved is True:

        state["confirmation_required"] = False

        state["confirmation_message"] = None

        state["workflow_step"] = (
            "confirmation_approved"
        )

        return state

    # ------------------------------------------
    # USER REJECTED
    # ------------------------------------------

    if confirmation_approved is False:

        state["confirmation_required"] = False

        state["confirmation_message"] = None

        state["workflow_status"] = (
            WORKFLOW_COMPLETED
        )

        state["workflow_step"] = (
            "confirmation_rejected"
        )

        state["tool_result"] = {
            "status": "cancelled",
            "message": (
                "The action was cancelled by the user."
            ),
        }

        return state

    # ------------------------------------------
    # CONFIRMATION REQUIRED
    # ------------------------------------------

    state["confirmation_required"] = True

    state["confirmation_message"] = (
        build_confirmation_message(
            tool_name=tool_name,
            tool_arguments=state.get(
                "tool_arguments",
                {},
            ),
        )
    )

    state["workflow_status"] = (
        "waiting_for_confirmation"
    )

    state["workflow_step"] = (
        "confirmation_pending"
    )

    return state


# ==========================================
# EMAIL AGENT
# ==========================================

def email_agent_node(
    state: LarviState,
) -> LarviState:
    """
    Execute an Email Agent workflow.

    Confirmation is checked before any
    external email action is executed.
    """

    try:

        tool_name = state.get(
            "selected_tool"
        )

        # ------------------------------------------
        # NO TOOL YET
        # ------------------------------------------

        if not tool_name:

            state["workflow_step"] = (
                "email_agent_ready"
            )

            return state

        tool_arguments = state.get(
            "tool_arguments",
            {},
        )

        # ------------------------------------------
        # CONFIRMATION CHECK
        # ------------------------------------------

        state = check_confirmation(
            state
        )

        # ------------------------------------------
        # WAITING FOR USER
        # ------------------------------------------

        if state.get(
            "confirmation_required"
        ):

            return state

        # ------------------------------------------
        # USER REJECTED
        # ------------------------------------------

        if (
            state.get("workflow_step")
            == "confirmation_rejected"
        ):

            return state

        # ------------------------------------------
        # EXECUTE EMAIL TOOL
        # ------------------------------------------

        result = email_agent.execute_tool(
            tool_name=tool_name,
            arguments=tool_arguments,
        )

        state["tool_result"] = result

        state["workflow_step"] = (
            "email_tool_executed"
        )

        return state

    except Exception as exc:

        state["workflow_status"] = "failed"

        state["error"] = str(exc)

        return state


# ==========================================
# CALENDAR AGENT
# ==========================================

def calendar_agent_node(
    state: LarviState,
) -> LarviState:
    """
    Execute a Calendar Agent workflow.

    Confirmation is checked before any
    external calendar action is executed.
    """

    try:

        tool_name = state.get(
            "selected_tool"
        )

        # ------------------------------------------
        # NO TOOL YET
        # ------------------------------------------

        if not tool_name:

            state["workflow_step"] = (
                "calendar_agent_ready"
            )

            return state

        tool_arguments = state.get(
            "tool_arguments",
            {},
        )

        # ------------------------------------------
        # CONFIRMATION CHECK
        # ------------------------------------------

        state = check_confirmation(
            state
        )

        # ------------------------------------------
        # WAITING FOR USER
        # ------------------------------------------

        if state.get(
            "confirmation_required"
        ):

            return state

        # ------------------------------------------
        # USER REJECTED
        # ------------------------------------------

        if (
            state.get("workflow_step")
            == "confirmation_rejected"
        ):

            return state

        # ------------------------------------------
        # EXECUTE CALENDAR TOOL
        # ------------------------------------------

        result = calendar_agent.execute_tool(
            tool_name=tool_name,
            arguments=tool_arguments,
        )

        state["tool_result"] = result

        state["workflow_step"] = (
            "calendar_tool_executed"
        )

        return state

    except Exception as exc:

        state["workflow_status"] = "failed"

        state["error"] = str(exc)

        return state


# ==========================================
# MULTI AGENT
# ==========================================

def multi_agent_node(
    state: LarviState,
) -> LarviState:
    """
    Coordinate Email and Calendar workflows.

    Information returned by one agent can be
    passed to the next agent through workflow_data.
    """

    try:

        workflow_data = state.get(
            "workflow_data",
            {},
        )

        workflow_step = state.get(
            "workflow_step",
            "",
        )

        # ==========================================
        # EMAIL PHASE
        # ==========================================

        if workflow_step in {
            "",
            "request_analyzed",
            "agent_selected",
            "email_phase",
        }:

            tool_name = state.get(
                "selected_tool"
            )

            if tool_name:

                # ----------------------------------
                # CONFIRMATION CHECK
                # ----------------------------------

                state = check_confirmation(
                    state
                )

                # Waiting for confirmation.
                if state.get(
                    "confirmation_required"
                ):

                    return state

                # User rejected.
                if (
                    state.get("workflow_step")
                    == "confirmation_rejected"
                ):

                    return state

                # ----------------------------------
                # EXECUTE EMAIL TOOL
                # ----------------------------------

                result = (
                    email_agent.execute_tool(
                        tool_name=tool_name,
                        arguments=state.get(
                            "tool_arguments",
                            {},
                        ),
                    )
                )

                state["tool_result"] = result

                workflow_data[
                    "email_result"
                ] = result

                state["workflow_data"] = (
                    workflow_data
                )

                state["workflow_step"] = (
                    "email_phase_completed"
                )

                return state

            state["workflow_step"] = (
                "email_phase"
            )

            return state

        # ==========================================
        # CALENDAR PHASE
        # ==========================================

        if workflow_step in {
            "email_phase_completed",
            "calendar_phase",
        }:

            calendar_tool = workflow_data.get(
                "calendar_tool"
            )

            calendar_arguments = (
                workflow_data.get(
                    "calendar_arguments",
                    {},
                )
            )

            if calendar_tool:

                # ----------------------------------
                # TEMPORARILY SET TOOL INFORMATION
                # FOR CONFIRMATION CHECK
                # ----------------------------------

                state["selected_tool"] = (
                    calendar_tool
                )

                state["tool_arguments"] = (
                    calendar_arguments
                )

                # ----------------------------------
                # CONFIRMATION CHECK
                # ----------------------------------

                state = check_confirmation(
                    state
                )

                # Waiting for confirmation.
                if state.get(
                    "confirmation_required"
                ):

                    return state

                # User rejected.
                if (
                    state.get("workflow_step")
                    == "confirmation_rejected"
                ):

                    return state

                # ----------------------------------
                # EXECUTE CALENDAR TOOL
                # ----------------------------------

                result = (
                    calendar_agent.execute_tool(
                        tool_name=calendar_tool,
                        arguments=calendar_arguments,
                    )
                )

                state["tool_result"] = result

                workflow_data[
                    "calendar_result"
                ] = result

                state["workflow_data"] = (
                    workflow_data
                )

                state["workflow_step"] = (
                    "calendar_phase_completed"
                )

                return state

            state["workflow_step"] = (
                "calendar_phase"
            )

            return state

        return state

    except Exception as exc:

        state["workflow_status"] = "failed"

        state["error"] = str(exc)

        return state


# ==========================================
# FINAL RESPONSE
# ==========================================

def generate_response_node(
    state: LarviState,
) -> LarviState:
    """
    Generate Larvi's final response from
    verified agent/tool results.
    """

    try:

        # ==========================================
        # CONFIRMATION RESPONSE
        # ==========================================

        if state.get(
            "confirmation_required"
        ):

            state["final_response"] = (
                state.get(
                    "confirmation_message"
                )
                or "Do you want me to continue?"
            )

            state["workflow_status"] = (
                "waiting_for_confirmation"
            )

            return state

        # ==========================================
        # NORMAL RESPONSE
        # ==========================================

        result = state.get(
            "tool_result"
        )

        if state.get("error"):

            result = {
                "status": "error",
                "error": state["error"],
            }

        response = (
            master_agent.generate_final_response(
                user_message=state.get(
                    "user_message",
                    "",
                ),
                result=result,
                conversation_history=state.get(
                    "conversation_history",
                    [],
                ),
            )
        )

        state["final_response"] = response

        state["workflow_status"] = (
            WORKFLOW_COMPLETED
        )

        state["workflow_step"] = (
            "completed"
        )

        return state

    except Exception as exc:

        state["workflow_status"] = "failed"

        state["error"] = str(exc)

        state["final_response"] = (
            "I couldn't complete your request "
            "because an internal error occurred."
        )

        return state


# ==========================================
# ERROR HANDLER
# ==========================================

def handle_error_node(
    state: LarviState,
) -> LarviState:
    """
    Convert internal errors into a safe
    user-facing response.
    """

    error = state.get(
        "error"
    )

    if error:

        state["final_response"] = (
            "I couldn't complete your request. "
            f"Reason: {error}"
        )

    else:

        state["final_response"] = (
            "I couldn't complete your request."
        )

    state["workflow_status"] = "failed"

    state["workflow_step"] = "failed"

    return state