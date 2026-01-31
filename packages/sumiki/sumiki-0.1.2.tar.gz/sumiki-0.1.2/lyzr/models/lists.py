"""
AgentList wrapper class
"""

from typing import Optional, List, TYPE_CHECKING, Any
from pydantic import BaseModel, Field, ConfigDict

if TYPE_CHECKING:
    from lyzr.models.agent import Agent


class AgentList(BaseModel):
    """List of agents with metadata"""
    agents: List['Agent'] = Field(default_factory=list, description="List of agents")
    total: Optional[int] = Field(None, description="Total count")

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def __iter__(self):
        return iter(self.agents)

    def __len__(self):
        return len(self.agents)

    def __getitem__(self, index):
        return self.agents[index]
