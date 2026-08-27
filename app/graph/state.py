from typing import Any, Dict, List, Optional

from typing_extensions import TypedDict


class LarviState(TypedDict, total=False):
    # ==========================================
    # USER REQUEST
    # ==========================================

    user_message: str
    conversation_id: str

    # ==========================================
    # CONVERSATION CONTEXT
    # ==========================================

    conversation_history: List[Dict[str, str]]

    # ==========================================
    # REQUEST ANALYSIS
    # ==========================================

    current_intent: str
    selected_agent: str
    routing_reason: str

    # ==========================================
    # AGENT / TOOL EXECUTION
    # ==========================================

    selected_tool: Optional[str]
    tool_arguments: Dict[str, Any]
    tool_result: Any

    # ==========================================
    # MULTI-AGENT WORKFLOW
    # ==========================================

    workflow_step: str
    workflow_data: Dict[str, Any]

    # ==========================================
    # CONFIRMATION
    # ==========================================

    confirmation_required: bool
    confirmation_approved: Optional[bool]
    confirmation_message: Optional[str]

    # ==========================================
    # RESPONSE
    # ==========================================

    final_response: str

    # ==========================================
    # STATUS / ERROR
    # ==========================================

    workflow_status: str
    error: Optional[str]