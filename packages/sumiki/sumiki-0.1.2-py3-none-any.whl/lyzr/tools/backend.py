"""
Backend tool integrations for Lyzr SDK

Support for ACI, Composio, and OpenAPI tools that execute on Studio backend.
"""

from typing import List, Literal, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class ToolConfig(BaseModel):
    """
    Configuration for backend-executed tools (ACI/Composio/OpenAPI)

    These tools execute on Lyzr Studio backend, not on the client.
    """

    tool_name: str = Field(..., description="Tool/integration name")
    tool_source: Literal["aci", "composio", "openapi"] = Field(..., description="Tool source type")
    action_names: List[str] = Field(default_factory=list, description="Specific actions to enable")
    persist_auth: bool = Field(True, description="Persist authentication credentials")

    model_config = ConfigDict(frozen=False)

    def to_api_format(self) -> Dict[str, Any]:
        """Convert to API request format"""
        return {
            "tool_name": self.tool_name,
            "tool_source": self.tool_source,
            "action_names": self.action_names,
            "persist_auth": self.persist_auth
        }


def aci_tool(
    name: str,
    actions: Optional[List[str]] = None,
    persist_auth: bool = True
) -> ToolConfig:
    """
    Create ACI tool configuration

    ACI tools are enterprise integrations (HubSpot, Stripe, Shopify, etc.)
    that execute on Studio backend.

    Args:
        name: Integration name (will be uppercased)
        actions: List of action names to enable (e.g., ["HUBSPOT_CREATE_CONTACT"])
        persist_auth: Persist authentication (default: True)

    Returns:
        ToolConfig: Tool configuration object

    Example:
        >>> from lyzr.integrations import aci_tool
        >>>
        >>> # Enable HubSpot contact creation
        >>> hubspot = aci_tool("HUBSPOT", actions=["HUBSPOT_CREATE_CONTACT", "HUBSPOT_GET_DEAL"])
        >>>
        >>> # Use in agent creation
        >>> agent = studio.create_agent(
        ...     name="Sales Agent",
        ...     provider="gpt-4o",
        ...     tools=[hubspot]
        ... )
    """
    return ToolConfig(
        tool_name=name.upper(),
        tool_source="aci",
        action_names=actions or [],
        persist_auth=persist_auth
    )


def composio_tool(
    name: str,
    actions: Optional[List[str]] = None,
    persist_auth: bool = True
) -> ToolConfig:
    """
    Create Composio tool configuration

    Composio tools are standard app integrations (Gmail, Google Calendar, GitHub, etc.)
    that execute on Studio backend.

    Args:
        name: Tool name (will be lowercased)
        actions: List of action names to enable (e.g., ["GMAIL_SEND_EMAIL"])
        persist_auth: Persist authentication (default: True)

    Returns:
        ToolConfig: Tool configuration object

    Example:
        >>> from lyzr.integrations import composio_tool
        >>>
        >>> # Enable Gmail
        >>> gmail = composio_tool("gmail", actions=["GMAIL_SEND_EMAIL", "GMAIL_READ_EMAIL"])
        >>>
        >>> # Use in agent creation
        >>> agent = studio.create_agent(
        ...     name="Email Agent",
        ...     provider="gpt-4o",
        ...     tools=[gmail]
        ... )
    """
    return ToolConfig(
        tool_name=name.lower(),
        tool_source="composio",
        action_names=actions or [],
        persist_auth=persist_auth
    )


def openapi_tool(
    name: str,
    persist_auth: bool = False
) -> ToolConfig:
    """
    Create OpenAPI tool configuration

    OpenAPI tools are custom API integrations that execute on Studio backend.

    Args:
        name: Tool name
        persist_auth: Persist authentication (default: False)

    Returns:
        ToolConfig: Tool configuration object

    Example:
        >>> from lyzr.integrations import openapi_tool
        >>>
        >>> # Add custom API
        >>> my_api = openapi_tool("my_custom_api")
        >>>
        >>> agent = studio.create_agent(
        ...     name="API Agent",
        ...     provider="gpt-4o",
        ...     tools=[my_api]
        ... )
    """
    return ToolConfig(
        tool_name=name,
        tool_source="openapi",
        action_names=[],
        persist_auth=persist_auth
    )
