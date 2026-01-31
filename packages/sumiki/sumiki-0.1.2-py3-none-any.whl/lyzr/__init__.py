"""
Lyzr Agent SDK - Intuitive Python SDK for Lyzr Agent API
"""

from lyzr.__version__ import __version__
from lyzr.studio import Studio
from lyzr.models import Agent, AgentConfig
from lyzr.responses import AgentResponse, AgentStream, TaskResponse, TaskStatus, Artifact
from lyzr.protocols import Runnable, Updatable, Deletable, Cloneable
from lyzr.inference import InferenceModule
from lyzr.knowledge_base import (
    KnowledgeBase,
    KnowledgeBaseModule,
    QueryResult,
    Document,
    KnowledgeBaseRuntimeConfig,
)
from lyzr.tools.local import Tool, ToolRegistry, LocalToolExecutor
from lyzr.tools.decorators import tool, get_registered_tools, clear_tools
from lyzr.tools.backend import ToolConfig
from lyzr.tools.backend_tools import (
    BackendToolAction,
    ToolSource,
    HubSpot,
    Stripe,
    Shopify,
    Salesforce,
    Slack,
    Gmail,
    GitHub,
    GoogleCalendar,
    GoogleDrive,
    Notion
)
from lyzr.image_models import ImageModelConfig, Gemini, DallE, ImageProvider
from lyzr.rai import RAIPolicy, RAIModule, RAIPolicyList, PIIType, PIIAction, SecretsAction, ValidationMethod
from lyzr.context import Context, ContextModule, ContextList
from lyzr.memory import (
    MemoryConfig,
    Memory,
    MemoryModule,
    MemoryProvider,
    MemoryStatus,
    MemoryResource,
    MemoryCredentialConfig,
    MemoryList
)
from lyzr.exceptions import (
    LyzrError,
    AuthenticationError,
    ValidationError,
    NotFoundError,
    APIError,
    RateLimitError,
    TimeoutError,
    InvalidResponseError,
    ToolNotFoundError,
)

__all__ = [
    # Main entry point
    "Studio",

    # Core models
    "Agent",
    "AgentConfig",

    # Knowledge Base
    "KnowledgeBase",
    "KnowledgeBaseModule",
    "QueryResult",
    "Document",
    "KnowledgeBaseRuntimeConfig",

    # Tools
    "tool",
    "Tool",
    "ToolRegistry",
    "LocalToolExecutor",
    "get_registered_tools",
    "clear_tools",
    "ToolConfig",
    "BackendToolAction",
    "ToolSource",

    # Typed Backend Tools
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

    # Image Models
    "ImageModelConfig",
    "Gemini",
    "DallE",
    "ImageProvider",

    # RAI (Responsible AI)
    "RAIPolicy",
    "RAIModule",
    "RAIPolicyList",
    "PIIType",
    "PIIAction",
    "SecretsAction",
    "ValidationMethod",

    # Context
    "Context",
    "ContextModule",
    "ContextList",

    # Memory
    "MemoryConfig",
    "Memory",
    "MemoryModule",
    "MemoryProvider",
    "MemoryStatus",
    "MemoryResource",
    "MemoryCredentialConfig",
    "MemoryList",

    # Response types
    "AgentResponse",
    "AgentStream",
    "TaskResponse",
    "TaskStatus",
    "Artifact",

    # Protocols
    "Runnable",
    "Updatable",
    "Deletable",
    "Cloneable",

    # Modules
    "InferenceModule",

    # Exceptions
    "LyzrError",
    "AuthenticationError",
    "ValidationError",
    "NotFoundError",
    "APIError",
    "RateLimitError",
    "TimeoutError",
    "InvalidResponseError",
    "ToolNotFoundError",
]

# Rebuild models to resolve forward references after all imports are complete
# This is needed because AgentConfig references Context, KnowledgeBase, etc.
AgentConfig.model_rebuild()
Agent.model_rebuild()
