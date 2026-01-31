"""
Memory entity classes
"""

from typing import Dict, Any, Optional, List, TYPE_CHECKING
from pydantic import BaseModel, Field, ConfigDict, PrivateAttr
from lyzr.memory.enums import MemoryProvider, MemoryStatus

if TYPE_CHECKING:
    from lyzr.http import HTTPClient
    from lyzr.memory.config import MemoryResource


class Memory(BaseModel):
    """
    Smart Memory object - represents a memory provider connection

    Can validate connections, check status, and manage resources (AWS).
    """

    credential_id: str = Field(..., description="Credential ID")
    provider: MemoryProvider = Field(..., description="Memory provider type")
    name: str = Field(..., description="Credential name")
    status: Optional[MemoryStatus] = Field(None, description="Connection status")

    # AWS-specific fields
    memory_id: Optional[str] = Field(None, description="AWS memory resource ID")
    memory_arn: Optional[str] = Field(None, description="AWS memory ARN")

    # Metadata
    validated_at: Optional[str] = Field(None, description="Last validation timestamp")
    created_at: Optional[str] = Field(None, description="Creation timestamp")

    # Private fields (injected by MemoryModule)
    _http: Optional['HTTPClient'] = PrivateAttr(default=None)
    _memory_module: Optional[Any] = PrivateAttr(default=None)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True
    )

    def _ensure_clients(self):
        """Ensure HTTP client and module are available"""
        if not self._http or not self._memory_module:
            raise RuntimeError(
                "Memory not properly initialized. "
                "Use Studio.create_memory_credential() or Studio.get_memory()"
            )

    def validate(self) -> Dict[str, Any]:
        """
        Validate memory provider connection

        Returns:
            Dict: Validation result with 'valid' key and provider-specific data

        Example:
            >>> memory = studio.create_memory_credential(provider="mem0", ...)
            >>> result = memory.validate()
            >>> print(f"Valid: {result['valid']}")
        """
        self._ensure_clients()
        return self._memory_module._validate(self.provider, self.credential_id)

    def get_status(self) -> MemoryStatus:
        """
        Get current memory connection status

        Returns:
            MemoryStatus: Current status (ACTIVE, PENDING, FAILED, etc.)

        Example:
            >>> status = memory.get_status()
            >>> print(f"Status: {status}")
        """
        self._ensure_clients()
        return self._memory_module._get_status(self.provider, self.credential_id)

    def list_resources(self) -> List['MemoryResource']:
        """
        List memory resources (AWS AgentCore only)

        Returns:
            List[MemoryResource]: List of AWS memory resources

        Raises:
            ValueError: If provider is not AWS AgentCore

        Example:
            >>> resources = aws_memory.list_resources()
            >>> for r in resources:
            ...     print(f"{r.memory_id}: {r.status}")
        """
        if self.provider != MemoryProvider.AWS_AGENTCORE:
            raise ValueError(
                f"list_resources() only available for AWS AgentCore, "
                f"not {self.provider.value}"
            )

        self._ensure_clients()
        return self._memory_module._list_resources(self.credential_id)

    def use_existing(self, memory_id: str) -> 'Memory':
        """
        Use an existing AWS memory resource (AWS AgentCore only)

        Args:
            memory_id: AWS memory resource ID to use

        Returns:
            Memory: Updated memory object

        Raises:
            ValueError: If provider is not AWS AgentCore

        Example:
            >>> aws_memory = aws_memory.use_existing("memory-abc123")
        """
        if self.provider != MemoryProvider.AWS_AGENTCORE:
            raise ValueError(
                f"use_existing() only available for AWS AgentCore, "
                f"not {self.provider.value}"
            )

        self._ensure_clients()
        return self._memory_module._use_existing_resource(self.credential_id, memory_id)

    def delete_resource(self) -> bool:
        """
        Delete AWS memory resource (AWS AgentCore only)

        Returns:
            bool: True if successful

        Raises:
            ValueError: If provider is not AWS AgentCore

        Example:
            >>> success = aws_memory.delete_resource()
        """
        if self.provider != MemoryProvider.AWS_AGENTCORE:
            raise ValueError(
                f"delete_resource() only available for AWS AgentCore, "
                f"not {self.provider.value}"
            )

        self._ensure_clients()
        return self._memory_module._delete_resource(self.credential_id)

    def delete(self) -> bool:
        """
        Delete this memory credential

        Returns:
            bool: True if successful

        Example:
            >>> memory.delete()
        """
        self._ensure_clients()
        return self._memory_module.delete_credential(self.credential_id)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return self.model_dump(by_alias=False, exclude_none=True)


class MemoryList(BaseModel):
    """List of memory credentials"""

    memories: List[Memory] = Field(default_factory=list, description="List of memories")
    total: Optional[int] = Field(None, description="Total count")

    def __iter__(self):
        return iter(self.memories)

    def __len__(self):
        return len(self.memories)

    def __getitem__(self, index):
        return self.memories[index]
