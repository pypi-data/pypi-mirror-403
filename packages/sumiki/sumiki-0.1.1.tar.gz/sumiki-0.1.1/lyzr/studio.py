"""
Studio - Main entry point for Lyzr Agent SDK
"""

from typing import Optional, Dict
from lyzr.http import HTTPClient
from lyzr.agents import AgentModule
from lyzr.knowledge_base import KnowledgeBaseModule
from lyzr.memory import MemoryModule
from lyzr.context import ContextModule
from lyzr.rai import RAIModule


class Studio:
    """
    Main client for interacting with Lyzr Agent API

    Studio provides a clean interface to all Lyzr Agent API functionality.
    Each resource (agents, memory, artifacts, etc.) is accessible both as
    a module and through convenience methods.

    Example:
        >>> studio = Studio(api_key="sk-xxx")
        >>>
        >>> # Method 1: Direct convenience methods
        >>> agent = studio.create_agent(name="Bot", provider="openai/gpt-4o")
        >>>
        >>> # Method 2: Through module
        >>> agent = studio.agents.create(name="Bot", provider="openai/gpt-4o")
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        env: str = "prod",
        timeout: Optional[int] = None,
        log: str = "warning",
    ):
        """
        Initialize Studio client

        Args:
            api_key: Lyzr API key (reads from LYZR_API_KEY env var if not provided)
            env: Environment (prod, dev, local) - default: prod
            timeout: Request timeout in seconds (default: 30s for prod/dev, 300s for local)
            log: Log level (debug, info, warning, error, none) - default: warning

        Raises:
            AuthenticationError: If API key is not provided or invalid
            ValueError: If environment is unknown or not configured

        Example:
            >>> # Production (default)
            >>> studio = Studio(api_key="sk-xxx")
            >>>
            >>> # Development
            >>> studio = Studio(api_key="sk-xxx", env="dev")
            >>>
            >>> # Debug logging
            >>> studio = Studio(api_key="sk-xxx", log="debug")
            >>>
            >>> # Using environment variable
            >>> import os
            >>> os.environ["LYZR_API_KEY"] = "sk-xxx"
            >>> studio = Studio()
        """
        from lyzr.urls import get_urls
        from lyzr.logger import set_log_level, get_logger

        # Set log level
        set_log_level(log)
        logger = get_logger()
        logger.info(f"Initializing Studio (env={env})")

        # Get environment configuration
        self.env_config = get_urls(env)
        self.env = env

        # Set default timeout based on environment
        if timeout is None:
            timeout = 300

        # Initialize HTTP client for Agent API
        self._http = HTTPClient(
            api_key=api_key, base_url=self.env_config.agent_api, timeout=timeout
        )

        # Register modules
        self._register_modules()

    def _register_modules(self):
        """Register all SDK modules and inject convenience methods"""

        # Register Agents module
        self.agents = AgentModule(self._http)

        # Inject convenience methods for agents
        # This allows both studio.create_agent() and studio.agents.create()
        self.create_agent = self.agents.create
        self.get_agent = self.agents.get
        self.list_agents = self.agents.list
        self.update_agent = self.agents.update
        self.delete_agent = self.agents.delete
        self.clone_agent = self.agents.clone
        self.bulk_delete_agents = self.agents.bulk_delete

        # Register KnowledgeBase module
        # Note: KnowledgeBaseModule creates its own HTTP client for RAG API
        self.knowledge_bases = KnowledgeBaseModule(self._http, self.env_config)

        # Inject convenience methods for knowledge bases
        self.create_knowledge_base = self.knowledge_bases.create
        self.get_knowledge_base = self.knowledge_bases.get
        self.list_knowledge_bases = self.knowledge_bases.list
        self.delete_knowledge_base = self.knowledge_bases.delete
        self.bulk_delete_knowledge_bases = self.knowledge_bases.bulk_delete

        # Register Context module
        self.contexts = ContextModule(self._http)
        self.create_context = self.contexts.create
        self.get_context = self.contexts.get
        self.list_contexts = self.contexts.list

        # Register RAI module
        self.rai = RAIModule(self._http, self.env_config)
        self.create_rai_policy = self.rai.create_policy
        self.get_rai_policy = self.rai.get_policy
        self.list_rai_policies = self.rai.list_policies

        # Register Memory module
        self.memory = MemoryModule(self._http)

        # Inject convenience methods for memory
        self.list_memory_providers = self.memory.list_providers
        self.create_memory_credential = self.memory.create_credential
        self.get_memory = self.memory.get_memory
        self.list_memories = self.memory.list_memories

        # Future modules will be registered here:
        # self.artifacts = ArtifactModule(self._http)
        # ...

    def list_available_tools(self) -> Dict:
        """
        List all available backend tools (ACI, Composio, OpenAPI)

        Returns:
            Dict: Available tools with aci_tools, composio_tools, openapi_tools

        Example:
            >>> tools = studio.list_available_tools()
            >>> for tool in tools['aci_tools']:
            ...     print(f"{tool['name']}: {tool['actions']}")
        """
        return self.agents.list_available_tools()

    def close(self):
        """Close the HTTP client connection"""
        self._http.close()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

    def __repr__(self) -> str:
        """String representation"""
        return f"Studio(base_url='{self._http.base_url}')"
