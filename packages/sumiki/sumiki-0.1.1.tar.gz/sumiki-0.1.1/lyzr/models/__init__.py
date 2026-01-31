"""
Agent models for Lyzr SDK
"""

from lyzr.models.config import AgentConfig
from lyzr.models.agent import Agent
from lyzr.models.lists import AgentList

# Rebuild models to resolve forward references
# This is needed because AgentConfig references Context, KnowledgeBase, etc.
# and AgentList references Agent
try:
    AgentConfig.model_rebuild()
    AgentList.model_rebuild()
except Exception:
    # If rebuild fails, it's okay - will be resolved at runtime
    pass

__all__ = ["AgentConfig", "Agent", "AgentList"]
