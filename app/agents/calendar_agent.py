from typing import Any, Dict, List

from langchain_core.tools import BaseTool

from app.tools.calendar_tools import CALENDAR_TOOLS


class CalendarAgent:
    """
    Specialized agent responsible for Google Calendar operations.
    """

    name = "calendar_agent"

    description = (
        "Handles Google Calendar operations including "
        "viewing events, searching events, checking "
        "availability, creating, updating, and deleting events."
    )

    def __init__(
        self,
        tools: List[BaseTool] | None = None,
    ) -> None:
        self.tools = tools or CALENDAR_TOOLS

        self._tools_by_name: Dict[
            str,
            BaseTool,
        ] = {
            tool.name: tool
            for tool in self.tools
        }

    # ==========================================
    # TOOLS
    # ==========================================

    def get_tools(self) -> List[BaseTool]:
        """
        Return all tools available to the Calendar Agent.
        """

        return self.tools

    def get_tool(
        self,
        tool_name: str,
    ) -> BaseTool:
        """
        Retrieve a specific calendar tool by name.
        """

        tool = self._tools_by_name.get(
            tool_name
        )

        if tool is None:
            raise ValueError(
                f"Calendar tool '{tool_name}' was not found."
            )

        return tool

    # ==========================================
    # TOOL EXECUTION
    # ==========================================

    def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
    ) -> Any:
        """
        Execute a selected calendar tool.
        """

        tool = self.get_tool(
            tool_name
        )

        try:
            return tool.invoke(
                arguments
            )

        except Exception as exc:
            raise RuntimeError(
                f"Calendar tool '{tool_name}' failed: {exc}"
            ) from exc

    # ==========================================
    # TOOL DESCRIPTIONS
    # ==========================================

    def describe_tools(
        self,
    ) -> List[Dict[str, str]]:
        """
        Return basic information about available tools.
        """

        return [
            {
                "name": tool.name,
                "description": (
                    tool.description or ""
                ),
            }
            for tool in self.tools
        ]


calendar_agent = CalendarAgent()