"""
Tools package for Lyzr SDK

Provides local and backend tool support.
"""

# Local tools
from lyzr.tools.local import Tool, ToolRegistry, LocalToolExecutor

# Tool decorator
from lyzr.tools.decorators import tool, get_registered_tools, clear_tools

# Backend tool configuration
from lyzr.tools.backend import ToolConfig

# Typed backend tools with autocomplete
from lyzr.tools.backend_tools import (
    ToolSource,
    BackendToolAction,
    # ACI Tools
    HubSpot,
    Stripe,
    Shopify,
    Salesforce,
    Slack,
    # Composio Tools
    Gmail,
    GitHub,
    GoogleCalendar,
    GoogleDrive,
    Notion
)

__all__ = [
    # Local tools
    "Tool",
    "ToolRegistry",
    "LocalToolExecutor",
    "tool",
    "get_registered_tools",
    "clear_tools",

    # Backend tools
    "ToolConfig",
    "ToolSource",
    "BackendToolAction",

    # Typed tool classes
    "HubSpot",
    "Stripe",
    "Shopify",
    "Salesforce",
    "Slack",
    "Gmail",
    "GitHub",
    "GoogleCalendar",
    "GoogleDrive",
    "Notion",
]
