from unittest.mock import patch

import pytest

from app.graph.workflow import larvi_workflow


@pytest.mark.asyncio
async def test_email_workflow():
    state = {
        "user_message": "Show me my latest emails",
        "conversation_id": "test-email-001",
        "conversation_history": [],
        "confirmation_approved": None,
        "confirmation_required": False,
    }

    with patch(
        "app.graph.nodes.master_agent.analyze_request",
        return_value={
            "current_intent": "Show me my latest emails",
            "selected_agent": "email_agent",
        },
    ), patch(
        "app.graph.nodes.master_agent.generate_final_response",
        return_value="Here are your latest emails.",
    ):

        result = await larvi_workflow.ainvoke(state)

    assert result["selected_agent"] == "email_agent"
    assert result["workflow_status"] == "completed"
    assert result["final_response"] == (
        "Here are your latest emails."
    )


@pytest.mark.asyncio
async def test_calendar_workflow():
    state = {
        "user_message": "What meetings do I have tomorrow?",
        "conversation_id": "test-calendar-001",
        "conversation_history": [],
        "confirmation_approved": None,
        "confirmation_required": False,
    }

    with patch(
        "app.graph.nodes.master_agent.analyze_request",
        return_value={
            "current_intent": "What meetings do I have tomorrow?",
            "selected_agent": "calendar_agent",
        },
    ), patch(
        "app.graph.nodes.master_agent.generate_final_response",
        return_value="You have two meetings tomorrow.",
    ):

        result = await larvi_workflow.ainvoke(state)

    assert result["selected_agent"] == "calendar_agent"
    assert result["workflow_status"] == "completed"
    assert result["final_response"] == (
        "You have two meetings tomorrow."
    )


@pytest.mark.asyncio
async def test_multi_agent_workflow():
    state = {
        "user_message": (
            "Find Ahmed's meeting email and add it to my calendar."
        ),
        "conversation_id": "test-multi-001",
        "conversation_history": [],
        "confirmation_approved": None,
        "confirmation_required": False,
    }

    with patch(
        "app.graph.nodes.master_agent.analyze_request",
        return_value={
            "current_intent": (
                "Find Ahmed's meeting email and add it to my calendar."
            ),
            "selected_agent": "multi_agent",
        },
    ), patch(
        "app.graph.nodes.master_agent.generate_final_response",
        return_value=(
            "I found the meeting and added it to your calendar."
        ),
    ):

        result = await larvi_workflow.ainvoke(state)

    assert result["selected_agent"] == "multi_agent"
    assert result["workflow_status"] == "completed"
    assert result["final_response"] == (
        "I found the meeting and added it to your calendar."
    )


@pytest.mark.asyncio
async def test_workflow_handles_invalid_agent():
    state = {
        "user_message": "Do something unknown",
        "conversation_id": "test-invalid-001",
        "conversation_history": [],
        "confirmation_approved": None,
        "confirmation_required": False,
    }

    with patch(
        "app.graph.nodes.master_agent.analyze_request",
        return_value={
            "current_intent": "Do something unknown",
            "selected_agent": "invalid_agent",
        },
    ):

        result = await larvi_workflow.ainvoke(state)

    assert result["workflow_status"] == "completed"
    assert result["selected_agent"] == "email_agent"


@pytest.mark.asyncio
async def test_workflow_preserves_conversation_context():
    state = {
        "user_message": "Move it to 5 PM",
        "conversation_id": "test-context-001",
        "conversation_history": [
            {
                "role": "user",
                "content": "Find my Project Review meeting.",
            },
            {
                "role": "assistant",
                "content": "I found the Project Review meeting at 3 PM.",
            },
        ],
        "confirmation_approved": None,
        "confirmation_required": False,
    }

    with patch(
        "app.graph.nodes.master_agent.analyze_request",
        return_value={
            "current_intent": "Move it to 5 PM",
            "selected_agent": "calendar_agent",
        },
    ), patch(
        "app.graph.nodes.master_agent.generate_final_response",
        return_value="The meeting has been moved to 5 PM.",
    ):

        result = await larvi_workflow.ainvoke(state)

    assert result["selected_agent"] == "calendar_agent"
    assert len(result["conversation_history"]) == 2
    assert result["workflow_status"] == "completed"