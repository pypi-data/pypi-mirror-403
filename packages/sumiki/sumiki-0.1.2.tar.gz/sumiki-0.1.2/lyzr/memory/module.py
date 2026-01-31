"""
MemoryModule for managing memory providers and credentials
"""

from typing import Dict, Any, Optional, List, TYPE_CHECKING
from lyzr.base import BaseModule
from lyzr.memory.enums import MemoryProvider, MemoryStatus
from lyzr.memory.config import MemoryCredentialConfig, MemoryResource
from lyzr.memory.entity import Memory, MemoryList

if TYPE_CHECKING:
    from lyzr.http import HTTPClient


class MemoryModule(BaseModule):
    """
    Module for managing memory providers and credentials

    Supports AWS AgentCore, Mem0, SuperMemory, and Lyzr providers.

    Example (Standalone):
        >>> from lyzr.http import HTTPClient
        >>> from lyzr.memory import MemoryModule
        >>> http = HTTPClient(api_key="sk-xxx")
        >>> memory_module = MemoryModule(http)
        >>> providers = memory_module.list_providers()

    Example (Through Studio):
        >>> from lyzr import Studio
        >>> studio = Studio(api_key="sk-xxx")
        >>> providers = studio.list_memory_providers()
    """

    def _make_smart_memory(self, memory_data: Dict[str, Any]) -> Memory:
        """
        Create smart Memory object with injected clients

        Args:
            memory_data: Raw memory data

        Returns:
            Memory: Smart memory object with methods
        """
        memory = Memory(**memory_data)
        memory._http = self._http
        memory._memory_module = self
        return memory

    def list_providers(self) -> List[Dict[str, Any]]:
        """
        List all available memory providers

        Returns:
            List[Dict]: Memory providers with metadata

        Example:
            >>> providers = memory_module.list_providers()
            >>> for p in providers:
            ...     print(f"{p['provider_id']}: {p['meta_data']['provider_name']}")
        """
        response = self._http.get("/v3/memory/providers")
        return response if isinstance(response, list) else []

    def get_provider(self, provider_id: str) -> Dict[str, Any]:
        """
        Get specific memory provider details

        Args:
            provider_id: Provider ID (aws-agentcore, mem0, supermemory)

        Returns:
            Dict: Provider details with form schema and metadata

        Example:
            >>> provider = memory_module.get_provider("mem0")
            >>> print(provider['form'])  # Form schema for credentials
        """
        return self._http.get(f"/v3/memory/providers/{provider_id}")

    def create_credential(
        self,
        provider: str,
        name: str,
        **credentials
    ) -> Memory:
        """
        Create memory provider credential

        Args:
            provider: Provider name (aws-agentcore, mem0, supermemory, lyzr)
            name: Credential name
            **credentials: Provider-specific credentials

        Returns:
            Memory: Smart memory object

        Example:
            >>> # Mem0
            >>> mem0 = memory_module.create_credential(
            ...     provider="mem0",
            ...     name="My Mem0",
            ...     api_key="mem0_key_here"
            ... )
            >>>
            >>> # AWS AgentCore
            >>> aws = memory_module.create_credential(
            ...     provider="aws-agentcore",
            ...     name="AWS Memory",
            ...     aws_access_key_id="...",
            ...     aws_secret_access_key="...",
            ...     aws_region="us-east-1"
            ... )
        """
        provider_enum = MemoryProvider(provider)

        # Build configuration
        config_data = {
            "provider": provider_enum,
            "name": name,
            **credentials
        }

        config = MemoryCredentialConfig(**config_data)

        # Create credential via provider credentials API
        response = self._http.post(
            "/v3/providers/credentials",
            json=config.to_api_dict()
        )

        # Build Memory object
        memory_data = {
            "credential_id": response.get("credential_id") or response.get("_id"),
            "provider": provider_enum,
            "name": name,
            "status": MemoryStatus.PENDING,
            "created_at": response.get("created_at")
        }

        return self._make_smart_memory(memory_data)

    def get_memory(self, credential_id: str, provider: str) -> Memory:
        """
        Get memory by credential ID

        Args:
            credential_id: Credential ID
            provider: Provider name

        Returns:
            Memory: Smart memory object

        Example:
            >>> memory = memory_module.get_memory("cred_123", "mem0")
        """
        provider_enum = MemoryProvider(provider)

        # Fetch credential
        response = self._http.get(f"/v3/providers/credentials/{credential_id}")

        memory_data = {
            "credential_id": credential_id,
            "provider": provider_enum,
            "name": response.get("name", "Unknown"),
            "created_at": response.get("created_at")
        }

        return self._make_smart_memory(memory_data)

    def list_memories(self) -> MemoryList:
        """
        List all memory credentials for current user

        Returns:
            MemoryList: List of memory credentials (iterable)

        Example:
            >>> memories = memory_module.list_memories()
            >>> for m in memories:
            ...     print(f"{m.name}: {m.provider.value}")
        """
        # Query provider credentials of type 'memory'
        try:
            response = self._http.get("/v3/providers/credentials/type/memory")

            if isinstance(response, list):
                memories = [self._make_smart_memory({
                    "credential_id": cred.get("_id") or cred.get("credential_id"),
                    "provider": MemoryProvider(cred.get("provider_id", "lyzr")),
                    "name": cred.get("name", "Unknown"),
                    "created_at": cred.get("created_at")
                }) for cred in response]

                return MemoryList(memories=memories, total=len(memories))
            else:
                return MemoryList(memories=[])
        except Exception:
            return MemoryList(memories=[])

    def delete_credential(self, credential_id: str) -> bool:
        """
        Delete memory credential

        Args:
            credential_id: Credential ID to delete

        Returns:
            bool: True if successful

        Example:
            >>> memory_module.delete_credential("cred_123")
        """
        self._http.delete(f"/v3/providers/credentials/{credential_id}")
        return True

    # ========================================================================
    # Provider-Specific Validation Methods
    # ========================================================================

    def _validate(self, provider: MemoryProvider, credential_id: str) -> Dict[str, Any]:
        """
        Internal: Validate memory provider connection

        Args:
            provider: Memory provider type
            credential_id: Credential ID

        Returns:
            Dict: Validation result
        """
        if provider == MemoryProvider.AWS_AGENTCORE:
            return self._http.get(f"/v3/memory/aws-agentcore/{credential_id}/validate")
        elif provider == MemoryProvider.MEM0:
            return self._http.get(f"/v3/memory/mem0/{credential_id}/validate")
        elif provider == MemoryProvider.SUPERMEMORY:
            return self._http.get(f"/v3/memory/supermemory/{credential_id}/validate")
        else:
            # Lyzr provider doesn't need validation
            return {"valid": True, "provider": "lyzr", "message": "Lyzr provider is built-in"}

    def _get_status(self, provider: MemoryProvider, credential_id: str) -> MemoryStatus:
        """
        Internal: Get memory provider status

        Args:
            provider: Memory provider type
            credential_id: Credential ID

        Returns:
            MemoryStatus: Current status
        """
        try:
            if provider == MemoryProvider.AWS_AGENTCORE:
                response = self._http.get(f"/v3/memory/aws-agentcore/{credential_id}/status")
            elif provider == MemoryProvider.MEM0:
                response = self._http.get(f"/v3/memory/mem0/{credential_id}/status")
            elif provider == MemoryProvider.SUPERMEMORY:
                response = self._http.get(f"/v3/memory/supermemory/{credential_id}/status")
            else:
                return MemoryStatus.ACTIVE  # Lyzr is always active

            # Parse status from response
            status_str = response.get("status", "pending").lower()

            # Map to MemoryStatus enum
            status_mapping = {
                "active": MemoryStatus.ACTIVE,
                "pending": MemoryStatus.PENDING,
                "validating": MemoryStatus.VALIDATING,
                "validated": MemoryStatus.VALIDATED,
                "failed": MemoryStatus.FAILED,
                "creating": MemoryStatus.CREATING
            }

            return status_mapping.get(status_str, MemoryStatus.PENDING)

        except Exception:
            return MemoryStatus.PENDING

    # ========================================================================
    # AWS AgentCore Specific Methods
    # ========================================================================

    def _list_resources(self, credential_id: str) -> List[MemoryResource]:
        """
        Internal: List AWS memory resources

        Args:
            credential_id: AWS credential ID

        Returns:
            List[MemoryResource]: AWS memory resources
        """
        response = self._http.get(f"/v3/memory/aws-agentcore/{credential_id}/resources")

        memories = response.get("memories", [])
        return [MemoryResource(**mem) for mem in memories]

    def _use_existing_resource(self, credential_id: str, memory_id: str) -> Memory:
        """
        Internal: Use existing AWS memory resource

        Args:
            credential_id: AWS credential ID
            memory_id: Memory resource ID to use

        Returns:
            Memory: Updated memory object
        """
        response = self._http.post(
            f"/v3/memory/aws-agentcore/{credential_id}/use-existing",
            json={"memory_id": memory_id}
        )

        # Update memory object with resource info
        memory_data = {
            "credential_id": credential_id,
            "provider": MemoryProvider.AWS_AGENTCORE,
            "name": response.get("name", "AWS Memory"),
            "status": MemoryStatus.ACTIVE,
            "memory_id": memory_id,
            "memory_arn": response.get("memory_arn")
        }

        return self._make_smart_memory(memory_data)

    def _delete_resource(self, credential_id: str) -> bool:
        """
        Internal: Delete AWS memory resource

        Args:
            credential_id: AWS credential ID

        Returns:
            bool: True if successful
        """
        self._http.delete(f"/v3/memory/aws-agentcore/{credential_id}/aws-resource")
        return True
