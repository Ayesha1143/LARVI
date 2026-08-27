from typing import Any, Dict, List

from langchain_core.tools import BaseTool

from app.tools.email_tools import EMAIL_TOOLS


class EmailAgent:
    """
    Specialized agent responsible for Gmail operations.
    """

    name = "email_agent"

    description = (
        "Handles Gmail operations including searching, "
        "reading, retrieving, drafting, sending, and "
        "replying to emails."
    )

    def __init__(
        self,
        tools: List[BaseTool] | None = None,
    ) -> None:
        self.tools = tools or EMAIL_TOOLS

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
        Return all tools available to the Email Agent.
        """

        return self.tools

    def get_tool(
        self,
        tool_name: str,
    ) -> BaseTool:
        """
        Retrieve a specific email tool by name.
        """

        tool = self._tools_by_name.get(
            tool_name
        )

        if tool is None:
            raise ValueError(
                f"Email tool '{tool_name}' was not found."
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
        Execute a selected email tool.
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
                f"Email tool '{tool_name}' failed: {exc}"
            ) from exc

    # ==========================================
    # TOOL DESCRIPTIONS
    # ==========================================

    def describe_tools(self) -> List[Dict[str, str]]:
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


email_agent = EmailAgent()