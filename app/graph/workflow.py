from langgraph.graph import END, START, StateGraph

from app.config.constants import (
    CALENDAR_AGENT,
    EMAIL_AGENT,
    MULTI_AGENT,
)
from app.graph.nodes import (
    analyze_request_node,
    calendar_agent_node,
    email_agent_node,
    generate_response_node,
    handle_error_node,
    multi_agent_node,
    select_agent_node,
)
from app.graph.state import LarviState


# ==========================================
# ROUTING AFTER AGENT SELECTION
# ==========================================

def route_after_analysis(
    state: LarviState,
) -> str:
    """
    Route the request to the selected agent.
    """

    if state.get("error"):
        return "error"

    selected_agent = state.get(
        "selected_agent",
        EMAIL_AGENT,
    )

    if selected_agent == EMAIL_AGENT:
        return EMAIL_AGENT

    if selected_agent == CALENDAR_AGENT:
        return CALENDAR_AGENT

    if selected_agent == MULTI_AGENT:
        return MULTI_AGENT

    return EMAIL_AGENT


# ==========================================
# ROUTING AFTER EMAIL/CALENDAR AGENT
# ==========================================

def route_after_agent(
    state: LarviState,
) -> str:
    """
    Route the workflow after a single-agent
    node has executed.
    """

    if state.get("error"):
        return "error"

    # ------------------------------------------
    # Confirmation is required.
    #
    # The node has NOT executed the external
    # action yet. Generate the confirmation
    # response for the user.
    # ------------------------------------------

    if state.get(
        "confirmation_required",
        False,
    ):
        return "response"

    return "response"


# ==========================================
# MULTI-AGENT ROUTING
# ==========================================

def route_after_multi_agent(
    state: LarviState,
) -> str:
    """
    Continue a multi-agent workflow until
    all required phases are completed.

    Confirmation requests stop the workflow
    and return a response to the user.
    """

    if state.get("error"):
        return "error"

    # ------------------------------------------
    # Confirmation required
    # ------------------------------------------

    if state.get(
        "confirmation_required",
        False,
    ):
        return "response"

    workflow_step = state.get(
        "workflow_step",
        "",
    )

    # ------------------------------------------
    # Email phase completed.
    # Continue to calendar phase.
    # ------------------------------------------

    if workflow_step == "email_phase_completed":
        return MULTI_AGENT

    # ------------------------------------------
    # Calendar phase completed.
    # ------------------------------------------

    if workflow_step == "calendar_phase_completed":
        return "response"

    # ------------------------------------------
    # Multi-agent workflow still needs
    # another execution.
    # ------------------------------------------

    if workflow_step in {
        "email_phase",
        "calendar_phase",
    }:
        return MULTI_AGENT

    return "response"


# ==========================================
# BUILD WORKFLOW
# ==========================================

def build_larvi_workflow():
    """
    Build and compile the Larvi LangGraph workflow.
    """

    graph = StateGraph(LarviState)

    # ==========================================
    # NODES
    # ==========================================

    graph.add_node(
        "analyze_request",
        analyze_request_node,
    )

    graph.add_node(
        "select_agent",
        select_agent_node,
    )

    graph.add_node(
        EMAIL_AGENT,
        email_agent_node,
    )

    graph.add_node(
        CALENDAR_AGENT,
        calendar_agent_node,
    )

    graph.add_node(
        MULTI_AGENT,
        multi_agent_node,
    )

    graph.add_node(
        "generate_response",
        generate_response_node,
    )

    graph.add_node(
        "error",
        handle_error_node,
    )

    # ==========================================
    # START
    # ==========================================

    graph.add_edge(
        START,
        "analyze_request",
    )

    graph.add_edge(
        "analyze_request",
        "select_agent",
    )

    # ==========================================
    # SELECT AGENT
    # ==========================================

    graph.add_conditional_edges(
        "select_agent",
        route_after_analysis,
        {
            EMAIL_AGENT: EMAIL_AGENT,
            CALENDAR_AGENT: CALENDAR_AGENT,
            MULTI_AGENT: MULTI_AGENT,
            "error": "error",
        },
    )

    # ==========================================
    # EMAIL AGENT
    # ==========================================

    graph.add_conditional_edges(
        EMAIL_AGENT,
        route_after_agent,
        {
            "response": "generate_response",
            "error": "error",
        },
    )

    # ==========================================
    # CALENDAR AGENT
    # ==========================================

    graph.add_conditional_edges(
        CALENDAR_AGENT,
        route_after_agent,
        {
            "response": "generate_response",
            "error": "error",
        },
    )

    # ==========================================
    # MULTI AGENT
    # ==========================================

    graph.add_conditional_edges(
        MULTI_AGENT,
        route_after_multi_agent,
        {
            MULTI_AGENT: MULTI_AGENT,
            "response": "generate_response",
            "error": "error",
        },
    )

    # ==========================================
    # FINAL RESPONSE
    # ==========================================

    graph.add_edge(
        "generate_response",
        END,
    )

    # ==========================================
    # ERROR
    # ==========================================

    graph.add_edge(
        "error",
        END,
    )

    return graph.compile()


# ==========================================
# COMPILED WORKFLOW
# ==========================================

larvi_workflow = build_larvi_workflow()