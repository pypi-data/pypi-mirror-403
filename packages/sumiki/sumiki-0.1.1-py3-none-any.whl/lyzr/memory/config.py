"""
Configuration classes for Memory module
"""

from typing import Literal, Dict, Any, Optional, List
from pydantic import BaseModel, Field, ConfigDict, field_validator
from lyzr.memory.enums import MemoryProvider


class MemoryConfig(BaseModel):
    """
    Memory configuration for agents

    Configures how agents maintain conversation context across messages
    in a session.
    """

    provider: Literal["lyzr"] = Field(
        "lyzr",
        description="Memory provider (currently only 'lyzr' is supported)"
    )
    max_messages_context_count: int = Field(
        10,
        ge=1,
        le=200,
        description="Maximum messages to keep in conversation context"
    )

    model_config = ConfigDict(frozen=True)

    @field_validator('max_messages_context_count')
    @classmethod
    def validate_max_messages(cls, v: int) -> int:
        """Validate max_messages_context_count is in reasonable range"""
        if v < 1:
            raise ValueError("max_messages_context_count must be at least 1")
        if v > 200:
            raise ValueError(
                "max_messages_context_count cannot exceed 200. "
                "Large context windows may impact performance and cost."
            )
        return v

    def to_feature_format(self) -> Dict[str, Any]:
        """
        Convert to feature format for API

        Returns:
            Dict: Feature object ready for API

        Example:
            >>> config = MemoryConfig(max_messages_context_count=50)
            >>> feature = config.to_feature_format()
            >>> print(feature)
            {
                "type": "MEMORY",
                "config": {
                    "provider": "lyzr",
                    "max_messages_context_count": 50
                },
                "priority": 0
            }
        """
        return {
            "type": "MEMORY",
            "config": {
                "provider": self.provider,
                "max_messages_context_count": self.max_messages_context_count
            },
            "priority": 0
        }


class MemoryResource(BaseModel):
    """AWS AgentCore memory resource"""

    memory_id: str = Field(..., description="AWS memory resource ID")
    name: Optional[str] = Field(None, description="Memory resource name")
    status: str = Field(..., description="Resource status (ACTIVE, CREATING, etc.)")
    arn: Optional[str] = Field(None, description="AWS ARN")
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    event_expiry_days: Optional[int] = Field(None, description="Event expiry in days")
    strategies: Optional[List[str]] = Field(None, description="Memory strategies enabled")

    model_config = ConfigDict(arbitrary_types_allowed=True)


class MemoryCredentialConfig(BaseModel):
    """Configuration for creating memory provider credentials"""

    provider: MemoryProvider = Field(..., description="Memory provider type")
    name: str = Field(..., description="Credential name")

    # AWS AgentCore fields
    aws_access_key_id: Optional[str] = Field(None, description="AWS access key")
    aws_secret_access_key: Optional[str] = Field(None, description="AWS secret key")
    aws_region: Optional[str] = Field(None, description="AWS region")

    # Mem0 fields
    mem0_api_key: Optional[str] = Field(None, description="Mem0 API key")
    mem0_host: Optional[str] = Field(None, description="Mem0 host URL")

    # SuperMemory fields
    supermemory_api_key: Optional[str] = Field(None, description="SuperMemory API key")
    supermemory_api_url: Optional[str] = Field(None, description="SuperMemory API URL")

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def to_api_dict(self) -> Dict[str, Any]:
        """Convert to provider credentials API format"""
        # Base credential data
        cred_data = {
            "name": self.name,
            "provider_id": self.provider.value,
            "type": "memory"
        }

        # Provider-specific credentials
        if self.provider == MemoryProvider.AWS_AGENTCORE:
            cred_data["credentials"] = {
                "aws_access_key_id": self.aws_access_key_id,
                "aws_secret_access_key": self.aws_secret_access_key,
                "region": self.aws_region
            }
        elif self.provider == MemoryProvider.MEM0:
            cred_data["credentials"] = {
                "api_key": self.mem0_api_key,
                "host": self.mem0_host or "https://api.mem0.ai"
            }
        elif self.provider == MemoryProvider.SUPERMEMORY:
            cred_data["credentials"] = {
                "api_key": self.supermemory_api_key,
                "api_url": self.supermemory_api_url or "https://api.supermemory.ai"
            }

        return cred_data
