"""Tool management for dynamic tool registration with MCP notifications.

This module provides a ToolManager class that enables dynamic tool registration
at runtime. When tools are added or removed through ToolManager, FastMCP's
add_tool/remove_tool methods are used, and developers can manually send
change notifications to clients using the MCP Context.

See: https://modelcontextprotocol.io/specification/2025-03-26/server/tools#list-changed-notification
"""

from typing import Callable, Optional, Any
from dataclasses import dataclass
from mcp.server.fastmcp import FastMCP


@dataclass
class RegisteredTool:
    """Information about a registered tool."""

    name: str
    """Unique name for the tool."""

    description: str
    """Human-readable description of the tool."""

    function: Callable
    """The actual function to call."""

    annotations: Optional[dict[str, str]] = None
    """Optional annotations describing tool behavior."""


class ToolManager:
    """Manages dynamic tool registration.

    This class provides a clean interface for adding and removing tools at runtime.
    When tools are registered, they're added to FastMCP, which can then send
    change notifications to clients.

    Important: To notify clients when tools change, use the MCP Context's
    send_notification method in your tool functions:

        from fastmcp.server.context import Context
        import mcp.types

        @mcp.tool
        async def my_tool(ctx: Context):
            # After adding a tool:
            await ctx.send_notification(mcp.types.ToolListChangedNotification())

    Usage:
        >>> from point_topic_mcp.core.tool_manager import ToolManager
        >>>
        >>> tool_manager = ToolManager(mcp)
        >>>
        >>> async def my_new_tool(param: str) -> str:
        ...     return f"Result: {param}"
        >>>
        >>> tool_manager.register_tool(
        ...     name="my_tool",
        ...     description="A new tool",
        ...     function=my_new_tool
        ... )

    Note:
        Tools must be registered before the MCP server starts for startup tools.
        For dynamic tool registration during runtime, use this manager after
        the server has started.
    """

    def __init__(self, mcp_server: FastMCP):
        """Initialize the tool manager.

        Args:
            mcp_server: The FastMCP server instance to manage tools for
        """
        self.mcp = mcp_server
        self._registered_tools: dict[str, RegisteredTool] = {}

    def register_tool(
        self,
        name: str,
        description: str,
        function: Callable,
        annotations: Optional[dict[str, str]] = None,
    ) -> None:
        """Register a new tool with the MCP server.

        After registering, you should send a change notification to clients:

            await ctx.send_notification(mcp.types.ToolListChangedNotification())

        Args:
            name: Unique identifier for the tool
            description: Human-readable description of what the tool does
            function: The function to call when the tool is invoked
            annotations: Optional annotations describing tool behavior

        Raises:
            ValueError: If a tool with the same name is already registered

        Example:
            >>> def get_user_data(user_id: int) -> dict:
            ...     return {"id": user_id, "name": "John"}
            >>>
            >>> tool_manager.register_tool(
            ...     name="get_user",
            ...     description="Fetch user data by ID",
            ...     function=get_user_data
            ... )
        """
        if name in self._registered_tools:
            raise ValueError(
                f"Tool '{name}' is already registered. "
                f"Use unregister_tool() to remove it first."
            )

        # Register the tool with FastMCP
        self.mcp.add_tool(function, name=name)

        # Track the tool in our registry
        tool_info = RegisteredTool(
            name=name,
            description=description,
            function=function,
            annotations=annotations,
        )
        self._registered_tools[name] = tool_info

    def unregister_tool(self, name: str) -> None:
        """Unregister a previously registered tool.

        After unregistering, you should send a change notification to clients:

            await ctx.send_notification(mcp.types.ToolListChangedNotification())

        Args:
            name: The name of the tool to unregister

        Raises:
            ValueError: If the tool is not registered

        Example:
            >>> tool_manager.unregister_tool("get_user")
        """
        if name not in self._registered_tools:
            raise ValueError(
                f"Tool '{name}' is not registered. Use register_tool() to add it first."
            )

        # Remove from FastMCP
        self.mcp.remove_tool(name)

        # Remove from our registry
        del self._registered_tools[name]

    def list_tools(self) -> dict[str, RegisteredTool]:
        """List all dynamically registered tools.

        Note: This returns only tools registered through this ToolManager.
        To get all tools including those registered at startup, use
        `mcp.list_tools()` instead.

        Returns:
            Dictionary mapping tool names to RegisteredTool objects

        Example:
            >>> tools = tool_manager.list_tools()
            >>> for name, tool_info in tools.items():
            ...     print(f"{name}: {tool_info.description}")
        """
        return self._registered_tools.copy()

    def get_tool(self, name: str) -> Optional[RegisteredTool]:
        """Get information about a specific tool.

        Args:
            name: The name of the tool

        Returns:
            RegisteredTool information or None if not found

        Example:
            >>> tool = tool_manager.get_tool("get_user")
            >>> if tool:
            ...     print(f"Tool: {tool.name} - {tool.description}")
        """
        return self._registered_tools.get(name)

    def is_registered(self, name: str) -> bool:
        """Check if a tool is registered.

        Args:
            name: The name of the tool

        Returns:
            True if the tool is registered, False otherwise

        Example:
            >>> if not tool_manager.is_registered("get_user"):
            ...     tool_manager.register_tool(...)
        """
        return name in self._registered_tools
