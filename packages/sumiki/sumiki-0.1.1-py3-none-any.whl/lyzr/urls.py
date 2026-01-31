"""
Environment-based URL configuration for Lyzr SDK

Centralized configuration for all service URLs across different environments.
"""

from pydantic import BaseModel, ConfigDict


class ServiceURLs(BaseModel):
    """Service URLs for a specific environment"""

    agent_api: str
    rag_api: str
    rai_api: str
    # Future additions:
    # memory_api: str
    # workflow_api: str
    # tools_api: str

    model_config = ConfigDict(frozen=True)


# Production URLs (default)
PROD_URLS = ServiceURLs(
    agent_api="https://agent-prod.studio.lyzr.ai",
    rag_api="https://rag-prod.studio.lyzr.ai",
    rai_api="https://srs-prod.studio.lyzr.ai"
)

# Development URLs
DEV_URLS = ServiceURLs(
    agent_api="https://agent-dev.test.studio.lyzr.ai",
    rag_api="https://rag-dev.test.studio.lyzr.ai",
    rai_api="https://srs-dev.test.studio.lyzr.ai"
)

# Local URLs
LOCAL_URLS = ServiceURLs(
    agent_api="http://localhost:8001",
    rag_api="http://localhost:8001",
    rai_api="http://localhost:8001"
)

# Environment mapping
ENVIRONMENTS = {
    "prod": PROD_URLS,
    "dev": DEV_URLS,
    "local": LOCAL_URLS
}


def get_urls(env: str = "prod") -> ServiceURLs:
    """
    Get service URLs for specified environment

    Args:
        env: Environment name (prod, dev, local)

    Returns:
        ServiceURLs: URL configuration for the environment

    Raises:
        ValueError: If environment is unknown

    Example:
        >>> urls = get_urls("prod")
        >>> print(urls.agent_api)
        https://agent-prod.studio.lyzr.ai
    """
    env = env.lower()

    if env not in ENVIRONMENTS:
        raise ValueError(
            f"Unknown environment: '{env}'. "
            f"Valid environments: {', '.join(ENVIRONMENTS.keys())}"
        )

    urls = ENVIRONMENTS[env]

    # Validate URLs are configured
    if not urls.agent_api or not urls.rag_api:
        raise ValueError(
            f"Environment '{env}' is not fully configured. "
            f"Please add URLs in lyzr/urls.py"
        )

    return urls
