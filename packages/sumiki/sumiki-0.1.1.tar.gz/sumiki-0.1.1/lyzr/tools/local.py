"""
Local Tools module for Lyzr SDK

Enables local tool execution with agents using decorator pattern.
"""

from typing import Callable, Dict, Any, List, Optional
from pydantic import BaseModel, Field, ConfigDict
import inspect


class Tool(BaseModel):
    """
    Local tool definition

    Represents a function that can be executed locally during agent runs.
    """

    name: str = Field(..., description="Tool name (unique identifier)")
    description: str = Field(..., description="What the tool does (for LLM)")
    parameters: Dict[str, Any] = Field(..., description="JSON schema for parameters")
    function: Optional[Callable] = Field(None, description="Python function to execute")

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        # Don't include function in serialization
        exclude={"function"}
    )

    def to_api_format(self) -> Dict[str, Any]:
        """
        Convert to Lyzr API format for registration

        Returns:
            Dict with name, description, and parameters for API
        """
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }

    async def execute(self, **kwargs) -> Any:
        """
        Execute the tool function with given arguments

        Args:
            **kwargs: Tool arguments

        Returns:
            Tool execution result

        Raises:
            RuntimeError: If tool has no function attached
        """
        if not self.function:
            raise RuntimeError(f"Tool '{self.name}' has no function attached")

        # Handle both sync and async functions
        if inspect.iscoroutinefunction(self.function):
            return await self.function(**kwargs)
        else:
            return self.function(**kwargs)


class ToolRegistry:
    """
    Manages tools for an agent

    Maintains a collection of tools that can be executed locally.
    """

    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def add(self, tool: Tool):
        """Add a tool to the registry"""
        self._tools[tool.name] = tool

    def register(self, tool: Tool):
        """Alias for add() - register a tool"""
        self.add(tool)

    def remove(self, tool_name: str) -> bool:
        """
        Remove a tool from the registry

        Args:
            tool_name: Name of tool to remove

        Returns:
            bool: True if tool was removed, False if not found
        """
        if tool_name in self._tools:
            del self._tools[tool_name]
            return True
        return False

    def get(self, name: str) -> Optional[Tool]:
        """Get tool by name"""
        return self._tools.get(name)

    def list(self) -> List[Tool]:
        """List all registered tools"""
        return list(self._tools.values())

    def clear(self):
        """Clear all tools"""
        self._tools.clear()

    def to_api_format(self) -> List[Dict[str, Any]]:
        """Convert all tools to API format for registration"""
        return [tool.to_api_format() for tool in self._tools.values()]

    def __len__(self) -> int:
        return len(self._tools)

    def __contains__(self, tool_name: str) -> bool:
        return tool_name in self._tools


class LocalToolExecutor:
    """
    Executes local tools during agent runs

    Handles tool execution with error handling - errors are returned
    as strings (not raised) so the agent can handle them intelligently.
    """

    def __init__(self, tools: ToolRegistry):
        self._tools = tools

    async def execute(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """
        Execute a tool by name with given arguments

        Args:
            tool_name: Name of tool to execute
            arguments: Tool arguments as dict

        Returns:
            str: Tool result (success or error message)

        Note: This method NEVER raises exceptions. All errors are returned
        as strings so the agent can handle them.
        """
        tool = self._tools.get(tool_name)

        if not tool:
            # Return error message (don't raise)
            available = list(self._tools._tools.keys())
            return (
                f"Error: Tool '{tool_name}' not found in local registry. "
                f"Available tools: {available}"
            )

        try:
            # Execute tool
            result = await tool.execute(**arguments)
            # Convert result to string
            return str(result)

        except Exception as e:
            # Return error as string (don't raise)
            error_type = type(e).__name__
            error_msg = str(e)
            return f"Error executing tool '{tool_name}': {error_type}: {error_msg}"
